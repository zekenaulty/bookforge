from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import re

from bookforge.util.schema import validate_json


REF_PATTERN = re.compile(r"^[1-9][0-9]*:[1-9][0-9]*$")
LOCATION_ID_PATTERN = re.compile(r"^LOC_[A-Z0-9_]+$")
PLACEHOLDER_PATTERN = re.compile(
    r"\b(current_location|unknown|placeholder|tbd|here|there|n/?a)\b",
    re.IGNORECASE,
)
META_TRANSITION_PATTERN = re.compile(
    r"\b(this beat|realized on page|movement from|action resumes at)\b",
    re.IGNORECASE,
)
MACHINE_ANCHOR_PATTERN = re.compile(r"^(loc_|LOC_|CHAR_|THREAD_)")

HANDOFF_MODE_ENUM = {
    "direct_continuation",
    "escorted_transfer",
    "detained_then_release",
    "time_skip",
    "hard_cut",
    "montage",
    "offscreen_processing",
    "combat_disengage",
    "arrival_checkpoint",
    "aftermath_relocation",
}

CONSTRAINT_STATE_ENUM = {
    "free",
    "pursued",
    "detained",
    "processed",
    "sheltered",
    "restricted",
    "engaged_combat",
    "fleeing",
}

SEAM_RESOLUTION_ENUM = {"inline_bridge", "micro_scene", "full_scene"}


@dataclass
class ValidationResult:
    status: str
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    metrics: Dict[str, Any]


def issue(
    code: str,
    message: str,
    *,
    path: Optional[str] = None,
    scene_ref: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"code": code, "message": message}
    if path:
        payload["path"] = path
    if scene_ref:
        payload["scene_ref"] = scene_ref
    return payload


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _norm_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.search(value))


def _is_meta(value: str) -> bool:
    return bool(META_TRANSITION_PATTERN.search(value))


def _is_machine_anchor(value: str) -> bool:
    token = value.strip()
    return (
        bool(MACHINE_ANCHOR_PATTERN.match(token))
        or token.isupper()
        or token.startswith("loc_")
    )


def _section_end_lookup(sections_payload: Dict[str, Any]) -> Dict[Tuple[int, int], str]:
    lookup: Dict[Tuple[int, int], str] = {}
    chapters = (
        sections_payload.get("chapters")
        if isinstance(sections_payload.get("chapters"), list)
        else []
    )
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_id = _to_int(section.get("section_id"))
            end_condition = _norm_text(section.get("end_condition"))
            if chapter_id and section_id and end_condition:
                lookup[(chapter_id, section_id)] = end_condition
    return lookup


