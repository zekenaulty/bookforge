from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
class NextWritingTarget:
    book_id: str
    branch_id: str
    selector: ScopeSelector
    status: str
    book_complete: bool
    can_continue: bool
    current_scene: Optional[Dict[str, Any]] = None
    next_scene: Optional[Dict[str, Any]] = None
    next_section: Optional[Dict[str, Any]] = None
    next_chapter: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None
    blocked_reason: Optional[str] = None
    node: Optional[TimelineNodeRef] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "next_writing_target_v1"

    def __post_init__(self) -> None:
        book_id = _clean_required(self.book_id, "book_id")
        branch_id = _clean_required(self.branch_id, "branch_id")
        status = _clean_required(self.status, "status")
        if self.selector.book_id != book_id:
            raise ValueError("selector.book_id must match book_id.")
        if self.selector.branch_id and self.selector.branch_id != branch_id:
            raise ValueError("selector.branch_id must match branch_id when provided.")
        if self.node is not None and self.node.book_id != book_id:
            raise ValueError("node.book_id must match book_id when provided.")
        object.__setattr__(self, "book_id", book_id)
        object.__setattr__(self, "branch_id", branch_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "recommended_action", _clean_optional(self.recommended_action))
        object.__setattr__(self, "blocked_reason", _clean_optional(self.blocked_reason))
        object.__setattr__(self, "current_scene", dict(self.current_scene) if isinstance(self.current_scene, dict) else None)
        object.__setattr__(self, "next_scene", dict(self.next_scene) if isinstance(self.next_scene, dict) else None)
        object.__setattr__(self, "next_section", dict(self.next_section) if isinstance(self.next_section, dict) else None)
        object.__setattr__(self, "next_chapter", dict(self.next_chapter) if isinstance(self.next_chapter, dict) else None)
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "status": self.status,
            "book_complete": bool(self.book_complete),
            "can_continue": bool(self.can_continue),
            "current_scene": dict(self.current_scene) if self.current_scene else None,
            "next_scene": dict(self.next_scene) if self.next_scene else None,
            "next_section": dict(self.next_section) if self.next_section else None,
            "next_chapter": dict(self.next_chapter) if self.next_chapter else None,
            "recommended_action": self.recommended_action,
            "blocked_reason": self.blocked_reason,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NextWritingTarget":
        if not isinstance(payload, dict):
            raise ValueError("NextWritingTarget payload must be a dictionary.")
        node = payload.get("node") if isinstance(payload.get("node"), dict) else None
        return cls(
            book_id=payload.get("book_id"),
            branch_id=payload.get("branch_id"),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            node=TimelineNodeRef.from_dict(node) if node else None,
            status=payload.get("status"),
            book_complete=bool(payload.get("book_complete")),
            can_continue=bool(payload.get("can_continue")),
            current_scene=payload.get("current_scene") if isinstance(payload.get("current_scene"), dict) else None,
            next_scene=payload.get("next_scene") if isinstance(payload.get("next_scene"), dict) else None,
            next_section=payload.get("next_section") if isinstance(payload.get("next_section"), dict) else None,
            next_chapter=payload.get("next_chapter") if isinstance(payload.get("next_chapter"), dict) else None,
            recommended_action=payload.get("recommended_action"),
            blocked_reason=payload.get("blocked_reason"),
            details=payload.get("details") if isinstance(payload.get("details"), dict) else {},
            schema_version=str(payload.get("schema_version") or "next_writing_target_v1"),
        )


@dataclass(frozen=True, slots=True)
class WritingGate:
    gate_key: str
    label: str
    status: str
    ready: bool
    scope: Dict[str, Any] = field(default_factory=dict)
    action: Optional[str] = None
    blocked_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "writing_gate_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_key", _clean_required(self.gate_key, "gate_key"))
        object.__setattr__(self, "label", _clean_required(self.label, "label"))
        object.__setattr__(self, "status", _clean_required(self.status, "status"))
        object.__setattr__(self, "action", _clean_optional(self.action))
        object.__setattr__(self, "blocked_reason", _clean_optional(self.blocked_reason))
        object.__setattr__(self, "scope", dict(self.scope) if isinstance(self.scope, dict) else {})
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_key": self.gate_key,
            "label": self.label,
            "status": self.status,
            "ready": bool(self.ready),
            "scope": dict(self.scope),
            "action": self.action,
            "blocked_reason": self.blocked_reason,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WritingGate":
        if not isinstance(payload, dict):
            raise ValueError("WritingGate payload must be a dictionary.")
        return cls(
            gate_key=payload.get("gate_key"),
            label=payload.get("label"),
            status=payload.get("status"),
            ready=bool(payload.get("ready")),
            scope=payload.get("scope") if isinstance(payload.get("scope"), dict) else {},
            action=payload.get("action"),
            blocked_reason=payload.get("blocked_reason"),
            details=payload.get("details") if isinstance(payload.get("details"), dict) else {},
            schema_version=str(payload.get("schema_version") or "writing_gate_v1"),
        )


