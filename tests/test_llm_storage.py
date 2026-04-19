from __future__ import annotations

from pathlib import Path

from bookforge.llm.storage import (
    current_thoughts_latest_path,
    current_thoughts_timestamped_path,
    llm_log_path,
    signature_active_path,
    signature_index_path,
    signature_ledger_path,
)


def test_llm_log_path_uses_book_chapter_action_layout(tmp_path: Path) -> None:
    path = llm_log_path(
        tmp_path,
        label="current_thoughts_error",
        extra={"book_id": "criticulous_the_rng_hellscape", "chapter": 1, "scene": 2},
        timestamp="20260418_120000",
    )

    assert path == (
        tmp_path
        / "logs"
        / "llm"
        / "criticulous_the_rng_hellscape"
        / "ch_001"
        / "current_thoughts"
        / "sc_002_current_thoughts_error_20260418_120000.json"
    )


def test_thought_artifacts_use_separate_root(tmp_path: Path) -> None:
    assert signature_ledger_path(tmp_path) == (
        tmp_path / "thoughts" / "signatures" / "thought_signature_ledger.jsonl"
    )
    assert signature_index_path(tmp_path) == (
        tmp_path / "thoughts" / "signatures" / "thought_signature_index.json"
    )
    assert signature_active_path(tmp_path) == (
        tmp_path / "thoughts" / "signatures" / "thought_signature_active.json"
    )
    assert current_thoughts_latest_path(tmp_path) == (
        tmp_path / "thoughts" / "current" / "current_thoughts_latest.json"
    )
    assert current_thoughts_timestamped_path(
        tmp_path,
        book_id="criticulous_the_rng_hellscape",
        chapter_id=1,
        timestamp="20260418_120000",
    ) == (
        tmp_path
        / "thoughts"
        / "current"
        / "criticulous_the_rng_hellscape"
        / "ch_001"
        / "current_thoughts_20260418_120000.json"
    )
