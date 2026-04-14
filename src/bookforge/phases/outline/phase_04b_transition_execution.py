from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import (
    ValidationResult,
    compile_location_identity,
    derive_phase04c_windows,
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

    phase_report = wrapper.get("phase_report") if isinstance(wrapper.get("phase_report"), dict) else {}
    impacts = (
        phase_report.get("insertion_edge_impacts")
        if isinstance(phase_report.get("insertion_edge_impacts"), list)
        else []
    )
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    if chapters and isinstance(chapters[0], dict):
        chapter_id = str(chapters[0].get("chapter_id") or "").strip()
        if chapter_id:
            windows = derive_phase04c_windows(chapter=chapters[0], insertion_impacts=impacts)
            runtime.setdefault("phase04c_windows_by_chapter", {})
            runtime["phase04c_windows_by_chapter"][chapter_id] = windows
            runtime.setdefault("phase04_insertion_impacts_by_chapter", {})
            runtime["phase04_insertion_impacts_by_chapter"][chapter_id] = impacts

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
    current = runtime.get("phase04_current_routing")
    if isinstance(current, dict):
        routing = current
    else:
        routing = runtime.get("phase04_routing") if isinstance(runtime.get("phase04_routing"), dict) else {}
    selected = routing.get("selected") if isinstance(routing, dict) else []
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
    current = runtime.get("phase04_current_routing")
    if isinstance(current, dict):
        routing = current
    else:
        routing = runtime.get("phase04_routing") if isinstance(runtime.get("phase04_routing"), dict) else {}
    selected = routing.get("selected", []) if isinstance(routing.get("selected"), list) else []
    selected_insertions = [
        item
        for item in selected
        if isinstance(item, dict)
        and str(item.get("requested_resolution") or "").strip() in {"micro_scene", "full_scene"}
    ]
    return {
        "outline_phase_04a_output": runtime.get("outline_phase_04a_output", {}),
        "phase_04_selected_candidates_json": selected,
        "phase_04_selected_insertions_json": selected_insertions,
        "phase_04_blocked_candidates_json": routing.get("blocked", []),
        "phase_04_policy_context_json": {
            "candidate_count": routing.get("candidate_count", 0),
            "exact_conflicts": routing.get("exact_conflicts", []),
        },
    }
