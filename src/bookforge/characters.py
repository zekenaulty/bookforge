from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import re
import hashlib

from bookforge.config.env import load_config, read_int_env
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import Message
from bookforge.prompt.renderer import render_template_file
from bookforge.util.paths import repo_root
from bookforge.util.json_extract import extract_json
from bookforge.util.schema import validate_json

DEFAULT_JSON_RETRY_COUNT = 1
DEFAULT_APPEARANCE_MAX_TOKENS = 4096


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _json_retry_count() -> int:
    return max(0, _int_env("BOOKFORGE_JSON_RETRY_COUNT", DEFAULT_JSON_RETRY_COUNT))


def _appearance_max_tokens() -> int:
    return max(512, _int_env("BOOKFORGE_APPEARANCE_MAX_TOKENS", DEFAULT_APPEARANCE_MAX_TOKENS))


def _extract_json(text: str) -> Dict[str, Any]:
    data = extract_json(text, label="Characters response")
    if not isinstance(data, dict):
        raise ValueError("Characters response JSON must be an object.")
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

def _load_outline(book_root: Path) -> Dict[str, Any]:
    outline_path = book_root / "outline" / "outline.json"
    if not outline_path.exists():
        return {}
    try:
        data = _read_json(outline_path)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _opening_outline_context(outline: Dict[str, Any]) -> Dict[str, Any]:
    chapters = outline.get("chapters") if isinstance(outline, dict) else None
    if not isinstance(chapters, list) or not chapters:
        return {}

    def chapter_key(value: Any) -> int:
        if isinstance(value, dict):
            raw = value.get("chapter_id")
            if isinstance(raw, int):
                return raw
            if isinstance(raw, str) and raw.isdigit():
                return int(raw)
        return 10000

    chapter = sorted(chapters, key=chapter_key)[0] if chapters else {}
    sections = chapter.get("sections") if isinstance(chapter, dict) else None
    if not isinstance(sections, list) or not sections:
        sections = []
    section = sections[0] if sections else {}
    scenes = section.get("scenes") if isinstance(section, dict) else None
    if not isinstance(scenes, list) or not scenes:
        scenes = []
    scene = scenes[0] if scenes else {}

    return {
        "chapter": {
            "chapter_id": chapter.get("chapter_id"),
            "title": chapter.get("title"),
            "goal": chapter.get("goal"),
            "chapter_role": chapter.get("chapter_role"),
            "stakes_shift": chapter.get("stakes_shift"),
            "bridge": chapter.get("bridge"),
            "pacing": chapter.get("pacing"),
        },
        "section": {
            "section_id": section.get("section_id"),
            "title": section.get("title"),
            "intent": section.get("intent"),
        },
        "scene": {
            "scene_id": scene.get("scene_id"),
            "summary": scene.get("summary"),
            "type": scene.get("type"),
            "outcome": scene.get("outcome"),
            "characters": scene.get("characters"),
            "introduces": scene.get("introduces"),
            "threads": scene.get("threads"),
        },
    }


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


