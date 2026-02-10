from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _chapter_scene_count(chapter: Dict[str, Any]) -> int:
    count = 0
    sections = chapter.get("sections", []) if isinstance(chapter.get("sections", []), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        scenes = section.get("scenes", []) if isinstance(section.get("scenes", []), list) else []
        count += len([scene for scene in scenes if isinstance(scene, dict)])
    return count


def _outline_summary(outline: Dict[str, Any]) -> Tuple[List[int], Dict[int, int]]:
    chapter_order: List[int] = []
    scene_counts: Dict[int, int] = {}
    chapters = outline.get("chapters", []) if isinstance(outline.get("chapters", []), list) else []
    for index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            continue
        chapter_id = chapter.get("chapter_id", index)
        try:
            chapter_num = int(chapter_id)
        except (TypeError, ValueError):
            continue
        chapter_order.append(chapter_num)
        scene_counts[chapter_num] = _chapter_scene_count(chapter)
    return chapter_order, scene_counts


def _build_character_registry(outline: Dict[str, Any]) -> List[Dict[str, str]]:
    registry: List[Dict[str, str]] = []
    characters = outline.get("characters", [])
    if not isinstance(characters, list):
        return registry
    for item in characters:
        if not isinstance(item, dict):
            continue
        character_id = str(item.get("character_id") or "").strip()
        if not character_id:
            continue
        name = str(item.get("name") or "").strip()
        registry.append({"character_id": character_id, "name": name})
    return registry


def _build_thread_registry(outline: Dict[str, Any]) -> List[Dict[str, str]]:
    registry: List[Dict[str, str]] = []
    threads = outline.get("threads", [])
    if not isinstance(threads, list):
        return registry
    for item in threads:
        if not isinstance(item, dict):
            continue
        thread_id = str(item.get("thread_id") or "").strip()
        if not thread_id:
            continue
        label = str(item.get("label") or "").strip()
        status = str(item.get("status") or "").strip()
        entry = {"thread_id": thread_id}
        if label:
            entry["label"] = label
        if status:
            entry["status"] = status
        registry.append(entry)
    return registry


def _character_name_map(registry: List[Dict[str, str]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for entry in registry:
        if not isinstance(entry, dict):
            continue
        char_id = str(entry.get("character_id") or "").strip()
        name = str(entry.get("name") or "").strip()
        if char_id:
            mapping[char_id] = name or char_id
    return mapping


def _character_id_map(registry: List[Dict[str, str]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for entry in registry:
        if not isinstance(entry, dict):
            continue
        char_id = str(entry.get("character_id") or "").strip()
        name = str(entry.get("name") or "").strip().lower()
        if name and char_id:
            mapping[name] = char_id
        if char_id:
            mapping[char_id.lower()] = char_id
    return mapping
