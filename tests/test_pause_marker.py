from pathlib import Path
import pytest

from bookforge.llm.errors import LLMRequestError
from bookforge.runner import PAUSE_EXIT_CODE, _pause_on_quota, _pause_on_reason, _apply_durable_updates_or_pause


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


def test_apply_durable_updates_or_pause_writes_chronology_pause_marker(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo"
    context_dir = book_root / "draft" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    state_path = book_root / "state.json"
    state_path.write_text(
        '{"schema_version":"1.0","status":"DRAFTING","cursor":{"chapter":1,"scene":1},"world":{},"summary":{"last_scene":[],"chapter_so_far":[],"story_so_far":[],"key_facts_ring":[],"must_stay_true":[],"pending_story_rollups":[]},"budgets":{},"duplication_warnings_in_row":0}',
        encoding="utf-8",
    )

    # Seed durable commits with a later committed scene so an older scene triggers conflict.
    (context_dir / "durable_commits.json").write_text(
        '{"schema_version":"1.0","applied_hashes":[],"latest_scene":{"chapter":2,"scene":3}}',
        encoding="utf-8",
    )
    (context_dir / "item_registry.json").write_text('{"schema_version":"1.0","items":[]}', encoding="utf-8")
    (context_dir / "plot_devices.json").write_text('{"schema_version":"1.0","devices":[]}', encoding="utf-8")
    (context_dir / "items").mkdir(parents=True, exist_ok=True)
    (context_dir / "plot_devices").mkdir(parents=True, exist_ok=True)
    (context_dir / "items" / "index.json").write_text('{"schema_version":"1.0","item_ids":[]}', encoding="utf-8")
    (context_dir / "plot_devices" / "index.json").write_text('{"schema_version":"1.0","device_ids":[]}', encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        _apply_durable_updates_or_pause(
            book_root=book_root,
            state_path=state_path,
            state=None,
            patch={
                "schema_version": "1.0",
                "item_registry_updates": [
                    {"item_id": "ITEM_x", "set": {"custodian": "CHAR_a"}, "reason": "x"}
                ],
            },
            chapter=1,
            scene=1,
            phase="scene",
            scene_card={"timeline_scope": "present", "ontological_scope": "real", "chapter": 1, "scene": 1},
        )

    assert excinfo.value.code == PAUSE_EXIT_CODE
    pause_path = context_dir / "run_paused.json"
    assert pause_path.exists()
    data = pause_path.read_text(encoding="utf-8")
    assert "durable_chronology_conflict" in data

