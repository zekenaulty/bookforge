from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import hashlib
import json

from bookforge.branching import (
    create_assembly_branch,
    create_branch,
    discard_branch,
    promote_branch_to_main,
    record_assembly_validation,
)
from bookforge.contracts import (
    ExecutionRequest,
    ExecutionResult,
    MAIN_BRANCH_ID,
    ScopeSelector,
    TimelineNodeRef,
    execution_result_for_branch_lifecycle,
)
from bookforge.query import current_main_node
from bookforge.supervision import paths as supervision_paths


def _now_token() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_execution_result_for_request(book_root: Path, branch_id: str, request_id: str) -> Optional[ExecutionResult]:
    result_path = supervision_paths.execution_results_path(book_root, branch_id if branch_id != MAIN_BRANCH_ID else None)
    if not result_path.exists():
        return None
    lines = [line.strip() for line in result_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in reversed(lines):
        payload = json.loads(line)
        if str(payload.get("request_id") or "").strip() == request_id:
            return ExecutionResult.from_dict(payload)
    return None


def _load_node_for_branch(book_root: Path, branch_id: str) -> Optional[TimelineNodeRef]:
    node_path = supervision_paths.current_node_path(book_root, branch_id if branch_id != MAIN_BRANCH_ID else None)
    if not node_path.exists():
        return None
    payload = json.loads(node_path.read_text(encoding="utf-8"))
    return TimelineNodeRef.from_dict(payload) if isinstance(payload, dict) else None


def build_create_branch_request(
    workspace: Path,
    book_id: str,
    *,
    chapter: Optional[int] = None,
    section: Optional[int] = None,
    branch_id: Optional[str] = None,
    fork_group_id: Optional[str] = None,
    merge_operation: str = "promotion",
    branch_role: str = "rerun",
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id)
    workflow_family = node.workflow_family if node else "section_local_outline"
    resolved_chapter = chapter if chapter is not None else (node.chapter if node is not None else None)
    resolved_section = section if section is not None else (node.section if node is not None else None)
    request_seed = "|".join(
        [
            book_id,
            "create_branch",
            str(resolved_chapter or ""),
            str(resolved_section or ""),
            str(branch_id or ""),
            str(fork_group_id or ""),
            merge_operation,
            branch_role,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="create_branch",
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=MAIN_BRANCH_ID,
            workflow_family=workflow_family,
            chapter=resolved_chapter,
            section=resolved_section,
        ),
        expected_node=None,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "branch_id": str(branch_id or "").strip() or None,
            "fork_group_id": str(fork_group_id or "").strip() or None,
            "merge_operation": merge_operation,
            "branch_role": branch_role,
        },
    )


def build_create_assembly_branch_request(
    book_id: str,
    *,
    fork_group_id: str,
    chapter_id: Optional[int] = None,
    branch_id: Optional[str] = None,
) -> ExecutionRequest:
    request_seed = "|".join(
        [
            book_id,
            "create_assembly_branch",
            str(fork_group_id),
            str(chapter_id or ""),
            str(branch_id or ""),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="create_assembly_branch",
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=MAIN_BRANCH_ID,
            fork_group_id=str(fork_group_id).strip() or None,
            chapter=chapter_id,
        ),
        expected_node=None,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={"branch_id": str(branch_id or "").strip() or None},
    )


