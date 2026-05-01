from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .scope_selector import ScopeSelector
from .timeline_node import TimelineNodeRef
from .writing_target import NextWritingTarget, WritingGateStatus


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
class AuthorLoopEnvelopeOption:
    envelope_key: str
    label: str
    selector: ScopeSelector
    branch_id: str
    ready: bool
    target_action: Optional[str] = None
    allowed_actions: List[str] = field(default_factory=list)
    max_steps_hint: Optional[int] = None
    max_duration_seconds_hint: Optional[int] = None
    mutation_scope: str = "branch_local"
    canonical_changed: bool = False
    approval_required: bool = False
    stop_conditions: List[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "author_loop_envelope_option_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "envelope_key", _clean_required(self.envelope_key, "envelope_key"))
        object.__setattr__(self, "label", _clean_required(self.label, "label"))
        object.__setattr__(self, "branch_id", _clean_required(self.branch_id, "branch_id"))
        object.__setattr__(self, "target_action", _clean_optional(self.target_action))
        object.__setattr__(self, "blocked_reason", _clean_optional(self.blocked_reason))
        object.__setattr__(self, "mutation_scope", _clean_required(self.mutation_scope, "mutation_scope"))
        object.__setattr__(self, "allowed_actions", [str(item).strip() for item in self.allowed_actions if str(item).strip()])
        object.__setattr__(self, "stop_conditions", [str(item).strip() for item in self.stop_conditions if str(item).strip()])
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "envelope_key": self.envelope_key,
            "label": self.label,
            "selector": self.selector.to_dict(),
            "branch_id": self.branch_id,
            "ready": bool(self.ready),
            "target_action": self.target_action,
            "allowed_actions": list(self.allowed_actions),
            "max_steps_hint": self.max_steps_hint,
            "max_duration_seconds_hint": self.max_duration_seconds_hint,
            "mutation_scope": self.mutation_scope,
            "canonical_changed": bool(self.canonical_changed),
            "approval_required": bool(self.approval_required),
            "stop_conditions": list(self.stop_conditions),
            "blocked_reason": self.blocked_reason,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class AuthorLoopEnvelopeOptions:
    book_id: str
    branch_id: str
    selector: ScopeSelector
    node: Optional[TimelineNodeRef]
    target: NextWritingTarget
    writing_gates: WritingGateStatus
    envelopes: List[AuthorLoopEnvelopeOption]
    recommended_envelope: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "author_loop_envelope_options_v1"

    def __post_init__(self) -> None:
        book_id = _clean_required(self.book_id, "book_id")
        branch_id = _clean_required(self.branch_id, "branch_id")
        if self.selector.book_id != book_id:
            raise ValueError("selector.book_id must match book_id.")
        if self.selector.branch_id and self.selector.branch_id != branch_id:
            raise ValueError("selector.branch_id must match branch_id when provided.")
        object.__setattr__(self, "book_id", book_id)
        object.__setattr__(self, "branch_id", branch_id)
        object.__setattr__(self, "envelopes", [
            item if isinstance(item, AuthorLoopEnvelopeOption) else AuthorLoopEnvelopeOption(**item)
            for item in self.envelopes
        ])
        object.__setattr__(self, "recommended_envelope", _clean_optional(self.recommended_envelope))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "target": self.target.to_dict(),
            "writing_gates": self.writing_gates.to_dict(),
            "recommended_envelope": self.recommended_envelope,
            "envelopes": [item.to_dict() for item in self.envelopes],
            "details": dict(self.details),
        }
