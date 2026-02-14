from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import json
import os
import shutil
import hashlib
from datetime import datetime, timezone

from bookforge.prompt.composition import compose_prompt_templates
from bookforge.prompt.system import write_system_prompt
from bookforge.memory.durable_state import ensure_durable_state_files
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
    "outline_phase_01_chapter_spine.md",
    "outline_phase_02_section_architecture.md",
    "outline_phase_03_scene_draft.md",
    "outline_phase_04_transition_causality_refinement.md",
    "outline_phase_05_cast_function_refinement.md",
    "outline_phase_06_thread_payoff_refinement.md",
    "plan.md",
    "preflight.md",
    "write.md",
    "lint.md",
    "repair.md",
    "state_repair.md",
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
    prompt_src = book_root / "prompts" / ".composition_build"
    compose_prompt_templates(output_dir=prompt_src, write_reports=False, enforce_checksums=False)

    templates_dir = book_root / "prompts" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    for name in PROMPT_TEMPLATE_FILES:
        shutil.copyfile(prompt_src / name, templates_dir / name)

    if prompt_src.exists():
        shutil.rmtree(prompt_src)

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
            "pending_story_rollups": [],
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
    ensure_durable_state_files(book_root)
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


def _remove_file_if_exists(path: Path, report: Dict[str, Any], key: str) -> bool:
    if not path.exists() or not path.is_file():
        return False
    path.unlink()
    report["files_deleted"] = int(report.get("files_deleted", 0)) + 1
    report[key] = int(report.get(key, 0)) + 1
    return True


def _remove_dir_if_exists(path: Path, report: Dict[str, Any], key: str) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    shutil.rmtree(path)
    report["dirs_deleted"] = int(report.get("dirs_deleted", 0)) + 1
    report[key] = int(report.get(key, 0)) + 1
    return True


def _ensure_dir(path: Path, report: Dict[str, Any], key: str) -> None:
    created = not path.exists()
    path.mkdir(parents=True, exist_ok=True)
    if created:
        report["dirs_recreated"] = int(report.get("dirs_recreated", 0)) + 1
        report[key] = int(report.get(key, 0)) + 1


def _clear_workspace_logs(workspace: Path, book_id: str, logs_scope: str, report: Dict[str, Any]) -> None:
    logs_root = workspace / "logs" / "llm"
    if not logs_root.exists() or not logs_root.is_dir():
        return

    deleted = 0
    if logs_scope == "all":
        for candidate in logs_root.iterdir():
            if candidate.is_file():
                candidate.unlink()
                deleted += 1
        report["all_log_files_deleted"] = int(report.get("all_log_files_deleted", 0)) + deleted
    else:
        pattern = f"{book_id}_*"
        for candidate in logs_root.glob(pattern):
            if candidate.is_file():
                candidate.unlink()
                deleted += 1
        report["book_log_files_deleted"] = int(report.get("book_log_files_deleted", 0)) + deleted

    report["files_deleted"] = int(report.get("files_deleted", 0)) + deleted



def _path_size(path: Path) -> int:
    try:
        if path.is_file():
            return path.stat().st_size
        if path.is_dir():
            total = 0
            for root, _, files in os.walk(path):
                for name in files:
                    try:
                        total += (Path(root) / name).stat().st_size
                    except OSError:
                        continue
            return total
    except OSError:
        return 0
    return 0


