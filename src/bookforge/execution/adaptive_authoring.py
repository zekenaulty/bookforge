from __future__ import annotations

from pathlib import Path
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple
import json
import shutil

from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ProducedArtifactReceipt, ScopeSelector, TimelineNodeRef
from bookforge.pipeline.chapter_seam import align_scene_pair_seam
from bookforge.query import current_execution_node
from bookforge.supervision import RuntimeIssue, capture_surface_snapshot, paths as supervision_paths

from .scene_actions import (
    _advance_branch_node,
    _artifact_relpath,
    _build_execution_node,
    _classify_live_node_mismatch,
    _emit_reconciled_result_for_request,
    _hash_id,
    _mark_branch_promote_ready,
    _now_token,
    _result_for_request,
)


def _request_branch_id(request: ExecutionRequest) -> str:
    return str(request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID


def _canonical_book_root(workspace: Path, book_id: str) -> Path:
    return Path(workspace) / "books" / book_id


def _execution_book_root(workspace: Path, book_id: str, branch_id: str) -> Path:
    canonical_root = _canonical_book_root(workspace, book_id)
    if branch_id == MAIN_BRANCH_ID:
        return canonical_root
    return supervision_paths.branch_snapshot_root(canonical_root, branch_id)


def _load_outline(book_root: Path) -> Dict[str, Any]:
    path = book_root / "outline" / "outline.json"
    if not path.exists():
        raise ValueError(f"Outline does not exist at {path}.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _load_registry(book_root: Path) -> Dict[str, Any]:
    path = book_root / "outline" / "snapshot_registry.json"
    if not path.exists():
        raise ValueError(f"Snapshot registry does not exist at {path}.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _scene_relpaths(chapter_id: int, scene_id: int) -> Dict[str, str]:
    return {
        "scene_prose": f"draft/chapters/ch_{int(chapter_id):03d}/scene_{int(scene_id):03d}.md",
        "scene_meta": f"draft/chapters/ch_{int(chapter_id):03d}/scene_{int(scene_id):03d}.meta.json",
    }


def _scene_file(book_root: Path, chapter_id: int, scene_id: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{int(chapter_id):03d}" / f"scene_{int(scene_id):03d}.md"


def _chapter_dir(book_root: Path, chapter_id: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{int(chapter_id):03d}"


def _bridge_plan_path(book_root: Path, chapter_id: int, scene_a_id: int, scene_b_id: int) -> Path:
    return book_root / "draft" / "context" / "bridge_scenes" / f"ch_{int(chapter_id):03d}" / f"bridge_after_scene_{int(scene_a_id):03d}_before_{int(scene_b_id):03d}.json"


def _bridge_apply_report_path(book_root: Path, chapter_id: int, scene_id: int) -> Path:
    return book_root / "draft" / "context" / "bridge_scenes" / f"ch_{int(chapter_id):03d}" / f"bridge_scene_{int(scene_id):03d}_apply_report.json"


def _chapter_scene_ids(outline: Dict[str, Any], chapter_id: int) -> List[int]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current != int(chapter_id):
            continue
        ids: List[int] = []
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for index, scene in enumerate(scenes, start=1):
                if not isinstance(scene, dict):
                    continue
                try:
                    ids.append(int(scene.get("scene_id") or scene.get("beat_id") or scene.get("id") or index))
                except (TypeError, ValueError):
                    continue
        if ids:
            return ids
    return []


def _find_chapter(outline: Dict[str, Any], chapter_id: int) -> Dict[str, Any]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current == int(chapter_id):
            return chapter
    raise ValueError(f"Chapter {int(chapter_id)} not found in outline.")


def _find_section_for_scene(outline: Dict[str, Any], chapter_id: int, scene_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    chapter = _find_chapter(outline, chapter_id)
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            try:
                current = int(scene.get("scene_id") or scene.get("beat_id") or scene.get("id"))
            except (TypeError, ValueError):
                continue
            if current == int(scene_id):
                return section, scene
    raise ValueError(f"Scene {int(chapter_id)}:{int(scene_id)} not found in outline.")


def _same_section_pair(outline: Dict[str, Any], chapter_id: int, scene_a_id: int, scene_b_id: int) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    section_a, scene_a = _find_section_for_scene(outline, chapter_id, scene_a_id)
    section_b, scene_b = _find_section_for_scene(outline, chapter_id, scene_b_id)
    if section_a is not section_b:
        raise ValueError("Bridge scene insertion apply currently requires both adjacent scenes to be in the same section.")
    return section_a, scene_a, scene_b


def _map_chapter_scene_refs(value: object, chapter_id: int, old_to_new: Dict[int, int]) -> object:
    text = str(value or "").strip()
    if not text.startswith(f"{int(chapter_id)}:"):
        return value
    _, scene_text = text.split(":", 1)
    try:
        old_scene_id = int(scene_text)
    except (TypeError, ValueError):
        return value
    new_scene_id = old_to_new.get(old_scene_id)
    if new_scene_id is None:
        return value
    return f"{int(chapter_id)}:{new_scene_id}"


def _renumber_outline_for_bridge(
    outline: Dict[str, Any],
    *,
    chapter_id: int,
    scene_a_id: int,
    scene_b_id: int,
    bridge_scene: Dict[str, Any],
) -> Dict[int, int]:
    section, scene_a, scene_b = _same_section_pair(outline, chapter_id, scene_a_id, scene_b_id)
    insertion_id = int(scene_a_id) + 1
    old_to_new: Dict[int, int] = {}
    chapter = _find_chapter(outline, chapter_id)
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for current_section in sections:
        if not isinstance(current_section, dict):
            continue
        for scene in current_section.get("scenes") if isinstance(current_section.get("scenes"), list) else []:
            if not isinstance(scene, dict):
                continue
            try:
                old_scene_id = int(scene.get("scene_id") or scene.get("beat_id") or scene.get("id"))
            except (TypeError, ValueError):
                continue
            if old_scene_id >= insertion_id:
                old_to_new[old_scene_id] = old_scene_id + 1

    for current_section in sections:
        if not isinstance(current_section, dict):
            continue
        scenes = current_section.get("scenes") if isinstance(current_section.get("scenes"), list) else []
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            try:
                old_scene_id = int(scene.get("scene_id") or scene.get("beat_id") or scene.get("id"))
            except (TypeError, ValueError):
                continue
            if old_scene_id in old_to_new:
                scene["scene_id"] = old_to_new[old_scene_id]
            for ref_key in ("consumes_outcome_from", "hands_off_to"):
                if ref_key in scene:
                    scene[ref_key] = _map_chapter_scene_refs(scene.get(ref_key), chapter_id, old_to_new)

    inserted_id = insertion_id
    bridge_scene["scene_id"] = inserted_id
    bridge_scene["consumes_outcome_from"] = f"{int(chapter_id)}:{int(scene_a_id)}"
    bridge_scene["hands_off_to"] = f"{int(chapter_id)}:{int(old_to_new.get(int(scene_b_id), int(scene_b_id)))}"
    scene_a["hands_off_to"] = f"{int(chapter_id)}:{inserted_id}"
    scene_b["consumes_outcome_from"] = f"{int(chapter_id)}:{inserted_id}"

    scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
    insert_at = 0
    for index, scene in enumerate(scenes):
        if scene is scene_a:
            insert_at = index + 1
            break
    scenes.insert(insert_at, bridge_scene)
    section["scenes"] = scenes
    section["target_scene_count"] = int(section.get("target_scene_count") or len(scenes)) + 1
    old_to_new[inserted_id] = inserted_id
    return old_to_new


def _renumber_registry_for_bridge(registry: Dict[str, Any], *, chapter_id: int, section_id: int, inserted_scene_id: int) -> None:
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current_chapter = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current_chapter != int(chapter_id):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            try:
                current_section = int(section.get("section_id"))
            except (TypeError, ValueError):
                continue
            start_text = str(section.get("scene_ref_start") or "")
            end_text = str(section.get("scene_ref_end") or "")
            if ":" not in start_text or ":" not in end_text:
                continue
            _, start_scene_text = start_text.split(":", 1)
            _, end_scene_text = end_text.split(":", 1)
            try:
                start_scene = int(start_scene_text)
                end_scene = int(end_scene_text)
            except (TypeError, ValueError):
                continue
            if current_chapter != int(chapter_id):
                continue
            if current_section == int(section_id):
                section["scene_ref_start"] = f"{int(chapter_id)}:{start_scene}"
                section["scene_ref_end"] = f"{int(chapter_id)}:{end_scene + 1 if end_scene >= inserted_scene_id else end_scene}"
                section["status"] = str(section.get("status") or "frozen").strip() or "frozen"
            elif start_scene >= inserted_scene_id:
                section["scene_ref_start"] = f"{int(chapter_id)}:{start_scene + 1}"
                section["scene_ref_end"] = f"{int(chapter_id)}:{end_scene + 1}"


def _scene_file_shift_suffixes() -> List[str]:
    return [
        ".md",
        ".meta.json",
        ".original.md",
        ".original.meta.json",
        ".fixed.md",
        ".fixed.meta.json",
    ]


def _move_path_if_exists(source: Path, target: Path, moved: List[Dict[str, str]]) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ValueError(f"Cannot shift scene artifact because target already exists: {target}")
    shutil.move(str(source), str(target))
    moved.append({"from": source.as_posix(), "to": target.as_posix()})


def _shift_branch_scene_artifacts(book_root: Path, *, chapter_id: int, insertion_id: int, max_scene_id: int) -> List[Dict[str, str]]:
    moved: List[Dict[str, str]] = []
    chapter_dir = _chapter_dir(book_root, chapter_id)
    for old_scene_id in range(int(max_scene_id), int(insertion_id) - 1, -1):
        new_scene_id = old_scene_id + 1
        for suffix in _scene_file_shift_suffixes():
            _move_path_if_exists(
                chapter_dir / f"scene_{old_scene_id:03d}{suffix}",
                chapter_dir / f"scene_{new_scene_id:03d}{suffix}",
                moved,
            )
        phase_root = book_root / "draft" / "context" / "phase_history"
        _move_path_if_exists(
            phase_root / f"ch{int(chapter_id):03d}_sc{old_scene_id:03d}.json",
            phase_root / f"ch{int(chapter_id):03d}_sc{new_scene_id:03d}.json",
            moved,
        )
        _move_path_if_exists(
            phase_root / f"ch{int(chapter_id):03d}_sc{old_scene_id:03d}",
            phase_root / f"ch{int(chapter_id):03d}_sc{new_scene_id:03d}",
            moved,
        )
        _move_path_if_exists(
            book_root / "draft" / "context" / "settings" / f"ch_{int(chapter_id):03d}" / f"scene_{old_scene_id:03d}",
            book_root / "draft" / "context" / "settings" / f"ch_{int(chapter_id):03d}" / f"scene_{new_scene_id:03d}",
            moved,
        )
        _move_path_if_exists(
            book_root / "draft" / "context" / "appearance" / f"ch_{int(chapter_id):03d}" / f"scene_{old_scene_id:03d}",
            book_root / "draft" / "context" / "appearance" / f"ch_{int(chapter_id):03d}" / f"scene_{new_scene_id:03d}",
            moved,
        )
    return [
        {
            "from": _artifact_relpath(book_root, Path(item["from"])),
            "to": _artifact_relpath(book_root, Path(item["to"])),
        }
        for item in moved
    ]


def _next_scene_id(outline: Dict[str, Any], chapter_id: int, scene_id: int) -> Optional[int]:
    ids = _chapter_scene_ids(outline, chapter_id)
    for index, current in enumerate(ids):
        if current == int(scene_id) and index + 1 < len(ids):
            return ids[index + 1]
    candidate = int(scene_id) + 1
    return candidate if candidate in ids else None


def _artifact_receipts_from_seam_report(book_root: Path, payload: Dict[str, Any], *, aligned: bool) -> List[ProducedArtifactReceipt]:
    receipts = [
        ProducedArtifactReceipt(
            artifact_key="scene_pair_seam_report",
            label="Scene-pair seam report",
            artifact_status="diagnostic",
            path=str(payload.get("report_path") or ""),
            format="application/json",
            consumable=True,
            resumable=False,
            replaceable=True,
            details={"status": payload.get("status")},
        )
    ]
    for artifact in payload.get("scene_artifacts") or []:
        if not isinstance(artifact, dict):
            continue
        scene_ref = str(artifact.get("scene_ref") or "")
        current_path = str(artifact.get("current_path") or "")
        original_path = str(artifact.get("original_path") or "")
        fixed_path = str(artifact.get("fixed_path") or "")
        if original_path:
            receipts.append(
                ProducedArtifactReceipt(
                    artifact_key=f"scene_{scene_ref.replace(':', '_')}_original",
                    label=f"Original scene {scene_ref} backup",
                    artifact_status="diagnostic",
                    path=original_path,
                    format="text/markdown",
                    consumable=True,
                    resumable=False,
                    replaceable=False,
                    details={"scene_ref": scene_ref},
                )
            )
        if fixed_path:
            receipts.append(
                ProducedArtifactReceipt(
                    artifact_key=f"scene_{scene_ref.replace(':', '_')}_fixed",
                    label=f"Fixed scene {scene_ref} candidate",
                    artifact_status="derived",
                    path=fixed_path,
                    format="text/markdown",
                    consumable=True,
                    resumable=True,
                    replaceable=True,
                    details={"scene_ref": scene_ref, "promoted_to_current": bool(aligned)},
                )
            )
        if aligned and current_path:
            receipts.append(
                ProducedArtifactReceipt(
                    artifact_key=f"scene_{scene_ref.replace(':', '_')}_current",
                    label=f"Aligned current scene {scene_ref}",
                    artifact_status="authoritative",
                    path=current_path,
                    format="text/markdown",
                    consumable=True,
                    resumable=False,
                    replaceable=True,
                    details={"scene_ref": scene_ref, "branch_authoritative": True},
                )
            )
    return receipts


def build_align_scene_pair_seam_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_a_id: int,
    scene_b_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for align_scene_pair_seam on branch {resolved_branch_id}.")
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=node.section,
        scene=scene_a_id,
        phase_id="align_scene_pair_seam",
    )
    resolved_scene_b = int(scene_b_id) if scene_b_id is not None else int(scene_a_id) + 1
    return ExecutionRequest(
        request_id=_hash_id(book_id, "align_scene_pair_seam", str(chapter_id), str(scene_a_id), str(resolved_scene_b), resolved_branch_id, node.revision_id, _now_token()),
        action="align_scene_pair_seam",
        selector=selector,
        expected_node=node,
        branch_id=resolved_branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_a_id": int(scene_a_id),
            "scene_b_id": resolved_scene_b,
            "macro_kind": "pairwise_scene_seam_alignment",
        },
    )


def align_scene_pair_seam_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "align_scene_pair_seam":
        raise ValueError("Unsupported execution action.")
    branch_id = _request_branch_id(request)
    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter or request.details.get("chapter_id") or 0)
    scene_a_id = int(request.details.get("scene_a_id") or request.selector.scene or 0)
    scene_b_id = int(request.details.get("scene_b_id") or (scene_a_id + 1))
    scope_details = {"chapter_id": chapter_id, "scene_a_id": scene_a_id, "scene_b_id": scene_b_id}
    canonical_root = _canonical_book_root(workspace, book_id)
    book_root = _execution_book_root(workspace, book_id, branch_id)
    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    fallback_node = request.expected_node or TimelineNodeRef(
        book_id=book_id,
        workflow_family="section_write",
        source_run_id="unknown",
        branch_id=branch_id,
        revision_id="unresolved",
        chapter=chapter_id or None,
        scene=scene_a_id or None,
        phase_id="align_scene_pair_seam",
    )
    if branch_id == MAIN_BRANCH_ID:
        result = _result_for_request(
            request=request,
            node=fallback_node,
            status="hard_fail",
            message="align_scene_pair_seam is branch-only; create a derived branch before seam re-authoring.",
            details={**scope_details, "failure_code": "branch_required", "canonical_changed": False},
        )
        return result
    if live_node is None:
        result = _result_for_request(
            request=request,
            node=fallback_node,
            status="hard_fail",
            message=f"No live execution node is available for align_scene_pair_seam on branch {branch_id}.",
            details={**scope_details, "failure_code": "missing_live_node", "canonical_changed": False},
        )
        return result
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(request.expected_node, live_node, action="align_scene_pair_seam")
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=message,
            runtime_issue=RuntimeIssue(
                category=failure_code,
                code=failure_code,
                severity="high",
                message=message,
                details={"expected_node": request.expected_node.to_dict(), "live_node": live_node.to_dict()},
            ),
            details={**scope_details, "failure_code": failure_code, "canonical_changed": False},
        )

    outline = _load_outline(book_root)
    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=request.selector.section,
        scene_id=scene_a_id,
        phase_id="align_scene_pair_seam",
    )
    try:
        payload = align_scene_pair_seam(book_root, outline, chapter_id, scene_a_id, scene_b_id)
    except Exception as exc:
        message = str(exc).strip() or "Scene-pair seam alignment failed."
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=message,
            runtime_issue=RuntimeIssue(
                category="scope_contract_violation",
                code="scene_pair_alignment_failed",
                severity="high",
                message=message,
                details=scope_details,
            ),
            details={**scope_details, "failure_code": "scene_pair_alignment_failed", "canonical_changed": False},
        )

    aligned = payload.get("status") == "aligned"
    status = "success" if aligned else "integrity_degraded"
    produced_artifacts = _artifact_receipts_from_seam_report(book_root, payload, aligned=aligned)
    artifact_paths = {
        "scene_pair_seam_report": str(payload.get("report_path") or ""),
    }
    for key, relpath in _scene_relpaths(chapter_id, scene_a_id).items():
        if (book_root / relpath).exists():
            artifact_paths[f"scene_a_{key}"] = relpath
    for key, relpath in _scene_relpaths(chapter_id, scene_b_id).items():
        if (book_root / relpath).exists():
            artifact_paths[f"scene_b_{key}"] = relpath
    _advance_branch_node(book_root, execution_node, phase_id="align_scene_pair_seam")
    if aligned:
        _mark_branch_promote_ready(book_root, branch_id)
    return _emit_reconciled_result_for_request(
        workspace=workspace,
        book_id=book_id,
        request=request,
        before_snapshot=before_snapshot,
        status=status,
        message=(
            f"Aligned scene pair ch{chapter_id:03d} sc{scene_a_id:03d}->sc{scene_b_id:03d} on branch {branch_id}."
            if aligned
            else f"Scene pair ch{chapter_id:03d} sc{scene_a_id:03d}->sc{scene_b_id:03d} needs author review."
        ),
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "status": payload.get("status"),
            "repair_action_count": payload.get("repair_action_count"),
            "issue_counts_before": payload.get("issue_counts_before"),
            "issue_counts_after": payload.get("issue_counts_after"),
            "branch_id": branch_id,
            "canonical_changed": False,
            "branch_change_status": "changed" if aligned else "candidate_written",
            "canonical_book_root": canonical_root.as_posix(),
        },
    )


