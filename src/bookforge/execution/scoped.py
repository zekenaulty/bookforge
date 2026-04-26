from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib

from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ScopeSelector
from bookforge.query import current_execution_node, current_main_node, get_section_status, get_workspace_status, get_workspace_status_for_branch
from bookforge.runner import PAUSE_EXIT_CODE, run_section_range
from bookforge.section_workflow import get_section_workflow_status, lock_section_from_written_state
from bookforge.supervision import (
    RuntimeIssue,
    SurfaceSnapshot,
    capture_main_branch_snapshot,
    capture_surface_snapshot,
    emit_reconciled_main_branch_contracts,
    emit_reconciled_branch_contracts,
    paths as supervision_paths,
)


def _now_token() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _request_branch_id(request: ExecutionRequest) -> str:
    return str(request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID


def _execution_book_root(workspace: Path, book_id: str, branch_id: str) -> Path:
    if branch_id == MAIN_BRANCH_ID:
        return Path(workspace) / "books" / book_id
    return supervision_paths.branch_snapshot_root(Path(workspace) / "books" / book_id, branch_id)


def _capture_execution_snapshot(workspace: Path, book_id: str, branch_id: str):
    if branch_id == MAIN_BRANCH_ID:
        return capture_main_branch_snapshot(workspace, book_id)
    return capture_surface_snapshot(workspace, book_id, branch_id=branch_id)


def build_resume_paused_section_request(
    workspace: Path,
    book_id: str,
    *,
    chapter: Optional[int] = None,
    section: Optional[int] = None,
    ack_outline_attention_items: bool = False,
    force_outline_gate_bypass: bool = False,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id)
    if node is None:
        raise ValueError("No current main-branch node is available for resume.")
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family=node.workflow_family,
        chapter=chapter or node.chapter,
        section=section or node.section,
    )
    request_seed = "|".join(
        [
            book_id,
            selector.workflow_family or "",
            str(selector.chapter or ""),
            str(selector.section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="resume_paused_section",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "ack_outline_attention_items": bool(ack_outline_attention_items),
            "force_outline_gate_bypass": bool(force_outline_gate_bypass),
        },
    )


def build_write_section_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    section_id: int,
    branch_id: str = MAIN_BRANCH_ID,
    ack_outline_attention_items: bool = False,
    force_outline_gate_bypass: bool = False,
) -> ExecutionRequest:
    branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=section_id,
    )
    request_seed = "|".join(
        [
            book_id,
            selector.workflow_family or "",
            str(selector.chapter or ""),
            str(selector.section or ""),
            branch_id,
            node.revision_id if node else "",
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="write_frozen_section",
        selector=selector,
        expected_node=node,
        branch_id=branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "section_id": int(section_id),
            "ack_outline_attention_items": bool(ack_outline_attention_items),
            "force_outline_gate_bypass": bool(force_outline_gate_bypass),
        },
    )


def _emit_adapter_result(
    *,
    workspace: Path,
    book_id: str,
    request: ExecutionRequest,
    before_snapshot: Optional[SurfaceSnapshot],
    status: str,
    message: str,
    runtime_issue: Optional[RuntimeIssue] = None,
    details: Optional[Dict[str, Any]] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
) -> ExecutionResult:
    branch_id = _request_branch_id(request)
    if branch_id == MAIN_BRANCH_ID:
        bundle = emit_reconciled_main_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            before_snapshot=before_snapshot,
            action=request.action,
            result_status=status,
            request_id=request.request_id,
            message=message,
            runtime_issues=[runtime_issue] if runtime_issue else None,
            artifact_paths=artifact_paths,
            details=dict(details or {}),
        )
    else:
        bundle = emit_reconciled_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            branch_id=branch_id,
            before_snapshot=before_snapshot,
            action=request.action,
            result_status=status,
            request_id=request.request_id,
            message=message,
            runtime_issues=[runtime_issue] if runtime_issue else None,
            artifact_paths=artifact_paths,
            details=dict(details or {}),
        )
    if bundle.execution_result is not None:
        return bundle.execution_result
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False) or request.expected_node
    if node is None:
        raise ValueError("Unable to resolve node for execution result.")
    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, status, _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status=status,
        node=node,
        selector=request.selector,
        message=message,
        details=dict(details or {}),
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def _section_row(workflow_status: Dict[str, Any], chapter_id: int, section_id: int) -> Optional[Dict[str, Any]]:
    chapters = workflow_status.get("chapters") if isinstance(workflow_status.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict) or int(chapter.get("chapter_id", 0) or 0) != int(chapter_id):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            if int(section.get("section_id", 0) or 0) == int(section_id):
                return section
    return None


