from pathlib import Path
import pytest

from bookforge.llm.errors import LLMRequestError
from bookforge.runner import PAUSE_EXIT_CODE, _pause_on_quota


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
