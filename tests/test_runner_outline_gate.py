from pathlib import Path
import json

import pytest

from bookforge.runner import run_loop
from bookforge.workspace import init_book_workspace


def _outline_payload() -> dict:
    return {
        "schema_version": "1.1",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Start the story.",
                "chapter_role": "hook",
                "stakes_shift": "Risk appears.",
                "bridge": {"from_prev": "", "to_next": "Complication escalates."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Intro",
                        "intent": "Introduce pressure.",
                        "end_condition": "Pressure is visible.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "The protagonist enters the city gate.",
                                "type": "setup",
                                "outcome": "The protagonist is now inside city jurisdiction.",
                                "characters": ["CHAR_protagonist"],
                                "threads": ["THREAD_pressure"],
                                "location_start_id": "LOC_CITY_GATE",
                                "location_end_id": "LOC_CITY_GATE",
                                "location_start_label": "City Gate",
                                "location_end_label": "City Gate",
                                "location_start": "City Gate",
                                "location_end": "City Gate",
                                "handoff_mode": "direct_continuation",
                                "constraint_state": "free",
                                "transition_in_text": "At the city gate, the action begins immediately.",
                                "transition_in_anchors": ["city", "gate", "begins"],
                                "seam_score": 10,
                                "seam_resolution": "inline_bridge",
                                "end_condition_echo": "Pressure is visible.",
                            }
                        ],
                    }
                ],
            }
        ],
        "characters": [
            {
                "character_id": "CHAR_protagonist",
                "name": "Protagonist",
                "pronouns": "they/them",
                "role": "lead",
                "intro": {"chapter": 1, "scene": 1},
            }
        ],
        "threads": [{"thread_id": "THREAD_pressure", "label": "Pressure", "status": "open"}],
    }


def _init_book(tmp_path: Path) -> Path:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    book_root = init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 1},
        series_id=None,
    )
    outline_root = book_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)
    (outline_root / "outline.json").write_text(json.dumps(_outline_payload(), ensure_ascii=True, indent=2), encoding="utf-8")
    return book_root


def _write_outline_report(book_root: Path, overall_status: str) -> None:
    outline_root = book_root / "outline"
    run_id = "test_run"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "book_id": "my_book",
        "run_id": run_id,
        "overall_status": overall_status,
        "requires_user_attention": True,
        "strict_blocking": True,
        "mode_values": {},
        "seam_outcomes": {},
        "attention_items": [{"code": "test_issue", "severity": "error", "message": "test"}],
    }
    (run_dir / "outline_pipeline_report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    latest_pointer = {
        "run_id": run_id,
        "updated_at": "2026-02-15T00:00:00Z",
        "path": f"pipeline_runs/{run_id}/outline_pipeline_report.json",
    }
    (outline_root / "outline_pipeline_report_latest.json").write_text(
        json.dumps(latest_pointer, ensure_ascii=True, indent=2), encoding="utf-8"
    )


def test_run_blocks_when_outline_report_missing(tmp_path: Path) -> None:
    _init_book(tmp_path)
    with pytest.raises(ValueError, match="WRITE GATED: outline pipeline report is missing or unreadable"):
        run_loop(workspace=tmp_path, book_id="my_book", steps=1)


def test_run_bypass_allows_continuation_when_outline_report_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init_book(tmp_path)

    def _boom(*args, **kwargs):
        raise RuntimeError("client_init")

    monkeypatch.setattr("bookforge.runner.get_llm_client", _boom)
    with pytest.raises(RuntimeError, match="client_init"):
        run_loop(workspace=tmp_path, book_id="my_book", steps=1, force_outline_gate_bypass=True)


def test_run_blocks_on_error_status_without_bypass(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_outline_report(book_root, "ERROR")
    with pytest.raises(ValueError, match="WRITE GATED: latest outline pipeline status is ERROR"):
        run_loop(workspace=tmp_path, book_id="my_book", steps=1)


def test_run_bypass_allows_continuation_on_error_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = _init_book(tmp_path)
    _write_outline_report(book_root, "ERROR")

    def _boom(*args, **kwargs):
        raise RuntimeError("client_init")

    monkeypatch.setattr("bookforge.runner.get_llm_client", _boom)
    with pytest.raises(RuntimeError, match="client_init"):
        run_loop(workspace=tmp_path, book_id="my_book", steps=1, force_outline_gate_bypass=True)
