from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import json
import re

from bookforge.contracts import CURRENT_NODE_FILENAME, MAIN_BRANCH_ID


def book_root(workspace: Path, book_id: str) -> Path:
    return workspace / "books" / book_id


def execution_book_root(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    resolved = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved == MAIN_BRANCH_ID:
        return book_root
    from bookforge.supervision import paths as supervision_paths

    return supervision_paths.branch_snapshot_root(book_root, resolved)


def outline_root(book_root: Path) -> Path:
    return book_root / "outline"


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def coerce_int(value: Any) -> Optional[int]:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return None
    return resolved if resolved >= 1 else None


def load_book_state(book_root: Path) -> Dict[str, Any]:
    return read_json(book_root / "state.json") or {}


def load_outline(book_root: Path) -> Dict[str, Any]:
    return read_json(outline_root(book_root) / "outline.json") or {}


def load_registry(book_root: Path) -> Dict[str, Any]:
    return read_json(outline_root(book_root) / "snapshot_registry.json") or {}


def latest_outline_run_id(book_root: Path) -> Optional[str]:
    latest = read_json(outline_root(book_root) / "pipeline_latest.json") or {}
    run_id = str(latest.get("run_id") or "").strip()
    return run_id or None


def latest_outline_pause_marker(book_root: Path) -> Optional[Dict[str, Any]]:
    run_id = latest_outline_run_id(book_root)
    if not run_id:
        return None
    return read_json(outline_root(book_root) / "pipeline_runs" / run_id / "pipeline_run_paused.json")


def latest_run_progress(book_root: Path) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    latest_path = book_root / "logs" / "runs" / "latest_run.txt"
    if not latest_path.exists():
        return None, None
    run_id = latest_path.read_text(encoding="utf-8").strip()
    if not run_id:
        return None, None
    progress = read_json(book_root / "logs" / "runs" / f"{run_id}.progress.json")
    return run_id, progress


def state_pause_marker(book_root: Path) -> Optional[Dict[str, Any]]:
    return read_json(book_root / "draft" / "context" / "run_paused.json")


def supervision_root(book_root: Path) -> Path:
    return book_root / "runtime" / "supervision"


def main_current_node_path(book_root: Path) -> Path:
    return supervision_root(book_root) / MAIN_BRANCH_ID / CURRENT_NODE_FILENAME


def branch_root(book_root: Path) -> Path:
    supervision_branches = supervision_root(book_root) / "branches"
    if supervision_branches.exists():
        return supervision_branches
    return book_root / "runtime" / "branches"


def branch_manifest_path(book_root: Path, branch_id: str) -> Path:
    supervision_path = supervision_root(book_root) / "branches" / branch_id / "branch_manifest.json"
    if supervision_path.exists():
        return supervision_path
    return branch_root(book_root) / branch_id / "branch_manifest.json"


def branch_current_node_path(book_root: Path, branch_id: str) -> Path:
    supervision_path = supervision_root(book_root) / "branches" / branch_id / CURRENT_NODE_FILENAME
    if supervision_path.exists():
        return supervision_path
    return branch_root(book_root) / branch_id / CURRENT_NODE_FILENAME


def list_branch_ids(book_root: Path) -> list[str]:
    roots = [supervision_root(book_root) / "branches", book_root / "runtime" / "branches"]
    ids: list[str] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name in seen:
                continue
            seen.add(child.name)
            ids.append(child.name)
    return ids


def compact_revision(*payloads: Optional[Dict[str, Any]]) -> str:
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        for key in ("updated_at", "created_at", "timestamp"):
            raw = str(payload.get(key) or "").strip()
            if raw:
                return re.sub(r"[^0-9a-zA-Z]+", "", raw.lower())[:32] or "observed"
    return "observed"


def first_non_empty(values: Iterable[Any]) -> Optional[str]:
    for value in values:
        cleaned = str(value or "").strip()
        if cleaned:
            return cleaned
    return None


def payload_timestamp(payload: Optional[Dict[str, Any]]) -> Optional[datetime]:
    if not isinstance(payload, dict):
        return None
    for key in ("updated_at", "created_at", "timestamp"):
        raw = str(payload.get(key) or "").strip()
        if not raw:
            continue
        normalized = raw.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            continue
    return None
