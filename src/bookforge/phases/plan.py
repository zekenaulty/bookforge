from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import os
import re

from bookforge.config.env import load_config
from bookforge.llm.client import LLMClient
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message
from bookforge.prompt.renderer import render_template_file
from bookforge.util.paths import repo_root
from bookforge.util.schema import SCHEMA_VERSION, validate_json


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _plan_max_tokens() -> int:
    return _int_env("BOOKFORGE_PLAN_MAX_TOKENS", 4096)


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


def _beat_summary(beat: Optional[Dict[str, Any]]) -> str:
    if not beat:
        return ""
    summary = beat.get("summary")
    return str(summary) if summary is not None else ""


def _build_outline_window(chapter: Dict[str, Any], scene_number: int) -> Dict[str, Any]:
    beats = chapter.get("beats", []) if isinstance(chapter.get("beats", []), list) else []
    if beats and scene_number > len(beats):
        chapter_id = chapter.get("chapter_id", "")
        raise ValueError(f"Scene {scene_number} exceeds available beats ({len(beats)}) for chapter {chapter_id}.")
    beat_index = max(0, scene_number - 1)
    if beats:
        beat_index = min(beat_index, len(beats) - 1)
    else:
        beat_index = 0

    current = beats[beat_index] if beats else {}
    prev = beats[beat_index - 1] if beats and beat_index > 0 else None
    nxt = beats[beat_index + 1] if beats and beat_index + 1 < len(beats) else None

    return {
        "chapter": {
            "chapter_id": chapter.get("chapter_id"),
            "title": chapter.get("title", ""),
            "goal": chapter.get("goal", ""),
            "characters": _chapter_characters(chapter),
        },
        "scene_index": scene_number,
        "previous": {
            "summary": _beat_summary(prev),
            "characters": _beat_characters(prev),
            "introduces": _beat_introduces(prev),
        } if prev else None,
        "current": {
            "beat_id": current.get("beat_id"),
            "summary": _beat_summary(current),
            "characters": _beat_characters(current),
            "introduces": _beat_introduces(current),
        },
        "next": {
            "summary": _beat_summary(nxt),
            "characters": _beat_characters(nxt),
            "introduces": _beat_introduces(nxt),
        } if nxt else None,
    }




def _beat_characters(beat: Optional[Dict[str, Any]]) -> List[str]:
    if not beat or not isinstance(beat, dict):
        return []
    values = beat.get("characters")
    return values if isinstance(values, list) else []


def _beat_introduces(beat: Optional[Dict[str, Any]]) -> List[str]:
    if not beat or not isinstance(beat, dict):
        return []
    values = beat.get("introduces")
    return values if isinstance(values, list) else []


def _chapter_characters(chapter: Dict[str, Any]) -> List[str]:
    values = chapter.get("characters")
    if isinstance(values, list):
        return values
    characters: List[str] = []
    for beat in chapter.get("beats", []) if isinstance(chapter.get("beats", []), list) else []:
        characters.extend(_beat_characters(beat))
    # de-dupe while preserving order
    seen = set()
    unique = []
    for item in characters:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique

def _scene_id(chapter: int, scene: int) -> str:
    return f"SC_{chapter:03d}_{scene:03d}"


def _normalize_scene_card(
    card: Dict[str, Any],
    chapter: int,
    scene: int,
    beat_target: str,
) -> Dict[str, Any]:
    if "schema_version" not in card:
        card["schema_version"] = SCHEMA_VERSION
    card.setdefault("scene_id", _scene_id(chapter, scene))
    card.setdefault("chapter", chapter)
    card.setdefault("scene", scene)
    if not card.get("beat_target"):
        card["beat_target"] = beat_target

    if not isinstance(card.get("required_callbacks"), list):
        card["required_callbacks"] = []
    if not isinstance(card.get("constraints"), list):
        card["constraints"] = []

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

    cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
    chapter_num = chapter if chapter is not None else int(cursor.get("chapter", 0) or 0)
    scene_num = scene if scene is not None else int(cursor.get("scene", 0) or 0)

    if chapter_num <= 0:
        chapter_num = 1
    if scene_num <= 0:
        scene_num = 1

    chapter_obj = _find_chapter(outline, chapter_num)
    outline_window = _build_outline_window(chapter_obj, scene_num)

    beat_target = outline_window.get("current", {}).get("summary") or chapter_obj.get("goal", "")
    beat_target = str(beat_target) if beat_target is not None else ""

    plan_template = _resolve_plan_template(book_root)
    prompt = render_template_file(
        plan_template,
        {
            "outline_window": outline_window,
            "state": state,
        },
    )

    if client is None:
        config = load_config()
        client = get_llm_client(config)
        if model is None:
            model = resolve_model("planner", config)
    elif model is None:
        model = "default"

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    max_tokens = _plan_max_tokens()
    response = client.chat(messages, model=model, temperature=0.4, max_tokens=max_tokens)
    log_path: Optional[Path] = None
    if should_log_llm():
        log_path = log_llm_response(workspace, "plan_scene", response)
    try:
        card = _extract_json(response.text)
    except ValueError as exc:
        if not log_path:
            log_path = log_llm_response(workspace, "plan_scene", response)
        extra = ""
        if _response_truncated(response):
            extra = f" Model output hit MAX_TOKENS ({max_tokens}); increase BOOKFORGE_PLAN_MAX_TOKENS."
        raise ValueError(f"{exc}{extra} (raw response logged to {log_path})") from exc

    card = _normalize_scene_card(card, chapter_num, scene_num, beat_target)
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
