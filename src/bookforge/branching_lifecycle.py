from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from bookforge import section_workflow as sw
from bookforge.contracts import (
    ASSEMBLY_BRANCH_PREFIX,
    BranchManifest,
    MAIN_BRANCH_ID,
    ScopeSelector,
    canonical_change_status_for_branch_lifecycle,
    execution_result_for_branch_lifecycle,
)
from bookforge.query import _common as query_common
from bookforge.query import current_execution_node, current_main_node
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
    _read_json,
    _write_branch_node,
    _write_manifest,
)


def _parse_scene_ref(value: object) -> Optional[int]:
    text = str(value or "").strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    try:
        number = int(text)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _promotion_target_root(book_root: Path, target_branch_id: str) -> Path:
    target = str(target_branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if target == MAIN_BRANCH_ID:
        return book_root
    return _branch_snapshot_root(book_root, target)


def _copy_snapshot_to_target(snapshot_root: Path, target_root: Path) -> None:
    _copy_if_exists(snapshot_root / "state.json", target_root / "state.json")
    _copy_if_exists(snapshot_root / "book.json", target_root / "book.json")
    for name in (
        "outline.json",
        sw.REGISTRY_FILENAME,
        sw.THIN_FILENAME,
        sw.TOC_FILENAME,
        sw.INDEX_FILENAME,
        sw.APPENDIX_FILENAME,
        "characters.json",
    ):
        _copy_if_exists(snapshot_root / "outline" / name, target_root / "outline" / name)
    _copytree_if_exists(snapshot_root / "outline" / "boundaries", target_root / "outline" / "boundaries")
    _copytree_if_exists(snapshot_root / "outline" / "chapters", target_root / "outline" / "chapters")
    _copytree_if_exists(snapshot_root / "draft", target_root / "draft")
    _copytree_if_exists(snapshot_root / "characters", target_root / "characters")
    _copytree_if_exists(snapshot_root / "prompts", target_root / "prompts")


def _manifest_chapter(manifest: BranchManifest) -> Optional[int]:
    return manifest.selector.chapter if manifest.selector.chapter is not None else manifest.parent_node.chapter


def _section_scene_range(snapshot_root: Path, chapter_id: int, section_id: int) -> tuple[Optional[int], Optional[int]]:
    registry_path = snapshot_root / "outline" / sw.REGISTRY_FILENAME
    if not registry_path.exists():
        return None, None
    try:
        registry = _read_json(registry_path)
    except Exception:
        return None, None
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict) or int(chapter.get("chapter_id", 0) or 0) != int(chapter_id):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict) or int(section.get("section_id", 0) or 0) != int(section_id):
                continue
            return _parse_scene_ref(section.get("scene_ref_start")), _parse_scene_ref(section.get("scene_ref_end"))
    return None, None


def _copy_scene_files(source_chapter_dir: Path, target_chapter_dir: Path, scene_id: int) -> list[str]:
    copied: list[str] = []
    if not source_chapter_dir.exists():
        return copied
    target_chapter_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"scene_{int(scene_id):03d}"
    for source in sorted(source_chapter_dir.glob(f"{prefix}*")):
        if not source.is_file():
            continue
        dest = target_chapter_dir / source.name
        _copy_if_exists(source, dest)
        copied.append(dest.as_posix())
    return copied


