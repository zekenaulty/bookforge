from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import ValidationResult, validate_phase_04c


STEP_ID = "phase_04c_metadata_relink"


def preprocess(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    wrapper = deepcopy(payload)
    outline = wrapper.get("outline") if isinstance(wrapper.get("outline"), dict) else {}
    wrapper["outline"] = outline
    return wrapper, []


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    sections = handoffs.get("outline_sections_v1") if isinstance(handoffs.get("outline_sections_v1"), dict) else None
    return validate_phase_04c(
        payload,
        sections_payload=sections,
        strict_transition_bridges=bool(settings.get("strict_transition_bridges", False)),
        runtime=runtime,
    )


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    outline = payload.get("outline") if isinstance(payload.get("outline"), dict) else {}
    return outline


def prompt_extras(runtime: Dict[str, Any]) -> Dict[str, Any]:
    window = runtime.get("phase04c_current_window") if isinstance(runtime.get("phase04c_current_window"), dict) else {}
    allowed_fields = (
        runtime.get("phase04c_allowed_fields")
        if isinstance(runtime.get("phase04c_allowed_fields"), dict)
        else {}
    )
    return {
        "phase_04c_window_json": window,
        "phase_04c_allowed_fields_json": allowed_fields,
    }
