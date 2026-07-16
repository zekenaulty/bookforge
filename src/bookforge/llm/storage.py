from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from typing import Any, Dict, Optional
from uuid import uuid4


_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def _safe_component(value: Any, *, fallback: str, max_length: int) -> str:
    raw = str(value or "")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-_.")
    if not cleaned:
        cleaned = fallback

    changed = cleaned != raw
    reserved = cleaned.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
    if len(cleaned) <= max_length and not changed and not reserved:
        return cleaned

    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    prefix_length = max(max_length - len(digest) - 1, 1)
    prefix = cleaned[:prefix_length].rstrip("-_.") or fallback[:prefix_length]
    return f"{prefix}-{digest}"


def _format_chapter_component(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "global"
    if number < 0:
        return "global"
    digits = str(number)
    if len(digits) > 9:
        digits = _safe_component(digits, fallback="000", max_length=12)
    return f"ch_{digits.zfill(3)}"


def _format_scene_prefix(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return ""
    if number < 0:
        return ""
    digits = str(number)
    if len(digits) > 9:
        digits = _safe_component(digits, fallback="000", max_length=12)
    return f"sc_{digits.zfill(3)}_"


def _normalize_action_descriptor(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(label or "event")).strip("-_.")
    cleaned = cleaned or "event"
    for pattern in (
        r"_json_retry\d+$",
        r"_schema_retry\d+$",
        r"_retry\d+$",
        r"_error$",
    ):
        cleaned = re.sub(pattern, "", cleaned)
    return cleaned.strip("-_.") or "event"


def _event_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return f"{stamp}_{uuid4().hex[:8]}"


def llm_transport_root(workspace: Path) -> Path:
    return workspace / "logs" / "llm"


def llm_log_dir(workspace: Path) -> Path:
    """Compatibility alias for callers that need the LLM transport root."""
    return llm_transport_root(workspace)


def llm_book_component(book_id: Any) -> str:
    return _safe_component(book_id or "global", fallback="global", max_length=32)


def llm_book_log_dir(workspace: Path, book_id: Any) -> Path:
    return llm_transport_root(workspace) / llm_book_component(book_id)


def legacy_book_log_prefix(book_id: Any) -> str:
    """Return the prefix produced by the pre-hierarchy flat log layout."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(book_id or ""))
    return cleaned.strip("-_")


def llm_log_path(
    workspace: Path,
    *,
    label: str,
    extra: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Path:
    scope = extra if isinstance(extra, dict) else {}
    book_component = llm_book_component(scope.get("book_id") or "global")
    run_component = _safe_component(
        scope.get("run_id") or "unscoped",
        fallback="unscoped",
        max_length=40,
    )
    chapter_component = _format_chapter_component(scope.get("chapter"))
    action_component = _safe_component(
        _normalize_action_descriptor(str(label or "event")),
        fallback="event",
        max_length=32,
    )
    label_component = _safe_component(label or "event", fallback="event", max_length=32)
    scene_prefix = _format_scene_prefix(scope.get("scene"))
    event_component = _safe_component(
        timestamp or _event_id(),
        fallback="event",
        max_length=40,
    )
    filename = f"{scene_prefix}{label_component}_{event_component}.json"
    return (
        llm_transport_root(workspace)
        / book_component
        / run_component
        / chapter_component
        / action_component
        / filename
    )