def validate_phase_01(payload: Dict[str, Any]) -> ValidationResult:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    if _norm_text(payload.get("schema_version")) != "spine_v1":
        errors.append(
            issue(
                "schema_version",
                "phase 01 schema_version must be spine_v1",
                path="schema_version",
            )
        )

    chapters = payload.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        errors.append(
            issue(
                "chapters_required",
                "phase 01 requires non-empty chapters array",
                path="chapters",
            )
        )
        return ValidationResult("fail", errors, warnings, metrics)

    for index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            errors.append(
                issue(
                    "chapter_type",
                    "chapter must be object",
                    path=f"chapters[{index-1}]",
                )
            )
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id != index:
            errors.append(
                issue(
                    "chapter_id_sequential",
                    f"chapter_id must be {index}",
                    path=f"chapters[{index-1}].chapter_id",
                )
            )
        for key in ("title", "goal", "chapter_role", "stakes_shift"):
            if not _norm_text(chapter.get(key)):
                errors.append(
                    issue(
                        "chapter_field_required",
                        f"{key} is required",
                        path=f"chapters[{index-1}].{key}",
                    )
                )
        bridge = chapter.get("bridge")
        if not isinstance(bridge, dict):
            errors.append(
                issue(
                    "bridge_required",
                    "bridge is required",
                    path=f"chapters[{index-1}].bridge",
                )
            )
        else:
            if "from_prev" not in bridge or "to_next" not in bridge:
                errors.append(
                    issue(
                        "bridge_keys",
                        "bridge must include from_prev and to_next",
                        path=f"chapters[{index-1}].bridge",
                    )
                )
        pacing = chapter.get("pacing")
        if not isinstance(pacing, dict):
            errors.append(
                issue(
                    "pacing_required",
                    "pacing is required",
                    path=f"chapters[{index-1}].pacing",
                )
            )
        else:
            if _to_int(pacing.get("expected_scene_count")) is None:
                errors.append(
                    issue(
                        "expected_scene_count_required",
                        "pacing.expected_scene_count must be integer",
                        path=f"chapters[{index-1}].pacing.expected_scene_count",
                    )
                )

    status = "pass" if not errors else "fail"
    metrics["chapter_count"] = len(chapters)
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_02(
    payload: Dict[str, Any],
    spine_payload: Optional[Dict[str, Any]],
) -> ValidationResult:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    if _norm_text(payload.get("schema_version")) != "sections_v1":
        errors.append(
            issue(
                "schema_version",
                "phase 02 schema_version must be sections_v1",
                path="schema_version",
            )
        )

    chapters = payload.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        errors.append(
            issue(
                "chapters_required",
                "phase 02 requires non-empty chapters array",
                path="chapters",
            )
        )
        return ValidationResult("fail", errors, warnings, metrics)

    expected_chapters: Set[int] = set()
    if isinstance(spine_payload, dict):
        spine_chapters = (
            spine_payload.get("chapters")
            if isinstance(spine_payload.get("chapters"), list)
            else []
        )
        expected_chapters = {
            int(item.get("chapter_id"))
            for item in spine_chapters
            if isinstance(item, dict) and _to_int(item.get("chapter_id"))
        }

    seen_chapters: Set[int] = set()
    for chapter_index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            errors.append(
                issue(
                    "chapter_type",
                    "chapter must be object",
                    path=f"chapters[{chapter_index-1}]",
                )
            )
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id != chapter_index:
            errors.append(
                issue(
                    "chapter_id_sequential",
                    f"chapter_id must be {chapter_index}",
                    path=f"chapters[{chapter_index-1}].chapter_id",
                )
            )
            continue
        seen_chapters.add(chapter_id)

        sections = chapter.get("sections")
        if not isinstance(sections, list) or not sections:
            errors.append(
                issue(
                    "sections_required",
                    "chapter.sections must be non-empty array",
                    path=f"chapters[{chapter_index-1}].sections",
                )
            )
            continue
        for section_index, section in enumerate(sections, start=1):
            if not isinstance(section, dict):
                errors.append(
                    issue(
                        "section_type",
                        "section must be object",
                        path=f"chapters[{chapter_index-1}].sections[{section_index-1}]",
                    )
                )
                continue
            section_id = _to_int(section.get("section_id"))
            if section_id != section_index:
                errors.append(
                    issue(
                        "section_id_sequential",
                        f"section_id must be {section_index}",
                        path=f"chapters[{chapter_index-1}].sections[{section_index-1}].section_id",
                    )
                )
            for key in ("title", "intent", "end_condition"):
                if not _norm_text(section.get(key)):
                    errors.append(
                        issue(
                            "section_field_required",
                            f"{key} is required",
                            path=f"chapters[{chapter_index-1}].sections[{section_index-1}].{key}",
                        )
                    )
            if _to_int(section.get("target_scene_count")) is None:
                errors.append(
                    issue(
                        "target_scene_count_required",
                        "target_scene_count must be integer",
                        path=f"chapters[{chapter_index-1}].sections[{section_index-1}].target_scene_count",
                    )
                )

    if expected_chapters and expected_chapters != seen_chapters:
        errors.append(
            issue(
                "chapter_set_mismatch",
                "phase 02 must include exactly phase 01 chapter ids",
                path="chapters",
            )
        )

    status = "pass" if not errors else "fail"
    metrics["chapter_count"] = len(chapters)
    return ValidationResult(status, errors, warnings, metrics)