def _sibling_writer_scope_pairs(book_root: Path, sibling: BranchManifest, assembly_branch_id: str) -> list[tuple[Path, Path]]:
    sibling_root = _branch_snapshot_root(book_root, sibling.branch_id)
    assembly_root = _branch_snapshot_root(book_root, assembly_branch_id)
    chapter_id = _manifest_chapter(sibling)
    if chapter_id is None:
        return []

    source_chapter_dir = sibling_root / "draft" / "chapters" / f"ch_{int(chapter_id):03d}"
    target_chapter_dir = assembly_root / "draft" / "chapters" / f"ch_{int(chapter_id):03d}"
    if sibling.selector.scene is not None:
        scene_ids = [int(sibling.selector.scene)]
    elif sibling.selector.section is not None:
        scene_start, scene_end = _section_scene_range(sibling_root, int(chapter_id), int(sibling.selector.section))
        if scene_start is None or scene_end is None:
            scene_ids = []
        else:
            scene_ids = list(range(int(scene_start), int(scene_end) + 1))
    else:
        if not source_chapter_dir.exists():
            return []
        return [(source, target_chapter_dir / source.name) for source in sorted(source_chapter_dir.rglob("*")) if source.is_file()]

    pairs: list[tuple[Path, Path]] = []
    for scene_id in scene_ids:
        prefix = f"scene_{int(scene_id):03d}"
        if not source_chapter_dir.exists():
            continue
        pairs.extend((source, target_chapter_dir / source.name) for source in sorted(source_chapter_dir.glob(f"{prefix}*")) if source.is_file())
    return pairs


def _copy_sibling_writer_scope_to_assembly(book_root: Path, sibling: BranchManifest, assembly_branch_id: str) -> list[str]:
    pairs = _sibling_writer_scope_pairs(book_root, sibling, assembly_branch_id)
    copied: list[str] = []
    for source, dest in pairs:
        _copy_if_exists(source, dest)
        copied.append(dest.as_posix())
    return copied


def _sibling_manifests_for_fork_group(book_root: Path, fork_group_id: str, *, exclude_branch_id: Optional[str] = None) -> List[BranchManifest]:
    sibling_manifests: List[BranchManifest] = []
    for sibling_id in query_common.list_branch_ids(book_root):
        if exclude_branch_id and sibling_id == exclude_branch_id:
            continue
        try:
            manifest = _load_manifest(book_root, sibling_id)
        except Exception:
            continue
        if manifest.fork_group_id == str(fork_group_id).strip() and manifest.merge_operation != "assembly":
            sibling_manifests.append(manifest)
    return sibling_manifests


def _assert_siblings_share_parent(sibling_manifests: List[BranchManifest]) -> tuple[dict, str]:
    if not sibling_manifests:
        raise ValueError("No sibling branches found for fork group.")
    parent_signature = sibling_manifests[0].parent_node.to_dict()
    parent_revision = sibling_manifests[0].parent_snapshot_revision
    for manifest in sibling_manifests[1:]:
        if manifest.parent_node.to_dict() != parent_signature or manifest.parent_snapshot_revision != parent_revision:
            raise ValueError("Fork-group siblings do not share the same frozen parent snapshot.")
    return parent_signature, parent_revision


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
    sibling_manifests = _sibling_manifests_for_fork_group(book_root, fork_group_id)
    if not sibling_manifests:
        raise ValueError(f"No sibling branches found for fork group {fork_group_id}.")

    _, parent_revision = _assert_siblings_share_parent(sibling_manifests)

    parent_branch_id = sibling_manifests[0].parent_node.branch_id or MAIN_BRANCH_ID
    live_parent = (
        current_main_node(workspace, book_id, prefer_emitted=False)
        if parent_branch_id == MAIN_BRANCH_ID
        else current_execution_node(workspace, book_id, branch_id=parent_branch_id, prefer_emitted=False)
    )
    if live_parent is not None and live_parent.revision_id != parent_revision:
        raise ValueError(f"Fork-group parent snapshot is stale against current {parent_branch_id} revision; rebase or recreate before assembly.")

    parent_node = sibling_manifests[0].parent_node
    resolved_branch_id = str(branch_id or "").strip()
    if not resolved_branch_id:
        resolved_branch_id = _generate_branch_id(
            ASSEMBLY_BRANCH_PREFIX,
            [book_id, fork_group_id, parent_revision, chapter_id or "", _now_iso()],
        )
    assembly_manifest = create_branch(
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
    copied: list[str] = []
    for sibling in sibling_manifests:
        copied.extend(_copy_sibling_writer_scope_to_assembly(book_root, sibling, assembly_manifest.branch_id))
    if copied:
        emit_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            branch_id=assembly_manifest.branch_id,
            action="assemble_fork_group_writer_outputs",
            result_status="success",
            request_id=request_id,
            message=f"Copied scoped writer outputs from {len(sibling_manifests)} sibling branches into assembly branch {assembly_manifest.branch_id}.",
            details={
                "fork_group_id": fork_group_id,
                "sibling_branch_ids": [manifest.branch_id for manifest in sibling_manifests],
                "copied_file_count": len(copied),
            },
        )
    return assembly_manifest


