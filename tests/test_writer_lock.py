from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import bookforge.runner as runner
from bookforge.pipeline.run_logging import _current_run_id
from bookforge.writer_lock import BookWriterLockError, book_writer_lock, writer_lock_path


def test_run_loop_holds_book_lock_before_delegating(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = tmp_path / "books" / "demo"
    book_root.mkdir(parents=True)
    observed = {"locked": False}

    def fake_run_loop_unlocked(**_: object) -> None:
        with pytest.raises(BookWriterLockError, match="already held"):
            with book_writer_lock(book_root, operation="competing_run"):
                pass
        observed["locked"] = True

    monkeypatch.setattr(runner, "_run_loop_unlocked", fake_run_loop_unlocked)

    runner.run_loop(tmp_path, "demo")

    assert observed["locked"] is True
    owner = json.loads(writer_lock_path(book_root).read_bytes()[1:].decode("utf-8"))
    assert owner["operation"] == "run_loop"
    assert owner["pid"] == os.getpid()


def test_book_writer_lock_rejects_another_process(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo"
    book_root.mkdir(parents=True)
    source_root = Path(__file__).resolve().parents[1] / "src"
    environment = os.environ.copy()
    prior_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(source_root)
        if not prior_pythonpath
        else str(source_root) + os.pathsep + prior_pythonpath
    )
    child_code = "\n".join(
        [
            "from pathlib import Path",
            "import sys",
            "from bookforge.writer_lock import book_writer_lock",
            "with book_writer_lock(Path(sys.argv[1]), operation='child_run'):",
            "    print('locked', flush=True)",
            "    sys.stdin.readline()",
        ]
    )
    process = subprocess.Popen(
        [sys.executable, "-c", child_code, str(book_root)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        assert process.stdout is not None
        ready = process.stdout.readline().strip()
        if ready != "locked":
            assert process.stderr is not None
            pytest.fail(f"Lock-holder process failed: {process.stderr.read()}")

        with pytest.raises(BookWriterLockError, match="child_run"):
            with book_writer_lock(book_root, operation="parent_run"):
                pass
    finally:
        if process.poll() is None and process.stdin is not None:
            try:
                process.stdin.write("\n")
                process.stdin.flush()
            except BrokenPipeError:
                pass
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise

    with book_writer_lock(book_root, operation="next_run"):
        pass


def test_run_ids_are_unique_even_within_one_second() -> None:
    first = _current_run_id()
    second = _current_run_id()

    assert first != second
    assert first.startswith("run_")
    assert second.startswith("run_")
