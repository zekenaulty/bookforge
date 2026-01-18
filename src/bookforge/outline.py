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


def _outline_max_tokens() -> int:
    return _int_env("BOOKFORGE_OUTLINE_MAX_TOKENS", 12288)


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


def _write_outline_chapters(chapters_dir: Path, chapters: List[Dict[str, Any]]) -> None:
    chapters_dir.mkdir(parents=True, exist_ok=True)
    for idx, chapter in enumerate(chapters, start=1):
        path = chapters_dir / f"ch_{idx:03d}.json"
        path.write_text(json.dumps(chapter, ensure_ascii=True, indent=2), encoding="utf-8")


def generate_outline(
    workspace: Path,
    book_id: str,
    new_version: bool = False,
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
    prompt = render_template_file(
        outline_template,
        {
            "book": book,
            "targets": book.get("targets", {}),
            "notes": "",
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

    max_tokens = _outline_max_tokens()
    response = client.chat(messages, model=model, temperature=0.6, max_tokens=max_tokens)
    log_path: Optional[Path] = None
    if should_log_llm():
        log_path = log_llm_response(workspace, "outline_generate", response)
    try:
        outline = _extract_json(response.text)
    except ValueError as exc:
        if not log_path:
            log_path = log_llm_response(workspace, "outline_generate", response)
        extra = ""
        if _response_truncated(response):
            extra = f" Model output hit MAX_TOKENS ({max_tokens}); increase BOOKFORGE_OUTLINE_MAX_TOKENS."
        raise ValueError(f"{exc}{extra} (raw response logged to {log_path})") from exc

    if "schema_version" not in outline:
        outline["schema_version"] = SCHEMA_VERSION

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
        if "beats" not in chapter or not isinstance(chapter.get("beats"), list):
            chapter["beats"] = []

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
