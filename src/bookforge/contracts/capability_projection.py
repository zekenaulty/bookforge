from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .execution_option import _BRANCH_POLICIES
from .vocabulary import is_valid_produced_artifact_status


_UNIT_TYPES = {
    "query",
    "readiness",
    "primitive_action",
    "validation_gate",
    "macro_workflow",
    "promotion_action",
    "projection_skill",
}
_CAPABILITY_TYPES = {
    "query",
    "readiness",
    "action",
    "artifact",
    "diagnostic",
    "macro",
    "promotion",
    "gap",
}
_MUTATION_CLASSES = {
    "read_only",
    "diagnostic_only",
    "provisional_branch_mutation",
    "branch_mutation",
    "canonical_mutation",
    "promotion",
    "assembly",
}
_IMPLEMENTATION_STATUSES = {
    "implemented",
    "designed_gap",
    "documented_exclusion",
}


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


def _clean_string_list(values: Any) -> List[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("Expected list value.")
    return [str(item).strip() for item in values if str(item).strip()]


@dataclass(frozen=True, slots=True)
class CapabilityEvidenceSource:
    source_type: str
    reference: str
    note: Optional[str] = None
    schema_version: str = "capability_evidence_source_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_type", _clean_required(self.source_type, "source_type"))
        object.__setattr__(self, "reference", _clean_required(self.reference, "reference"))
        object.__setattr__(self, "note", _clean_optional(self.note))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_type": self.source_type,
            "reference": self.reference,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CapabilityEvidenceSource":
        if not isinstance(payload, dict):
            raise ValueError("CapabilityEvidenceSource payload must be a dictionary.")
        return cls(
            source_type=payload.get("source_type"),
            reference=payload.get("reference"),
            note=payload.get("note"),
            schema_version=str(payload.get("schema_version") or "capability_evidence_source_v1"),
        )


@dataclass(frozen=True, slots=True)
class CapabilityRefusalSemantics:
    refusal_mode: str
    refusal_reason_codes: List[str] = field(default_factory=list)
    human_message: Optional[str] = None
    schema_version: str = "capability_refusal_semantics_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "refusal_mode", _clean_required(self.refusal_mode, "refusal_mode"))
        object.__setattr__(self, "refusal_reason_codes", _clean_string_list(self.refusal_reason_codes))
        object.__setattr__(self, "human_message", _clean_optional(self.human_message))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "refusal_mode": self.refusal_mode,
            "refusal_reason_codes": list(self.refusal_reason_codes),
            "human_message": self.human_message,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CapabilityRefusalSemantics":
        if not isinstance(payload, dict):
            raise ValueError("CapabilityRefusalSemantics payload must be a dictionary.")
        return cls(
            refusal_mode=payload.get("refusal_mode"),
            refusal_reason_codes=list(payload.get("refusal_reason_codes") or []),
            human_message=payload.get("human_message"),
            schema_version=str(payload.get("schema_version") or "capability_refusal_semantics_v1"),
        )


