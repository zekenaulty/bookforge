from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, BranchManifest, ScopeSelector, TimelineNodeRef
from bookforge.supervision import paths as supervision_paths

from . import _common
from .workspace import current_main_node


@dataclass(frozen=True, slots=True)
class BranchInventoryRecord:
    branch_id: str
    fork_group_id: Optional[str]
    lifecycle_state: Optional[str]
    merge_operation: Optional[str]
    workflow_family: Optional[str]
    source_run_id: Optional[str]
    branch_role: Optional[str]
    validation_status: Optional[str]
    validation_message: Optional[str]
    parent_node: Optional[TimelineNodeRef]
    current_node: Optional[TimelineNodeRef]
    selector: Optional[Dict[str, Any]]
    manifest_path: str
    snapshot_path: Optional[str]
    stale_parent: bool
    warning_codes: List[str]
    schema_version: str = "branch_inventory_record_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "branch_id": self.branch_id,
            "fork_group_id": self.fork_group_id,
            "lifecycle_state": self.lifecycle_state,
            "merge_operation": self.merge_operation,
            "workflow_family": self.workflow_family,
            "source_run_id": self.source_run_id,
            "branch_role": self.branch_role,
            "validation_status": self.validation_status,
            "validation_message": self.validation_message,
            "parent_node": self.parent_node.to_dict() if self.parent_node else None,
            "current_node": self.current_node.to_dict() if self.current_node else None,
            "selector": dict(self.selector) if isinstance(self.selector, dict) else None,
            "manifest_path": self.manifest_path,
            "snapshot_path": self.snapshot_path,
            "stale_parent": self.stale_parent,
            "warning_codes": list(self.warning_codes),
        }


@dataclass(frozen=True, slots=True)
class ForkGroupInventoryRecord:
    fork_group_id: str
    branch_ids: List[str]
    lifecycle_states: Dict[str, int]
    parent_source_run_ids: List[str]
    has_mixed_parent_lineage: bool
    schema_version: str = "fork_group_inventory_record_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "fork_group_id": self.fork_group_id,
            "branch_ids": list(self.branch_ids),
            "lifecycle_states": dict(self.lifecycle_states),
            "parent_source_run_ids": list(self.parent_source_run_ids),
            "has_mixed_parent_lineage": self.has_mixed_parent_lineage,
        }


@dataclass(frozen=True, slots=True)
class BranchInventory:
    book_id: str
    main_node: Optional[TimelineNodeRef]
    branches: List[BranchInventoryRecord]
    fork_groups: List[ForkGroupInventoryRecord]
    warnings: List[str]
    source: str = "bookforge.query.branches.v1"
    schema_version: str = "branch_inventory_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "source": self.source,
            "main_node": self.main_node.to_dict() if self.main_node else None,
            "branches": [branch.to_dict() for branch in self.branches],
            "fork_groups": [group.to_dict() for group in self.fork_groups],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class BranchDetailView:
    book_id: str
    branch_id: str
    selector: ScopeSelector
    branch_record: Optional[BranchInventoryRecord]
    main_node: Optional[TimelineNodeRef]
    workspace_status: Dict[str, Any]
    legal_actions: List[Dict[str, Any]]
    reader: Optional[Dict[str, Any]]
    scene_readiness: Optional[Dict[str, Any]]
    recovery_health: Optional[Dict[str, Any]]
    warnings: List[str]
    source: str = "bookforge.query.branches.detail.v1"
    schema_version: str = "branch_detail_view_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "source": self.source,
            "selector": self.selector.to_dict(),
            "branch_record": self.branch_record.to_dict() if self.branch_record else None,
            "main_node": self.main_node.to_dict() if self.main_node else None,
            "workspace_status": dict(self.workspace_status),
            "legal_actions": [dict(action) for action in self.legal_actions],
            "reader": dict(self.reader) if self.reader is not None else None,
            "scene_readiness": dict(self.scene_readiness) if self.scene_readiness is not None else None,
            "recovery_health": dict(self.recovery_health) if self.recovery_health is not None else None,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class BranchArtifactRecord:
    path: str
    artifact_class: str
    artifact_status: str
    branch_relationship: str
    size_bytes: int
    modified_at: str
    sha256: str
    main_sha256: Optional[str] = None
    schema_version: str = "branch_artifact_record_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "path": self.path,
            "artifact_class": self.artifact_class,
            "artifact_status": self.artifact_status,
            "branch_relationship": self.branch_relationship,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at,
            "sha256": self.sha256,
            "main_sha256": self.main_sha256,
        }


