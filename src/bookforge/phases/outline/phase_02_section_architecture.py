from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .validators import ValidationResult, validate_phase_02


STEP_ID = "phase_02_section_architecture"


def preprocess(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    return payload, []


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    spine = handoffs.get("outline_spine_v1") if isinstance(handoffs.get("outline_spine_v1"), dict) else None
    return validate_phase_02(payload, spine)


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload
