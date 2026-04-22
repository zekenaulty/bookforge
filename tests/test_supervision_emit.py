from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.llm.errors import LLMRequestError, QuotaViolation
from bookforge.pipeline.run_logging import _write_latest_run_pointer
from bookforge.runner import PAUSE_EXIT_CODE, _pause_on_quota
from bookforge.section_workflow import initialize_section_workflow
from bookforge.supervision import paths as supervision_paths
from bookforge.workspace import init_book_workspace


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


def test_initialize_section_workflow_emits_main_branch_state_surface(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    current_node = _read_json(supervision_paths.current_node_path(book_root))
    state_surface = _read_json(supervision_paths.state_surface_latest_path(book_root))
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert current_node["workflow_family"] == "section_local_outline"
    assert current_node["source_run_id"] == "run_001"
    assert state_surface["selector"]["branch_id"] == "main"
    assert state_surface["selector"]["chapter"] is None
    assert state_surface["workflow_source_run_id"] == "run_001"
    assert state_surface["chapter_status_counts"] == {"in_progress": 1}
    assert execution_result["action"] == "initialize_section_workflow"
    assert execution_result["status"] == "success"
    assert execution_result["details"]["pre_reconciliation_status"] == "success"
    assert execution_result["details"]["canonical_change_status"] == "canonical"
    assert execution_result["details"]["state_change_status"] == "changed"


def test_initialize_section_workflow_no_op_emits_integrity_ticket(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    stale_draft = book_root / "outline" / "section_drafts" / "ch_001_sec_001_phase03.json"
    stale_draft.parent.mkdir(parents=True, exist_ok=True)
    stale_draft.write_text("{}", encoding="utf-8")

    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=False)

    issues_payload = _read_json(supervision_paths.issues_latest_path(book_root))
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    tickets = issues_payload["tickets"]
    assert any(ticket["code"] == "stale_section_drafts_present" for ticket in tickets)
    assert any(ticket["category"] == "chimera_risk" for ticket in tickets)
    assert execution_result["action"] == "initialize_section_workflow"
    assert execution_result["status"] == "no_op"


def test_pause_on_quota_emits_retryable_pause_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

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

    current_node = _read_json(supervision_paths.current_node_path(book_root))
    issues_payload = _read_json(supervision_paths.issues_latest_path(book_root))
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert current_node["workflow_family"] == "section_write"
    assert current_node["phase_id"] == "write_scene"
    assert any(ticket["category"] == "provider_retry_exhausted" for ticket in issues_payload["tickets"])
    assert execution_result["status"] == "retryable_pause"
    assert execution_result["action"] == "run_loop"
    assert execution_result["details"]["pre_reconciliation_status"] == "retryable_pause"
    assert execution_result["details"]["canonical_change_status"] == "none"
