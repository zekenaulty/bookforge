from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .scope_selector import ScopeSelector
from .timeline_node import TimelineNodeRef
from .vocabulary import BRANCH_LIFECYCLE_STATES, MERGE_OPERATIONS


def _clean_required(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be omitted or a non-empty string.")
    return cleaned


@dataclass(frozen=True, slots=True)
class BranchManifest:
    book_id: str
    branch_id: str
    lifecycle_state: str
    merge_operation: str
    workflow_family: str
    source_run_id: str
    parent_node: TimelineNodeRef
    selector: ScopeSelector
    parent_snapshot_revision: str
    created_at: str
    updated_at: str
    fork_group_id: Optional[str] = None
    branch_role: Optional[str] = None
    validation_status: Optional[str] = None
    validation_message: Optional[str] = None
    schema_version: str = "branch_manifest_v1"

    def __post_init__(self) -> None:
        book_id = _clean_required(self.book_id, "book_id")
        branch_id = _clean_required(self.branch_id, "branch_id")
        lifecycle_state = _clean_required(self.lifecycle_state, "lifecycle_state")
        merge_operation = _clean_required(self.merge_operation, "merge_operation")
        workflow_family = _clean_required(self.workflow_family, "workflow_family")
        source_run_id = _clean_required(self.source_run_id, "source_run_id")
        parent_snapshot_revision = _clean_required(self.parent_snapshot_revision, "parent_snapshot_revision")
        created_at = _clean_required(self.created_at, "created_at")
        updated_at = _clean_required(self.updated_at, "updated_at")
        fork_group_id = _clean_optional(self.fork_group_id, "fork_group_id")
        branch_role = _clean_optional(self.branch_role, "branch_role")
        validation_status = _clean_optional(self.validation_status, "validation_status")
        validation_message = _clean_optional(self.validation_message, "validation_message")

        if lifecycle_state not in BRANCH_LIFECYCLE_STATES:
            raise ValueError(f"Unknown lifecycle_state: {lifecycle_state}")
        if merge_operation not in MERGE_OPERATIONS:
            raise ValueError(f"Unknown merge_operation: {merge_operation}")
        if self.parent_node.book_id != book_id:
            raise ValueError("parent_node.book_id must match book_id.")
        if self.selector.book_id != book_id:
            raise ValueError("selector.book_id must match book_id.")
        if self.selector.branch_id is not None and self.selector.branch_id != branch_id:
            raise ValueError("selector.branch_id must match branch_id when provided.")
        if fork_group_id is not None and self.selector.fork_group_id != fork_group_id:
            raise ValueError("selector.fork_group_id must match fork_group_id when provided.")
        if self.parent_node.source_run_id != source_run_id:
            raise ValueError("parent_node.source_run_id must match source_run_id.")

        object.__setattr__(self, "book_id", book_id)
        object.__setattr__(self, "branch_id", branch_id)
        object.__setattr__(self, "lifecycle_state", lifecycle_state)
        object.__setattr__(self, "merge_operation", merge_operation)
        object.__setattr__(self, "workflow_family", workflow_family)
        object.__setattr__(self, "source_run_id", source_run_id)
        object.__setattr__(self, "parent_snapshot_revision", parent_snapshot_revision)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "fork_group_id", fork_group_id)
        object.__setattr__(self, "branch_role", branch_role)
        object.__setattr__(self, "validation_status", validation_status)
        object.__setattr__(self, "validation_message", validation_message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "fork_group_id": self.fork_group_id,
            "lifecycle_state": self.lifecycle_state,
            "merge_operation": self.merge_operation,
            "workflow_family": self.workflow_family,
            "source_run_id": self.source_run_id,
            "parent_node": self.parent_node.to_dict(),
            "selector": self.selector.to_dict(),
            "parent_snapshot_revision": self.parent_snapshot_revision,
            "branch_role": self.branch_role,
            "validation_status": self.validation_status,
            "validation_message": self.validation_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "BranchManifest":
        if not isinstance(payload, dict):
            raise ValueError("BranchManifest payload must be a dictionary.")
        return cls(
            book_id=payload.get("book_id"),
            branch_id=payload.get("branch_id"),
            fork_group_id=payload.get("fork_group_id"),
            lifecycle_state=payload.get("lifecycle_state"),
            merge_operation=payload.get("merge_operation"),
            workflow_family=payload.get("workflow_family"),
            source_run_id=payload.get("source_run_id"),
            parent_node=TimelineNodeRef.from_dict(payload.get("parent_node") or {}),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            parent_snapshot_revision=payload.get("parent_snapshot_revision"),
            branch_role=payload.get("branch_role"),
            validation_status=payload.get("validation_status"),
            validation_message=payload.get("validation_message"),
            created_at=payload.get("created_at"),
            updated_at=payload.get("updated_at"),
            schema_version=str(payload.get("schema_version") or "branch_manifest_v1"),
        )
