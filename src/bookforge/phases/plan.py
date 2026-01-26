from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import os
import re

from bookforge.config.env import load_config, read_int_env
from bookforge.llm.client import LLMClient
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message
from bookforge.llm.errors import LLMRequestError
from bookforge.prompt.renderer import render_template_file
from bookforge.util.paths import repo_root
from bookforge.util.schema import validate_json


SCENE_CARD_SCHEMA_VERSION = "1.1"
DEFAULT_EMPTY_RESPONSE_RETRIES = 1


def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _plan_max_tokens() -> int:
    return _int_env("BOOKFORGE_PLAN_MAX_TOKENS", 16384)


def _empty_response_retries() -> int:
    return max(0, _int_env("BOOKFORGE_EMPTY_RESPONSE_RETRIES", DEFAULT_EMPTY_RESPONSE_RETRIES))


def _response_truncated(response: LLMResponse) -> bool:
    raw = response.raw
    if not isinstance(raw, dict):
        return False
    candidates = raw.get("candidates", [])
    if not candidates:
        return False
    finish = candidates[0].get("finishReason")
    return str(finish).upper() == "MAX_TOKENS"


def _clean_json_payload(payload: str) -> str:
    cleaned = payload.strip()
    cleaned = cleaned.replace("\ufeff", "")
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"')
    cleaned = cleaned.replace("\u2018", "'").replace("\u2019", "'")
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        payload = match.group(1)
    else:
        match = re.search(r"(\{[\s\S]*\})", text)
        if not match:
            raise ValueError("No JSON object found in response.")
        payload = match.group(1)
    payload = payload.strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        cleaned = _clean_json_payload(payload)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(cleaned)
            except (ValueError, SyntaxError) as exc:
                raise ValueError("Invalid JSON in response.") from exc
    if not isinstance(data, dict):
        raise ValueError("Scene card response JSON must be an object.")
    return data


def _resolve_plan_template(book_root: Path) -> Path:
    book_template = book_root / "prompts" / "templates" / "plan.md"
    if book_template.exists():
        return book_template
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / "plan.md"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _character_slug(character_id: str) -> str:
    cleaned = str(character_id or "").strip()
    if cleaned.upper().startswith("CHAR_"):
        cleaned = cleaned[5:]
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]+", "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned.lower() or "character"


def _load_character_states(book_root: Path, cast_present_ids: List[str]) -> List[Dict[str, Any]]:
    states: List[Dict[str, Any]] = []
    for char_id in cast_present_ids:
        slug = _character_slug(str(char_id))
        state_path = book_root / "draft" / "context" / "characters" / f"{slug}.state.json"
        if state_path.exists():
            try:
                states.append(json.loads(state_path.read_text(encoding="utf-8")))
                continue
            except json.JSONDecodeError:
                pass
        states.append({"character_id": str(char_id), "missing": True})
    return states



def _find_chapter(outline: Dict[str, Any], chapter_number: int) -> Dict[str, Any]:
    chapters = outline.get("chapters", [])
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("Outline must include chapters to plan scenes.")

    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = chapter.get("chapter_id")
        if chapter_id is None:
            continue
        if str(chapter_id) == str(chapter_number):
            return chapter

    index = chapter_number - 1
    if 0 <= index < len(chapters):
        candidate = chapters[index]
        if isinstance(candidate, dict):
            return candidate

    raise ValueError(f"Chapter {chapter_number} not found in outline.")


def _scene_summary(scene: Optional[Dict[str, Any]]) -> str:
    if not scene:
        return ""
    summary = scene.get("summary")
    return str(summary) if summary is not None else ""


def _scene_characters(scene: Optional[Dict[str, Any]]) -> List[str]:
    if not scene or not isinstance(scene, dict):
        return []
    values = scene.get("characters")
    return values if isinstance(values, list) else []


def _scene_introduces(scene: Optional[Dict[str, Any]]) -> List[str]:
    if not scene or not isinstance(scene, dict):
        return []
    values = scene.get("introduces")
    return values if isinstance(values, list) else []


def _scene_threads(scene: Optional[Dict[str, Any]]) -> List[str]:
    if not scene or not isinstance(scene, dict):
        return []
    values = scene.get("threads")
    return values if isinstance(values, list) else []


def _scene_callbacks(scene: Optional[Dict[str, Any]]) -> List[str]:
    if not scene or not isinstance(scene, dict):
        return []
    values = scene.get("callbacks")
    return values if isinstance(values, list) else []


