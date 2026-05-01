from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from bookforge.query.integrity import get_integrity_verdict
from bookforge.query.workflow import get_workflow_snapshot
from bookforge.query.workspace import get_workspace_status

from .emit import (
    EmissionBundle,
    _build_branch_state_surface,
    emit_branch_contracts,
    emit_main_branch_contracts,
)


@dataclass(frozen=True, slots=True)
class SurfaceSnapshot:
    book_id: str
    branch_id: str
    node: Optional[Dict[str, Any]]
    state_status: Optional[str]
    workflow_run_mode: Optional[str]
    integrity_status: Optional[str]
    integrity_issue_codes: tuple[str, ...]
    active_section: Optional[Dict[str, Any]]
    cursor: Dict[str, Any]


def _integrity_rank(status: Optional[str]) -> int:
    mapping = {
        "healthy": 0,
        "passed": 0,
        "attention_required": 1,
        "needs_review": 1,
        "chimera_risk": 2,
        "failed": 2,
    }
    return mapping.get(str(status or "").strip().lower(), 1)


def _state_change_status(before: Optional[SurfaceSnapshot], after: Optional[SurfaceSnapshot]) -> str:
    if before is None or after is None:
        return "unavailable"
    comparable_before = {
        "node": before.node,
        "state_status": before.state_status,
        "workflow_run_mode": before.workflow_run_mode,
        "integrity_status": before.integrity_status,
        "integrity_issue_codes": list(before.integrity_issue_codes),
        "active_section": before.active_section,
        "cursor": before.cursor,
    }
    comparable_after = {
        "node": after.node,
        "state_status": after.state_status,
        "workflow_run_mode": after.workflow_run_mode,
        "integrity_status": after.integrity_status,
        "integrity_issue_codes": list(after.integrity_issue_codes),
        "active_section": after.active_section,
        "cursor": after.cursor,
    }
    return "changed" if comparable_before != comparable_after else "unchanged"


def _integrity_change(before: Optional[SurfaceSnapshot], after: Optional[SurfaceSnapshot]) -> str:
    if before is None or after is None:
        return "unknown"
    before_rank = _integrity_rank(before.integrity_status)
    after_rank = _integrity_rank(after.integrity_status)
    if after_rank > before_rank:
        return "worsened"
    if after_rank < before_rank:
        return "improved"
    return "unchanged"


def capture_main_branch_snapshot(workspace, book_id: str) -> Optional[SurfaceSnapshot]:
    return capture_surface_snapshot(workspace, book_id, branch_id="main")


def capture_surface_snapshot(workspace, book_id: str, *, branch_id: str = "main") -> Optional[SurfaceSnapshot]:
    resolved_branch_id = str(branch_id or "main").strip() or "main"
    if resolved_branch_id == "main":
        status = get_workspace_status(workspace, book_id, prefer_emitted=False)
        workflow = get_workflow_snapshot(workspace, book_id, prefer_emitted=False)
        integrity = get_integrity_verdict(workspace, book_id, prefer_emitted=False)
        node = status.current_node
        return SurfaceSnapshot(
            book_id=book_id,
            branch_id="main",
            node=node.to_dict() if node is not None else None,
            state_status=status.state_status,
            workflow_run_mode=workflow.run_mode,
            integrity_status=integrity.status,
            integrity_issue_codes=tuple(issue.code for issue in integrity.issues),
            active_section=dict(status.active_section) if isinstance(status.active_section, dict) else None,
            cursor=dict(status.cursor) if isinstance(status.cursor, dict) else {},
        )

    book_root = Path(workspace) / "books" / book_id
    surface = _build_branch_state_surface(book_root, resolved_branch_id)
    if surface is None:
        return None
    return SurfaceSnapshot(
        book_id=book_id,
        branch_id=resolved_branch_id,
        node=surface.node.to_dict(),
        state_status=surface.state_status,
        workflow_run_mode=surface.workflow_run_mode,
        integrity_status=surface.integrity_status,
        integrity_issue_codes=tuple(surface.integrity_issue_codes),
        active_section=dict(surface.active_section) if isinstance(surface.active_section, dict) else None,
        cursor=dict(surface.cursor) if isinstance(surface.cursor, dict) else {},
    )


