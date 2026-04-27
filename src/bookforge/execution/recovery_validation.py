from __future__ import annotations

from pathlib import Path

from bookforge.branching import promote_branch_to_main
from bookforge.branching_store import _evolve_manifest, _load_manifest, _write_manifest
from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ScopeSelector
from bookforge.query import current_main_node, get_outline_lineage_audit
from bookforge.query.recovery import get_recovery_branch_health, get_recovery_manifest
from bookforge.supervision import RuntimeIssue, capture_surface_snapshot

from .recovery_common import (
    advance_recovery_node,
    book_root,
    emit_result,
    now_token,
    request_id,
    write_receipt,
    write_recovery_manifest,
)


def validate_recovery_branch(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "validate_recovery_branch":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("validate_recovery_branch requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    manifest = _load_manifest(root, branch_id)
    audit = get_outline_lineage_audit(workspace, book_id, branch_id=branch_id)
    blockers = []
    if audit.status == "chimera_risk":
        blockers.append("branch still reports chimera_risk")
    actions = {receipt.action for receipt in get_recovery_branch_health(workspace, book_id, branch_id=branch_id).receipts}
    for required in ("quarantine_artifacts", "normalize_outline_scope", "invalidate_scope_outputs"):
        if required not in actions:
            blockers.append(f"{required} has not completed")
    status = "success" if not blockers else "integrity_degraded"
    lifecycle = "promote_ready" if not blockers else "needs_review"
    updated = _evolve_manifest(
        manifest,
        lifecycle_state=lifecycle,
        validation_status="passed" if not blockers else "failed",
        validation_message="Recovery branch passed validation." if not blockers else "; ".join(blockers),
    )
    _write_manifest(root, updated)
    manifest_payload = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    manifest_payload["status"] = "validated" if not blockers else "needs_review"
    manifest_payload["updated_at"] = now_token()
    manifest_payload["validation"] = {"status": updated.validation_status, "blockers": blockers, "outline_lineage_status": audit.status}
    write_recovery_manifest(root, branch_id, manifest_payload)
    advance_recovery_node(workspace, book_id, branch_id, "validate_recovery_branch")
    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="validate_recovery_branch",
        status=status,
        message=updated.validation_message or "Recovery validation completed.",
        details={"blockers": blockers, "outline_lineage_status": audit.status},
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status=status,
        message=updated.validation_message or "Recovery validation completed.",
        receipt=receipt,
        before_snapshot=before_snapshot,
        runtime_issue=RuntimeIssue(
            category="chimera_risk",
            code="recovery_validation_failed",
            severity="high",
            message="Recovery branch validation failed.",
            details={"blockers": blockers},
        )
        if blockers
        else None,
    )


def promote_recovery_branch(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "promote_recovery_branch":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("promote_recovery_branch requires a derived recovery branch.")
    book_id = request.selector.book_id
    health = get_recovery_branch_health(workspace, book_id, branch_id=branch_id)
    if health.status != "healthy":
        raise ValueError(f"Recovery branch {branch_id} is not healthy: {health.blockers}")
    promote_branch_to_main(workspace, book_id, branch_id, request_id=request.request_id)
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("Unable to resolve main node after recovery promotion.")
    return ExecutionResult(
        result_id=request_id(book_id, request.action, branch_id, "success"),
        action=request.action,
        status="success",
        node=node,
        selector=ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID),
        message=f"Recovery branch {branch_id} promoted to main.",
        details={"source_branch_id": branch_id, "recovery_health": health.to_dict()},
        emitted_at=now_token(),
        request_id=request.request_id,
    )