def _collect_reset_archive_targets(
    workspace: Path,
    book_root: Path,
    book_id: str,
    keep_logs: bool,
    logs_scope: str,
    include_logs: bool,
) -> List[Path]:
    targets: List[Path] = []

    def _add_if_exists(candidate: Path) -> None:
        if candidate.exists():
            targets.append(candidate)

    # Files rewritten during reset.
    _add_if_exists(book_root / 'state.json')

    # Directories removed during reset.
    _add_if_exists(book_root / 'draft' / 'chapters')
    _add_if_exists(book_root / 'exports')
    _add_if_exists(book_root / 'logs')

    context_dir = book_root / 'draft' / 'context'
    _add_if_exists(context_dir / 'bible.md')
    _add_if_exists(context_dir / 'last_excerpt.md')
    _add_if_exists(context_dir / 'continuity_pack.json')
    _add_if_exists(context_dir / 'run_paused.json')

    _add_if_exists(context_dir / 'continuity_history')
    _add_if_exists(context_dir / 'chapter_summaries')
    _add_if_exists(context_dir / 'characters')
    _add_if_exists(context_dir / 'phase_history')

    _add_if_exists(context_dir / 'item_registry.json')
    _add_if_exists(context_dir / 'plot_devices.json')
    _add_if_exists(context_dir / 'durable_commits.json')

    _add_if_exists(context_dir / 'items')
    _add_if_exists(context_dir / 'plot_devices')

    if include_logs and not keep_logs:
        logs_root = workspace / 'logs' / 'llm'
        if logs_root.exists() and logs_root.is_dir():
            if logs_scope == 'all':
                for candidate in logs_root.iterdir():
                    if candidate.is_file():
                        targets.append(candidate)
            else:
                pattern = f"{book_id}_*"
                for candidate in logs_root.glob(pattern):
                    if candidate.is_file():
                        targets.append(candidate)

    # Deduplicate and ensure we don't include child paths when parent is already included.
    unique_targets = []
    seen = set()
    for target in sorted(targets, key=lambda p: len(str(p))):
        resolved = str(target.resolve())
        if resolved in seen:
            continue
        skip = False
        for parent in unique_targets:
            if target.resolve().is_relative_to(parent.resolve()):
                skip = True
                break
        if skip:
            continue
        unique_targets.append(target)
        seen.add(resolved)

    return unique_targets


def _validate_archive(archive_root: Path, workspace: Path, targets: List[Path]) -> None:
    if not archive_root.exists():
        raise RuntimeError('Archive root was not created.')
    manifest_path = archive_root / 'archive_manifest.json'
    if not manifest_path.exists():
        raise RuntimeError('Archive manifest missing; aborting reset.')
    for target in targets:
        rel = target.relative_to(workspace)
        dest = archive_root / rel
        if not dest.exists():
            raise RuntimeError(f"Archive missing expected path: {dest}")


def _archive_reset_targets(
    workspace: Path,
    book_id: str,
    targets: List[Path],
    archive_mode: str,
    include_logs: bool,
    logs_scope: str,
) -> Path:
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    rel_paths = sorted({str(target.relative_to(workspace)).replace('\\', '/') for target in targets})
    hash_seed = "\n".join(rel_paths).encode('utf-8') if rel_paths else b'empty'
    short_hash = hashlib.sha1(hash_seed).hexdigest()[:8]

    archive_root = workspace / 'archives' / book_id / f"reset_{timestamp}_{short_hash}"
    if archive_root.exists():
        suffix = 1
        while (workspace / 'archives' / book_id / f"reset_{timestamp}_{short_hash}_{suffix}").exists():
            suffix += 1
        archive_root = workspace / 'archives' / book_id / f"reset_{timestamp}_{short_hash}_{suffix}"

    archive_root.mkdir(parents=True, exist_ok=True)

    archive_mode = str(archive_mode).strip().lower()
    if archive_mode not in {'copy', 'move'}:
        raise ValueError("archive_mode must be 'copy' or 'move'.")

    sizes = {}
    total_size = 0
    for target in targets:
        rel = str(target.relative_to(workspace)).replace('\\', '/')
        size = _path_size(target)
        sizes[rel] = size
        total_size += size

    for target in targets:
        rel = target.relative_to(workspace)
        dest = archive_root / rel
        if target.is_dir():
            if archive_mode == 'copy':
                shutil.copytree(target, dest)
            else:
                shutil.move(str(target), str(dest))
        elif target.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            if archive_mode == 'copy':
                shutil.copy2(target, dest)
            else:
                shutil.move(str(target), str(dest))

    manifest = {
        'timestamp': timestamp,
        'book_id': book_id,
        'archive_mode': archive_mode,
        'include_logs': include_logs,
        'logs_scope': logs_scope,
        'purge_paths': rel_paths,
        'sizes': sizes,
        'total_size': total_size,
    }

    manifest_path = archive_root / 'archive_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding='utf-8')

    _validate_archive(archive_root, workspace, targets)
    return archive_root


