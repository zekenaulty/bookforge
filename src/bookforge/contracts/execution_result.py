from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .scope_selector import ScopeSelector
from .timeline_node import TimelineNodeRef
from .vocabulary import is_valid_execution_result_status


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
class ExecutionResult:
    result_id: str
    action: str
    status: str
    node: TimelineNodeRef
    selector: ScopeSelector
    message: Optional[str] = None
    issue_ticket_ids: List[str] = field(default_factory=list)
    artifact_paths: Dict[str, str] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    emitted_at: Optional[str] = None
    request_id: Optional[str] = None
    schema_version: str = "execution_result_v1"

    def __post_init__(self) -> None:
        result_id = _clean_required(self.result_id, "result_id")
        action = _clean_required(self.action, "action")
        status = _clean_required(self.status, "status")
        if not is_valid_execution_result_status(status):
            raise ValueError(f"Unknown execution result status: {status}")
        if self.node.book_id != self.selector.book_id:
            raise ValueError("selector.book_id must match node.book_id.")
        object.__setattr__(self, "result_id", result_id)
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "message", _clean_optional(self.message))
        object.__setattr__(self, "emitted_at", _clean_optional(self.emitted_at))
        object.__setattr__(self, "request_id", _clean_optional(self.request_id))
        object.__setattr__(self, "issue_ticket_ids", [str(item).strip() for item in self.issue_ticket_ids if str(item).strip()])
        object.__setattr__(self, "artifact_paths", {str(key): str(value) for key, value in dict(self.artifact_paths).items() if str(key).strip() and str(value).strip()})
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "result_id": self.result_id,
            "action": self.action,
            "status": self.status,
            "node": self.node.to_dict(),
            "selector": self.selector.to_dict(),
            "message": self.message,
            "issue_ticket_ids": list(self.issue_ticket_ids),
            "artifact_paths": dict(self.artifact_paths),
            "details": dict(self.details),
            "emitted_at": self.emitted_at,
            "request_id": self.request_id,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ExecutionResult":
        if not isinstance(payload, dict):
            raise ValueError("ExecutionResult payload must be a dictionary.")
        return cls(
            result_id=payload.get("result_id"),
            action=payload.get("action"),
            status=payload.get("status"),
            node=TimelineNodeRef.from_dict(payload.get("node") or {}),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            message=payload.get("message"),
            issue_ticket_ids=list(payload.get("issue_ticket_ids") or []),
            artifact_paths=payload.get("artifact_paths") or {},
            details=payload.get("details") or {},
            emitted_at=payload.get("emitted_at"),
            request_id=payload.get("request_id"),
            schema_version=str(payload.get("schema_version") or "execution_result_v1"),
        )
