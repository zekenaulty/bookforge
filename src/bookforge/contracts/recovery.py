from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .timeline_node import TimelineNodeRef


def _clean_required(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _scope_list(scopes: List[Dict[str, Any]]) -> List[Dict[str, int]]:
    cleaned: List[Dict[str, int]] = []
    for scope in list(scopes or []):
        if not isinstance(scope, dict):
            continue
        try:
            chapter_id = int(scope.get("chapter_id") or scope.get("chapter") or 0)
            section_id = scope.get("section_id", scope.get("section"))
            scene_id = scope.get("scene_id", scope.get("scene"))
            item: Dict[str, int] = {"chapter_id": chapter_id}
            if section_id is not None:
                item["section_id"] = int(section_id)
            if scene_id is not None:
                item["scene_id"] = int(scene_id)
        except (TypeError, ValueError):
            continue
        if item["chapter_id"] >= 1:
            cleaned.append(item)
    return cleaned


@dataclass(frozen=True, slots=True)
class RecoveryAnchor:
    anchor_type: str
    source_run_id: Optional[str] = None
    artifact_family: Optional[str] = None
    description: Optional[str] = None
    schema_version: str = "recovery_anchor_v1"

    def __post_init__(self) -> None:
        anchor_type = _clean_required(self.anchor_type, "anchor_type")
        if anchor_type not in {
            "declared_source_run",
            "latest_outline_run",
            "frozen_chapter_projection",
            "manual_hybrid",
            "shelf",
        }:
            raise ValueError(f"Unknown recovery anchor_type: {anchor_type}")
        object.__setattr__(self, "anchor_type", anchor_type)
        object.__setattr__(self, "source_run_id", _clean_optional(self.source_run_id))
        object.__setattr__(self, "artifact_family", _clean_optional(self.artifact_family))
        object.__setattr__(self, "description", _clean_optional(self.description))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "anchor_type": self.anchor_type,
            "source_run_id": self.source_run_id,
            "artifact_family": self.artifact_family,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RecoveryAnchor":
        if not isinstance(payload, dict):
            raise ValueError("RecoveryAnchor payload must be a dictionary.")
        return cls(
            anchor_type=payload.get("anchor_type"),
            source_run_id=payload.get("source_run_id"),
            artifact_family=payload.get("artifact_family"),
            description=payload.get("description"),
            schema_version=str(payload.get("schema_version") or "recovery_anchor_v1"),
        )


@dataclass(frozen=True, slots=True)
class RecoveryScope:
    affected_scopes: List[Dict[str, int]]
    downstream_scopes: List[Dict[str, int]] = field(default_factory=list)
    salvage_policy: str = "none"
    schema_version: str = "recovery_scope_v1"

    def __post_init__(self) -> None:
        salvage_policy = _clean_required(self.salvage_policy, "salvage_policy")
        if salvage_policy not in {"none", "reference_only", "explicit_reuse_required"}:
            raise ValueError(f"Unknown salvage_policy: {salvage_policy}")
        affected = _scope_list(self.affected_scopes)
        if not affected:
            raise ValueError("RecoveryScope requires at least one affected scope.")
        object.__setattr__(self, "affected_scopes", affected)
        object.__setattr__(self, "downstream_scopes", _scope_list(self.downstream_scopes))
        object.__setattr__(self, "salvage_policy", salvage_policy)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "affected_scopes": [dict(item) for item in self.affected_scopes],
            "downstream_scopes": [dict(item) for item in self.downstream_scopes],
            "salvage_policy": self.salvage_policy,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RecoveryScope":
        if not isinstance(payload, dict):
            raise ValueError("RecoveryScope payload must be a dictionary.")
        return cls(
            affected_scopes=list(payload.get("affected_scopes") or []),
            downstream_scopes=list(payload.get("downstream_scopes") or []),
            salvage_policy=str(payload.get("salvage_policy") or "none"),
            schema_version=str(payload.get("schema_version") or "recovery_scope_v1"),
        )


@dataclass(frozen=True, slots=True)
class RecoveryReceipt:
    receipt_id: str
    action: str
    branch_id: str
    node: TimelineNodeRef
    status: str
    message: str
    artifact_paths: Dict[str, str] = field(default_factory=dict)
    removed_active_paths: List[str] = field(default_factory=list)
    quarantined_paths: List[Dict[str, str]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "recovery_receipt_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt_id", _clean_required(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "action", _clean_required(self.action, "action"))
        object.__setattr__(self, "branch_id", _clean_required(self.branch_id, "branch_id"))
        object.__setattr__(self, "status", _clean_required(self.status, "status"))
        object.__setattr__(self, "message", _clean_required(self.message, "message"))
        object.__setattr__(self, "artifact_paths", {str(k): str(v) for k, v in dict(self.artifact_paths).items()})
        object.__setattr__(self, "removed_active_paths", [str(item) for item in self.removed_active_paths if str(item).strip()])
        object.__setattr__(
            self,
            "quarantined_paths",
            [
                {"source": str(item.get("source") or ""), "quarantine": str(item.get("quarantine") or "")}
                for item in self.quarantined_paths
                if isinstance(item, dict) and str(item.get("source") or "").strip()
            ],
        )
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "action": self.action,
            "branch_id": self.branch_id,
            "node": self.node.to_dict(),
            "status": self.status,
            "message": self.message,
            "artifact_paths": dict(self.artifact_paths),
            "removed_active_paths": list(self.removed_active_paths),
            "quarantined_paths": [dict(item) for item in self.quarantined_paths],
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RecoveryReceipt":
        if not isinstance(payload, dict):
            raise ValueError("RecoveryReceipt payload must be a dictionary.")
        return cls(
            receipt_id=payload.get("receipt_id"),
            action=payload.get("action"),
            branch_id=payload.get("branch_id"),
            node=TimelineNodeRef.from_dict(payload.get("node") or {}),
            status=payload.get("status"),
            message=payload.get("message"),
            artifact_paths=payload.get("artifact_paths") or {},
            removed_active_paths=list(payload.get("removed_active_paths") or []),
            quarantined_paths=list(payload.get("quarantined_paths") or []),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "recovery_receipt_v1"),
        )


@dataclass(frozen=True, slots=True)
class RecoveryBranchHealth:
    book_id: str
    branch_id: str
    node: Optional[TimelineNodeRef]
    status: str
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    receipts: List[RecoveryReceipt] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "recovery_branch_health_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "book_id", _clean_required(self.book_id, "book_id"))
        object.__setattr__(self, "branch_id", _clean_required(self.branch_id, "branch_id"))
        object.__setattr__(self, "status", _clean_required(self.status, "status"))
        object.__setattr__(self, "blockers", [str(item) for item in self.blockers if str(item).strip()])
        object.__setattr__(self, "warnings", [str(item) for item in self.warnings if str(item).strip()])
        object.__setattr__(
            self,
            "receipts",
            [item if isinstance(item, RecoveryReceipt) else RecoveryReceipt.from_dict(item) for item in self.receipts],
        )
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "node": self.node.to_dict() if self.node else None,
            "status": self.status,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "receipts": [item.to_dict() for item in self.receipts],
            "details": dict(self.details),
        }
