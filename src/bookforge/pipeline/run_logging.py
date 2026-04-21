from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Dict, Optional


def _run_logs_dir(book_root: Path) -> Path:
    return book_root / "logs" / "runs"


def _run_log_path(book_root: Path, run_id: str) -> Path:
    return _run_logs_dir(book_root) / f"{run_id}.log"


def _run_progress_path(book_root: Path, run_id: str) -> Path:
    return _run_logs_dir(book_root) / f"{run_id}.progress.json"


def _current_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"run_{stamp}"


def _append_run_log(book_root: Path, run_id: str, message: str) -> None:
    log_dir = _run_logs_dir(book_root)
    log_dir.mkdir(parents=True, exist_ok=True)
    path = _run_log_path(book_root, run_id)
    line = message.rstrip()
    if not line:
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _write_latest_run_pointer(book_root: Path, run_id: str) -> Path:
    log_dir = _run_logs_dir(book_root)
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "latest_run.txt"
    path.write_text(run_id + "\n", encoding="utf-8")
    return path


def _write_run_progress(book_root: Path, run_id: str, payload: Dict[str, Any]) -> Path:
    log_dir = _run_logs_dir(book_root)
    log_dir.mkdir(parents=True, exist_ok=True)
    path = _run_progress_path(book_root, run_id)
    progress = dict(payload)
    progress["run_id"] = str(run_id).strip()
    progress["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps(progress, ensure_ascii=True, indent=2), encoding="utf-8")
    return path

