from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.contracts import (
    BranchManifest,
    ExecutionResult,
    IssueTicket,
    MAIN_BRANCH_ID,
    ProducedArtifactReceipt,
    ScopeSelector,
    StateSurface,
    TimelineNodeRef,
    classify_source_artifact,
)
from bookforge.query.integrity import get_integrity_verdict
from bookforge.query.workflow import get_workflow_snapshot
from bookforge.query import _common as query_common
from bookforge.query.workspace import get_workspace_status

from . import paths


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class RuntimeIssue:
    category: str
    code: str
    severity: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EmissionBundle:
    node: Optional[TimelineNodeRef]
    state_surface: Optional[StateSurface]
    issue_tickets: List[IssueTicket]
    execution_result: Optional[ExecutionResult]


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _selector_for_node(book_id: str, node: TimelineNodeRef) -> ScopeSelector:
    return ScopeSelector(
        book_id=book_id,
        branch_id=node.branch_id,
        fork_group_id=node.fork_group_id,
        workflow_family=node.workflow_family,
        chapter=node.chapter,
        section=node.section,
        scene=node.scene,
        phase_id=node.phase_id,
        turn_id=node.turn_id,
    )


def _selector_for_branch(book_id: str, node: TimelineNodeRef) -> ScopeSelector:
    return ScopeSelector(
        book_id=book_id,
        branch_id=node.branch_id,
        fork_group_id=node.fork_group_id,
    )


def _ticket_category(code: str) -> str:
    if code in {"source_run_mismatch", "mutable_source_materialization"}:
        return "lineage_conflict"
    if code == "stale_parent":
        return "stale_parent"
    if code == "stale_write":
        return "stale_write"
    if code == "overscoped_recovery":
        return "overscoped_recovery"
    if code in {"stale_section_drafts_present", "duplicate_character_name", "branch_fork_contamination"}:
        return "chimera_risk"
    return "scope_contract_violation"


def _ticket_id(node: TimelineNodeRef, category: str, code: str) -> str:
    seed = "|".join(
        [
            node.book_id,
            node.branch_id,
            node.revision_id,
            category,
            code,
            str(node.chapter or ""),
            str(node.section or ""),
            str(node.scene or ""),
        ]
    )
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _integrity_tickets(book_id: str, node: TimelineNodeRef, verdict) -> List[IssueTicket]:
    selector = _selector_for_branch(book_id, node)
    now = _now_iso()
    tickets: List[IssueTicket] = []
    for issue in list(getattr(verdict, "issues", []) or []):
        code = str(getattr(issue, "code", "") or "").strip()
        severity = str(getattr(issue, "severity", "") or "").strip() or "medium"
        message = str(getattr(issue, "message", "") or "").strip() or code
        details = getattr(issue, "details", {}) or {}
        if not code:
            continue
        tickets.append(
            IssueTicket(
                ticket_id=_ticket_id(node, _ticket_category(code), code),
                category=_ticket_category(code),
                code=code,
                severity=severity,
                message=message,
                node=node,
                selector=selector,
                branch_scope=node.branch_id,
                details=details if isinstance(details, dict) else {},
                detected_at=now,
            )
        )
    return tickets


def _runtime_ticket(book_id: str, node: TimelineNodeRef, issue: RuntimeIssue) -> IssueTicket:
    return IssueTicket(
        ticket_id=_ticket_id(node, issue.category, issue.code),
        category=issue.category,
        code=issue.code,
        severity=issue.severity,
        message=issue.message,
        node=node,
        selector=_selector_for_node(book_id, node),
        branch_scope=node.branch_id,
        details=dict(issue.details),
        detected_at=_now_iso(),
    )


def _merge_tickets(*groups: List[IssueTicket]) -> List[IssueTicket]:
    merged: Dict[str, IssueTicket] = {}
    for group in groups:
        for ticket in group:
            merged[ticket.ticket_id] = ticket
    return list(merged.values())


