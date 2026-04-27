from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional, Tuple

from bookforge.config.env import load_config
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.outline import PHASE03_T1_INSTRUCTION, PHASE03_T2_INSTRUCTION
from bookforge.pipeline.chapter_seam import finalize_locked_chapter
from bookforge.phases.outline import context as outline_context
from bookforge.phases.outline import get_handler
from bookforge.prompt.renderer import render_template_file
from bookforge.runner import run_section_range
from bookforge.supervision import capture_main_branch_snapshot, emit_reconciled_main_branch_contracts
from bookforge.util.json_extract import extract_json


REGISTRY_FILENAME = "snapshot_registry.json"
THIN_FILENAME = "outline.thin.json"
TOC_FILENAME = "outline.toc.json"
INDEX_FILENAME = "outline.index.json"
APPENDIX_FILENAME = "outline.appendix.json"
SECTION_DRAFT_DIRNAME = "section_drafts"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _book_root(workspace: Path, book_id: str) -> Path:
    return workspace / "books" / book_id


def _outline_dir(book_root: Path) -> Path:
    return book_root / "outline"


def _pipeline_run_dir(book_root: Path, run_id: Optional[str]) -> Tuple[str, Path]:
    resolved_run_id = str(run_id or "").strip()
    if not resolved_run_id:
        latest_path = _outline_dir(book_root) / "pipeline_latest.json"
        if not latest_path.exists():
            raise FileNotFoundError(f"Missing outline pipeline latest pointer: {latest_path}")
        latest = _read_json(latest_path)
        resolved_run_id = str(latest.get("run_id") or "").strip()
    if not resolved_run_id:
        raise ValueError("Unable to resolve outline run id.")
    run_dir = _outline_dir(book_root) / "pipeline_runs" / resolved_run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Outline pipeline run not found: {run_dir}")
    return resolved_run_id, run_dir