def _flatten_scenes(chapter: Dict[str, Any]) -> List[Dict[str, Any]]:
    sections = chapter.get("sections", []) if isinstance(chapter.get("sections", []), list) else []
    flattened: List[Dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_info = {
            "section_id": section.get("section_id"),
            "title": section.get("title", ""),
            "intent": section.get("intent", ""),
            "section_role": section.get("section_role", ""),
        }
        scenes = section.get("scenes", []) if isinstance(section.get("scenes", []), list) else []
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            flattened.append({"section": section_info, "scene": scene})
    return flattened


def _chapter_characters(chapter: Dict[str, Any]) -> List[str]:
    characters: List[str] = []
    for entry in _flatten_scenes(chapter):
        characters.extend(_scene_characters(entry.get("scene")))
    seen = set()
    unique = []
    for item in characters:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _character_name_map(outline: Dict[str, Any]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    characters = outline.get("characters", [])
    if not isinstance(characters, list):
        return mapping
    for item in characters:
        if not isinstance(item, dict):
            continue
        character_id = str(item.get("character_id") or "").strip()
        if not character_id:
            continue
        name = str(item.get("name") or character_id).strip() or character_id
        mapping[character_id] = name
    return mapping


def _build_outline_window(chapter: Dict[str, Any], scene_number: int) -> Dict[str, Any]:
    scenes = _flatten_scenes(chapter)
    if scenes and scene_number > len(scenes):
        chapter_id = chapter.get("chapter_id", "")
        raise ValueError(f"Scene {scene_number} exceeds available scenes ({len(scenes)}) for chapter {chapter_id}.")

    index = max(0, scene_number - 1)
    if scenes:
        index = min(index, len(scenes) - 1)
    else:
        index = 0

    current_entry = scenes[index] if scenes else None
    prev_entry = scenes[index - 1] if scenes and index > 0 else None
    next_entry = scenes[index + 1] if scenes and index + 1 < len(scenes) else None

    def _entry_payload(entry: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not entry:
            return None
        scene = entry.get("scene", {})
        section = entry.get("section", {})
        return {
            "scene_id": scene.get("scene_id"),
            "summary": _scene_summary(scene),
            "type": scene.get("type"),
            "outcome": scene.get("outcome"),
            "characters": _scene_characters(scene),
            "introduces": _scene_introduces(scene),
            "threads": _scene_threads(scene),
            "callbacks": _scene_callbacks(scene),
            "section": {
                "section_id": section.get("section_id"),
                "title": section.get("title", ""),
                "intent": section.get("intent", ""),
                "section_role": section.get("section_role", ""),
            },
        }

    current_payload = _entry_payload(current_entry)

    return {
        "chapter": {
            "chapter_id": chapter.get("chapter_id"),
            "title": chapter.get("title", ""),
            "goal": chapter.get("goal", ""),
            "chapter_role": chapter.get("chapter_role", ""),
            "stakes_shift": chapter.get("stakes_shift", ""),
            "bridge": chapter.get("bridge", {}),
            "pacing": chapter.get("pacing", {}),
            "characters": _chapter_characters(chapter),
        },
        "section": current_payload.get("section") if current_payload else None,
        "scene_index": scene_number,
        "previous": _entry_payload(prev_entry),
        "current": current_payload,
        "next": _entry_payload(next_entry),
    }


def _scene_id(chapter: int, scene: int) -> str:
    return f"SC_{chapter:03d}_{scene:03d}"


def _normalize_scene_card(
    card: Dict[str, Any],
    chapter: int,
    scene: int,
    scene_target: str,
    cast_present: List[str],
    cast_present_ids: List[str],
    introduces: List[str],
    introduces_ids: List[str],
    thread_ids: List[str],
    callbacks: List[str],
) -> Dict[str, Any]:
    if "schema_version" not in card:
        card["schema_version"] = SCENE_CARD_SCHEMA_VERSION
    card.setdefault("scene_id", _scene_id(chapter, scene))
    card.setdefault("chapter", chapter)
    card.setdefault("scene", scene)
    scene_target_value = card.get("scene_target")
    if scene_target_value is None or scene_target_value == "":
        card["scene_target"] = scene_target
    else:
        if not isinstance(scene_target_value, str):
            scene_target_value = str(scene_target_value)
        if scene_target_value.strip().isdigit():
            card["scene_target"] = scene_target
        else:
            card["scene_target"] = scene_target_value

    if not isinstance(card.get("required_callbacks"), list):
        card["required_callbacks"] = []
    if not card.get("required_callbacks") and callbacks:
        card["required_callbacks"] = list(callbacks)
    if not isinstance(card.get("constraints"), list):
        card["constraints"] = []
    card["cast_present"] = list(cast_present)
    card["cast_present_ids"] = list(cast_present_ids)
    card["introduces"] = list(introduces)
    card["introduces_ids"] = list(introduces_ids)
    card["thread_ids"] = list(thread_ids)

    return card


def plan_scene(
    workspace: Path,
    book_id: str,
    chapter: Optional[int] = None,
    scene: Optional[int] = None,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
) -> Path:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    outline_path = book_root / "outline" / "outline.json"
    state_path = book_root / "state.json"
    system_path = book_root / "prompts" / "system_v1.md"

    if not outline_path.exists():
        raise FileNotFoundError(f"Missing outline.json: {outline_path}")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state.json: {state_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    outline = _load_json(outline_path)
    state = _load_json(state_path)

    validate_json(outline, "outline")

    cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
    chapter_num = chapter if chapter is not None else int(cursor.get("chapter", 0) or 0)
    scene_num = scene if scene is not None else int(cursor.get("scene", 0) or 0)

    if chapter_num <= 0:
        chapter_num = 1
    if scene_num <= 0:
        scene_num = 1

    chapter_obj = _find_chapter(outline, chapter_num)
    outline_window = _build_outline_window(chapter_obj, scene_num)

    current_scene = outline_window.get("current") or {}
    scene_target = current_scene.get("summary") or chapter_obj.get("goal", "")
    scene_target = str(scene_target) if scene_target is not None else ""
    character_names = _character_name_map(outline)
    cast_present_ids = current_scene.get("characters", [])
    if not isinstance(cast_present_ids, list):
        cast_present_ids = []
    cast_present_ids = [str(item) for item in cast_present_ids if str(item).strip()]
    cast_present = [character_names.get(item, item) for item in cast_present_ids]

    character_states = _load_character_states(book_root, cast_present_ids)

    introduces_ids = current_scene.get("introduces", [])
    if not isinstance(introduces_ids, list):
        introduces_ids = []
    introduces_ids = [str(item) for item in introduces_ids if str(item).strip()]
    introduces = [character_names.get(item, item) for item in introduces_ids]

    thread_ids = current_scene.get("threads", [])
    if not isinstance(thread_ids, list):
        thread_ids = []
    thread_ids = [str(item) for item in thread_ids if str(item).strip()]

    callbacks = current_scene.get("callbacks", [])
    if not isinstance(callbacks, list):
        callbacks = []
    callbacks = [str(item) for item in callbacks if str(item).strip()]

    plan_template = _resolve_plan_template(book_root)
    prompt = render_template_file(
        plan_template,
        {
            "outline_window": outline_window,
            "state": state,
            "character_states": character_states,
        },
    )

    if client is None:
        config = load_config()
        client = get_llm_client(config, phase="planner")
        if model is None:
            model = resolve_model("planner", config)
    elif model is None:
        model = "default"

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    max_tokens = _plan_max_tokens()
    request = {"model": model, "temperature": 0.4, "max_tokens": max_tokens}
    log_path: Optional[Path] = None
    key_slot = getattr(client, "key_slot", None)
    log_extra: Dict[str, Any] = {"book_id": book_id, "chapter": chapter_num, "scene": scene_num}
    if key_slot:
        log_extra["key_slot"] = key_slot
    retries = _empty_response_retries()
    attempt = 0
    while True:
        try:
            response = client.chat(messages, model=model, temperature=0.4, max_tokens=max_tokens)
        except LLMRequestError as exc:
            if should_log_llm():
                log_llm_error(workspace, "plan_scene_error", exc, request=request, messages=messages, extra=log_extra)
            raise
        label = "plan_scene" if attempt == 0 else f"plan_scene_retry{attempt}"
        if should_log_llm():
            log_path = log_llm_response(workspace, label, response, request=request, messages=messages, extra=log_extra)
        if str(response.text).strip() or attempt >= retries:
            break
        attempt += 1
    try:
        card = _extract_json(response.text)
    except ValueError as exc:
        if not log_path:
            log_path = log_llm_response(workspace, "plan_scene", response, request=request, messages=messages, extra=log_extra)
        extra_msg = ""
        if _response_truncated(response):
            extra_msg = f" Model output hit MAX_TOKENS ({max_tokens}); increase BOOKFORGE_PLAN_MAX_TOKENS."
        raise ValueError(f"{exc}{extra_msg} (raw response logged to {log_path})") from exc

    card = _normalize_scene_card(
        card,
        chapter_num,
        scene_num,
        scene_target,
        cast_present,
        cast_present_ids,
        introduces,
        introduces_ids,
        thread_ids,
        callbacks,
    )
    validate_json(card, "scene_card")

    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    scene_path = chapter_dir / f"scene_{scene_num:03d}.meta.json"
    scene_path.write_text(json.dumps(card, ensure_ascii=True, indent=2), encoding="utf-8")

    state.setdefault("plan", {})
    plan_data = state.get("plan", {}) if isinstance(state.get("plan"), dict) else {}
    rel_scene_path = scene_path.relative_to(book_root).as_posix()
    plan_data["scene_card"] = rel_scene_path
    plan_data["outline_path"] = "outline/outline.json"
    state["plan"] = plan_data

    state_cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
    state_cursor["chapter"] = chapter_num
    state_cursor["scene"] = scene_num
    state["cursor"] = state_cursor

    if state.get("status") in {"NEW", "OUTLINED"}:
        state["status"] = "PLANNED"

    validate_json(state, "state")
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    return scene_path
