from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .scope_selector import ScopeSelector
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


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    request_id: str
    action: str
    selector: ScopeSelector
    expected_node: Optional[TimelineNodeRef] = None
    branch_id: Optional[str] = None
    requested_at: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "execution_request_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _clean_required(self.request_id, "request_id"))
        object.__setattr__(self, "action", _clean_required(self.action, "action"))
        object.__setattr__(self, "branch_id", _clean_optional(self.branch_id))
        object.__setattr__(self, "requested_at", _clean_optional(self.requested_at))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "action": self.action,
            "selector": self.selector.to_dict(),
            "expected_node": self.expected_node.to_dict() if self.expected_node else None,
            "branch_id": self.branch_id,
            "requested_at": self.requested_at,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ExecutionRequest":
        if not isinstance(payload, dict):
            raise ValueError("ExecutionRequest payload must be a dictionary.")
        expected_node = payload.get("expected_node") if isinstance(payload.get("expected_node"), dict) else None
        return cls(
            request_id=payload.get("request_id"),
            action=payload.get("action"),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            expected_node=TimelineNodeRef.from_dict(expected_node) if expected_node else None,
            branch_id=payload.get("branch_id"),
            requested_at=payload.get("requested_at"),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "execution_request_v1"),
        )
