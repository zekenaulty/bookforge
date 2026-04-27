from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import json

from bookforge.contracts import (
    ExecutionRequest,
    ExecutionResult,
    MAIN_BRANCH_ID,
    ProducedArtifactReceipt,
    RecoveryAnchor,
    RecoveryReceipt,
    RecoveryScope,
    ScopeSelector,
    TimelineNodeRef,
)
from bookforge.query import current_execution_node, current_main_node, get_outline_lineage_audit
from bookforge.query.recovery import promotion_removals_path, recovery_manifest_path, recovery_receipts_path
from bookforge.supervision import (
    RuntimeIssue,
    capture_surface_snapshot,
    emit_reconciled_branch_contracts,
)
from bookforge.supervision import paths as supervision_paths


def now_token() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_id(book_id: str, action: str, *parts: object) -> str:
    seed = "|".join([book_id, action, *(str(part or "") for part in parts), now_token()])
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def book_root(workspace: Path, book_id: str) -> Path:
    return Path(workspace) / "books" / book_id


def execution_root(root: Path, branch_id: str) -> Path:
    if branch_id == MAIN_BRANCH_ID:
        return root
    return supervision_paths.branch_snapshot_root(root, branch_id)


def write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def append_jsonl(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path


def relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def selected_scopes(workspace: Path, book_id: str, scopes: Optional[List[Dict[str, int]]] = None) -> List[Dict[str, int]]:
    if scopes:
        return RecoveryScope(affected_scopes=scopes).affected_scopes
    audit = get_outline_lineage_audit(workspace, book_id)
    return [{"chapter_id": row.chapter_id, "section_id": row.section_id} for row in audit.affected_sections]


def load_recovery_scope(manifest: Dict[str, Any]) -> RecoveryScope:
    return RecoveryScope.from_dict(manifest.get("scope") or {})


def load_recovery_anchor(manifest: Dict[str, Any]) -> RecoveryAnchor:
    return RecoveryAnchor.from_dict(manifest.get("anchor") or {})


def write_recovery_manifest(root: Path, branch_id: str, payload: Dict[str, Any]) -> Path:
    return write_json(recovery_manifest_path(root, branch_id), payload)


def advance_recovery_node(workspace: Path, book_id: str, branch_id: str, phase_id: str) -> TimelineNodeRef:
    root = book_root(workspace, book_id)
    current = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if current is None:
        raise ValueError(f"No current node is available for recovery branch {branch_id}.")
    node = TimelineNodeRef(
        book_id=current.book_id,
        workflow_family="recovery_import",
        source_run_id=current.source_run_id,
        branch_id=branch_id,
        fork_group_id=current.fork_group_id,
        chapter=current.chapter,
        section=current.section,
        scene=current.scene,
        phase_id=phase_id,
        turn_id=current.turn_id,
        revision_id=request_id(book_id, phase_id, branch_id),
    )
    write_json(supervision_paths.current_node_path(root, branch_id), node.to_dict())
    return node


def record_promotion_removals(root: Path, branch_id: str, rel_paths: Iterable[str]) -> Path:
    path = promotion_removals_path(root, branch_id)
    payload = read_json(path)
    existing = {str(item).strip() for item in payload.get("remove_paths", []) if str(item).strip()}
    existing.update(str(item).strip() for item in rel_paths if str(item).strip())
    return write_json(
        path,
        {
            "schema_version": "promotion_removals_v1",
            "branch_id": branch_id,
            "updated_at": now_token(),
            "remove_paths": sorted(existing),
        },
    )


def write_receipt(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    action: str,
    status: str,
    message: str,
    artifact_paths: Optional[Dict[str, str]] = None,
    removed_active_paths: Optional[List[str]] = None,
    quarantined_paths: Optional[List[Dict[str, str]]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> RecoveryReceipt:
    root = book_root(workspace, book_id)
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for recovery branch {branch_id}.")
    receipt = RecoveryReceipt(
        receipt_id=request_id(book_id, action, branch_id, status),
        action=action,
        branch_id=branch_id,
        node=node,
        status=status,
        message=message,
        artifact_paths=dict(artifact_paths or {}),
        removed_active_paths=list(removed_active_paths or []),
        quarantined_paths=list(quarantined_paths or []),
        details=dict(details or {}),
    )
    append_jsonl(recovery_receipts_path(root, branch_id), receipt.to_dict())
    return receipt


def emit_result(
    workspace: Path,
    book_id: str,
    request: ExecutionRequest,
    *,
    status: str,
    message: str,
    receipt: Optional[RecoveryReceipt] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts: Optional[List[ProducedArtifactReceipt]] = None,
    details: Optional[Dict[str, Any]] = None,
    runtime_issue: Optional[RuntimeIssue] = None,
    before_snapshot=None,
) -> ExecutionResult:
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError(f"{request.action} requires a derived recovery branch.")
    merged_details = dict(details or {})
    if receipt is not None:
        merged_details["recovery_receipt"] = receipt.to_dict()
    bundle = emit_reconciled_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        before_snapshot=before_snapshot or capture_surface_snapshot(workspace, book_id, branch_id=branch_id),
        action=request.action,
        result_status=status,
        request_id=request.request_id,
        message=message,
        runtime_issues=[runtime_issue] if runtime_issue else None,
        artifact_paths=dict(artifact_paths or {}),
        produced_artifacts=list(produced_artifacts or []),
        details=merged_details,
    )
    if bundle.execution_result is not None:
        return bundle.execution_result
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError("Unable to resolve node for recovery execution result.")
    return ExecutionResult(
        result_id=request_id(book_id, request.action, branch_id, status),
        action=request.action,
        status=status,
        node=node,
        selector=request.selector,
        message=message,
        artifact_paths=dict(artifact_paths or {}),
        produced_artifacts=list(produced_artifacts or []),
        details=merged_details,
        emitted_at=now_token(),
        request_id=request.request_id,
    )


def build_create_recovery_branch_request(
    workspace: Path,
    book_id: str,
    *,
    anchor_type: str,
    source_run_id: Optional[str] = None,
    affected_scopes: Optional[List[Dict[str, int]]] = None,
    branch_id: Optional[str] = None,
    salvage_policy: str = "none",
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    scope = RecoveryScope(affected_scopes=selected_scopes(workspace, book_id, affected_scopes), salvage_policy=salvage_policy)
    anchor = RecoveryAnchor(anchor_type=anchor_type, source_run_id=source_run_id)
    return ExecutionRequest(
        request_id=request_id(book_id, "create_recovery_branch", anchor_type, source_run_id, branch_id),
        action="create_recovery_branch",
        selector=ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID, workflow_family="recovery_import"),
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=now_token(),
        details={"branch_id": str(branch_id or "").strip() or None, "anchor": anchor.to_dict(), "scope": scope.to_dict()},
    )


def build_recovery_branch_request(workspace: Path, book_id: str, *, action: str, branch_id: str) -> ExecutionRequest:
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    return ExecutionRequest(
        request_id=request_id(book_id, action, branch_id),
        action=action,
        selector=ScopeSelector(book_id=book_id, branch_id=branch_id, workflow_family="recovery_import"),
        expected_node=node,
        branch_id=branch_id,
        requested_at=now_token(),
        details={},
    )
