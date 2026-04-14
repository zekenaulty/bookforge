from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .validators import ValidationResult, validate_phase_04d


STEP_ID = "phase_04d_seam_hygiene"


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _find_chapter(outline: Dict[str, Any], chapter_id: int) -> Dict[str, Any]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        if _to_int(chapter.get("chapter_id")) == chapter_id:
            return chapter
    return {}


def _scene_index(chapter: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    index: Dict[int, Dict[str, Any]] = {}
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            scene_id = _to_int(scene.get("scene_id"))
            if scene_id:
                index[scene_id] = scene
    return index


def preprocess(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not isinstance(payload, dict):
        return deepcopy(payload), []

    outline = payload.get("outline") if isinstance(payload.get("outline"), dict) else None
    if not isinstance(outline, dict):
        return deepcopy(payload), []

    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    if len(chapters) != 1 or not isinstance(chapters[0], dict):
        return deepcopy(payload), []

    chapter_patch = chapters[0]
    chapter_id = _to_int(chapter_patch.get("chapter_id"))
    if not chapter_id:
        return deepcopy(payload), []

    before_outline = runtime.get("phase04d_before_outline")
    if not isinstance(before_outline, dict):
        return deepcopy(payload), []

    before_chapter = _find_chapter(before_outline, chapter_id)
    if not before_chapter:
        return deepcopy(payload), []

    allowed_fields = runtime.get("phase04d_allowed_fields")
    allowed_scene_fields = (
        set(allowed_fields.get("scene_fields"))
        if isinstance(allowed_fields, dict) and isinstance(allowed_fields.get("scene_fields"), list)
        else set()
    )
    window_refs = runtime.get("phase04d_window_scene_refs")
    window_set = {str(ref) for ref in window_refs if str(ref).strip()} if isinstance(window_refs, list) else set()

    merged_chapter = deepcopy(before_chapter)
    merged_index = _scene_index(merged_chapter)

    patch_sections = chapter_patch.get("sections") if isinstance(chapter_patch.get("sections"), list) else []
    for section in patch_sections:
        if not isinstance(section, dict):
            continue
        scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            scene_id = _to_int(scene.get("scene_id"))
            if not scene_id:
                continue
            ref = f"{chapter_id}:{scene_id}"
            if window_set and ref not in window_set:
                continue
            target = merged_index.get(scene_id)
            if not isinstance(target, dict):
                continue
            for field in allowed_scene_fields:
                if field in scene:
                    target[field] = deepcopy(scene[field])

    merged_outline = deepcopy(outline)
    merged_outline["chapters"] = [merged_chapter]
    merged_payload = deepcopy(payload)
    merged_payload["outline"] = merged_outline
    return merged_payload, []


def validate(
    payload: Dict[str, Any],
    *,
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> ValidationResult:
    sections = handoffs.get("outline_sections_v1") if isinstance(handoffs.get("outline_sections_v1"), dict) else None
    return validate_phase_04d(
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
        "phase_04d_window_json": runtime.get("phase04d_current_window", {}),
        "phase_04d_allowed_fields_json": runtime.get("phase04d_allowed_fields", {}),
    }
