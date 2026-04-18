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
    "terminal",
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


def _chapter_scene_order(chapter: Dict[str, Any]) -> List[Tuple[int, str, Dict[str, Any]]]:
    ordered: List[Tuple[int, str, Dict[str, Any]]] = []
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
            if not chapter_id or not scene_id:
                continue
            ref = f"{chapter_id}:{scene_id}"
            ordered.append((scene_id, ref, scene))
    return ordered


def _outline_scene_ref_map(outline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        for scene_id, ref, scene in _chapter_scene_order(chapter):
            mapping[ref] = scene
    return mapping


def derive_phase04c_windows(
    *,
    chapter: Dict[str, Any],
    insertion_impacts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not insertion_impacts:
        return []
    chapter_id = _to_int(chapter.get("chapter_id")) or 0
    if chapter_id < 1:
        return []

    ordered = _chapter_scene_order(chapter)
    if not ordered:
        return []

    ref_to_index = {ref: idx for idx, (_, ref, _) in enumerate(ordered)}
    normalized: List[Dict[str, Any]] = []
    for item in insertion_impacts:
        if not isinstance(item, dict):
            continue
        from_ref = _norm_text(item.get("from_scene_ref"))
        to_ref = _norm_text(item.get("to_scene_ref"))
        inserted_ref = _norm_text(item.get("inserted_scene_ref"))
        if not from_ref or not to_ref or not inserted_ref:
            continue
        indices = [
            ref_to_index.get(from_ref),
            ref_to_index.get(inserted_ref),
            ref_to_index.get(to_ref),
        ]
        indices = [idx for idx in indices if isinstance(idx, int)]
        if not indices:
            continue
        normalized.append(
            {
                "start": min(indices),
                "end": max(indices),
                "impact": {
                    "from_scene_ref": from_ref,
                    "to_scene_ref": to_ref,
                    "inserted_scene_ref": inserted_ref,
                    "requested_resolution": _norm_text(item.get("requested_resolution")),
                    "resolution": _norm_text(item.get("resolution")),
                },
            }
        )

    if not normalized:
        return []

    normalized.sort(key=lambda item: (item["start"], item["end"]))
    merged: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    for item in normalized:
        if current is None:
            current = {
                "start": item["start"],
                "end": item["end"],
                "impacts": [item["impact"]],
            }
            continue
        if item["start"] <= current["end"] + 1:
            current["end"] = max(current["end"], item["end"])
            current["impacts"].append(item["impact"])
        else:
            merged.append(current)
            current = {
                "start": item["start"],
                "end": item["end"],
                "impacts": [item["impact"]],
            }
    if current is not None:
        merged.append(current)

    windows: List[Dict[str, Any]] = []
    for index, item in enumerate(merged, start=1):
        start_idx = int(item["start"])
        end_idx = int(item["end"])
        window_refs = [ref for _, ref, _ in ordered[start_idx : end_idx + 1]]
        window_id = f"ch{chapter_id:02d}_win{index:02d}"
        windows.append(
            {
                "window_id": window_id,
                "chapter_id": chapter_id,
                "scene_id_start": ordered[start_idx][0],
                "scene_id_end": ordered[end_idx][0],
                "scene_refs": window_refs,
                "impact_edges": deepcopy(item["impacts"]),
            }
        )
    return windows


def derive_intro_mismatches_by_chapter(outline: Dict[str, Any]) -> Dict[str, List[str]]:
    mismatches: Dict[str, List[str]] = {}
    if not isinstance(outline, dict):
        return mismatches
    appearances = _first_character_appearance(outline)
    registry = _character_map(outline)
    for char_id, first_ref in appearances.items():
        entry = registry.get(char_id)
        if not isinstance(entry, dict):
            continue
        intro = entry.get("intro") if isinstance(entry.get("intro"), dict) else {}
        intro_chapter = _to_int(intro.get("chapter"))
        intro_scene = _to_int(intro.get("scene"))
        if intro_chapter != first_ref.get("chapter") or intro_scene != first_ref.get("scene"):
            chapter_key = str(first_ref.get("chapter") or "")
            if not chapter_key:
                continue
            mismatches.setdefault(chapter_key, []).append(char_id)
    return mismatches


def _location_jump_violations(
    chapter: Dict[str, Any],
    *,
    allowed_jump_modes: Set[str],
) -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    ordered = _chapter_scene_order(chapter)
    if len(ordered) < 2:
        return violations
    for idx in range(len(ordered) - 1):
        _, from_ref, from_scene = ordered[idx]
        _, to_ref, to_scene = ordered[idx + 1]
        from_loc = _norm_text(from_scene.get("location_end_id") or from_scene.get("location_end"))
        to_loc = _norm_text(to_scene.get("location_start_id") or to_scene.get("location_start"))
        if not from_loc or not to_loc:
            continue
        if from_loc == to_loc:
            continue
        mode = _norm_text(to_scene.get("handoff_mode"))
        if mode == "terminal":
            continue
        if mode in allowed_jump_modes:
            continue
        violations.append(
            {
                "scene_ref": to_ref,
                "from_scene_ref": from_ref,
                "handoff_mode": mode,
                "reason": "location_jump_requires_arrival_or_time_skip",
            }
        )
    return violations


def derive_handoff_normalize_targets(
    *,
    chapter: Dict[str, Any],
    allowed_jump_modes: Set[str],
) -> List[Dict[str, Any]]:
    targets: List[Dict[str, Any]] = []
    ordered = _chapter_scene_order(chapter)
    if not ordered:
        return targets
    chapter_id = _to_int(chapter.get("chapter_id")) or 0
    # Chapter-final terminal normalization
    _, last_ref, last_scene = ordered[-1]
    last_mode = _norm_text(last_scene.get("handoff_mode"))
    if last_mode != "terminal":
        targets.append(
            {
                "scene_ref": last_ref,
                "reason": "chapter_terminal_requires_terminal",
                "chapter_id": chapter_id,
            }
        )
    # Location jump violations
    for item in _location_jump_violations(chapter, allowed_jump_modes=allowed_jump_modes):
        item["chapter_id"] = chapter_id
        item["allowed_jump_modes"] = sorted(allowed_jump_modes)
        targets.append(item)
    return targets


def derive_phase04d_windows(
    *,
    chapter: Dict[str, Any],
    insertion_impacts: List[Dict[str, Any]],
    require_seam_fields: bool = True,
) -> List[Dict[str, Any]]:
    chapter_id = _to_int(chapter.get("chapter_id")) or 0
    if chapter_id < 1:
        return []
    ordered = _chapter_scene_order(chapter)
    if not ordered:
        return []

    ref_to_index = {ref: idx for idx, (_, ref, _) in enumerate(ordered)}
    issue_reasons: Dict[int, Set[str]] = {}
    impact_entries: List[Dict[str, Any]] = []

    for item in insertion_impacts:
        if not isinstance(item, dict):
            continue
        from_ref = _norm_text(item.get("from_scene_ref"))
        to_ref = _norm_text(item.get("to_scene_ref"))
        inserted_ref = _norm_text(item.get("inserted_scene_ref"))
        if not from_ref or not to_ref or not inserted_ref:
            continue
        indices = [
            ref_to_index.get(from_ref),
            ref_to_index.get(inserted_ref),
            ref_to_index.get(to_ref),
        ]
        indices = [idx for idx in indices if isinstance(idx, int)]
        if not indices:
            continue
        start_idx = min(indices)
        end_idx = max(indices)
        impact_entries.append(
            {
                "start": start_idx,
                "end": end_idx,
                "impact": {
                    "from_scene_ref": from_ref,
                    "to_scene_ref": to_ref,
                    "inserted_scene_ref": inserted_ref,
                    "requested_resolution": _norm_text(item.get("requested_resolution")),
                    "resolution": _norm_text(item.get("resolution")),
                },
            }
        )
        for idx in indices:
            issue_reasons.setdefault(idx, set()).add("insertion_impact")

    for idx, (_, ref, scene) in enumerate(ordered):
        if require_seam_fields and (
            "seam_score" not in scene or "seam_resolution" not in scene
        ):
            issue_reasons.setdefault(idx, set()).add("missing_seam_metadata")
        in_anchors = scene.get("transition_in_anchors")
        out_anchors = scene.get("transition_out_anchors")
        if isinstance(in_anchors, list) and isinstance(out_anchors, list) and in_anchors == out_anchors:
            issue_reasons.setdefault(idx, set()).add("identical_anchors")

    if not issue_reasons:
        return []

    expanded: Set[int] = set()
    for idx in issue_reasons.keys():
        for offset in (-1, 0, 1):
            neighbor = idx + offset
            if 0 <= neighbor < len(ordered):
                expanded.add(neighbor)

    sorted_idx = sorted(expanded)
    windows: List[Dict[str, Any]] = []
    start = None
    prev = None
    for idx in sorted_idx:
        if start is None:
            start = idx
            prev = idx
            continue
        if idx == prev + 1:
            prev = idx
            continue
        windows.append((start, prev))
        start = idx
        prev = idx
    if start is not None:
        windows.append((start, prev if prev is not None else start))

    output: List[Dict[str, Any]] = []
    for window_index, (start_idx, end_idx) in enumerate(windows, start=1):
        window_refs = [ref for _, ref, _ in ordered[start_idx : end_idx + 1]]
        reasons: Set[str] = set()
        for idx in range(start_idx, end_idx + 1):
            reasons |= issue_reasons.get(idx, set())
        impact_edges = [
            deepcopy(item["impact"])
            for item in impact_entries
            if item["start"] <= end_idx and item["end"] >= start_idx
        ]
        window_id = f"ch{chapter_id:02d}_seam{window_index:02d}"
        output.append(
            {
                "window_id": window_id,
                "chapter_id": chapter_id,
                "scene_id_start": ordered[start_idx][0],
                "scene_id_end": ordered[end_idx][0],
                "scene_refs": window_refs,
                "reasons": sorted(reasons),
                "impact_edges": impact_edges,
            }
        )
    return output


def _scene_changed_fields(before: Dict[str, Any], after: Dict[str, Any]) -> Set[str]:
    changed: Set[str] = set()
    keys = set(before.keys()) | set(after.keys())
    for key in keys:
        if before.get(key) != after.get(key):
            changed.add(key)
    return changed


def _character_map(outline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    characters = outline.get("characters") if isinstance(outline.get("characters"), list) else []
    for entry in characters:
        if not isinstance(entry, dict):
            continue
        char_id = _norm_text(entry.get("character_id"))
        if not char_id:
            continue
        mapping[char_id] = entry
    return mapping


def _first_character_appearance(outline: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    appearances: Dict[str, Dict[str, int]] = {}
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
                characters = scene.get("characters") if isinstance(scene.get("characters"), list) else []
                for char_id in characters:
                    char_key = _norm_text(char_id)
                    if not char_key or char_key in appearances:
                        continue
                    appearances[char_key] = {
                        "chapter": chapter_id,
                        "scene": scene_id,
                    }
    return appearances


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
        if subset_ids is None and chapter_id != chapter_index:
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
    chapter_subset_ids: Optional[Set[int]] = None,
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
    subset_ids: Optional[Set[int]] = None
    if chapter_subset_ids:
        subset_ids = {int(item) for item in chapter_subset_ids if _to_int(item)}
    validated_chapters = 0

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
        if subset_ids is not None:
            if chapter_id is None:
                errors.append(
                    issue(
                        "chapter_id_required",
                        "chapter_id is required",
                        path=f"chapters[{chapter_index-1}].chapter_id",
                    )
                )
                continue
            if chapter_id not in subset_ids:
                continue
        if subset_ids is None and chapter_id != chapter_index:
            errors.append(
                issue(
                    "chapter_id_sequential",
                    f"chapter_id must be {chapter_index}",
                    path=f"chapters[{chapter_index-1}].chapter_id",
                )
            )
            continue
        validated_chapters += 1

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
                section_status = _norm_text(section.get("status"))
                if section_status == "stub":
                    continue
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

    metrics["chapter_count"] = validated_chapters if subset_ids is not None else len(chapters)
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
                "Selected insertion candidates were not resolved by LLM output: "
                + ", ".join(sorted(unresolved_selected)),
                path="phase_report.resolved_candidates",
            )
        )
    if selected_insertions and not inserted_ref_set:
        errors.append(
            issue(
                "transition_insertion_required",
                "Selected insertion candidates require inserted scenes, but none were reported",
                path="phase_report.inserted_scene_refs",
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

    insertion_impacts = (
        phase_report.get("insertion_edge_impacts")
        if isinstance(phase_report.get("insertion_edge_impacts"), list)
        else []
    )
    if inserted_ref_set and not insertion_impacts:
        errors.append(
            issue(
                "transition_insertion_impacts_required",
                "phase_report.insertion_edge_impacts is required when insertions occur",
                path="phase_report.insertion_edge_impacts",
            )
        )
    outline_scene_refs = set(_outline_scene_ref_map(wrapper_outline).keys())
    impact_inserted_refs: Set[str] = set()
    for idx, item in enumerate(insertion_impacts):
        if not isinstance(item, dict):
            errors.append(
                issue(
                    "transition_insertion_impact_type",
                    "insertion_edge_impacts entries must be objects",
                    path=f"phase_report.insertion_edge_impacts[{idx}]",
                )
            )
            continue
        from_ref = _norm_text(item.get("from_scene_ref"))
        to_ref = _norm_text(item.get("to_scene_ref"))
        inserted_ref = _norm_text(item.get("inserted_scene_ref"))
        if not REF_PATTERN.fullmatch(from_ref):
            errors.append(
                issue(
                    "transition_insertion_impact_ref",
                    "from_scene_ref must be chapter:scene",
                    path=f"phase_report.insertion_edge_impacts[{idx}].from_scene_ref",
                )
            )
        if not REF_PATTERN.fullmatch(to_ref):
            errors.append(
                issue(
                    "transition_insertion_impact_ref",
                    "to_scene_ref must be chapter:scene",
                    path=f"phase_report.insertion_edge_impacts[{idx}].to_scene_ref",
                )
            )
        if not REF_PATTERN.fullmatch(inserted_ref):
            errors.append(
                issue(
                    "transition_insertion_impact_ref",
                    "inserted_scene_ref must be chapter:scene",
                    path=f"phase_report.insertion_edge_impacts[{idx}].inserted_scene_ref",
                )
            )
        if from_ref and from_ref not in outline_scene_refs:
            errors.append(
                issue(
                    "transition_insertion_impact_ref",
                    "from_scene_ref must exist in outline",
                    path=f"phase_report.insertion_edge_impacts[{idx}].from_scene_ref",
                )
            )
        if to_ref and to_ref not in outline_scene_refs:
            errors.append(
                issue(
                    "transition_insertion_impact_ref",
                    "to_scene_ref must exist in outline",
                    path=f"phase_report.insertion_edge_impacts[{idx}].to_scene_ref",
                )
            )
        if inserted_ref and inserted_ref not in outline_scene_refs:
            errors.append(
                issue(
                    "transition_insertion_impact_ref",
                    "inserted_scene_ref must exist in outline",
                    path=f"phase_report.insertion_edge_impacts[{idx}].inserted_scene_ref",
                )
            )
        if inserted_ref:
            impact_inserted_refs.add(inserted_ref)

        requested = _norm_text(item.get("requested_resolution"))
        if requested and requested not in SEAM_RESOLUTION_ENUM:
            errors.append(
                issue(
                    "transition_insertion_impact_resolution",
                    "requested_resolution must be inline_bridge|micro_scene|full_scene",
                    path=f"phase_report.insertion_edge_impacts[{idx}].requested_resolution",
                )
            )
        resolution = _norm_text(item.get("resolution"))
        if resolution and resolution not in SEAM_RESOLUTION_ENUM:
            errors.append(
                issue(
                    "transition_insertion_impact_resolution",
                    "resolution must be inline_bridge|micro_scene|full_scene",
                    path=f"phase_report.insertion_edge_impacts[{idx}].resolution",
                )
            )
        if requested and resolution and requested != resolution:
            errors.append(
                issue(
                    "transition_insertion_impact_resolution",
                    "requested_resolution must match resolution in insertion_edge_impacts",
                    path=f"phase_report.insertion_edge_impacts[{idx}]",
                )
            )

    if required_inserted_refs and impact_inserted_refs:
        missing_impacts = sorted(required_inserted_refs - impact_inserted_refs)
        if missing_impacts:
            errors.append(
                issue(
                    "transition_insertion_impact_missing",
                    "insertion_edge_impacts must include each inserted_scene_ref",
                    path="phase_report.insertion_edge_impacts",
                )
            )

    metrics["inserted_scene_count"] = len(inserted_ref_set)
    metrics["unresolved_required_insertions"] = len(unresolved_selected)
    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_04c(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
    runtime: Dict[str, Any],
) -> ValidationResult:
    wrapper_outline, wrapper_errors = _validate_wrapper(
        payload, "outline_relink_v1", "phase_report"
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

    before_outline = runtime.get("phase04c_before_outline")
    window_refs = runtime.get("phase04c_window_scene_refs")
    allowed_fields = runtime.get("phase04c_allowed_fields")
    allowed_characters = runtime.get("phase04c_window_character_ids")
    expected_window_id = _norm_text(runtime.get("phase04c_window_id"))

    if not isinstance(before_outline, dict) or not isinstance(window_refs, list) or not window_refs:
        status = "pass" if not errors else "fail"
        return ValidationResult(status, errors, warnings, metrics)

    window_set = {str(ref) for ref in window_refs if str(ref).strip()}
    allowed_scene_fields = (
        set(allowed_fields.get("scene_fields"))
        if isinstance(allowed_fields, dict) and isinstance(allowed_fields.get("scene_fields"), list)
        else set()
    )
    allowed_character_fields = (
        set(allowed_fields.get("character_fields"))
        if isinstance(allowed_fields, dict) and isinstance(allowed_fields.get("character_fields"), list)
        else set()
    )
    allowed_character_ids = (
        {str(item) for item in allowed_characters if str(item).strip()}
        if isinstance(allowed_characters, list)
        else set()
    )

    before_scene_map = _outline_scene_ref_map(before_outline)
    after_scene_map = _outline_scene_ref_map(wrapper_outline)

    missing_refs = [ref for ref in window_set if ref not in before_scene_map or ref not in after_scene_map]
    if missing_refs:
        errors.append(
            issue(
                "phase04c_window_scene_missing",
                "Window scene refs must exist in before/after outline",
                path="runtime.phase04c_window_scene_refs",
            )
        )

    before_refs = set(before_scene_map.keys())
    after_refs = set(after_scene_map.keys())
    if before_refs != after_refs:
        errors.append(
            issue(
                "phase04c_scene_ref_drift",
                "Scene refs must not be added or removed during relink",
                path="outline.chapters",
            )
        )

    touched_scene_refs: Set[str] = set()
    disallowed_scene_changes: List[Tuple[str, Set[str]]] = []
    for ref, before_scene in before_scene_map.items():
        after_scene = after_scene_map.get(ref)
        if after_scene is None:
            continue
        changed_fields = _scene_changed_fields(before_scene, after_scene)
        if not changed_fields:
            continue
        touched_scene_refs.add(ref)
        if ref not in window_set:
            disallowed_scene_changes.append((ref, changed_fields))
            continue
        disallowed_fields = {field for field in changed_fields if field not in allowed_scene_fields}
        if disallowed_fields:
            disallowed_scene_changes.append((ref, disallowed_fields))

    for ref, fields in disallowed_scene_changes:
        errors.append(
            issue(
                "phase04c_scene_field_change",
                f"Disallowed field changes for {ref}: {sorted(fields)}",
                scene_ref=ref,
            )
        )

    phase_report = payload.get("phase_report") if isinstance(payload.get("phase_report"), dict) else {}
    report_window_id = _norm_text(phase_report.get("window_id"))
    if expected_window_id and report_window_id and report_window_id != expected_window_id:
        errors.append(
            issue(
                "phase04c_window_id_mismatch",
                "phase_report.window_id must match active window",
                path="phase_report.window_id",
            )
        )

    touched_report = phase_report.get("touched_scene_refs")
    if touched_report is not None and not isinstance(touched_report, list):
        errors.append(
            issue(
                "phase04c_report_type",
                "phase_report.touched_scene_refs must be array",
                path="phase_report.touched_scene_refs",
            )
        )

    before_characters = _character_map(before_outline)
    after_characters = _character_map(wrapper_outline)
    updated_character_ids: Set[str] = set()
    for char_id, after_entry in after_characters.items():
        before_entry = before_characters.get(char_id)
        if before_entry is None:
            if char_id not in allowed_character_ids:
                errors.append(
                    issue(
                        "phase04c_character_add_forbidden",
                        "Character additions are not permitted during relink",
                        path="characters",
                    )
                )
            continue
        if before_entry == after_entry:
            continue
        if char_id not in allowed_character_ids:
            errors.append(
                issue(
                    "phase04c_character_scope",
                    f"Character {char_id} updated outside allowed window scope",
                    path="characters",
                )
            )
            continue
        changed_fields = _scene_changed_fields(before_entry, after_entry)
        disallowed_fields = {field for field in changed_fields if field not in allowed_character_fields}
        if disallowed_fields:
            errors.append(
                issue(
                    "phase04c_character_field_change",
                    f"Disallowed character field changes for {char_id}: {sorted(disallowed_fields)}",
                    path="characters",
                )
            )
            continue
        updated_character_ids.add(char_id)

    if updated_character_ids:
        appearances = _first_character_appearance(wrapper_outline)
        for char_id in updated_character_ids:
            expected_intro = appearances.get(char_id)
            entry = after_characters.get(char_id, {})
            intro = entry.get("intro") if isinstance(entry.get("intro"), dict) else {}
            intro_chapter = _to_int(intro.get("chapter"))
            intro_scene = _to_int(intro.get("scene"))
            if not expected_intro:
                errors.append(
                    issue(
                        "phase04c_character_intro_missing",
                        f"No scene appearance found for {char_id}",
                        path="characters",
                    )
                )
                continue
            if intro_chapter != expected_intro.get("chapter") or intro_scene != expected_intro.get("scene"):
                errors.append(
                    issue(
                        "phase04c_character_intro_mismatch",
                        f"Intro for {char_id} must match first appearance {expected_intro}",
                        path="characters",
                    )
                )

    metrics["touched_scene_count"] = len(touched_scene_refs)
    metrics["updated_character_count"] = len(updated_character_ids)
    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_04c_intro(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
    runtime: Dict[str, Any],
) -> ValidationResult:
    wrapper_outline, wrapper_errors = _validate_wrapper(
        payload, "outline_intro_sync_v1", "phase_report"
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

    before_outline = runtime.get("phase04c_intro_before_outline")
    allowed_character_ids = runtime.get("phase04c_intro_character_ids")
    if not isinstance(before_outline, dict) or not isinstance(allowed_character_ids, list):
        status = "pass" if not errors else "fail"
        return ValidationResult(status, errors, warnings, metrics)

    allowed_set = {str(item) for item in allowed_character_ids if str(item).strip()}
    before_scene_map = _outline_scene_ref_map(before_outline)
    after_scene_map = _outline_scene_ref_map(wrapper_outline)
    if before_scene_map.keys() != after_scene_map.keys():
        errors.append(
            issue(
                "phase04c_intro_scene_ref_drift",
                "Scenes must not be added or removed during intro sync",
                path="outline.chapters",
            )
        )
    for ref, before_scene in before_scene_map.items():
        after_scene = after_scene_map.get(ref)
        if after_scene is None:
            continue
        if _scene_changed_fields(before_scene, after_scene):
            errors.append(
                issue(
                    "phase04c_intro_scene_change",
                    f"Scene changes are not permitted during intro sync ({ref})",
                    scene_ref=ref,
                )
            )

    before_characters = _character_map(before_outline)
    after_characters = _character_map(wrapper_outline)
    updated_character_ids: Set[str] = set()
    for char_id, after_entry in after_characters.items():
        before_entry = before_characters.get(char_id)
        if before_entry is None:
            errors.append(
                issue(
                    "phase04c_intro_character_add_forbidden",
                    "Character additions are not permitted during intro sync",
                    path="characters",
                )
            )
            continue
        if before_entry == after_entry:
            continue
        changed_fields = _scene_changed_fields(before_entry, after_entry)
        if char_id not in allowed_set:
            errors.append(
                issue(
                    "phase04c_intro_character_scope",
                    f"Character {char_id} updated outside allowed scope",
                    path="characters",
                )
            )
            continue
        disallowed_fields = {field for field in changed_fields if field != "intro"}
        if disallowed_fields:
            errors.append(
                issue(
                    "phase04c_intro_character_field_change",
                    f"Disallowed character field changes for {char_id}: {sorted(disallowed_fields)}",
                    path="characters",
                )
            )
            continue
        updated_character_ids.add(char_id)

    if updated_character_ids:
        appearances = _first_character_appearance(wrapper_outline)
        for char_id in updated_character_ids:
            expected_intro = appearances.get(char_id)
            entry = after_characters.get(char_id, {})
            intro = entry.get("intro") if isinstance(entry.get("intro"), dict) else {}
            intro_chapter = _to_int(intro.get("chapter"))
            intro_scene = _to_int(intro.get("scene"))
            if not expected_intro:
                errors.append(
                    issue(
                        "phase04c_intro_missing_appearance",
                        f"No scene appearance found for {char_id}",
                        path="characters",
                    )
                )
                continue
            if intro_chapter != expected_intro.get("chapter") or intro_scene != expected_intro.get("scene"):
                errors.append(
                    issue(
                        "phase04c_intro_mismatch",
                        f"Intro for {char_id} must match first appearance {expected_intro}",
                        path="characters",
                    )
                )

    metrics["updated_character_count"] = len(updated_character_ids)
    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_04c_handoff(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
    runtime: Dict[str, Any],
) -> ValidationResult:
    wrapper_outline, wrapper_errors = _validate_wrapper(
        payload, "outline_handoff_normalize_v1", "phase_report"
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

    before_outline = runtime.get("phase04c_handoff_before_outline")
    allowed_scene_refs = runtime.get("phase04c_handoff_scene_refs")
    allowed_jump_modes = runtime.get("phase04c_handoff_allowed_jump_modes")
    if not isinstance(before_outline, dict) or not isinstance(allowed_scene_refs, list):
        status = "pass" if not errors else "fail"
        return ValidationResult(status, errors, warnings, metrics)

    allowed_chapters: Set[int] = set()
    for ref in allowed_scene_refs:
        ref_text = _norm_text(ref)
        if ":" not in ref_text:
            continue
        try:
            chapter_id = int(ref_text.split(":", 1)[0])
        except ValueError:
            continue
        if chapter_id > 0:
            allowed_chapters.add(chapter_id)

    allowed_set = {str(item) for item in allowed_scene_refs if str(item).strip()}
    before_scene_map = _outline_scene_ref_map(before_outline)
    after_scene_map = _outline_scene_ref_map(wrapper_outline)
    if before_scene_map.keys() != after_scene_map.keys():
        errors.append(
            issue(
                "phase04c_handoff_scene_ref_drift",
                "Scenes must not be added or removed during handoff normalize",
                path="outline.chapters",
            )
        )

    touched_scene_refs: Set[str] = set()
    disallowed_scene_changes: List[Tuple[str, Set[str]]] = []
    for ref, before_scene in before_scene_map.items():
        after_scene = after_scene_map.get(ref)
        if after_scene is None:
            continue
        changed_fields = _scene_changed_fields(before_scene, after_scene)
        if not changed_fields:
            continue
        touched_scene_refs.add(ref)
        if ref not in allowed_set:
            disallowed_scene_changes.append((ref, changed_fields))
            continue
        disallowed_fields = {field for field in changed_fields if field != "handoff_mode"}
        if disallowed_fields:
            disallowed_scene_changes.append((ref, disallowed_fields))

    for ref, fields in disallowed_scene_changes:
        errors.append(
            issue(
                "phase04c_handoff_scene_field_change",
                f"Disallowed field changes for {ref}: {sorted(fields)}",
                scene_ref=ref,
            )
        )

    if allowed_jump_modes is not None:
        allowed = {str(mode) for mode in allowed_jump_modes if str(mode).strip()}
    else:
        allowed = {"arrival_checkpoint", "time_skip"}
    chapters = wrapper_outline.get("chapters") if isinstance(wrapper_outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id")) or 0
        if allowed_chapters and chapter_id not in allowed_chapters:
            continue
        violations = _location_jump_violations(chapter, allowed_jump_modes=allowed)
        for item in violations:
            errors.append(
                issue(
                    "handoff_location_jump",
                    "Location jump requires arrival_checkpoint or time_skip",
                    scene_ref=_norm_text(item.get("scene_ref")),
                )
            )
        ordered = _chapter_scene_order(chapter)
        if ordered:
            _, last_ref, last_scene = ordered[-1]
            if _norm_text(last_scene.get("handoff_mode")) != "terminal":
                errors.append(
                    issue(
                        "chapter_terminal_requires_terminal",
                        "Chapter-final scene must use handoff_mode=terminal",
                        scene_ref=last_ref,
                    )
                )

    metrics["touched_scene_count"] = len(touched_scene_refs)
    status = "pass" if not errors else "fail"
    return ValidationResult(status, errors, warnings, metrics)


def validate_phase_04d(
    payload: Dict[str, Any],
    *,
    sections_payload: Optional[Dict[str, Any]],
    strict_transition_bridges: bool,
    runtime: Dict[str, Any],
) -> ValidationResult:
    wrapper_outline, wrapper_errors = _validate_wrapper(
        payload, "outline_seam_hygiene_v1", "phase_report"
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

    before_outline = runtime.get("phase04d_before_outline")
    window_refs = runtime.get("phase04d_window_scene_refs")
    allowed_fields = runtime.get("phase04d_allowed_fields")
    expected_window_id = _norm_text(runtime.get("phase04d_window_id"))

    has_window_context = (
        isinstance(before_outline, dict)
        and isinstance(window_refs, list)
        and bool(window_refs)
    )
    window_set = {str(ref) for ref in window_refs if str(ref).strip()} if has_window_context else set()

    touched_scene_refs: Set[str] = set()
    if has_window_context:
        allowed_scene_fields = (
            set(allowed_fields.get("scene_fields"))
            if isinstance(allowed_fields, dict) and isinstance(allowed_fields.get("scene_fields"), list)
            else set()
        )

        before_scene_map = _outline_scene_ref_map(before_outline)
        after_scene_map = _outline_scene_ref_map(wrapper_outline)
        if before_scene_map.keys() != after_scene_map.keys():
            errors.append(
                issue(
                    "phase04d_scene_ref_drift",
                    "Scene refs must not be added or removed during seam hygiene",
                    path="outline.chapters",
                )
            )

        disallowed_scene_changes: List[Tuple[str, Set[str]]] = []
        for ref, before_scene in before_scene_map.items():
            after_scene = after_scene_map.get(ref)
            if after_scene is None:
                continue
            changed_fields = _scene_changed_fields(before_scene, after_scene)
            if not changed_fields:
                continue
            touched_scene_refs.add(ref)
            if ref not in window_set:
                disallowed_scene_changes.append((ref, changed_fields))
                continue
            disallowed_fields = {field for field in changed_fields if field not in allowed_scene_fields}
            if disallowed_fields:
                disallowed_scene_changes.append((ref, disallowed_fields))

        for ref, fields in disallowed_scene_changes:
            errors.append(
                issue(
                    "phase04d_scene_field_change",
                    f"Disallowed field changes for {ref}: {sorted(fields)}",
                    scene_ref=ref,
                )
            )

    # Enforce seam metadata presence.
    # During window execution: only enforce within the active window.
    # During final validation (no window context): enforce globally.
    chapters = wrapper_outline.get("chapters") if isinstance(wrapper_outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = chapter.get("chapter_id")
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_ref = f"{chapter_id}:{scene.get('scene_id')}"
                if has_window_context and scene_ref not in window_set:
                    continue
                if "seam_score" not in scene or "seam_resolution" not in scene:
                    errors.append(
                        issue(
                            "seam_metadata_required",
                            "seam_score and seam_resolution are required on every scene",
                            scene_ref=scene_ref,
                        )
                    )

    phase_report = payload.get("phase_report") if isinstance(payload.get("phase_report"), dict) else {}
    report_window_id = _norm_text(phase_report.get("window_id"))
    if expected_window_id and report_window_id and report_window_id != expected_window_id:
        errors.append(
            issue(
                "phase04d_window_id_mismatch",
                "phase_report.window_id must match active window",
                path="phase_report.window_id",
            )
        )

    # No character changes allowed (only enforce when baseline is available)
    if isinstance(before_outline, dict):
        if _character_map(before_outline) != _character_map(wrapper_outline):
            errors.append(
                issue(
                    "phase04d_character_change",
                    "Character registry changes are not permitted during seam hygiene",
                    path="characters",
                )
            )

    metrics["touched_scene_count"] = len(touched_scene_refs)
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
    chapter_last_scene: Dict[int, Dict[str, Any]] = {}
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id")) or 0
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        last_scene: Optional[Dict[str, Any]] = None
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                if last_scene is None or _to_int(scene.get("scene_id")) > _to_int(last_scene.get("scene_id")):
                    last_scene = scene
                if "transition_in" in scene and "transition_in_text" not in scene:
                    scene["transition_in_text"] = scene.get("transition_in")
                if "transition_out" in scene and "transition_out_text" not in scene:
                    scene["transition_out_text"] = scene.get("transition_out")
        if chapter_id and last_scene is not None:
            chapter_last_scene[chapter_id] = last_scene

    # Enforce chapter-terminal invariants: terminal scenes should not hand off.
    for chapter_id, last_scene in chapter_last_scene.items():
        if _norm_text(last_scene.get("handoff_mode")) == "terminal":
            last_scene.pop("hands_off_to", None)

    # Clear cross-chapter consumes_outcome_from when previous chapter is terminal.
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id")) or 0
        if chapter_id <= 1:
            continue
        previous_last = chapter_last_scene.get(chapter_id - 1)
        if not previous_last or _norm_text(previous_last.get("handoff_mode")) != "terminal":
            continue
        # find first scene in chapter
        first_scene: Optional[Dict[str, Any]] = None
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                if first_scene is None or _to_int(scene.get("scene_id")) < _to_int(first_scene.get("scene_id")):
                    first_scene = scene
        if first_scene is None:
            continue
        consumes = _norm_text(first_scene.get("consumes_outcome_from"))
        if consumes and consumes.startswith(f"{chapter_id - 1}:"):
            first_scene.pop("consumes_outcome_from", None)
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
