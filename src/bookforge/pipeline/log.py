from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

_RUN_LOG_PATH: ContextVar[Optional[Path]] = ContextVar("bookforge_run_log_path", default=None)

def set_run_log_path(path: Optional[Path]) -> None:
    """Set the run log for the current context (legacy compatibility helper)."""
    _RUN_LOG_PATH.set(path)


@contextmanager
def use_run_log_path(path: Optional[Path]) -> Iterator[None]:
    token = _RUN_LOG_PATH.set(path)
    try:
        yield
    finally:
        _RUN_LOG_PATH.reset(token)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _status(message: str) -> None:
    line = f"[bookforge] {message}"
    print(line, flush=True)
    run_log_path = _RUN_LOG_PATH.get()
    if run_log_path:
        with run_log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
