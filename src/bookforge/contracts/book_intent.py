from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


BOOK_INTENT_STATUSES = {"draft", "approved", "created", "shelved"}


def _clean_required(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _clean_string_list(values: Any) -> List[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [item.strip() for item in values.split(",") if item.strip()]
    if not isinstance(values, list):
        raise ValueError("Expected list value.")
    return [str(item).strip() for item in values if str(item).strip()]


@dataclass(frozen=True, slots=True)
class BookIntent:
    intent_id: str
    status: str
    title: str
    author_ref: str
    genre: List[str]
    seed_text: str
    book_id: Optional[str] = None
    series_id: Optional[str] = None
    targets: Dict[str, Any] = field(default_factory=dict)
    short_synopsis: Optional[str] = None
    long_synopsis: Optional[str] = None
    reader_promise: Optional[str] = None
    central_conflict: Optional[str] = None
    tone: Optional[str] = None
    must_have: List[str] = field(default_factory=list)
    must_not: List[str] = field(default_factory=list)
    source_ref: Optional[str] = None
    created_at: Optional[str] = None
    approved_at: Optional[str] = None
    created_book_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "book_intent_v1"

    def __post_init__(self) -> None:
        status = _clean_required(self.status, "status")
        if status not in BOOK_INTENT_STATUSES:
            raise ValueError(f"Unknown book intent status: {status}")
        object.__setattr__(self, "intent_id", _clean_required(self.intent_id, "intent_id"))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "title", _clean_required(self.title, "title"))
        object.__setattr__(self, "author_ref", _clean_required(self.author_ref, "author_ref"))
        object.__setattr__(self, "genre", _clean_string_list(self.genre))
        if not self.genre:
            raise ValueError("genre must include at least one value.")
        object.__setattr__(self, "seed_text", _clean_required(self.seed_text, "seed_text"))
        object.__setattr__(self, "book_id", _clean_optional(self.book_id))
        object.__setattr__(self, "series_id", _clean_optional(self.series_id))
        object.__setattr__(self, "targets", dict(self.targets) if isinstance(self.targets, dict) else {})
        object.__setattr__(self, "short_synopsis", _clean_optional(self.short_synopsis))
        object.__setattr__(self, "long_synopsis", _clean_optional(self.long_synopsis))
        object.__setattr__(self, "reader_promise", _clean_optional(self.reader_promise))
        object.__setattr__(self, "central_conflict", _clean_optional(self.central_conflict))
        object.__setattr__(self, "tone", _clean_optional(self.tone))
        object.__setattr__(self, "must_have", _clean_string_list(self.must_have))
        object.__setattr__(self, "must_not", _clean_string_list(self.must_not))
        object.__setattr__(self, "source_ref", _clean_optional(self.source_ref))
        object.__setattr__(self, "created_at", _clean_optional(self.created_at))
        object.__setattr__(self, "approved_at", _clean_optional(self.approved_at))
        object.__setattr__(self, "created_book_id", _clean_optional(self.created_book_id))
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "intent_id": self.intent_id,
            "status": self.status,
            "book_id": self.book_id,
            "title": self.title,
            "author_ref": self.author_ref,
            "genre": list(self.genre),
            "targets": dict(self.targets),
            "series_id": self.series_id,
            "seed_text": self.seed_text,
            "short_synopsis": self.short_synopsis,
            "long_synopsis": self.long_synopsis,
            "reader_promise": self.reader_promise,
            "central_conflict": self.central_conflict,
            "tone": self.tone,
            "must_have": list(self.must_have),
            "must_not": list(self.must_not),
            "source_ref": self.source_ref,
            "created_at": self.created_at,
            "approved_at": self.approved_at,
            "created_book_id": self.created_book_id,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "BookIntent":
        if not isinstance(payload, dict):
            raise ValueError("BookIntent payload must be a dictionary.")
        return cls(
            intent_id=payload.get("intent_id"),
            status=payload.get("status") or "draft",
            book_id=payload.get("book_id"),
            title=payload.get("title"),
            author_ref=payload.get("author_ref"),
            genre=list(payload.get("genre") or []),
            targets=payload.get("targets") or {},
            series_id=payload.get("series_id"),
            seed_text=payload.get("seed_text"),
            short_synopsis=payload.get("short_synopsis"),
            long_synopsis=payload.get("long_synopsis"),
            reader_promise=payload.get("reader_promise"),
            central_conflict=payload.get("central_conflict"),
            tone=payload.get("tone"),
            must_have=list(payload.get("must_have") or []),
            must_not=list(payload.get("must_not") or []),
            source_ref=payload.get("source_ref"),
            created_at=payload.get("created_at"),
            approved_at=payload.get("approved_at"),
            created_book_id=payload.get("created_book_id"),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "book_intent_v1"),
        )