def reconcile_main_branch_transition(
    before: Optional[SurfaceSnapshot],
    after: Optional[SurfaceSnapshot],
    *,
    requested_status: str,
) -> tuple[str, Dict[str, Any]]:
    state_change_status = _state_change_status(before, after)
    integrity_change = _integrity_change(before, after)
    final_status = str(requested_status).strip()
    if final_status in {"success", "no_op"} and integrity_change == "worsened":
        final_status = "integrity_degraded"
    elif final_status == "success" and state_change_status == "unchanged":
        final_status = "no_op"

    canonical_change_status = "none"
    if final_status in {"success", "integrity_degraded"} and state_change_status == "changed":
        canonical_change_status = "canonical"

    details: Dict[str, Any] = {
        "pre_reconciliation_status": requested_status,
        "state_change_status": state_change_status,
        "canonical_change_status": canonical_change_status,
        "canonical_changed": canonical_change_status == "canonical",
        "integrity_change": integrity_change,
        "integrity_status_before": before.integrity_status if before is not None else None,
        "integrity_status_after": after.integrity_status if after is not None else None,
        "integrity_issue_codes_before": list(before.integrity_issue_codes) if before is not None else [],
        "integrity_issue_codes_after": list(after.integrity_issue_codes) if after is not None else [],
        "pre_revision_id": (before.node or {}).get("revision_id") if before is not None else None,
        "post_revision_id": (after.node or {}).get("revision_id") if after is not None else None,
        "before_node": before.node if before is not None else None,
        "after_node": after.node if after is not None else None,
    }
    return final_status, details


def reconcile_branch_transition(
    before: Optional[SurfaceSnapshot],
    after: Optional[SurfaceSnapshot],
    *,
    requested_status: str,
) -> tuple[str, Dict[str, Any]]:
    branch_change_status = _state_change_status(before, after)
    integrity_change = _integrity_change(before, after)
    final_status = str(requested_status).strip()
    if final_status in {"success", "no_op"} and integrity_change == "worsened":
        final_status = "integrity_degraded"
    elif final_status == "success" and branch_change_status == "unchanged":
        final_status = "no_op"

    details: Dict[str, Any] = {
        "pre_reconciliation_status": requested_status,
        "branch_change_status": branch_change_status,
        "canonical_changed": False,
        "integrity_change": integrity_change,
        "integrity_status_before": before.integrity_status if before is not None else None,
        "integrity_status_after": after.integrity_status if after is not None else None,
        "integrity_issue_codes_before": list(before.integrity_issue_codes) if before is not None else [],
        "integrity_issue_codes_after": list(after.integrity_issue_codes) if after is not None else [],
        "pre_revision_id": (before.node or {}).get("revision_id") if before is not None else None,
        "post_revision_id": (after.node or {}).get("revision_id") if after is not None else None,
        "before_node": before.node if before is not None else None,
        "after_node": after.node if after is not None else None,
    }
    return final_status, details


def emit_reconciled_main_branch_contracts(
    *,
    workspace,
    book_id: str,
    before_snapshot: Optional[SurfaceSnapshot],
    action: str,
    result_status: str,
    message: str,
    runtime_issues=None,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts=None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> EmissionBundle:
    after_snapshot = capture_main_branch_snapshot(workspace, book_id)
    final_status, reconciliation = reconcile_main_branch_transition(
        before_snapshot,
        after_snapshot,
        requested_status=result_status,
    )
    merged_details = {**dict(details or {}), **reconciliation}
    return emit_main_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        action=action,
        result_status=final_status,
        message=message,
        runtime_issues=runtime_issues,
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details=merged_details,
        request_id=request_id,
    )


def emit_reconciled_branch_contracts(
    *,
    workspace,
    book_id: str,
    branch_id: str,
    before_snapshot: Optional[SurfaceSnapshot],
    action: str,
    result_status: str,
    message: str,
    runtime_issues=None,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts=None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> EmissionBundle:
    after_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    final_status, reconciliation = reconcile_branch_transition(
        before_snapshot,
        after_snapshot,
        requested_status=result_status,
    )
    merged_details = {**dict(details or {}), **reconciliation}
    return emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        action=action,
        result_status=final_status,
        message=message,
        runtime_issues=runtime_issues,
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details=merged_details,
        request_id=request_id,
    )
