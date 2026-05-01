from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, ScopeSelector, TimelineNodeRef

from . import _common
from .workspace import current_execution_node


DEFAULT_READER_TEXT_LIMIT = 24_000
MAX_READER_TEXT_LIMIT = 80_000


@dataclass(frozen=True, slots=True)
class BookReaderScene:
    scene: int
    section: Optional[int]
    title: Optional[str]
    summary: Optional[str]
    status: str
    source_path: Optional[str]
    meta_path: Optional[str]
    character_count: int
    meta_summary: Optional[str]
    artifact_status: str = "authoritative"
    schema_version: str = "book_reader_scene_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scene": self.scene,
            "section": self.section,
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "source_path": self.source_path,
            "meta_path": self.meta_path,
            "character_count": self.character_count,
            "meta_summary": self.meta_summary,
            "artifact_status": self.artifact_status,
        }


@dataclass(frozen=True, slots=True)
class BookReaderChapter:
    chapter: int
    title: Optional[str]
    summary: Optional[str]
    status: str
    source_path: Optional[str]
    provisional_path: Optional[str]
    character_count: int
    scene_count: int
    scenes: List[BookReaderScene]
    artifact_status: str = "authoritative"
    schema_version: str = "book_reader_chapter_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "chapter": self.chapter,
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "source_path": self.source_path,
            "provisional_path": self.provisional_path,
            "character_count": self.character_count,
            "scene_count": self.scene_count,
            "artifact_status": self.artifact_status,
            "scenes": [scene.to_dict() for scene in self.scenes],
        }


@dataclass(frozen=True, slots=True)
class BookReaderSelection:
    chapter: Optional[int]
    scene: Optional[int]
    kind: str
    status: str
    source_path: Optional[str]
    text: str
    character_count: int
    truncated: bool
    artifact_status: str = "authoritative"
    schema_version: str = "book_reader_selection_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "chapter": self.chapter,
            "scene": self.scene,
            "kind": self.kind,
            "status": self.status,
            "source_path": self.source_path,
            "text": self.text,
            "character_count": self.character_count,
            "truncated": self.truncated,
            "artifact_status": self.artifact_status,
        }


@dataclass(frozen=True, slots=True)
class BookReaderAnchor:
    book_id: str
    selector: ScopeSelector
    node: Optional[TimelineNodeRef]
    branch_id: str
    chapter: int
    scene: Optional[int]
    kind: str
    reader_status: str
    artifact_status: str
    freshness_status: str
    source_path: Optional[str]
    execution_source_path: Optional[str]
    source_hash: Optional[str]
    span_start: int
    span_end: int
    selected_hash: Optional[str]
    text: str
    character_count: int
    selected_character_count: int
    truncated: bool
    valid_as_mutation_target: bool
    invalid_reason: Optional[str]
    allowed_mutation_scopes: List[str]
    recommended_action_keys: List[str]
    details: Dict[str, Any]
    source: str = "bookforge.query.reader.anchor.v1"
    schema_version: str = "book_reader_anchor_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "branch_id": self.branch_id,
            "chapter": self.chapter,
            "scene": self.scene,
            "kind": self.kind,
            "reader_status": self.reader_status,
            "artifact_status": self.artifact_status,
            "freshness_status": self.freshness_status,
            "source_path": self.source_path,
            "execution_source_path": self.execution_source_path,
            "source_hash": self.source_hash,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "selected_hash": self.selected_hash,
            "text": self.text,
            "character_count": self.character_count,
            "selected_character_count": self.selected_character_count,
            "truncated": self.truncated,
            "valid_as_mutation_target": self.valid_as_mutation_target,
            "invalid_reason": self.invalid_reason,
            "allowed_mutation_scopes": list(self.allowed_mutation_scopes),
            "recommended_action_keys": list(self.recommended_action_keys),
            "details": dict(self.details),
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class BookReaderView:
    book_id: str
    title: str
    selector: ScopeSelector
    chapters: List[BookReaderChapter]
    selected: Optional[BookReaderSelection]
    warnings: List[str]
    node: Optional[TimelineNodeRef] = None
    source: str = "bookforge.query.reader.v1"
    canonical_query_available: bool = True
    schema_version: str = "book_reader_view_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "title": self.title,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "source": self.source,
            "canonical_query_available": self.canonical_query_available,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "selected": self.selected.to_dict() if self.selected else None,
            "warnings": list(self.warnings),
        }