def build_plan_bridge_scene_insertion_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_a_id: int,
    scene_b_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
    objective: Optional[str] = None,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for plan_bridge_scene_insertion on branch {resolved_branch_id}.")
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=node.section,
        scene=scene_a_id,
        phase_id="plan_bridge_scene_insertion",
    )
    resolved_scene_b = int(scene_b_id) if scene_b_id is not None else int(scene_a_id) + 1
    return ExecutionRequest(
        request_id=_hash_id(book_id, "plan_bridge_scene_insertion", str(chapter_id), str(scene_a_id), str(resolved_scene_b), resolved_branch_id, node.revision_id, _now_token()),
        action="plan_bridge_scene_insertion",
        selector=selector,
        expected_node=node,
        branch_id=resolved_branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_a_id": int(scene_a_id),
            "scene_b_id": resolved_scene_b,
            "objective": str(objective or "").strip() or "Create a bridge scene candidate between adjacent scenes.",
            "macro_kind": "adaptive_bridge_scene_insertion_plan",
        },
    )


def _write_bridge_plan(book_root: Path, payload: Dict[str, Any]) -> Path:
    chapter_id = int(payload["chapter_id"])
    scene_a_id = int(payload["scene_a_id"])
    scene_b_id = int(payload["scene_b_id"])
    path = book_root / "draft" / "context" / "bridge_scenes" / f"ch_{chapter_id:03d}" / f"bridge_after_scene_{scene_a_id:03d}_before_{scene_b_id:03d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def plan_bridge_scene_insertion_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "plan_bridge_scene_insertion":
        raise ValueError("Unsupported execution action.")
    branch_id = _request_branch_id(request)
    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter or request.details.get("chapter_id") or 0)
    scene_a_id = int(request.details.get("scene_a_id") or request.selector.scene or 0)
    scene_b_id = int(request.details.get("scene_b_id") or (scene_a_id + 1))
    scope_details = {"chapter_id": chapter_id, "scene_a_id": scene_a_id, "scene_b_id": scene_b_id}
    book_root = _execution_book_root(workspace, book_id, branch_id)
    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    fallback_node = request.expected_node or TimelineNodeRef(
        book_id=book_id,
        workflow_family="section_write",
        source_run_id="unknown",
        branch_id=branch_id,
        revision_id="unresolved",
        chapter=chapter_id or None,
        scene=scene_a_id or None,
        phase_id="plan_bridge_scene_insertion",
    )
    if branch_id == MAIN_BRANCH_ID:
        return _result_for_request(
            request=request,
            node=fallback_node,
            status="hard_fail",
            message="plan_bridge_scene_insertion is branch-only; create a derived branch before planning adaptive scene insertion.",
            details={**scope_details, "failure_code": "branch_required", "canonical_changed": False},
        )
    if live_node is None:
        return _result_for_request(
            request=request,
            node=fallback_node,
            status="hard_fail",
            message=f"No live execution node is available for plan_bridge_scene_insertion on branch {branch_id}.",
            details={**scope_details, "failure_code": "missing_live_node", "canonical_changed": False},
        )
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(request.expected_node, live_node, action="plan_bridge_scene_insertion")
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=message,
            runtime_issue=RuntimeIssue(
                category=failure_code,
                code=failure_code,
                severity="high",
                message=message,
                details={"expected_node": request.expected_node.to_dict(), "live_node": live_node.to_dict()},
            ),
            details={**scope_details, "failure_code": failure_code, "canonical_changed": False},
        )

    outline = _load_outline(book_root)
    valid_next_scene = _next_scene_id(outline, chapter_id, scene_a_id)
    if valid_next_scene != scene_b_id:
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message="Bridge scene planning requires adjacent scene ids from the active outline.",
            runtime_issue=RuntimeIssue(
                category="scope_contract_violation",
                code="non_adjacent_bridge_scene_target",
                severity="high",
                message="Bridge scene planning requires adjacent scene ids from the active outline.",
                details={**scope_details, "outline_next_scene_id": valid_next_scene},
            ),
            details={**scope_details, "failure_code": "non_adjacent_bridge_scene_target", "canonical_changed": False},
        )

    scene_a_path = _scene_file(book_root, chapter_id, scene_a_id)
    scene_b_path = _scene_file(book_root, chapter_id, scene_b_id)
    payload = {
        "schema_version": "bridge_scene_insertion_plan_v1",
        "book_id": book_id,
        "branch_id": branch_id,
        "chapter_id": chapter_id,
        "scene_a_id": scene_a_id,
        "scene_b_id": scene_b_id,
        "objective": str(request.details.get("objective") or "").strip() or "Create a bridge scene candidate between adjacent scenes.",
        "status": "proposal",
        "artifact_status": "provisional",
        "mutation_policy": "does_not_modify_outline_or_prose",
        "recommended_next_actions": [
            "review_bridge_scene_insertion_plan",
            "draft_bridge_scene_candidate",
            "apply_bridge_scene_insertion",
        ],
        "source_artifacts": {
            "scene_a_path": _artifact_relpath(book_root, scene_a_path) if scene_a_path.exists() else None,
            "scene_b_path": _artifact_relpath(book_root, scene_b_path) if scene_b_path.exists() else None,
        },
        "constraints": [
            "Treat this as a proposal only.",
            "Do not renumber scenes or mutate outline state until apply_bridge_scene_insertion exists and validates scope.",
            "Bridge content must preserve both adjacent scenes and explain why a new beat is necessary.",
        ],
        "created_at": _now_token(),
    }
    plan_path = _write_bridge_plan(book_root, payload)
    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=request.selector.section,
        scene_id=scene_a_id,
        phase_id="plan_bridge_scene_insertion",
    )
    _advance_branch_node(book_root, execution_node, phase_id="plan_bridge_scene_insertion")
    relpath = _artifact_relpath(book_root, plan_path)
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="bridge_scene_insertion_plan",
            label="Bridge scene insertion plan",
            artifact_status="provisional",
            path=relpath,
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"chapter_id": chapter_id, "scene_a_id": scene_a_id, "scene_b_id": scene_b_id},
        )
    ]
    return _emit_reconciled_result_for_request(
        workspace=workspace,
        book_id=book_id,
        request=request,
        before_snapshot=before_snapshot,
        status="success",
        message=f"Planned branch-local bridge scene insertion between scenes {scene_a_id} and {scene_b_id}.",
        artifact_paths={"bridge_scene_insertion_plan": relpath},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "branch_id": branch_id,
            "canonical_changed": False,
            "branch_change_status": "changed",
            "proposal_only": True,
            "recommended_next_actions": list(payload["recommended_next_actions"]),
        },
    )


