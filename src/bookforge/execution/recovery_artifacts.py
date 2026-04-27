from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List
import shutil

from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID
from bookforge.query.recovery import get_recovery_manifest, get_scope_invalidation_preview, recovery_dir
from bookforge.supervision import capture_surface_snapshot

from .recovery_common import (
    advance_recovery_node,
    book_root,
    emit_result,
    execution_root,
    load_recovery_scope,
    record_promotion_removals,
    relative,
    write_receipt,
)


def _quarantine_path(root: Path, branch_id: str, action: str, rel_path: str) -> Path:
    return recovery_dir(root, branch_id) / "quarantine" / action / rel_path


def _move_to_quarantine(root: Path, branch_id: str, rel_paths: Iterable[str], *, action: str) -> List[Dict[str, str]]:
    snapshot_root = execution_root(root, branch_id)
    moved: List[Dict[str, str]] = []
    for rel_path in sorted({str(item).strip().replace("\\", "/") for item in rel_paths if str(item).strip()}):
        source = snapshot_root / rel_path
        if not source.exists() or not source.is_file():
            continue
        dest = _quarantine_path(root, branch_id, action, rel_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        shutil.move(str(source), str(dest))
        moved.append({"source": rel_path, "quarantine": relative(root, dest)})
    return moved


def _section_draft_rel_paths(scope) -> List[str]:
    rel_paths: List[str] = []
    for item in scope.affected_scopes:
        if "section_id" not in item:
            continue
        rel_paths.append(f"outline/section_drafts/ch_{int(item['chapter_id']):03d}_sec_{int(item['section_id']):03d}_phase03.json")
    return rel_paths


def quarantine_artifacts(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "quarantine_artifacts":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("quarantine_artifacts requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    scope = load_recovery_scope(manifest)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    moved = _move_to_quarantine(root, branch_id, _section_draft_rel_paths(scope), action="quarantine_artifacts")
    removed = [item["source"] for item in moved]
    removals_path = record_promotion_removals(root, branch_id, removed)
    advance_recovery_node(workspace, book_id, branch_id, "quarantine_artifacts")
    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="quarantine_artifacts",
        status="success",
        message=f"Quarantined {len(moved)} active artifacts.",
        artifact_paths={"promotion_removals": relative(root, removals_path)},
        removed_active_paths=removed,
        quarantined_paths=moved,
        details={"artifact_families": ["section_draft"]},
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status="success",
        message=f"Quarantined {len(moved)} active artifacts.",
        receipt=receipt,
        artifact_paths={"promotion_removals": relative(root, removals_path)},
        before_snapshot=before_snapshot,
    )


def invalidate_scope_outputs(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "invalidate_scope_outputs":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("invalidate_scope_outputs requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    preview = get_scope_invalidation_preview(workspace, book_id, branch_id=branch_id)
    moved = _move_to_quarantine(root, branch_id, preview["candidate_paths"], action="invalidate_scope_outputs")
    removed = [item["source"] for item in moved]
    removals_path = record_promotion_removals(root, branch_id, removed)
    advance_recovery_node(workspace, book_id, branch_id, "invalidate_scope_outputs")
    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="invalidate_scope_outputs",
        status="success",
        message=f"Invalidated {len(moved)} output artifacts.",
        artifact_paths={"promotion_removals": relative(root, removals_path)},
        removed_active_paths=removed,
        quarantined_paths=moved,
        details={"affected_scopes": preview["affected_scopes"]},
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status="success",
        message=f"Invalidated {len(moved)} output artifacts.",
        receipt=receipt,
        artifact_paths={"promotion_removals": relative(root, removals_path)},
        before_snapshot=before_snapshot,
    )
