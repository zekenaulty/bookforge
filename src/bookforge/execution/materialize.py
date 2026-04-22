from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import hashlib
import json

from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ScopeSelector
from bookforge.query import current_main_node
from bookforge.section_workflow import (
    finalize_chapter_from_locked_sections,
    freeze_section_from_phase03_artifact,
    initialize_section_workflow,
    lock_section_from_written_state,
)
from bookforge.supervision import paths as supervision_paths


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
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id)
    request_seed = "|".join(
        [
            book_id,
            "finalize_chapter_from_locked_sections",
            str(chapter_id),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="finalize_chapter_from_locked_sections",
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=MAIN_BRANCH_ID,
            workflow_family=(node.workflow_family if node else "section_local_outline"),
            chapter=chapter_id,
        ),
        expected_node=None,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
        },
    )


def build_lock_section_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    section_id: int,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id)
    request_seed = "|".join(
        [
            book_id,
            "lock_section_from_written_state",
            str(chapter_id),
            str(section_id),
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=hashlib.sha1(request_seed.encode("utf-8")).hexdigest()[:16],
        action="lock_section_from_written_state",
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


def finalize_chapter(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "finalize_chapter_from_locked_sections":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("finalize_chapter_from_locked_sections only supports main-branch execution.")
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


def lock_section(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "lock_section_from_written_state":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("lock_section_from_written_state only supports main-branch execution.")
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