def build_apply_bridge_scene_insertion_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_a_id: int,
    scene_b_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
    bridge_plan_path: Optional[str] = None,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for apply_bridge_scene_insertion on branch {resolved_branch_id}.")
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=node.section,
        scene=scene_a_id,
        phase_id="apply_bridge_scene_insertion",
    )
    resolved_scene_b = int(scene_b_id) if scene_b_id is not None else int(scene_a_id) + 1
    return ExecutionRequest(
        request_id=_hash_id(book_id, "apply_bridge_scene_insertion", str(chapter_id), str(scene_a_id), str(resolved_scene_b), resolved_branch_id, node.revision_id, _now_token()),
        action="apply_bridge_scene_insertion",
        selector=selector,
        expected_node=node,
        branch_id=resolved_branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_a_id": int(scene_a_id),
            "scene_b_id": resolved_scene_b,
            "bridge_plan_path": str(bridge_plan_path or "").strip(),
            "macro_kind": "adaptive_bridge_scene_insertion_apply",
        },
    )


def _load_bridge_plan(book_root: Path, request: ExecutionRequest, chapter_id: int, scene_a_id: int, scene_b_id: int) -> Tuple[Path, Dict[str, Any]]:
    raw_plan_path = str(request.details.get("bridge_plan_path") or "").strip()
    plan_path = book_root / raw_plan_path if raw_plan_path else _bridge_plan_path(book_root, chapter_id, scene_a_id, scene_b_id)
    if not plan_path.exists():
        raise ValueError(f"Bridge scene insertion plan does not exist: {_artifact_relpath(book_root, plan_path)}")
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Bridge scene insertion plan must be a JSON object.")
    if str(payload.get("schema_version") or "") != "bridge_scene_insertion_plan_v1":
        raise ValueError("Bridge scene insertion plan has an unsupported schema_version.")
    if str(payload.get("branch_id") or "").strip() != _request_branch_id(request):
        raise ValueError("Bridge scene insertion plan branch does not match the execution branch.")
    for key, expected in {"chapter_id": chapter_id, "scene_a_id": scene_a_id, "scene_b_id": scene_b_id}.items():
        try:
            actual = int(payload.get(key))
        except (TypeError, ValueError):
            raise ValueError(f"Bridge scene insertion plan is missing {key}.") from None
        if actual != int(expected):
            raise ValueError(f"Bridge scene insertion plan {key}={actual} does not match requested {expected}.")
    return plan_path, payload