@dataclass(frozen=True, slots=True)
class BranchArtifactIndex:
    book_id: str
    branch_id: str
    root_path: str
    records: List[BranchArtifactRecord]
    class_counts: Dict[str, int]
    relationship_counts: Dict[str, int]
    warnings: List[str]
    source: str = "bookforge.query.branches.artifacts.v1"
    schema_version: str = "branch_artifact_index_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "source": self.source,
            "root_path": self.root_path,
            "records": [record.to_dict() for record in self.records],
            "class_counts": dict(self.class_counts),
            "relationship_counts": dict(self.relationship_counts),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class BranchDiffSummary:
    book_id: str
    branch_id: str
    against_branch_id: str
    status: str
    changed_records: List[BranchArtifactRecord]
    relationship_counts: Dict[str, int]
    class_counts: Dict[str, int]
    warnings: List[str]
    source: str = "bookforge.query.branches.diff_summary.v1"
    schema_version: str = "branch_diff_summary_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "against_branch_id": self.against_branch_id,
            "source": self.source,
            "status": self.status,
            "changed_records": [record.to_dict() for record in self.changed_records],
            "relationship_counts": dict(self.relationship_counts),
            "class_counts": dict(self.class_counts),
            "warnings": list(self.warnings),
        }


def get_branch_inventory(workspace, book_id: str) -> BranchInventory:
    book_root = _common.book_root(Path(workspace), book_id)
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_id}")
    main_node = current_main_node(workspace, book_id, prefer_emitted=True)
    branches = [_load_branch_record(book_root, branch_id, main_node) for branch_id in _common.list_branch_ids(book_root)]
    warnings: List[str] = []
    if not branches:
        warnings.append("No derived branches found.")
    fork_groups = _fork_groups(branches)
    return BranchInventory(
        book_id=book_id,
        main_node=main_node,
        branches=branches,
        fork_groups=fork_groups,
        warnings=warnings,
    )


def get_branch_inventory_record(workspace, book_id: str, branch_id: str) -> Optional[BranchInventoryRecord]:
    for record in get_branch_inventory(workspace, book_id).branches:
        if record.branch_id == branch_id:
            return record
    return None


