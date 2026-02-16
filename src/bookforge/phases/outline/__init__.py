from __future__ import annotations

from typing import Any, Dict

from . import phase_01_chapter_spine
from . import phase_02_section_architecture
from . import phase_03_scene_draft
from . import phase_04a_transition_seam_analysis
from . import phase_04b_transition_execution
from . import phase_05_cast_function_refinement
from . import phase_06_thread_payoff_refinement


HANDLERS = {
    "phase_01_chapter_spine": phase_01_chapter_spine,
    "phase_02_section_architecture": phase_02_section_architecture,
    "phase_03_scene_draft": phase_03_scene_draft,
    "phase_04a_transition_seam_analysis": phase_04a_transition_seam_analysis,
    "phase_04b_transition_execution": phase_04b_transition_execution,
    "phase_05_cast_function_refinement": phase_05_cast_function_refinement,
    "phase_06_thread_payoff_refinement": phase_06_thread_payoff_refinement,
}


def get_handler(step_id: str):
    handler = HANDLERS.get(step_id)
    if handler is None:
        raise ValueError(f"Unknown outline step handler: {step_id}")
    return handler


def step_runtime_defaults() -> Dict[str, Any]:
    return {
        "location_registry": {"schema_version": "location_registry_v1", "locations": []},
        "phase04_routing": {
            "candidate_count": 0,
            "selected": [],
            "blocked": [],
            "exact_conflicts": [],
        },
    }
