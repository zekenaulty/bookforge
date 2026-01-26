from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import json
import shutil

from bookforge.prompt.system import write_system_prompt
from bookforge.util.paths import repo_root
from bookforge.util.schema import SCHEMA_VERSION, validate_json


DEFAULT_VOICE = {
    "pov": "third_limited",
    "tense": "past",
    "style_tags": ["no-recaps", "forward-motion", "tight-prose"],
}

DEFAULT_INVARIANTS = [
    "No world resets.",
    "No convenient amnesia as a continuity device.",
    "Do not change established names/relationships.",
]

DEFAULT_PAGE_METRICS = {
    "words_per_page": 250,
    "chars_per_page": 1500,
}

DEFAULT_BUDGETS = {
    "max_new_entities": 1,
    "max_new_threads": 1,
    "min_scene_words": 0,
    "max_scene_words": 0,
}

PROMPT_TEMPLATE_FILES = [
    "outline.md",
    "plan.md",
    "write.md",
    "lint.md",
    "repair.md",
    "continuity_pack.md",
    "characters_generate.md",
    "style_anchor.md",
    "system_base.md",
    "output_contract.md",
]



def parse_genre(value: str) -> List[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise ValueError("--genre must include at least one genre.")
    return items


def _parse_target_value(raw: str) -> Any:
    value = raw.strip()
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def parse_targets(values: Iterable[str]) -> Dict[str, Any]:
    targets: Dict[str, Any] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Invalid --target value: {raw}. Expected key=value.")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid --target value: {raw}. Key cannot be empty.")
        targets[key] = _parse_target_value(value)
    return targets


def _parse_author_ref(author_ref: str) -> Tuple[str, str]:
    parts = [part for part in author_ref.split("/") if part]
    if len(parts) != 2:
        raise ValueError("--author-ref must look like <author_slug>/vN")
    return parts[0], parts[1]



def _resolve_series_id(series_id: Optional[str], book_id: str) -> str:
    if series_id:
        cleaned = series_id.strip()
        if cleaned:
            return cleaned
    return book_id


