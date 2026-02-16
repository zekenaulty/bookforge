from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import (
    ValidationResult,
    compile_location_identity,
    issue,
    validate_phase_04b,
)


STEP_ID = "phase_04b_transition_execution"


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

    routing = runtime.get("phase04_routing") if isinstance(runtime.get("phase04_routing"), dict) else {}
    exact_conflicts = routing.get("exact_conflicts") if isinstance(routing.get("exact_conflicts"), list) else []
    if exact_conflicts:
        location_errors.append(
            issue(
                "exact_scene_count_transition_conflict",
                "Exact scene-count mode conflicts with required transition insertion.",
                path="phase_report.exact_scene_count_transition_conflict",
            )
        )
    return wrapper, location_errors


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    sections = handoffs.get("outline_sections_v1") if isinstance(handoffs.get("outline_sections_v1"), dict) else None
    selected = runtime.get("phase04_routing", {}).get("selected") if isinstance(runtime.get("phase04_routing"), dict) else []
    if not isinstance(selected, list):
        selected = []
    return validate_phase_04b(
        payload,
        sections_payload=sections,
        strict_transition_bridges=bool(settings.get("strict_transition_bridges", False)),
        selected_candidates=selected,
    )


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    outline = payload.get("outline") if isinstance(payload.get("outline"), dict) else {}
    return outline


def prompt_extras(runtime: Dict[str, Any]) -> Dict[str, Any]:
    routing = runtime.get("phase04_routing") if isinstance(runtime.get("phase04_routing"), dict) else {}
    return {
        "outline_phase_04a_output": runtime.get("outline_phase_04a_output", {}),
        "phase_04_selected_candidates_json": routing.get("selected", []),
        "phase_04_blocked_candidates_json": routing.get("blocked", []),
        "phase_04_policy_context_json": {
            "candidate_count": routing.get("candidate_count", 0),
            "exact_conflicts": routing.get("exact_conflicts", []),
        },
    }