def validate_assembly_branch(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    manifest = _load_manifest(book_root, branch_id)
    if manifest.merge_operation != "assembly":
        raise ValueError("validate_assembly_branch requires an assembly branch.")
    fork_group_id = str(manifest.fork_group_id or "").strip()
    if not fork_group_id:
        raise ValueError("Assembly branch is missing fork_group_id.")

    siblings = _sibling_manifests_for_fork_group(book_root, fork_group_id, exclude_branch_id=branch_id)
    _assert_siblings_share_parent(siblings)
    missing: list[str] = []
    expected_count = 0
    for sibling in siblings:
        for _source, dest in _sibling_writer_scope_pairs(book_root, sibling, branch_id):
            expected_count += 1
            if not dest.exists():
                missing.append(dest.relative_to(_branch_snapshot_root(book_root, branch_id)).as_posix())

    passed = expected_count > 0 and not missing
    if passed:
        message = f"Assembly branch {branch_id} contains {expected_count} staged writer output files from {len(siblings)} sibling branches."
    elif expected_count <= 0:
        message = f"Assembly branch {branch_id} has no expected sibling writer outputs to validate."
    else:
        message = f"Assembly branch {branch_id} is missing {len(missing)} staged writer output files."
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
        action="validate_assembly_branch",
        result_status=execution_result_for_branch_lifecycle(lifecycle_state),
        request_id=request_id,
        message=message,
        details={
            "branch_id": branch_id,
            "merge_operation": manifest.merge_operation,
            "validation_status": validation_status,
            "expected_file_count": expected_count,
            "missing_file_count": len(missing),
            "missing_files": missing,
        },
    )
    return updated


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

    _copy_snapshot_to_target(snapshot_root, book_root)

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