def _validate_scene_transition_fields(
    *,
    scene: Dict[str, Any],
    scene_ref: str,
    is_first: bool,
    is_last: bool,
    strict_transition_bridges: bool,
    require_links: bool,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # Keep legacy location_start/location_end populated when labels are present.
    # This is deterministic alias normalization, not semantic autofill.
    for prefix in ("location_start", "location_end"):
        if not _norm_text(scene.get(prefix)):
            label = _norm_text(scene.get(f"{prefix}_label"))
            if label:
                scene[prefix] = label

    required_common = [
        "location_start_label",
        "location_end_label",
        "location_start",
        "location_end",
        "handoff_mode",
        "constraint_state",
        "transition_in_text",
        "transition_in_anchors",
    ]
    for field in required_common:
        value = scene.get(field)
        if field.endswith("_anchors"):
            anchors = _norm_list(value)
            if len(anchors) < 3 or len(anchors) > 6:
                errors.append(
                    issue(
                        "transition_anchor_count",
                        f"{field} must contain 3-6 anchors",
                        scene_ref=scene_ref,
                    )
                )
            else:
                if any(_is_placeholder(item) for item in anchors):
                    errors.append(
                        issue(
                            "transition_placeholder",
                            f"{field} must not contain placeholders",
                            scene_ref=scene_ref,
                        )
                    )
                if any(_is_machine_anchor(item) for item in anchors):
                    errors.append(
                        issue(
                            "transition_fields_invalid",
                            f"{field} contains machine/id-like tokens",
                            scene_ref=scene_ref,
                        )
                    )
            continue
        text = _norm_text(value)
        if not text:
            errors.append(
                issue(
                    "transition_field_required",
                    f"{field} is required",
                    scene_ref=scene_ref,
                )
            )
            continue
        if _is_placeholder(text):
            errors.append(
                issue(
                    "transition_placeholder",
                    f"{field} contains placeholder token",
                    scene_ref=scene_ref,
                )
            )
        if "transition" in field and _is_meta(text):
            errors.append(
                issue(
                    "transition_fields_invalid",
                    f"{field} contains meta/fallback phrasing",
                    scene_ref=scene_ref,
                )
            )

    handoff_mode = _norm_text(scene.get("handoff_mode"))
    constraint_state = _norm_text(scene.get("constraint_state"))
    if handoff_mode and handoff_mode not in HANDOFF_MODE_ENUM:
        errors.append(
            issue(
                "handoff_mode_enum",
                f"Invalid handoff_mode {handoff_mode}",
                scene_ref=scene_ref,
            )
        )
    if constraint_state and constraint_state not in CONSTRAINT_STATE_ENUM:
        errors.append(
            issue(
                "constraint_state_enum",
                f"Invalid constraint_state {constraint_state}",
                scene_ref=scene_ref,
            )
        )
    if strict_transition_bridges and handoff_mode == "hard_cut":
        errors.append(
            issue(
                "hard_cut_disallowed",
                "hard_cut is disallowed in strict transition bridge mode",
                scene_ref=scene_ref,
            )
        )

    if require_links and not is_first:
        value = _norm_text(scene.get("consumes_outcome_from"))
        if not value or not REF_PATTERN.fullmatch(value):
            errors.append(
                issue(
                    "consumes_required",
                    "consumes_outcome_from is required in chapter:scene format",
                    scene_ref=scene_ref,
                )
            )

    if not is_last:
        out_text = _norm_text(scene.get("transition_out_text"))
        if not out_text:
            errors.append(
                issue(
                    "transition_out_required",
                    "transition_out_text is required for non-last scenes",
                    scene_ref=scene_ref,
                )
            )
        else:
            if _is_placeholder(out_text):
                errors.append(
                    issue(
                        "transition_placeholder",
                        "transition_out_text contains placeholder token",
                        scene_ref=scene_ref,
                    )
                )
            if _is_meta(out_text):
                errors.append(
                    issue(
                        "transition_fields_invalid",
                        "transition_out_text contains meta/fallback phrasing",
                        scene_ref=scene_ref,
                    )
                )

        out_anchors = _norm_list(scene.get("transition_out_anchors"))
        if len(out_anchors) < 3 or len(out_anchors) > 6:
            errors.append(
                issue(
                    "transition_out_anchor_count",
                    "transition_out_anchors must contain 3-6 anchors",
                    scene_ref=scene_ref,
                )
            )
        else:
            if any(_is_placeholder(item) for item in out_anchors):
                errors.append(
                    issue(
                        "transition_placeholder",
                        "transition_out_anchors contain placeholders",
                        scene_ref=scene_ref,
                    )
                )
            if any(_is_machine_anchor(item) for item in out_anchors):
                errors.append(
                    issue(
                        "transition_fields_invalid",
                        "transition_out_anchors contain machine/id-like tokens",
                        scene_ref=scene_ref,
                    )
                )

        if require_links:
            hands = _norm_text(scene.get("hands_off_to"))
            if not hands or not REF_PATTERN.fullmatch(hands):
                errors.append(
                    issue(
                        "hands_required",
                        "hands_off_to is required in chapter:scene format",
                        scene_ref=scene_ref,
                    )
                )

    seam_score = scene.get("seam_score")
    if seam_score is not None:
        number = _to_int(seam_score)
        if number is None or number < 0 or number > 100:
            errors.append(
                issue(
                    "seam_score_range",
                    "seam_score must be integer 0-100",
                    scene_ref=scene_ref,
                )
            )
    seam_resolution = _norm_text(scene.get("seam_resolution"))
    if seam_resolution and seam_resolution not in SEAM_RESOLUTION_ENUM:
        errors.append(
            issue(
                "seam_resolution_enum",
                "seam_resolution must be inline_bridge|micro_scene|full_scene",
                scene_ref=scene_ref,
            )
        )

    return errors, warnings


def validate_outline(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]] = None,
    strict_transition_bridges: bool = False,
    require_links: bool = False,
) -> ValidationResult:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    try:
        validate_json(payload, "outline")
    except Exception as exc:
        errors.append(issue("outline_schema", str(exc), path="<root>"))
        return ValidationResult("fail", errors, warnings, metrics)

    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    if not chapters:
        errors.append(
            issue(
                "chapters_required",
                "outline.chapters must be non-empty",
                path="chapters",
            )
        )
        return ValidationResult("fail", errors, warnings, metrics)

    section_end_lookup = _section_end_lookup(sections_payload or {})

    for chapter_index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            errors.append(
                issue(
                    "chapter_type",
                    "chapter must be object",
                    path=f"chapters[{chapter_index-1}]",
                )
            )
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id != chapter_index:
            errors.append(
                issue(
                    "chapter_id_sequential",
                    f"chapter_id must be {chapter_index}",
                    path=f"chapters[{chapter_index-1}].chapter_id",
                )
            )
            continue

        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        if not sections:
            errors.append(
                issue(
                    "sections_required",
                    "chapter.sections must be non-empty",
                    path=f"chapters[{chapter_index-1}].sections",
                )
            )
            continue

        flattened: List[Tuple[int, int, Dict[str, Any]]] = []
        for section_index, section in enumerate(sections, start=1):
            if not isinstance(section, dict):
                errors.append(
                    issue(
                        "section_type",
                        "section must be object",
                        path=f"chapters[{chapter_index-1}].sections[{section_index-1}]",
                    )
                )
                continue
            section_id = _to_int(section.get("section_id"))
            if section_id != section_index:
                errors.append(
                    issue(
                        "section_id_sequential",
                        f"section_id must be {section_index}",
                        path=f"chapters[{chapter_index-1}].sections[{section_index-1}].section_id",
                    )
                )
                continue
            end_condition = _norm_text(section.get("end_condition"))
            if not end_condition:
                errors.append(
                    issue(
                        "end_condition_required",
                        "section.end_condition is required",
                        path=f"chapters[{chapter_index-1}].sections[{section_index-1}].end_condition",
                    )
                )

            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            if not scenes:
                errors.append(
                    issue(
                        "scenes_required",
                        "section.scenes must be non-empty",
                        path=f"chapters[{chapter_index-1}].sections[{section_index-1}].scenes",
                    )
                )
                continue
            for scene_index, scene in enumerate(scenes, start=1):
                if not isinstance(scene, dict):
                    errors.append(
                        issue(
                            "scene_type",
                            "scene must be object",
                            path=f"chapters[{chapter_index-1}].sections[{section_index-1}].scenes[{scene_index-1}]",
                        )
                    )
                    continue
                flattened.append((section_id, scene_index, scene))

        for expected_scene_id, (section_id, scene_index, scene) in enumerate(flattened, start=1):
            actual_scene_id = _to_int(scene.get("scene_id"))
            if actual_scene_id != expected_scene_id:
                errors.append(
                    issue(
                        "scene_id_monotonic",
                        f"scene_id must be chapter-local monotonic; expected {expected_scene_id}",
                        scene_ref=f"{chapter_id}:{actual_scene_id or expected_scene_id}",
                    )
                )

        for flat_index, (section_id, scene_index, scene) in enumerate(flattened):
            scene_id = _to_int(scene.get("scene_id")) or (flat_index + 1)
            scene_ref = f"{chapter_id}:{scene_id}"
            is_first = flat_index == 0
            is_last = flat_index == len(flattened) - 1

            scene_errors, scene_warnings = _validate_scene_transition_fields(
                scene=scene,
                scene_ref=scene_ref,
                is_first=is_first,
                is_last=is_last,
                strict_transition_bridges=strict_transition_bridges,
                require_links=require_links,
            )
            errors.extend(scene_errors)
            warnings.extend(scene_warnings)

            expected_end = section_end_lookup.get((chapter_id, section_id))
            if expected_end:
                section_scenes = [item for item in flattened if item[0] == section_id]
                is_section_final = bool(section_scenes and section_scenes[-1][2] is scene)
                if is_section_final:
                    echo = _norm_text(scene.get("end_condition_echo"))
                    if not echo:
                        errors.append(
                            issue(
                                "end_condition_echo_required",
                                "section-final scene must include end_condition_echo",
                                scene_ref=scene_ref,
                            )
                        )
                    elif echo.casefold() != expected_end.casefold():
                        errors.append(
                            issue(
                                "end_condition_echo_mismatch",
                                "end_condition_echo must match section end_condition",
                                scene_ref=scene_ref,
                            )
                        )

    metrics["chapter_count"] = len(chapters)
    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)

