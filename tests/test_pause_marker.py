from pathlib import Path
import pytest

from bookforge.llm.errors import LLMRequestError
from bookforge.runner import PAUSE_EXIT_CODE, _pause_on_quota, _pause_on_reason


def test_pause_on_quota_writes_marker(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo"
    book_root.mkdir(parents=True)
    state_path = book_root / "state.json"

    error = LLMRequestError(
        status_code=429,
        message="quota",
        retry_after_seconds=5.0,
        quota_violations=[],
        raw_response=None,
    )

    with pytest.raises(SystemExit) as excinfo:
        _pause_on_quota(book_root, state_path, None, "write_scene", error, None)

    assert excinfo.value.code == PAUSE_EXIT_CODE
    pause_path = book_root / "draft" / "context" / "run_paused.json"
    assert pause_path.exists()


def test_pause_on_reason_writes_marker(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo"
    book_root.mkdir(parents=True)
    state_path = book_root / "state.json"

    with pytest.raises(SystemExit) as excinfo:
        _pause_on_reason(
            book_root,
            state_path,
            None,
            "lint_scene",
            "durable_slice_missing",
            "Missing durable ids",
            {"chapter": 1, "scene": 2},
            details={"issues": [{"code": "durable_slice_missing", "message": "missing ITEM_x"}]},
        )

    assert excinfo.value.code == PAUSE_EXIT_CODE
    pause_path = book_root / "draft" / "context" / "run_paused.json"
    assert pause_path.exists()
    data = pause_path.read_text(encoding="utf-8")
    assert "durable_slice_missing" in data
    assert "Missing durable ids" in data