def _parse_scene_range(section_row: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    scene_ref_start = str(section_row.get("scene_ref_start") or "").strip()
    scene_ref_end = str(section_row.get("scene_ref_end") or "").strip()
    if ":" not in scene_ref_start or ":" not in scene_ref_end:
        return None
    _, scene_start_text = scene_ref_start.split(":", 1)
    _, scene_end_text = scene_ref_end.split(":", 1)
    try:
        return int(scene_start_text), int(scene_end_text)
    except ValueError:
        return None


def _missing_scene_artifacts(
    workspace: Path,
    book_id: str,
    chapter_id: int,
    scene_start: int,
    scene_end: int,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> List[str]:
    book_root = _execution_book_root(workspace, book_id, branch_id)
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
    missing: List[str] = []
    for scene_id in range(scene_start, scene_end + 1):
        prose_path = chapter_dir / f"scene_{scene_id:03d}.md"
        meta_path = chapter_dir / f"scene_{scene_id:03d}.meta.json"
        if not prose_path.exists():
            missing.append(str(prose_path))
        if not meta_path.exists():
            missing.append(str(meta_path))
    return missing


def _classify_live_node_mismatch(expected_node, live_node) -> tuple[str, str, str]:
    if expected_node is None or live_node is None:
        return (
            "expected_node_mismatch",
            "scope_contract_violation",
            "Live node does not match the expected resume node.",
        )
    expected = expected_node.to_dict()
    live = live_node.to_dict()
    comparable_keys = (
        "book_id",
        "workflow_family",
        "source_run_id",
        "branch_id",
        "fork_group_id",
        "chapter",
        "section",
        "scene",
        "phase_id",
        "turn_id",
    )
    if all(expected.get(key) == live.get(key) for key in comparable_keys) and expected.get("revision_id") != live.get("revision_id"):
        return (
            "stale_write",
            "stale_write",
            "Requested resume target has been superseded by a newer main-branch revision.",
        )
    return (
        "expected_node_mismatch",
        "scope_contract_violation",
        "Live node does not match the expected resume node.",
    )


def _hard_fail(
    *,
    workspace: Path,
    request: ExecutionRequest,
    code: str,
    category: str,
    message: str,
    live_node,
    extra: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    details = {
        "expected_node": request.expected_node.to_dict() if request.expected_node else None,
        "live_node": live_node.to_dict() if live_node else None,
        **dict(extra or {}),
    }
    return _emit_adapter_result(
        workspace=workspace,
        book_id=request.selector.book_id,
        request=request,
        before_snapshot=_capture_execution_snapshot(workspace, request.selector.book_id, _request_branch_id(request)),
        status="hard_fail",
        message=message,
        runtime_issue=RuntimeIssue(
            category=category,
            code=code,
            severity="high",
            message=message,
            details=details,
        ),
        details=details,
    )


def write_frozen_section(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "write_frozen_section":
        raise ValueError("Unsupported execution action.")
    if request.selector.chapter is None or request.selector.section is None:
        raise ValueError("write_frozen_section requires chapter and section scope.")

    branch_id = _request_branch_id(request)
    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    section_id = int(request.selector.section)
    before_snapshot = _capture_execution_snapshot(workspace, book_id, branch_id)
    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if live_node is not None and live_node.branch_id != branch_id:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="branch_mismatch",
            category="scope_contract_violation",
            message=f"Live node is not on requested branch {branch_id}; write_frozen_section refuses execution.",
            live_node=live_node,
        )
    if request.expected_node is not None and live_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        mismatch_code, mismatch_category, mismatch_message = _classify_live_node_mismatch(request.expected_node, live_node)
        return _hard_fail(
            workspace=workspace,
            request=request,
            code=mismatch_code,
            category=mismatch_category,
            message=mismatch_message,
            live_node=live_node,
        )

    status = get_workspace_status_for_branch(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    pause_marker = status.pause_marker or {}
    if pause_marker:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="pause_marker_present",
            category="scope_contract_violation",
            message="An active pause marker is present; use resume_paused_section instead of write_frozen_section.",
            live_node=live_node,
            extra={"pause_marker": pause_marker},
        )

    workflow_status = get_section_workflow_status(workspace, book_id) if branch_id == MAIN_BRANCH_ID else {}
    active_section = (
        workflow_status.get("active_section")
        if isinstance(workflow_status.get("active_section"), dict)
        else status.active_section
    )
    if not isinstance(active_section, dict):
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="active_section_missing",
            category="scope_contract_violation",
            message="No active frozen section is available for write_frozen_section.",
            live_node=live_node,
        )

    active_chapter = int(active_section.get("chapter_id", 0) or 0)
    active_section_id = int(active_section.get("section_id", 0) or 0)
    if chapter_id != active_chapter or section_id != active_section_id:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="selector_section_mismatch",
            category="scope_contract_violation",
            message="Requested scope does not match the active frozen section.",
            live_node=live_node,
            extra={"active_chapter": active_chapter, "active_section": active_section_id},
        )

    section_row = (
        _section_row(workflow_status, chapter_id, section_id)
        if branch_id == MAIN_BRANCH_ID
        else get_section_status(workspace, book_id, chapter_id, section_id, branch_id=branch_id)
    )
    if not isinstance(section_row, dict):
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="section_status_missing",
            category="scope_contract_violation",
            message="Unable to resolve workflow state for the selected frozen section.",
            live_node=live_node,
        )

    normalized_status = str(section_row.get("status") or "").strip().lower()
    if normalized_status == "locked":
        return _emit_adapter_result(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="no_op",
            message=f"Section {chapter_id}:{section_id} is already locked; no write is required.",
            details={
                "chapter_id": chapter_id,
                "section_id": section_id,
                "section_status": section_row.get("status"),
            },
        )
    if normalized_status != "frozen":
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="section_not_frozen",
            category="scope_contract_violation",
            message="write_frozen_section requires the selected section to be frozen.",
            live_node=live_node,
            extra={"section_status": section_row.get("status")},
        )

    scene_range = _parse_scene_range(section_row)
    if scene_range is None:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="section_scene_range_missing",
            category="scope_contract_violation",
            message="Selected frozen section does not have a valid scene range.",
            live_node=live_node,
        )
    scene_start, scene_end = scene_range
    missing_before = _missing_scene_artifacts(workspace, book_id, chapter_id, scene_start, scene_end, branch_id=branch_id)
    if not missing_before:
        return _emit_adapter_result(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="no_op",
            message=f"Section {chapter_id}:{section_id} already has complete scene artifacts; use lock_section_from_written_state.",
            details={
                "chapter_id": chapter_id,
                "section_id": section_id,
                "scene_ref_start": section_row.get("scene_ref_start"),
                "scene_ref_end": section_row.get("scene_ref_end"),
                "already_written": True,
            },
        )

    try:
        run_kwargs = {
            "workspace": workspace,
            "book_id": book_id,
            "chapter_id": chapter_id,
            "section_id": section_id,
            "scene_start": scene_start,
            "scene_end": scene_end,
            "resume": False,
            "ack_outline_attention_items": bool(request.details.get("ack_outline_attention_items")),
            "force_outline_gate_bypass": bool(request.details.get("force_outline_gate_bypass")),
        }
        if branch_id != MAIN_BRANCH_ID:
            run_kwargs["branch_id"] = branch_id
        run_section_range(**run_kwargs)
    except SystemExit as exc:
        if exc.code != PAUSE_EXIT_CODE:
            raise
        after_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
        return _emit_adapter_result(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="retryable_pause",
            message=f"Section {chapter_id}:{section_id} paused before completing its scene range.",
            details={
                "chapter_id": chapter_id,
                "section_id": section_id,
                "scene_ref_start": section_row.get("scene_ref_start"),
                "scene_ref_end": section_row.get("scene_ref_end"),
                "pre_revision_id": live_node.revision_id if live_node else None,
                "post_revision_id": after_node.revision_id if after_node else None,
                "before_node": live_node.to_dict() if live_node else None,
                "after_node": after_node.to_dict() if after_node else None,
            },
        )
    except Exception as exc:
        after_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
        return _emit_adapter_result(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=f"write_frozen_section failed: {exc}",
            runtime_issue=RuntimeIssue(
                category="scope_contract_violation",
                code="write_execution_failed",
                severity="high",
                message=str(exc),
                details={
                    "chapter_id": chapter_id,
                    "section_id": section_id,
                    "before_node": live_node.to_dict() if live_node else None,
                },
            ),
            details={
                "chapter_id": chapter_id,
                "section_id": section_id,
                "scene_ref_start": section_row.get("scene_ref_start"),
                "scene_ref_end": section_row.get("scene_ref_end"),
                "pre_revision_id": live_node.revision_id if live_node else None,
                "post_revision_id": after_node.revision_id if after_node else None,
                "before_node": live_node.to_dict() if live_node else None,
                "after_node": after_node.to_dict() if after_node else None,
            },
        )

    missing_after = _missing_scene_artifacts(workspace, book_id, chapter_id, scene_start, scene_end, branch_id=branch_id)
    if missing_after:
        after_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
        return _emit_adapter_result(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=f"Section {chapter_id}:{section_id} exited without producing all required scene artifacts.",
            runtime_issue=RuntimeIssue(
                category="scope_contract_violation",
                code="written_artifacts_missing",
                severity="high",
                message="write_frozen_section exited without producing all required scene artifacts.",
                details={
                    "chapter_id": chapter_id,
                    "section_id": section_id,
                    "missing_artifacts": missing_after,
                },
            ),
            details={
                "chapter_id": chapter_id,
                "section_id": section_id,
                "missing_artifacts": missing_after,
                "scene_ref_start": section_row.get("scene_ref_start"),
                "scene_ref_end": section_row.get("scene_ref_end"),
                "pre_revision_id": live_node.revision_id if live_node else None,
                "post_revision_id": after_node.revision_id if after_node else None,
                "before_node": live_node.to_dict() if live_node else None,
                "after_node": after_node.to_dict() if after_node else None,
            },
        )

    after_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    return _emit_adapter_result(
        workspace=workspace,
        book_id=book_id,
        request=request,
        before_snapshot=before_snapshot,
        status="success",
        message=f"Section {chapter_id}:{section_id} written through terminal scene without locking.",
        details={
            "chapter_id": chapter_id,
            "section_id": section_id,
            "scene_ref_start": section_row.get("scene_ref_start"),
            "scene_ref_end": section_row.get("scene_ref_end"),
            "pre_revision_id": live_node.revision_id if live_node else None,
            "post_revision_id": after_node.revision_id if after_node else None,
            "before_node": live_node.to_dict() if live_node else None,
            "after_node": after_node.to_dict() if after_node else None,
        },
    )