def _short_id_hash(value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return digest[:8]


def _character_state_filename(character_id: str) -> str:
    slug = _character_slug(character_id)
    return f"{slug}__{_short_id_hash(character_id)}.state.json"


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


def _normalize_titles_in_continuity_state(continuity_state: Dict[str, Any]) -> None:
    if not isinstance(continuity_state, dict):
        return
    if "titles" in continuity_state:
        continuity_state["titles"] = _normalize_titles_value(continuity_state.get("titles"))



def _workspace_root_from_book_root(book_root: Path) -> Path:
    return book_root.parent.parent


def _series_root_for_book_root(book_root: Path) -> Path:
    book_path = book_root / "book.json"
    book: Dict[str, Any] = {}
    if book_path.exists():
        try:
            book = _read_json(book_path)
        except json.JSONDecodeError:
            book = {}
    workspace = _workspace_root_from_book_root(book_root)
    return _series_root(workspace, book)


def _load_character_canon(book_root: Path, character_id: str) -> Optional[Dict[str, Any]]:
    series_root = _series_root_for_book_root(book_root)
    slug = _character_slug(character_id)
    canon_path = series_root / "canon" / "characters" / slug / "character.json"
    if not canon_path.exists():
        return None
    try:
        data = _read_json(canon_path)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _appearance_current_from_base(base: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(base, dict):
        return None
    current: Dict[str, Any] = {}
    for key in ("version", "summary", "atoms", "marks", "alias_map", "appearance_art", "attire"):
        value = base.get(key)
        if isinstance(value, (dict, list, str, int, float, bool)):
            current[key] = value
    if not any(key in current for key in ("atoms", "marks", "summary")):
        return None
    return current


def _ensure_character_appearance_current(
    book_root: Path,
    state: Dict[str, Any],
    character_id: str,
    state_path: Optional[Path] = None,
) -> bool:
    current = state.get("appearance_current")
    if isinstance(current, dict) and any(key in current for key in ("atoms", "marks", "summary")):
        return False

    base = state.get("appearance_base") if isinstance(state.get("appearance_base"), dict) else None
    if base is None:
        canon = _load_character_canon(book_root, character_id)
        base = canon.get("appearance_base") if isinstance(canon, dict) else None

    derived = _appearance_current_from_base(base)
    if not isinstance(derived, dict):
        return False

    state["appearance_current"] = derived
    state["appearance_projection_pending"] = True
    history = state.get("appearance_history")
    if not isinstance(history, list):
        state["appearance_history"] = []

    if state_path is not None:
        state["updated_at"] = _now_iso()
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
    return True

def _render_appearance_projection_prompt(
    book_root: Path,
    character: Dict[str, Any],
    appearance_base: Dict[str, Any],
    appearance_current: Dict[str, Any],
) -> str:
    template = _resolve_template(book_root, "appearance_projection.md")
    return render_template_file(
        template,
        {
            "character": character,
            "appearance_base": appearance_base,
            "appearance_current": appearance_current,
        },
    )


def _refresh_character_appearance_projection(
    book_root: Path,
    character_id: str,
    *,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
    force: bool = False,
) -> bool:
    state_path = resolve_character_state_path(book_root, character_id)
    if state_path is None or not state_path.exists():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(state, dict):
        return False

    _ensure_character_appearance_current(book_root, state, character_id, state_path)
    appearance_current = state.get("appearance_current")
    if not isinstance(appearance_current, dict):
        return False

    has_summary = isinstance(appearance_current.get("summary"), str) and appearance_current.get("summary", "").strip()
    pending = bool(state.get("appearance_projection_pending"))
    if not force and not pending and has_summary:
        return False

    canon = _load_character_canon(book_root, character_id) or {}
    appearance_base = canon.get("appearance_base") if isinstance(canon.get("appearance_base"), dict) else {}

    character = {
        "character_id": character_id,
        "name": state.get("name") or canon.get("name") or "",
    }

    prompt = _render_appearance_projection_prompt(book_root, character, appearance_base, appearance_current)

    if client is None:
        config = load_config()
        client = get_llm_client(config, phase="characters")
        if model is None:
            model = resolve_model("characters", config)
    elif model is None:
        model = "default"

    system_path = book_root / "prompts" / "system_v1.md"
    system_prompt = system_path.read_text(encoding="utf-8") if system_path.exists() else ""
    messages: List[Message] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    request = {"model": model, "temperature": 0.3, "max_tokens": _appearance_max_tokens()}
    workspace = _workspace_root_from_book_root(book_root)
    key_slot = getattr(client, "key_slot", None)
    log_extra: Dict[str, Any] = {"book_id": book_root.name, "character_id": character_id}
    if key_slot:
        log_extra["key_slot"] = key_slot

    try:
        response = client.chat(messages, model=model, temperature=0.3, max_tokens=_appearance_max_tokens())
    except LLMRequestError as exc:
        if should_log_llm():
            log_llm_error(workspace, "appearance_projection_error", exc, request=request, messages=messages, extra=log_extra)
        raise

    if should_log_llm():
        log_llm_response(workspace, "appearance_projection", response, request=request, messages=messages, extra=log_extra)

    data = _extract_json(response.text)
    summary = data.get("summary") if isinstance(data, dict) else None
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Appearance projection response missing required summary.")

    appearance_current["summary"] = summary.strip()
    appearance_art = data.get("appearance_art") if isinstance(data, dict) else None
    if isinstance(appearance_art, dict):
        appearance_current["appearance_art"] = appearance_art

    state["appearance_current"] = appearance_current
    state["appearance_projection_pending"] = False
    state["updated_at"] = _now_iso()
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
    return True


def refresh_appearance_projections(
    book_root: Path,
    character_ids: List[str],
    *,
    force: bool = False,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
) -> List[str]:
    if not character_ids:
        return []
    config = load_config() if client is None else None
    if client is None:
        client = get_llm_client(config, phase="characters")
    if model is None:
        model = resolve_model("characters", config)
    refreshed: List[str] = []
    seen = set()
    for char_id in character_ids:
        cid = str(char_id).strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        if _refresh_character_appearance_projection(book_root, cid, client=client, model=model, force=force):
            refreshed.append(cid)
    return refreshed

def _unique_state_path(characters_dir: Path, character_id: str) -> Path:
    base_path = characters_dir / _character_state_filename(character_id)
    if base_path.exists():
        try:
            data = json.loads(base_path.read_text(encoding="utf-8"))
            if str(data.get("character_id") or "").strip() == str(character_id).strip():
                return base_path
        except json.JSONDecodeError:
            pass
        from datetime import datetime, timezone
        slug = _character_slug(character_id)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return characters_dir / f"{slug}__{stamp}.state.json"
    return base_path


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


def _read_book_index(book_root: Path) -> Dict[str, str]:
    index_path = book_root / "draft" / "context" / "characters" / "index.json"
    if not index_path.exists():
        return {}
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    entries = data.get("characters") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return {}
    mapping: Dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        char_id = str(entry.get("character_id") or "").strip()
        state_path = str(entry.get("state_path") or "").strip()
        if char_id and state_path:
            mapping[char_id] = state_path
    return mapping


def _persist_book_index(book_root: Path, index_map: Dict[str, str]) -> None:
    entries: List[Dict[str, str]] = []
    for char_id, state_path in index_map.items():
        entries.append({"character_id": char_id, "state_path": state_path})
    if entries:
        _update_book_index(book_root, entries)


def ensure_character_index(book_root: Path) -> Dict[str, str]:
    characters_dir = book_root / "draft" / "context" / "characters"
    if not characters_dir.exists():
        return {}

    index_map = _read_book_index(book_root)
    if index_map:
        missing = [
            char_id
            for char_id, rel_path in index_map.items()
            if not (book_root / rel_path).exists()
        ]
        if not missing:
            return index_map

    rebuilt: Dict[str, str] = {}
    for path in characters_dir.glob("*.state.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        char_id = str(data.get("character_id") or "").strip()
        if not char_id:
            continue
        rel_path = str(path.relative_to(book_root)).replace("\\", "/")
        rebuilt[char_id] = rel_path

    if rebuilt:
        _persist_book_index(book_root, rebuilt)
        return rebuilt

    return index_map


def resolve_character_state_path(book_root: Path, character_id: str) -> Optional[Path]:
    character_id = str(character_id or "").strip()
    if not character_id:
        return None
    characters_dir = book_root / "draft" / "context" / "characters"
    index_map = ensure_character_index(book_root)
    rel_path = index_map.get(character_id)
    if rel_path:
        candidate = book_root / rel_path
        if candidate.exists():
            return candidate

    slug = _character_slug(character_id)
    candidates = sorted(characters_dir.glob(f"{slug}__*.state.json"))
    if candidates:
        chosen = candidates[0]
        rel_path = str(chosen.relative_to(book_root)).replace("\\", "/")
        index_map[character_id] = rel_path
        _persist_book_index(book_root, index_map)
        return chosen

    legacy = characters_dir / f"{slug}.state.json"
    if legacy.exists():
        rel_path = str(legacy.relative_to(book_root)).replace("\\", "/")
        index_map[character_id] = rel_path
        _persist_book_index(book_root, index_map)
        return legacy

    return None


def create_character_state_path(book_root: Path, character_id: str) -> Path:
    characters_dir = book_root / "draft" / "context" / "characters"
    characters_dir.mkdir(parents=True, exist_ok=True)
    state_path = _unique_state_path(characters_dir, character_id)
    rel_path = str(state_path.relative_to(book_root)).replace("\\", "/")
    index_map = ensure_character_index(book_root)
    index_map[str(character_id).strip()] = rel_path
    _persist_book_index(book_root, index_map)
    return state_path


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
    outline = _load_outline(book_root)
    outline_opening = _opening_outline_context(outline)
    outline_opening_json = json.dumps(outline_opening, ensure_ascii=True, indent=2) if outline_opening else "{}"
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
            "outline_opening": outline_opening_json,
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

    retries = _json_retry_count()
    parse_attempt = 0
    while True:
        try:
            data = _extract_json(response.text)
            break
        except ValueError as exc:
            if parse_attempt >= retries:
                raise ValueError(f"{exc} (raw response logged to {log_path})") from exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return ONLY the JSON object. No prose, no markdown, no commentary.",
            })
            response = client.chat(retry_messages, model=model, temperature=0.5, max_tokens=32768)
            label = f"characters_generate_json_retry{parse_attempt + 1}"
            if should_log_llm():
                log_path = log_llm_response(workspace, label, response, request=request, messages=retry_messages, extra=log_extra)
            parse_attempt += 1

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

        appearance_base = char.get("appearance_base")
        if not isinstance(appearance_base, dict):
            appearance_base = {}

        canonical = {
            "schema_version": "1.0",
            "character_id": char_id,
            "name": char.get("name", ""),
            "pronouns": char.get("pronouns", ""),
            "role": char.get("role", ""),
            "persona": char.get("persona", {}),
            "appearance_base": appearance_base,
            "voice_notes": char.get("voice_notes", []),
        }
        canon_path = char_dir / "character.json"
        canon_path.write_text(json.dumps(canonical, ensure_ascii=True, indent=2), encoding="utf-8")
        updated_paths.append(canon_path)

        continuity_state = char.get("character_continuity_system_state")
        if not isinstance(continuity_state, dict):
            continuity_state = {}
        for key in (
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
        ):
            value = char.get(key)
            if key in continuity_state:
                continue
            if isinstance(value, (dict, list, str, int, float, bool)):
                continuity_state[key] = value

        _normalize_titles_in_continuity_state(continuity_state)

        stats_mirror = continuity_state.get("stats") if isinstance(continuity_state.get("stats"), dict) else {}
        skills_mirror = continuity_state.get("skills") if isinstance(continuity_state.get("skills"), dict) else {}

        appearance_current = char.get("appearance_current")
        if not isinstance(appearance_current, dict):
            appearance_current = _appearance_current_from_base(appearance_base) or {}

        state = {
            "schema_version": "1.0",
            "character_id": char_id,
            "name": char.get("name", ""),
            "inventory": char.get("inventory", []),
            "containers": char.get("containers", []),
            "appearance_current": appearance_current,
            "appearance_history": [],
            "character_continuity_system_state": continuity_state,
            "stats": stats_mirror,
            "skills": skills_mirror,
            "invariants": char.get("invariants", []),
            "history": [],
            "updated_at": _now_iso(),
        }
        characters_dir = book_root / "draft" / "context" / "characters"
        characters_dir.mkdir(parents=True, exist_ok=True)
        state_path = _unique_state_path(characters_dir, char_id)
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
    index_map = ensure_character_index(book_root)
    if not index_map:
        return False
    for rel_path in index_map.values():
        if not (book_root / rel_path).exists():
            return False
    return True























