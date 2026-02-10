from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from bookforge.characters import ensure_character_index, resolve_character_state_path, create_character_state_path

SUMMARY_CHAPTER_SO_FAR_CAP = 20
SUMMARY_KEY_FACTS_CAP = 25
SUMMARY_MUST_STAY_TRUE_CAP = 20
SUMMARY_STORY_SO_FAR_CAP = 40


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _maybe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _summary_list(value: Any) -> List[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [value]
    else:
        items = []
    cleaned: List[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _normalize_title_entry(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, dict):
        title = dict(value)
        name = ""
        for key in ("name", "title", "label", "id", "key"):
            candidate = title.get(key)
            if isinstance(candidate, str) and candidate.strip():
                name = candidate.strip()
                break
        if not name:
            return None
        title["name"] = name
        return title
    text = str(value).strip()
    if not text:
        return None
    return {"name": text}


def _normalize_titles_value(value: Any) -> List[Dict[str, Any]]:
    raw_items: List[Any] = []
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, dict):
        if any(key in value for key in ("name", "title", "label", "id", "key")):
            raw_items = [value]
        else:
            for key, entry in value.items():
                wrapped: Dict[str, Any] = {"name": str(key).strip()}
                if isinstance(entry, dict):
                    wrapped.update(entry)
                elif entry is not None:
                    wrapped["value"] = entry
                raw_items.append(wrapped)
    elif value is not None:
        raw_items = [value]

    normalized: List[Dict[str, Any]] = []
    for item in raw_items:
        title = _normalize_title_entry(item)
        if title:
            normalized.append(title)

    by_name: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for title in normalized:
        key = str(title.get("name") or "").strip().lower()
        if not key:
            continue
        if key not in by_name:
            by_name[key] = dict(title)
            order.append(key)
            continue
        merged = dict(by_name[key])
        merged.update(title)
        by_name[key] = merged

    return [by_name[key] for key in order]


def _normalize_titles_in_continuity_state(continuity: Dict[str, Any]) -> None:
    if not isinstance(continuity, dict):
        return
    if "titles" in continuity:
        continuity["titles"] = _normalize_titles_value(continuity.get("titles"))


def _dedupe_preserve(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _append_continuity_list_item(target_set: Dict[str, Any], key: str, value: str) -> None:
    if key == "titles":
        existing = target_set.get("titles")
        normalized_existing = _normalize_titles_value(existing)
        title = _normalize_title_entry(value)
        if title:
            normalized_existing.append(title)
        target_set["titles"] = _normalize_titles_value(normalized_existing)
        return
    existing = target_set.get(key)
    if isinstance(existing, list):
        if value not in existing:
            existing.append(value)
            target_set[key] = existing
        return
    target_set[key] = [value]


def _apply_bag_updates(bag: Dict[str, Any], updates: Dict[str, Any]) -> None:
    if not isinstance(bag, dict) or not isinstance(updates, dict):
        return
    set_block = updates.get("set")
    delta_block = updates.get("delta")
    remove_block = updates.get("remove")

    # Apply delta first so explicit set values are authoritative when both target the same key.
    if isinstance(delta_block, dict):
        for key, value in delta_block.items():
            if str(key) == "titles":
                bag["titles"] = _normalize_titles_value(value)
                continue
            if isinstance(value, (int, float)):
                existing = bag.get(key)
                if isinstance(existing, (int, float)):
                    bag[key] = existing + value
                elif isinstance(existing, dict) and isinstance(existing.get("current"), (int, float)):
                    existing["current"] = existing.get("current", 0) + value
                    bag[key] = existing
                else:
                    bag[key] = value
            elif isinstance(value, dict):
                existing = bag.get(key)
                if not isinstance(existing, dict):
                    existing = {}
                for sub_key, sub_val in value.items():
                    if isinstance(sub_val, (int, float)):
                        prior = existing.get(sub_key)
                        if isinstance(prior, (int, float)):
                            existing[sub_key] = prior + sub_val
                        else:
                            existing[sub_key] = sub_val
                    else:
                        existing[sub_key] = sub_val
                bag[key] = existing
            else:
                bag[key] = value

    if isinstance(set_block, dict):
        for key, value in set_block.items():
            if str(key) == "titles":
                bag["titles"] = _normalize_titles_value(value)
                continue
            bag[str(key)] = value

    if isinstance(remove_block, list):
        for key in remove_block:
            name = str(key).strip()
            if name:
                if "." not in name:
                    bag.pop(name, None)
                    continue
                parts = [part for part in name.split(".") if part]
                if not parts:
                    continue
                parent = bag
                for part in parts[:-1]:
                    next_obj = parent.get(part)
                    if not isinstance(next_obj, dict):
                        parent = {}
                        break
                    parent = next_obj
                if isinstance(parent, dict):
                    parent.pop(parts[-1], None)


def _ensure_character_continuity_system_state(state: Dict[str, Any]) -> Dict[str, Any]:
    continuity = state.get("character_continuity_system_state")
    if not isinstance(continuity, dict):
        continuity = {}

    for source_key, target_key in (
        ("stats", "stats"),
        ("skills", "skills"),
        ("titles", "titles"),
        ("effects", "effects"),
        ("statuses", "statuses"),
        ("resources", "resources"),
        ("classes", "classes"),
        ("ranks", "ranks"),
        ("traits", "traits"),
        ("flags", "flags"),
        ("talents", "talents"),
        ("perks", "perks"),
        ("achievements", "achievements"),
        ("affinities", "affinities"),
        ("reputations", "reputations"),
        ("cooldowns", "cooldowns"),
        ("progression", "progression"),
        ("system_tracking_metadata", "system_tracking_metadata"),
        ("extended_system_data", "extended_system_data"),
    ):
        legacy_value = state.get(source_key)
        if target_key in continuity:
            continue
        if isinstance(legacy_value, (dict, list, str, int, float, bool)):
            continuity[target_key] = legacy_value

    _normalize_titles_in_continuity_state(continuity)
    state["character_continuity_system_state"] = continuity

    stats_family = continuity.get("stats")
    if isinstance(stats_family, dict):
        state["stats"] = stats_family
    skills_family = continuity.get("skills")
    if isinstance(skills_family, dict):
        state["skills"] = skills_family

    return continuity


def _ensure_global_continuity_system_state(state: Dict[str, Any]) -> Dict[str, Any]:
    continuity = state.get("global_continuity_system_state")
    if not isinstance(continuity, dict):
        continuity = {}

    legacy_run_stats = state.get("run_stats")
    if isinstance(legacy_run_stats, dict) and "stats" not in continuity:
        continuity["stats"] = legacy_run_stats

    legacy_run_skills = state.get("run_skills")
    if isinstance(legacy_run_skills, dict) and "skills" not in continuity:
        continuity["skills"] = legacy_run_skills

    legacy_run_bags = state.get("run_bags")
    if isinstance(legacy_run_bags, dict) and "bags" not in continuity:
        continuity["bags"] = legacy_run_bags

    legacy_global_bags = state.get("global_bags")
    if isinstance(legacy_global_bags, dict) and "bags" not in continuity:
        continuity["bags"] = legacy_global_bags

    _normalize_titles_in_continuity_state(continuity)
    state["global_continuity_system_state"] = continuity

    stats_family = continuity.get("stats")
    if isinstance(stats_family, dict):
        state["run_stats"] = stats_family
    skills_family = continuity.get("skills")
    if isinstance(skills_family, dict):
        state["run_skills"] = skills_family

    return continuity


def _apply_character_continuity_system_updates(book_root: Path, patch: Dict[str, Any]) -> None:
    updates = patch.get("character_continuity_system_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        return
    ensure_character_index(book_root)
    for update in updates:
        if not isinstance(update, dict):
            continue
        char_id = str(update.get("character_id") or "").strip()
        if not char_id:
            continue
        state_path = resolve_character_state_path(book_root, char_id)
        if state_path is None:
            state_path = create_character_state_path(book_root, char_id)
        try:
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        except json.JSONDecodeError:
            state = {}
        if not isinstance(state, dict):
            state = {}

        continuity = _ensure_character_continuity_system_state(state)
        _apply_bag_updates(continuity, update)
        state["character_continuity_system_state"] = continuity

        state.setdefault("history", [])
        if isinstance(state.get("history"), list):
            note = update.get("reason")
            chapter = _maybe_int(update.get("chapter"))
            scene = _maybe_int(update.get("scene"))
            entry = {"changes": ["continuity_system_state_updated"]}
            if isinstance(note, str) and note.strip():
                entry["notes"] = note.strip()
            if chapter is not None:
                entry["chapter"] = chapter
            if scene is not None:
                entry["scene"] = scene
            state["history"].append(entry)
            if chapter is not None and scene is not None:
                state["last_touched"] = {"chapter": chapter, "scene": scene}

        state["updated_at"] = _now_iso()
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")


def _apply_global_continuity_system_updates(state: Dict[str, Any], patch: Dict[str, Any]) -> None:
    updates = patch.get("global_continuity_system_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        updates = []

    legacy_stat = patch.get("run_stat_updates") if isinstance(patch, dict) else None
    if isinstance(legacy_stat, dict):
        updates = list(updates)
        updates.append({"set": {"stats": legacy_stat.get("set", {})}, "delta": {"stats": legacy_stat.get("delta", {})}})

    legacy_skill = patch.get("run_skill_updates") if isinstance(patch, dict) else None
    if isinstance(legacy_skill, dict):
        updates = list(updates)
        updates.append({"set": {"skills": legacy_skill.get("set", {})}, "delta": {"skills": legacy_skill.get("delta", {})}})

    continuity = _ensure_global_continuity_system_state(state)
    for update in updates:
        if isinstance(update, dict):
            _apply_bag_updates(continuity, update)

    state["global_continuity_system_state"] = continuity


def _apply_character_stat_updates(book_root: Path, patch: Dict[str, Any]) -> None:
    _apply_character_continuity_system_updates(book_root, patch)


def _apply_run_stat_updates(state: Dict[str, Any], patch: Dict[str, Any]) -> None:
    _apply_global_continuity_system_updates(state, patch)


def _summary_from_state(state: Dict[str, Any]) -> Dict[str, List[str]]:
    if not isinstance(state, dict):
        return {
            "last_scene": [],
            "chapter_so_far": [],
            "story_so_far": [],
            "key_facts_ring": [],
            "must_stay_true": [],
            "pending_story_rollups": [],
        }
    summary = state.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    return {
        "last_scene": _summary_list(summary.get("last_scene")),
        "chapter_so_far": _summary_list(summary.get("chapter_so_far")),
        "story_so_far": _summary_list(summary.get("story_so_far")),
        "key_facts_ring": _summary_list(summary.get("key_facts_ring")),
        "must_stay_true": _summary_list(summary.get("must_stay_true")),
        "pending_story_rollups": _summary_list(summary.get("pending_story_rollups")),
    }


def _merge_summary_update(state: Dict[str, Any], summary_update: Dict[str, Any], chapter_end: bool = False) -> None:
    summary = _summary_from_state(state)

    last_scene = _summary_list(summary_update.get("last_scene"))
    if last_scene:
        summary["last_scene"] = last_scene

    chapter_add = _summary_list(summary_update.get("chapter_so_far_add"))
    if chapter_add:
        summary["chapter_so_far"] = (summary.get("chapter_so_far", []) + chapter_add)[-SUMMARY_CHAPTER_SO_FAR_CAP:]

    pending = _summary_list(summary.get("pending_story_rollups"))
    story_add = _summary_list(summary_update.get("story_so_far_add"))
    if chapter_end:
        if pending or story_add:
            summary["story_so_far"] = (
                summary.get("story_so_far", []) + pending + story_add
            )[-SUMMARY_STORY_SO_FAR_CAP:]
        summary["pending_story_rollups"] = []
    else:
        if story_add:
            summary["pending_story_rollups"] = (pending + story_add)[-SUMMARY_STORY_SO_FAR_CAP:]
        else:
            summary["pending_story_rollups"] = pending

    key_events = _summary_list(summary_update.get("key_events"))
    must_stay_true = _summary_list(summary_update.get("must_stay_true"))
    if key_events or must_stay_true:
        ring = summary.get("key_facts_ring", []) + key_events + must_stay_true
        summary["key_facts_ring"] = _dedupe_preserve(ring)[-SUMMARY_KEY_FACTS_CAP:]

    if must_stay_true:
        merged_invariants = summary.get("must_stay_true", []) + must_stay_true
        summary["must_stay_true"] = _dedupe_preserve(merged_invariants)[-SUMMARY_MUST_STAY_TRUE_CAP:]

    state["summary"] = summary


def _apply_state_patch(state: Dict[str, Any], patch: Dict[str, Any], chapter_end: bool = False) -> Dict[str, Any]:
    _apply_run_stat_updates(state, patch)

    world_updates = patch.get("world_updates")
    if world_updates is None and isinstance(patch.get("world"), dict):
        world_updates = patch.get("world")
    if isinstance(world_updates, dict):
        world = state.get("world", {}) if isinstance(state.get("world", {}), dict) else {}
        for key, value in world_updates.items():
            world[key] = value
        state["world"] = world

    thread_updates = patch.get("thread_updates")
    if isinstance(thread_updates, list):
        world = state.get("world", {}) if isinstance(state.get("world", {}), dict) else {}
        world["open_threads"] = thread_updates
        state["world"] = world

    summary_update = patch.get("summary_update")
    if isinstance(summary_update, dict):
        _merge_summary_update(state, summary_update, chapter_end=chapter_end)
    else:
        if chapter_end:
            _merge_summary_update(state, {}, chapter_end=True)
        if "summary" not in state:
            state["summary"] = _summary_from_state(state)

    delta = patch.get("duplication_warnings_in_row_delta")
    if isinstance(delta, int):
        current = int(state.get("duplication_warnings_in_row", 0) or 0)
        state["duplication_warnings_in_row"] = max(0, current + delta)

    return state


def _apply_character_updates(book_root: Path, patch: Dict[str, Any], chapter_num: int, scene_num: int) -> None:
    updates = patch.get("character_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        return
    characters_dir = book_root / "draft" / "context" / "characters"
    characters_dir.mkdir(parents=True, exist_ok=True)
    ensure_character_index(book_root)
    for update in updates:
        if not isinstance(update, dict):
            continue
        char_id = str(update.get("character_id") or "").strip()
        if not char_id:
            continue
        state_path = resolve_character_state_path(book_root, char_id)
        if state_path is None:
            state_path = create_character_state_path(book_root, char_id)
        state: Dict[str, Any] = {
            "schema_version": "1.0",
            "character_id": char_id,
            "inventory": [],
            "containers": [],
            "invariants": [],
            "history": [],
        }
        if state_path.exists():
            try:
                loaded = json.loads(state_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    state.update(loaded)
            except json.JSONDecodeError:
                pass

        chapter = int(update.get("chapter", chapter_num) or chapter_num)
        scene = int(update.get("scene", scene_num) or scene_num)

        inventory = update.get("inventory")
        if isinstance(inventory, list):
            state["inventory"] = inventory
        containers = update.get("containers")
        if isinstance(containers, list):
            state["containers"] = containers

        invariants_add = update.get("invariants_add")
        if isinstance(invariants_add, list):
            existing = state.get("invariants", [])
            if not isinstance(existing, list):
                existing = []
            combined = existing + [str(item) for item in invariants_add if str(item).strip()]
            deduped = []
            seen = set()
            for item in combined:
                key = str(item).strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                deduped.append(item)
            state["invariants"] = deduped

        history_entry: Dict[str, Any] = {"chapter": chapter, "scene": scene, "changes": []}
        persona_updates = update.get("persona_updates")
        if isinstance(persona_updates, list):
            history_entry["persona_updates"] = [str(item) for item in persona_updates if str(item).strip()]
        notes = update.get("notes")
        if isinstance(notes, str) and notes.strip():
            history_entry["notes"] = notes.strip()
        if isinstance(inventory, list):
            history_entry["changes"].append("inventory_updated")
        if isinstance(containers, list):
            history_entry["changes"].append("containers_updated")
        if history_entry.get("persona_updates") or history_entry.get("notes") or history_entry.get("changes"):
            history = state.get("history", [])
            if not isinstance(history, list):
                history = []
            history.append(history_entry)
            state["history"] = history

        state["last_touched"] = {"chapter": chapter, "scene": scene}
        state["updated_at"] = _now_iso()
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")


def _update_bible(book_root: Path, patch: Dict[str, Any]) -> None:
    world_updates = patch.get("world_updates")
    if not isinstance(world_updates, dict):
        return
    recent_facts = world_updates.get("recent_facts")
    if not isinstance(recent_facts, list):
        return
    lines = [str(item).strip() for item in recent_facts if str(item).strip()]
    if not lines:
        return
    bible_path = book_root / "draft" / "context" / "bible.md"
    existing = ""
    if bible_path.exists():
        existing = bible_path.read_text(encoding="utf-8")
    if existing and not existing.endswith("\n"):
        existing += "\n"
    update = "\n".join([f"- {item}" for item in lines]) + "\n"
    bible_path.write_text(existing + update, encoding="utf-8")


def _rollup_chapter_summary(book_root: Path, state: Dict[str, Any], chapter_num: int) -> None:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}"
    if not chapter_dir.exists():
        return

    key_events: List[str] = []
    must_stay_true: List[str] = []
    for meta_path in sorted(chapter_dir.glob("scene_*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        key_events.extend(_summary_list(meta.get("key_events")))
        must_stay_true.extend(_summary_list(meta.get("must_stay_true")))

    summary = _summary_from_state(state)
    chapter_summary = _dedupe_preserve(key_events + must_stay_true)
    if chapter_summary:
        summary["story_so_far"] = (summary.get("story_so_far", []) + chapter_summary)[-SUMMARY_STORY_SO_FAR_CAP:]
    summary["chapter_so_far"] = []
    state["summary"] = summary

    summaries_dir = book_root / "draft" / "context" / "chapter_summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summaries_dir / f"ch_{chapter_num:03d}.json"
    payload = {
        "chapter": chapter_num,
        "key_events": _dedupe_preserve(key_events),
        "must_stay_true": _dedupe_preserve(must_stay_true),
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _find_chapter_outline(outline: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
    chapters = outline.get("chapters", []) if isinstance(outline, dict) else []
    if isinstance(chapters, list):
        for entry in chapters:
            if not isinstance(entry, dict):
                continue
            chapter_id = entry.get("chapter_id")
            try:
                chapter_id_int = int(chapter_id)
            except (TypeError, ValueError):
                continue
            if chapter_id_int == chapter_num:
                return entry
    return {}


def _section_title(section: Dict[str, Any], index: int) -> str:
    title = str(section.get("title", "")).strip()
    if title:
        return title
    return f"Section {index}"


def _scene_id_from_obj(scene_obj: Dict[str, Any], fallback: int) -> int:
    for key in ("scene_id", "beat_id", "id"):
        value = scene_obj.get(key)
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return fallback


def _compile_chapter_markdown(book_root: Path, outline: Dict[str, Any], chapter_num: int) -> Path:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    chapter = _find_chapter_outline(outline, chapter_num)
    chapter_title = str(chapter.get("title", "")).strip() if chapter else ""
    if chapter_title:
        header = f"Chapter {chapter_num}: {chapter_title}"
    else:
        header = f"Chapter {chapter_num}"

    sections = chapter.get("sections", []) if isinstance(chapter, dict) else []
    if not isinstance(sections, list) or not sections:
        fallback_scenes = []
        if isinstance(chapter, dict):
            raw = chapter.get("scenes") or chapter.get("beats") or []
            if isinstance(raw, list):
                fallback_scenes = raw
        sections = [{"section_id": 1, "title": "", "scenes": fallback_scenes}]

    blocks: List[str] = [f"# {header}"]
    for idx_section, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            continue
        blocks.append(f"## {_section_title(section, idx_section)}")
        scenes = section.get("scenes", [])
        if not isinstance(scenes, list):
            scenes = []
        if not scenes:
            blocks.append("[No scenes listed for this section]")
            continue
        for idx_scene, scene_obj in enumerate(scenes, start=1):
            scene_id = _scene_id_from_obj(scene_obj, idx_scene)
            scene_path = chapter_dir / f"scene_{scene_id:03d}.md"
            if scene_path.exists():
                scene_text = scene_path.read_text(encoding="utf-8").strip()
                blocks.append(scene_text)
            else:
                blocks.append(f"[Missing scene {scene_id:03d}]")

    compiled = "\n\n".join([block for block in blocks if str(block).strip()]) + "\n"

    chapter_file = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.md"
    chapter_file.write_text(compiled, encoding="utf-8")
    return chapter_file

