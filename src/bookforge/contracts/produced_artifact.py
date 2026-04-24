from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .vocabulary import is_valid_produced_artifact_status


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
class ProducedArtifactReceipt:
    artifact_key: str
    label: str
    artifact_status: str
    path: str
    format: Optional[str] = None
    consumable: bool = False
    resumable: bool = False
    replaceable: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "produced_artifact_v1"

    def __post_init__(self) -> None:
        artifact_key = _clean_required(self.artifact_key, "artifact_key")
        label = _clean_required(self.label, "label")
        artifact_status = _clean_required(self.artifact_status, "artifact_status")
        if not is_valid_produced_artifact_status(artifact_status):
            raise ValueError(f"Unknown produced artifact status: {artifact_status}")
        path = _clean_required(self.path, "path")
        object.__setattr__(self, "artifact_key", artifact_key)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "artifact_status", artifact_status)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "format", _clean_optional(self.format))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_key": self.artifact_key,
            "label": self.label,
            "artifact_status": self.artifact_status,
            "path": self.path,
            "format": self.format,
            "consumable": bool(self.consumable),
            "resumable": bool(self.resumable),
            "replaceable": bool(self.replaceable),
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ProducedArtifactReceipt":
        if not isinstance(payload, dict):
            raise ValueError("ProducedArtifactReceipt payload must be a dictionary.")
        return cls(
            artifact_key=payload.get("artifact_key"),
            label=payload.get("label"),
            artifact_status=payload.get("artifact_status"),
            path=payload.get("path"),
            format=payload.get("format"),
            consumable=bool(payload.get("consumable")),
            resumable=bool(payload.get("resumable")),
            replaceable=bool(payload.get("replaceable")),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "produced_artifact_v1"),
        )
