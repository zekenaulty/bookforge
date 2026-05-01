from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
import json

from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ScopeSelector, TimelineNodeRef
from bookforge.pipeline.chapter_seam import finalize_locked_chapter
from bookforge.query import current_execution_node, current_main_node
from bookforge.section_workflow import (
    REGISTRY_FILENAME,
    _chapter_all_sections_locked,
    _find_outline_section,
    _find_registry_chapter,
    _find_registry_section,
    _load_workflow_state,
    _next_cursor_after_section,
    _normalize_artifact_paths,
    _outline_dir,
    _read_json,
    _update_chapter_finalization_fields,
    _workflow_is_complete,
    _write_json,
    _write_workflow_state,
    finalize_chapter_from_locked_sections,
    freeze_section_from_phase03_artifact,
    initialize_section_workflow,
    lock_section_from_written_state,
)
from bookforge.supervision import capture_surface_snapshot, emit_reconciled_branch_contracts, paths as supervision_paths
from .scene_actions import _advance_branch_node, _mark_branch_promote_ready


def _now_token() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_execution_result_for_request(book_root: Path, request_id: str) -> Optional[ExecutionResult]:
    result_path = supervision_paths.execution_results_path(book_root)
    if not result_path.exists():
        return None
    lines = [line.strip() for line in result_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in reversed(lines):
        payload = json.loads(line)
        if str(payload.get("request_id") or "").strip() == request_id:
            return ExecutionResult.from_dict(payload)
    return None


def _load_branch_execution_result_for_request(book_root: Path, branch_id: str, request_id: str) -> Optional[ExecutionResult]:
    result_path = supervision_paths.execution_results_path(book_root, branch_id)
    if not result_path.exists():
        return None
    lines = [line.strip() for line in result_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in reversed(lines):
        payload = json.loads(line)
        if str(payload.get("request_id") or "").strip() == request_id:
            return ExecutionResult.from_dict(payload)
    return None


def build_initialize_workflow_request(
    workspace: Path,
    book_id: str,
    *,
    run_id: Optional[str] = None,
    overwrite: bool = False,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id)
    request_seed = "|".join(
        [
            book_id,
            "initialize_section_workflow",
            str(run_id or ""),
            str(bool(overwrite)),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="initialize_section_workflow",
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=MAIN_BRANCH_ID,
            workflow_family=(node.workflow_family if node else "section_local_outline"),
        ),
        expected_node=None,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "run_id": str(run_id or "").strip() or None,
            "overwrite": bool(overwrite),
        },
    )


def build_freeze_section_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    section_id: int,
    run_id: Optional[str] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id)
    request_seed = "|".join(
        [
            book_id,
            "freeze_section_from_phase03_artifact",
            str(chapter_id),
            str(section_id),
            str(run_id or ""),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="freeze_section_from_phase03_artifact",
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=MAIN_BRANCH_ID,
            workflow_family=(node.workflow_family if node else "section_local_outline"),
            chapter=chapter_id,
            section=section_id,
        ),
        expected_node=None,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "section_id": int(section_id),
            "run_id": str(run_id or "").strip() or None,
        },
    )


def build_finalize_chapter_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    branch_id: str = MAIN_BRANCH_ID,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id)
    request_seed = "|".join(
        [
            book_id,
            "finalize_chapter_from_locked_sections",
            str(chapter_id),
            resolved_branch_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="finalize_chapter_from_locked_sections",
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=resolved_branch_id,
            workflow_family=(node.workflow_family if node else "section_local_outline"),
            chapter=chapter_id,
        ),
        expected_node=None,
        branch_id=resolved_branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "branch_id": resolved_branch_id,
        },
    )


def build_lock_section_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    section_id: int,
    branch_id: str = MAIN_BRANCH_ID,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id)
    request_seed = "|".join(
        [
            book_id,
            "lock_section_from_written_state",
            str(chapter_id),
            str(section_id),
            resolved_branch_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="lock_section_from_written_state",
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=resolved_branch_id,
            workflow_family=(node.workflow_family if node else "section_local_outline"),
            chapter=chapter_id,
            section=section_id,
        ),
        expected_node=None,
        branch_id=resolved_branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "section_id": int(section_id),
            "branch_id": resolved_branch_id,
        },
    )


