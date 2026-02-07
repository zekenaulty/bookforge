from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast
import json
import re
import shutil
import time

from bookforge.config.env import load_config, read_env_value, read_int_env
from bookforge.characters import characters_ready, generate_characters, resolve_character_state_path, ensure_character_index, create_character_state_path
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message
from bookforge.memory.continuity import (
    ContinuityPack,
    continuity_pack_path,
    load_style_anchor,
    save_continuity_pack,
    save_style_anchor,
    style_anchor_path,
)
from bookforge.memory.durable_state import (
    ensure_durable_state_files,
    load_item_registry,
    load_plot_devices,
)
from bookforge.phases.plan import plan_scene
from bookforge.prompt.renderer import render_template_file
from bookforge.prompt.system import load_system_prompt
from bookforge.util.paths import repo_root
from bookforge.util.json_extract import extract_json
from bookforge.util.schema import validate_json


DEFAULT_WRITE_MAX_TOKENS = 73728
DEFAULT_LINT_MAX_TOKENS = 147456
DEFAULT_REPAIR_MAX_TOKENS = 147456
DEFAULT_STATE_REPAIR_MAX_TOKENS = 147456
DEFAULT_CONTINUITY_MAX_TOKENS = 147456
DEFAULT_PREFLIGHT_MAX_TOKENS = 147456
DEFAULT_STYLE_ANCHOR_MAX_TOKENS = 32768
DEFAULT_EMPTY_RESPONSE_RETRIES = 2
DEFAULT_REQUEST_ERROR_RETRIES = 1
DEFAULT_REQUEST_ERROR_BACKOFF_SECONDS = 2.0
DEFAULT_REQUEST_ERROR_MAX_SLEEP = 60.0
DEFAULT_JSON_RETRY_COUNT = 1
PAUSE_EXIT_CODE = 75

SUMMARY_CHAPTER_SO_FAR_CAP = 20
SUMMARY_KEY_FACTS_CAP = 25
SUMMARY_MUST_STAY_TRUE_CAP = 20
SUMMARY_STORY_SO_FAR_CAP = 40


def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _write_max_tokens() -> int:
    return _int_env("BOOKFORGE_WRITE_MAX_TOKENS", DEFAULT_WRITE_MAX_TOKENS)


def _lint_max_tokens() -> int:
    return _int_env("BOOKFORGE_LINT_MAX_TOKENS", DEFAULT_LINT_MAX_TOKENS)


def _repair_max_tokens() -> int:
    return _int_env("BOOKFORGE_REPAIR_MAX_TOKENS", DEFAULT_REPAIR_MAX_TOKENS)


def _state_repair_max_tokens() -> int:
    return _int_env("BOOKFORGE_STATE_REPAIR_MAX_TOKENS", DEFAULT_STATE_REPAIR_MAX_TOKENS)


def _continuity_max_tokens() -> int:
    return _int_env("BOOKFORGE_CONTINUITY_MAX_TOKENS", DEFAULT_CONTINUITY_MAX_TOKENS)


def _preflight_max_tokens() -> int:
    return _int_env("BOOKFORGE_PREFLIGHT_MAX_TOKENS", DEFAULT_PREFLIGHT_MAX_TOKENS)

def _style_anchor_max_tokens() -> int:
    return _int_env("BOOKFORGE_STYLE_ANCHOR_MAX_TOKENS", DEFAULT_STYLE_ANCHOR_MAX_TOKENS)


def _empty_response_retries() -> int:
    return max(0, _int_env("BOOKFORGE_EMPTY_RESPONSE_RETRIES", DEFAULT_EMPTY_RESPONSE_RETRIES))


def _request_error_retries() -> int:
    return max(0, _int_env("BOOKFORGE_REQUEST_ERROR_RETRIES", DEFAULT_REQUEST_ERROR_RETRIES))


def _json_retry_count() -> int:
    return max(0, _int_env("BOOKFORGE_JSON_RETRY_COUNT", DEFAULT_JSON_RETRY_COUNT))




def _lint_mode() -> str:
    raw = read_env_value("BOOKFORGE_LINT_MODE")
    if raw is None:
        raw = "warn"
    raw = str(raw).strip().lower()
    if raw in {"strict", "warn", "off"}:
        return raw
    return "warn"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _status(message: str) -> None:
    print(f"[bookforge] {message}", flush=True)


def _resolve_template(book_root: Path, name: str) -> Path:
    book_template = book_root / "prompts" / "templates" / name
    if book_template.exists():
        return book_template
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / name


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _durable_state_context(book_root: Path) -> Dict[str, Any]:
    ensure_durable_state_files(book_root)
    return {
        "item_registry": load_item_registry(book_root),
        "plot_devices": load_plot_devices(book_root),
    }


def _response_truncated(response: LLMResponse) -> bool:
    raw = response.raw
    if not isinstance(raw, dict):
        return False
    if response.provider == "gemini":
        candidates = raw.get("candidates", [])
        if not candidates:
            return False
        finish = candidates[0].get("finishReason")
        return str(finish).upper() == "MAX_TOKENS"
    if response.provider == "openai":
        choice = raw.get("choices", [{}])[0]
        finish = choice.get("finish_reason")
        return str(finish).lower() == "length"
    return False




