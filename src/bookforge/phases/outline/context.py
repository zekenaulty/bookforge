from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import re

from bookforge.util.paths import repo_root
from bookforge.util.schema import validate_json


PHASE_01 = "phase_01_chapter_spine"
PHASE_02 = "phase_02_section_architecture"
PHASE_03 = "phase_03_scene_draft"
PHASE_04 = "phase_04_transition_causality_refinement"
PHASE_05 = "phase_05_cast_function_refinement"
PHASE_06 = "phase_06_thread_payoff_refinement"

STEP_04A = "phase_04a_transition_seam_analysis"
STEP_04B = "phase_04b_transition_execution"
STEP_04C = "phase_04c_metadata_relink"
STEP_04C_INTRO = "phase_04c_intro_sync"
STEP_04C_HANDOFF = "phase_04c_handoff_normalize"
STEP_04D = "phase_04d_seam_hygiene"

LOGICAL_PHASE_ORDER: List[str] = [
    PHASE_01,
    PHASE_02,
    PHASE_03,
    PHASE_04,
    PHASE_05,
    PHASE_06,
]

STEP_ORDER: List[str] = [
    PHASE_01,
    PHASE_02,
    PHASE_03,
    STEP_04A,
    STEP_04B,
    STEP_04C,
    STEP_04C_INTRO,
    STEP_04C_HANDOFF,
    STEP_04D,
    PHASE_05,
    PHASE_06,
]

STEP_TO_LOGICAL: Dict[str, str] = {
    PHASE_01: PHASE_01,
    PHASE_02: PHASE_02,
    PHASE_03: PHASE_03,
    STEP_04A: PHASE_04,
    STEP_04B: PHASE_04,
    STEP_04C: PHASE_04,
    STEP_04C_INTRO: PHASE_04,
    STEP_04C_HANDOFF: PHASE_04,
    STEP_04D: PHASE_04,
    PHASE_05: PHASE_05,
    PHASE_06: PHASE_06,
}

LOGICAL_TO_STEPS: Dict[str, List[str]] = {
    PHASE_01: [PHASE_01],
    PHASE_02: [PHASE_02],
    PHASE_03: [PHASE_03],
    PHASE_04: [STEP_04A, STEP_04B, STEP_04C, STEP_04C_INTRO, STEP_04C_HANDOFF, STEP_04D],
    PHASE_05: [PHASE_05],
    PHASE_06: [PHASE_06],
}

HINT_REF_PATTERN = re.compile(r"^[1-9][0-9]*:[1-9][0-9]*$")


@dataclass(frozen=True)
class StepSpec:
    step_id: str
    logical_phase: str
    template_name: str
    handoff_key: str
    handoff_file: str
    output_schema: str


STEP_SPECS: Dict[str, StepSpec] = {
    PHASE_01: StepSpec(
        step_id=PHASE_01,
        logical_phase=PHASE_01,
        template_name="outline_phase_01_chapter_spine.md",
        handoff_key="outline_spine_v1",
        handoff_file="outline_spine_v1.json",
        output_schema="spine_v1",
    ),
    PHASE_02: StepSpec(
        step_id=PHASE_02,
        logical_phase=PHASE_02,
        template_name="outline_phase_02_section_architecture.md",
        handoff_key="outline_sections_v1",
        handoff_file="outline_sections_v1.json",
        output_schema="sections_v1",
    ),
    PHASE_03: StepSpec(
        step_id=PHASE_03,
        logical_phase=PHASE_03,
        template_name="outline_phase_03_scene_draft.md",
        handoff_key="outline_draft_v1_1",
        handoff_file="outline_draft_v1_1.json",
        output_schema="outline",
    ),
    STEP_04A: StepSpec(
        step_id=STEP_04A,
        logical_phase=PHASE_04,
        template_name="outline_phase_04a_transition_seam_analysis.md",
        handoff_key="outline_phase_04a_output",
        handoff_file="phase_04a_output.json",
        output_schema="transition_refine_v1",
    ),
    STEP_04B: StepSpec(
        step_id=STEP_04B,
        logical_phase=PHASE_04,
        template_name="outline_phase_04b_transition_execution.md",
        handoff_key="outline_transitions_refined_v1_1",
        handoff_file="outline_transitions_refined_v1_1.json",
        output_schema="transition_refine_v1",
    ),
    STEP_04C: StepSpec(
        step_id=STEP_04C,
        logical_phase=PHASE_04,
        template_name="outline_phase_04c_metadata_relink.md",
        handoff_key="outline_transitions_relinked_v1_1",
        handoff_file="outline_transitions_relinked_v1_1.json",
        output_schema="outline_relink_v1",
    ),
    STEP_04C_INTRO: StepSpec(
        step_id=STEP_04C_INTRO,
        logical_phase=PHASE_04,
        template_name="outline_phase_04c_intro_sync.md",
        handoff_key="outline_intro_synced_v1_1",
        handoff_file="outline_intro_synced_v1_1.json",
        output_schema="outline_intro_sync_v1",
    ),
    STEP_04C_HANDOFF: StepSpec(
        step_id=STEP_04C_HANDOFF,
        logical_phase=PHASE_04,
        template_name="outline_phase_04c_handoff_normalize.md",
        handoff_key="outline_handoff_normalized_v1_1",
        handoff_file="outline_handoff_normalized_v1_1.json",
        output_schema="outline_handoff_normalize_v1",
    ),
    STEP_04D: StepSpec(
        step_id=STEP_04D,
        logical_phase=PHASE_04,
        template_name="outline_phase_04d_seam_hygiene.md",
        handoff_key="outline_seams_hygiened_v1_1",
        handoff_file="outline_seams_hygiened_v1_1.json",
        output_schema="outline_seam_hygiene_v1",
    ),
    PHASE_05: StepSpec(
        step_id=PHASE_05,
        logical_phase=PHASE_05,
        template_name="outline_phase_05_cast_function_refinement.md",
        handoff_key="outline_cast_refined_v1_1",
        handoff_file="outline_cast_refined_v1_1.json",
        output_schema="cast_refine_v1",
    ),
    PHASE_06: StepSpec(
        step_id=PHASE_06,
        logical_phase=PHASE_06,
        template_name="outline_phase_06_thread_payoff_refinement.md",
        handoff_key="outline_final_v1_1",
        handoff_file="outline_final_v1_1.json",
        output_schema="outline",
    ),
}


