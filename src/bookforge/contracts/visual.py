from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
class VisualProviderDescriptor:
    provider_id: str
    model_id: str
    display_name: str
    implementation_status: str
    aliases: List[str] = field(default_factory=list)
    supported_purposes: List[str] = field(default_factory=list)
    supported_aspect_ratios: List[str] = field(default_factory=list)
    output_formats: List[str] = field(default_factory=list)
    generation_supported: bool = True
    edit_supported: bool = False
    reference_image_supported: bool = False
    transparent_background_supported: bool = False
    max_reference_images: Optional[int] = None
    default_for_purpose: List[str] = field(default_factory=list)
    price_notes: Optional[str] = None
    price_verified: bool = False
    verification_date: Optional[str] = None
    source_urls: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "visual_provider_descriptor_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_id", _clean_required(self.provider_id, "provider_id"))
        object.__setattr__(self, "model_id", _clean_required(self.model_id, "model_id"))
        object.__setattr__(self, "display_name", _clean_required(self.display_name, "display_name"))
        object.__setattr__(self, "implementation_status", _clean_required(self.implementation_status, "implementation_status"))
        object.__setattr__(self, "aliases", _clean_string_list(self.aliases))
        object.__setattr__(self, "supported_purposes", _clean_string_list(self.supported_purposes))
        object.__setattr__(self, "supported_aspect_ratios", _clean_string_list(self.supported_aspect_ratios))
        object.__setattr__(self, "output_formats", _clean_string_list(self.output_formats))
        object.__setattr__(self, "default_for_purpose", _clean_string_list(self.default_for_purpose))
        object.__setattr__(self, "price_notes", _clean_optional(self.price_notes))
        object.__setattr__(self, "verification_date", _clean_optional(self.verification_date))
        object.__setattr__(self, "source_urls", _clean_string_list(self.source_urls))
        object.__setattr__(self, "limitations", _clean_string_list(self.limitations))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    @property
    def key(self) -> str:
        return f"{self.provider_id}:{self.model_id}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "key": self.key,
            "display_name": self.display_name,
            "implementation_status": self.implementation_status,
            "aliases": list(self.aliases),
            "supported_purposes": list(self.supported_purposes),
            "supported_aspect_ratios": list(self.supported_aspect_ratios),
            "output_formats": list(self.output_formats),
            "generation_supported": bool(self.generation_supported),
            "edit_supported": bool(self.edit_supported),
            "reference_image_supported": bool(self.reference_image_supported),
            "transparent_background_supported": bool(self.transparent_background_supported),
            "max_reference_images": self.max_reference_images,
            "default_for_purpose": list(self.default_for_purpose),
            "price_notes": self.price_notes,
            "price_verified": bool(self.price_verified),
            "verification_date": self.verification_date,
            "source_urls": list(self.source_urls),
            "limitations": list(self.limitations),
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "VisualProviderDescriptor":
        if not isinstance(payload, dict):
            raise ValueError("VisualProviderDescriptor payload must be a dictionary.")
        return cls(
            provider_id=payload.get("provider_id"),
            model_id=payload.get("model_id"),
            display_name=payload.get("display_name"),
            implementation_status=payload.get("implementation_status"),
            aliases=list(payload.get("aliases") or []),
            supported_purposes=list(payload.get("supported_purposes") or []),
            supported_aspect_ratios=list(payload.get("supported_aspect_ratios") or []),
            output_formats=list(payload.get("output_formats") or []),
            generation_supported=bool(payload.get("generation_supported", True)),
            edit_supported=bool(payload.get("edit_supported")),
            reference_image_supported=bool(payload.get("reference_image_supported")),
            transparent_background_supported=bool(payload.get("transparent_background_supported")),
            max_reference_images=payload.get("max_reference_images"),
            default_for_purpose=list(payload.get("default_for_purpose") or []),
            price_notes=payload.get("price_notes"),
            price_verified=bool(payload.get("price_verified")),
            verification_date=payload.get("verification_date"),
            source_urls=list(payload.get("source_urls") or []),
            limitations=list(payload.get("limitations") or []),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "visual_provider_descriptor_v1"),
        )


@dataclass(frozen=True, slots=True)
class VisualPromptPlan:
    prompt_plan_id: str
    visual_purpose: str
    provider_id: str
    model_id: str
    user_prompt: str
    provider_prompt: str
    negative_prompt: Optional[str] = None
    style_profile: Optional[str] = None
    reference_image_refs: List[str] = field(default_factory=list)
    layer_intent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "visual_prompt_plan_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "prompt_plan_id", _clean_required(self.prompt_plan_id, "prompt_plan_id"))
        object.__setattr__(self, "visual_purpose", _clean_required(self.visual_purpose, "visual_purpose"))
        object.__setattr__(self, "provider_id", _clean_required(self.provider_id, "provider_id"))
        object.__setattr__(self, "model_id", _clean_required(self.model_id, "model_id"))
        object.__setattr__(self, "user_prompt", _clean_required(self.user_prompt, "user_prompt"))
        object.__setattr__(self, "provider_prompt", _clean_required(self.provider_prompt, "provider_prompt"))
        object.__setattr__(self, "negative_prompt", _clean_optional(self.negative_prompt))
        object.__setattr__(self, "style_profile", _clean_optional(self.style_profile))
        object.__setattr__(self, "reference_image_refs", _clean_string_list(self.reference_image_refs))
        object.__setattr__(self, "layer_intent", _clean_optional(self.layer_intent))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "prompt_plan_id": self.prompt_plan_id,
            "visual_purpose": self.visual_purpose,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "user_prompt": self.user_prompt,
            "provider_prompt": self.provider_prompt,
            "negative_prompt": self.negative_prompt,
            "style_profile": self.style_profile,
            "reference_image_refs": list(self.reference_image_refs),
            "layer_intent": self.layer_intent,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class VisualActionReadiness:
    action: str
    visual_purpose: str
    provider_id: str
    model_id: str
    ready: bool
    allowed: bool
    missing_prerequisites: List[str] = field(default_factory=list)
    refusal_reasons: List[str] = field(default_factory=list)
    produced_artifact_statuses: List[str] = field(default_factory=list)
    provider: Optional[VisualProviderDescriptor] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "visual_action_readiness_v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", _clean_required(self.action, "action"))
        object.__setattr__(self, "visual_purpose", _clean_required(self.visual_purpose, "visual_purpose"))
        object.__setattr__(self, "provider_id", _clean_required(self.provider_id, "provider_id"))
        object.__setattr__(self, "model_id", _clean_required(self.model_id, "model_id"))
        object.__setattr__(self, "missing_prerequisites", _clean_string_list(self.missing_prerequisites))
        object.__setattr__(self, "refusal_reasons", _clean_string_list(self.refusal_reasons))
        object.__setattr__(self, "produced_artifact_statuses", _clean_string_list(self.produced_artifact_statuses))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "action": self.action,
            "visual_purpose": self.visual_purpose,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "ready": bool(self.ready),
            "allowed": bool(self.allowed),
            "missing_prerequisites": list(self.missing_prerequisites),
            "refusal_reasons": list(self.refusal_reasons),
            "produced_artifact_statuses": list(self.produced_artifact_statuses),
            "provider": self.provider.to_dict() if self.provider else None,
            "details": dict(self.details),
        }
