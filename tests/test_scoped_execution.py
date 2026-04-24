from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.execution import build_resume_paused_section_request, resume_paused_section
from bookforge.llm.errors import LLMRequestError, QuotaViolation
from bookforge.pipeline.run_logging import _write_latest_run_pointer, _write_run_progress
from bookforge.runner import PAUSE_EXIT_CODE, _pause_on_quota
from bookforge.section_workflow import freeze_section_from_phase03_artifact, initialize_section_workflow
from bookforge.supervision import paths as supervision_paths
from bookforge.workspace import init_book_workspace
from bookforge.cli import build_parser


def _init_book(tmp_path: Path) -> Path:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")
    return init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 1},
        series_id=None,
    )


def _write_run_artifacts(book_root: Path, run_id: str = "run_001") -> None:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (outline_root / "pipeline_latest.json").write_text(
        json.dumps({"run_id": run_id}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "outline_spine_v1.json").write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "chapter_id": 1,
                        "title": "Opening",
                        "goal": "Start the story.",
                        "chapter_role": "hook",
                        "stakes_shift": "Pressure escalates.",
                        "bridge": {"from_prev": "", "to_next": "Move into danger."},
                        "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                    }
                ]
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "outline_sections_v1.json").write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "chapter_id": 1,
                        "sections": [
                            {
                                "section_id": 1,
                                "title": "Arrival",
                                "intent": "Get inside.",
                                "section_role": "setup",
                                "target_scene_count": 1,
                                "end_condition": "The door opens.",
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "outline_final_v1_1.json").write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "chapters": [
                    {
                        "chapter_id": 1,
                        "title": "Opening",
                        "sections": [
                            {
                                "section_id": 1,
                                "title": "Arrival",
                                "intent": "Get inside.",
                                "end_condition": "The door opens.",
                                "scenes": [{"scene_id": 1, "summary": "First scene."}],
                            }
                        ],
                    }
                ],
                "characters": [{"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"}],
                "threads": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_last_jsonl(path: Path) -> dict:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    return json.loads(lines[-1])


def _setup_paused_section(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    run_id = "writer_run_001"
    _write_latest_run_pointer(book_root, run_id)
    state_path = book_root / "state.json"
    state = _read_json(state_path)
    error = LLMRequestError(
        status_code=429,
        message="Quota exceeded.",
        retry_after_seconds=60.0,
        quota_violations=[
            QuotaViolation(
                quota_metric="tokens",
                quota_id="quota-1",
                quota_dimensions={"model": "gemini"},
                quota_value="1",
            )
        ],
        raw_response=None,
    )
    with pytest.raises(SystemExit) as exc:
        _pause_on_quota(
            book_root=book_root,
            state_path=state_path,
            state=state,
            run_id=run_id,
            phase="write_scene",
            error=error,
            scene_card={"chapter": 1, "scene": 1, "section_id": 1},
        )
    assert exc.value.code == PAUSE_EXIT_CODE
    return book_root


def test_resume_paused_section_succeeds_when_live_node_matches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = _setup_paused_section(tmp_path)
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / "scene_001.md").write_text("Scene prose.", encoding="utf-8")
    (chapter_dir / "scene_001.meta.json").write_text(json.dumps({"ok": True}, ensure_ascii=True, indent=2), encoding="utf-8")

    def _fake_run_section_range(*args, **kwargs):
        pause_path = book_root / "draft" / "context" / "run_paused.json"
        if pause_path.exists():
            pause_path.unlink()
        _write_run_progress(
            book_root,
            "writer_run_001",
            {
                "book_id": "my_book",
                "status": "complete",
                "phase": "run_complete",
                "chapter": 1,
                "scene": 1,
                "section": 1,
            },
        )

    monkeypatch.setattr("bookforge.execution.scoped.run_section_range", _fake_run_section_range)

    request = build_resume_paused_section_request(tmp_path, "my_book")
    result = resume_paused_section(tmp_path, request)

    current_node = _read_json(supervision_paths.current_node_path(book_root))
    assert result.status == "success"
    assert result.action == "resume_paused_section"
    assert result.request_id == request.request_id
    assert current_node["workflow_family"] == "section_local_outline"
    assert current_node["branch_id"] == "main"


def test_resume_paused_section_classifies_revision_only_target_drift_as_stale_write(tmp_path: Path) -> None:
    book_root = _setup_paused_section(tmp_path)
    request = build_resume_paused_section_request(tmp_path, "my_book")
    mismatched = request.expected_node.to_dict()
    mismatched["revision_id"] = "badrevision"
    request = request.__class__(
        request_id=request.request_id,
        action=request.action,
        selector=request.selector,
        expected_node=request.expected_node.from_dict(mismatched),
        branch_id=request.branch_id,
        requested_at=request.requested_at,
        details=request.details,
    )

    result = resume_paused_section(tmp_path, request)
    issues_payload = _read_json(supervision_paths.issues_latest_path(book_root))

    assert result.status == "hard_fail"
    assert any(ticket["code"] == "stale_write" for ticket in issues_payload["tickets"])
    assert any(ticket["category"] == "stale_write" for ticket in issues_payload["tickets"])


def test_resume_paused_section_returns_retryable_pause_when_writer_pauses_again(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_paused_section(tmp_path)

    def _pause_again(*args, **kwargs):
        raise SystemExit(PAUSE_EXIT_CODE)

    monkeypatch.setattr("bookforge.execution.scoped.run_section_range", _pause_again)

    request = build_resume_paused_section_request(tmp_path, "my_book")
    result = resume_paused_section(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "retryable_pause"
    assert execution_result["action"] == "resume_paused_section"
    assert execution_result["status"] == "retryable_pause"


def test_cli_parser_accepts_resume_paused_section_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "resume-paused-section",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--section",
            "2",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "resume-paused-section"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.section == 2
