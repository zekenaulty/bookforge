from __future__ import annotations

from pathlib import Path
from typing import Optional

from bookforge.contracts import (
    ASSEMBLY_BRANCH_PREFIX,
    BranchManifest,
    ScopeSelector,
    canonical_change_status_for_branch_lifecycle,
)
from bookforge.query import current_main_node, resolve_scope_selector
from bookforge.supervision import emit_branch_contracts

from .branching_store import (
    _book_root,
    _branch_node,
    _branch_selector,
    _copy_book_projection_to_branch,
    _generate_branch_id,
    _load_manifest,
    _now_iso,
    _write_branch_node,
    _write_manifest,
    load_branch_manifest,
)


def create_branch(
    workspace: Path,
    book_id: str,
    selector: ScopeSelector,
    *,
    branch_id: Optional[str] = None,
    fork_group_id: Optional[str] = None,
    merge_operation: str = "promotion",
    branch_role: str = "rerun",
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    parent_node = resolve_scope_selector(workspace, selector) or current_main_node(workspace, book_id, prefer_emitted=False)
    if parent_node is None:
        raise ValueError("Unable to resolve parent node for branch creation.")
    if parent_node.branch_id == "main":
        live_main = current_main_node(workspace, book_id, prefer_emitted=False)
        if live_main is not None and parent_node.revision_id != live_main.revision_id:
            raise ValueError(
                f"Cannot create branch from stale parent main@{parent_node.revision_id}; current main revision is {live_main.revision_id}."
            )
    created_at = _now_iso()
    resolved_branch_id = str(branch_id or "").strip()
    if not resolved_branch_id:
        prefix = ASSEMBLY_BRANCH_PREFIX if merge_operation == "assembly" else "branch"
        resolved_branch_id = _generate_branch_id(
            prefix,
            [
                book_id,
                parent_node.branch_id,
                parent_node.revision_id,
                selector.workflow_family or parent_node.workflow_family,
                selector.chapter or parent_node.chapter or "",
                selector.section or parent_node.section or "",
                created_at,
            ],
        )
    if resolved_branch_id == "main":
        raise ValueError("Derived branch id cannot be 'main'.")

    _copy_book_projection_to_branch(book_root, resolved_branch_id, source_branch_id=parent_node.branch_id)
    node = _branch_node(parent_node, selector, resolved_branch_id, fork_group_id)
    selector_payload = _branch_selector(book_id, resolved_branch_id, parent_node, selector, fork_group_id)
    manifest = BranchManifest(
        book_id=book_id,
        branch_id=resolved_branch_id,
        fork_group_id=fork_group_id,
        lifecycle_state="active",
        merge_operation=merge_operation,
        workflow_family=node.workflow_family,
        source_run_id=parent_node.source_run_id,
        parent_node=parent_node,
        selector=selector_payload,
        parent_snapshot_revision=parent_node.revision_id,
        branch_role=branch_role,
        created_at=created_at,
        updated_at=created_at,
    )
    _write_manifest(book_root, manifest)
    _write_branch_node(book_root, node)
    emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=resolved_branch_id,
        action="create_branch",
        result_status="success",
        request_id=request_id,
        message=f"Derived branch {resolved_branch_id} created from {parent_node.branch_id}@{parent_node.revision_id}.",
        details={
            "merge_operation": merge_operation,
            "branch_role": branch_role,
            "canonical_change_status": canonical_change_status_for_branch_lifecycle("active"),
        },
    )
    return manifest


def branch_can_read_branch(workspace: Path, book_id: str, reader_branch_id: str, target_branch_id: str) -> bool:
    if reader_branch_id == target_branch_id:
        return True
    if target_branch_id == "main":
        return True
    reader = load_branch_manifest(workspace, book_id, reader_branch_id)
    target = load_branch_manifest(workspace, book_id, target_branch_id)
    if reader.fork_group_id and reader.fork_group_id == target.fork_group_id:
        return False
    return False


def load_branch_for_action(workspace: Path, book_id: str, branch_id: str) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    return _load_manifest(book_root, branch_id)
