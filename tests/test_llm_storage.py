from __future__ import annotations

from pathlib import Path

from bookforge.llm.storage import llm_book_log_dir, llm_log_path, llm_transport_root


def test_llm_log_path_groups_book_run_chapter_and_action(tmp_path: Path) -> None:
    path = llm_log_path(
        tmp_path,
        label="write_scene_retry1",
        extra={"book_id": "my_book", "run_id": "run_demo", "chapter": 2, "scene": 3},
        timestamp="20260715_120000_123456_deadbeef",
    )

    assert path == (
        tmp_path
        / "logs"
        / "llm"
        / "my_book"
        / "run_demo"
        / "ch_002"
        / "write_scene"
        / "sc_003_write_scene_retry1_20260715_120000_123456_deadbeef.json"
    )


def test_llm_log_path_groups_error_and_json_retry_with_base_action(tmp_path: Path) -> None:
    error_path = llm_log_path(
        tmp_path,
        label="plan_scene_error",
        extra={"book_id": "my_book"},
        timestamp="event_a",
    )
    retry_path = llm_log_path(
        tmp_path,
        label="plan_scene_json_retry2",
        extra={"book_id": "my_book"},
        timestamp="event_b",
    )

    assert error_path.parent.name == "plan_scene"
    assert retry_path.parent.name == "plan_scene"
    assert error_path.parts[-4:-1] == ("unscoped", "global", "plan_scene")


def test_llm_log_paths_are_unique_without_an_explicit_timestamp(tmp_path: Path) -> None:
    first = llm_log_path(tmp_path, label="write_scene", extra={"book_id": "my_book"})
    second = llm_log_path(tmp_path, label="write_scene", extra={"book_id": "my_book"})

    assert first != second


def test_llm_log_components_cannot_escape_root_or_alias_unsafe_book_ids(tmp_path: Path) -> None:
    first = llm_log_path(
        tmp_path,
        label="../write/scene",
        extra={"book_id": "../same", "run_id": "../../run", "chapter": "odd"},
        timestamp="../../event",
    )
    second_book_dir = llm_book_log_dir(tmp_path, "..\\same")
    root = llm_transport_root(tmp_path)

    first.relative_to(root)
    second_book_dir.relative_to(root)
    assert ".." not in first.relative_to(root).parts
    assert first.parts[len(root.parts)] != second_book_dir.name
    assert all(len(component) <= 100 for component in first.relative_to(root).parts)

    huge_scope = llm_log_path(
        tmp_path,
        label="write_scene",
        extra={"book_id": "book", "chapter": 10**100, "scene": 10**100},
        timestamp="event",
    )
    assert all(len(component) <= 100 for component in huge_scope.relative_to(root).parts)
