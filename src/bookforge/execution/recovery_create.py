from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil

from bookforge import section_workflow as sw
from bookforge.branching import create_branch
from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ProducedArtifactReceipt, ScopeSelector
from bookforge.supervision import emit_branch_contracts

from .recovery_common import (
    book_root,
    execution_root,
    now_token,
    read_json,
    relative,
    write_json,
    write_receipt,
    write_recovery_manifest,
)


def _copytree_into_branch(source: Path, dest: Path) -> Optional[str]:
    if not source.exists() or not source.is_dir():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, dirs_exist_ok=True)
    return dest.as_posix()


def _copy_file_into_branch(source: Path, dest: Path) -> Optional[str]:
    if not source.exists() or not source.is_file():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest.as_posix()


def _materialize_recovery_inputs(root: Path, branch_id: str) -> Dict[str, str]:
    snapshot_root = execution_root(root, branch_id)
    source_outline = root / "outline"
    target_outline = snapshot_root / "outline"
    copied: Dict[str, str] = {}
    for name in ("pipeline_runs", "section_drafts"):
        copied_path = _copytree_into_branch(source_outline / name, target_outline / name)
        if copied_path:
            copied[name] = relative(snapshot_root, Path(copied_path))
    for name in (
        "pipeline_latest.json",
        "outline_pipeline_report_latest.json",
        "outline_final_v1_1.json",
        "outline_seams_hygiened_v1_1.json",
    ):
        copied_path = _copy_file_into_branch(source_outline / name, target_outline / name)
        if copied_path:
            copied[name] = relative(snapshot_root, Path(copied_path))
    return copied


def _parse_scene_ref(value: object) -> Optional[int]:
    text = str(value or "").strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    try:
        number = int(text)
    except (TypeError, ValueError):
        return None
    return number if number >= 1 else None


def _scope_key(chapter_id: int, section_id: Optional[int]) -> str:
    if section_id is None:
        return f"ch_{int(chapter_id):03d}"
    return f"ch_{int(chapter_id):03d}_sec_{int(section_id):03d}"


def _scope_output_ranges(root: Path, scope) -> Dict[str, Dict[str, Any]]:
    registry = read_json(root / "outline" / sw.REGISTRY_FILENAME)
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    ranges: Dict[str, Dict[str, Any]] = {}
    for item in scope.affected_scopes:
        chapter_id = int(item["chapter_id"])
        section_id = item.get("section_id")
        scene_ids: List[int] = []
        for chapter in chapters:
            if not isinstance(chapter, dict) or int(chapter.get("chapter_id", 0) or 0) != chapter_id:
                continue
            sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
            if section_id is None:
                for section in sections:
                    start = _parse_scene_ref(section.get("scene_ref_start"))
                    end = _parse_scene_ref(section.get("scene_ref_end"))
                    if start is not None and end is not None and end >= start:
                        scene_ids.extend(range(start, end + 1))
                break
            for section in sections:
                if not isinstance(section, dict) or int(section.get("section_id", 0) or 0) != int(section_id):
                    continue
                start = _parse_scene_ref(section.get("scene_ref_start"))
                end = _parse_scene_ref(section.get("scene_ref_end"))
                if start is not None and end is not None and end >= start:
                    scene_ids.extend(range(start, end + 1))
                break
        ranges[_scope_key(chapter_id, int(section_id) if section_id is not None else None)] = {
            "chapter_id": chapter_id,
            "section_id": int(section_id) if section_id is not None else None,
            "scene_ids": sorted(set(scene_ids)),
        }
    return ranges


def create_recovery_branch(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "create_recovery_branch":
        raise ValueError("Unsupported execution action.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    anchor = request.details.get("anchor") or {}
    scope = request.details.get("scope") or {}
    from bookforge.contracts import RecoveryAnchor, RecoveryScope

    recovery_anchor = RecoveryAnchor.from_dict(anchor)
    recovery_scope = RecoveryScope.from_dict(scope)
    if not recovery_scope.affected_scopes:
        raise ValueError("create_recovery_branch requires at least one affected scope.")

    manifest = create_branch(
        workspace=workspace,
        book_id=book_id,
        selector=ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID, workflow_family="recovery_import"),
        branch_id=request.details.get("branch_id"),
        merge_operation="promotion",
        branch_role="recovery",
        request_id=request.request_id,
    )
    copied_inputs = _materialize_recovery_inputs(root, manifest.branch_id)
    output_ranges = _scope_output_ranges(root, recovery_scope)
    payload = {
        "schema_version": "recovery_manifest_v1",
        "book_id": book_id,
        "branch_id": manifest.branch_id,
        "created_at": now_token(),
        "updated_at": now_token(),
        "anchor": recovery_anchor.to_dict(),
        "scope": recovery_scope.to_dict(),
        "status": "active",
        "cleanliness_status": "isolated_not_clean",
        "cleanliness_note": (
            "Recovery branch creation snapshots current branch state and materializes recovery evidence. "
            "The branch is isolated, but it is not clean until quarantine, normalization, invalidation, rebuild, "
            "redraft, and validation complete."
        ),
        "materialized_inputs": copied_inputs,
        "scope_output_ranges": output_ranges,
    }
    manifest_path = write_recovery_manifest(root, manifest.branch_id, payload)
    receipt = write_receipt(
        workspace,
        book_id,
        manifest.branch_id,
        action="create_recovery_branch",
        status="success",
        message=f"Recovery branch {manifest.branch_id} created.",
        artifact_paths={"recovery_manifest": relative(root, manifest_path)},
        details={
            "anchor": recovery_anchor.to_dict(),
            "scope": recovery_scope.to_dict(),
            "cleanliness_status": "isolated_not_clean",
            "cleanliness_note": payload["cleanliness_note"],
            "required_cleanup_actions": [
                "quarantine_artifacts",
                "normalize_outline_scope",
                "invalidate_scope_outputs",
                "rebuild_state_scope",
                "redraft_scope",
                "validate_recovery_branch",
            ],
            "materialized_inputs": copied_inputs,
            "scope_output_ranges": output_ranges,
        },
    )
    bundle = emit_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=manifest.branch_id,
        action=request.action,
        result_status="success",
        request_id=request.request_id,
        message=f"Recovery branch {manifest.branch_id} created.",
        artifact_paths={"recovery_manifest": relative(root, manifest_path)},
        produced_artifacts=[
            ProducedArtifactReceipt(
                artifact_key="recovery_manifest",
                label="Recovery manifest",
                artifact_status="authoritative",
                path=relative(root, manifest_path),
                format="json",
                consumable=True,
                replaceable=True,
            )
        ],
        details={"branch_id": manifest.branch_id, "recovery_receipt": receipt.to_dict()},
    )
    if bundle.execution_result is None:
        raise ValueError("create_recovery_branch did not emit an execution result.")
    return bundle.execution_result
