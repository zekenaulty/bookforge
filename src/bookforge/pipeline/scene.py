from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

from bookforge.characters import ensure_character_index, resolve_character_state_path
from bookforge.pipeline.state_apply import _ensure_character_continuity_system_state, _find_chapter_outline


def _scene_cast_ids_from_outline(outline: Dict[str, Any], chapter_num: int, scene_num: int) -> List[str]:
    chapter = _find_chapter_outline(outline, chapter_num)
    scenes: List[Dict[str, Any]] = []
    sections = chapter.get("sections") if isinstance(chapter, dict) else None
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            sec_scenes = section.get("scenes")
            if isinstance(sec_scenes, list):
                scenes.extend([item for item in sec_scenes if isinstance(item, dict)])
    else:
        raw = chapter.get("scenes") if isinstance(chapter, dict) else None
        if isinstance(raw, list):
            scenes = [item for item in raw if isinstance(item, dict)]
    if not scenes:
        return []
    index = max(0, scene_num - 1)
    if index >= len(scenes):
        return []
    current = scenes[index]
    cast_ids = current.get("characters") if isinstance(current, dict) else None
    if not isinstance(cast_ids, list):
        return []
    return [str(item) for item in cast_ids if str(item).strip()]


def _load_character_states(book_root: Path, scene_card: Dict[str, Any]) -> List[Dict[str, Any]]:
    cast_ids = scene_card.get("cast_present_ids", []) if isinstance(scene_card, dict) else []
    if not isinstance(cast_ids, list):
        cast_ids = []
    ensure_character_index(book_root)
    states: List[Dict[str, Any]] = []
    for char_id in cast_ids:
        state_path = resolve_character_state_path(book_root, str(char_id))
        if state_path and state_path.exists():
            try:
                loaded = json.loads(state_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    _ensure_character_continuity_system_state(loaded)
                states.append(loaded)
                continue
            except json.JSONDecodeError:
                pass
        states.append({"character_id": str(char_id), "missing": True})
    return states


def _normalize_continuity_pack(
    pack: Dict[str, Any],
    scene_card: Dict[str, Any],
    thread_registry: List[Dict[str, str]],
) -> Dict[str, Any]:
    normalized = dict(pack)
    allowed_cast = scene_card.get("cast_present", [])
    if not isinstance(allowed_cast, list):
        allowed_cast = []
    allowed_cast = [str(item) for item in allowed_cast if str(item).strip()]
    cast_present = normalized.get("cast_present", [])
    if not isinstance(cast_present, list):
        cast_present = []
    cast_present = [str(item) for item in cast_present if str(item).strip()]
    if allowed_cast:
        filtered_cast = [item for item in cast_present if item in allowed_cast]
        normalized["cast_present"] = filtered_cast or list(allowed_cast)
    else:
        normalized["cast_present"] = []

    allowed_threads = {
        str(item.get("thread_id")).strip()
        for item in thread_registry
        if isinstance(item, dict) and str(item.get("thread_id") or "").strip()
    }
    thread_ids = scene_card.get("thread_ids", [])
    if not isinstance(thread_ids, list):
        thread_ids = []
    thread_ids = [str(item) for item in thread_ids if str(item).strip()]
    open_threads = normalized.get("open_threads", [])
    if not isinstance(open_threads, list):
        open_threads = []
    open_threads = [str(item) for item in open_threads if str(item).strip()]
    if thread_ids:
        open_threads = thread_ids
    if allowed_threads:
        open_threads = [item for item in open_threads if item in allowed_threads]
    normalized["open_threads"] = open_threads

    return normalized


def _parse_until(value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not value:
        return None, None
    parts = [part.strip() for part in value.split(":") if part.strip()]
    if len(parts) == 2 and parts[0].lower() == "chapter":
        return int(parts[1]), None
    if len(parts) == 4 and parts[0].lower() == "chapter" and parts[2].lower() == "scene":
        return int(parts[1]), int(parts[3])
    raise ValueError("Invalid --until value. Expected chapter:N or chapter:N:scene:M.")
