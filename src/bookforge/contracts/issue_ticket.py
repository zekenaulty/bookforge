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
class IssueTicket:
    ticket_id: str
    category: str
    code: str
    severity: str
    message: str
    node: TimelineNodeRef
    selector: ScopeSelector
    branch_scope: str = "main"
    status: str = "open"
    details: Dict[str, Any] = field(default_factory=dict)
    detected_at: Optional[str] = None
    schema_version: str = "issue_ticket_v1"

    def __post_init__(self) -> None:
        ticket_id = _clean_required(self.ticket_id, "ticket_id")
        category = _clean_required(self.category, "category")
        code = _clean_required(self.code, "code")
        severity = _clean_required(self.severity, "severity")
        message = _clean_required(self.message, "message")
        branch_scope = _clean_required(self.branch_scope, "branch_scope")
        status = _clean_required(self.status, "status")
        if self.node.book_id != self.selector.book_id:
            raise ValueError("selector.book_id must match node.book_id.")
        object.__setattr__(self, "ticket_id", ticket_id)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "branch_scope", branch_scope)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "detected_at", _clean_optional(self.detected_at))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ticket_id": self.ticket_id,
            "category": self.category,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "node": self.node.to_dict(),
            "selector": self.selector.to_dict(),
            "branch_scope": self.branch_scope,
            "status": self.status,
            "details": dict(self.details),
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "IssueTicket":
        if not isinstance(payload, dict):
            raise ValueError("IssueTicket payload must be a dictionary.")
        return cls(
            ticket_id=payload.get("ticket_id"),
            category=payload.get("category"),
            code=payload.get("code"),
            severity=payload.get("severity"),
            message=payload.get("message"),
            node=TimelineNodeRef.from_dict(payload.get("node") or {}),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            branch_scope=payload.get("branch_scope") or "main",
            status=payload.get("status") or "open",
            details=payload.get("details") or {},
            detected_at=payload.get("detected_at"),
            schema_version=str(payload.get("schema_version") or "issue_ticket_v1"),
        )