def initialize_workflow(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "initialize_section_workflow":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("initialize_section_workflow only supports main-branch execution.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    initialize_section_workflow(
        workspace=workspace,
        book_id=book_id,
        run_id=request.details.get("run_id"),
        overwrite=bool(request.details.get("overwrite")),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, request.request_id)
    if emitted is not None:
        return emitted

    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("Unable to resolve emitted node for initialize_section_workflow.")
    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, "success", _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status="success",
        node=node,
        selector=request.selector,
        message="Section workflow initialized.",
        details=dict(request.details),
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def freeze_section(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "freeze_section_from_phase03_artifact":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("freeze_section_from_phase03_artifact only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.section is None:
        raise ValueError("freeze_section_from_phase03_artifact requires chapter and section scope.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    freeze_section_from_phase03_artifact(
        workspace=workspace,
        book_id=book_id,
        chapter_id=int(request.selector.chapter),
        section_id=int(request.selector.section),
        run_id=request.details.get("run_id"),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, request.request_id)
    if emitted is not None:
        return emitted

    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("Unable to resolve emitted node for freeze_section_from_phase03_artifact.")
    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, "success", _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status="success",
        node=node,
        selector=request.selector,
        message="Section frozen from phase-03 artifact.",
        details=dict(request.details),
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def _branch_finalize_chapter(
    workspace: Path,
    request: ExecutionRequest,
    *,
    branch_id: str,
) -> ExecutionResult:
    if request.selector.chapter is None:
        raise ValueError("finalize_chapter_from_locked_sections requires chapter scope.")

    book_id = request.selector.book_id
    canonical_root = Path(workspace) / "books" / book_id
    branch_root = supervision_paths.branch_snapshot_root(canonical_root, branch_id)
    if not branch_root.exists():
        raise ValueError(f"Branch snapshot root does not exist: {branch_id}")
    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if live_node is None:
        raise ValueError(f"No live execution node is available for branch {branch_id}.")

    chapter_id = int(request.selector.chapter)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    outline, registry = _load_workflow_state(branch_root)
    if not _chapter_all_sections_locked(registry, chapter_id):
        raise ValueError(f"Chapter {chapter_id} is not ready for branch-local finalization; all sections must be locked first.")
    registry_chapter = _find_registry_chapter(registry, chapter_id)
    if (
        str(registry_chapter.get("chapter_status") or "").strip().lower() == "finalized"
        and str(registry_chapter.get("chapter_final_markdown") or "").strip()
    ):
        artifact_paths = _normalize_artifact_paths(
            branch_root,
            {
                "outline": _outline_dir(branch_root) / "outline.json",
                "registry": _outline_dir(branch_root) / REGISTRY_FILENAME,
                "chapter_seam_report": registry_chapter.get("chapter_seam_report"),
                "chapter_original_markdown": registry_chapter.get("chapter_original_markdown"),
                "chapter_fixed_markdown": registry_chapter.get("chapter_fixed_markdown"),
                "chapter_candidate_markdown": registry_chapter.get("chapter_candidate_markdown"),
                "chapter_final_markdown": registry_chapter.get("chapter_final_markdown"),
            },
        )
        bundle = emit_reconciled_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            branch_id=branch_id,
            before_snapshot=before_snapshot,
            action="finalize_chapter_from_locked_sections",
            result_status="no_op",
            message=f"Branch-local chapter {chapter_id} is already finalized.",
            artifact_paths=artifact_paths,
            details={
                "chapter_id": chapter_id,
                "branch_id": branch_id,
                "status": registry_chapter.get("chapter_status"),
                "mutation_scope": "branch_authoritative",
            },
            request_id=request.request_id,
        )
        if bundle.execution_result is not None:
            return bundle.execution_result
        emitted = _load_branch_execution_result_for_request(canonical_root, branch_id, request.request_id)
        if emitted is not None:
            return emitted
        raise ValueError("Unable to resolve emitted branch chapter finalization result.")

    chapter_finalization = finalize_locked_chapter(branch_root, outline, chapter_id)
    _update_chapter_finalization_fields(registry, chapter_id, chapter_finalization)
    state_path = branch_root / "state.json"
    if state_path.exists():
        state = _read_json(state_path)
        if _workflow_is_complete(registry):
            state["status"] = "COMPLETE"
            _write_json(state_path, state)
    paths = _write_workflow_state(branch_root, outline, registry)
    artifact_paths = _normalize_artifact_paths(
        branch_root,
        {
            "outline": paths["outline"],
            "registry": paths["registry"],
            "chapter_seam_report": chapter_finalization.get("report_path"),
            "chapter_original_markdown": chapter_finalization.get("original_path"),
            "chapter_fixed_markdown": chapter_finalization.get("fixed_path"),
            "chapter_candidate_markdown": chapter_finalization.get("candidate_path"),
            "chapter_final_markdown": chapter_finalization.get("final_path"),
        },
    )
    advanced = TimelineNodeRef(
        book_id=live_node.book_id,
        workflow_family=live_node.workflow_family,
        source_run_id=live_node.source_run_id,
        branch_id=live_node.branch_id,
        fork_group_id=live_node.fork_group_id,
        chapter=chapter_id,
        section=None,
        scene=None,
        phase_id="finalize_chapter_from_locked_sections",
        turn_id=live_node.turn_id,
        revision_id=live_node.revision_id,
    )
    _advance_branch_node(branch_root, advanced, phase_id="finalize_chapter_from_locked_sections")
    _mark_branch_promote_ready(branch_root, branch_id)
    bundle = emit_reconciled_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        before_snapshot=before_snapshot,
        action="finalize_chapter_from_locked_sections",
        result_status="success",
        message=f"Branch-local chapter {chapter_id} finalized from locked sections.",
        artifact_paths=artifact_paths,
        details={
            "chapter_id": chapter_id,
            "branch_id": branch_id,
            "status": chapter_finalization.get("status"),
            "mutation_scope": "branch_authoritative",
        },
        request_id=request.request_id,
    )
    if bundle.execution_result is not None:
        return bundle.execution_result
    emitted = _load_branch_execution_result_for_request(canonical_root, branch_id, request.request_id)
    if emitted is not None:
        return emitted
    raise ValueError("Unable to resolve emitted branch chapter finalization result.")


def finalize_chapter(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "finalize_chapter_from_locked_sections":
        raise ValueError("Unsupported execution action.")
    resolved_branch_id = str(request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_branch_id != MAIN_BRANCH_ID:
        return _branch_finalize_chapter(workspace, request, branch_id=resolved_branch_id)
    if request.selector.chapter is None:
        raise ValueError("finalize_chapter_from_locked_sections requires chapter scope.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    finalize_chapter_from_locked_sections(
        workspace=workspace,
        book_id=book_id,
        chapter_id=int(request.selector.chapter),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, request.request_id)
    if emitted is not None:
        return emitted

    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("Unable to resolve emitted node for finalize_chapter_from_locked_sections.")
    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, "success", _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status="success",
        node=node,
        selector=request.selector,
        message=f"Chapter {int(request.selector.chapter)} finalized from locked sections.",
        details=dict(request.details),
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def _branch_lock_section(
    workspace: Path,
    request: ExecutionRequest,
    *,
    branch_id: str,
) -> ExecutionResult:
    if request.selector.chapter is None or request.selector.section is None:
        raise ValueError("lock_section_from_written_state requires chapter and section scope.")

    book_id = request.selector.book_id
    canonical_root = Path(workspace) / "books" / book_id
    branch_root = supervision_paths.branch_snapshot_root(canonical_root, branch_id)
    if not branch_root.exists():
        raise ValueError(f"Branch snapshot root does not exist: {branch_id}")
    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if live_node is None:
        raise ValueError(f"No live execution node is available for branch {branch_id}.")

    chapter_id = int(request.selector.chapter)
    section_id = int(request.selector.section)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    outline, registry = _load_workflow_state(branch_root)
    registry_section = _find_registry_section(registry, chapter_id, section_id)
    outline_section = _find_outline_section(outline, chapter_id, section_id)
    status = str(registry_section.get("status") or "").strip().lower()
    if status == "locked":
        artifact_paths = _normalize_artifact_paths(
            branch_root,
            {
                "outline": _outline_dir(branch_root) / "outline.json",
                "registry": _outline_dir(branch_root) / REGISTRY_FILENAME,
            },
        )
        bundle = emit_reconciled_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            branch_id=branch_id,
            before_snapshot=before_snapshot,
            action="lock_section_from_written_state",
            result_status="no_op",
            message=f"Branch-local section {chapter_id}:{section_id} is already locked.",
            artifact_paths=artifact_paths,
            details={
                "chapter_id": chapter_id,
                "section_id": section_id,
                "branch_id": branch_id,
                "status": "locked",
                "mutation_scope": "branch_authoritative",
            },
            request_id=request.request_id,
        )
        if bundle.execution_result is not None:
            return bundle.execution_result
        emitted = _load_branch_execution_result_for_request(canonical_root, branch_id, request.request_id)
        if emitted is not None:
            return emitted
        raise ValueError("Unable to resolve emitted branch lock result.")
    if status != "frozen":
        raise ValueError(f"Section {chapter_id}:{section_id} must be frozen before it can be locked.")

    scenes = outline_section.get("scenes") if isinstance(outline_section.get("scenes"), list) else []
    if not scenes:
        raise ValueError(f"Cannot lock empty section {chapter_id}:{section_id}.")
    chapter_dir = branch_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
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
        raise FileNotFoundError("Cannot lock branch-local section; missing generated artifacts:\n" + "\n".join(missing))

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
        chapter_finalization = finalize_locked_chapter(branch_root, outline, chapter_id)
        _update_chapter_finalization_fields(registry, chapter_id, chapter_finalization)

    state_path = branch_root / "state.json"
    if state_path.exists():
        state = _read_json(state_path)
        next_chapter, next_scene = _next_cursor_after_section(registry, chapter_id, section_id, scene_end)
        state["cursor"] = {"chapter": next_chapter, "scene": next_scene}
        state["status"] = "COMPLETE" if _workflow_is_complete(registry) else "OUTLINED"
        _write_json(state_path, state)

    paths = _write_workflow_state(branch_root, outline, registry)
    artifact_paths = _normalize_artifact_paths(
        branch_root,
        {
            "outline": paths["outline"],
            "registry": paths["registry"],
            "chapter_seam_report": chapter_finalization.get("report_path") if isinstance(chapter_finalization, dict) else None,
            "chapter_final_markdown": chapter_finalization.get("final_path") if isinstance(chapter_finalization, dict) else None,
        },
    )
    advanced = TimelineNodeRef(
        book_id=live_node.book_id,
        workflow_family=live_node.workflow_family,
        source_run_id=live_node.source_run_id,
        branch_id=live_node.branch_id,
        fork_group_id=live_node.fork_group_id,
        chapter=chapter_id,
        section=section_id,
        scene=scene_end,
        phase_id="lock_section_from_written_state",
        turn_id=live_node.turn_id,
        revision_id=live_node.revision_id,
    )
    _advance_branch_node(branch_root, advanced, phase_id="lock_section_from_written_state")
    _mark_branch_promote_ready(branch_root, branch_id)
    bundle = emit_reconciled_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        before_snapshot=before_snapshot,
        action="lock_section_from_written_state",
        result_status="success",
        message=f"Branch-local section {chapter_id}:{section_id} locked from written scene state.",
        artifact_paths=artifact_paths,
        details={
            "chapter_id": chapter_id,
            "section_id": section_id,
            "branch_id": branch_id,
            "status": "locked",
            "scene_ref_start": f"{chapter_id}:{scene_start}",
            "scene_ref_end": f"{chapter_id}:{scene_end}",
            "mutation_scope": "branch_authoritative",
            "chapter_finalized": isinstance(chapter_finalization, dict),
        },
        request_id=request.request_id,
    )
    if bundle.execution_result is not None:
        return bundle.execution_result
    emitted = _load_branch_execution_result_for_request(canonical_root, branch_id, request.request_id)
    if emitted is not None:
        return emitted
    raise ValueError("Unable to resolve emitted branch lock result.")


def lock_section(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "lock_section_from_written_state":
        raise ValueError("Unsupported execution action.")
    resolved_branch_id = str(request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_branch_id != MAIN_BRANCH_ID:
        return _branch_lock_section(workspace, request, branch_id=resolved_branch_id)
    if request.selector.chapter is None or request.selector.section is None:
        raise ValueError("lock_section_from_written_state requires chapter and section scope.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    lock_section_from_written_state(
        workspace=workspace,
        book_id=book_id,
        chapter_id=int(request.selector.chapter),
        section_id=int(request.selector.section),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, request.request_id)
    if emitted is not None:
        return emitted

    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("Unable to resolve emitted node for lock_section_from_written_state.")
    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, "success", _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status="success",
        node=node,
        selector=request.selector,
        message=f"Section {int(request.selector.chapter)}:{int(request.selector.section)} locked from written state.",
        details=dict(request.details),
        emitted_at=_now_token(),
        request_id=request.request_id,
    )