@dataclass(frozen=True, slots=True)
class CapabilityDescriptor:
    capability_id: str
    human_label: str
    unit_type: str
    capability_type: str
    supported_scope_kinds: List[str]
    branch_policy: str
    mutation_class: str
    implementation_status: str = "implemented"
    required_selector_shape: List[str] = field(default_factory=list)
    action_key: Optional[str] = None
    query_key: Optional[str] = None
    approval_required: bool = False
    readiness_source: Optional[str] = None
    expected_receipt_type: Optional[str] = None
    process_area: Optional[str] = None
    produced_artifact_statuses: List[str] = field(default_factory=list)
    legal_next_action_relationships: List[str] = field(default_factory=list)
    refusal_semantics: Optional[CapabilityRefusalSemantics] = None
    child_actions: List[str] = field(default_factory=list)
    evidence_sources: List[CapabilityEvidenceSource] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "capability_descriptor_v1"

    def __post_init__(self) -> None:
        capability_id = _clean_required(self.capability_id, "capability_id")
        unit_type = _clean_required(self.unit_type, "unit_type")
        capability_type = _clean_required(self.capability_type, "capability_type")
        branch_policy = _clean_required(self.branch_policy, "branch_policy")
        mutation_class = _clean_required(self.mutation_class, "mutation_class")
        implementation_status = _clean_required(self.implementation_status, "implementation_status")
        if unit_type not in _UNIT_TYPES:
            raise ValueError(f"Unknown capability unit_type: {unit_type}")
        if capability_type not in _CAPABILITY_TYPES:
            raise ValueError(f"Unknown capability_type: {capability_type}")
        if branch_policy not in _BRANCH_POLICIES:
            raise ValueError(f"Unknown branch_policy: {branch_policy}")
        if mutation_class not in _MUTATION_CLASSES:
            raise ValueError(f"Unknown mutation_class: {mutation_class}")
        if implementation_status not in _IMPLEMENTATION_STATUSES:
            raise ValueError(f"Unknown implementation_status: {implementation_status}")
        statuses = _clean_string_list(self.produced_artifact_statuses)
        for status in statuses:
            if not is_valid_produced_artifact_status(status):
                raise ValueError(f"Unknown produced artifact status: {status}")
        if "ready" in self.details or "allowed" in self.details:
            raise ValueError("CapabilityDescriptor must not carry dynamic readiness fields.")
        object.__setattr__(self, "capability_id", capability_id)
        object.__setattr__(self, "human_label", _clean_required(self.human_label, "human_label"))
        object.__setattr__(self, "unit_type", unit_type)
        object.__setattr__(self, "capability_type", capability_type)
        object.__setattr__(self, "supported_scope_kinds", _clean_string_list(self.supported_scope_kinds))
        object.__setattr__(self, "required_selector_shape", _clean_string_list(self.required_selector_shape))
        object.__setattr__(self, "branch_policy", branch_policy)
        object.__setattr__(self, "mutation_class", mutation_class)
        object.__setattr__(self, "implementation_status", implementation_status)
        object.__setattr__(self, "action_key", _clean_optional(self.action_key))
        object.__setattr__(self, "query_key", _clean_optional(self.query_key))
        object.__setattr__(self, "readiness_source", _clean_optional(self.readiness_source))
        object.__setattr__(self, "expected_receipt_type", _clean_optional(self.expected_receipt_type))
        object.__setattr__(self, "process_area", _clean_optional(self.process_area))
        object.__setattr__(self, "produced_artifact_statuses", statuses)
        object.__setattr__(self, "legal_next_action_relationships", _clean_string_list(self.legal_next_action_relationships))
        object.__setattr__(self, "child_actions", _clean_string_list(self.child_actions))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "human_label": self.human_label,
            "unit_type": self.unit_type,
            "capability_type": self.capability_type,
            "implementation_status": self.implementation_status,
            "action_key": self.action_key,
            "query_key": self.query_key,
            "supported_scope_kinds": list(self.supported_scope_kinds),
            "required_selector_shape": list(self.required_selector_shape),
            "branch_policy": self.branch_policy,
            "mutation_class": self.mutation_class,
            "approval_required": bool(self.approval_required),
            "readiness_source": self.readiness_source,
            "expected_receipt_type": self.expected_receipt_type,
            "process_area": self.process_area,
            "produced_artifact_statuses": list(self.produced_artifact_statuses),
            "legal_next_action_relationships": list(self.legal_next_action_relationships),
            "refusal_semantics": self.refusal_semantics.to_dict() if self.refusal_semantics else None,
            "child_actions": list(self.child_actions),
            "evidence_sources": [source.to_dict() for source in self.evidence_sources],
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CapabilityDescriptor":
        if not isinstance(payload, dict):
            raise ValueError("CapabilityDescriptor payload must be a dictionary.")
        refusal = payload.get("refusal_semantics")
        return cls(
            capability_id=payload.get("capability_id"),
            human_label=payload.get("human_label"),
            unit_type=payload.get("unit_type"),
            capability_type=payload.get("capability_type"),
            implementation_status=str(payload.get("implementation_status") or "implemented"),
            action_key=payload.get("action_key"),
            query_key=payload.get("query_key"),
            supported_scope_kinds=list(payload.get("supported_scope_kinds") or []),
            required_selector_shape=list(payload.get("required_selector_shape") or []),
            branch_policy=payload.get("branch_policy"),
            mutation_class=payload.get("mutation_class"),
            approval_required=bool(payload.get("approval_required")),
            readiness_source=payload.get("readiness_source"),
            expected_receipt_type=payload.get("expected_receipt_type"),
            process_area=payload.get("process_area"),
            produced_artifact_statuses=list(payload.get("produced_artifact_statuses") or []),
            legal_next_action_relationships=list(payload.get("legal_next_action_relationships") or []),
            refusal_semantics=CapabilityRefusalSemantics.from_dict(refusal) if isinstance(refusal, dict) else None,
            child_actions=list(payload.get("child_actions") or []),
            evidence_sources=[
                CapabilityEvidenceSource.from_dict(source)
                for source in payload.get("evidence_sources") or []
                if isinstance(source, dict)
            ],
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "capability_descriptor_v1"),
        )


@dataclass(frozen=True, slots=True)
class CapabilityProjection:
    capabilities: List[CapabilityDescriptor]
    projection_source: str = "static_registry"
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "capability_projection_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "projection_source", _clean_required(self.projection_source, "projection_source"))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})
        seen = set()
        for capability in self.capabilities:
            if capability.capability_id in seen:
                raise ValueError(f"Duplicate capability_id: {capability.capability_id}")
            seen.add(capability.capability_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "projection_source": self.projection_source,
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CapabilityProjection":
        if not isinstance(payload, dict):
            raise ValueError("CapabilityProjection payload must be a dictionary.")
        return cls(
            capabilities=[
                CapabilityDescriptor.from_dict(item)
                for item in payload.get("capabilities") or []
                if isinstance(item, dict)
            ],
            projection_source=str(payload.get("projection_source") or "static_registry"),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "capability_projection_v1"),
        )