def get_book_reader_view(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    max_text_chars: int = DEFAULT_READER_TEXT_LIMIT,
    prefer_emitted: bool = True,
) -> BookReaderView:
    canonical_root = _common.book_root(Path(workspace), book_id)
    if not canonical_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_id}")
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    book_root = _common.execution_book_root(canonical_root, resolved_branch_id)
    if not book_root.exists():
        raise FileNotFoundError(f"Book execution root not found for branch {resolved_branch_id}: {book_id}")
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    book_meta = _common.read_json(canonical_root / "book.json") or {}
    title = _first_text(book_meta, ("title", "name")) or book_id
    chapters = _chapter_index(canonical_root, book_root)
    selected = _selected_payload(canonical_root, book_root, chapter_id, scene_id, max_text_chars)
    warnings = _reader_warnings(chapters, selected, branch_id=resolved_branch_id)
    return BookReaderView(
        book_id=book_id,
        title=title,
        selector=ScopeSelector(
            book_id=book_id,
            branch_id=resolved_branch_id,
            chapter=chapter_id,
            scene=scene_id,
        ),
        node=node,
        chapters=chapters,
        selected=selected,
        warnings=warnings,
    )


def get_book_reader_index(workspace, book_id: str, *, branch_id: str = MAIN_BRANCH_ID) -> BookReaderView:
    return get_book_reader_view(workspace, book_id, branch_id=branch_id)


def get_book_reader_chapter(
    workspace,
    book_id: str,
    chapter_id: int,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    include_text: bool = True,
    max_text_chars: int = DEFAULT_READER_TEXT_LIMIT,
) -> BookReaderView:
    return get_book_reader_view(
        workspace,
        book_id,
        branch_id=branch_id,
        chapter_id=int(chapter_id),
        max_text_chars=max_text_chars if include_text else 0,
    )


def get_book_reader_scene(
    workspace,
    book_id: str,
    chapter_id: int,
    scene_id: int,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    include_text: bool = True,
    max_text_chars: int = DEFAULT_READER_TEXT_LIMIT,
) -> BookReaderView:
    return get_book_reader_view(
        workspace,
        book_id,
        branch_id=branch_id,
        chapter_id=int(chapter_id),
        scene_id=int(scene_id),
        max_text_chars=max_text_chars if include_text else 0,
    )


