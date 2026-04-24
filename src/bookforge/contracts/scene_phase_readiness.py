from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .produced_artifact import ProducedArtifactReceipt
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
class ScenePhaseActionReadiness:
    action: str
    legal: bool
    ready: bool
    mutation_scope: str
    missing_prerequisites: List[str] = field(default_factory=list)
    available_inputs: List[str] = field(default_factory=list)
    existing_outputs: List[ProducedArtifactReceipt] = field(default_factory=list)
    refusal_reason: Optional[str] = None
    recommended: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "scene_phase_action_readiness_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", _clean_required(self.action, "action"))
        object.__setattr__(self, "mutation_scope", _clean_required(self.mutation_scope, "mutation_scope"))
        object.__setattr__(self, "missing_prerequisites", [str(item).strip() for item in self.missing_prerequisites if str(item).strip()])
        object.__setattr__(self, "available_inputs", [str(item).strip() for item in self.available_inputs if str(item).strip()])
        object.__setattr__(self, "existing_outputs", [
            item if isinstance(item, ProducedArtifactReceipt) else ProducedArtifactReceipt.from_dict(item)
            for item in self.existing_outputs
        ])
        object.__setattr__(self, "refusal_reason", _clean_optional(self.refusal_reason))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "action": self.action,
            "legal": bool(self.legal),
            "ready": bool(self.ready),
            "mutation_scope": self.mutation_scope,
            "missing_prerequisites": list(self.missing_prerequisites),
            "available_inputs": list(self.available_inputs),
            "existing_outputs": [item.to_dict() for item in self.existing_outputs],
            "refusal_reason": self.refusal_reason,
            "recommended": bool(self.recommended),
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ScenePhaseActionReadiness":
        if not isinstance(payload, dict):
            raise ValueError("ScenePhaseActionReadiness payload must be a dictionary.")
        return cls(
            action=payload.get("action"),
            legal=bool(payload.get("legal")),
            ready=bool(payload.get("ready")),
            mutation_scope=payload.get("mutation_scope"),
            missing_prerequisites=list(payload.get("missing_prerequisites") or []),
            available_inputs=list(payload.get("available_inputs") or []),
            existing_outputs=list(payload.get("existing_outputs") or []),
            refusal_reason=payload.get("refusal_reason"),
            recommended=bool(payload.get("recommended")),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "scene_phase_action_readiness_v1"),
        )


@dataclass(frozen=True, slots=True)
class ScenePhaseReadiness:
    book_id: str
    selector: ScopeSelector
    scene_status: str
    actions: List[ScenePhaseActionReadiness]
    node: Optional[TimelineNodeRef] = None
    recommended_next_action: Optional[str] = None
    updated_at: Optional[str] = None
    schema_version: str = "scene_phase_readiness_v1"

    def __post_init__(self) -> None:
        book_id = _clean_required(self.book_id, "book_id")
        if self.selector.book_id != book_id:
            raise ValueError("selector.book_id must match book_id.")
        if self.node is not None and self.node.book_id != book_id:
            raise ValueError("node.book_id must match book_id when provided.")
        object.__setattr__(self, "book_id", book_id)
        object.__setattr__(self, "scene_status", _clean_required(self.scene_status, "scene_status"))
        object.__setattr__(self, "actions", [
            item if isinstance(item, ScenePhaseActionReadiness) else ScenePhaseActionReadiness.from_dict(item)
            for item in self.actions
        ])
        object.__setattr__(self, "recommended_next_action", _clean_optional(self.recommended_next_action))
        object.__setattr__(self, "updated_at", _clean_optional(self.updated_at))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "scene_status": self.scene_status,
            "recommended_next_action": self.recommended_next_action,
            "actions": [item.to_dict() for item in self.actions],
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ScenePhaseReadiness":
        if not isinstance(payload, dict):
            raise ValueError("ScenePhaseReadiness payload must be a dictionary.")
        node = payload.get("node") if isinstance(payload.get("node"), dict) else None
        return cls(
            book_id=payload.get("book_id"),
            selector=ScopeSelector.from_dict(payload.get("selector") or {}),
            node=TimelineNodeRef.from_dict(node) if node else None,
            scene_status=payload.get("scene_status"),
            recommended_next_action=payload.get("recommended_next_action"),
            actions=list(payload.get("actions") or []),
            updated_at=payload.get("updated_at"),
            schema_version=str(payload.get("schema_version") or "scene_phase_readiness_v1"),
        )