def _normalize_lint_report(report: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(report)
    if "schema_version" not in normalized:
        normalized["schema_version"] = "1.0"

    status = normalized.get("status")
    if not status:
        passed = normalized.get("pass")
        if isinstance(passed, bool):
            normalized["status"] = "pass" if passed else "fail"

    issues: List[Dict[str, Any]] = []
    raw_issues = normalized.get("issues")
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if isinstance(item, dict) and item.get("message"):
                issues.append(item)
            elif item is not None:
                issues.append({"code": "issue", "message": str(item)})

    violations = normalized.get("violations")
    if isinstance(violations, list):
        for item in violations:
            if item is not None:
                issues.append({"code": "violation", "message": str(item), "severity": "error"})

    warnings = normalized.get("warnings")
    if isinstance(warnings, list):
        for item in warnings:
            if item is not None:
                issues.append({"code": "warning", "message": str(item), "severity": "warning"})

    if not isinstance(normalized.get("issues"), list) or issues:
        normalized["issues"] = issues

    if "status" not in normalized or not normalized.get("status"):
        normalized["status"] = "fail" if normalized.get("issues") else "pass"

    return normalized


def _extract_json(text: str) -> Dict[str, Any]:
    data = extract_json(text, label="Response")
    if not isinstance(data, dict):
        raise ValueError("Response JSON must be an object.")
    return data


def _strip_compliance_block(text: str) -> str:
    if not re.match(r"^COMPLIANCE\s*:", text.strip(), flags=re.IGNORECASE):
        return text
    match = re.search(r"\bPROSE\s*:\s*", text, re.IGNORECASE)
    if match:
        return text[match.end():].strip()
    parts = re.split(r"\n\s*\n", text, maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return ""


def _extract_prose_and_patch(text: str) -> Tuple[str, Dict[str, Any]]:
    match = None
    for candidate in re.finditer(r"STATE\s*_(?:OKPATCH|PATCH)\s*:\s*", text, re.IGNORECASE):
        match = candidate
    if not match:
        return _extract_prose_and_patch_fallback(text)
    prose_block = text[:match.start()].strip()
    patch_block = text[match.end():].strip()
    prose_block = _strip_compliance_block(prose_block)
    prose = re.sub(r"^PROSE\s*:\s*", "", prose_block, flags=re.IGNORECASE).strip()
    if not prose:
        prose = prose_block.strip()
    patch = _extract_json(patch_block)
    if "schema_version" not in patch:
        patch["schema_version"] = "1.0"
    return prose, patch


def _extract_prose_and_patch_fallback(text: str) -> Tuple[str, Dict[str, Any]]:
    fence_matches = list(re.finditer(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE))
    if fence_matches:
        match = fence_matches[-1]
        patch_block = match.group(1).strip()
        prose_block = text[:match.start()].strip()
        prose_block = _strip_compliance_block(prose_block)
        prose = re.sub(r"^PROSE\s*:\s*", "", prose_block, flags=re.IGNORECASE).strip()
        if not prose:
            prose = prose_block.strip()
        patch = _extract_json(patch_block)
        if "schema_version" not in patch:
            patch["schema_version"] = "1.0"
        return prose, patch

    match = re.search(r"(\{[\s\S]*\})\s*$", text)
    if match:
        patch_block = match.group(1).strip()
        prose_block = text[:match.start()].strip()
        prose_block = _strip_compliance_block(prose_block)
        prose = re.sub(r"^PROSE\s*:\s*", "", prose_block, flags=re.IGNORECASE).strip()
        if not prose:
            prose = prose_block.strip()
        patch = _extract_json(patch_block)
        if "schema_version" not in patch:
            patch["schema_version"] = "1.0"
        return prose, patch

    raise ValueError(
        "Missing STATE_PATCH/STATE_OKPATCH block in response (searched for explicit marker, fenced JSON, or trailing JSON)."
    )


def _parse_until(value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not value:
        return None, None
    parts = [part.strip() for part in value.split(":") if part.strip()]
    if len(parts) == 2 and parts[0].lower() == "chapter":
        return int(parts[1]), None
    if len(parts) == 4 and parts[0].lower() == "chapter" and parts[2].lower() == "scene":
        return int(parts[1]), int(parts[3])
    raise ValueError("Invalid --until value. Expected chapter:N or chapter:N:scene:M.")


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

def _last_touched_from_character_state(state: Dict[str, Any]) -> Tuple[int, int]:
    if isinstance(state.get("last_touched"), dict):
        chapter = _maybe_int(state.get("last_touched", {}).get("chapter"))
        scene = _maybe_int(state.get("last_touched", {}).get("scene"))
        if chapter is not None and scene is not None:
            return chapter, scene

    history = state.get("history")
    if isinstance(history, list):
        for entry in reversed(history):
            if not isinstance(entry, dict):
                continue
            chapter = _maybe_int(entry.get("chapter"))
            scene = _maybe_int(entry.get("scene"))
            if chapter is not None and scene is not None:
                return chapter, scene
    return 0, 0


def _snapshot_character_states_before_preflight(
    book_root: Path,
    scene_card: Dict[str, Any],
) -> List[Path]:
    cast_ids = scene_card.get("cast_present_ids", []) if isinstance(scene_card, dict) else []
    if not isinstance(cast_ids, list):
        cast_ids = []
    cast_ids = [str(item) for item in cast_ids if str(item).strip()]
    if not cast_ids:
        return []

    history_dir = book_root / "draft" / "context" / "characters" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    ensure_character_index(book_root)

    snapshots: List[Path] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    for char_id in cast_ids:
        state_path = resolve_character_state_path(book_root, char_id)
        if state_path is None or not state_path.exists():
            continue
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(loaded, dict):
            continue

        touched_ch, touched_sc = _last_touched_from_character_state(loaded)
        prefix = f"ch{touched_ch:03d}_sc{touched_sc:03d}_"
        candidate = history_dir / f"{prefix}{state_path.name}"
        if candidate.exists():
            candidate = history_dir / f"{prefix}{stamp}_{state_path.name}"
        shutil.copyfile(state_path, candidate)
        snapshots.append(candidate)
    return snapshots
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


def _coerce_summary_update(patch: Dict[str, Any]) -> None:
    summary_update = patch.get("summary_update")
    if not isinstance(summary_update, dict):
        return
    for key in (
        "last_scene",
        "key_events",
        "must_stay_true",
        "chapter_so_far_add",
        "story_so_far_add",
        "threads_touched",
    ):
        if key in summary_update:
            summary_update[key] = _summary_list(summary_update.get(key))


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

def _coerce_character_updates(patch: Dict[str, Any]) -> None:
    updates = patch.get("character_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        return
    for update in updates:
        if not isinstance(update, dict):
            continue
        for key in ("persona_updates", "invariants_add"):
            if key in update:
                update[key] = _summary_list(update.get(key))

def _fill_character_update_context(patch: Dict[str, Any], scene_card: Dict[str, Any]) -> None:
    updates = patch.get("character_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        return
    chapter = _maybe_int(scene_card.get("chapter")) if isinstance(scene_card, dict) else None
    scene = _maybe_int(scene_card.get("scene")) if isinstance(scene_card, dict) else None
    for update in updates:
        if not isinstance(update, dict):
            continue
        if "chapter" not in update and chapter is not None:
            update["chapter"] = chapter
        if "scene" not in update and scene is not None:
            update["scene"] = scene


def _fill_character_continuity_update_context(patch: Dict[str, Any], scene_card: Dict[str, Any]) -> None:
    updates = patch.get("character_continuity_system_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        return
    chapter = _maybe_int(scene_card.get("chapter")) if isinstance(scene_card, dict) else None
    scene = _maybe_int(scene_card.get("scene")) if isinstance(scene_card, dict) else None
    for update in updates:
        if not isinstance(update, dict):
            continue
        if "chapter" not in update and chapter is not None:
            update["chapter"] = chapter
        if "scene" not in update and scene is not None:
            update["scene"] = scene
def _coerce_stat_updates(patch: Dict[str, Any]) -> None:
    if not isinstance(patch, dict):
        return

    continuity_reserved = {
        "character_id",
        "set",
        "delta",
        "remove",
        "reason",
        "reason_category",
        "expected_before",
        "chapter",
        "scene",
        "notes",
    }
    known_families = (
        "stats",
        "skills",
        "titles",
        "effects",
        "statuses",
        "resources",
        "classes",
        "ranks",
        "traits",
        "flags",
        "talents",
        "perks",
        "achievements",
        "affinities",
        "reputations",
        "cooldowns",
        "progression",
        "system_tracking_metadata",
        "extended_system_data",
    )

    def _ensure_update_dict(update: Dict[str, Any]) -> None:
        if "set" in update and not isinstance(update.get("set"), dict):
            update["set"] = {}
        if "delta" in update and not isinstance(update.get("delta"), dict):
            update["delta"] = {}
        if "remove" in update:
            update["remove"] = _summary_list(update.get("remove"))
        update.setdefault("set", {})
        if not isinstance(update.get("set"), dict):
            update["set"] = {}

    def _is_dynamic_value(value: Any) -> bool:
        return isinstance(value, (dict, list, str, int, float, bool))

    def _fold_top_level_mechanics_into_set(update: Dict[str, Any]) -> None:
        set_block = update.get("set")
        if not isinstance(set_block, dict):
            set_block = {}
            update["set"] = set_block
        for key, value in list(update.items()):
            if key in continuity_reserved:
                continue
            if _is_dynamic_value(value):
                set_block[key] = value
                update.pop(key, None)
        for family in known_families:
            if family in update and _is_dynamic_value(update.get(family)):
                set_block[family] = update.get(family)

    def _normalize_titles_in_update(update: Dict[str, Any]) -> None:
        for block_key in ("set", "delta"):
            block = update.get(block_key)
            if not isinstance(block, dict):
                continue
            if "titles" in block:
                block["titles"] = _normalize_titles_value(block.get("titles"))

    char_updates = patch.get("character_continuity_system_updates")
    if not isinstance(char_updates, list):
        char_updates = []
        patch["character_continuity_system_updates"] = char_updates

    global_updates = patch.get("global_continuity_system_updates")
    if not isinstance(global_updates, list):
        global_updates = []
        patch["global_continuity_system_updates"] = global_updates

    for update in char_updates:
        if isinstance(update, dict):
            _ensure_update_dict(update)
            _fold_top_level_mechanics_into_set(update)
            _normalize_titles_in_update(update)

    for update in global_updates:
        if isinstance(update, dict):
            _ensure_update_dict(update)
            _fold_top_level_mechanics_into_set(update)
            _normalize_titles_in_update(update)

    legacy_char_stat = patch.get("character_stat_updates")
    if isinstance(legacy_char_stat, list):
        for update in legacy_char_stat:
            if not isinstance(update, dict):
                continue
            char_id = str(update.get("character_id") or "").strip()
            if not char_id:
                continue
            target = _upsert_continuity_update(char_updates, char_id)
            _coerce_legacy_family_update_into_continuity(target, update, "stats")

    legacy_char_skill = patch.get("character_skill_updates")
    if isinstance(legacy_char_skill, list):
        for update in legacy_char_skill:
            if not isinstance(update, dict):
                continue
            char_id = str(update.get("character_id") or "").strip()
            if not char_id:
                continue
            target = _upsert_continuity_update(char_updates, char_id)
            _coerce_legacy_family_update_into_continuity(target, update, "skills")

    legacy_run_stat = patch.get("run_stat_updates")
    if isinstance(legacy_run_stat, dict):
        target = _upsert_global_continuity_update(global_updates)
        _coerce_legacy_family_update_into_continuity(target, legacy_run_stat, "stats")

    legacy_run_skill = patch.get("run_skill_updates")
    if isinstance(legacy_run_skill, dict):
        target = _upsert_global_continuity_update(global_updates)
        _coerce_legacy_family_update_into_continuity(target, legacy_run_skill, "skills")

    for update in char_updates:
        if isinstance(update, dict):
            _ensure_update_dict(update)
            _normalize_titles_in_update(update)

    for update in global_updates:
        if isinstance(update, dict):
            _ensure_update_dict(update)
            _normalize_titles_in_update(update)

def _normalize_stat_key(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
    return cleaned.strip("_")


def _parse_stat_value(raw: str) -> Any:
    if raw is None:
        return None
    text = str(raw).strip()
    locked = "locked" in text.lower()
    text = re.sub(r"\(.*?\)", "", text).strip()
    if "/" in text:
        parts = [part.strip() for part in text.split("/", 1)]
        if len(parts) == 2 and parts[0].replace(".", "", 1).isdigit() and parts[1].replace(".", "", 1).isdigit():
            current = float(parts[0]) if "." in parts[0] else int(parts[0])
            maximum = float(parts[1]) if "." in parts[1] else int(parts[1])
            result = {"current": current, "max": maximum}
            if locked:
                result["locked"] = True
            return result
    numeric = text.replace("%", "").strip()
    if numeric.replace(".", "", 1).isdigit():
        value = float(numeric) if "." in numeric else int(numeric)
        if text.endswith("%"):
            value = f"{value}%"
        if locked:
            return {"value": value, "locked": True}
        return value
    return text


def _upsert_continuity_update(updates: list, character_id: str) -> dict:
    for update in updates:
        if isinstance(update, dict) and str(update.get("character_id") or "") == character_id:
            return update
    new_item = {"character_id": character_id, "set": {}, "delta": {}}
    updates.append(new_item)
    return new_item


def _upsert_global_continuity_update(updates: list) -> dict:
    for update in updates:
        if isinstance(update, dict):
            return update
    new_item = {"set": {}, "delta": {}}
    updates.append(new_item)
    return new_item


def _merge_continuity_update_block(target: Dict[str, Any], key: str, payload: Any) -> None:
    if payload is None:
        return
    if isinstance(payload, dict):
        target.setdefault(key, {})
        existing = target.get(key)
        if not isinstance(existing, dict):
            target[key] = dict(payload)
            return
        for sub_key, sub_value in payload.items():
            existing[sub_key] = sub_value
        target[key] = existing
        return
    target[key] = payload


def _coerce_legacy_family_update_into_continuity(target: Dict[str, Any], legacy_update: Dict[str, Any], family_key: str) -> None:
    target.setdefault("set", {})
    target.setdefault("delta", {})

    direct = legacy_update.get(family_key)
    if isinstance(direct, (dict, list, str, int, float)):
        _merge_continuity_update_block(target["set"], family_key, direct)

    set_block = legacy_update.get("set")
    if isinstance(set_block, dict):
        _merge_continuity_update_block(target["set"], family_key, set_block)

    delta_block = legacy_update.get("delta")
    if isinstance(delta_block, dict):
        _merge_continuity_update_block(target["delta"], family_key, delta_block)

    reason = legacy_update.get("reason")
    if isinstance(reason, str) and reason.strip() and not target.get("reason"):
        target["reason"] = reason.strip()


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

def _migrate_numeric_invariants(patch: Dict[str, Any]) -> None:
    updates = patch.get("character_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        return

    continuity_updates = patch.setdefault("character_continuity_system_updates", [])
    if not isinstance(continuity_updates, list):
        continuity_updates = []
        patch["character_continuity_system_updates"] = continuity_updates

    family_aliases = {
        "title": "titles",
        "titles": "titles",
        "effect": "effects",
        "effects": "effects",
        "status": "statuses",
        "statuses": "statuses",
        "resource": "resources",
        "resources": "resources",
        "class": "classes",
        "classes": "classes",
        "rank": "ranks",
        "ranks": "ranks",
    }

    for update in updates:
        if not isinstance(update, dict):
            continue
        char_id = str(update.get("character_id") or "").strip()
        if not char_id:
            continue
        invariants = update.get("invariants_add")
        if not isinstance(invariants, list):
            continue

        target = _upsert_continuity_update(continuity_updates, char_id)
        target.setdefault("set", {})

        kept = []
        for item in invariants:
            text = str(item).strip()
            typed_match = re.match(r"^(stat|skill)\s*:\s*([^=]+?)\s*=\s*(.+)$", text, re.IGNORECASE)
            if typed_match:
                kind = typed_match.group(1).lower()
                key = _normalize_stat_key(typed_match.group(2))
                value = _parse_stat_value(typed_match.group(3))
                if not key:
                    kept.append(item)
                    continue
                family_key = "stats" if kind == "stat" else "skills"
                family = target["set"].get(family_key)
                if not isinstance(family, dict):
                    family = {}
                family[key] = value
                target["set"][family_key] = family
                continue

            generic_match = re.match(r"^([a-zA-Z_\- ]+)\s*:\s*(.+)$", text)
            if generic_match:
                prefix = _normalize_stat_key(generic_match.group(1))
                value = generic_match.group(2).strip()
                mapped_family = family_aliases.get(prefix)
                if mapped_family and value:
                    _append_continuity_list_item(target["set"], mapped_family, value)
                    continue

            kept.append(item)

        update["invariants_add"] = kept

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

def _extract_authoritative_surfaces(prose: str) -> List[Dict[str, Any]]:
    surfaces: List[Dict[str, Any]] = []
    for line_no, raw_line in enumerate(str(prose).splitlines(), start=1):
        text = raw_line.strip()
        if not text:
            continue
        if not (text.startswith("[") and text.endswith("]")):
            continue

        kind = "ui_block"
        if re.match(r"^\[[^\]:]{1,80}:\s*[-+0-9]", text):
            kind = "ui_stat"
        elif text.lower().startswith("[system"):
            kind = "system_notification"
        elif text.lower().startswith("[warning"):
            kind = "system_notification"

        surfaces.append({"line": line_no, "kind": kind, "text": text})
    return surfaces


def _extract_ui_stat_lines(
    prose: str,
    authoritative_surfaces: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    lines: List[Dict[str, Any]] = []
    source_texts: List[str] = []

    if authoritative_surfaces is not None:
        for surface in authoritative_surfaces:
            if not isinstance(surface, dict):
                continue
            text = surface.get("text")
            if isinstance(text, str) and text.strip():
                source_texts.append(text)
    else:
        source_texts = [str(prose)]

    for chunk in source_texts:
        for match in re.finditer(r"\[([^\]:]{1,80}):\s*([0-9]+(?:\.[0-9]+)?)(?:/([0-9]+(?:\.[0-9]+)?))?\s*%?\]", chunk):
            key = match.group(1).strip()
            current_raw = match.group(2)
            max_raw = match.group(3)
            current = float(current_raw) if "." in current_raw else int(current_raw)
            maximum: Any = None
            if max_raw is not None:
                maximum = float(max_raw) if "." in max_raw else int(max_raw)
            lines.append({"key": key, "current": current, "max": maximum})
    return lines


def _stat_key_aliases() -> Dict[str, str]:
    return {
        "critical_hit_rate": "crit_rate",
        "crit_rate": "crit_rate",
        "critical_rate": "crit_rate",
        "hp": "hp",
        "stamina": "stamina",
        "mp": "mp",
        "mana": "mp",
        "level": "level",
    }


def _stat_mismatch_issues(
    prose: str,
    character_states: List[Dict[str, Any]],
    run_stats: Dict[str, Any],
    authoritative_surfaces: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    lines = _extract_ui_stat_lines(prose, authoritative_surfaces)
    if not lines:
        return []

    def _line_matches_stat(line: Dict[str, Any], stat_val: Any) -> bool:
        if isinstance(stat_val, dict):
            current = stat_val.get("current") if isinstance(stat_val.get("current"), (int, float)) else None
            maximum = stat_val.get("max") if isinstance(stat_val.get("max"), (int, float)) else None
            current_match = current is None or current == line["current"]
            max_match = line["max"] is None or maximum is None or maximum == line["max"]
            return current_match and max_match
        if isinstance(stat_val, (int, float)):
            return line["current"] == stat_val
        if isinstance(stat_val, str):
            stripped = stat_val.strip().rstrip("%").strip()
            if stripped.replace(".", "", 1).isdigit():
                numeric = float(stripped) if "." in stripped else int(stripped)
                return line["current"] == numeric
        return False

    aliases = _stat_key_aliases()
    alias_to_indices: Dict[str, List[int]] = {}
    for idx, state in enumerate(character_states):
        if not isinstance(state, dict):
            continue
        alias_values: List[str] = []
        char_id = str(state.get("character_id") or "").strip()
        if char_id:
            alias_values.append(_normalize_stat_key(char_id))
            if char_id.upper().startswith("CHAR_"):
                alias_values.append(_normalize_stat_key(char_id[5:]))
        name = str(state.get("name") or "").strip()
        if name:
            alias_values.append(_normalize_stat_key(name))
        for alias in alias_values:
            if not alias:
                continue
            current = alias_to_indices.get(alias, [])
            if idx not in current:
                current.append(idx)
            alias_to_indices[alias] = current

    sorted_aliases = sorted(alias_to_indices.keys(), key=len, reverse=True)

    def _owner_and_stat_key(raw_key: str) -> Tuple[Optional[List[int]], str]:
        normalized = _normalize_stat_key(raw_key)
        for alias in sorted_aliases:
            token_prefix = alias + "_"
            token_suffix = "_" + alias
            if normalized.startswith(token_prefix):
                stat_key = normalized[len(token_prefix):]
                if stat_key:
                    return alias_to_indices.get(alias), stat_key
            if normalized.endswith(token_suffix):
                stat_key = normalized[: -len(token_suffix)]
                if stat_key:
                    return alias_to_indices.get(alias), stat_key
        return None, normalized

    issues: List[Dict[str, Any]] = []
    for line in lines:
        owner_indices, extracted_key = _owner_and_stat_key(line["key"])
        key = aliases.get(extracted_key, extracted_key)
        key = aliases.get(key, key)

        candidates: List[Tuple[str, Any]] = []
        state_indices = owner_indices if owner_indices is not None else list(range(len(character_states)))
        for idx in state_indices:
            state = character_states[idx]
            if not isinstance(state, dict):
                continue
            continuity = state.get("character_continuity_system_state")
            if isinstance(continuity, dict):
                stats = continuity.get("stats") if isinstance(continuity.get("stats"), dict) else {}
            else:
                stats = state.get("stats") if isinstance(state.get("stats"), dict) else {}
            if key in stats:
                char_id = str(state.get("character_id") or "unknown")
                candidates.append((f"character:{char_id}", stats.get(key)))
        if owner_indices is None and isinstance(run_stats, dict) and key in run_stats:
            candidates.append(("global", run_stats.get(key)))

        if not candidates:
            issues.append({
                "code": "stat_unowned",
                "message": f"UI stat '{line['key']}' not found in character_continuity_system_state/global_continuity_system_state.",
                "severity": "warning",
            })
            continue

        if any(_line_matches_stat(line, value) for _, value in candidates):
            continue

        formatted = ", ".join([f"{source}={value}" for source, value in candidates])
        issues.append({
            "code": "stat_mismatch",
            "message": f"UI stat '{line['key']}' does not match any candidate value ({formatted}).",
            "severity": "warning",
        })
    return issues
def _pov_drift_issues(prose: str, pov: Optional[str]) -> List[Dict[str, Any]]:
    if not pov:
        return []
    pov_key = str(pov).lower()
    if not pov_key.startswith("third"):
        return []
    if re.search(r"\b(I|I'm|I've|I'd|me|my|mine)\b", prose):
        return [{
            "code": "pov_drift",
            "message": "First-person pronouns detected in third-person POV scene.",
            "severity": "warning",
        }]
    return []







def _summary_from_state(state: Dict[str, Any]) -> Dict[str, List[str]]:
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



def _global_continuity_stats(state: Dict[str, Any]) -> Dict[str, Any]:
    continuity = state.get("global_continuity_system_state")
    if isinstance(continuity, dict):
        stats = continuity.get("stats")
        if isinstance(stats, dict):
            return stats
    legacy = state.get("run_stats")
    return legacy if isinstance(legacy, dict) else {}
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


def _contains_any(text: str, terms: List[str]) -> bool:
    for term in terms:
        if not term:
            continue
        if " " in term:
            if term in text:
                return True
        else:
            if re.search(r"\b" + re.escape(term) + r"\b", text):
                return True
    return False


def _heuristic_invariant_issues(
    prose: str,
    summary_update: Dict[str, Any],
    invariants: List[str],
) -> List[Dict[str, Any]]:
    if not invariants:
        return []
    prose_lower = prose.lower()
    observed = prose_lower
    summary_bits: List[str] = []
    for key in ("last_scene", "key_events", "must_stay_true", "chapter_so_far_add", "story_so_far_add"):
        items = summary_update.get(key)
        if isinstance(items, list):
            summary_bits.extend([str(item) for item in items if str(item).strip()])
    if summary_bits:
        observed += " " + " ".join([item.lower() for item in summary_bits])

    objects = ["shard", "blade", "sword", "knife", "dagger", "map", "canister", "oath", "mark"]
    presence = ["present", "here", "carried", "carry", "carrying", "held", "holds", "has", "in his pack", "in his satchel", "on his person"]
    absence = ["gone", "missing", "lost", "destroyed", "shattered", "dissolved", "vanished", "consumed", "erased"]
    physical = ["physical", "solid", "tangible", "carryable"]
    embedded = ["embedded", "bound", "fused", "absorbed", "within him", "in his body", "in his chest"]
    alive = ["alive", "living", "breathing"]
    dead = ["dead", "killed", "slain", "corpse"]

    issues: List[Dict[str, Any]] = []
    for invariant in invariants:
        inv_text = str(invariant).strip().lower()
        if not inv_text:
            continue
        relevant_objects = [obj for obj in objects if obj in inv_text]
        if not relevant_objects:
            continue
        for obj in relevant_objects:
            if obj not in observed:
                continue
            if _contains_any(inv_text, presence) and _contains_any(observed, absence):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests present, prose suggests absent.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, absence) and _contains_any(observed, presence):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests absent, prose suggests present.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, physical) and _contains_any(observed, embedded):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests physical, prose suggests embedded.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, embedded) and _contains_any(observed, physical):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests embedded, prose suggests physical.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, alive) and _contains_any(observed, dead):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests alive, prose suggests dead.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, dead) and _contains_any(observed, alive):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests dead, prose suggests alive.",
                    "severity": "error",
                })
                continue

    milestone_patterns = {
        "shard_bind": [
            r"\b(?:bind(?:s|ing|ed)|bound)\b.{0,40}\bshard\b",
            r"\bshard\b.{0,40}\b(?:bind(?:s|ing|ed)|bound)\b",
            r"\boath\b.{0,40}\bfilament\b",
        ],
        "maps_acquired": [
            r"\bmaps?\b.{0,40}\b(acquire|acquired|retrieve|retrieved|unfurl|unfurled|take|took|get|got)\b",
            r"\b(acquire|retriev|unfurl|take|get)\w*\b.{0,40}\bmaps?\b",
            r"\bcharts?\b",
            r"\bstar[- ]?map\b",
        ],
        "shadow_form_first": [
            r"\bshadow[- ]?form\b",
            r"\bshadow\b.{0,20}\bforms\b",
        ],
    }

    milestones: List[tuple[str, str]] = []
    for invariant in invariants:
        match = re.search(r"milestone\s*:\s*([a-z0-9_\- ]+)\s*=\s*(done|not_yet)", str(invariant), re.IGNORECASE)
        if not match:
            continue
        key = match.group(1).strip().lower().replace("-", "_").replace(" ", "_")
        status = match.group(2).upper()
        if key:
            milestones.append((key, status))

    for key, status in milestones:
        patterns = milestone_patterns.get(key)
        if not patterns:
            token = key.replace("_", " ")
            if token:
                patterns = [r"\b" + re.escape(token) + r"\b"]
        hit = False
        for pattern in patterns or []:
            if re.search(pattern, prose_lower):
                hit = True
                break
        if not hit:
            continue
        if status == "DONE":
            issues.append({
                "code": "milestone_duplicate",
                "message": f"Milestone '{key}' is DONE but appears to be depicted again.",
                "severity": "warning",
            })
        elif status == "NOT_YET":
            issues.append({
                "code": "milestone_future",
                "message": f"Milestone '{key}' is NOT_YET but appears to be depicted early.",
                "severity": "warning",
            })

    invariant_text = " ".join([str(item).lower() for item in invariants])
    if "right" in invariant_text and re.search(r"\bleft\s+(arm|forearm|hand)\b.{0,40}\b(scar|mark|filament|oath|sigil)\b", prose_lower):
        issues.append({
            "code": "arm_side_mismatch",
            "message": "Possible arm-side mismatch: invariants mention right-side mark but prose mentions left-side mark.",
            "severity": "warning",
        })
    if "left" in invariant_text and re.search(r"\bright\s+(arm|forearm|hand)\b.{0,40}\b(scar|mark|filament|oath|sigil)\b", prose_lower):
        issues.append({
            "code": "arm_side_mismatch",
            "message": "Possible arm-side mismatch: invariants mention left-side mark but prose mentions right-side mark.",
            "severity": "warning",
        })

    if "longsword" in invariant_text:
        if any(term in prose_lower for term in ["short-blade", "short blade", "dagger", "knife"]) and "longsword" not in prose_lower:
            issues.append({
                "code": "inventory_mismatch",
                "message": "Possible weapon mismatch: invariants mention longsword but prose emphasizes a different blade.",
                "severity": "warning",
            })
    if any(term in invariant_text for term in ["short-blade", "short blade", "dagger", "knife"]):
        if "longsword" in prose_lower and not any(term in prose_lower for term in ["short-blade", "short blade", "dagger", "knife"]):
            issues.append({
                "code": "inventory_mismatch",
                "message": "Possible weapon mismatch: invariants mention short blade but prose emphasizes a longsword.",
                "severity": "warning",
            })

    mojibake_markers = ["\ufffd", "\u00c3", "\u00c2", "\u00e2\u0080\u0094", "\u00e2\u0080\u0099", "\u00e2\u0080\u009c", "\u00e2\u0080\u009d"]
    if any(marker in prose for marker in mojibake_markers):
        issues.append({
            "code": "encoding_mojibake",
            "message": "Possible encoding/mojibake artifacts detected in prose output.",
            "severity": "warning",
        })

    return issues


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


def _cursor_beyond_target(
    chapter: int,
    scene: int,
    target: Tuple[Optional[int], Optional[int]],
    scene_counts: Dict[int, int],
) -> bool:
    target_chapter, target_scene = target
    if target_chapter is None:
        return False
    if chapter > target_chapter:
        return True
    if chapter < target_chapter:
        return False
    if target_scene is None:
        target_scene = scene_counts.get(target_chapter, 0)
    if target_scene <= 0:
        return False
    return scene > target_scene


def _advance_cursor(
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    chapter: int,
    scene: int,
) -> Tuple[int, int, bool]:
    total_scenes = scene_counts.get(chapter, 0)
    if total_scenes and scene < total_scenes:
        return chapter, scene + 1, False
    if chapter in chapter_order:
        index = chapter_order.index(chapter)
        if index + 1 < len(chapter_order):
            return chapter_order[index + 1], 1, False
    return chapter + 1, 1, True


def _existing_scene_card(state: Dict[str, Any], book_root: Path) -> Optional[Path]:
    plan_data = state.get("plan", {}) if isinstance(state.get("plan"), dict) else {}
    rel_path = plan_data.get("scene_card")
    if not rel_path:
        return None
    path = book_root / rel_path
    if not path.exists():
        return None

    cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
    chapter = int(cursor.get("chapter", 0) or 0)
    scene = int(cursor.get("scene", 0) or 0)
    try:
        card = _load_json(path)
    except Exception:
        return None
    card_chapter = int(card.get("chapter", 0) or 0)
    card_scene = int(card.get("scene", 0) or 0)
    if chapter and scene and (card_chapter != chapter or card_scene != scene):
        return None
    return path



def _author_fragment_path(workspace: Path, author_ref: str) -> Path:
    parts = [part for part in author_ref.split("/") if part]
    if len(parts) != 2:
        raise ValueError("author_ref must look like <author_slug>/vN")
    return workspace / "authors" / parts[0] / parts[1] / "system_fragment.md"


def _maybe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _previous_scene_ref(
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    chapter: int,
    scene: int,
) -> Optional[Tuple[int, int]]:
    if scene > 1:
        return chapter, scene - 1
    if chapter in chapter_order:
        idx = chapter_order.index(chapter)
        if idx > 0:
            prev_chapter = chapter_order[idx - 1]
            prev_count = int(scene_counts.get(prev_chapter, 0) or 0)
            if prev_count > 0:
                return prev_chapter, prev_count
    return None


def _scene_prose_path(book_root: Path, chapter: int, scene: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{chapter:03d}" / f"scene_{scene:03d}.md"


def _read_scene_prose(book_root: Path, chapter: int, scene: int) -> str:
    path = _scene_prose_path(book_root, chapter, scene)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _last_appearance_for_character(
    book_root: Path,
    outline: Dict[str, Any],
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    chapter: int,
    scene: int,
    character_id: str,
) -> Optional[Dict[str, Any]]:
    pointer = _previous_scene_ref(chapter_order, scene_counts, chapter, scene)
    while pointer is not None:
        ref_ch, ref_sc = pointer
        cast_ids = _scene_cast_ids_from_outline(outline, ref_ch, ref_sc)
        if character_id in cast_ids:
            prose = _read_scene_prose(book_root, ref_ch, ref_sc)
            if prose.strip():
                return {
                    "character_id": character_id,
                    "chapter": ref_ch,
                    "scene": ref_sc,
                    "prose": prose,
                }
        pointer = _previous_scene_ref(chapter_order, scene_counts, ref_ch, ref_sc)
    return None


def _build_preflight_context(
    book_root: Path,
    outline: Dict[str, Any],
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    scene_card: Dict[str, Any],
) -> Dict[str, Any]:
    chapter = _maybe_int(scene_card.get("chapter")) or 0
    scene = _maybe_int(scene_card.get("scene")) or 0
    cast_ids = scene_card.get("cast_present_ids", [])
    if not isinstance(cast_ids, list):
        cast_ids = []
    cast_ids = [str(item) for item in cast_ids if str(item).strip()]

    immediate_previous: Dict[str, Any] = {"available": False}
    immediate_cast_ids: List[str] = []
    previous = _previous_scene_ref(chapter_order, scene_counts, chapter, scene)
    if previous is not None:
        prev_ch, prev_sc = previous
        prose = _read_scene_prose(book_root, prev_ch, prev_sc)
        immediate_previous = {
            "available": bool(prose.strip()),
            "chapter": prev_ch,
            "scene": prev_sc,
            "prose": prose,
        }
        immediate_cast_ids = _scene_cast_ids_from_outline(outline, prev_ch, prev_sc)

    cast_last_appearance: List[Dict[str, Any]] = []
    for char_id in cast_ids:
        if char_id in immediate_cast_ids:
            continue
        item = _last_appearance_for_character(
            book_root,
            outline,
            chapter_order,
            scene_counts,
            chapter,
            scene,
            char_id,
        )
        if item:
            cast_last_appearance.append(item)

    return {
        "immediate_previous_scene": immediate_previous,
        "cast_last_appearance": cast_last_appearance,
    }


def _sanitize_preflight_patch(patch: Dict[str, Any]) -> Dict[str, Any]:
    allowed_keys = {
        "schema_version",
        "world_updates",
        "thread_updates",
        "world",
        "canon_updates",
        "character_updates",
        "character_continuity_system_updates",
        "global_continuity_system_updates",
        "character_stat_updates",
        "character_skill_updates",
        "run_stat_updates",
        "run_skill_updates",
        "inventory_alignment_updates",
        "item_registry_updates",
        "plot_device_updates",
        "transfer_updates",
    }
    sanitized: Dict[str, Any] = {}
    for key, value in patch.items():
        if key in allowed_keys:
            sanitized[key] = value
    sanitized.setdefault("schema_version", "1.0")
    return sanitized

def _log_scope(book_root: Path, scene_card: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scope: Dict[str, Any] = {"book_id": book_root.name}
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        if chapter is not None:
            scope["chapter"] = chapter
        scene = _maybe_int(scene_card.get("scene"))
        if scene is not None:
            scope["scene"] = scene
    return scope


def _chat(
    workspace: Path,
    label: str,
    client: LLMClient,
    messages: List[Message],
    model: str,
    temperature: float,
    max_tokens: int,
    log_extra: Optional[Dict[str, Any]] = None,
) -> LLMResponse:
    key_slot = getattr(client, "key_slot", None)
    merged_extra: Dict[str, Any] = {}
    if log_extra:
        merged_extra.update(log_extra)
    if key_slot:
        merged_extra["key_slot"] = key_slot
    extra = merged_extra or None
    request = {"model": model, "temperature": temperature, "max_tokens": max_tokens}
    retries = _empty_response_retries()
    error_retries = _request_error_retries()
    attempt = 0
    error_attempt = 0
    while True:
        try:
            response = client.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        except LLMRequestError as exc:
            if should_log_llm():
                log_llm_error(workspace, f"{label}_error", exc, request=request, messages=messages, extra=extra)
            if exc.status_code in {429, 500, 502, 503, 504} and error_attempt < error_retries:
                delay = exc.retry_after_seconds
                if delay is None:
                    delay = DEFAULT_REQUEST_ERROR_BACKOFF_SECONDS * (2 ** error_attempt)
                delay = min(delay, DEFAULT_REQUEST_ERROR_MAX_SLEEP)
                if delay > 0:
                    time.sleep(delay)
                error_attempt += 1
                continue
            raise
        label_used = label if attempt == 0 else f"{label}_retry{attempt}"
        if should_log_llm():
            log_llm_response(workspace, label_used, response, request=request, messages=messages, extra=extra)
        if str(response.text).strip() or attempt >= retries:
            return response
        attempt += 1

def _write_pause_marker(
    book_root: Path,
    phase: str,
    error: LLMRequestError,
    scene_card: Optional[Dict[str, Any]] = None,
) -> Path:
    context_dir = book_root / "draft" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "book_id": book_root.name,
        "phase": phase,
        "status_code": error.status_code,
        "message": error.message,
        "retry_after_seconds": error.retry_after_seconds,
        "quota_violations": [
            {
                "quota_metric": item.quota_metric,
                "quota_id": item.quota_id,
                "quota_dimensions": item.quota_dimensions,
                "quota_value": item.quota_value,
            }
            for item in error.quota_violations
        ],
        "created_at": _now_iso(),
    }
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        scene = _maybe_int(scene_card.get("scene"))
        if chapter is not None:
            payload["chapter"] = chapter
        if scene is not None:
            payload["scene"] = scene
    pause_path = context_dir / "run_paused.json"
    pause_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return pause_path


def _pause_on_quota(
    book_root: Path,
    state_path: Path,
    state: Optional[Dict[str, Any]],
    phase: str,
    error: LLMRequestError,
    scene_card: Optional[Dict[str, Any]] = None,
) -> None:
    if error.status_code != 429 and not error.quota_violations:
        raise error
    if state is not None:
        try:
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception:
            pass
    _write_pause_marker(book_root, phase, error, scene_card)
    _status(f"Run paused due to quota in phase '{phase}': {error}")
    raise SystemExit(PAUSE_EXIT_CODE)





def _fallback_style_anchor(author_fragment: str) -> str:
    cleaned = re.sub(r"^You are [^.]+\.\s*", "", author_fragment, flags=re.IGNORECASE).strip()
    if cleaned:
        return cleaned
    return "Write in tight third-person limited with concrete sensory detail and forward motion."


def _ensure_style_anchor(
    workspace: Path,
    book_root: Path,
    book: Dict[str, Any],
    system_path: Path,
    client: LLMClient,
    model: str,
) -> str:
    anchor_path = style_anchor_path(book_root)
    existing = load_style_anchor(anchor_path)
    if existing.strip():
        return existing
    author_ref = str(book.get("author_ref", ""))
    fragment_path = _author_fragment_path(workspace, author_ref)
    if not fragment_path.exists():
        raise FileNotFoundError(f"Author fragment not found: {fragment_path}")
    author_fragment = fragment_path.read_text(encoding="utf-8")

    template = _resolve_template(book_root, "style_anchor.md")
    prompt = render_template_file(
        template,
        {
            "author_fragment": author_fragment,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "style_anchor",
        client,
        messages,
        model=model,
        temperature=0.7,
        max_tokens=_style_anchor_max_tokens(),
        log_extra=_log_scope(book_root),
    )
    text = response.text.strip()
    if not text:
        retry_prompt = (
            prompt
            + "\n\nOutput must be non-empty and 200-400 words."
            + " If you are unsure, write 8-12 sentences of neutral prose with no names."
        )
        retry_messages: List[Message] = [
            {"role": "system", "content": system_path.read_text(encoding="utf-8")},
            {"role": "user", "content": retry_prompt},
        ]
        response = _chat(
            workspace,
            "style_anchor_retry",
            client,
            retry_messages,
            model=model,
            temperature=0.7,
            max_tokens=_style_anchor_max_tokens(),
            log_extra=_log_scope(book_root),
        )
        text = response.text.strip()
    if not text:
        text = _fallback_style_anchor(author_fragment)
    if not text:
        raise ValueError("Style anchor generation returned empty output.")
    save_style_anchor(anchor_path, text)
    return text


def _scene_state_preflight(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    scene_card: Dict[str, Any],
    state: Dict[str, Any],
    outline: Dict[str, Any],
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "preflight.md")
    context = _build_preflight_context(book_root, outline, chapter_order, scene_counts, scene_card)
    durable = _durable_state_context(book_root)
    prompt = render_template_file(
        template,
        {
            "scene_card": scene_card,
            "state": state,
            "summary": _summary_from_state(state),
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
            "immediate_previous_scene": context.get("immediate_previous_scene", {}),
            "cast_last_appearance": context.get("cast_last_appearance", []),
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": load_system_prompt(system_path, book_root / "outline" / "outline.json", include_outline=True)},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "scene_state_preflight",
        client,
        messages,
        model=model,
        temperature=0.2,
        max_tokens=_preflight_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            patch = _extract_json(response.text)
            break
        except ValueError as exc:
            if attempt >= retries:
                raise exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return ONLY the JSON object. No prose, no markdown, no commentary.",
            })
            response = _chat(
                workspace,
                f"scene_state_preflight_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.2,
                max_tokens=_preflight_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1

    patch = _sanitize_preflight_patch(patch)
    _coerce_summary_update(patch)
    _coerce_character_updates(patch)
    _coerce_stat_updates(patch)
    _migrate_numeric_invariants(patch)
    _fill_character_update_context(patch, scene_card)
    _fill_character_continuity_update_context(patch, scene_card)
    validate_json(patch, "state_patch")
    return patch

def _generate_continuity_pack(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "continuity_pack.md")
    durable = _durable_state_context(book_root)
    recent_facts = state.get("world", {}).get("recent_facts", [])
    prompt = render_template_file(
        template,
        {
            "state": state,
            "summary": _summary_from_state(state),
            "recent_facts": recent_facts,
            "scene_card": scene_card,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "continuity_pack",
        client,
        messages,
        model=model,
        temperature=0.4,
        max_tokens=_continuity_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            data = _extract_json(response.text)
            break
        except ValueError as exc:
            if attempt >= retries:
                raise exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return ONLY the JSON object. No prose, no markdown, no commentary.",
            })
            response = _chat(
                workspace,
                f"continuity_pack_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.4,
                max_tokens=_continuity_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1
    data = _normalize_continuity_pack(data, scene_card, thread_registry)
    data["summary"] = _summary_from_state(state)
    pack = ContinuityPack.from_dict(data)
    save_continuity_pack(continuity_pack_path(book_root), pack)
    return pack.to_dict()


def _write_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    scene_card: Dict[str, Any],
    continuity_pack: Dict[str, Any],
    state: Dict[str, Any],
    style_anchor: str,
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Tuple[str, Dict[str, Any]]:
    template = _resolve_template(book_root, "write.md")
    durable = _durable_state_context(book_root)
    prompt = render_template_file(
        template,
        {
            "scene_card": scene_card,
            "continuity_pack": continuity_pack,
            "state": state,
            "style_anchor": style_anchor,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": load_system_prompt(system_path, book_root / "outline" / "outline.json", include_outline=True)},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "write_scene",
        client,
        messages,
        model=model,
        temperature=0.7,
        max_tokens=_write_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            prose, patch = _extract_prose_and_patch(response.text)
            break
        except ValueError as exc:
            if attempt >= retries:
                extra = ""
                if _response_truncated(response):
                    extra = f" Model output hit MAX_TOKENS ({_write_max_tokens()}); increase BOOKFORGE_WRITE_MAX_TOKENS."
                raise ValueError(f"{exc}{extra}") from exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return PROSE plus a STATE_PATCH JSON block. Output format: PROSE: <text> then STATE_PATCH: <json>. No markdown.",
            })
            response = _chat(
                workspace,
                f"write_scene_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.7,
                max_tokens=_write_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1

    _coerce_summary_update(patch)
    _coerce_character_updates(patch)
    _coerce_stat_updates(patch)
    _migrate_numeric_invariants(patch)
    _fill_character_update_context(patch, scene_card)
    _fill_character_continuity_update_context(patch, scene_card)
    validate_json(patch, "state_patch")
    return prose, patch


def _lint_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    state: Dict[str, Any],
    patch: Dict[str, Any],
    scene_card: Dict[str, Any],
    invariants: List[str],
    character_states: List[Dict[str, Any]],
    pov: Optional[str],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "lint.md")
    durable = _durable_state_context(book_root)
    authoritative_surfaces = _extract_authoritative_surfaces(prose)
    prompt = render_template_file(
        template,
        {
            "prose": prose,
            "state": state,
            "summary": _summary_from_state(state),
            "invariants": invariants,
            "authoritative_surfaces": authoritative_surfaces,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
            "character_states": character_states,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "lint_scene",
        client,
        messages,
        model=model,
        temperature=0.0,
        max_tokens=_lint_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            report = _extract_json(response.text)
            break
        except ValueError as exc:
            if attempt >= retries:
                raise exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return ONLY the JSON object. No prose, no markdown, no commentary.",
            })
            response = _chat(
                workspace,
                f"lint_scene_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.0,
                max_tokens=_lint_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1
    report = _normalize_lint_report(report)
    summary_update = patch.get("summary_update") if isinstance(patch, dict) else {}
    if not isinstance(summary_update, dict):
        summary_update = {}
    heuristic_issues = _heuristic_invariant_issues(prose, summary_update, invariants)
    extra_issues = _stat_mismatch_issues(
        prose,
        character_states,
        _global_continuity_stats(state),
        authoritative_surfaces=authoritative_surfaces,
    )
    extra_issues += _pov_drift_issues(prose, pov)
    combined = heuristic_issues + extra_issues
    if combined:
        report["issues"] = list(report.get("issues", [])) + combined
        report["status"] = "fail"
        report.setdefault("mode", "heuristic")
    validate_json(report, "lint_report")
    return report


def _repair_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    lint_report: Dict[str, Any],
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Tuple[str, Dict[str, Any]]:
    template = _resolve_template(book_root, "repair.md")
    durable = _durable_state_context(book_root)
    prompt = render_template_file(
        template,
        {
            "issues": lint_report.get("issues", []),
            "prose": prose,
            "state": state,
            "scene_card": scene_card,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": load_system_prompt(system_path, book_root / "outline" / "outline.json", include_outline=True)},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "repair_scene",
        client,
        messages,
        model=model,
        temperature=0.4,
        max_tokens=_repair_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            prose, patch = _extract_prose_and_patch(response.text)
            break
        except ValueError as exc:
            if attempt >= retries:
                extra = ""
                if _response_truncated(response):
                    extra = f" Model output hit MAX_TOKENS ({_repair_max_tokens()}); increase BOOKFORGE_REPAIR_MAX_TOKENS."
                raise ValueError(f"{exc}{extra}") from exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return PROSE plus a STATE_PATCH JSON block. Output format: PROSE: <text> then STATE_PATCH: <json>. No markdown.",
            })
            response = _chat(
                workspace,
                f"repair_scene_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.4,
                max_tokens=_repair_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1

    _coerce_summary_update(patch)
    _coerce_character_updates(patch)
    _coerce_stat_updates(patch)
    _migrate_numeric_invariants(patch)
    _fill_character_update_context(patch, scene_card)
    _fill_character_continuity_update_context(patch, scene_card)
    validate_json(patch, "state_patch")
    return prose, patch


def _state_repair(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    continuity_pack: Dict[str, Any],
    draft_patch: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "state_repair.md")
    durable = _durable_state_context(book_root)
    prompt = render_template_file(
        template,
        {
            "prose": prose,
            "state": state,
            "summary": _summary_from_state(state),
            "scene_card": scene_card,
            "continuity_pack": continuity_pack,
            "draft_patch": draft_patch,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": load_system_prompt(system_path, book_root / "outline" / "outline.json", include_outline=True)},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "state_repair",
        client,
        messages,
        model=model,
        temperature=0.2,
        max_tokens=_state_repair_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            patch = _extract_json(response.text)
            break
        except ValueError as exc:
            if attempt >= retries:
                raise exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return ONLY the JSON object. No prose, no markdown, no commentary.",
            })
            response = _chat(
                workspace,
                f"state_repair_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.2,
                max_tokens=_state_repair_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1
    if "schema_version" not in patch:
        patch["schema_version"] = "1.0"
    _coerce_summary_update(patch)
    _coerce_character_updates(patch)
    _coerce_stat_updates(patch)
    _migrate_numeric_invariants(patch)
    _fill_character_update_context(patch, scene_card)
    _fill_character_continuity_update_context(patch, scene_card)
    validate_json(patch, "state_patch")
    return patch


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


def _write_scene_files(
    book_root: Path,
    chapter: int,
    scene: int,
    prose: str,
    scene_card: Dict[str, Any],
    patch: Dict[str, Any],
    lint_report: Dict[str, Any],
    write_attempts: int,
) -> Path:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    prose_path = chapter_dir / f"scene_{scene:03d}.md"
    if prose_path.exists():
        raise FileExistsError(f"Scene already exists: {prose_path}")
    prose_path.write_text(prose.strip() + "\n", encoding="utf-8")

    meta_path = chapter_dir / f"scene_{scene:03d}.meta.json"
    meta = dict(scene_card)
    meta["prose_path"] = prose_path.relative_to(book_root).as_posix()
    meta["state_patch"] = patch
    summary_update = patch.get("summary_update") if isinstance(patch, dict) else {}
    if not isinstance(summary_update, dict):
        summary_update = {}
    meta["scene_summary"] = _summary_list(summary_update.get("last_scene"))
    meta["key_events"] = _summary_list(summary_update.get("key_events"))
    meta["must_stay_true"] = _summary_list(summary_update.get("must_stay_true"))
    meta["threads_touched"] = _summary_list(summary_update.get("threads_touched"))
    meta["lint_report"] = lint_report
    meta["write_attempts"] = write_attempts
    meta["updated_at"] = _now_iso()
    meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")

    last_excerpt_path = book_root / "draft" / "context" / "last_excerpt.md"
    last_excerpt_path.write_text(prose.strip() + "\n", encoding="utf-8")

    return prose_path


def run_loop(
    workspace: Path,
    book_id: str,
    steps: Optional[int] = None,
    until: Optional[str] = None,
    resume: bool = False,
) -> None:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    book_path = book_root / "book.json"
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"

    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state.json: {state_path}")
    if not outline_path.exists():
        raise FileNotFoundError(f"Missing outline.json: {outline_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    book = _load_json(book_path)
    outline = _load_json(outline_path)
    validate_json(outline, "outline")

    chapter_order, scene_counts = _outline_summary(outline)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    if not chapter_order:
        raise ValueError("Outline is missing chapters; cannot run writer loop.")

    target = _parse_until(until)
    if steps is None and target == (None, None):
        steps_remaining: Optional[int] = 1
    else:
        steps_remaining = steps

    config = load_config()
    planner_client = get_llm_client(config, phase="planner")
    continuity_client = get_llm_client(config, phase="continuity")
    preflight_client = get_llm_client(config, phase="preflight")
    writer_client = get_llm_client(config, phase="writer")
    repair_client = get_llm_client(config, phase="repair")
    state_repair_client = get_llm_client(config, phase="state_repair")
    linter_client = get_llm_client(config, phase="linter")
    planner_model = resolve_model("planner", config)
    continuity_model = resolve_model("continuity", config)
    preflight_model = resolve_model("preflight", config)

    if not characters_ready(book_root):
        try:
            generate_characters(workspace=workspace, book_id=book_id)
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, None, "characters_generate", exc)
    writer_model = resolve_model("writer", config)
    repair_model = resolve_model("repair", config)
    state_repair_model = resolve_model("state_repair", config)
    linter_model = resolve_model("linter", config)

    try:
        style_anchor = _ensure_style_anchor(
            workspace,
            book_root,
            book,
            system_path,
            writer_client,
            writer_model,
        )
    except LLMRequestError as exc:
        _pause_on_quota(book_root, state_path, None, "style_anchor", exc)

    while True:
        state = _load_json(state_path)
        cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
        chapter = int(cursor.get("chapter", 0) or 0)
        scene = int(cursor.get("scene", 0) or 0)

        if chapter <= 0:
            chapter = chapter_order[0]
        if scene <= 0:
            scene = 1

        if _cursor_beyond_target(chapter, scene, target, scene_counts):
            break
        if steps_remaining is not None and steps_remaining <= 0:
            break

        scene_card_path = _existing_scene_card(state, book_root) if resume else None
        if scene_card_path is None:
            _status(f"Planning chapter {chapter} scene {scene}...")
            try:
                scene_card_path = plan_scene(
                    workspace=workspace,
                    book_id=book_id,
                    client=planner_client,
                    model=planner_model,
                )
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "plan_scene", exc)
            _status(f"Planned scene card: ch{chapter:03d} sc{scene:03d} OK")
        else:
            _status(f"Using existing scene card: ch{chapter:03d} sc{scene:03d}")

        scene_card = _load_json(scene_card_path)
        validate_json(scene_card, "scene_card")
        chapter_num = int(scene_card.get("chapter", chapter))
        scene_num = int(scene_card.get("scene", scene))

        cast_ids = scene_card.get("cast_present_ids", []) if isinstance(scene_card, dict) else []
        if not isinstance(cast_ids, list):
            cast_ids = []
        cast_ids = [str(item) for item in cast_ids if str(item).strip()]
        if not cast_ids:
            derived = _scene_cast_ids_from_outline(outline, chapter_num, scene_num)
            if not derived:
                name_map = _character_id_map(character_registry)
                cast_names = scene_card.get("cast_present", []) if isinstance(scene_card, dict) else []
                if not isinstance(cast_names, list):
                    cast_names = []
                for name in cast_names:
                    mapped = name_map.get(str(name).strip().lower())
                    if mapped:
                        derived.append(mapped)
            if derived:
                scene_card["cast_present_ids"] = derived
                cast_ids = list(derived)
        if cast_ids and not scene_card.get("cast_present"):
            name_map = _character_name_map(character_registry)
            scene_card["cast_present"] = [name_map.get(item, item) for item in cast_ids]

        state = _load_json(state_path)

        chapter_total = scene_counts.get(chapter_num)
        chapter_end = isinstance(chapter_total, int) and chapter_total > 0 and scene_num >= chapter_total

        _status(f"Loading character states (cast only): ch{chapter_num:03d} sc{scene_num:03d}...")
        character_states = _load_character_states(book_root, scene_card)
        _status("Character states loaded OK")
        snapshots = _snapshot_character_states_before_preflight(book_root, scene_card)
        if snapshots:
            _status(f"Character state snapshots written: {len(snapshots)}")

        _status(f"Preflight state alignment: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            preflight_patch = _scene_state_preflight(
                workspace,
                book_root,
                system_path,
                scene_card,
                state,
                outline,
                chapter_order,
                scene_counts,
                character_registry,
                thread_registry,
                character_states,
                preflight_client,
                preflight_model,
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "scene_state_preflight", exc, scene_card)

        state = _apply_state_patch(state, preflight_patch, chapter_end=False)
        _apply_character_updates(book_root, preflight_patch, chapter_num, scene_num)
        _apply_character_stat_updates(book_root, preflight_patch)
        character_states = _load_character_states(book_root, scene_card)
        _status("Preflight alignment complete OK")

        _status(f"Generating continuity pack: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            continuity_pack = _generate_continuity_pack(
                workspace,
                book_root,
                system_path,
                state,
                scene_card,
                character_registry,
                thread_registry,
                character_states,
                continuity_client,
                continuity_model,
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "continuity_pack", exc, scene_card)
        _status("Continuity pack ready OK")

        base_invariants = book.get("invariants", []) if isinstance(book.get("invariants", []), list) else []

        _status(f"Writing scene: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            prose, patch = _write_scene(
                workspace,
                book_root,
                system_path,
                scene_card,
                continuity_pack,
                state,
                style_anchor,
                character_registry,
                thread_registry,
                character_states,
                writer_client,
                writer_model,
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "write_scene", exc, scene_card)
        _status("Write complete OK")

        _status(f"Repairing state: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            patch = _state_repair(
                workspace,
                book_root,
                system_path,
                prose,
                state,
                scene_card,
                continuity_pack,
                patch,
                character_registry,
                thread_registry,
                character_states,
                state_repair_client,
                state_repair_model,
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "state_repair", exc, scene_card)
        _status("State repair complete OK")

        lint_state = json.loads(json.dumps(state))
        lint_state = _apply_state_patch(lint_state, patch, chapter_end=chapter_end)
        summary = _summary_from_state(lint_state)
        invariants = list(base_invariants)
        invariants += summary.get("must_stay_true", [])
        invariants += summary.get("key_facts_ring", [])

        lint_mode = _lint_mode()

        if lint_mode == "off":
            lint_report = {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "off"}
            _status("Linting disabled (mode=off).")
        else:
            _status(f"Linting scene: ch{chapter_num:03d} sc{scene_num:03d}...")
            try:
                lint_report = _lint_scene(
                    workspace,
                    book_root,
                    system_path,
                    prose,
                    lint_state,
                    patch,
                    scene_card,
                    invariants,
                    character_states,
                    book.get("pov"),
                    linter_client,
                    linter_model,
                )
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "lint_scene", exc, scene_card)
            _status(f"Lint status: {lint_report.get('status', 'unknown')}")

        write_attempts = 1
        if lint_mode != "off" and lint_report.get("status") == "fail":
            _status(f"Repairing scene: ch{chapter_num:03d} sc{scene_num:03d}...")
            try:
                prose, patch = _repair_scene(
                    workspace,
                    book_root,
                    system_path,
                    prose,
                    lint_report,
                    state,
                    scene_card,
                    character_registry,
                    thread_registry,
                    character_states,
                    repair_client,
                    repair_model,
                )
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "repair_scene", exc, scene_card)
            _status("Repair complete OK")
            write_attempts += 1

            _status(f"Repairing state: ch{chapter_num:03d} sc{scene_num:03d}...")
            try:
                patch = _state_repair(
                    workspace,
                    book_root,
                    system_path,
                    prose,
                    state,
                    scene_card,
                    continuity_pack,
                    patch,
                    character_registry,
                    thread_registry,
                    character_states,
                    state_repair_client,
                    state_repair_model,
                )
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "state_repair", exc, scene_card)
            _status("State repair complete OK")

            lint_state = json.loads(json.dumps(state))
            lint_state = _apply_state_patch(lint_state, patch, chapter_end=chapter_end)
            summary = _summary_from_state(lint_state)
            invariants = list(base_invariants)
            invariants += summary.get("must_stay_true", [])
            invariants += summary.get("key_facts_ring", [])

            _status(f"Linting scene: ch{chapter_num:03d} sc{scene_num:03d}...")
            try:
                lint_report = _lint_scene(
                    workspace,
                    book_root,
                    system_path,
                    prose,
                    lint_state,
                    patch,
                    scene_card,
                    invariants,
                    character_states,
                    book.get("pov"),
                    linter_client,
                    linter_model,
                )
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "lint_scene", exc, scene_card)
            _status(f"Lint status: {lint_report.get('status', 'unknown')}")
            if lint_report.get("status") == "fail" and lint_mode == "strict":
                raise ValueError("Lint failed after repair; see lint logs for details.")

        chapter_total = scene_counts.get(chapter_num)
        chapter_end = isinstance(chapter_total, int) and chapter_total > 0 and scene_num >= chapter_total

        _status("Applying state patch...")
        state = _apply_state_patch(state, patch, chapter_end=chapter_end)
        _status("State updated OK")

        updates = patch.get("character_updates") if isinstance(patch, dict) else None
        if isinstance(updates, list) and updates:
            _status("Updating character states...")
            _apply_character_updates(book_root, patch, chapter_num, scene_num)
            _apply_character_stat_updates(book_root, patch)
            _status("Character states updated OK")
        else:
            _apply_character_updates(book_root, patch, chapter_num, scene_num)
            _apply_character_stat_updates(book_root, patch)

        cursor_override = patch.get("cursor_advance") if isinstance(patch.get("cursor_advance"), dict) else None
        if cursor_override:
            next_chapter = int(cursor_override.get("chapter", chapter_num) or chapter_num)
            next_scene = int(cursor_override.get("scene", scene_num + 1) or (scene_num + 1))
            completed = False
        else:
            next_chapter, next_scene, completed = _advance_cursor(
                chapter_order,
                scene_counts,
                chapter_num,
                scene_num,
            )

        _status("Persisting scene files...")
        _write_scene_files(
            book_root,
            chapter_num,
            scene_num,
            prose,
            scene_card,
            patch,
            lint_report,
            write_attempts,
        )
        _status("Scene files written OK")

        _update_bible(book_root, patch)

        if chapter_end:
            _status(f"Rolling up chapter summary: ch{chapter_num:03d}...")
            _rollup_chapter_summary(book_root, state, chapter_num)
            _status(f"Compiling chapter: ch{chapter_num:03d}...")
            _compile_chapter_markdown(book_root, outline, chapter_num)
            _status("Chapter compiled OK")

        _status(f"Advancing cursor -> ch{next_chapter:03d} sc{next_scene:03d}")
        state["cursor"] = {"chapter": next_chapter, "scene": next_scene}
        if completed:
            state["status"] = "COMPLETE"
        else:
            state["status"] = "DRAFTING"

        validate_json(state, "state")
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

        if steps_remaining is not None:
            steps_remaining -= 1


def run() -> None:
    raise NotImplementedError("Use run_loop via CLI.")