def get_book_reader_anchor(
    workspace,
    book_id: str,
    chapter_id: int,
    *,
    scene_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
    start_offset: Optional[int] = None,
    end_offset: Optional[int] = None,
    max_text_chars: int = DEFAULT_READER_TEXT_LIMIT,
    prefer_emitted: bool = True,
) -> BookReaderAnchor:
    canonical_root = _common.book_root(Path(workspace), book_id)
    if not canonical_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_id}")
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    book_root = _common.execution_book_root(canonical_root, resolved_branch_id)
    if not book_root.exists():
        raise FileNotFoundError(f"Book execution root not found for branch {resolved_branch_id}: {book_id}")
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    path, kind = _reader_target_path(book_root, int(chapter_id), scene_id)
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        chapter=int(chapter_id),
        scene=int(scene_id) if scene_id is not None else None,
    )
    if not path.exists():
        return BookReaderAnchor(
            book_id=book_id,
            selector=selector,
            node=node,
            branch_id=resolved_branch_id,
            chapter=int(chapter_id),
            scene=int(scene_id) if scene_id is not None else None,
            kind=kind,
            reader_status="missing",
            artifact_status="diagnostic",
            freshness_status="missing",
            source_path=_rel(canonical_root, path),
            execution_source_path=_rel(book_root, path),
            source_hash=None,
            span_start=0,
            span_end=0,
            selected_hash=None,
            text="",
            character_count=0,
            selected_character_count=0,
            truncated=False,
            valid_as_mutation_target=False,
            invalid_reason="source_artifact_missing",
            allowed_mutation_scopes=[],
            recommended_action_keys=[],
            details={"branch_scoped": resolved_branch_id != MAIN_BRANCH_ID},
        )

    text = path.read_text(encoding="utf-8", errors="replace")
    source_hash = _sha256_text(text)
    span = _resolve_span(text, start_offset=start_offset, end_offset=end_offset)
    if span["invalid_reason"]:
        return BookReaderAnchor(
            book_id=book_id,
            selector=selector,
            node=node,
            branch_id=resolved_branch_id,
            chapter=int(chapter_id),
            scene=int(scene_id) if scene_id is not None else None,
            kind=kind,
            reader_status="invalid_span",
            artifact_status="authoritative",
            freshness_status="current",
            source_path=_rel(canonical_root, path),
            execution_source_path=_rel(book_root, path),
            source_hash=source_hash,
            span_start=span["start"],
            span_end=span["end"],
            selected_hash=None,
            text="",
            character_count=len(text),
            selected_character_count=0,
            truncated=False,
            valid_as_mutation_target=False,
            invalid_reason=span["invalid_reason"],
            allowed_mutation_scopes=[],
            recommended_action_keys=[],
            details={
                "branch_scoped": resolved_branch_id != MAIN_BRANCH_ID,
                "requested_start_offset": start_offset,
                "requested_end_offset": end_offset,
            },
        )

    selected_text = text[span["start"]:span["end"]]
    limit = max(0, min(int(max_text_chars or 0), MAX_READER_TEXT_LIMIT))
    truncated = len(selected_text) > limit
    valid_as_mutation_target = kind == "scene_prose"
    invalid_reason = None if valid_as_mutation_target else "chapter_level_anchor_requires_scene_scope"
    recommended_action_keys = ["create_branch"] if resolved_branch_id == MAIN_BRANCH_ID else ["continue_scene"]
    allowed_mutation_scopes = ["scene"] if resolved_branch_id == MAIN_BRANCH_ID else ["branch", "scene"]
    if not valid_as_mutation_target:
        recommended_action_keys = ["book_reader_scene"]
        allowed_mutation_scopes = []

    return BookReaderAnchor(
        book_id=book_id,
        selector=selector,
        node=node,
        branch_id=resolved_branch_id,
        chapter=int(chapter_id),
        scene=int(scene_id) if scene_id is not None else None,
        kind=kind,
        reader_status="canonical_current" if resolved_branch_id == MAIN_BRANCH_ID else "branch_current",
        artifact_status="authoritative",
        freshness_status="current",
        source_path=_rel(canonical_root, path),
        execution_source_path=_rel(book_root, path),
        source_hash=source_hash,
        span_start=span["start"],
        span_end=span["end"],
        selected_hash=_sha256_text(selected_text),
        text=selected_text[:limit],
        character_count=len(text),
        selected_character_count=len(selected_text),
        truncated=truncated,
        valid_as_mutation_target=valid_as_mutation_target,
        invalid_reason=invalid_reason,
        allowed_mutation_scopes=allowed_mutation_scopes,
        recommended_action_keys=recommended_action_keys,
        details={
            "branch_scoped": resolved_branch_id != MAIN_BRANCH_ID,
            "canonical_mutation_allowed": False,
            "branch_local_required_for_mutation": True,
            "span_specific_rewrite_available": False,
            "line_start": _line_for_offset(text, span["start"]),
            "line_end": _line_for_offset(text, max(span["end"] - 1, span["start"])),
        },
    )


