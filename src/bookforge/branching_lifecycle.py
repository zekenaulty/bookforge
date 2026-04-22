from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from bookforge import section_workflow as sw
from bookforge.contracts import (
    ASSEMBLY_BRANCH_PREFIX,
    BranchManifest,
    ScopeSelector,
    canonical_change_status_for_branch_lifecycle,
    execution_result_for_branch_lifecycle,
)
from bookforge.query import _common as query_common
from bookforge.query import current_main_node
from bookforge.supervision import (
    capture_surface_snapshot,
    capture_main_branch_snapshot,
    emit_branch_contracts,
    emit_reconciled_branch_contracts,
    emit_reconciled_main_branch_contracts,
)

from .branching_fork import create_branch
from .branching_store import (
    _book_root,
    _branch_snapshot_root,
    _copy_if_exists,
    _copytree_if_exists,
    _evolve_manifest,
    _generate_branch_id,
    _load_manifest,
    _now_iso,
    _write_manifest,
)


def discard_branch(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    manifest = _load_manifest(book_root, branch_id)
    updated = _evolve_manifest(manifest, lifecycle_state="discard", validation_message=reason or manifest.validation_message)
    _write_manifest(book_root, updated)
    emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        action="discard_branch",
        result_status=execution_result_for_branch_lifecycle("discard"),
        request_id=request_id,
        message=f"Branch {branch_id} discarded.",
        details={
            "branch_id": branch_id,
            "reason": str(reason or "").strip() or None,
            "canonical_change_status": canonical_change_status_for_branch_lifecycle("discard"),
        },
    )
    return updated


def create_assembly_branch(
    workspace: Path,
    book_id: str,
    fork_group_id: str,
    *,
    chapter_id: Optional[int] = None,
    branch_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    sibling_manifests: List[BranchManifest] = []
    for sibling_id in query_common.list_branch_ids(book_root):
        try:
            manifest = _load_manifest(book_root, sibling_id)
        except Exception:
            continue
        if manifest.fork_group_id == str(fork_group_id).strip():
            sibling_manifests.append(manifest)
    if not sibling_manifests:
        raise ValueError(f"No sibling branches found for fork group {fork_group_id}.")

    parent_signature = sibling_manifests[0].parent_node.to_dict()
    parent_revision = sibling_manifests[0].parent_snapshot_revision
    for manifest in sibling_manifests[1:]:
        if manifest.parent_node.to_dict() != parent_signature or manifest.parent_snapshot_revision != parent_revision:
            raise ValueError("Fork-group siblings do not share the same frozen parent snapshot.")

    live_main = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_main is not None and live_main.revision_id != parent_revision:
        raise ValueError("Fork-group parent snapshot is stale against current main revision; rebase or recreate before assembly.")

    parent_node = sibling_manifests[0].parent_node
    resolved_branch_id = str(branch_id or "").strip()
    if not resolved_branch_id:
        resolved_branch_id = _generate_branch_id(
            ASSEMBLY_BRANCH_PREFIX,
            [book_id, fork_group_id, parent_revision, chapter_id or "", _now_iso()],
        )
    return create_branch(
        workspace=workspace,
        book_id=book_id,
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=parent_node.branch_id,
            workflow_family=parent_node.workflow_family,
            chapter=chapter_id or parent_node.chapter,
        ),
        branch_id=resolved_branch_id,
        fork_group_id=fork_group_id,
        merge_operation="assembly",
        branch_role="assembly",
        request_id=request_id,
    )


def record_assembly_validation(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    passed: bool,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    manifest = _load_manifest(book_root, branch_id)
    if manifest.merge_operation != "assembly":
        raise ValueError("record_assembly_validation requires an assembly branch.")
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    lifecycle_state = "assembled_pending_promotion" if passed else "needs_review"
    validation_status = "passed" if passed else "failed"
    updated = _evolve_manifest(
        manifest,
        lifecycle_state=lifecycle_state,
        validation_status=validation_status,
        validation_message=message,
    )
    _write_manifest(book_root, updated)
    emit_reconciled_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        before_snapshot=before_snapshot,
        action="record_assembly_validation",
        result_status=execution_result_for_branch_lifecycle(lifecycle_state),
        request_id=request_id,
        message=message or ("Assembly validation passed." if passed else "Assembly validation failed."),
        details={
            "branch_id": branch_id,
            "merge_operation": manifest.merge_operation,
            "validation_status": validation_status,
        },
    )
    return updated


def promote_branch_to_main(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    manifest = _load_manifest(book_root, branch_id)
    if manifest.merge_operation == "assembly" and manifest.validation_status != "passed":
        raise ValueError(f"Assembly branch {branch_id} cannot promote without passed validation.")
    if manifest.lifecycle_state not in {"promote_ready", "assembled_pending_promotion"}:
        raise ValueError(f"Branch {branch_id} is not eligible for promotion; lifecycle_state={manifest.lifecycle_state}.")

    snapshot_root = _branch_snapshot_root(book_root, branch_id)
    if not snapshot_root.exists():
        raise FileNotFoundError(f"Branch snapshot missing for {branch_id}.")
    before_snapshot = capture_main_branch_snapshot(workspace, book_id)

    _copy_if_exists(snapshot_root / "state.json", book_root / "state.json")
    for name in (
        "outline.json",
        sw.REGISTRY_FILENAME,
        sw.THIN_FILENAME,
        sw.TOC_FILENAME,
        sw.INDEX_FILENAME,
        sw.APPENDIX_FILENAME,
        "characters.json",
    ):
        _copy_if_exists(snapshot_root / "outline" / name, book_root / "outline" / name)
    _copytree_if_exists(snapshot_root / "outline" / "boundaries", book_root / "outline" / "boundaries")
    _copytree_if_exists(snapshot_root / "outline" / "chapters", book_root / "outline" / "chapters")

    updated = _evolve_manifest(manifest, lifecycle_state="promoted")
    _write_manifest(book_root, updated)
    emit_reconciled_main_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        before_snapshot=before_snapshot,
        action="promote_branch_to_main",
        result_status="success",
        request_id=request_id,
        message=f"Branch {branch_id} promoted to main.",
        details={
            "source_branch_id": branch_id,
            "merge_operation": manifest.merge_operation,
            "branch_lifecycle_state": "promoted",
        },
    )
    emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        action="promote_branch_to_main",
        result_status=execution_result_for_branch_lifecycle("promoted"),
        request_id=request_id,
        message=f"Branch {branch_id} promoted to main.",
        details={"canonical_change_status": canonical_change_status_for_branch_lifecycle("promoted")},
    )
    return updated
