from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import os
import re
import logging

from bookforge.config.env import load_config, read_int_env
from bookforge.llm.client import LLMClient
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message
from bookforge.llm.errors import LLMRequestError
from bookforge.prompt.renderer import render_template_file
from bookforge.util.paths import repo_root
from bookforge.util.schema import validate_json


OUTLINE_SCHEMA_VERSION = "1.1"

logger = logging.getLogger(__name__)

PREFERRED_CHAPTER_ROLES = {
    "hook",
    "setup",
    "pressure",
    "reversal",
    "revelation",
    "investigation",
    "journey",
    "trial",
    "alliance",
    "betrayal",
    "siege",
    "confrontation",
    "climax",
    "aftermath",
    "transition",
    "hinge",
}

PREFERRED_SCENE_TYPES = {
    "setup",
    "action",
    "reveal",
    "escalation",
    "choice",
    "consequence",
    "aftermath",
    "transition",
}

PREFERRED_TEMPOS = {
    "slow_burn",
    "steady",
    "rush",
}

PREFERRED_INTENSITY_RANGE = (1, 5)


MAX_ENUM_CONTEXT = 3

def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _outline_max_tokens() -> int:
    return _int_env("BOOKFORGE_OUTLINE_MAX_TOKENS", 49152)


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


def _find_matching_bracket(payload: str, start_index: int) -> Optional[int]:
    depth = 0
    in_string = False
    escape = False

    for i in range(start_index, len(payload)):
        ch = payload[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                return i

    return None


def _append_missing_closers(payload: str) -> str:
    stack: List[str] = []
    in_string = False
    escape = False

    for ch in payload:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch in "{[":
            stack.append(ch)
            continue
        if ch in "}]":
            if not stack:
                continue
            opener = stack[-1]
            if (opener == "{" and ch == "}") or (opener == "[" and ch == "]"):
                stack.pop()

    if not stack:
        return payload

    closers = {"{": "}", "[": "]"}
    return payload + "".join(closers[ch] for ch in reversed(stack))


def _repair_outline_extra_chapters(payload: str) -> str:
    chapters_key = payload.find('"chapters"')
    if chapters_key == -1:
        return payload
    start = payload.find('[', chapters_key)
    if start == -1:
        return payload
    end = _find_matching_bracket(payload, start)
    if end is None:
        return payload

    remainder = payload[end + 1:]
    trimmed = remainder.lstrip()
    if not trimmed:
        return payload

    if trimmed.startswith('}'):
        tail = trimmed[1:].lstrip()
        if tail.startswith(']'):
            tail_after = tail[1:].lstrip()
            if re.match(r'^,\s*"(threads|characters)"', tail_after):
                after = remainder
                match = re.match(r'\s*}\s*]', after)
                if match:
                    after = after[match.end():]
                return payload[:end + 1] + after
        if re.match(r'^,\s*"(threads|characters)"', tail):
            after = remainder
            match = re.match(r'\s*}', after)
            if match:
                after = after[match.end():]
            return payload[:end + 1] + after

    probe = trimmed
    if probe.startswith('}'):
        probe = probe[1:].lstrip()

    if not re.match(r'^,\s*\{\s*"chapter_id"', probe):
        return payload

    after = remainder
    match = re.match(r'\s*}', after)
    if match:
        after = after[match.end():]
    return payload[:end] + after


def _repair_outline_json(payload: str) -> str:
    repaired = payload
    repaired = re.sub(r'}\]\}\]\s*,\s*"chapter_id"', r'}]}]}, {"chapter_id"', repaired)
    repaired = re.sub(r'}\]\}\]\s*,\s*"threads"', r'}]}]}], "threads"', repaired)
    repaired = re.sub(r'}\]\}\]\s*,\s*"characters"', r'}]}]}], "characters"', repaired)
    for _ in range(5):
        updated = _repair_outline_extra_chapters(repaired)
        if updated == repaired:
            break
        repaired = updated
    return _append_missing_closers(repaired)


def _add_enum_warning(collection: Dict[str, List[str]], value: str, context: str) -> None:
    contexts = collection.setdefault(value, [])
    if len(contexts) < MAX_ENUM_CONTEXT and context not in contexts:
        contexts.append(context)


def _format_enum_warnings(collection: Dict[str, List[str]]) -> str:
    parts: List[str] = []
    for value in sorted(collection.keys()):
        contexts = collection[value]
        if contexts:
            parts.append(f"{value} ({', '.join(contexts)})")
        else:
            parts.append(value)
    return "; ".join(parts)


def _warn_outline_enum_values(outline: Dict[str, Any]) -> None:
    chapters = outline.get("chapters")
    if not isinstance(chapters, list):
        return
    unknown_roles: Dict[str, List[str]] = {}
    unknown_tempos: Dict[str, List[str]] = {}
    unknown_scene_types: Dict[str, List[str]] = {}
    unknown_intensities: Dict[str, List[str]] = {}

    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = chapter.get("chapter_id", "?")
        role = chapter.get("chapter_role")
        if isinstance(role, str) and role and role not in PREFERRED_CHAPTER_ROLES:
            _add_enum_warning(unknown_roles, role, f"chapter {chapter_id}")

        pacing = chapter.get("pacing")
        if isinstance(pacing, dict):
            tempo = pacing.get("tempo")
            if isinstance(tempo, str) and tempo and tempo not in PREFERRED_TEMPOS:
                _add_enum_warning(unknown_tempos, tempo, f"chapter {chapter_id}")
            intensity = pacing.get("intensity")
            if isinstance(intensity, (int, float)):
                low, high = PREFERRED_INTENSITY_RANGE
                if intensity < low or intensity > high:
                    _add_enum_warning(unknown_intensities, str(intensity), f"chapter {chapter_id}")
            elif isinstance(intensity, str):
                try:
                    numeric = float(intensity)
                except ValueError:
                    _add_enum_warning(unknown_intensities, intensity, f"chapter {chapter_id}")
                else:
                    low, high = PREFERRED_INTENSITY_RANGE
                    if numeric < low or numeric > high:
                        _add_enum_warning(unknown_intensities, intensity, f"chapter {chapter_id}")
            elif intensity is not None:
                _add_enum_warning(unknown_intensities, str(intensity), f"chapter {chapter_id}")

        sections = chapter.get("sections")
        if not isinstance(sections, list):
            continue
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_id = section.get("section_id", "?")
            scenes = section.get("scenes")
            if not isinstance(scenes, list):
                continue
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_id = scene.get("scene_id", "?")
                scene_type = scene.get("type")
                if isinstance(scene_type, str) and scene_type and scene_type not in PREFERRED_SCENE_TYPES:
                    _add_enum_warning(
                        unknown_scene_types,
                        scene_type,
                        f"ch {chapter_id} sec {section_id} scene {scene_id}",
                    )

    if unknown_roles:
        logger.warning(
            "Outline uses non-standard chapter_role values: %s",
            _format_enum_warnings(unknown_roles),
        )
    if unknown_tempos:
        logger.warning(
            "Outline uses non-standard tempo values: %s",
            _format_enum_warnings(unknown_tempos),
        )
    if unknown_scene_types:
        logger.warning(
            "Outline uses non-standard scene type values: %s",
            _format_enum_warnings(unknown_scene_types),
        )
    if unknown_intensities:
        logger.warning(
            "Outline uses intensity values outside 1-5: %s",
            _format_enum_warnings(unknown_intensities),
        )


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
                repaired = _repair_outline_json(cleaned)
                data = json.loads(repaired)
            except json.JSONDecodeError:
                try:
                    data = ast.literal_eval(repaired)
                except (ValueError, SyntaxError) as exc:
                    raise ValueError("Invalid JSON in response.") from exc
            except (ValueError, SyntaxError) as exc:
                raise ValueError("Invalid JSON in response.") from exc
    if not isinstance(data, dict):
        raise ValueError("Outline response JSON must be an object.")
    return data




def _slugify(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s-]+", "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or "character"


def _ensure_character_ids(characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for idx, character in enumerate(characters, start=1):
        if not isinstance(character, dict):
            continue
        if not character.get("character_id"):
            name = str(character.get("name") or character.get("persona_name") or f"character_{idx}")
            character["character_id"] = f"CHAR_{_slugify(name)}"
    return characters


def _next_outline_version(outline_root: Path) -> int:
    highest = 0
    for path in outline_root.glob("outline_v*.json"):
        match = re.match(r"outline_v(\d+)\.json", path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def _archive_outline(outline_root: Path) -> None:
    outline_path = outline_root / "outline.json"
    if not outline_path.exists():
        return
    version = _next_outline_version(outline_root)
    outline_path.replace(outline_root / f"outline_v{version}.json")

    chapters_dir = outline_root / "chapters"
    if chapters_dir.exists():
        chapters_dir.replace(outline_root / f"chapters_v{version}")


def _resolve_outline_template(book_root: Path) -> Path:
    book_template = book_root / "prompts" / "templates" / "outline.md"
    if book_template.exists():
        return book_template
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / "outline.md"




def _read_prompt_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _write_outline_chapters(chapters_dir: Path, chapters: List[Dict[str, Any]]) -> None:
    chapters_dir.mkdir(parents=True, exist_ok=True)
    for idx, chapter in enumerate(chapters, start=1):
        path = chapters_dir / f"ch_{idx:03d}.json"
        path.write_text(json.dumps(chapter, ensure_ascii=True, indent=2), encoding="utf-8")


def generate_outline(
    workspace: Path,
    book_id: str,
    new_version: bool = False,
    prompt_file: Optional[Path] = None,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
) -> Path:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    book_path = book_root / "book.json"
    state_path = book_root / "state.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state.json: {state_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    book = json.loads(book_path.read_text(encoding="utf-8"))

    outline_template = _resolve_outline_template(book_root)

    user_prompt = ""
    if prompt_file is not None:
        user_prompt = _read_prompt_file(prompt_file)

    prompt = render_template_file(
        outline_template,
        {
            "book": book,
            "targets": book.get("targets", {}),
            "notes": "",
            "user_prompt": user_prompt,
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

    max_tokens = _outline_max_tokens()
    key_slot = getattr(client, "key_slot", None)
    request = {"model": model, "temperature": 0.6, "max_tokens": max_tokens}
    try:
        response = client.chat(messages, model=model, temperature=0.6, max_tokens=max_tokens)
    except LLMRequestError as exc:
        if should_log_llm():
            extra = {"key_slot": key_slot} if key_slot else None
            log_llm_error(workspace, "outline_generate_error", exc, request=request, messages=messages, extra=extra)
        raise

    log_path: Optional[Path] = None
    log_extra = {"key_slot": key_slot} if key_slot else None
    if should_log_llm():
        log_path = log_llm_response(workspace, "outline_generate", response, request=request, messages=messages, extra=log_extra)
    try:

        outline = _extract_json(response.text)
    except ValueError as exc:
        if not log_path:
            log_path = log_llm_response(workspace, "outline_generate", response, request=request, messages=messages, extra=log_extra)
        extra_msg = ""
        if _response_truncated(response):
            extra_msg = f" Model output hit MAX_TOKENS ({max_tokens}); increase BOOKFORGE_OUTLINE_MAX_TOKENS."
        raise ValueError(f"{exc}{extra_msg} (raw response logged to {log_path})") from exc

    if "schema_version" not in outline:
        outline["schema_version"] = OUTLINE_SCHEMA_VERSION

    characters = outline.get("characters")
    if isinstance(characters, list):
        outline["characters"] = _ensure_character_ids(characters)

    chapters = outline.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("Outline must include a non-empty chapters array.")

    for idx, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            raise ValueError("Outline chapters must be objects.")
        if "chapter_id" not in chapter:
            chapter["chapter_id"] = idx
        sections = chapter.get("sections")
        if not isinstance(sections, list) or not sections:
            raise ValueError("Outline chapters must include a non-empty sections array.")
        scene_counter = 0
        for section_idx, section in enumerate(sections, start=1):
            if not isinstance(section, dict):
                raise ValueError("Outline sections must be objects.")
            if "section_id" not in section:
                section["section_id"] = section_idx
            scenes = section.get("scenes")
            if not isinstance(scenes, list) or not scenes:
                raise ValueError("Outline sections must include a non-empty scenes array.")
            for scene in scenes:
                if not isinstance(scene, dict):
                    raise ValueError("Outline scenes must be objects.")
                scene_counter += 1
                if "scene_id" not in scene:
                    scene["scene_id"] = scene_counter

    _warn_outline_enum_values(outline)

    validate_json(outline, "outline")

    outline_root = book_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)
    outline_path = outline_root / "outline.json"

    if outline_path.exists():
        if not new_version:
            raise FileExistsError("outline.json already exists. Use --new-version to regenerate.")
        _archive_outline(outline_root)

    outline_path.write_text(json.dumps(outline, ensure_ascii=True, indent=2), encoding="utf-8")

    characters = outline.get("characters")
    if isinstance(characters, list):
        outline_characters_path = outline_root / "characters.json"
        outline_characters_path.write_text(json.dumps(characters, ensure_ascii=True, indent=2), encoding="utf-8")

    _write_outline_chapters(outline_root / "chapters", chapters)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["outline"] = {"path": "outline/outline.json"}
    if state.get("status") == "NEW":
        state["status"] = "OUTLINED"
    validate_json(state, "state")
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    return outline_path