def _chapter_index(canonical_root: Path, book_root: Path) -> List[BookReaderChapter]:
    chapter_dir = book_root / "draft" / "chapters"
    outline_dir = book_root / "outline" / "chapters"
    chapters: List[BookReaderChapter] = []
    for chapter_id in _chapter_ids(chapter_dir, outline_dir):
        chapter_path = chapter_dir / f"ch_{chapter_id:03d}.md"
        provisional_path = chapter_dir / f"ch_{chapter_id:03d}.provisional.md"
        scene_dir = chapter_dir / f"ch_{chapter_id:03d}"
        outline = (
            _common.read_json(outline_dir / f"ch_{chapter_id:03d}.json")
            or _common.read_json(outline_dir / f"chapter_{chapter_id:03d}.json")
            or _chapter_from_merged_outline(book_root, chapter_id)
            or {}
        )
        scenes = _scene_index(canonical_root, book_root, scene_dir, outline)
        chapters.append(
            BookReaderChapter(
                chapter=chapter_id,
                title=_first_text(outline, ("title", "chapter_title", "name")),
                summary=_first_text(outline, ("summary", "synopsis", "chapter_summary")),
                status="available" if chapter_path.exists() else "missing",
                source_path=_rel(canonical_root, chapter_path) if chapter_path.exists() else None,
                provisional_path=_rel(canonical_root, provisional_path) if provisional_path.exists() else None,
                character_count=_safe_size(chapter_path),
                scene_count=len(scenes),
                scenes=scenes,
            )
        )
    return chapters


def _chapter_from_merged_outline(book_root: Path, chapter_id: int) -> Dict[str, Any]:
    outline = _common.load_outline(book_root)
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        if _common.coerce_int(chapter.get("chapter_id") or chapter.get("chapter")) == int(chapter_id):
            return chapter
    return {}


def _selected_payload(
    canonical_root: Path,
    book_root: Path,
    chapter_id: Optional[int],
    scene_id: Optional[int],
    max_text_chars: int,
) -> Optional[BookReaderSelection]:
    if chapter_id is None:
        return None
    limit = max(0, min(int(max_text_chars or 0), MAX_READER_TEXT_LIMIT))
    path, kind = _reader_target_path(book_root, int(chapter_id), scene_id)
    if not path.exists():
        return BookReaderSelection(
            chapter=int(chapter_id),
            scene=int(scene_id) if scene_id is not None else None,
            kind=kind,
            status="missing",
            source_path=_rel(canonical_root, path),
            text="",
            character_count=0,
            truncated=False,
            artifact_status="diagnostic",
        )
    text = path.read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > limit
    return BookReaderSelection(
        chapter=int(chapter_id),
        scene=int(scene_id) if scene_id is not None else None,
        kind=kind,
        status="available",
        source_path=_rel(canonical_root, path),
        text=text[:limit],
        character_count=len(text),
        truncated=truncated,
    )


def _reader_target_path(book_root: Path, chapter_id: int, scene_id: Optional[int]) -> tuple[Path, str]:
    chapter_dir = book_root / "draft" / "chapters"
    if scene_id is not None:
        return chapter_dir / f"ch_{int(chapter_id):03d}" / f"scene_{int(scene_id):03d}.md", "scene_prose"
    return chapter_dir / f"ch_{int(chapter_id):03d}.md", "chapter_draft"


def _scene_index(canonical_root: Path, book_root: Path, scene_dir: Path, outline: Dict[str, Any]) -> List[BookReaderScene]:
    outline_scenes = _outline_scenes(outline)
    scene_ids = {item["scene"] for item in outline_scenes if isinstance(item.get("scene"), int)}
    if scene_dir.exists():
        for path in scene_dir.glob("scene_*.md"):
            parsed = _parse_number(path.stem, "scene_")
            if parsed:
                scene_ids.add(parsed)
    outline_by_scene = {item["scene"]: item for item in outline_scenes if isinstance(item.get("scene"), int)}
    scenes: List[BookReaderScene] = []
    for scene_id in sorted(scene_ids):
        prose_path = scene_dir / f"scene_{scene_id:03d}.md"
        meta_path = scene_dir / f"scene_{scene_id:03d}.meta.json"
        meta = _common.read_json(meta_path) or {}
        outline_item = outline_by_scene.get(scene_id, {})
        scenes.append(
            BookReaderScene(
                scene=scene_id,
                section=_common.coerce_int(outline_item.get("section")),
                title=outline_item.get("title"),
                summary=outline_item.get("summary"),
                status="available" if prose_path.exists() else "missing",
                source_path=_rel(canonical_root, prose_path) if prose_path.exists() else None,
                meta_path=_rel(canonical_root, meta_path) if meta_path.exists() else None,
                character_count=_safe_size(prose_path),
                meta_summary=_first_text(meta, ("summary", "scene_summary", "synopsis")),
                artifact_status="authoritative" if prose_path.exists() else "diagnostic",
            )
        )
    return scenes