def reset_book_workspace_detailed(
    workspace: Path,
    book_id: str,
    keep_logs: bool = False,
    logs_scope: str = "book",
    archive: bool = False,
    archive_mode: str = "copy",
    archive_logs: bool = False,
) -> Tuple[Path, Dict[str, Any]]:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    logs_scope = str(logs_scope).strip().lower()
    if logs_scope not in {"book", "all"}:
        raise ValueError("logs_scope must be 'book' or 'all'.")

    report: Dict[str, Any] = {
        "book_id": book_id,
        "files_deleted": 0,
        "dirs_deleted": 0,
        "dirs_recreated": 0,
        "state_rewritten": 0,
        "context_files_rewritten": 0,
        "book_log_files_deleted": 0,
        "all_log_files_deleted": 0,
        "durable_reinitialized": 0,
    }

    archive_root: Optional[Path] = None
    if archive:
        targets = _collect_reset_archive_targets(
            workspace=workspace,
            book_root=book_root,
            book_id=book_id,
            keep_logs=keep_logs,
            logs_scope=logs_scope,
            include_logs=archive_logs,
        )
        archive_root = _archive_reset_targets(
            workspace=workspace,
            book_id=book_id,
            targets=targets,
            archive_mode=archive_mode,
            include_logs=archive_logs,
            logs_scope=logs_scope,
        )
        report["archive_path"] = str(archive_root)
        report["archive_mode"] = archive_mode
        report["archive_logs"] = bool(archive_logs)
        report["archive_targets"] = len(targets)


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
            "pending_story_rollups": [],
        },
        "budgets": budgets,
        "duplication_warnings_in_row": 0,
    }

    validate_json(state, "state")
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
    report["state_rewritten"] = int(report.get("state_rewritten", 0)) + 1

    _remove_dir_if_exists(book_root / "draft" / "chapters", report, "chapters_dirs_deleted")
    _ensure_dir(book_root / "draft" / "chapters", report, "chapters_dirs_recreated")

    _remove_dir_if_exists(book_root / "exports", report, "exports_dirs_deleted")
    _ensure_dir(book_root / "exports", report, "exports_dirs_recreated")

    _remove_dir_if_exists(book_root / "logs", report, "book_logs_dirs_deleted")
    _ensure_dir(book_root / "logs", report, "book_logs_dirs_recreated")

    context_dir = book_root / "draft" / "context"
    _ensure_dir(context_dir, report, "context_dirs_recreated")
    (context_dir / "bible.md").write_text("", encoding="utf-8")
    (context_dir / "last_excerpt.md").write_text("", encoding="utf-8")
    report["context_files_rewritten"] = int(report.get("context_files_rewritten", 0)) + 2

    _remove_file_if_exists(context_dir / "continuity_pack.json", report, "continuity_files_deleted")
    _remove_file_if_exists(context_dir / "run_paused.json", report, "pause_markers_deleted")

    _remove_dir_if_exists(context_dir / "continuity_history", report, "continuity_dirs_deleted")
    _remove_dir_if_exists(context_dir / "chapter_summaries", report, "chapter_summary_dirs_deleted")
    _remove_dir_if_exists(context_dir / "characters", report, "character_dirs_deleted")
    _remove_dir_if_exists(context_dir / "phase_history", report, "phase_history_dirs_deleted")

    _remove_file_if_exists(context_dir / "item_registry.json", report, "durable_files_deleted")
    _remove_file_if_exists(context_dir / "plot_devices.json", report, "durable_files_deleted")
    _remove_file_if_exists(context_dir / "durable_commits.json", report, "durable_files_deleted")

    _remove_dir_if_exists(context_dir / "items", report, "durable_dirs_deleted")
    _remove_dir_if_exists(context_dir / "plot_devices", report, "durable_dirs_deleted")

    if not keep_logs:
        _clear_workspace_logs(workspace, book_id, logs_scope, report)

    ensure_durable_state_files(book_root)
    report["durable_reinitialized"] = int(report.get("durable_reinitialized", 0)) + 1

    return book_root, report


def reset_book_workspace(workspace: Path, book_id: str) -> Path:
    book_root, _ = reset_book_workspace_detailed(workspace=workspace, book_id=book_id)
    return book_root
