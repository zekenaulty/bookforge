from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import (
    ValidationResult,
    compile_location_identity,
    validate_outline,
)


STEP_ID = "phase_03_scene_draft"


def preprocess(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    outline = deepcopy(payload)
    registry = runtime.get("location_registry") if isinstance(runtime.get("location_registry"), dict) else None
    compiled_registry, location_errors = compile_location_identity(outline=outline, registry=registry)
    runtime["location_registry"] = compiled_registry
    return outline, location_errors


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    sections = handoffs.get("outline_sections_v1") if isinstance(handoffs.get("outline_sections_v1"), dict) else None
    return validate_outline(
        payload,
        sections_payload=sections,
        strict_transition_bridges=bool(settings.get("strict_transition_bridges", False)),
        require_links=True,
    )


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload
