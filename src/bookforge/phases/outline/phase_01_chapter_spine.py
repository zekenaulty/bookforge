from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .validators import ValidationResult, validate_phase_01


STEP_ID = "phase_01_chapter_spine"


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
    return validate_phase_01(payload)


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload
