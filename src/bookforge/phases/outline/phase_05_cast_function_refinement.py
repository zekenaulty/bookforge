from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import (
    ValidationResult,
    compile_location_identity,
    validate_phase_05,
)


STEP_ID = "phase_05_cast_function_refinement"


def preprocess(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    wrapper = deepcopy(payload)
    outline = wrapper.get("outline") if isinstance(wrapper.get("outline"), dict) else {}
    registry = runtime.get("location_registry") if isinstance(runtime.get("location_registry"), dict) else None
    compiled_registry, location_errors = compile_location_identity(outline=outline, registry=registry)
    runtime["location_registry"] = compiled_registry
    wrapper["outline"] = outline
    return wrapper, location_errors


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    sections = handoffs.get("outline_sections_v1") if isinstance(handoffs.get("outline_sections_v1"), dict) else None
    return validate_phase_05(
        payload,
        sections_payload=sections,
        strict_transition_bridges=bool(settings.get("strict_transition_bridges", False)),
    )


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    outline = payload.get("outline") if isinstance(payload.get("outline"), dict) else {}
    return outline