def _outline_scenes(outline: Dict[str, Any]) -> List[Dict[str, Any]]:
    scenes: List[Dict[str, Any]] = []
    sections = outline.get("sections") if isinstance(outline.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = _common.coerce_int(section.get("section_id") or section.get("section"))
        raw_scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        for scene in raw_scenes:
            if not isinstance(scene, dict):
                continue
            scene_id = _common.coerce_int(scene.get("scene_id") or scene.get("scene"))
            if scene_id is None:
                continue
            scenes.append(
                {
                    "section": section_id,
                    "scene": scene_id,
                    "title": _first_text(scene, ("title", "scene_title", "label")),
                    "summary": _first_text(scene, ("summary", "synopsis", "purpose")),
                }
            )
    return scenes


def _chapter_ids(chapter_dir: Path, outline_dir: Path) -> List[int]:
    ids: set[int] = set()
    for root in (chapter_dir, outline_dir):
        if not root.exists():
            continue
        for path in root.glob("ch_*.md"):
            parsed = _parse_number(path.stem, "ch_")
            if parsed:
                ids.add(parsed)
        for path in root.glob("ch_*.json"):
            parsed = _parse_number(path.stem, "ch_")
            if parsed:
                ids.add(parsed)
        for path in root.glob("ch_*"):
            if path.is_dir():
                parsed = _parse_number(path.name, "ch_")
                if parsed:
                    ids.add(parsed)
    return sorted(ids)


def _reader_warnings(
    chapters: List[BookReaderChapter],
    selected: Optional[BookReaderSelection],
    *,
    branch_id: str,
) -> List[str]:
    warnings: List[str] = []
    if branch_id != MAIN_BRANCH_ID:
        warnings.append(f"Reader view is branch-scoped and not canonical main: {branch_id}.")
    if not chapters:
        warnings.append("No draft chapters or frozen chapter projections were found.")
    if selected and selected.status == "missing":
        warnings.append(f"Selected prose artifact is missing: {selected.source_path}.")
    return warnings


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def _first_text(payload: Dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_number(value: str, prefix: str) -> Optional[int]:
    if not value.startswith(prefix):
        return None
    try:
        parsed = int(value[len(prefix):])
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resolve_span(text: str, *, start_offset: Optional[int], end_offset: Optional[int]) -> Dict[str, Any]:
    try:
        start = 0 if start_offset is None else int(start_offset)
        end = len(text) if end_offset is None else int(end_offset)
    except (TypeError, ValueError):
        return {"start": 0, "end": 0, "invalid_reason": "span_offsets_must_be_integers"}
    bounded_start = max(0, min(start, len(text)))
    bounded_end = max(0, min(end, len(text)))
    if start < 0 or end < 0:
        return {"start": bounded_start, "end": bounded_end, "invalid_reason": "span_offsets_must_be_non_negative"}
    if start > len(text) or end > len(text):
        return {"start": bounded_start, "end": bounded_end, "invalid_reason": "span_offsets_out_of_range"}
    if start >= end:
        return {"start": bounded_start, "end": bounded_end, "invalid_reason": "span_start_must_be_before_end"}
    return {"start": start, "end": end, "invalid_reason": None}


def _line_for_offset(text: str, offset: int) -> int:
    bounded = max(0, min(int(offset), len(text)))
    return text.count("\n", 0, bounded) + 1


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