def _load_spine_and_sections(run_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    spine_path = run_dir / "outline_spine_v1.json"
    sections_path = run_dir / "outline_sections_v1.json"
    if not spine_path.exists():
        raise FileNotFoundError(f"Missing outline spine artifact: {spine_path}")
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing outline sections artifact: {sections_path}")
    return _read_json(spine_path), _read_json(sections_path)


def _merge_registry_items(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for item in existing + incoming:
        if not isinstance(item, dict):
            continue
        item_key = str(item.get(key) or "").strip()
        if not item_key:
            continue
        if item_key not in merged:
            merged[item_key] = deepcopy(item)
            continue
        current = merged[item_key]
        for field, value in item.items():
            if field not in current or current.get(field) in (None, "", [], {}):
                current[field] = deepcopy(value)
    return list(merged.values())


def _collect_outline_registries(run_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    characters: List[Dict[str, Any]] = []
    threads: List[Dict[str, Any]] = []
    for path in sorted(run_dir.glob("phase_03_scene_draft_chapter_*_output.json")):
        try:
            payload = _read_json(path)
        except Exception:
            continue
        chapter_characters = payload.get("characters") if isinstance(payload.get("characters"), list) else []
        chapter_threads = payload.get("threads") if isinstance(payload.get("threads"), list) else []
        characters = _merge_registry_items(characters, chapter_characters, "character_id")
        threads = _merge_registry_items(threads, chapter_threads, "thread_id")
    return characters, threads


def _spine_by_chapter(spine: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    mapping: Dict[int, Dict[str, Any]] = {}
    chapters = spine.get("chapters") if isinstance(spine.get("chapters"), list) else []
    for entry in chapters:
        if not isinstance(entry, dict):
            continue
        try:
            chapter_id = int(entry.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        mapping[chapter_id] = entry
    return mapping


def _build_canonical_outline(
    spine: Dict[str, Any],
    sections: Dict[str, Any],
    characters: List[Dict[str, Any]],
    threads: List[Dict[str, Any]],
) -> Dict[str, Any]:
    spine_map = _spine_by_chapter(spine)
    chapters_payload: List[Dict[str, Any]] = []
    chapters = sections.get("chapters") if isinstance(sections.get("chapters"), list) else []
    for chapter_entry in chapters:
        if not isinstance(chapter_entry, dict):
            continue
        try:
            chapter_id = int(chapter_entry.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        spine_entry = deepcopy(spine_map.get(chapter_id, {}))
        chapter_payload: Dict[str, Any] = {
            "chapter_id": chapter_id,
            "title": str(spine_entry.get("title") or "").strip(),
            "goal": str(spine_entry.get("goal") or "").strip(),
            "chapter_role": str(spine_entry.get("chapter_role") or "").strip(),
            "stakes_shift": str(spine_entry.get("stakes_shift") or "").strip(),
            "bridge": deepcopy(spine_entry.get("bridge") if isinstance(spine_entry.get("bridge"), dict) else {}),
            "pacing": deepcopy(spine_entry.get("pacing") if isinstance(spine_entry.get("pacing"), dict) else {}),
            "sections": [],
        }
        section_entries = chapter_entry.get("sections") if isinstance(chapter_entry.get("sections"), list) else []
        for section_entry in section_entries:
            if not isinstance(section_entry, dict):
                continue
            try:
                section_id = int(section_entry.get("section_id"))
            except (TypeError, ValueError):
                continue
            chapter_payload["sections"].append(
                {
                    "section_id": section_id,
                    "title": str(section_entry.get("title") or "").strip(),
                    "intent": str(section_entry.get("intent") or "").strip(),
                    "section_role": str(section_entry.get("section_role") or "").strip(),
                    "target_scene_count": int(section_entry.get("target_scene_count") or 0),
                    "end_condition": str(section_entry.get("end_condition") or "").strip(),
                    "status": "stub",
                    "scenes": [],
                }
            )
        chapters_payload.append(chapter_payload)
    return {
        "schema_version": "1.1",
        "characters": deepcopy(characters),
        "threads": deepcopy(threads),
        "chapters": chapters_payload,
    }


def _build_snapshot_registry(book_id: str, run_id: str, outline: Dict[str, Any]) -> Dict[str, Any]:
    chapters_payload: List[Dict[str, Any]] = []
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        section_payloads: List[Dict[str, Any]] = []
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            try:
                section_id = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            section_payloads.append(
                {
                    "section_id": section_id,
                    "title": str(section.get("title") or "").strip(),
                    "status": str(section.get("status") or "stub").strip() or "stub",
                    "target_scene_count": int(section.get("target_scene_count") or 0),
                    "scene_ref_start": None,
                    "scene_ref_end": None,
                    "boundary_artifact": None,
                }
            )
        chapters_payload.append(
            {
                "chapter_id": chapter_id,
                "title": str(chapter.get("title") or "").strip(),
                "chapter_status": "in_progress",
                "chapter_seam_report": None,
                "chapter_original_markdown": None,
                "chapter_fixed_markdown": None,
                "chapter_provisional_markdown": None,
                "chapter_final_markdown": None,
                "chapter_candidate_markdown": None,
                "sections": section_payloads,
            }
        )
    return {
        "schema_version": "section_workflow_v1",
        "book_id": book_id,
        "source_run_id": run_id,
        "updated_at": _now_iso(),
        "active_section": None,
        "chapters": chapters_payload,
    }


def _flatten_sections(registry: Dict[str, Any]) -> List[Tuple[int, int]]:
    refs: List[Tuple[int, int]] = []
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            try:
                section_id = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            refs.append((chapter_id, section_id))
    return refs


def _find_registry_section(registry: Dict[str, Any], chapter_id: int, section_id: int) -> Dict[str, Any]:
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current_chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current_chapter_id != chapter_id:
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            try:
                current_section_id = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            if current_section_id == section_id:
                return section
    raise ValueError(f"Section not found in registry: {chapter_id}:{section_id}")


def _find_registry_chapter(registry: Dict[str, Any], chapter_id: int) -> Dict[str, Any]:
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current_chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current_chapter_id == chapter_id:
            return chapter
    raise ValueError(f"Chapter not found in registry: {chapter_id}")


def _find_outline_section(outline: Dict[str, Any], chapter_id: int, section_id: int) -> Dict[str, Any]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current_chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current_chapter_id != chapter_id:
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            try:
                current_section_id = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            if current_section_id == section_id:
                return section
    raise ValueError(f"Section not found in outline: {chapter_id}:{section_id}")


def _previous_section_ref(registry: Dict[str, Any], chapter_id: int, section_id: int) -> Optional[Tuple[int, int]]:
    refs = _flatten_sections(registry)
    try:
        index = refs.index((chapter_id, section_id))
    except ValueError:
        return None
    if index <= 0:
        return None
    return refs[index - 1]


def _next_section_ref(registry: Dict[str, Any], chapter_id: int, section_id: int) -> Optional[Tuple[int, int]]:
    refs = _flatten_sections(registry)
    try:
        index = refs.index((chapter_id, section_id))
    except ValueError:
        return None
    if index + 1 >= len(refs):
        return None
    return refs[index + 1]


def _section_scene_range(section: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
    scene_ids: List[int] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        try:
            scene_ids.append(int(scene.get("scene_id")))
        except (TypeError, ValueError):
            continue
    if not scene_ids:
        return None, None
    return min(scene_ids), max(scene_ids)


def _chapter_scene_sequence(chapter: Dict[str, Any]) -> List[Dict[str, Any]]:
    ordered: List[Dict[str, Any]] = []
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        sortable: List[Tuple[int, int, Dict[str, Any]]] = []
        for index, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                continue
            scene_id = _to_int(scene.get("scene_id"))
            if scene_id is None:
                continue
            sortable.append((scene_id, index, scene))
        for _, _, scene in sorted(sortable, key=lambda item: (item[0], item[1])):
            ordered.append(scene)
    return ordered


def _normalize_chapter_scene_graph(
    *,
    book_root: Path,
    outline: Dict[str, Any],
    registry: Dict[str, Any],
    chapter_id: int,
) -> bool:
    chapter = _find_registry_chapter(registry, chapter_id)
    outline_chapter = None
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for item in chapters:
        if not isinstance(item, dict):
            continue
        try:
            current_chapter_id = int(item.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current_chapter_id == chapter_id:
            outline_chapter = item
            break
    if not isinstance(outline_chapter, dict):
        return False

    ordered_scenes = _chapter_scene_sequence(outline_chapter)
    if not ordered_scenes:
        return False

    old_scene_ids: List[int] = []
    old_to_new: Dict[str, str] = {}
    for new_id, scene in enumerate(ordered_scenes, start=1):
        old_scene_id = _to_int(scene.get("scene_id"))
        if old_scene_id is None:
            continue
        old_scene_ids.append(old_scene_id)
        old_to_new[f"{chapter_id}:{old_scene_id}"] = f"{chapter_id}:{new_id}"

    changed = old_scene_ids != list(range(1, len(old_scene_ids) + 1))

    for new_id, scene in enumerate(ordered_scenes, start=1):
        old_scene_id = _to_int(scene.get("scene_id"))
        if old_scene_id != new_id:
            scene["scene_id"] = new_id
            changed = True

    for index, scene in enumerate(ordered_scenes):
        current_ref = f"{chapter_id}:{index + 1}"
        prev_ref = f"{chapter_id}:{index}" if index > 0 else None
        next_ref = f"{chapter_id}:{index + 2}" if index + 1 < len(ordered_scenes) else None

        consumes = str(scene.get("consumes_outcome_from") or "").strip()
        if consumes.startswith(f"{chapter_id}:"):
            mapped = old_to_new.get(consumes)
            desired = mapped or prev_ref or ""
            if desired:
                if consumes != desired:
                    scene["consumes_outcome_from"] = desired
                    changed = True
            else:
                if "consumes_outcome_from" in scene:
                    scene.pop("consumes_outcome_from", None)
                    changed = True
        elif not consumes and prev_ref:
            scene["consumes_outcome_from"] = prev_ref
            changed = True

        hands_off_to = str(scene.get("hands_off_to") or "").strip()
        if next_ref is None or str(scene.get("handoff_mode") or "").strip() == "terminal":
            if "hands_off_to" in scene:
                scene.pop("hands_off_to", None)
                changed = True
        elif hands_off_to.startswith(f"{chapter_id}:"):
            mapped = old_to_new.get(hands_off_to)
            desired = mapped or next_ref
            if hands_off_to != desired:
                scene["hands_off_to"] = desired
                changed = True
        elif not hands_off_to:
            scene["hands_off_to"] = next_ref
            changed = True

        if _to_int(scene.get("scene_id")) != index + 1:
            scene["scene_id"] = index + 1
            changed = True
        if current_ref != f"{chapter_id}:{index + 1}":
            changed = True

    sections = outline_chapter.get("sections") if isinstance(outline_chapter.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = _to_int(section.get("section_id"))
        if section_id is None:
            continue
        registry_section = _find_registry_section(registry, chapter_id, section_id)
        status = str(registry_section.get("status") or section.get("status") or "stub").strip().lower()
        scene_start, scene_end = _section_scene_range(section)
        if status in {"frozen", "locked"} and scene_start is not None and scene_end is not None:
            registry_section["scene_ref_start"] = f"{chapter_id}:{scene_start}"
            registry_section["scene_ref_end"] = f"{chapter_id}:{scene_end}"
            boundary_path = _emit_boundary_artifact(book_root, outline, chapter_id, section_id)
            registry_section["boundary_artifact"] = _registry_relpath(book_root, boundary_path)
        elif status == "stub":
            registry_section["scene_ref_start"] = None
            registry_section["scene_ref_end"] = None
            registry_section["boundary_artifact"] = None

    chapter["chapter_status"] = str(chapter.get("chapter_status") or "in_progress").strip() or "in_progress"
    return changed


def _section_boundary_path(book_root: Path, chapter_id: int, section_id: int) -> Path:
    return _outline_dir(book_root) / "boundaries" / f"ch_{chapter_id:03d}_sec_{section_id:03d}_boundary.json"


def _emit_boundary_artifact(book_root: Path, outline: Dict[str, Any], chapter_id: int, section_id: int) -> Path:
    section = _find_outline_section(outline, chapter_id, section_id)
    scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
    if not scenes:
        raise ValueError(f"Cannot emit boundary artifact for empty section {chapter_id}:{section_id}")
    terminal_scene = None
    terminal_scene_id = None
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        try:
            scene_id = int(scene.get("scene_id"))
        except (TypeError, ValueError):
            continue
        if terminal_scene_id is None or scene_id > terminal_scene_id:
            terminal_scene_id = scene_id
            terminal_scene = scene
    if not isinstance(terminal_scene, dict) or terminal_scene_id is None:
        raise ValueError(f"Unable to resolve terminal scene for section {chapter_id}:{section_id}")
    payload = {
        "schema_version": "section_boundary_seam_v1",
        "chapter_id": chapter_id,
        "section_id": section_id,
        "chunk_ref": f"ch{chapter_id:03d}:sec{section_id:03d}",
        "terminal_scene_ref": f"{chapter_id}:{terminal_scene_id}",
        "transition_out_text": str(terminal_scene.get("transition_out_text") or "").strip(),
        "transition_out_anchors": list(
            terminal_scene.get("transition_out_anchors")
            if isinstance(terminal_scene.get("transition_out_anchors"), list)
            else []
        ),
        "location_end": str(
            terminal_scene.get("location_end_label")
            or terminal_scene.get("location_end")
            or ""
        ).strip(),
        "constraint_state": str(terminal_scene.get("constraint_state") or "").strip(),
        "handoff_mode": str(terminal_scene.get("handoff_mode") or "").strip(),
        "active_thread_ids": list(terminal_scene.get("threads") if isinstance(terminal_scene.get("threads"), list) else []),
        "newly_hot_entity_ids": list(
            terminal_scene.get("introduces") if isinstance(terminal_scene.get("introduces"), list) else []
        ),
        "updated_at": _now_iso(),
    }
    path = _section_boundary_path(book_root, chapter_id, section_id)
    return _write_json(path, payload)


def _registry_relpath(book_root: Path, path: Path) -> str:
    return path.relative_to(book_root).as_posix()


def _normalize_artifact_paths(book_root: Path, artifact_paths: Optional[Dict[str, Any]]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for key, value in dict(artifact_paths or {}).items():
        name = str(key or "").strip()
        if not name or value is None:
            continue
        if isinstance(value, Path):
            try:
                normalized[name] = _registry_relpath(book_root, value)
            except ValueError:
                normalized[name] = value.as_posix()
            continue
        text = str(value).strip()
        if text:
            normalized[name] = text
    return normalized


def _emit_section_workflow_contracts(
    *,
    workspace: Path,
    book_id: str,
    book_root: Path,
    before_snapshot,
    action: str,
    result_status: str,
    message: str,
    artifact_paths: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> None:
    emit_reconciled_main_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        before_snapshot=before_snapshot,
        action=action,
        result_status=result_status,
        message=message,
        artifact_paths=_normalize_artifact_paths(book_root, artifact_paths),
        details=dict(details or {}),
        request_id=request_id,
    )


def _rebuild_views(book_root: Path, outline: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Path]:
    outline_dir = _outline_dir(book_root)
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    registry_chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    registry_map: Dict[Tuple[int, int], Dict[str, Any]] = {}
    chapter_registry_map: Dict[int, Dict[str, Any]] = {}
    for chapter in registry_chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        chapter_registry_map[chapter_id] = chapter
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            try:
                section_id = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            registry_map[(chapter_id, section_id)] = section

    thin_chapters: List[Dict[str, Any]] = []
    toc_chapters: List[Dict[str, Any]] = []
    index_sections: List[Dict[str, Any]] = []
    appendix_sections: List[Dict[str, Any]] = []
    appendix_chapters: List[Dict[str, Any]] = []

    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        registry_chapter = chapter_registry_map.get(chapter_id, {})
        chapter_sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        thin_sections: List[Dict[str, Any]] = []
        toc_sections: List[Dict[str, Any]] = []
        for section in chapter_sections:
            if not isinstance(section, dict):
                continue
            try:
                section_id = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            registry_section = registry_map.get((chapter_id, section_id), {})
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            scene_start, scene_end = _section_scene_range(section)
            thin_sections.append(
                {
                    "section_id": section_id,
                    "title": str(section.get("title") or "").strip(),
                    "intent": str(section.get("intent") or "").strip(),
                    "end_condition": str(section.get("end_condition") or "").strip(),
                    "status": str(registry_section.get("status") or section.get("status") or "stub").strip(),
                    "target_scene_count": int(section.get("target_scene_count") or 0),
                    "scene_count": len([item for item in scenes if isinstance(item, dict)]),
                    "scene_ref_start": f"{chapter_id}:{scene_start}" if scene_start is not None else None,
                    "scene_ref_end": f"{chapter_id}:{scene_end}" if scene_end is not None else None,
                }
            )
            toc_sections.append(
                {
                    "section_id": section_id,
                    "title": str(section.get("title") or "").strip(),
                    "status": str(registry_section.get("status") or section.get("status") or "stub").strip(),
                    "target_scene_count": int(section.get("target_scene_count") or 0),
                    "scene_count": len([item for item in scenes if isinstance(item, dict)]),
                    "scene_ref_start": f"{chapter_id}:{scene_start}" if scene_start is not None else None,
                    "scene_ref_end": f"{chapter_id}:{scene_end}" if scene_end is not None else None,
                    "boundary_artifact": registry_section.get("boundary_artifact"),
                }
            )
            index_sections.append(
                {
                    "chapter_id": chapter_id,
                    "section_id": section_id,
                    "status": str(registry_section.get("status") or section.get("status") or "stub").strip(),
                    "scene_ref_start": f"{chapter_id}:{scene_start}" if scene_start is not None else None,
                    "scene_ref_end": f"{chapter_id}:{scene_end}" if scene_end is not None else None,
                    "boundary_artifact": registry_section.get("boundary_artifact"),
                }
            )
            appendix_sections.append(
                {
                    "chapter_id": chapter_id,
                    "section_id": section_id,
                    "status": str(registry_section.get("status") or section.get("status") or "stub").strip(),
                    "freeze_lock_audit": {
                        "scene_ref_start": f"{chapter_id}:{scene_start}" if scene_start is not None else None,
                        "scene_ref_end": f"{chapter_id}:{scene_end}" if scene_end is not None else None,
                    },
                    "boundary_artifact": registry_section.get("boundary_artifact"),
                }
            )
        thin_chapters.append(
            {
                "chapter_id": chapter_id,
                "title": str(chapter.get("title") or "").strip(),
                "goal": str(chapter.get("goal") or "").strip(),
                "chapter_status": str(registry_chapter.get("chapter_status") or "in_progress").strip(),
                "sections": thin_sections,
            }
        )
        toc_chapters.append(
            {
                "chapter_id": chapter_id,
                "title": str(chapter.get("title") or "").strip(),
                "chapter_status": str(registry_chapter.get("chapter_status") or "in_progress").strip(),
                "chapter_seam_report": registry_chapter.get("chapter_seam_report"),
                "chapter_original_markdown": registry_chapter.get("chapter_original_markdown"),
                "chapter_fixed_markdown": registry_chapter.get("chapter_fixed_markdown"),
                "chapter_final_markdown": registry_chapter.get("chapter_final_markdown"),
                "sections": toc_sections,
            }
        )
        appendix_chapters.append(
            {
                "chapter_id": chapter_id,
                "chapter_status": str(registry_chapter.get("chapter_status") or "in_progress").strip(),
                "chapter_seam_report": registry_chapter.get("chapter_seam_report"),
                "chapter_original_markdown": registry_chapter.get("chapter_original_markdown"),
                "chapter_fixed_markdown": registry_chapter.get("chapter_fixed_markdown"),
                "chapter_provisional_markdown": registry_chapter.get("chapter_provisional_markdown"),
                "chapter_final_markdown": registry_chapter.get("chapter_final_markdown"),
                "chapter_candidate_markdown": registry_chapter.get("chapter_candidate_markdown"),
            }
        )

    thin_payload = {
        "schema_version": "outline_thin_v1",
        "book_id": book_root.name,
        "updated_at": _now_iso(),
        "chapters": thin_chapters,
    }
    toc_payload = {
        "schema_version": "outline_toc_v1",
        "book_id": book_root.name,
        "updated_at": _now_iso(),
        "chapters": toc_chapters,
    }
    index_payload = {
        "schema_version": "outline_index_v1",
        "book_id": book_root.name,
        "updated_at": _now_iso(),
        "sections": index_sections,
        "registry_path": "outline/snapshot_registry.json",
    }
    appendix_payload = {
        "schema_version": "outline_appendix_v1",
        "book_id": book_root.name,
        "updated_at": _now_iso(),
        "report_pointers": {
            "outline_pipeline_latest": "outline/outline_pipeline_report_latest.json",
            "snapshot_registry": "outline/snapshot_registry.json",
        },
        "chapters": appendix_chapters,
        "sections": appendix_sections,
    }
    return {
        "thin": _write_json(outline_dir / THIN_FILENAME, thin_payload),
        "toc": _write_json(outline_dir / TOC_FILENAME, toc_payload),
        "index": _write_json(outline_dir / INDEX_FILENAME, index_payload),
        "appendix": _write_json(outline_dir / APPENDIX_FILENAME, appendix_payload),
    }


def _load_workflow_state(book_root: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    outline_path = _outline_dir(book_root) / "outline.json"
    registry_path = _outline_dir(book_root) / REGISTRY_FILENAME
    if not outline_path.exists():
        raise FileNotFoundError(f"Missing canonical outline: {outline_path}")
    if not registry_path.exists():
        raise FileNotFoundError(f"Missing snapshot registry: {registry_path}")
    return _read_json(outline_path), _read_json(registry_path)


def _write_workflow_state(book_root: Path, outline: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Path]:
    outline_dir = _outline_dir(book_root)
    registry["updated_at"] = _now_iso()
    outline_path = _write_json(outline_dir / "outline.json", outline)
    registry_path = _write_json(outline_dir / REGISTRY_FILENAME, registry)
    characters = outline.get("characters") if isinstance(outline.get("characters"), list) else []
    if characters:
        _write_json(outline_dir / "characters.json", {"characters": characters})
    view_paths = _rebuild_views(book_root, outline, registry)
    result = {"outline": outline_path, "registry": registry_path}
    result.update(view_paths)
    return result


def _clear_workflow_generated_artifacts(book_root: Path) -> None:
    outline_dir = _outline_dir(book_root)
    for path in (
        outline_dir / SECTION_DRAFT_DIRNAME,
        outline_dir / "boundaries",
        book_root / "runtime" / "supervision",
    ):
        if path.exists():
            shutil.rmtree(path)


def _ensure_state_initialized(book_root: Path, outline_exists: bool) -> None:
    state_path = book_root / "state.json"
    if not state_path.exists():
        return
    state = _read_json(state_path)
    if outline_exists:
        state["status"] = "OUTLINED"
    _write_json(state_path, state)


def initialize_section_workflow(
    workspace: Path,
    book_id: str,
    run_id: Optional[str] = None,
    overwrite: bool = False,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    before_snapshot = capture_main_branch_snapshot(workspace, book_id)
    book_root = _book_root(workspace, book_id)
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")
    outline_dir = _outline_dir(book_root)
    outline_path = outline_dir / "outline.json"
    registry_path = outline_dir / REGISTRY_FILENAME
    resolved_run_id, run_dir = _pipeline_run_dir(book_root, run_id)
    if outline_path.exists() and registry_path.exists() and not overwrite:
        outline, registry = _load_workflow_state(book_root)
        _validate_workflow_source_alignment(
            run_dir=run_dir,
            resolved_run_id=resolved_run_id,
            outline=outline,
            registry=registry,
        )
        views = _rebuild_views(book_root, outline, registry)
        result = {
            "book_id": book_id,
            "run_id": resolved_run_id,
            "outline_path": outline_path,
            "registry_path": registry_path,
            "views": {key: str(path) for key, path in views.items()},
            "initialized": False,
        }
        _emit_section_workflow_contracts(
            workspace=workspace,
            book_id=book_id,
            book_root=book_root,
            before_snapshot=before_snapshot,
            action="initialize_section_workflow",
            result_status="no_op",
            message=f"Section workflow already initialized for source run {resolved_run_id}.",
            artifact_paths={
                "outline": outline_path,
                "registry": registry_path,
                "thin": views.get("thin"),
                "toc": views.get("toc"),
                "index": views.get("index"),
                "appendix": views.get("appendix"),
            },
            details={"run_id": resolved_run_id, "initialized": False},
            request_id=request_id,
        )
        return result

    if overwrite:
        _clear_workflow_generated_artifacts(book_root)

    spine, sections = _load_spine_and_sections(run_dir)
    characters, threads = _collect_outline_registries(run_dir)
    outline = _build_canonical_outline(spine, sections, characters, threads)
    registry = _build_snapshot_registry(book_id, resolved_run_id, outline)
    paths = _write_workflow_state(book_root, outline, registry)
    _ensure_state_initialized(book_root, outline_exists=True)
    result = {
        "book_id": book_id,
        "run_id": resolved_run_id,
        "outline_path": str(paths["outline"]),
        "registry_path": str(paths["registry"]),
        "views": {key: str(path) for key, path in paths.items() if key in {"thin", "toc", "index", "appendix"}},
        "initialized": True,
    }
    _emit_section_workflow_contracts(
        workspace=workspace,
        book_id=book_id,
        book_root=book_root,
        before_snapshot=before_snapshot,
        action="initialize_section_workflow",
        result_status="success",
        message=f"Section workflow initialized from source run {resolved_run_id}.",
        artifact_paths=paths,
        details={"run_id": resolved_run_id, "initialized": True},
        request_id=request_id,
    )
    return result


def _ensure_initialized(
    workspace: Path,
    book_id: str,
    run_id: Optional[str] = None,
) -> Tuple[Path, str, Path, Dict[str, Any], Dict[str, Any]]:
    book_root = _book_root(workspace, book_id)
    outline_path = _outline_dir(book_root) / "outline.json"
    registry_path = _outline_dir(book_root) / REGISTRY_FILENAME
    if not outline_path.exists() or not registry_path.exists():
        initialize_section_workflow(workspace=workspace, book_id=book_id, run_id=run_id, overwrite=False)
    resolved_run_id, run_dir = _pipeline_run_dir(book_root, run_id)
    outline, registry = _load_workflow_state(book_root)
    _validate_workflow_source_alignment(
        run_dir=run_dir,
        resolved_run_id=resolved_run_id,
        outline=outline,
        registry=registry,
    )
    return book_root, resolved_run_id, run_dir, outline, registry


def _find_phase03_section(run_dir: Path, chapter_id: int, section_id: int) -> Dict[str, Any]:
    artifact = run_dir / f"phase_03_scene_draft_chapter_{chapter_id:03d}_output.json"
    candidate_payloads: List[Dict[str, Any]] = []
    if artifact.exists():
        candidate_payloads.append(_read_json(artifact))

    for fallback_name in [
        "outline_final_v1_1.json",
        "outline_cast_refined_v1_1.json",
        "outline_seams_hygiened_v1_1.json",
        "outline_handoff_normalized_v1_1.json",
        "outline_draft_v1_1.json",
    ]:
        fallback_path = run_dir / fallback_name
        if fallback_path.exists():
            candidate_payloads.append(_read_json(fallback_path))

    for payload in candidate_payloads:
        chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            try:
                current_chapter_id = int(chapter.get("chapter_id"))
            except (TypeError, ValueError):
                continue
            if current_chapter_id != chapter_id:
                continue
            sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
            for section in sections:
                if not isinstance(section, dict):
                    continue
                try:
                    current_section_id = int(section.get("section_id"))
                except (TypeError, ValueError):
                    continue
                if current_section_id == section_id:
                    return {"payload": payload, "section": deepcopy(section)}

    raise ValueError(f"Section not found in source run artifacts: {chapter_id}:{section_id}")


def _resolve_source_outline_payload(run_dir: Path) -> Dict[str, Any]:
    for candidate_name in [
        "outline_final_v1_1.json",
        "outline_cast_refined_v1_1.json",
        "outline_seams_hygiened_v1_1.json",
        "outline_handoff_normalized_v1_1.json",
        "outline_draft_v1_1.json",
    ]:
        candidate_path = run_dir / candidate_name
        if candidate_path.exists():
            return _read_json(candidate_path)
    raise FileNotFoundError(f"No source outline payload found in run artifacts: {run_dir}")


def _normalize_section_for_source_compare(section: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for field in ("section_id", "title", "intent", "end_condition", "scenes"):
        if field in section:
            normalized[field] = deepcopy(section.get(field))
    return normalized


def _workflow_section_has_materialized_content(section: Dict[str, Any], registry_section: Dict[str, Any]) -> bool:
    scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
    if scenes:
        return True
    status = str(registry_section.get("status") or section.get("status") or "").strip().lower()
    return status in {"frozen", "locked"}


def _validate_workflow_source_alignment(
    *,
    run_dir: Path,
    resolved_run_id: str,
    outline: Dict[str, Any],
    registry: Dict[str, Any],
) -> None:
    issues: List[str] = []
    source_run_id = str(registry.get("source_run_id") or "").strip()
    if source_run_id and source_run_id != resolved_run_id:
        issues.append(
            "workflow source_run_id="
            + source_run_id
            + f" but requested run_id={resolved_run_id}"
        )

    try:
        source_outline = _resolve_source_outline_payload(run_dir)
    except Exception as exc:
        issues.append(str(exc))
        source_outline = {}

    source_characters = source_outline.get("characters") if isinstance(source_outline.get("characters"), list) else []
    source_character_ids = {
        str(item.get("character_id") or "").strip()
        for item in source_characters
        if isinstance(item, dict) and str(item.get("character_id") or "").strip()
    }
    outline_characters = outline.get("characters") if isinstance(outline.get("characters"), list) else []
    extra_character_ids = sorted(
        {
            str(item.get("character_id") or "").strip()
            for item in outline_characters
            if isinstance(item, dict) and str(item.get("character_id") or "").strip()
        }
        - source_character_ids
    )
    if extra_character_ids:
        issues.append("outline contains character ids not present in source run: " + ", ".join(extra_character_ids))

    source_threads = source_outline.get("threads") if isinstance(source_outline.get("threads"), list) else []
    source_thread_ids = {
        str(item.get("thread_id") or "").strip()
        for item in source_threads
        if isinstance(item, dict) and str(item.get("thread_id") or "").strip()
    }
    outline_threads = outline.get("threads") if isinstance(outline.get("threads"), list) else []
    extra_thread_ids = sorted(
        {
            str(item.get("thread_id") or "").strip()
            for item in outline_threads
            if isinstance(item, dict) and str(item.get("thread_id") or "").strip()
        }
        - source_thread_ids
    )
    if extra_thread_ids:
        issues.append("outline contains thread ids not present in source run: " + ", ".join(extra_thread_ids))

    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id is None:
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for registry_section in sections:
            if not isinstance(registry_section, dict):
                continue
            section_id = _to_int(registry_section.get("section_id"))
            if section_id is None:
                continue
            outline_section = _find_outline_section(outline, chapter_id, section_id)
            if not _workflow_section_has_materialized_content(outline_section, registry_section):
                continue
            source_section = _find_phase03_section(run_dir, chapter_id, section_id)["section"]
            if _normalize_section_for_source_compare(outline_section) != _normalize_section_for_source_compare(source_section):
                issues.append(
                    f"materialized section {chapter_id}:{section_id} does not match source run {resolved_run_id}"
                )

    if issues:
        joined = "; ".join(issues)
        raise ValueError(
            "Workflow/source alignment failure. The workflow outline is forked from its source run. "
            + joined
            + ". Reinitialize with --overwrite from the intended run before advancing sections."
        )


def _section_draft_path(book_root: Path, chapter_id: int, section_id: int) -> Path:
    return _outline_dir(book_root) / SECTION_DRAFT_DIRNAME / f"ch_{chapter_id:03d}_sec_{section_id:03d}_phase03.json"


def _build_section_draft_chapter_input(
    outline: Dict[str, Any],
    chapter_id: int,
    section_id: int,
) -> Dict[str, Any]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    chapter_payload: Dict[str, Any] = {}
    for chapter_entry in chapters:
        if not isinstance(chapter_entry, dict):
            continue
        try:
            current_chapter_id = int(chapter_entry.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current_chapter_id != chapter_id:
            continue
        chapter_payload = deepcopy(chapter_entry)
        break
    if not chapter_payload:
        raise ValueError(f"Chapter not found in outline: {chapter_id}")
    sections = chapter_payload.get("sections") if isinstance(chapter_payload.get("sections"), list) else []
    built_sections: List[Dict[str, Any]] = []
    for section_entry in sections:
        if not isinstance(section_entry, dict):
            continue
        try:
            current_section_id = int(section_entry.get("section_id"))
        except (TypeError, ValueError):
            continue
        copied = deepcopy(section_entry)
        if current_section_id < section_id:
            built_sections.append(copied)
            continue
        if current_section_id == section_id:
            copied["status"] = "draftable"
            built_sections.append(copied)
            continue
        copied["scenes"] = []
        copied["status"] = "stub"
        built_sections.append(copied)
    chapter_payload["sections"] = built_sections
    return {"schema_version": "1.1", "chapters": [chapter_payload]}


def _chapter_slice(outline: Dict[str, Any], chapter_id: int) -> Dict[str, Any]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current_chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current_chapter_id == chapter_id:
            return {"chapters": [deepcopy(chapter)]}
    return {"chapters": []}


def _extract_json_object(text: str, label: str) -> Dict[str, Any]:
    parsed = extract_json(text, label=label)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return parsed


def _phase03_validation_errors(payload: Dict[str, Any], sections_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    handler = get_handler(outline_context.PHASE_03)
    runtime: Dict[str, Any] = {"current_chapter_id": None}
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    if chapters:
        try:
            runtime["current_chapter_id"] = int(chapters[0].get("chapter_id"))
        except (TypeError, ValueError):
            runtime["current_chapter_id"] = None
    settings = {"strict_transition_bridges": True}
    handoffs = {"outline_sections_v1": sections_payload}
    processed_payload, preprocess_errors = handler.preprocess(
        payload,
        handoffs=handoffs,
        settings=settings,
        runtime=runtime,
    )
    validation = handler.validate(
        processed_payload,
        handoffs=handoffs,
        settings=settings,
        runtime=runtime,
    )
    return list(preprocess_errors) + list(validation.errors)


def _section_draft_notes(
    chapter_id: int,
    section_id: int,
    section: Dict[str, Any],
    registry: Dict[str, Any],
) -> str:
    previous_ref = _previous_section_ref(registry, chapter_id, section_id)
    previous_note = "No previous section; this is book opening context."
    if previous_ref is not None:
        prev_section = _find_registry_section(registry, previous_ref[0], previous_ref[1])
        previous_note = (
            f"Previous section {previous_ref[0]}:{previous_ref[1]} is "
            f"{prev_section.get('status')} with terminal ref {prev_section.get('scene_ref_end')}."
        )
    target_scene_count = int(section.get("target_scene_count") or 0)
    return "\n".join(
        [
            f"Active section target: chapter {chapter_id}, section {section_id}.",
            "Draft ONLY the active section's scenes.",
            "Preserve any existing earlier section scenes unchanged.",
            "Leave later sections as stubs with empty scenes arrays.",
            "Return exactly one chapter payload containing the full chapter shape.",
            previous_note,
            f"The active section target_scene_count is {target_scene_count}.",
            "Scene ids must remain chapter-local and monotonic across the chapter.",
        ]
    )


def _draft_section_with_phase03(
    workspace: Path,
    book_id: str,
    book_root: Path,
    run_dir: Path,
    outline: Dict[str, Any],
    registry: Dict[str, Any],
    chapter_id: int,
    section_id: int,
) -> Dict[str, Any]:
    sections_payload = _read_json(run_dir / "outline_sections_v1.json")
    chapter_input_outline = _build_section_draft_chapter_input(outline, chapter_id, section_id)
    previous_chapter_outline = _chapter_slice(outline, chapter_id - 1) if chapter_id > 1 else {}
    next_chapter_outline = _chapter_slice(outline, chapter_id + 1)
    book_payload = _read_json(book_root / "book.json")
    targets = deepcopy(book_payload.get("targets") if isinstance(book_payload.get("targets"), dict) else {})
    active_section = _find_outline_section(outline, chapter_id, section_id)
    notes = _section_draft_notes(chapter_id, section_id, active_section, registry)

    template_path = outline_context.resolve_outline_template(book_root, "outline_phase_03_scene_draft.md")
    render_values = {
        "book": book_payload,
        "targets": targets,
        "notes": notes,
        "user_prompt": "",
        "transition_hints": {"hints": []},
        "scene_count_policy": outline_context.build_scene_count_policy(
            exact_scene_count=False,
            scene_count_range=None,
        ),
        "chapter_target_id": chapter_id,
        "chapter_input_outline": chapter_input_outline,
        "chapter_prev_outline": previous_chapter_outline,
        "chapter_next_outline": next_chapter_outline,
    }
    prompt = render_template_file(template_path, render_values)
    system_prompt = (book_root / "prompts" / "system_v1.md").read_text(encoding="utf-8")

    config = load_config()
    client = get_llm_client(config, phase="outline")
    model = resolve_model("outline", config)
    provider_name = str(getattr(client, "provider", "")).lower()
    base_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    t1_max_tokens = 1024
    t1_assistant_parts: Optional[List[Dict[str, Any]]] = None
    t1_messages = list(base_messages)
    t1_messages.append({"role": "user", "content": PHASE03_T1_INSTRUCTION})
    try:
        t1_response = client.chat(t1_messages, model=model, temperature=0.2, max_tokens=t1_max_tokens)
    except LLMRequestError as exc:
        if should_log_llm():
            log_llm_error(
                workspace,
                "workflow_section_phase03_t1_error",
                exc,
                request={"model": model, "temperature": 0.2, "max_tokens": t1_max_tokens},
                messages=t1_messages,
                extra={"book_id": book_id, "chapter": chapter_id, "section_id": section_id, "phase_id": "workflow_section_phase03", "turn_id": "T1"},
            )
        raise
    if should_log_llm():
        log_llm_response(
            workspace,
            "workflow_section_phase03_t1",
            t1_response,
            request={"model": model, "temperature": 0.2, "max_tokens": t1_max_tokens},
            messages=t1_messages,
            extra={"book_id": book_id, "chapter": chapter_id, "section_id": section_id, "phase_id": "workflow_section_phase03", "turn_id": "T1"},
        )
    try:
        _extract_json_object(t1_response.text, "workflow_section_phase03_t1")
        if isinstance(t1_response.assistant_parts, list):
            t1_assistant_parts = t1_response.assistant_parts
    except Exception:
        t1_assistant_parts = None

    retry_message: Optional[str] = None
    for attempt in range(2):
        t2_messages = list(base_messages)
        if t1_assistant_parts and provider_name == "gemini":
            t2_messages.append({"role": "assistant", "parts": t1_assistant_parts})
        t2_messages.append({"role": "user", "content": PHASE03_T2_INSTRUCTION})
        if retry_message:
            t2_messages.append({"role": "user", "content": retry_message})
        try:
            response = client.chat(t2_messages, model=model, temperature=0.2, max_tokens=65536)
        except LLMRequestError as exc:
            if should_log_llm():
                log_llm_error(
                    workspace,
                    "workflow_section_phase03_error",
                    exc,
                    request={"model": model, "temperature": 0.2, "max_tokens": 65536},
                    messages=t2_messages,
                    extra={"book_id": book_id, "chapter": chapter_id, "section_id": section_id, "phase_id": "workflow_section_phase03", "turn_id": "T2"},
                )
            raise
        if should_log_llm():
            log_llm_response(
                workspace,
                "workflow_section_phase03",
                response,
                request={"model": model, "temperature": 0.2, "max_tokens": 65536},
                messages=t2_messages,
                extra={"book_id": book_id, "chapter": chapter_id, "section_id": section_id, "phase_id": "workflow_section_phase03", "turn_id": "T2", "attempt": attempt + 1},
            )
        parsed = _extract_json_object(response.text, "workflow_section_phase03")
        errors = _phase03_validation_errors(parsed, sections_payload)
        if not errors:
            _write_json(_section_draft_path(book_root, chapter_id, section_id), parsed)
            return parsed
        lines = [
            "Your previous section draft failed deterministic validation.",
            "Return ONLY a corrected single JSON object for the chapter.",
            "Fix these issues:",
        ]
        for item in errors[:12]:
            code = str(item.get("code") or "validation_error")
            message = str(item.get("message") or "")
            scene_ref = str(item.get("scene_ref") or "").strip()
            path = str(item.get("path") or "").strip()
            context = scene_ref or path
            if context:
                lines.append(f"- [{code}] {context}: {message}")
            else:
                lines.append(f"- [{code}] {message}")
        retry_message = "\n".join(lines)
    raise ValueError(f"Section draft failed validation for {chapter_id}:{section_id}")


def _assert_freeze_preconditions(registry: Dict[str, Any], chapter_id: int, section_id: int) -> None:
    previous_ref = _previous_section_ref(registry, chapter_id, section_id)
    if previous_ref is None:
        return
    prev_section = _find_registry_section(registry, previous_ref[0], previous_ref[1])
    prev_status = str(prev_section.get("status") or "").strip().lower()
    if prev_status not in {"frozen", "locked"}:
        raise ValueError(
            f"Cannot freeze {chapter_id}:{section_id} before predecessor {previous_ref[0]}:{previous_ref[1]} is frozen or locked."
        )


def freeze_section_from_phase03_artifact(
    workspace: Path,
    book_id: str,
    chapter_id: int,
    section_id: int,
    run_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    before_snapshot = capture_main_branch_snapshot(workspace, book_id)
    book_root, resolved_run_id, run_dir, outline, registry = _ensure_initialized(
        workspace=workspace,
        book_id=book_id,
        run_id=run_id,
    )
    _assert_freeze_preconditions(registry, chapter_id, section_id)
    registry_section = _find_registry_section(registry, chapter_id, section_id)
    chapter_changed = _normalize_chapter_scene_graph(
        book_root=book_root,
        outline=outline,
        registry=registry,
        chapter_id=chapter_id,
    )
    current_status = str(registry_section.get("status") or "").strip().lower()
    if current_status == "locked":
        if chapter_changed:
            _write_workflow_state(book_root, outline, registry)
        result = {
            "book_id": book_id,
            "run_id": resolved_run_id,
            "chapter_id": chapter_id,
            "section_id": section_id,
            "status": "locked",
            "scene_ref_start": registry_section.get("scene_ref_start"),
            "scene_ref_end": registry_section.get("scene_ref_end"),
            "boundary_artifact": registry_section.get("boundary_artifact"),
            "updated": chapter_changed,
        }
        _emit_section_workflow_contracts(
            workspace=workspace,
            book_id=book_id,
            book_root=book_root,
            before_snapshot=before_snapshot,
            action="freeze_section_from_phase03_artifact",
            result_status="no_op",
            message=f"Section {chapter_id}:{section_id} is already locked.",
            artifact_paths={"outline": _outline_dir(book_root) / "outline.json", "registry": _outline_dir(book_root) / REGISTRY_FILENAME},
            details={"chapter_id": chapter_id, "section_id": section_id, "status": "locked", "updated": chapter_changed},
            request_id=request_id,
        )
        return result
    if current_status == "frozen":
        if chapter_changed:
            _write_workflow_state(book_root, outline, registry)
        result = {
            "book_id": book_id,
            "run_id": resolved_run_id,
            "chapter_id": chapter_id,
            "section_id": section_id,
            "status": "frozen",
            "scene_ref_start": registry_section.get("scene_ref_start"),
            "scene_ref_end": registry_section.get("scene_ref_end"),
            "boundary_artifact": registry_section.get("boundary_artifact"),
            "updated": chapter_changed,
        }
        _emit_section_workflow_contracts(
            workspace=workspace,
            book_id=book_id,
            book_root=book_root,
            before_snapshot=before_snapshot,
            action="freeze_section_from_phase03_artifact",
            result_status="no_op",
            message=f"Section {chapter_id}:{section_id} is already frozen.",
            artifact_paths={"outline": _outline_dir(book_root) / "outline.json", "registry": _outline_dir(book_root) / REGISTRY_FILENAME},
            details={"chapter_id": chapter_id, "section_id": section_id, "status": "frozen", "updated": chapter_changed},
            request_id=request_id,
        )
        return result

    phase03_payload: Dict[str, Any]
    phase03_section: Dict[str, Any]
    try:
        phase03 = _find_phase03_section(run_dir, chapter_id, section_id)
        phase03_payload = phase03["payload"]
        phase03_section = phase03["section"]
    except Exception:
        phase03_payload = _draft_section_with_phase03(
            workspace=workspace,
            book_id=book_id,
            book_root=book_root,
            run_dir=run_dir,
            outline=outline,
            registry=registry,
            chapter_id=chapter_id,
            section_id=section_id,
        )
        drafted_section = None
        chapters = phase03_payload.get("chapters") if isinstance(phase03_payload.get("chapters"), list) else []
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            try:
                current_chapter_id = int(chapter.get("chapter_id"))
            except (TypeError, ValueError):
                continue
            if current_chapter_id != chapter_id:
                continue
            sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
            for section in sections:
                if not isinstance(section, dict):
                    continue
                try:
                    current_section_id = int(section.get("section_id"))
                except (TypeError, ValueError):
                    continue
                if current_section_id == section_id:
                    drafted_section = deepcopy(section)
                    break
            if drafted_section is not None:
                break
        if drafted_section is None:
            raise ValueError(f"Generated section draft missing target section {chapter_id}:{section_id}")
        phase03_section = drafted_section
    scenes = phase03_section.get("scenes") if isinstance(phase03_section.get("scenes"), list) else []
    if not scenes:
        raise ValueError(f"Cannot freeze empty section {chapter_id}:{section_id}.")

    outline_section = _find_outline_section(outline, chapter_id, section_id)
    outline_section.update(
        {
            "title": str(phase03_section.get("title") or outline_section.get("title") or "").strip(),
            "intent": str(phase03_section.get("intent") or outline_section.get("intent") or "").strip(),
            "end_condition": str(
                phase03_section.get("end_condition") or outline_section.get("end_condition") or ""
            ).strip(),
            "status": "frozen",
            "scenes": scenes,
        }
    )
    outline["characters"] = _merge_registry_items(
        list(outline.get("characters") if isinstance(outline.get("characters"), list) else []),
        list(phase03_payload.get("characters") if isinstance(phase03_payload.get("characters"), list) else []),
        "character_id",
    )
    outline["threads"] = _merge_registry_items(
        list(outline.get("threads") if isinstance(outline.get("threads"), list) else []),
        list(phase03_payload.get("threads") if isinstance(phase03_payload.get("threads"), list) else []),
        "thread_id",
    )
    _normalize_chapter_scene_graph(
        book_root=book_root,
        outline=outline,
        registry=registry,
        chapter_id=chapter_id,
    )

    scene_start, scene_end = _section_scene_range(outline_section)
    if scene_start is None or scene_end is None:
        raise ValueError(f"Unable to derive scene range for section {chapter_id}:{section_id}")

    boundary_path = _emit_boundary_artifact(book_root, outline, chapter_id, section_id)
    registry_section["status"] = "frozen"
    registry_section["scene_ref_start"] = f"{chapter_id}:{scene_start}"
    registry_section["scene_ref_end"] = f"{chapter_id}:{scene_end}"
    registry_section["boundary_artifact"] = _registry_relpath(book_root, boundary_path)
    registry["active_section"] = {"chapter_id": chapter_id, "section_id": section_id, "status": "frozen"}

    state_path = book_root / "state.json"
    if state_path.exists():
        state = _read_json(state_path)
        cursor = state.get("cursor") if isinstance(state.get("cursor"), dict) else {}
        current_chapter = int(cursor.get("chapter", 0) or 0)
        current_scene = int(cursor.get("scene", 0) or 0)
        if current_chapter <= 0 or current_scene <= 0:
            state["cursor"] = {"chapter": chapter_id, "scene": scene_start}
        state["status"] = "OUTLINED"
        _write_json(state_path, state)

    paths = _write_workflow_state(book_root, outline, registry)
    result = {
        "book_id": book_id,
        "run_id": resolved_run_id,
        "chapter_id": chapter_id,
        "section_id": section_id,
        "status": "frozen",
        "scene_ref_start": registry_section["scene_ref_start"],
        "scene_ref_end": registry_section["scene_ref_end"],
        "boundary_artifact": registry_section["boundary_artifact"],
        "outline_path": str(paths["outline"]),
        "updated": True,
    }
    _emit_section_workflow_contracts(
        workspace=workspace,
        book_id=book_id,
        book_root=book_root,
        before_snapshot=before_snapshot,
        action="freeze_section_from_phase03_artifact",
        result_status="success",
        message=f"Section {chapter_id}:{section_id} frozen from source run {resolved_run_id}.",
        artifact_paths={"outline": paths["outline"], "registry": paths["registry"], "boundary_artifact": boundary_path},
        details={"chapter_id": chapter_id, "section_id": section_id, "run_id": resolved_run_id, "status": "frozen"},
        request_id=request_id,
    )
    return result


def _next_cursor_after_section(registry: Dict[str, Any], chapter_id: int, section_id: int, scene_end: int) -> Tuple[int, int]:
    next_ref = _next_section_ref(registry, chapter_id, section_id)
    if next_ref is None:
        return chapter_id + 1, 1
    next_chapter, _ = next_ref
    if next_chapter == chapter_id:
        return chapter_id, scene_end + 1
    return next_chapter, 1


def _chapter_all_sections_locked(registry: Dict[str, Any], chapter_id: int) -> bool:
    chapter = _find_registry_chapter(registry, chapter_id)
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    seen = False
    for section in sections:
        if not isinstance(section, dict):
            continue
        seen = True
        if str(section.get("status") or "").strip().lower() != "locked":
            return False
    return seen


def _workflow_is_complete(registry: Dict[str, Any]) -> bool:
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    saw_chapter = False
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        saw_chapter = True
        if str(chapter.get("chapter_status") or "").strip().lower() != "finalized":
            return False
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        saw_section = False
        for section in sections:
            if not isinstance(section, dict):
                continue
            saw_section = True
            if str(section.get("status") or "").strip().lower() != "locked":
                return False
        if not saw_section:
            return False
    return saw_chapter


def _update_chapter_finalization_fields(
    registry: Dict[str, Any],
    chapter_id: int,
    chapter_finalization: Dict[str, Any],
) -> None:
    registry_chapter = _find_registry_chapter(registry, chapter_id)
    registry_chapter["chapter_status"] = str(chapter_finalization.get("status") or "attention_required").strip()
    registry_chapter["chapter_seam_report"] = chapter_finalization.get("report_path")
    registry_chapter["chapter_original_markdown"] = chapter_finalization.get("original_path")
    registry_chapter["chapter_fixed_markdown"] = chapter_finalization.get("fixed_path")
    registry_chapter["chapter_provisional_markdown"] = chapter_finalization.get("provisional_path")
    registry_chapter["chapter_final_markdown"] = chapter_finalization.get("final_path")
    registry_chapter["chapter_candidate_markdown"] = chapter_finalization.get("candidate_path")


def finalize_chapter_from_locked_sections(
    workspace: Path,
    book_id: str,
    chapter_id: int,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    before_snapshot = capture_main_branch_snapshot(workspace, book_id)
    book_root, _, _, outline, registry = _ensure_initialized(workspace=workspace, book_id=book_id, run_id=None)
    if not _chapter_all_sections_locked(registry, chapter_id):
        raise ValueError(f"Chapter {chapter_id} is not ready for finalization; all sections must be locked first.")
    registry_chapter = _find_registry_chapter(registry, chapter_id)
    if (
        str(registry_chapter.get("chapter_status") or "").strip().lower() == "finalized"
        and str(registry_chapter.get("chapter_final_markdown") or "").strip()
    ):
        _emit_section_workflow_contracts(
            workspace=workspace,
            book_id=book_id,
            book_root=book_root,
            before_snapshot=before_snapshot,
            action="finalize_chapter_from_locked_sections",
            result_status="no_op",
            message=f"Chapter {chapter_id} is already finalized.",
            artifact_paths={
                "outline": _outline_dir(book_root) / "outline.json",
                "registry": _outline_dir(book_root) / REGISTRY_FILENAME,
                "chapter_seam_report": registry_chapter.get("chapter_seam_report"),
                "chapter_original_markdown": registry_chapter.get("chapter_original_markdown"),
                "chapter_fixed_markdown": registry_chapter.get("chapter_fixed_markdown"),
                "chapter_candidate_markdown": registry_chapter.get("chapter_candidate_markdown"),
                "chapter_final_markdown": registry_chapter.get("chapter_final_markdown"),
            },
            details={"chapter_id": chapter_id, "status": registry_chapter.get("chapter_status")},
            request_id=request_id,
        )
        return {
            "status": registry_chapter.get("chapter_status"),
            "report_path": registry_chapter.get("chapter_seam_report"),
            "original_path": registry_chapter.get("chapter_original_markdown"),
            "fixed_path": registry_chapter.get("chapter_fixed_markdown"),
            "provisional_path": registry_chapter.get("chapter_provisional_markdown"),
            "candidate_path": registry_chapter.get("chapter_candidate_markdown"),
            "final_path": registry_chapter.get("chapter_final_markdown"),
            "updated": False,
        }
    chapter_finalization = finalize_locked_chapter(book_root, outline, chapter_id)
    _update_chapter_finalization_fields(registry, chapter_id, chapter_finalization)
    state_path = book_root / "state.json"
    if state_path.exists():
        state = _read_json(state_path)
        if _workflow_is_complete(registry):
            state["status"] = "COMPLETE"
            _write_json(state_path, state)
    paths = _write_workflow_state(book_root, outline, registry)
    result = dict(chapter_finalization)
    result["outline_path"] = str(paths["outline"])
    result["registry_path"] = str(paths["registry"])
    _emit_section_workflow_contracts(
        workspace=workspace,
        book_id=book_id,
        book_root=book_root,
        before_snapshot=before_snapshot,
        action="finalize_chapter_from_locked_sections",
        result_status="success",
        message=f"Chapter {chapter_id} finalized from locked sections.",
        artifact_paths={
            "outline": paths["outline"],
            "registry": paths["registry"],
            "chapter_seam_report": chapter_finalization.get("report_path"),
            "chapter_original_markdown": chapter_finalization.get("original_path"),
            "chapter_fixed_markdown": chapter_finalization.get("fixed_path"),
            "chapter_candidate_markdown": chapter_finalization.get("candidate_path"),
            "chapter_final_markdown": chapter_finalization.get("final_path"),
        },
        details={"chapter_id": chapter_id, "status": chapter_finalization.get("status")},
        request_id=request_id,
    )
    return result


def lock_section_from_written_state(
    workspace: Path,
    book_id: str,
    chapter_id: int,
    section_id: int,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    before_snapshot = capture_main_branch_snapshot(workspace, book_id)
    book_root, _, _, outline, registry = _ensure_initialized(workspace=workspace, book_id=book_id, run_id=None)
    registry_section = _find_registry_section(registry, chapter_id, section_id)
    outline_section = _find_outline_section(outline, chapter_id, section_id)
    status = str(registry_section.get("status") or "").strip().lower()
    if status == "locked":
        result = {
            "book_id": book_id,
            "chapter_id": chapter_id,
            "section_id": section_id,
            "status": "locked",
            "scene_ref_start": registry_section.get("scene_ref_start"),
            "scene_ref_end": registry_section.get("scene_ref_end"),
            "updated": False,
        }
        _emit_section_workflow_contracts(
            workspace=workspace,
            book_id=book_id,
            book_root=book_root,
            before_snapshot=before_snapshot,
            action="lock_section_from_written_state",
            result_status="no_op",
            message=f"Section {chapter_id}:{section_id} is already locked.",
            artifact_paths={"outline": _outline_dir(book_root) / "outline.json", "registry": _outline_dir(book_root) / REGISTRY_FILENAME},
            details={"chapter_id": chapter_id, "section_id": section_id, "status": "locked"},
            request_id=request_id,
        )
        return result
    if status != "frozen":
        raise ValueError(f"Section {chapter_id}:{section_id} must be frozen before it can be locked.")
    scenes = outline_section.get("scenes") if isinstance(outline_section.get("scenes"), list) else []
    if not scenes:
        raise ValueError(f"Cannot lock empty section {chapter_id}:{section_id}.")
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
    scene_ids: List[int] = []
    missing: List[str] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        try:
            scene_id = int(scene.get("scene_id"))
        except (TypeError, ValueError):
            continue
        scene_ids.append(scene_id)
        prose_path = chapter_dir / f"scene_{scene_id:03d}.md"
        meta_path = chapter_dir / f"scene_{scene_id:03d}.meta.json"
        if not prose_path.exists():
            missing.append(str(prose_path))
        if not meta_path.exists():
            missing.append(str(meta_path))
    if missing:
        raise FileNotFoundError("Cannot lock section; missing generated artifacts:\n" + "\n".join(missing))
    scene_start = min(scene_ids)
    scene_end = max(scene_ids)
    outline_section["status"] = "locked"
    registry_section["status"] = "locked"
    registry["active_section"] = None
    registry_chapter = _find_registry_chapter(registry, chapter_id)
    registry_chapter["chapter_status"] = "in_progress"
    registry_chapter["chapter_seam_report"] = None
    registry_chapter["chapter_original_markdown"] = None
    registry_chapter["chapter_fixed_markdown"] = None
    registry_chapter["chapter_provisional_markdown"] = None
    registry_chapter["chapter_final_markdown"] = None
    registry_chapter["chapter_candidate_markdown"] = None

    chapter_finalization: Optional[Dict[str, Any]] = None
    if _chapter_all_sections_locked(registry, chapter_id):
        chapter_finalization = finalize_locked_chapter(book_root, outline, chapter_id)
        _update_chapter_finalization_fields(registry, chapter_id, chapter_finalization)
    state_path = book_root / "state.json"
    if state_path.exists():
        state = _read_json(state_path)
        next_chapter, next_scene = _next_cursor_after_section(registry, chapter_id, section_id, scene_end)
        state["cursor"] = {"chapter": next_chapter, "scene": next_scene}
        state["status"] = "COMPLETE" if _workflow_is_complete(registry) else "OUTLINED"
        _write_json(state_path, state)
    paths = _write_workflow_state(book_root, outline, registry)
    result = {
        "book_id": book_id,
        "chapter_id": chapter_id,
        "section_id": section_id,
        "status": "locked",
        "scene_ref_start": f"{chapter_id}:{scene_start}",
        "scene_ref_end": f"{chapter_id}:{scene_end}",
        "outline_path": str(paths["outline"]),
        "chapter_finalization": chapter_finalization,
        "updated": True,
    }
    _emit_section_workflow_contracts(
        workspace=workspace,
        book_id=book_id,
        book_root=book_root,
        before_snapshot=before_snapshot,
        action="lock_section_from_written_state",
        result_status="success",
        message=f"Section {chapter_id}:{section_id} locked from written scene state.",
        artifact_paths={
            "outline": paths["outline"],
            "registry": paths["registry"],
            "chapter_seam_report": chapter_finalization.get("report_path") if isinstance(chapter_finalization, dict) else None,
            "chapter_final_markdown": chapter_finalization.get("final_path") if isinstance(chapter_finalization, dict) else None,
        },
        details={"chapter_id": chapter_id, "section_id": section_id, "status": "locked"},
        request_id=request_id,
    )
    return result


def get_section_workflow_status(
    workspace: Path,
    book_id: str,
) -> Dict[str, Any]:
    book_root = _book_root(workspace, book_id)
    outline, registry = _load_workflow_state(book_root)
    state_path = book_root / "state.json"
    state = _read_json(state_path) if state_path.exists() else {}
    chapters_summary: List[Dict[str, Any]] = []
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        section_rows: List[Dict[str, Any]] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            try:
                section_id = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            registry_section = _find_registry_section(registry, chapter_id, section_id)
            section_rows.append(
                {
                    "section_id": section_id,
                    "title": str(section.get("title") or "").strip(),
                    "status": str(registry_section.get("status") or section.get("status") or "stub").strip(),
                    "scene_ref_start": registry_section.get("scene_ref_start"),
                    "scene_ref_end": registry_section.get("scene_ref_end"),
                    "boundary_artifact": registry_section.get("boundary_artifact"),
                }
            )
        chapters_summary.append({"chapter_id": chapter_id, "title": str(chapter.get("title") or "").strip(), "sections": section_rows})
    return {
        "book_id": book_id,
        "cursor": state.get("cursor"),
        "state_status": state.get("status"),
        "active_section": registry.get("active_section"),
        "source_run_id": registry.get("source_run_id"),
        "chapters": [
            {
                **chapter_row,
                "chapter_status": str(_find_registry_chapter(registry, int(chapter_row.get("chapter_id") or 0)).get("chapter_status") or "in_progress").strip(),
                "chapter_seam_report": _find_registry_chapter(registry, int(chapter_row.get("chapter_id") or 0)).get("chapter_seam_report"),
                "chapter_original_markdown": _find_registry_chapter(registry, int(chapter_row.get("chapter_id") or 0)).get("chapter_original_markdown"),
                "chapter_fixed_markdown": _find_registry_chapter(registry, int(chapter_row.get("chapter_id") or 0)).get("chapter_fixed_markdown"),
                "chapter_final_markdown": _find_registry_chapter(registry, int(chapter_row.get("chapter_id") or 0)).get("chapter_final_markdown"),
                "chapter_candidate_markdown": _find_registry_chapter(registry, int(chapter_row.get("chapter_id") or 0)).get("chapter_candidate_markdown"),
            }
            for chapter_row in chapters_summary
        ],
    }


def advance_section_workflow(
    workspace: Path,
    book_id: str,
    chapter_id: int,
    section_id: int,
    run_id: Optional[str] = None,
    resume: bool = False,
    ack_outline_attention_items: bool = False,
    force_outline_gate_bypass: bool = False,
) -> Dict[str, Any]:
    freeze_result = freeze_section_from_phase03_artifact(
        workspace=workspace,
        book_id=book_id,
        chapter_id=chapter_id,
        section_id=section_id,
        run_id=run_id,
    )
    scene_end_ref = str(freeze_result.get("scene_ref_end") or "").strip()
    if not scene_end_ref or ":" not in scene_end_ref:
        raise ValueError(f"Unable to resolve section end ref for {chapter_id}:{section_id}")
    scene_start_ref = str(freeze_result.get("scene_ref_start") or "").strip()
    if not scene_start_ref or ":" not in scene_start_ref:
        raise ValueError(f"Unable to resolve section start ref for {chapter_id}:{section_id}")
    _, scene_start_text = scene_start_ref.split(":", 1)
    _, scene_end_text = scene_end_ref.split(":", 1)
    scene_start = int(scene_start_text)
    scene_end = int(scene_end_text)
    run_section_range(
        workspace=workspace,
        book_id=book_id,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_start=scene_start,
        scene_end=scene_end,
        resume=resume,
        ack_outline_attention_items=ack_outline_attention_items,
        force_outline_gate_bypass=force_outline_gate_bypass,
    )
    lock_result = lock_section_from_written_state(
        workspace=workspace,
        book_id=book_id,
        chapter_id=chapter_id,
        section_id=section_id,
    )
    return {
        "freeze": freeze_result,
        "lock": lock_result,
    }