@dataclass(frozen=True, slots=True)
class WritingGateStatus:
    book_id: str
    branch_id: str
    selector: ScopeSelector
    gates: List[WritingGate]
    book_complete: bool
    can_continue: bool
    recommended_next_action: Optional[str] = None
    blocked_reason: Optional[str] = None
    node: Optional[TimelineNodeRef] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "writing_gate_status_v1"

    def __post_init__(self) -> None:
        book_id = _clean_required(self.book_id, "book_id")
        branch_id = _clean_required(self.branch_id, "branch_id")
        if self.selector.book_id != book_id:
            raise ValueError("selector.book_id must match book_id.")
        if self.selector.branch_id and self.selector.branch_id != branch_id:
            raise ValueError("selector.branch_id must match branch_id when provided.")
        if self.node is not None and self.node.book_id != book_id:
            raise ValueError("node.book_id must match book_id when provided.")
        object.__setattr__(self, "book_id", book_id)
        object.__setattr__(self, "branch_id", branch_id)
        object.__setattr__(self, "gates", [
            item if isinstance(item, WritingGate) else WritingGate.from_dict(item)
            for item in self.gates
        ])
        object.__setattr__(self, "recommended_next_action", _clean_optional(self.recommended_next_action))
        object.__setattr__(self, "blocked_reason", _clean_optional(self.blocked_reason))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "book_complete": bool(self.book_complete),
            "can_continue": bool(self.can_continue),
            "recommended_next_action": self.recommended_next_action,
            "blocked_reason": self.blocked_reason,
            "gates": [item.to_dict() for item in self.gates],
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WritingGateStatus":
        if not isinstance(payload, dict):
            raise ValueError("WritingGateStatus payload must be a dictionary.")
        node = payload.get("node") if isinstance(payload.get("node"), dict) else None
        return cls(
            book_id=payload.get("book_id"),
            branch_id=payload.get("branch_id"),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            node=TimelineNodeRef.from_dict(node) if node else None,
            book_complete=bool(payload.get("book_complete")),
            can_continue=bool(payload.get("can_continue")),
            recommended_next_action=payload.get("recommended_next_action"),
            blocked_reason=payload.get("blocked_reason"),
            gates=list(payload.get("gates") or []),
            details=payload.get("details") if isinstance(payload.get("details"), dict) else {},
            schema_version=str(payload.get("schema_version") or "writing_gate_status_v1"),
        )


@dataclass(frozen=True, slots=True)
class WritingBootstrapStage:
    stage_key: str
    label: str
    status: str
    ready: bool
    action: Optional[str] = None
    approval_class: Optional[str] = None
    target_selector: Dict[str, Any] = field(default_factory=dict)
    blocked_reason: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "writing_bootstrap_stage_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "stage_key", _clean_required(self.stage_key, "stage_key"))
        object.__setattr__(self, "label", _clean_required(self.label, "label"))
        object.__setattr__(self, "status", _clean_required(self.status, "status"))
        object.__setattr__(self, "action", _clean_optional(self.action))
        object.__setattr__(self, "approval_class", _clean_optional(self.approval_class))
        object.__setattr__(self, "blocked_reason", _clean_optional(self.blocked_reason))
        object.__setattr__(
            self,
            "target_selector",
            dict(self.target_selector) if isinstance(self.target_selector, dict) else {},
        )
        object.__setattr__(
            self,
            "evidence_refs",
            [str(item).strip() for item in self.evidence_refs if str(item).strip()],
        )
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stage_key": self.stage_key,
            "label": self.label,
            "status": self.status,
            "ready": bool(self.ready),
            "action": self.action,
            "approval_class": self.approval_class,
            "target_selector": dict(self.target_selector),
            "blocked_reason": self.blocked_reason,
            "evidence_refs": list(self.evidence_refs),
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WritingBootstrapStage":
        if not isinstance(payload, dict):
            raise ValueError("WritingBootstrapStage payload must be a dictionary.")
        return cls(
            stage_key=payload.get("stage_key"),
            label=payload.get("label"),
            status=payload.get("status"),
            ready=bool(payload.get("ready")),
            action=payload.get("action"),
            approval_class=payload.get("approval_class"),
            target_selector=payload.get("target_selector") if isinstance(payload.get("target_selector"), dict) else {},
            blocked_reason=payload.get("blocked_reason"),
            evidence_refs=list(payload.get("evidence_refs") or []),
            details=payload.get("details") if isinstance(payload.get("details"), dict) else {},
            schema_version=str(payload.get("schema_version") or "writing_bootstrap_stage_v1"),
        )