def promote_branch_to_parent(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    target_branch_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    manifest = _load_manifest(book_root, branch_id)
    resolved_target = str(target_branch_id or manifest.parent_node.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_target == branch_id:
        raise ValueError("Branch cannot promote into itself.")
    if manifest.merge_operation == "assembly" and manifest.validation_status != "passed":
        raise ValueError(f"Assembly branch {branch_id} cannot promote without passed validation.")
    if manifest.lifecycle_state not in {"promote_ready", "assembled_pending_promotion"}:
        raise ValueError(f"Branch {branch_id} is not eligible for promotion; lifecycle_state={manifest.lifecycle_state}.")
    if resolved_target != MAIN_BRANCH_ID:
        _load_manifest(book_root, resolved_target)

    snapshot_root = _branch_snapshot_root(book_root, branch_id)
    if not snapshot_root.exists():
        raise FileNotFoundError(f"Branch snapshot missing for {branch_id}.")
    before_snapshot = (
        capture_main_branch_snapshot(workspace, book_id)
        if resolved_target == MAIN_BRANCH_ID
        else capture_surface_snapshot(workspace, book_id, branch_id=resolved_target)
    )
    target_root = _promotion_target_root(book_root, resolved_target)
    _copy_snapshot_to_target(snapshot_root, target_root)

    source_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if resolved_target != MAIN_BRANCH_ID and source_node is not None:
        _write_branch_node(
            book_root,
            source_node.__class__(
                book_id=source_node.book_id,
                workflow_family=source_node.workflow_family,
                source_run_id=source_node.source_run_id,
                branch_id=resolved_target,
                fork_group_id=source_node.fork_group_id,
                chapter=source_node.chapter,
                section=source_node.section,
                scene=source_node.scene,
                phase_id="branch_promotion",
                turn_id=source_node.turn_id,
                revision_id=f"promote{_now_iso().replace('-', '').replace(':', '').replace('.', '').replace('+00:00', 'Z')[:24]}",
            ),
        )

    updated = _evolve_manifest(manifest, lifecycle_state="promoted")
    _write_manifest(book_root, updated)
    details = {
        "source_branch_id": branch_id,
        "target_branch_id": resolved_target,
        "merge_operation": manifest.merge_operation,
        "branch_lifecycle_state": "promoted",
        "canonical_change_status": "canonical" if resolved_target == MAIN_BRANCH_ID else "none",
    }
    if resolved_target == MAIN_BRANCH_ID:
        emit_reconciled_main_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            before_snapshot=before_snapshot,
            action="promote_branch_to_parent",
            result_status="success",
            request_id=request_id,
            message=f"Branch {branch_id} promoted to main.",
            details=details,
        )
    else:
        emit_reconciled_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            branch_id=resolved_target,
            before_snapshot=before_snapshot,
            action="promote_branch_to_parent",
            result_status="success",
            request_id=request_id,
            message=f"Branch {branch_id} promoted to parent branch {resolved_target}.",
            details=details,
        )
    emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        action="promote_branch_to_parent",
        result_status=execution_result_for_branch_lifecycle("promoted"),
        request_id=request_id,
        message=f"Branch {branch_id} promoted to {resolved_target}.",
        details=details,
    )
    return updated


def rebase_branch(
    workspace: Path,
    book_id: str,
    branch_id: str,
    *,
    new_branch_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> BranchManifest:
    book_root = _book_root(workspace, book_id)
    manifest = _load_manifest(book_root, branch_id)
    parent_branch_id = manifest.parent_node.branch_id or MAIN_BRANCH_ID
    parent_node = current_execution_node(workspace, book_id, branch_id=parent_branch_id, prefer_emitted=False)
    if parent_node is None:
        raise ValueError(f"Cannot rebase {branch_id}; parent branch {parent_branch_id} has no current node.")
    if parent_node.revision_id == manifest.parent_snapshot_revision:
        raise ValueError(f"Branch {branch_id} is not stale against parent {parent_branch_id}.")

    refreshed = create_branch(
        workspace=workspace,
        book_id=book_id,
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=parent_branch_id,
            workflow_family=manifest.selector.workflow_family,
            chapter=manifest.selector.chapter,
            section=manifest.selector.section,
            scene=manifest.selector.scene,
            phase_id=manifest.selector.phase_id,
            turn_id=manifest.selector.turn_id,
        ),
        branch_id=new_branch_id,
        fork_group_id=manifest.fork_group_id,
        merge_operation=manifest.merge_operation,
        branch_role=manifest.branch_role or "rebased",
        request_id=request_id,
    )
    updated_old = _evolve_manifest(
        manifest,
        lifecycle_state="discard",
        validation_status="failed",
        validation_message=f"Rebased into {refreshed.branch_id}; old branch discarded.",
    )
    _write_manifest(book_root, updated_old)
    emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        action="rebase_branch",
        result_status=execution_result_for_branch_lifecycle("discard"),
        request_id=request_id,
        message=f"Branch {branch_id} rebased into {refreshed.branch_id}; old branch discarded.",
        details={
            "old_branch_id": branch_id,
            "new_branch_id": refreshed.branch_id,
            "parent_branch_id": parent_branch_id,
            "old_parent_revision": manifest.parent_snapshot_revision,
            "new_parent_revision": parent_node.revision_id,
        },
    )
    return refreshed
