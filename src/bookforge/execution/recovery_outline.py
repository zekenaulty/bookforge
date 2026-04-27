from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

from bookforge import section_workflow as sw
from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, RecoveryAnchor
from bookforge.query.recovery import get_recovery_manifest
from bookforge.supervision import capture_surface_snapshot

from .recovery_common import (
    advance_recovery_node,
    book_root,
    emit_result,
    execution_root,
    load_recovery_anchor,
    load_recovery_scope,
    read_json,
    relative,
    write_json,
    write_receipt,
)


_RUN_ANCHOR_NAMES = (
    "outline_final_v1_1.json",
    "outline_cast_refined_v1_1.json",
    "outline_seams_hygiened_v1_1.json",
    "outline_handoff_normalized_v1_1.json",
    "outline_draft_v1_1.json",
    "outline_sections_v1.json",
)


def _preferred_run_anchor(outline_root: Path, run_id: Optional[str]) -> Optional[Path]:
    resolved = str(run_id or "").strip()
    if not resolved:
        return None
    run_dir = outline_root / "pipeline_runs" / resolved
    for name in _RUN_ANCHOR_NAMES:
        candidate = run_dir / name
        if candidate.exists():
            return candidate
    return None


def _chapter(payload: Dict[str, Any], chapter_id: int) -> Optional[Dict[str, Any]]:
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    for chapter in chapters:
        if isinstance(chapter, dict) and int(chapter.get("chapter_id", 0) or 0) == int(chapter_id):
            return chapter
    if isinstance(payload.get("chapter"), dict) and int(payload["chapter"].get("chapter_id", 0) or 0) == int(chapter_id):
        return payload["chapter"]
    if int(payload.get("chapter_id", 0) or 0) == int(chapter_id):
        return payload
    return None


def _section(chapter: Dict[str, Any], section_id: int) -> Optional[Dict[str, Any]]:
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if isinstance(section, dict) and int(section.get("section_id", 0) or 0) == int(section_id):
            return section
    return None


def _replace_section(outline: Dict[str, Any], chapter_id: int, source_section: Dict[str, Any]) -> None:
    target_chapter = _chapter(outline, chapter_id)
    if target_chapter is None:
        target_chapter = {"chapter_id": chapter_id, "title": f"Chapter {chapter_id}", "sections": []}
        outline.setdefault("chapters", []).append(target_chapter)
    sections = target_chapter.setdefault("sections", [])
    section_id = int(source_section.get("section_id", 0) or 0)
    for index, existing in enumerate(sections):
        if isinstance(existing, dict) and int(existing.get("section_id", 0) or 0) == section_id:
            sections[index] = json.loads(json.dumps(source_section, ensure_ascii=True))
            return
    sections.append(json.loads(json.dumps(source_section, ensure_ascii=True)))
    sections.sort(key=lambda item: int(item.get("section_id", 0) or 0) if isinstance(item, dict) else 0)


def _replace_chapter(outline: Dict[str, Any], source_chapter: Dict[str, Any]) -> None:
    chapter_id = int(source_chapter.get("chapter_id", 0) or 0)
    chapters = outline.setdefault("chapters", [])
    for index, existing in enumerate(chapters):
        if isinstance(existing, dict) and int(existing.get("chapter_id", 0) or 0) == chapter_id:
            chapters[index] = json.loads(json.dumps(source_chapter, ensure_ascii=True))
            return
    chapters.append(json.loads(json.dumps(source_chapter, ensure_ascii=True)))
    chapters.sort(key=lambda item: int(item.get("chapter_id", 0) or 0) if isinstance(item, dict) else 0)


def _source_payload(root: Path, anchor: RecoveryAnchor) -> Dict[str, Any]:
    outline_root = root / "outline"
    if anchor.anchor_type in {"declared_source_run", "latest_outline_run"}:
        run_id = anchor.source_run_id
        if not run_id:
            if anchor.anchor_type == "latest_outline_run":
                latest = read_json(outline_root / "pipeline_latest.json")
                run_id = str(latest.get("run_id") or latest.get("latest_run_id") or "").strip() or None
            else:
                registry = read_json(outline_root / sw.REGISTRY_FILENAME)
                run_id = str(registry.get("source_run_id") or "").strip() or None
        anchor_path = _preferred_run_anchor(outline_root, run_id)
        if anchor_path is None:
            raise FileNotFoundError(f"No outline run anchor found for {run_id}.")
        return read_json(anchor_path)
    if anchor.anchor_type == "frozen_chapter_projection":
        chapters = []
        for path in sorted((outline_root / "chapters").glob("ch_*.json")):
            payload = read_json(path)
            chapter = _chapter(payload, int(path.stem.split("_", 1)[1]))
            if chapter:
                chapters.append(chapter)
        return {"chapters": chapters, "characters": (read_json(outline_root / "characters.json").get("characters") or [])}
    raise ValueError(f"Unsupported normalization anchor: {anchor.anchor_type}")


def normalize_outline_scope(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "normalize_outline_scope":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("normalize_outline_scope requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    branch_root = execution_root(root, branch_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    anchor = load_recovery_anchor(manifest)
    scope = load_recovery_scope(manifest)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)

    source = _source_payload(branch_root, anchor)
    outline_path = branch_root / "outline" / "outline.json"
    outline = read_json(outline_path)
    changed_scopes = []
    for item in scope.affected_scopes:
        chapter_id = int(item["chapter_id"])
        source_chapter = _chapter(source, chapter_id)
        if source_chapter is None:
            raise ValueError(f"Selected anchor does not contain chapter {chapter_id}.")
        if "section_id" in item:
            source_section = _section(source_chapter, int(item["section_id"]))
            if source_section is None:
                raise ValueError(f"Selected anchor does not contain section {chapter_id}:{item['section_id']}.")
            _replace_section(outline, chapter_id, source_section)
        else:
            _replace_chapter(outline, source_chapter)
        changed_scopes.append(dict(item))
    if isinstance(source.get("characters"), list):
        outline["characters"] = json.loads(json.dumps(source["characters"], ensure_ascii=True))
    run_id = anchor.source_run_id or str(manifest.get("source_run_id") or "").strip() or "recovery"
    registry = sw._build_snapshot_registry(book_id, run_id, outline)
    paths = sw._write_workflow_state(branch_root, outline, registry)
    for item in {int(scope_item["chapter_id"]) for scope_item in scope.affected_scopes}:
        chapter = _chapter(outline, item)
        if chapter:
            write_json(branch_root / "outline" / "chapters" / f"ch_{item:03d}.json", chapter)
    advance_recovery_node(workspace, book_id, branch_id, "normalize_outline_scope")
    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="normalize_outline_scope",
        status="success",
        message=f"Normalized {len(changed_scopes)} outline scopes from {anchor.anchor_type}.",
        artifact_paths={key: relative(branch_root, path) for key, path in paths.items()},
        details={"anchor": anchor.to_dict(), "changed_scopes": changed_scopes},
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status="success",
        message=f"Normalized {len(changed_scopes)} outline scopes from {anchor.anchor_type}.",
        receipt=receipt,
        artifact_paths={key: relative(branch_root, path) for key, path in paths.items()},
        before_snapshot=before_snapshot,
    )