def _validate_wrapper(
    payload: Dict[str, Any],
    schema_version: str,
    report_key: str,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    errors: List[Dict[str, Any]] = []
    if _norm_text(payload.get("schema_version")) != schema_version:
        errors.append(
            issue(
                "schema_version",
                f"wrapper schema_version must be {schema_version}",
                path="schema_version",
            )
        )
        return None, errors
    outline = payload.get("outline")
    if not isinstance(outline, dict):
        errors.append(
            issue(
                "outline_required",
                "wrapper must include outline object",
                path="outline",
            )
        )
        return None, errors
    report = payload.get(report_key)
    if not isinstance(report, dict):
        errors.append(
            issue(
                "report_required",
                f"wrapper must include {report_key} object",
                path=report_key,
            )
        )
    return outline, errors


def validate_phase_04a(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
) -> ValidationResult:
    wrapper_outline, wrapper_errors = _validate_wrapper(
        payload, "transition_refine_v1", "phase_report"
    )
    errors = list(wrapper_errors)
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    if wrapper_outline is None:
        return ValidationResult("fail", errors, warnings, metrics)

    base = validate_outline(
        wrapper_outline,
        sections_payload=sections_payload,
        strict_transition_bridges=strict_transition_bridges,
        require_links=True,
    )
    errors.extend(base.errors)
    warnings.extend(base.warnings)
    metrics.update(base.metrics)

    phase_report = (
        payload.get("phase_report") if isinstance(payload.get("phase_report"), dict) else {}
    )
    candidates = phase_report.get("candidate_seams")
    if candidates is not None:
        if not isinstance(candidates, list):
            errors.append(
                issue(
                    "candidate_seams_type",
                    "phase_report.candidate_seams must be array",
                    path="phase_report.candidate_seams",
                )
            )
        else:
            for idx, item in enumerate(candidates):
                if not isinstance(item, dict):
                    errors.append(
                        issue(
                            "candidate_seam_type",
                            "candidate seam must be object",
                            path=f"phase_report.candidate_seams[{idx}]",
                        )
                    )
                    continue
                from_ref = _norm_text(item.get("from_scene_ref"))
                to_ref = _norm_text(item.get("to_scene_ref"))
                if not REF_PATTERN.fullmatch(from_ref):
                    errors.append(
                        issue(
                            "candidate_scene_ref",
                            "from_scene_ref must be chapter:scene",
                            path=f"phase_report.candidate_seams[{idx}].from_scene_ref",
                        )
                    )
                if not REF_PATTERN.fullmatch(to_ref):
                    errors.append(
                        issue(
                            "candidate_scene_ref",
                            "to_scene_ref must be chapter:scene",
                            path=f"phase_report.candidate_seams[{idx}].to_scene_ref",
                        )
                    )
                score = _to_int(item.get("seam_score"))
                if score is None or score < 0 or score > 100:
                    errors.append(
                        issue(
                            "candidate_seam_score",
                            "seam_score must be integer 0-100",
                            path=f"phase_report.candidate_seams[{idx}].seam_score",
                        )
                    )
                resolution = _norm_text(item.get("requested_resolution"))
                if resolution not in SEAM_RESOLUTION_ENUM:
                    errors.append(
                        issue(
                            "candidate_resolution",
                            "requested_resolution must be inline_bridge|micro_scene|full_scene",
                            path=f"phase_report.candidate_seams[{idx}].requested_resolution",
                        )
                    )

    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_04b(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
    selected_candidates: List[Dict[str, Any]],
) -> ValidationResult:
    wrapper_outline, wrapper_errors = _validate_wrapper(
        payload, "transition_refine_v1", "phase_report"
    )
    errors = list(wrapper_errors)
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    if wrapper_outline is None:
        return ValidationResult("fail", errors, warnings, metrics)

    base = validate_outline(
        wrapper_outline,
        sections_payload=sections_payload,
        strict_transition_bridges=strict_transition_bridges,
        require_links=True,
    )
    errors.extend(base.errors)
    warnings.extend(base.warnings)
    metrics.update(base.metrics)

    selected_insertions: List[Dict[str, str]] = []
    selected_keys: set[str] = set()
    for item in selected_candidates:
        if not isinstance(item, dict):
            continue
        requested = _norm_text(item.get("requested_resolution"))
        if requested not in {"micro_scene", "full_scene"}:
            continue
        from_ref = _norm_text(item.get("from_scene_ref"))
        to_ref = _norm_text(item.get("to_scene_ref"))
        if not from_ref or not to_ref:
            continue
        key = f"{from_ref}->{to_ref}->{requested}"
        if key in selected_keys:
            continue
        selected_keys.add(key)
        selected_insertions.append(
            {
                "from_scene_ref": from_ref,
                "to_scene_ref": to_ref,
                "requested_resolution": requested,
            }
        )

    phase_report = (
        payload.get("phase_report") if isinstance(payload.get("phase_report"), dict) else {}
    )
    downgraded = (
        phase_report.get("downgraded_resolution")
        if isinstance(phase_report.get("downgraded_resolution"), list)
        else []
    )
    if downgraded:
        errors.append(
            issue(
                "transition_downgrade_forbidden",
                "downgraded_resolution must be empty; selected insertion downgrades are forbidden",
                path="phase_report.downgraded_resolution",
            )
        )

    inserted_scene_refs = (
        phase_report.get("inserted_scene_refs")
        if isinstance(phase_report.get("inserted_scene_refs"), list)
        else []
    )
    inserted_ref_set = {
        _norm_text(item) for item in inserted_scene_refs if _norm_text(item)
    }

    resolved = (
        phase_report.get("resolved_candidates")
        if isinstance(phase_report.get("resolved_candidates"), list)
        else []
    )
    resolved_items: List[Dict[str, Any]] = []
    for idx, item in enumerate(resolved):
        if not isinstance(item, dict):
            continue
        from_ref = _norm_text(item.get("from_scene_ref"))
        to_ref = _norm_text(item.get("to_scene_ref"))
        if not from_ref or not to_ref:
            continue
        resolved_items.append(
            {
                "idx": idx,
                "item": item,
                "from_scene_ref": from_ref,
                "to_scene_ref": to_ref,
                "requested_resolution": _norm_text(item.get("requested_resolution")),
                "resolution": _norm_text(item.get("resolution")),
                "inserted_scene_ref": _norm_text(item.get("inserted_scene_ref")),
            }
        )

    required_inserted_refs: set[str] = set()
    unresolved_selected: List[str] = []
    for selected in selected_insertions:
        selected_from_ref = selected["from_scene_ref"]
        selected_to_ref = selected["to_scene_ref"]
        expected_resolution = selected["requested_resolution"]

        matched: Optional[Dict[str, Any]] = None
        for resolved_item in resolved_items:
            if resolved_item["from_scene_ref"] != selected_from_ref:
                continue
            if resolved_item["requested_resolution"] != expected_resolution:
                continue
            if resolved_item["resolution"] != expected_resolution:
                continue
            # Allow to_scene_ref drift after insertion renumbering if inserted_scene_ref
            # captures the selected edge destination.
            if (
                resolved_item["to_scene_ref"] == selected_to_ref
                or resolved_item["inserted_scene_ref"] == selected_to_ref
            ):
                matched = resolved_item
                break

        if matched is None:
            unresolved_selected.append(f"{selected_from_ref}->{selected_to_ref}")
            continue

        idx = int(matched["idx"])
        item = matched["item"]
        item_requested = _norm_text(item.get("requested_resolution"))
        if item_requested != expected_resolution:
            errors.append(
                issue(
                    "transition_insertion_resolution_mismatch",
                    f"resolved_candidates[{idx}] requested_resolution must be {expected_resolution}",
                    path=f"phase_report.resolved_candidates[{idx}].requested_resolution",
                )
            )
        item_resolution = _norm_text(item.get("resolution"))
        if item_resolution != expected_resolution:
            errors.append(
                issue(
                    "transition_insertion_resolution_mismatch",
                    f"resolved_candidates[{idx}] resolution must be {expected_resolution}",
                    path=f"phase_report.resolved_candidates[{idx}].resolution",
                )
            )
        inserted_ref = _norm_text(item.get("inserted_scene_ref"))
        if not inserted_ref:
            errors.append(
                issue(
                    "transition_insertion_missing_scene_ref",
                    "resolved insertion candidate must provide inserted_scene_ref",
                    path=f"phase_report.resolved_candidates[{idx}].inserted_scene_ref",
                )
            )
        else:
            required_inserted_refs.add(inserted_ref)

    if unresolved_selected:
        errors.append(
            issue(
                "transition_insertion_required",
                "Selected insertion candidates were not resolved by LLM output",
                path="phase_report.resolved_candidates",
            )
        )

    missing_inserted_refs = sorted(required_inserted_refs - inserted_ref_set)
    if missing_inserted_refs:
        errors.append(
            issue(
                "transition_insertion_missing_scene_ref",
                "phase_report.inserted_scene_refs must include every resolved inserted_scene_ref",
                path="phase_report.inserted_scene_refs",
            )
        )

    unresolved_required = phase_report.get("unresolved_required_insertions")
    if isinstance(unresolved_required, list) and unresolved_required:
        errors.append(
            issue(
                "phase04b_required_insertion_unresolved",
                "phase_report lists unresolved required insertions",
                path="phase_report.unresolved_required_insertions",
            )
        )

    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_05(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
) -> ValidationResult:
    wrapper_outline, wrapper_errors = _validate_wrapper(payload, "cast_refine_v1", "cast_report")
    errors = list(wrapper_errors)
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    if wrapper_outline is None:
        return ValidationResult("fail", errors, warnings, metrics)

    base = validate_outline(
        wrapper_outline,
        sections_payload=sections_payload,
        strict_transition_bridges=strict_transition_bridges,
        require_links=True,
    )
    errors.extend(base.errors)
    warnings.extend(base.warnings)
    metrics.update(base.metrics)
    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_06(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
) -> ValidationResult:
    return validate_outline(
        payload,
        sections_payload=sections_payload,
        strict_transition_bridges=strict_transition_bridges,
        require_links=True,
    )


def parse_error_v1(payload: Dict[str, Any], step_id: str) -> ValidationResult:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}
    try:
        validate_json(payload, "error_v1")
    except Exception as exc:
        errors.append(issue("error_v1_schema", str(exc), path="<root>"))
        return ValidationResult("fail", errors, warnings, metrics)

    reason = _norm_text(payload.get("reason_code")) or "error_v1"
    errors.append(issue(reason, f"{step_id} returned error_v1", path="<root>"))
    return ValidationResult("fail", errors, warnings, metrics)


