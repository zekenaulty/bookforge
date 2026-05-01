from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import _common
from .integrity import get_integrity_verdict
from .workspace import get_workspace_status


@dataclass(frozen=True, slots=True)
class BookCard:
    book_id: str
    title: str
    author_ref: str
    state_status: Optional[str]
    cursor_chapter: int
    cursor_scene: int
    integrity_status: Optional[str]
    integrity_issue_codes: List[str]
    branch_count: int
    chapter_status_counts: Dict[str, int]
    current_node: Optional[Dict[str, Any]]
    current_node_source: Optional[str]
    observation_source: str
    warning_count: int
    warnings: List[str]
    last_modified: Optional[str]
    available: bool
    schema_version: str = "book_card_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "title": self.title,
            "author_ref": self.author_ref,
            "state_status": self.state_status,
            "cursor_chapter": self.cursor_chapter,
            "cursor_scene": self.cursor_scene,
            "integrity_status": self.integrity_status,
            "integrity_issue_codes": list(self.integrity_issue_codes),
            "branch_count": self.branch_count,
            "chapter_status_counts": dict(self.chapter_status_counts),
            "current_node": dict(self.current_node) if isinstance(self.current_node, dict) else None,
            "current_node_source": self.current_node_source,
            "observation_source": self.observation_source,
            "warning_count": self.warning_count,
            "warnings": list(self.warnings),
            "last_modified": self.last_modified,
            "available": self.available,
        }


def list_book_cards(workspace) -> List[BookCard]:
    books_root = Path(workspace) / "books"
    if not books_root.exists():
        return []
    cards: List[BookCard] = []
    for book_root in sorted((path for path in books_root.iterdir() if path.is_dir()), key=lambda p: p.name.lower()):
        if not (book_root / "book.json").exists():
            continue
        cards.append(get_book_card(workspace, book_root.name))
    return cards


def get_book_card(workspace, book_id: str) -> BookCard:
    book_root = _common.book_root(Path(workspace), book_id)
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_id}")
    book_meta = _common.read_json(book_root / "book.json") or {}
    title = _first_text(book_meta, ("title", "name")) or book_id
    author_ref = _first_text(book_meta, ("author_ref", "author")) or ""
    warnings: List[str] = []
    try:
        status = get_workspace_status(workspace, book_id, prefer_emitted=True)
        integrity = get_integrity_verdict(workspace, book_id)
        cursor = status.cursor if isinstance(status.cursor, dict) else {}
        current_node = status.current_node.to_dict() if status.current_node else None
        return BookCard(
            book_id=book_id,
            title=title,
            author_ref=author_ref,
            state_status=status.state_status,
            cursor_chapter=_coerce_int(cursor.get("chapter")) or 0,
            cursor_scene=_coerce_int(cursor.get("scene")) or 0,
            integrity_status=integrity.status,
            integrity_issue_codes=[issue.code for issue in integrity.issues],
            branch_count=len(status.branches),
            chapter_status_counts=dict(status.chapter_status_counts),
            current_node=current_node,
            current_node_source="bookforge-query",
            observation_source="bookforge-query",
            warning_count=0,
            warnings=[],
            last_modified=_last_modified(book_root),
            available=True,
        )
    except Exception as exc:
        state = _common.load_book_state(book_root)
        cursor = state.get("cursor") if isinstance(state.get("cursor"), dict) else {}
        warnings.append(f"Book card used fallback metadata: {exc}")
        return BookCard(
            book_id=book_id,
            title=title,
            author_ref=author_ref,
            state_status=_first_text(state, ("status",)),
            cursor_chapter=_coerce_int(cursor.get("chapter")) or 0,
            cursor_scene=_coerce_int(cursor.get("scene")) or 0,
            integrity_status=None,
            integrity_issue_codes=[],
            branch_count=0,
            chapter_status_counts={},
            current_node=None,
            current_node_source=None,
            observation_source="bookforge-query-fallback",
            warning_count=len(warnings),
            warnings=warnings,
            last_modified=_last_modified(book_root),
            available=False,
        )


def _last_modified(book_root: Path) -> Optional[str]:
    candidates = [
        book_root / "book.json",
        book_root / "state.json",
        book_root / "outline" / "snapshot_registry.json",
        book_root / "draft" / "chapters",
        book_root / "runtime" / "supervision",
    ]
    mtimes = []
    for path in candidates:
        try:
            if path.exists():
                mtimes.append(path.stat().st_mtime)
        except OSError:
            continue
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes), timezone.utc).isoformat()


def _first_text(payload: Dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _coerce_int(value: Any) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 1 else None