def _ensure_series_workspace(workspace: Path, series_id: str, book_id: str) -> None:
    series_root = workspace / "series" / series_id
    (series_root / "canon" / "characters").mkdir(parents=True, exist_ok=True)
    (series_root / "canon" / "locations").mkdir(parents=True, exist_ok=True)
    (series_root / "canon" / "rules").mkdir(parents=True, exist_ok=True)
    (series_root / "canon" / "threads").mkdir(parents=True, exist_ok=True)

    series_manifest_path = series_root / "series.json"
    if series_manifest_path.exists():
        try:
            existing = json.loads(series_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid series.json: {series_manifest_path}") from exc
        if not isinstance(existing, dict):
            raise ValueError(f"Invalid series.json: {series_manifest_path}")
        books = existing.get("books", [])
        if not isinstance(books, list):
            books = []
        if book_id not in books:
            books.append(book_id)
        existing["schema_version"] = SCHEMA_VERSION
        existing["series_id"] = existing.get("series_id", series_id)
        existing["books"] = books
        series_manifest = existing
    else:
        series_manifest = {
            "schema_version": SCHEMA_VERSION,
            "series_id": series_id,
            "books": [book_id],
        }
    series_manifest_path.write_text(
        json.dumps(series_manifest, ensure_ascii=True, indent=2), encoding="utf-8"
    )

    series_index_path = series_root / "canon" / "index.json"
    if not series_index_path.exists():
        series_index_path.write_text("{}", encoding="utf-8")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _render_book_constitution(book: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"Title: {book.get('title', '')}")
    lines.append(f"Book ID: {book.get('book_id', '')}")
    lines.append(f"Author Ref: {book.get('author_ref', '')}")

    genre = ", ".join([str(item) for item in book.get("genre", []) if str(item).strip()])
    if genre:
        lines.append(f"Genre: {genre}")

    series_id = book.get("series_id")
    if series_id:
        lines.append(f"Series ID: {series_id}")

    series_ref = book.get("series_ref")
    if series_ref:
        lines.append(f"Series Ref: {series_ref}")

    voice = book.get("voice", {}) if isinstance(book.get("voice"), dict) else {}
    if voice:
        lines.append("\nVoice")
        pov = voice.get("pov")
        tense = voice.get("tense")
        style_tags = voice.get("style_tags", [])
        if pov:
            lines.append(f"- POV: {pov}")
        if tense:
            lines.append(f"- Tense: {tense}")
        if style_tags:
            lines.append(f"- Style tags: {', '.join([str(tag) for tag in style_tags])}")

    targets = book.get("targets", {}) if isinstance(book.get("targets"), dict) else {}
    if targets:
        lines.append("\nTargets")
        for key in sorted(targets.keys()):
            lines.append(f"- {key}: {targets[key]}")

    page_metrics = book.get("page_metrics", {}) if isinstance(book.get("page_metrics"), dict) else {}
    if page_metrics:
        lines.append("\nPage Metrics")
        words = page_metrics.get("words_per_page")
        chars = page_metrics.get("chars_per_page")
        if words is not None:
            lines.append(f"- Words per page: {words}")
        if chars is not None:
            lines.append(f"- Chars per page: {chars}")

    invariants = book.get("invariants", []) if isinstance(book.get("invariants"), list) else []
    if invariants:
        lines.append("\nInvariants")
        for item in invariants:
            lines.append(f"- {item}")

    return "\n".join(lines).strip() + "\n"


def _copy_prompt_templates(book_root: Path) -> None:
    root = repo_root(Path(__file__).resolve())
    prompt_src = root / "resources" / "prompt_templates"
    templates_dir = book_root / "prompts" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    for name in PROMPT_TEMPLATE_FILES:
        shutil.copyfile(prompt_src / name, templates_dir / name)

    registry_src = root / "resources" / "prompt_registry.json"
    (book_root / "prompts").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(registry_src, book_root / "prompts" / "registry.json")


def init_book_workspace(
    workspace: Path,
    book_id: str,
    author_ref: str,
    title: str,
    genre: List[str],
    targets: Dict[str, Any],
    series_id: Optional[str] = None,
) -> Path:
    book_root = workspace / "books" / book_id
    if book_root.exists():
        raise FileExistsError(f"Book workspace already exists: {book_root}")

    author_slug, author_version = _parse_author_ref(author_ref)
    author_fragment_path = workspace / "authors" / author_slug / author_version / "system_fragment.md"
    if not author_fragment_path.exists():
        raise FileNotFoundError(f"Author fragment not found: {author_fragment_path}")

    resolved_series_id = _resolve_series_id(series_id, book_id)

    book = {
        "schema_version": SCHEMA_VERSION,
        "book_id": book_id,
        "title": title,
        "genre": genre,
        "targets": targets,
        "voice": DEFAULT_VOICE,
        "invariants": DEFAULT_INVARIANTS,
        "author_ref": author_ref,
        "page_metrics": DEFAULT_PAGE_METRICS,
    }
    book["series_id"] = resolved_series_id
    book["series_ref"] = f"series/{resolved_series_id}"

    state = {
        "schema_version": SCHEMA_VERSION,
        "status": "NEW",
        "cursor": {
            "chapter": 0,
            "scene": 0,
        },
        "world": {
            "time": {},
            "location": "",
            "cast_present": [],
            "open_threads": [],
            "recent_facts": [],
        },
        "summary": {
            "last_scene": [],
            "chapter_so_far": [],
            "story_so_far": [],
            "key_facts_ring": [],
            "must_stay_true": [],
        },
        "budgets": dict(DEFAULT_BUDGETS),
        "duplication_warnings_in_row": 0,
    }

    validate_json(book, "book")
    validate_json(state, "state")

    (book_root / "prompts" / "templates").mkdir(parents=True, exist_ok=True)
    (book_root / "outline" / "chapters").mkdir(parents=True, exist_ok=True)
    (book_root / "canon" / "characters").mkdir(parents=True, exist_ok=True)
    (book_root / "canon" / "locations").mkdir(parents=True, exist_ok=True)
    (book_root / "canon" / "rules").mkdir(parents=True, exist_ok=True)
    (book_root / "canon" / "threads").mkdir(parents=True, exist_ok=True)
    (book_root / "draft" / "context").mkdir(parents=True, exist_ok=True)
    (book_root / "draft" / "chapters").mkdir(parents=True, exist_ok=True)
    (book_root / "exports").mkdir(parents=True, exist_ok=True)
    (book_root / "logs").mkdir(parents=True, exist_ok=True)

    _ensure_series_workspace(workspace, resolved_series_id, book_id)

    (book_root / "book.json").write_text(json.dumps(book, ensure_ascii=True, indent=2), encoding="utf-8")
    (book_root / "state.json").write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
    (book_root / "canon" / "index.json").write_text("{}", encoding="utf-8")
    (book_root / "draft" / "context" / "bible.md").write_text("", encoding="utf-8")
    (book_root / "draft" / "context" / "last_excerpt.md").write_text("", encoding="utf-8")

    _copy_prompt_templates(book_root)

    author_fragment = _read_text(author_fragment_path)
    base_rules = _read_text(book_root / "prompts" / "templates" / "system_base.md")
    output_contract = _read_text(book_root / "prompts" / "templates" / "output_contract.md")

    constitution_text = _render_book_constitution(book)
    constitution_path = book_root / "prompts" / "book_constitution.md"
    constitution_path.write_text(constitution_text, encoding="utf-8")

    system_path = book_root / "prompts" / "system_v1.md"
    write_system_prompt(system_path, base_rules, constitution_text, author_fragment, output_contract)

    return book_root



def update_book_templates(workspace: Path, book_id: Optional[str] = None) -> List[Path]:
    books_root = workspace / "books"
    if book_id:
        book_root = books_root / book_id
        if not book_root.exists():
            raise FileNotFoundError(f"Book workspace not found: {book_root}")
        book_roots = [book_root]
    else:
        if not books_root.exists():
            raise FileNotFoundError(f"Books folder not found: {books_root}")
        book_roots = [path for path in books_root.iterdir() if path.is_dir()]

    updated: List[Path] = []
    for book_root in book_roots:
        book_path = book_root / "book.json"
        if not book_path.exists():
            continue
        _copy_prompt_templates(book_root)

        book = json.loads(book_path.read_text(encoding="utf-8"))
        constitution_text = _render_book_constitution(book)
        constitution_path = book_root / "prompts" / "book_constitution.md"
        constitution_path.write_text(constitution_text, encoding="utf-8")

        author_ref = str(book.get("author_ref", "")).strip()
        author_fragment_path = workspace / "authors" / Path(author_ref) / "system_fragment.md"
        if not author_fragment_path.exists():
            raise FileNotFoundError(f"Author fragment not found: {author_fragment_path}")
        author_fragment = _read_text(author_fragment_path)

        base_rules = _read_text(book_root / "prompts" / "templates" / "system_base.md")
        output_contract = _read_text(book_root / "prompts" / "templates" / "output_contract.md")

        system_path = book_root / "prompts" / "system_v1.md"
        write_system_prompt(system_path, base_rules, constitution_text, author_fragment, output_contract)

        updated.append(book_root)

    return updated


def reset_book_workspace(workspace: Path, book_id: str) -> Path:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    book_path = book_root / "book.json"
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"

    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")

    existing_state: Dict[str, Any] = {}
    if state_path.exists():
        try:
            existing_state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_state = {}

    budgets = dict(DEFAULT_BUDGETS)
    existing_budgets = existing_state.get("budgets") if isinstance(existing_state, dict) else None
    if isinstance(existing_budgets, dict):
        for key, value in existing_budgets.items():
            if key in DEFAULT_BUDGETS:
                if isinstance(value, int):
                    budgets[key] = value
                elif isinstance(value, float):
                    budgets[key] = int(value)
                elif isinstance(value, str) and value.strip().isdigit():
                    budgets[key] = int(value)
            else:
                budgets[key] = value

    status = "OUTLINED" if outline_path.exists() else "NEW"
    state = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "cursor": {
            "chapter": 0,
            "scene": 0,
        },
        "world": {
            "time": {},
            "location": "",
            "cast_present": [],
            "open_threads": [],
            "recent_facts": [],
        },
        "summary": {
            "last_scene": [],
            "chapter_so_far": [],
            "story_so_far": [],
            "key_facts_ring": [],
            "must_stay_true": [],
        },
        "budgets": budgets,
        "duplication_warnings_in_row": 0,
    }

    validate_json(state, "state")
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    chapters_dir = book_root / "draft" / "chapters"
    if chapters_dir.exists():
        shutil.rmtree(chapters_dir)
    chapters_dir.mkdir(parents=True, exist_ok=True)

    context_dir = book_root / "draft" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "bible.md").write_text("", encoding="utf-8")
    (context_dir / "last_excerpt.md").write_text("", encoding="utf-8")
    continuity_path = context_dir / "continuity_pack.json"
    if continuity_path.exists():
        continuity_path.unlink()

    continuity_history_dir = context_dir / "continuity_history"
    if continuity_history_dir.exists():
        shutil.rmtree(continuity_history_dir)

    chapter_summaries_dir = context_dir / "chapter_summaries"
    if chapter_summaries_dir.exists():
        shutil.rmtree(chapter_summaries_dir)

    return book_root