def normalize_outline_for_write(payload: Dict[str, Any]) -> Dict[str, Any]:
    outline = deepcopy(payload)
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                if "transition_in" in scene and "transition_in_text" not in scene:
                    scene["transition_in_text"] = scene.get("transition_in")
                if "transition_out" in scene and "transition_out_text" not in scene:
                    scene["transition_out_text"] = scene.get("transition_out")
    return outline

def _stable_location_id(label: str) -> str:
    base = re.sub(r"[^A-Z0-9]+", "_", label.upper()).strip("_")
    base = base or "LOCATION"
    digest = hashlib.sha1(label.strip().lower().encode("utf-8")).hexdigest().upper()[:6]
    return f"LOC_{base}_{digest}"


def compile_location_identity(
    *,
    outline: Dict[str, Any],
    registry: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if registry is None or not isinstance(registry, dict):
        registry = {"schema_version": "location_registry_v1", "locations": []}

    errors: List[Dict[str, Any]] = []
    entries = registry.get("locations") if isinstance(registry.get("locations"), list) else []
    by_label: Dict[str, Dict[str, Any]] = {}
    by_id: Dict[str, Dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        loc_id = _norm_text(item.get("location_id"))
        name = _norm_text(item.get("display_name"))
        if loc_id and name:
            by_id[loc_id] = item
            by_label[name.casefold()] = item

    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id")) or 0
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_id = _to_int(scene.get("scene_id")) or 0
                scene_ref = f"{chapter_id}:{scene_id}" if chapter_id and scene_id else None
                for prefix in ("location_start", "location_end"):
                    label = _norm_text(scene.get(f"{prefix}_label"))
                    if not label:
                        errors.append(
                            issue(
                                "missing_location_context",
                                f"{prefix}_label is required",
                                scene_ref=scene_ref,
                            )
                        )
                        continue
                    if _is_placeholder(label):
                        errors.append(
                            issue(
                                "transition_placeholder",
                                f"{prefix}_label contains placeholder token",
                                scene_ref=scene_ref,
                            )
                        )
                        continue
                    existing = by_label.get(label.casefold())
                    if existing is None:
                        loc_id = _stable_location_id(label)
                        while (
                            loc_id in by_id
                            and _norm_text(by_id[loc_id].get("display_name")).casefold()
                            != label.casefold()
                        ):
                            loc_id = f"{loc_id}_X"
                        item = {
                            "location_id": loc_id,
                            "display_name": label,
                            "aliases": [],
                            "stability_key": label.casefold(),
                            "introduced_in": scene_ref or "",
                        }
                        entries.append(item)
                        by_label[label.casefold()] = item
                        by_id[loc_id] = item
                        existing = item
                    scene[f"{prefix}_id"] = _norm_text(existing.get("location_id"))

    registry["schema_version"] = "location_registry_v1"
    registry["locations"] = entries
    return registry, errors


def route_phase04_candidates(
    *,
    candidate_seams: List[Dict[str, Any]],
    exact_scene_count: bool,
    allow_transition_scene_insertions: bool,
    transition_insert_budget_per_chapter: int,
) -> Dict[str, Any]:
    normalized: List[Dict[str, Any]] = []
    for item in candidate_seams:
        if not isinstance(item, dict):
            continue
        from_ref = _norm_text(item.get("from_scene_ref"))
        to_ref = _norm_text(item.get("to_scene_ref"))
        score = _to_int(item.get("seam_score"))
        resolution = _norm_text(item.get("requested_resolution"))
        if not from_ref or not to_ref or score is None or resolution not in SEAM_RESOLUTION_ENUM:
            continue
        chapter = _to_int(from_ref.split(":", 1)[0]) or 0
        normalized.append(
            {
                "from_scene_ref": from_ref,
                "to_scene_ref": to_ref,
                "seam_score": score,
                "requested_resolution": resolution,
                "chapter_id": chapter,
                "reason": _norm_text(item.get("reason")),
            }
        )

    selected: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    exact_conflicts: List[Dict[str, Any]] = []

    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for item in normalized:
        grouped.setdefault(item["chapter_id"], []).append(item)

    budget = max(0, int(transition_insert_budget_per_chapter))
    for chapter_id, items in grouped.items():
        insertion = [x for x in items if x["requested_resolution"] in {"micro_scene", "full_scene"}]
        inline = [x for x in items if x["requested_resolution"] == "inline_bridge"]
        selected.extend(inline)

        if insertion:
            if exact_scene_count:
                for item in insertion:
                    exact_conflicts.append(
                        {
                            "scene_ref": item["from_scene_ref"],
                            "to_scene_ref": item["to_scene_ref"],
                            "seam_score": item["seam_score"],
                            "reason": "exact_scene_count_transition_conflict",
                        }
                    )
                continue

            if not allow_transition_scene_insertions:
                for item in insertion:
                    blocked.append(
                        {
                            "scene_ref": item["from_scene_ref"],
                            "to_scene_ref": item["to_scene_ref"],
                            "seam_score": item["seam_score"],
                            "reason": "insertions_disabled",
                        }
                    )
                continue

            ordered = sorted(
                insertion,
                key=lambda x: (
                    -int(x["seam_score"]),
                    _to_int(x["from_scene_ref"].split(":", 1)[1]) or 0,
                    x["from_scene_ref"],
                    x["to_scene_ref"],
                ),
            )
            selected.extend(ordered[:budget])
            for item in ordered[budget:]:
                blocked.append(
                    {
                        "scene_ref": item["from_scene_ref"],
                        "to_scene_ref": item["to_scene_ref"],
                        "seam_score": item["seam_score"],
                        "reason": "blocked_by_budget",
                    }
                )

    return {
        "candidate_count": len(normalized),
        "selected": selected,
        "blocked": blocked,
        "exact_conflicts": exact_conflicts,
    }
