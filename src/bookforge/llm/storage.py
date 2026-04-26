from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
import re


def _sanitize_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or ""))
    cleaned = cleaned.strip("-_.")
    return cleaned or "unknown"


def _compact_component(value: str, *, max_length: int = 48) -> str:
    if len(value) <= max_length:
        return value
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    prefix_length = max(max_length - len(digest) - 1, 1)
    return f"{value[:prefix_length].rstrip('-_.')}-{digest}"


def _format_chapter_component(value: Any) -> str:
    try:
        return f"ch_{int(value):03d}"
    except (TypeError, ValueError):
        return "global"


def _format_scene_prefix(value: Any) -> str:
    try:
        return f"sc_{int(value):03d}_"
    except (TypeError, ValueError):
        return ""


def _normalize_action_descriptor(label: str) -> str:
    raw = _sanitize_component(str(label or "event"))
    if not raw:
        return "event"
    patterns = (
        r"_json_retry\d+$",
        r"_schema_retry\d+$",
        r"_retry\d+$",
        r"_error$",
    )
    normalized = raw
    for pattern in patterns:
        normalized = re.sub(pattern, "", normalized)
    normalized = normalized.strip("-_.")
    return normalized or raw


def llm_transport_root(workspace: Path) -> Path:
    return workspace / "logs" / "llm"


def llm_log_dir(workspace: Path) -> Path:
    return llm_transport_root(workspace)


def llm_log_path(
    workspace: Path,
    *,
    label: str,
    extra: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Path:
    extra = extra if isinstance(extra, dict) else {}
    book_component = _sanitize_component(str(extra.get("book_id") or "global"))
    chapter_component = _format_chapter_component(extra.get("chapter"))
    raw_label_component = _compact_component(_sanitize_component(str(label or "event")))
    action_component = _compact_component(_normalize_action_descriptor(str(label or "event")))
    scene_prefix = _format_scene_prefix(extra.get("scene"))
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{scene_prefix}{raw_label_component}_{timestamp}.json"
    return llm_transport_root(workspace) / book_component / chapter_component / action_component / filename


def thoughts_root(workspace: Path) -> Path:
    return workspace / "thoughts"


def signatures_dir(workspace: Path) -> Path:
    return thoughts_root(workspace) / "signatures"


def current_thoughts_dir(workspace: Path) -> Path:
    return thoughts_root(workspace) / "current"


def current_thoughts_history_dir(
    workspace: Path,
    *,
    book_id: Optional[str] = None,
    chapter_id: Any = None,
) -> Path:
    book_component = _sanitize_component(str(book_id or "global"))
    chapter_component = _format_chapter_component(chapter_id)
    return current_thoughts_dir(workspace) / book_component / chapter_component


def signature_ledger_path(workspace: Path) -> Path:
    return signatures_dir(workspace) / "thought_signature_ledger.jsonl"


def signature_index_path(workspace: Path) -> Path:
    return signatures_dir(workspace) / "thought_signature_index.json"


def signature_active_path(workspace: Path) -> Path:
    return signatures_dir(workspace) / "thought_signature_active.json"


def signature_active_lock_path(workspace: Path) -> Path:
    return signatures_dir(workspace) / ".thought_signature_active.lock"


def current_thoughts_latest_path(workspace: Path) -> Path:
    return current_thoughts_dir(workspace) / "current_thoughts_latest.json"


def current_thoughts_timestamped_path(
    workspace: Path,
    *,
    book_id: Optional[str] = None,
    chapter_id: Any = None,
    timestamp: Optional[str] = None,
) -> Path:
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return current_thoughts_history_dir(
        workspace,
        book_id=book_id,
        chapter_id=chapter_id,
    ) / f"current_thoughts_{timestamp}.json"


def legacy_signature_ledger_path(workspace: Path) -> Path:
    return llm_transport_root(workspace) / "thought_signature_ledger.jsonl"


def legacy_signature_index_path(workspace: Path) -> Path:
    return llm_transport_root(workspace) / "thought_signature_index.json"


def legacy_signature_active_path(workspace: Path) -> Path:
    return llm_transport_root(workspace) / "thought_signature_active.json"


def legacy_signature_active_lock_path(workspace: Path) -> Path:
    return llm_transport_root(workspace) / ".thought_signature_active.lock"


def legacy_current_thoughts_latest_path(workspace: Path) -> Path:
    return llm_transport_root(workspace) / "current_thoughts_latest.json"