def step_spec(step_id: str) -> StepSpec:
    spec = STEP_SPECS.get(step_id)
    if spec is None:
        raise ValueError(f"Unknown outline step: {step_id}")
    return spec


def normalize_phase_selector(
    *,
    from_phase: Optional[str],
    to_phase: Optional[str],
    single_phase: Optional[str],
) -> Tuple[str, str]:
    raw_from = (from_phase or "").strip()
    raw_to = (to_phase or "").strip()
    raw_single = (single_phase or "").strip()

    if raw_single:
        raw_from = raw_single
        raw_to = raw_single

    if not raw_from:
        raw_from = LOGICAL_PHASE_ORDER[0]
    if not raw_to:
        raw_to = LOGICAL_PHASE_ORDER[-1]

    if raw_from in STEP_SPECS:
        from_step = raw_from
    elif raw_from in LOGICAL_TO_STEPS:
        from_step = LOGICAL_TO_STEPS[raw_from][0]
    else:
        raise ValueError(f"Unknown --from-phase value: {raw_from}")

    if raw_to in STEP_SPECS:
        to_step = raw_to
    elif raw_to in LOGICAL_TO_STEPS:
        to_step = LOGICAL_TO_STEPS[raw_to][-1]
    else:
        raise ValueError(f"Unknown --to-phase value: {raw_to}")

    if STEP_ORDER.index(from_step) > STEP_ORDER.index(to_step):
        raise ValueError("--from-phase must not come after --to-phase")

    return from_step, to_step


def step_slice(from_step: str, to_step: str) -> List[str]:
    start = STEP_ORDER.index(from_step)
    end = STEP_ORDER.index(to_step)
    return STEP_ORDER[start : end + 1]


def resolve_outline_template(book_root: Path, template_name: str) -> Path:
    local_path = book_root / "prompts" / "templates" / template_name
    if local_path.exists():
        return local_path
    fallback = repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / template_name
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Missing outline template: {template_name}")


def read_transition_hints(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"hints": []}
    if not path.exists():
        raise FileNotFoundError(f"Transition hints file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid transition hints JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Transition hints payload must be a JSON object.")
    validate_json(payload, "outline_transition_hints")
    return payload


def build_scene_count_policy(
    *,
    exact_scene_count: bool,
    scene_count_range: Optional[str],
) -> Dict[str, Any]:
    mode = "exact" if exact_scene_count else "strong_non_exact"
    policy: Dict[str, Any] = {
        "mode": mode,
        "expected_scene_count_enforcement": "strict" if exact_scene_count else "strong_non_exact",
        "chapter_scene_count_exact_mode": exact_scene_count,
        "notes": [],
    }

    if scene_count_range:
        raw = scene_count_range.strip()
        parts = raw.split("-", 1)
        if len(parts) != 2:
            raise ValueError("--scene-count-range must be MIN-MAX")
        try:
            low = int(parts[0].strip())
            high = int(parts[1].strip())
        except ValueError as exc:
            raise ValueError("--scene-count-range must be MIN-MAX integers") from exc
        if low < 1 or high < low:
            raise ValueError("--scene-count-range must satisfy 1 <= MIN <= MAX")
        policy["range"] = {"min": low, "max": high}
        policy["notes"].append("When choosing within range, bias toward the higher end when plausible.")
    return policy


def base_prompt_values(
    *,
    book: Dict[str, Any],
    targets: Dict[str, Any],
    notes: str,
    user_prompt: str,
    transition_hints: Dict[str, Any],
    scene_count_policy: Dict[str, Any],
    handoffs: Dict[str, Any],
    extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    values: Dict[str, Any] = {
        "book": book,
        "targets": targets,
        "notes": notes,
        "user_prompt": user_prompt,
        "transition_hints": transition_hints,
        "scene_count_policy": scene_count_policy,
    }
    values.update(handoffs)
    if extras:
        values.update(extras)
    return values
