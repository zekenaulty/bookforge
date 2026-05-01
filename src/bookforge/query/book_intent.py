from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from bookforge.contracts import BookIntent


BOOK_INTENT_ROOT_NAME = "book_intents"
BOOK_INTENT_FILENAME = "book_intent.json"


@dataclass(frozen=True, slots=True)
class BookIntentRecord:
    intent: BookIntent
    path: str
    artifact_status: str
    last_modified: Optional[str]
    schema_version: str = "book_intent_record_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "intent": self.intent.to_dict(),
            "path": self.path,
            "artifact_status": self.artifact_status,
            "last_modified": self.last_modified,
        }


def book_intents_root(workspace: Path | str) -> Path:
    return Path(workspace) / BOOK_INTENT_ROOT_NAME


def resolve_book_intent_path(workspace: Path | str, intent_ref: str | Path) -> Path:
    raw = str(intent_ref or "").strip()
    if not raw:
        raise ValueError("intent_ref is required.")

    candidate = Path(raw)
    if candidate.exists():
        if candidate.is_dir():
            return candidate / BOOK_INTENT_FILENAME
        return candidate

    root = book_intents_root(workspace)
    by_id = root / raw / BOOK_INTENT_FILENAME
    if by_id.exists():
        return by_id

    if raw.endswith(".json"):
        by_name = root / raw
        if by_name.exists():
            return by_name

    raise FileNotFoundError(f"Book intent not found: {raw}")


def get_book_intent(workspace: Path | str, intent_ref: str | Path) -> BookIntentRecord:
    path = resolve_book_intent_path(workspace, intent_ref)
    payload = json.loads(path.read_text(encoding="utf-8"))
    intent = BookIntent.from_dict(payload)
    return BookIntentRecord(
        intent=intent,
        path=path.as_posix(),
        artifact_status=_artifact_status_for_intent(intent),
        last_modified=_last_modified(path),
    )


def list_book_intents(workspace: Path | str, *, status: Optional[str] = None) -> List[BookIntentRecord]:
    root = book_intents_root(workspace)
    if not root.exists():
        return []
    normalized_status = str(status or "").strip().lower() or None
    records: List[BookIntentRecord] = []
    for path in sorted(root.glob(f"*/{BOOK_INTENT_FILENAME}"), key=lambda item: item.as_posix().lower()):
        try:
            record = get_book_intent(workspace, path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if normalized_status and record.intent.status != normalized_status:
            continue
        records.append(record)
    records.sort(key=lambda record: record.last_modified or "", reverse=True)
    return records


def _artifact_status_for_intent(intent: BookIntent) -> str:
    if intent.status in {"approved", "created"}:
        return "authoritative"
    if intent.status == "shelved":
        return "diagnostic"
    return "provisional"


def _last_modified(path: Path) -> Optional[str]:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return None
