from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_RUN_LOG_PATH: Optional[Path] = None

def set_run_log_path(path: Optional[Path]) -> None:
    global _RUN_LOG_PATH
    _RUN_LOG_PATH = path


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _status(message: str) -> None:
    line = f"[bookforge] {message}"
    print(line, flush=True)
    if _RUN_LOG_PATH:
        with _RUN_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
