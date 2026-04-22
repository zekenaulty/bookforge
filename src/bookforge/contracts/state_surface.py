from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .scope_selector import ScopeSelector
from .timeline_node import TimelineNodeRef


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _coerce_int_map(payload: Any) -> Dict[str, int]:
    if not isinstance(payload, dict):
        return {}
    result: Dict[str, int] = {}
    for key, value in payload.items():
        name = str(key or "").strip()
        if not name:
            continue
        try:
            resolved = int(value)
        except (TypeError, ValueError):
            continue
        result[name] = resolved
    return result


def _coerce_cursor(payload: Any) -> Dict[str, int]:
    if not isinstance(payload, dict):
        return {}
    result: Dict[str, int] = {}
    for key in ("chapter", "scene"):
        try:
            resolved = int(payload.get(key))
        except (TypeError, ValueError):
            continue
        result[key] = resolved
    return result


@dataclass(frozen=True, slots=True)
class StateSurface:
    book_id: str
    node: TimelineNodeRef
    selector: ScopeSelector
    state_status: Optional[str] = None
    workflow_run_mode: Optional[str] = None
    workflow_source_run_id: Optional[str] = None
    source_artifact_class: Optional[str] = None
    source_artifact_path: Optional[str] = None
    active_section: Optional[Dict[str, Any]] = None
    cursor: Dict[str, int] = field(default_factory=dict)
    integrity_status: Optional[str] = None
    integrity_issue_codes: List[str] = field(default_factory=list)
    branch_count: int = 0
    chapter_status_counts: Dict[str, int] = field(default_factory=dict)
    updated_at: Optional[str] = None
    schema_version: str = "state_surface_v1"

    def __post_init__(self) -> None:
        book_id = str(self.book_id or "").strip()
        if not book_id:
            raise ValueError("book_id is required.")
        if self.node.book_id != book_id:
            raise ValueError("node.book_id must match state surface book_id.")
        if self.selector.book_id != book_id:
            raise ValueError("selector.book_id must match state surface book_id.")
        if int(self.branch_count or 0) < 0:
            raise ValueError("branch_count must be >= 0.")

        object.__setattr__(self, "book_id", book_id)
        object.__setattr__(self, "state_status", _clean_optional(self.state_status))
        object.__setattr__(self, "workflow_run_mode", _clean_optional(self.workflow_run_mode))
        object.__setattr__(self, "workflow_source_run_id", _clean_optional(self.workflow_source_run_id))
        object.__setattr__(self, "source_artifact_class", _clean_optional(self.source_artifact_class))
        object.__setattr__(self, "source_artifact_path", _clean_optional(self.source_artifact_path))
        object.__setattr__(self, "integrity_status", _clean_optional(self.integrity_status))
        object.__setattr__(self, "updated_at", _clean_optional(self.updated_at))
        object.__setattr__(self, "cursor", _coerce_cursor(self.cursor))
        object.__setattr__(self, "chapter_status_counts", _coerce_int_map(self.chapter_status_counts))
        object.__setattr__(self, "integrity_issue_codes", [str(code).strip() for code in self.integrity_issue_codes if str(code).strip()])
        object.__setattr__(self, "branch_count", int(self.branch_count or 0))
        if isinstance(self.active_section, dict):
            object.__setattr__(self, "active_section", dict(self.active_section))
        else:
            object.__setattr__(self, "active_section", None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "node": self.node.to_dict(),
            "selector": self.selector.to_dict(),
            "state_status": self.state_status,
            "workflow_run_mode": self.workflow_run_mode,
            "workflow_source_run_id": self.workflow_source_run_id,
            "source_artifact_class": self.source_artifact_class,
            "source_artifact_path": self.source_artifact_path,
            "active_section": dict(self.active_section) if isinstance(self.active_section, dict) else None,
            "cursor": dict(self.cursor),
            "integrity_status": self.integrity_status,
            "integrity_issue_codes": list(self.integrity_issue_codes),
            "branch_count": self.branch_count,
            "chapter_status_counts": dict(self.chapter_status_counts),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "StateSurface":
        if not isinstance(payload, dict):
            raise ValueError("StateSurface payload must be a dictionary.")
        return cls(
            book_id=payload.get("book_id"),
            node=TimelineNodeRef.from_dict(payload.get("node") or {}),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            state_status=payload.get("state_status"),
            workflow_run_mode=payload.get("workflow_run_mode"),
            workflow_source_run_id=payload.get("workflow_source_run_id"),
            source_artifact_class=payload.get("source_artifact_class"),
            source_artifact_path=payload.get("source_artifact_path"),
            active_section=payload.get("active_section"),
            cursor=payload.get("cursor") or {},
            integrity_status=payload.get("integrity_status"),
            integrity_issue_codes=list(payload.get("integrity_issue_codes") or []),
            branch_count=payload.get("branch_count") or 0,
            chapter_status_counts=payload.get("chapter_status_counts") or {},
            updated_at=payload.get("updated_at"),
            schema_version=str(payload.get("schema_version") or "state_surface_v1"),
        )