def _chapter_status_counts(registry: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        status = str(chapter.get("chapter_status") or "").strip()
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def _load_branch_manifest(book_root: Path, branch_id: str) -> Optional[BranchManifest]:
    payload = _read_json(paths.branch_manifest_path(book_root, branch_id))
    if not isinstance(payload, dict):
        return None
    try:
        return BranchManifest.from_dict(payload)
    except ValueError:
        return None


def _load_branch_node(book_root: Path, branch_id: str) -> Optional[TimelineNodeRef]:
    payload = _read_json(paths.current_node_path(book_root, branch_id))
    if not isinstance(payload, dict):
        return None
    try:
        return TimelineNodeRef.from_dict(payload)
    except ValueError:
        return None


def _build_state_surface(workspace: Path, book_id: str) -> Optional[StateSurface]:
    status = get_workspace_status(workspace, book_id, prefer_emitted=False)
    workflow = get_workflow_snapshot(workspace, book_id, prefer_emitted=False)
    integrity = get_integrity_verdict(workspace, book_id, prefer_emitted=False)
    node = status.current_node
    if node is None:
        return None
    return StateSurface(
        book_id=book_id,
        node=node,
        selector=_selector_for_branch(book_id, node),
        state_status=status.state_status,
        workflow_run_mode=workflow.run_mode,
        workflow_source_run_id=status.source_run_id,
        source_artifact_class=workflow.source_artifact_class,
        source_artifact_path=workflow.source_artifact_path,
        active_section=status.active_section,
        cursor=status.cursor,
        integrity_status=integrity.status,
        integrity_issue_codes=[issue.code for issue in integrity.issues],
        branch_count=len(status.branches),
        chapter_status_counts={str(key): int(value) for key, value in getattr(status, "chapter_status_counts", {}).items()} if hasattr(status, "chapter_status_counts") else {},
        updated_at=_now_iso(),
    )


def _build_branch_state_surface(book_root: Path, branch_id: str) -> Optional[StateSurface]:
    manifest = _load_branch_manifest(book_root, branch_id)
    node = _load_branch_node(book_root, branch_id)
    if manifest is None or node is None:
        return None
    snapshot_root = paths.branch_snapshot_root(book_root, branch_id)
    state = _read_json(paths.branch_snapshot_state_path(book_root, branch_id)) or {}
    registry = _read_json(paths.branch_snapshot_outline_root(book_root, branch_id) / "snapshot_registry.json") or {}
    outline_path = paths.branch_snapshot_outline_root(book_root, branch_id) / "outline.json"
    source_artifact_path = outline_path.as_posix() if outline_path.exists() else None
    source_artifact_class = classify_source_artifact(outline_path).value if outline_path.exists() else None
    return StateSurface(
        book_id=manifest.book_id,
        node=node,
        selector=_selector_for_branch(manifest.book_id, node),
        state_status=str(state.get("status") or "").strip() or None,
        workflow_run_mode=manifest.lifecycle_state,
        workflow_source_run_id=manifest.source_run_id,
        source_artifact_class=source_artifact_class,
        source_artifact_path=source_artifact_path,
        active_section=registry.get("active_section") if isinstance(registry.get("active_section"), dict) else None,
        cursor=state.get("cursor") if isinstance(state.get("cursor"), dict) else {},
        integrity_status=(manifest.validation_status or "healthy"),
        integrity_issue_codes=[],
        branch_count=len(query_common.list_branch_ids(book_root)),
        chapter_status_counts=_chapter_status_counts(registry),
        updated_at=_now_iso(),
    )


def emit_branch_contracts(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    action: Optional[str] = None,
    result_status: Optional[str] = None,
    request_id: Optional[str] = None,
    message: Optional[str] = None,
    runtime_issues: Optional[List[RuntimeIssue]] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts: Optional[List[ProducedArtifactReceipt]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> EmissionBundle:
    book_root = workspace / "books" / book_id
    if branch_id == MAIN_BRANCH_ID:
        state_surface = _build_state_surface(workspace, book_id)
    else:
        state_surface = _build_branch_state_surface(book_root, branch_id)
    if state_surface is None:
        return EmissionBundle(node=None, state_surface=None, issue_tickets=[], execution_result=None)

    node = state_surface.node
    _write_json(paths.current_node_path(book_root, node.branch_id), node.to_dict())
    _write_json(paths.state_surface_latest_path(book_root, node.branch_id), state_surface.to_dict())
    _append_jsonl(paths.state_surface_history_path(book_root, node.branch_id), state_surface.to_dict())

    integrity_tickets: List[IssueTicket] = []
    if branch_id == MAIN_BRANCH_ID:
        integrity = get_integrity_verdict(workspace, book_id, prefer_emitted=False)
        integrity_tickets = _integrity_tickets(book_id, node, integrity)
    runtime_tickets = [_runtime_ticket(book_id, node, issue) for issue in list(runtime_issues or [])]
    tickets = _merge_tickets(integrity_tickets, runtime_tickets)
    issues_payload = {
        "schema_version": "issue_ticket_list_v1",
        "book_id": book_id,
        "branch_id": node.branch_id,
        "updated_at": _now_iso(),
        "tickets": [ticket.to_dict() for ticket in tickets],
    }
    _write_json(paths.issues_latest_path(book_root, node.branch_id), issues_payload)
    for ticket in tickets:
        _append_jsonl(paths.issues_history_path(book_root, node.branch_id), ticket.to_dict())

    execution_result = None
    if action and result_status:
        execution_result = ExecutionResult(
            result_id=hashlib.sha1(
                "|".join([book_id, node.branch_id, node.revision_id, action, result_status, _now_iso()]).encode("utf-8")
            ).hexdigest()[:16],
            action=action,
            status=result_status,
            node=node,
            selector=_selector_for_node(book_id, node),
            message=message,
            issue_ticket_ids=[ticket.ticket_id for ticket in tickets],
            artifact_paths=dict(artifact_paths or {}),
            produced_artifacts=list(produced_artifacts or []),
            details=dict(details or {}),
            emitted_at=_now_iso(),
            request_id=request_id,
        )
        _append_jsonl(paths.execution_results_path(book_root, node.branch_id), execution_result.to_dict())

    return EmissionBundle(
        node=node,
        state_surface=state_surface,
        issue_tickets=tickets,
        execution_result=execution_result,
    )


def emit_main_branch_contracts(
    workspace: Path,
    book_id: str,
    *,
    action: Optional[str] = None,
    result_status: Optional[str] = None,
    request_id: Optional[str] = None,
    message: Optional[str] = None,
    runtime_issues: Optional[List[RuntimeIssue]] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts: Optional[List[ProducedArtifactReceipt]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> EmissionBundle:
    return emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        action=action,
        result_status=result_status,
        request_id=request_id,
        message=message,
        runtime_issues=runtime_issues,
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details=details,
    )
