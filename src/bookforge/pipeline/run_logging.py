from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Optional
from uuid import uuid4


_RUN_ID_PATTERN = re.compile(r"run_[A-Za-z0-9._-]+\Z")


def _validated_run_id(run_id: str) -> str:
    value = str(run_id)
    if not _RUN_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid run_id: {run_id!r}")
    return value


def _run_logs_dir(book_root: Path) -> Path:
    return book_root / "logs" / "runs"


def _run_log_path(book_root: Path, run_id: str) -> Path:
    return _run_logs_dir(book_root) / f"{_validated_run_id(run_id)}.log"


def _current_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return f"run_{stamp}_{uuid4().hex[:8]}"


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
    value = _validated_run_id(run_id)
    temporary = log_dir / f".latest_run_{uuid4().hex}.tmp"
    temporary.write_text(value + "\n", encoding="utf-8")
    temporary.replace(path)
    return path
