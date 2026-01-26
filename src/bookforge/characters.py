from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import re

from bookforge.config.env import load_config
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import Message
from bookforge.prompt.renderer import render_template_file
from bookforge.util.paths import repo_root
from bookforge.util.schema import validate_json


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
        raise ValueError("Response JSON must be an object.")
    return data


def _resolve_template(book_root: Path, name: str) -> Path:
    book_template = book_root / "prompts" / "templates" / name
    if book_template.exists():
        return book_template
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / name


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_outline_characters(book_root: Path) -> List[Dict[str, Any]]:
    characters_path = book_root / "outline" / "characters.json"
    if characters_path.exists():
        data = _read_json(characters_path)
        if isinstance(data, list):
            return data
    outline_path = book_root / "outline" / "outline.json"
    if outline_path.exists():
        outline = _read_json(outline_path)
        characters = outline.get("characters")
        if isinstance(characters, list):
            return characters
    return []


def _slugify(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s-]+", "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or "character"


def _character_slug(character_id: str) -> str:
    cleaned = character_id.strip()
    if cleaned.upper().startswith("CHAR_"):
        cleaned = cleaned[5:]
    return _slugify(cleaned)


def _series_root(workspace: Path, book: Dict[str, Any]) -> Path:
    series_ref = str(book.get("series_ref") or "").strip()
    if series_ref:
        return workspace / series_ref
    series_id = str(book.get("series_id") or book.get("book_id") or "series").strip()
    return workspace / "series" / (series_id or "series")


def _ensure_series_dirs(series_root: Path) -> None:
    (series_root / "canon" / "characters").mkdir(parents=True, exist_ok=True)
    (series_root / "canon" / "index.json").parent.mkdir(parents=True, exist_ok=True)
    index_path = series_root / "canon" / "index.json"
    if not index_path.exists():
        index_path.write_text("{}", encoding="utf-8")