def _bridge_scene_outline_entry(*, chapter_id: int, scene_a_id: int, scene_b_id: int, section_id: Optional[int], plan: Dict[str, Any], plan_relpath: str) -> Dict[str, Any]:
    objective = str(plan.get("objective") or "").strip() or "Bridge the adjacent scenes without changing their established outcomes."
    return {
        "scene_id": int(scene_a_id) + 1,
        "title": "Bridge Scene",
        "summary": objective,
        "intent": objective,
        "handoff_mode": "handoff",
        "threads": list(plan.get("threads") if isinstance(plan.get("threads"), list) else []),
        "introduced_by": "apply_bridge_scene_insertion",
        "insertion_status": "provisional",
        "source_bridge_plan": plan_relpath,
        "source_scene_pair": {
            "chapter_id": int(chapter_id),
            "scene_a_id": int(scene_a_id),
            "scene_b_id": int(scene_b_id),
            "section_id": int(section_id) if section_id is not None else None,
        },
        "constraints": [
            "Preserve the established ending of scene A.",
            "Preserve the established opening facts and outcome of scene B.",
            "Use this bridge only to add necessary connective tissue.",
        ],
    }


def apply_bridge_scene_insertion_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "apply_bridge_scene_insertion":
        raise ValueError("Unsupported execution action.")
    branch_id = _request_branch_id(request)
    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter or request.details.get("chapter_id") or 0)
    scene_a_id = int(request.details.get("scene_a_id") or request.selector.scene or 0)
    scene_b_id = int(request.details.get("scene_b_id") or (scene_a_id + 1))
    scope_details = {"chapter_id": chapter_id, "scene_a_id": scene_a_id, "scene_b_id": scene_b_id}
    book_root = _execution_book_root(workspace, book_id, branch_id)
    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    fallback_node = request.expected_node or TimelineNodeRef(
        book_id=book_id,
        workflow_family="section_write",
        source_run_id="unknown",
        branch_id=branch_id,
        revision_id="unresolved",
        chapter=chapter_id or None,
        scene=scene_a_id or None,
        phase_id="apply_bridge_scene_insertion",
    )
    if branch_id == MAIN_BRANCH_ID:
        return _result_for_request(
            request=request,
            node=fallback_node,
            status="hard_fail",
            message="apply_bridge_scene_insertion is branch-only; create a derived branch before applying adaptive scene insertion.",
            details={**scope_details, "failure_code": "branch_required", "canonical_changed": False},
        )
    if live_node is None:
        return _result_for_request(
            request=request,
            node=fallback_node,
            status="hard_fail",
            message=f"No live execution node is available for apply_bridge_scene_insertion on branch {branch_id}.",
            details={**scope_details, "failure_code": "missing_live_node", "canonical_changed": False},
        )
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(request.expected_node, live_node, action="apply_bridge_scene_insertion")
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=message,
            runtime_issue=RuntimeIssue(
                category=failure_code,
                code=failure_code,
                severity="high",
                message=message,
                details={"expected_node": request.expected_node.to_dict(), "live_node": live_node.to_dict()},
            ),
            details={**scope_details, "failure_code": failure_code, "canonical_changed": False},
        )

    try:
        outline = _load_outline(book_root)
        registry = _load_registry(book_root)
        valid_next_scene = _next_scene_id(outline, chapter_id, scene_a_id)
        if valid_next_scene != scene_b_id:
            raise ValueError("Bridge scene insertion apply requires adjacent scene ids from the active branch outline.")
        plan_path, plan = _load_bridge_plan(book_root, request, chapter_id, scene_a_id, scene_b_id)
        section, _, _ = _same_section_pair(outline, chapter_id, scene_a_id, scene_b_id)
        section_id = int(request.selector.section or section.get("section_id") or 0)
        if section_id <= 0:
            raise ValueError("Unable to resolve section for bridge scene insertion.")
        existing_ids = _chapter_scene_ids(outline, chapter_id)
        max_scene_id = max(existing_ids) if existing_ids else scene_b_id
        inserted_scene_id = int(scene_a_id) + 1
        moved_artifacts = _shift_branch_scene_artifacts(
            book_root,
            chapter_id=chapter_id,
            insertion_id=inserted_scene_id,
            max_scene_id=max_scene_id,
        )
        bridge_scene = _bridge_scene_outline_entry(
            chapter_id=chapter_id,
            scene_a_id=scene_a_id,
            scene_b_id=scene_b_id,
            section_id=section_id,
            plan=plan,
            plan_relpath=_artifact_relpath(book_root, plan_path),
        )
        old_to_new = _renumber_outline_for_bridge(
            outline,
            chapter_id=chapter_id,
            scene_a_id=scene_a_id,
            scene_b_id=scene_b_id,
            bridge_scene=bridge_scene,
        )
        _renumber_registry_for_bridge(registry, chapter_id=chapter_id, section_id=section_id, inserted_scene_id=inserted_scene_id)
        outline_path = _write_json(book_root / "outline" / "outline.json", outline)
        registry_path = _write_json(book_root / "outline" / "snapshot_registry.json", registry)
        from bookforge.section_workflow import _rebuild_views

        rebuilt_views = _rebuild_views(book_root, outline, registry)
        report = {
            "schema_version": "bridge_scene_insertion_apply_report_v1",
            "book_id": book_id,
            "branch_id": branch_id,
            "chapter_id": chapter_id,
            "section_id": section_id,
            "scene_a_id": scene_a_id,
            "scene_b_id": scene_b_id,
            "inserted_scene_id": inserted_scene_id,
            "status": "applied",
            "artifact_status": "diagnostic",
            "source_bridge_plan": _artifact_relpath(book_root, plan_path),
            "ref_map": {f"{chapter_id}:{old}": f"{chapter_id}:{new}" for old, new in sorted(old_to_new.items())},
            "moved_artifacts": moved_artifacts,
            "rebuilt_views": {key: _artifact_relpath(book_root, path) for key, path in rebuilt_views.items()},
            "recommended_next_actions": ["plan_scene", "continue_scene"],
            "created_at": _now_token(),
        }
        apply_report_path = _write_json(_bridge_apply_report_path(book_root, chapter_id, inserted_scene_id), report)
    except Exception as exc:
        message = str(exc).strip() or "Bridge scene insertion apply failed."
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=message,
            runtime_issue=RuntimeIssue(
                category="scope_contract_violation",
                code="bridge_scene_insertion_apply_failed",
                severity="high",
                message=message,
                details=scope_details,
            ),
            details={**scope_details, "failure_code": "bridge_scene_insertion_apply_failed", "canonical_changed": False},
        )

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=inserted_scene_id,
        phase_id="apply_bridge_scene_insertion",
    )
    _advance_branch_node(book_root, execution_node, phase_id="apply_bridge_scene_insertion")
    rel_report = _artifact_relpath(book_root, apply_report_path)
    rel_outline = _artifact_relpath(book_root, outline_path)
    rel_registry = _artifact_relpath(book_root, registry_path)
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="bridge_scene_insertion_apply_report",
            label="Bridge scene insertion apply report",
            artifact_status="diagnostic",
            path=rel_report,
            format="application/json",
            consumable=True,
            resumable=False,
            replaceable=True,
            details={"inserted_scene_id": inserted_scene_id},
        ),
        ProducedArtifactReceipt(
            artifact_key="branch_outline",
            label="Branch outline after bridge insertion",
            artifact_status="authoritative",
            path=rel_outline,
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"branch_authoritative": True, "inserted_scene_id": inserted_scene_id},
        ),
        ProducedArtifactReceipt(
            artifact_key="branch_snapshot_registry",
            label="Branch snapshot registry after bridge insertion",
            artifact_status="authoritative",
            path=rel_registry,
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"branch_authoritative": True, "inserted_scene_id": inserted_scene_id},
        ),
    ]
    return _emit_reconciled_result_for_request(
        workspace=workspace,
        book_id=book_id,
        request=request,
        before_snapshot=before_snapshot,
        status="success",
        message=f"Applied branch-local bridge scene insertion as scene {inserted_scene_id}.",
        artifact_paths={
            "bridge_scene_insertion_apply_report": rel_report,
            "outline": rel_outline,
            "snapshot_registry": rel_registry,
        },
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "inserted_scene_id": inserted_scene_id,
            "branch_id": branch_id,
            "canonical_changed": False,
            "branch_change_status": "changed",
            "recommended_next_actions": ["plan_scene", "continue_scene"],
        },
    )