def resume_paused_section(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "resume_paused_section":
        raise ValueError("Unsupported execution action.")
    if request.expected_node is None:
        raise ValueError("resume_paused_section requires expected_node.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("resume_paused_section only supports main-branch execution.")

    book_id = request.selector.book_id
    before_snapshot = capture_main_branch_snapshot(workspace, book_id)
    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="missing_live_node",
            category="scope_contract_violation",
            message="No live main-branch node is available for resume.",
            live_node=None,
        )
    if live_node.branch_id != MAIN_BRANCH_ID:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="branch_mismatch",
            category="scope_contract_violation",
            message="Live node is not on main; resume_paused_section refuses derived-branch execution.",
            live_node=live_node,
        )
    if live_node.to_dict() != request.expected_node.to_dict():
        mismatch_code, mismatch_category, mismatch_message = _classify_live_node_mismatch(request.expected_node, live_node)
        return _hard_fail(
            workspace=workspace,
            request=request,
            code=mismatch_code,
            category=mismatch_category,
            message=mismatch_message,
            live_node=live_node,
        )
    if live_node.workflow_family != "section_write":
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="workflow_family_mismatch",
            category="scope_contract_violation",
            message="resume_paused_section only resumes section_write nodes.",
            live_node=live_node,
        )

    status = get_workspace_status(workspace, book_id, prefer_emitted=False)
    pause_marker = status.pause_marker or {}
    if not pause_marker:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="pause_marker_missing",
            category="scope_contract_violation",
            message="No active pause marker is present for resume.",
            live_node=live_node,
        )

    workflow_status = get_section_workflow_status(workspace, book_id)
    active_section = workflow_status.get("active_section") if isinstance(workflow_status.get("active_section"), dict) else None
    if not isinstance(active_section, dict):
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="active_section_missing",
            category="scope_contract_violation",
            message="No active frozen section is available for resume.",
            live_node=live_node,
        )

    chapter_id = int(active_section.get("chapter_id", 0) or 0)
    section_id = int(active_section.get("section_id", 0) or 0)
    if request.selector.chapter is not None and request.selector.chapter != chapter_id:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="selector_chapter_mismatch",
            category="scope_contract_violation",
            message="Requested chapter does not match the active paused section.",
            live_node=live_node,
            extra={"active_chapter": chapter_id, "active_section": section_id},
        )
    if request.selector.section is not None and request.selector.section != section_id:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="selector_section_mismatch",
            category="scope_contract_violation",
            message="Requested section does not match the active paused section.",
            live_node=live_node,
            extra={"active_chapter": chapter_id, "active_section": section_id},
        )

    section_row = _section_row(workflow_status, chapter_id, section_id)
    if not isinstance(section_row, dict):
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="section_status_missing",
            category="scope_contract_violation",
            message="Unable to resolve section workflow state for the active paused section.",
            live_node=live_node,
        )
    if str(section_row.get("status") or "").strip().lower() != "frozen":
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="section_not_frozen",
            category="scope_contract_violation",
            message="resume_paused_section requires the active section to remain frozen.",
            live_node=live_node,
            extra={"section_status": section_row.get("status")},
        )

    scene_ref_end = str(section_row.get("scene_ref_end") or "").strip()
    if ":" not in scene_ref_end:
        return _hard_fail(
            workspace=workspace,
            request=request,
            code="section_scene_range_missing",
            category="scope_contract_violation",
            message="Active frozen section does not have a terminal scene ref.",
            live_node=live_node,
        )
    _, scene_end_text = scene_ref_end.split(":", 1)
    scene_end = int(scene_end_text)

    try:
        scene_ref_start = str(section_row.get("scene_ref_start") or "").strip()
        if ":" not in scene_ref_start:
            return _hard_fail(
                workspace=workspace,
                request=request,
                code="section_scene_range_missing",
                category="scope_contract_violation",
                message="Active frozen section does not have a starting scene ref.",
                live_node=live_node,
            )
        _, scene_start_text = scene_ref_start.split(":", 1)
        scene_start = int(scene_start_text)

        run_section_range(
            workspace=workspace,
            book_id=book_id,
            chapter_id=chapter_id,
            section_id=section_id,
            scene_start=scene_start,
            scene_end=scene_end,
            resume=True,
            ack_outline_attention_items=bool(request.details.get("ack_outline_attention_items")),
            force_outline_gate_bypass=bool(request.details.get("force_outline_gate_bypass")),
        )
    except SystemExit as exc:
        if exc.code != PAUSE_EXIT_CODE:
            raise
        after_node = current_main_node(workspace, book_id, prefer_emitted=False)
        return _emit_adapter_result(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="retryable_pause",
            message="Section resume paused again before lock completion.",
            details={
                "remained_in_requested_mode": bool(after_node and after_node.workflow_family == live_node.workflow_family),
                "pre_revision_id": live_node.revision_id,
                "post_revision_id": after_node.revision_id if after_node else None,
                "before_node": live_node.to_dict(),
                "after_node": after_node.to_dict() if after_node else None,
            },
        )
    except Exception as exc:
        after_node = current_main_node(workspace, book_id, prefer_emitted=False)
        return _emit_adapter_result(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=f"Section resume failed: {exc}",
            runtime_issue=RuntimeIssue(
                category="scope_contract_violation",
                code="resume_execution_failed",
                severity="high",
                message=str(exc),
                details={"before_node": live_node.to_dict()},
            ),
            details={
                "remained_in_requested_mode": bool(after_node and after_node.workflow_family == live_node.workflow_family),
                "pre_revision_id": live_node.revision_id,
                "post_revision_id": after_node.revision_id if after_node else None,
                "before_node": live_node.to_dict(),
                "after_node": after_node.to_dict() if after_node else None,
            },
        )

    lock_result = lock_section_from_written_state(
        workspace=workspace,
        book_id=book_id,
        chapter_id=chapter_id,
        section_id=section_id,
    )
    after_node = current_main_node(workspace, book_id, prefer_emitted=False)
    return _emit_adapter_result(
        workspace=workspace,
        book_id=book_id,
        request=request,
        before_snapshot=before_snapshot,
        status="success",
        message=f"Paused section {chapter_id}:{section_id} resumed and locked successfully.",
        artifact_paths={
            "outline_path": str(lock_result.get("outline_path") or ""),
        },
        details={
            "remained_in_requested_mode": bool(after_node and after_node.workflow_family in {"section_write", "section_local_outline"}),
            "pre_revision_id": live_node.revision_id,
            "post_revision_id": after_node.revision_id if after_node else None,
            "before_node": live_node.to_dict(),
            "after_node": after_node.to_dict() if after_node else None,
            "lock_result": lock_result,
        },
    )
