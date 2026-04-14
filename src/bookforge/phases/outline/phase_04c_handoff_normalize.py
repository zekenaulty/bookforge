from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import ValidationResult, validate_phase_04c_handoff


STEP_ID = "phase_04c_handoff_normalize"


def preprocess(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    return deepcopy(payload), []


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    sections = handoffs.get("outline_sections_v1") if isinstance(handoffs.get("outline_sections_v1"), dict) else None
    return validate_phase_04c_handoff(
        payload,
        sections_payload=sections,
        strict_transition_bridges=bool(settings.get("strict_transition_bridges", False)),
        runtime=runtime,
    )


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    outline = payload.get("outline") if isinstance(payload.get("outline"), dict) else {}
    return outline


def prompt_extras(runtime: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "phase_04c_handoff_fix_json": runtime.get("phase04c_handoff_targets", []),
        "phase_04c_handoff_allowed_jump_modes_json": runtime.get("phase04c_handoff_allowed_jump_modes", []),
    }
