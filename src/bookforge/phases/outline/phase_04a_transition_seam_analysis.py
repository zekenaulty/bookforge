from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import (
    ValidationResult,
    compile_location_identity,
    route_phase04_candidates,
    validate_phase_04a,
)


STEP_ID = "phase_04a_transition_seam_analysis"


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

    phase_report = wrapper.get("phase_report") if isinstance(wrapper.get("phase_report"), dict) else {}
    candidates = phase_report.get("candidate_seams") if isinstance(phase_report.get("candidate_seams"), list) else []
    routing = route_phase04_candidates(
        candidate_seams=candidates,
        exact_scene_count=bool(settings.get("exact_scene_count", False)),
        allow_transition_scene_insertions=bool(settings.get("allow_transition_scene_insertions", True)),
        transition_insert_budget_per_chapter=int(settings.get("transition_insert_budget_per_chapter", 2) or 2),
    )
    runtime["phase04_routing"] = routing
    return wrapper, location_errors


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    sections = handoffs.get("outline_sections_v1") if isinstance(handoffs.get("outline_sections_v1"), dict) else None
    return validate_phase_04a(
        payload,
        sections_payload=sections,
        strict_transition_bridges=bool(settings.get("strict_transition_bridges", False)),
    )


def handoff_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload


def prompt_extras(runtime: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "phase_04_selected_candidates_json": runtime.get("phase04_routing", {}).get("selected", []),
        "phase_04_blocked_candidates_json": runtime.get("phase04_routing", {}).get("blocked", []),
        "phase_04_policy_context_json": {
            "candidate_count": runtime.get("phase04_routing", {}).get("candidate_count", 0),
            "exact_conflicts": runtime.get("phase04_routing", {}).get("exact_conflicts", []),
        },
    }