@dataclass(frozen=True, slots=True)
class WritingBootstrapStatus:
    book_id: str
    status: str
    can_start_writing: bool
    stages: List[WritingBootstrapStage]
    recommended_action: Optional[str] = None
    required_approval_class: Optional[str] = None
    target_selector: Dict[str, Any] = field(default_factory=dict)
    target_branch_id: Optional[str] = None
    blocked_reason: Optional[str] = None
    artifact_refs: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    source: str = "bookforge.query.writing_bootstrap.v1"
    schema_version: str = "writing_bootstrap_status_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "book_id", _clean_required(self.book_id, "book_id"))
        object.__setattr__(self, "status", _clean_required(self.status, "status"))
        object.__setattr__(
            self,
            "stages",
            [item if isinstance(item, WritingBootstrapStage) else WritingBootstrapStage.from_dict(item) for item in self.stages],
        )
        object.__setattr__(self, "recommended_action", _clean_optional(self.recommended_action))
        object.__setattr__(self, "required_approval_class", _clean_optional(self.required_approval_class))
        object.__setattr__(self, "target_branch_id", _clean_optional(self.target_branch_id))
        object.__setattr__(self, "blocked_reason", _clean_optional(self.blocked_reason))
        object.__setattr__(
            self,
            "target_selector",
            dict(self.target_selector) if isinstance(self.target_selector, dict) else {},
        )
        object.__setattr__(
            self,
            "artifact_refs",
            [dict(item) for item in self.artifact_refs if isinstance(item, dict)],
        )
        object.__setattr__(
            self,
            "warnings",
            [str(item).strip() for item in self.warnings if str(item).strip()],
        )
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source": self.source,
            "book_id": self.book_id,
            "status": self.status,
            "can_start_writing": bool(self.can_start_writing),
            "recommended_action": self.recommended_action,
            "required_approval_class": self.required_approval_class,
            "target_selector": dict(self.target_selector),
            "target_branch_id": self.target_branch_id,
            "blocked_reason": self.blocked_reason,
            "stages": [item.to_dict() for item in self.stages],
            "artifact_refs": [dict(item) for item in self.artifact_refs],
            "warnings": list(self.warnings),
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WritingBootstrapStatus":
        if not isinstance(payload, dict):
            raise ValueError("WritingBootstrapStatus payload must be a dictionary.")
        return cls(
            book_id=payload.get("book_id"),
            status=payload.get("status"),
            can_start_writing=bool(payload.get("can_start_writing")),
            recommended_action=payload.get("recommended_action"),
            required_approval_class=payload.get("required_approval_class"),
            target_selector=payload.get("target_selector") if isinstance(payload.get("target_selector"), dict) else {},
            target_branch_id=payload.get("target_branch_id"),
            blocked_reason=payload.get("blocked_reason"),
            stages=list(payload.get("stages") or []),
            artifact_refs=list(payload.get("artifact_refs") or []),
            warnings=list(payload.get("warnings") or []),
            details=payload.get("details") if isinstance(payload.get("details"), dict) else {},
            source=str(payload.get("source") or "bookforge.query.writing_bootstrap.v1"),
            schema_version=str(payload.get("schema_version") or "writing_bootstrap_status_v1"),
        )
