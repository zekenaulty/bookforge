from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from bookforge.pipeline.log import _status, use_run_log_path
from bookforge.pipeline.run_logging import _run_log_path, _write_latest_run_pointer


def test_run_log_context_keeps_concurrent_books_separate(tmp_path: Path) -> None:
    first = tmp_path / "first.log"
    second = tmp_path / "second.log"
    barrier = Barrier(2)

    def write_status(path: Path, message: str) -> None:
        with use_run_log_path(path):
            barrier.wait()
            _status(message)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(write_status, first, "first-book-only"),
            pool.submit(write_status, second, "second-book-only"),
        ]
        for future in futures:
            future.result()

    assert "first-book-only" in first.read_text(encoding="utf-8")
    assert "second-book-only" not in first.read_text(encoding="utf-8")
    assert "second-book-only" in second.read_text(encoding="utf-8")
    assert "first-book-only" not in second.read_text(encoding="utf-8")


def test_run_log_path_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid run_id"):
        _run_log_path(tmp_path, "run_../../escape")


def test_latest_run_pointer_is_replaced_without_temp_debris(tmp_path: Path) -> None:
    first = _write_latest_run_pointer(tmp_path, "run_first")
    second = _write_latest_run_pointer(tmp_path, "run_second")

    assert first == second
    assert second.read_text(encoding="utf-8") == "run_second\n"
    assert list(second.parent.glob(".latest_run_*.tmp")) == []