def get_branch_detail(
    workspace,
    book_id: str,
    branch_id: str,
    *,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    max_text_chars: int = 0,
    prefer_emitted: bool = True,
) -> BranchDetailView:
    """Return a Nanda-facing workbench view for one branch and optional scope.

    This is intentionally read-only. It gives an author agent the branch-local
    context needed to choose a safe next action without walking raw files.
    """

    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    inventory = get_branch_inventory(workspace, book_id)
    branch_record = next((record for record in inventory.branches if record.branch_id == resolved_branch_id), None)
    warnings: List[str] = []
    if resolved_branch_id != MAIN_BRANCH_ID and branch_record is None:
        warnings.append("branch_not_found")
    if resolved_branch_id == MAIN_BRANCH_ID:
        warnings.append("main_branch_detail_requested")
    if branch_record is not None:
        warnings.extend(branch_record.warning_codes)

    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family=branch_record.workflow_family if branch_record else None,
        chapter=chapter_id,
        section=section_id,
        scene=scene_id,
    )

    workspace_status: Dict[str, Any]
    try:
        from .workspace import get_workspace_status_for_branch

        status = get_workspace_status_for_branch(
            workspace,
            book_id,
            branch_id=resolved_branch_id,
            prefer_emitted=prefer_emitted,
        )
        workspace_status = _workspace_status_to_dict(status)
    except Exception as exc:
        workspace_status = {}
        warnings.append(f"workspace_status_unavailable:{exc}")

    legal_actions: List[Dict[str, Any]] = []
    try:
        from .actions import list_execution_options

        legal_actions = [
            option.to_dict()
            for option in list_execution_options(workspace, selector, prefer_emitted=prefer_emitted)
        ]
    except Exception as exc:
        warnings.append(f"legal_actions_unavailable:{exc}")

    reader: Optional[Dict[str, Any]] = None
    try:
        from .reader import get_book_reader_view

        reader = get_book_reader_view(
            workspace,
            book_id,
            branch_id=resolved_branch_id,
            chapter_id=chapter_id,
            scene_id=scene_id,
            max_text_chars=max(0, int(max_text_chars or 0)),
        ).to_dict()
    except Exception as exc:
        warnings.append(f"reader_unavailable:{exc}")

    scene_readiness: Optional[Dict[str, Any]] = None
    if chapter_id is not None and scene_id is not None:
        try:
            from .scene_phase import get_scene_phase_readiness

            scene_readiness = get_scene_phase_readiness(
                workspace,
                book_id,
                branch_id=resolved_branch_id,
                chapter_id=chapter_id,
                scene_id=scene_id,
                section_id=section_id,
                prefer_emitted=prefer_emitted,
            ).to_dict()
        except Exception as exc:
            warnings.append(f"scene_readiness_unavailable:{exc}")

    recovery_health: Optional[Dict[str, Any]] = None
    if resolved_branch_id != MAIN_BRANCH_ID:
        try:
            from .recovery import get_recovery_branch_health

            health = get_recovery_branch_health(Path(workspace), book_id, branch_id=resolved_branch_id)
            health_payload = health.to_dict()
            if health_payload.get("status") != "blocked" or health_payload.get("details", {}).get("manifest"):
                recovery_health = health_payload
            else:
                warnings.append("recovery_health_not_applicable")
        except Exception as exc:
            warnings.append(f"recovery_health_unavailable:{exc}")

    return BranchDetailView(
        book_id=book_id,
        branch_id=resolved_branch_id,
        selector=selector,
        branch_record=branch_record,
        main_node=inventory.main_node,
        workspace_status=workspace_status,
        legal_actions=legal_actions,
        reader=reader,
        scene_readiness=scene_readiness,
        recovery_health=recovery_health,
        warnings=_dedupe(warnings),
    )


def get_branch_artifact_index(
    workspace,
    book_id: str,
    branch_id: str = MAIN_BRANCH_ID,
    *,
    limit: int = 500,
) -> BranchArtifactIndex:
    canonical_root = _common.book_root(Path(workspace), book_id)
    if not canonical_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_id}")
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_branch_id == MAIN_BRANCH_ID:
        root = canonical_root
    else:
        root = supervision_paths.branch_snapshot_root(canonical_root, resolved_branch_id)
    warnings: List[str] = []
    if not root.exists():
        warnings.append("branch_snapshot_missing")
        return BranchArtifactIndex(
            book_id=book_id,
            branch_id=resolved_branch_id,
            root_path=root.as_posix(),
            records=[],
            class_counts={},
            relationship_counts={},
            warnings=warnings,
        )
    max_records = max(1, int(limit or 500))
    records: List[BranchArtifactRecord] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if len(records) >= max_records:
            warnings.append("record_limit_reached")
            break
        rel = path.relative_to(root).as_posix()
        if _skip_artifact(rel):
            continue
        main_path = canonical_root / rel
        sha = _sha256(path)
        main_sha = _sha256(main_path) if main_path.exists() else None
        relationship = _branch_relationship(
            branch_id=resolved_branch_id,
            main_path=main_path,
            sha=sha,
            main_sha=main_sha,
        )
        artifact_class = _artifact_class(rel)
        records.append(
            BranchArtifactRecord(
                path=rel,
                artifact_class=artifact_class,
                artifact_status=_artifact_status(resolved_branch_id, relationship, artifact_class),
                branch_relationship=relationship,
                size_bytes=path.stat().st_size,
                modified_at=_mtime_iso(path),
                sha256=sha,
                main_sha256=main_sha,
            )
        )
    return BranchArtifactIndex(
        book_id=book_id,
        branch_id=resolved_branch_id,
        root_path=root.as_posix(),
        records=records,
        class_counts=_count_by(records, "artifact_class"),
        relationship_counts=_count_by(records, "branch_relationship"),
        warnings=_dedupe(warnings),
    )