def _update_series_index(series_root: Path, entries: List[Dict[str, str]]) -> None:
    index_path = series_root / "canon" / "index.json"
    data: Dict[str, Any] = {}
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    if not isinstance(data, dict):
        data = {}
    existing = data.get("characters")
    if not isinstance(existing, list):
        existing = []
    by_id = {str(item.get("character_id")): item for item in existing if isinstance(item, dict)}
    for entry in entries:
        char_id = str(entry.get("character_id"))
        if not char_id:
            continue
        by_id[char_id] = entry
    data["characters"] = list(by_id.values())
    index_path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def _update_book_index(book_root: Path, entries: List[Dict[str, str]]) -> None:
    characters_dir = book_root / "draft" / "context" / "characters"
    characters_dir.mkdir(parents=True, exist_ok=True)
    index_path = characters_dir / "index.json"
    data: Dict[str, Any] = {}
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    if not isinstance(data, dict):
        data = {}
    existing = data.get("characters")
    if not isinstance(existing, list):
        existing = []
    by_id = {str(item.get("character_id")): item for item in existing if isinstance(item, dict)}
    for entry in entries:
        char_id = str(entry.get("character_id"))
        if not char_id:
            continue
        by_id[char_id] = entry
    data["characters"] = list(by_id.values())
    index_path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def generate_characters(
    workspace: Path,
    book_id: str,
    count: Optional[int] = None,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
) -> List[Path]:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    book_path = book_root / "book.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    book = _read_json(book_path)
    outline_characters = _load_outline_characters(book_root)
    if not outline_characters:
        raise ValueError("Outline characters not found; generate outline first.")

    if count is not None and count > 0:
        outline_characters = outline_characters[:count]

    series_root = _series_root(workspace, book)
    _ensure_series_dirs(series_root)
    series_manifest_path = series_root / "series.json"
    series_manifest = {}
    if series_manifest_path.exists():
        try:
            series_manifest = json.loads(series_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            series_manifest = {}

    template = _resolve_template(book_root, "characters_generate.md")
    prompt = render_template_file(
        template,
        {
            "book": book,
            "outline_characters": outline_characters,
            "series": series_manifest,
        },
    )

    if client is None:
        config = load_config()
        client = get_llm_client(config, phase="characters")
        if model is None:
            model = resolve_model("characters", config)
    elif model is None:
        model = "default"

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    request = {"model": model, "temperature": 0.5, "max_tokens": 32768}
    key_slot = getattr(client, "key_slot", None)
    log_extra: Dict[str, Any] = {"book_id": book_id}
    if key_slot:
        log_extra["key_slot"] = key_slot

    try:
        response = client.chat(messages, model=model, temperature=0.5, max_tokens=32768)
    except LLMRequestError as exc:
        if should_log_llm():
            log_llm_error(workspace, "characters_generate_error", exc, request=request, messages=messages, extra=log_extra)
        raise

    log_path: Optional[Path] = None
    if should_log_llm():
        log_path = log_llm_response(workspace, "characters_generate", response, request=request, messages=messages, extra=log_extra)

    data = _extract_json(response.text)
    characters = data.get("characters")
    if not isinstance(characters, list):
        raise ValueError(f"Invalid characters response. (raw response logged to {log_path})")

    outline_by_id = {}
    outline_by_name = {}
    for stub in outline_characters:
        if not isinstance(stub, dict):
            continue
        char_id = str(stub.get("character_id") or "").strip()
        name = str(stub.get("name") or "").strip()
        if char_id:
            outline_by_id[char_id] = stub
        if name:
            outline_by_name[name.lower()] = char_id

    updated_paths: List[Path] = []
    series_index_entries: List[Dict[str, str]] = []
    book_index_entries: List[Dict[str, str]] = []

    for char in characters:
        if not isinstance(char, dict):
            continue
        char_id = str(char.get("character_id") or "").strip()
        if not char_id:
            name = str(char.get("name") or "").strip()
            if name and name.lower() in outline_by_name:
                char_id = outline_by_name[name.lower()]
                char["character_id"] = char_id
        if not char_id:
            raise ValueError("Character entry missing character_id and could not be inferred.")

        slug = _character_slug(char_id)
        char_dir = series_root / "canon" / "characters" / slug
        char_dir.mkdir(parents=True, exist_ok=True)

        canonical = {
            "schema_version": "1.0",
            "character_id": char_id,
            "name": char.get("name", ""),
            "pronouns": char.get("pronouns", ""),
            "role": char.get("role", ""),
            "persona": char.get("persona", {}),
            "voice_notes": char.get("voice_notes", []),
        }
        canon_path = char_dir / "character.json"
        canon_path.write_text(json.dumps(canonical, ensure_ascii=True, indent=2), encoding="utf-8")
        updated_paths.append(canon_path)

        state = {
            "schema_version": "1.0",
            "character_id": char_id,
            "name": char.get("name", ""),
            "inventory": char.get("inventory", []),
            "containers": char.get("containers", []),
            "invariants": char.get("invariants", []),
            "history": [],
            "updated_at": _now_iso(),
        }

        characters_dir = book_root / "draft" / "context" / "characters"
        characters_dir.mkdir(parents=True, exist_ok=True)
        state_path = characters_dir / f"{slug}.state.json"
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        updated_paths.append(state_path)

        series_index_entries.append({
            "character_id": char_id,
            "path": str(canon_path.relative_to(series_root)).replace('\\', '/'),
        })
        book_index_entries.append({
            "character_id": char_id,
            "state_path": str(state_path.relative_to(book_root)).replace('\\', '/'),
            "canon_path": str(canon_path.relative_to(series_root)).replace('\\', '/'),
        })

    _update_series_index(series_root, series_index_entries)
    _update_book_index(book_root, book_index_entries)

    state_path = book_root / "state.json"
    if state_path.exists():
        state_data = _read_json(state_path)
        state_data["characters"] = {
            "status": "READY",
            "updated_at": _now_iso(),
            "count": len(book_index_entries),
        }
        validate_json(state_data, "state")
        state_path.write_text(json.dumps(state_data, ensure_ascii=True, indent=2), encoding="utf-8")

    return updated_paths


def characters_ready(book_root: Path) -> bool:
    index_path = book_root / "draft" / "context" / "characters" / "index.json"
    if not index_path.exists():
        return False
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    entries = data.get("characters") if isinstance(data, dict) else None
    return isinstance(entries, list) and len(entries) > 0