def build_discard_branch_request(
    book_id: str,
    *,
    branch_id: str,
    reason: Optional[str] = None,
) -> ExecutionRequest:
    request_seed = "|".join(
        [
            book_id,
            "discard_branch",
            str(branch_id),
            str(reason or ""),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="discard_branch",
        selector=ScopeSelector(book_id=book_id, branch_id=branch_id),
        expected_node=None,
        branch_id=branch_id,
        requested_at=_now_token(),
        details={"reason": str(reason or "").strip() or None},
    )


def build_promote_branch_request(
    book_id: str,
    *,
    branch_id: str,
) -> ExecutionRequest:
    request_seed = "|".join(
        [
            book_id,
            "promote_branch_to_main",
            str(branch_id),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="promote_branch_to_main",
        selector=ScopeSelector(book_id=book_id, branch_id=branch_id),
        expected_node=None,
        branch_id=branch_id,
        requested_at=_now_token(),
        details={},
    )


def build_record_assembly_validation_request(
    book_id: str,
    *,
    branch_id: str,
    passed: bool,
    message: Optional[str] = None,
) -> ExecutionRequest:
    request_seed = "|".join(
        [
            book_id,
            "record_assembly_validation",
            str(branch_id),
            str(bool(passed)),
            str(message or ""),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="record_assembly_validation",
        selector=ScopeSelector(book_id=book_id, branch_id=branch_id),
        expected_node=None,
        branch_id=branch_id,
        requested_at=_now_token(),
        details={
            "passed": bool(passed),
            "message": str(message or "").strip() or None,
        },
    )


def create_branch_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "create_branch":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("create_branch only supports main-branch derivation requests.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    manifest = create_branch(
        workspace=workspace,
        book_id=book_id,
        selector=request.selector,
        branch_id=request.details.get("branch_id"),
        fork_group_id=request.details.get("fork_group_id"),
        merge_operation=str(request.details.get("merge_operation") or "promotion"),
        branch_role=str(request.details.get("branch_role") or "rerun"),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, manifest.branch_id, request.request_id)
    if emitted is not None:
        if emitted.action == request.action:
            return emitted
        return ExecutionResult(
            result_id=emitted.result_id,
            action=request.action,
            status=emitted.status,
            node=emitted.node,
            selector=request.selector,
            message=emitted.message,
            issue_ticket_ids=list(emitted.issue_ticket_ids),
            artifact_paths=dict(emitted.artifact_paths),
            details={
                **dict(emitted.details),
                "fork_group_id": manifest.fork_group_id,
                "merge_operation": manifest.merge_operation,
                "branch_role": manifest.branch_role,
            },
            emitted_at=emitted.emitted_at,
            request_id=emitted.request_id,
        )

    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, "success", _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status="success",
        node=manifest.parent_node,
        selector=request.selector,
        message=f"Derived branch {manifest.branch_id} created.",
        details={
            "branch_id": manifest.branch_id,
            "merge_operation": manifest.merge_operation,
            "branch_role": manifest.branch_role,
        },
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def create_assembly_branch_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "create_assembly_branch":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("create_assembly_branch only supports main-branch derivation requests.")
    fork_group_id = str(request.selector.fork_group_id or "").strip()
    if not fork_group_id:
        raise ValueError("create_assembly_branch requires selector.fork_group_id.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    manifest = create_assembly_branch(
        workspace=workspace,
        book_id=book_id,
        fork_group_id=fork_group_id,
        chapter_id=request.selector.chapter,
        branch_id=request.details.get("branch_id"),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, manifest.branch_id, request.request_id)
    if emitted is not None:
        if emitted.action == request.action:
            return emitted
        return ExecutionResult(
            result_id=emitted.result_id,
            action=request.action,
            status=emitted.status,
            node=emitted.node,
            selector=request.selector,
            message=emitted.message,
            issue_ticket_ids=list(emitted.issue_ticket_ids),
            artifact_paths=dict(emitted.artifact_paths),
            details={
                **dict(emitted.details),
                "branch_id": manifest.branch_id,
                "fork_group_id": manifest.fork_group_id,
                "merge_operation": manifest.merge_operation,
                "branch_role": manifest.branch_role,
            },
            emitted_at=emitted.emitted_at,
            request_id=emitted.request_id,
        )
    node = _load_node_for_branch(book_root, manifest.branch_id)
    if node is None:
        raise ValueError(f"Unable to resolve emitted node for assembly branch {manifest.branch_id}.")

    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, "success", _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status="success",
        node=node,
        selector=request.selector,
        message=f"Assembly branch {manifest.branch_id} created.",
        details={
            "branch_id": manifest.branch_id,
            "fork_group_id": manifest.fork_group_id,
            "merge_operation": manifest.merge_operation,
            "branch_role": manifest.branch_role,
        },
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def discard_branch_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "discard_branch":
        raise ValueError("Unsupported execution action.")
    target_branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not target_branch_id or target_branch_id == MAIN_BRANCH_ID:
        raise ValueError("discard_branch requires a derived branch target.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    manifest = discard_branch(
        workspace=workspace,
        book_id=book_id,
        branch_id=target_branch_id,
        reason=request.details.get("reason"),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, manifest.branch_id, request.request_id)
    if emitted is not None:
        return emitted
    node = _load_node_for_branch(book_root, manifest.branch_id)
    if node is None:
        raise ValueError(f"Unable to resolve emitted node for discarded branch {manifest.branch_id}.")

    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join(
                [
                    book_id,
                    request.request_id,
                    execution_result_for_branch_lifecycle("discard"),
                    _now_token(),
                ]
            ).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status=execution_result_for_branch_lifecycle("discard"),
        node=node,
        selector=request.selector,
        message=f"Branch {manifest.branch_id} discarded.",
        details={"reason": request.details.get("reason"), "branch_id": manifest.branch_id},
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def promote_branch_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "promote_branch_to_main":
        raise ValueError("Unsupported execution action.")
    target_branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not target_branch_id or target_branch_id == MAIN_BRANCH_ID:
        raise ValueError("promote_branch_to_main requires a derived branch target.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    manifest = promote_branch_to_main(
        workspace=workspace,
        book_id=book_id,
        branch_id=target_branch_id,
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, MAIN_BRANCH_ID, request.request_id)
    if emitted is not None:
        return emitted
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"Unable to resolve emitted node for promoted branch {manifest.branch_id}.")

    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([book_id, request.request_id, "success", _now_token()]).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status="success",
        node=node,
        selector=ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID),
        message=f"Branch {manifest.branch_id} promoted to main.",
        details={
            "source_branch_id": manifest.branch_id,
            "merge_operation": manifest.merge_operation,
            "branch_lifecycle_state": "promoted",
        },
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def record_assembly_validation_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "record_assembly_validation":
        raise ValueError("Unsupported execution action.")
    target_branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not target_branch_id or target_branch_id == MAIN_BRANCH_ID:
        raise ValueError("record_assembly_validation requires a derived assembly branch target.")

    book_id = request.selector.book_id
    book_root = Path(workspace) / "books" / book_id
    manifest = record_assembly_validation(
        workspace=workspace,
        book_id=book_id,
        branch_id=target_branch_id,
        passed=bool(request.details.get("passed")),
        message=request.details.get("message"),
        request_id=request.request_id,
    )
    emitted = _load_execution_result_for_request(book_root, manifest.branch_id, request.request_id)
    if emitted is not None:
        return emitted
    node = _load_node_for_branch(book_root, manifest.branch_id)
    if node is None:
        raise ValueError(f"Unable to resolve emitted node for assembly validation on {manifest.branch_id}.")

    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join(
                [
                    book_id,
                    request.request_id,
                    execution_result_for_branch_lifecycle(manifest.lifecycle_state),
                    _now_token(),
                ]
            ).encode("utf-8")
        ).hexdigest()[:16],
        action=request.action,
        status=execution_result_for_branch_lifecycle(manifest.lifecycle_state),
        node=node,
        selector=request.selector,
        message=request.details.get("message") or "Assembly validation recorded.",
        details={
            "validation_status": manifest.validation_status,
            "branch_id": manifest.branch_id,
            "merge_operation": manifest.merge_operation,
        },
        emitted_at=_now_token(),
        request_id=request.request_id,
    )