def get_branch_diff_summary(
    workspace,
    book_id: str,
    branch_id: str,
    *,
    against: str = MAIN_BRANCH_ID,
    limit: int = 500,
) -> BranchDiffSummary:
    resolved_branch_id = str(branch_id or "").strip()
    against_branch_id = str(against or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    warnings: List[str] = []
    if not resolved_branch_id:
        raise ValueError("branch_id is required.")
    if against_branch_id != MAIN_BRANCH_ID:
        warnings.append("only_main_comparison_supported")
    index = get_branch_artifact_index(workspace, book_id, resolved_branch_id, limit=limit)
    changed = [
        record
        for record in index.records
        if record.branch_relationship in {"branch_modified", "branch_only"}
    ]
    status = "no_changes" if not changed else "has_changes"
    warnings.extend(index.warnings)
    return BranchDiffSummary(
        book_id=book_id,
        branch_id=resolved_branch_id,
        against_branch_id=MAIN_BRANCH_ID,
        status=status,
        changed_records=changed,
        relationship_counts=dict(index.relationship_counts),
        class_counts=_count_by(changed, "artifact_class"),
        warnings=_dedupe(warnings),
    )


def _load_branch_record(book_root: Path, branch_id: str, main_node: Optional[TimelineNodeRef]) -> BranchInventoryRecord:
    manifest_path = _common.branch_manifest_path(book_root, branch_id)
    manifest_payload = _common.read_json(manifest_path) or {}
    current_payload = _common.read_json(_common.branch_current_node_path(book_root, branch_id))
    manifest: Optional[BranchManifest] = None
    warnings: List[str] = []
    try:
        manifest = BranchManifest.from_dict(manifest_payload)
    except ValueError as exc:
        warnings.append(f"invalid_manifest:{exc}")
    current_node = None
    if isinstance(current_payload, dict):
        try:
            current_node = TimelineNodeRef.from_dict(current_payload)
        except ValueError as exc:
            warnings.append(f"invalid_current_node:{exc}")
    parent_node = manifest.parent_node if manifest else None
    stale_parent = _is_stale_parent(parent_node, main_node)
    if stale_parent:
        warnings.append("stale_parent")
    snapshot_path = supervision_paths.branch_snapshot_root(book_root, branch_id)
    return BranchInventoryRecord(
        branch_id=branch_id,
        fork_group_id=manifest.fork_group_id if manifest else _string_or_none(manifest_payload.get("fork_group_id")),
        lifecycle_state=manifest.lifecycle_state if manifest else _string_or_none(manifest_payload.get("lifecycle_state")),
        merge_operation=manifest.merge_operation if manifest else _string_or_none(manifest_payload.get("merge_operation")),
        workflow_family=manifest.workflow_family if manifest else _string_or_none(manifest_payload.get("workflow_family")),
        source_run_id=manifest.source_run_id if manifest else _string_or_none(manifest_payload.get("source_run_id")),
        branch_role=manifest.branch_role if manifest else _string_or_none(manifest_payload.get("branch_role")),
        validation_status=manifest.validation_status if manifest else _string_or_none(manifest_payload.get("validation_status")),
        validation_message=manifest.validation_message if manifest else _string_or_none(manifest_payload.get("validation_message")),
        parent_node=parent_node,
        current_node=current_node,
        selector=manifest.selector.to_dict() if manifest else manifest_payload.get("selector") if isinstance(manifest_payload.get("selector"), dict) else None,
        manifest_path=manifest_path.as_posix(),
        snapshot_path=snapshot_path.as_posix() if snapshot_path.exists() else None,
        stale_parent=stale_parent,
        warning_codes=warnings,
    )


def _is_stale_parent(parent_node: Optional[TimelineNodeRef], main_node: Optional[TimelineNodeRef]) -> bool:
    if parent_node is None or main_node is None:
        return False
    if parent_node.branch_id != MAIN_BRANCH_ID:
        return False
    if parent_node.source_run_id != main_node.source_run_id:
        return True
    if parent_node.revision_id != main_node.revision_id:
        return True
    return False


def _workspace_status_to_dict(status: Any) -> Dict[str, Any]:
    return {
        "book_id": status.book_id,
        "state_status": status.state_status,
        "cursor": dict(status.cursor or {}),
        "source_run_id": status.source_run_id,
        "active_section": dict(status.active_section) if isinstance(status.active_section, dict) else None,
        "current_node": status.current_node.to_dict() if status.current_node else None,
        "pause_marker_present": bool(status.pause_marker),
        "progress_heartbeat_present": bool(status.progress_heartbeat),
        "branch_count": len(status.branches),
        "chapter_status_counts": dict(status.chapter_status_counts),
    }


def _fork_groups(branches: List[BranchInventoryRecord]) -> List[ForkGroupInventoryRecord]:
    grouped: Dict[str, List[BranchInventoryRecord]] = {}
    for branch in branches:
        if branch.fork_group_id:
            grouped.setdefault(branch.fork_group_id, []).append(branch)
    records: List[ForkGroupInventoryRecord] = []
    for fork_group_id, members in sorted(grouped.items()):
        lifecycle_counts: Dict[str, int] = {}
        source_run_ids: set[str] = set()
        for member in members:
            if member.lifecycle_state:
                lifecycle_counts[member.lifecycle_state] = lifecycle_counts.get(member.lifecycle_state, 0) + 1
            if member.parent_node:
                source_run_ids.add(member.parent_node.source_run_id)
        records.append(
            ForkGroupInventoryRecord(
                fork_group_id=fork_group_id,
                branch_ids=sorted(member.branch_id for member in members),
                lifecycle_states=lifecycle_counts,
                parent_source_run_ids=sorted(source_run_ids),
                has_mixed_parent_lineage=len(source_run_ids) > 1,
            )
        )
    return records


def _dedupe(values: List[str]) -> List[str]:
    seen: set[str] = set()
    deduped: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _skip_artifact(relpath: str) -> bool:
    if relpath.startswith("."):
        return True
    if relpath.startswith("logs/"):
        return True
    if "/__pycache__/" in f"/{relpath}/":
        return True
    return False


def _artifact_class(relpath: str) -> str:
    lower = relpath.lower()
    if lower.startswith("outline/"):
        return "outline"
    if lower.startswith("draft/chapters/") and lower.endswith(".md"):
        return "prose"
    if lower.startswith("draft/chapters/") and lower.endswith(".json"):
        return "scene_metadata"
    if lower.startswith("draft/context/bridge_scenes/") and lower.endswith("_apply_report.json"):
        return "adaptive_authoring_report"
    if lower.startswith("draft/context/bridge_scenes/"):
        return "adaptive_authoring_plan"
    if lower.startswith("draft/context/phase_history/") and "/" in lower[len("draft/context/phase_history/"):]:
        return "scene_phase_artifact"
    if lower.startswith("draft/context/phase_history/") and lower.endswith(".json"):
        return "scene_phase_history"
    if lower.startswith("draft/context/"):
        return "scene_context"
    if lower.startswith("context/"):
        return "continuity_context"
    if lower.startswith("state/") or lower in {"book.json", "series.json"}:
        return "state"
    if lower.startswith("supervision/"):
        return "supervision"
    if lower.endswith(".json"):
        return "json"
    if lower.endswith(".md"):
        return "markdown"
    return "other"


def _artifact_status(branch_id: str, relationship: str, artifact_class: str) -> str:
    if artifact_class in {"supervision", "adaptive_authoring_report"}:
        return "diagnostic"
    if artifact_class == "adaptive_authoring_plan":
        return "provisional"
    if artifact_class == "scene_phase_artifact":
        return "provisional"
    if artifact_class == "scene_phase_history":
        return "diagnostic"
    if artifact_class == "scene_context":
        return "derived"
    if branch_id == MAIN_BRANCH_ID:
        return "authoritative"
    if relationship == "inherited_from_main":
        return "derived"
    return "provisional"


def _branch_relationship(*, branch_id: str, main_path: Path, sha: str, main_sha: Optional[str]) -> str:
    if branch_id == MAIN_BRANCH_ID:
        return "canonical_main"
    if not main_path.exists():
        return "branch_only"
    if main_sha == sha:
        return "inherited_from_main"
    return "branch_modified"


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_by(records: List[BranchArtifactRecord], field_name: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for record in records:
        value = str(getattr(record, field_name))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _string_or_none(value: Any) -> Optional[str]:
    cleaned = str(value or "").strip()
    return cleaned or None
