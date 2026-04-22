from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.branching import create_branch, discard_branch, load_branch_manifest, rerun_freeze_section_on_branch
from bookforge.contracts import ScopeSelector
from bookforge.query import get_workspace_status
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
    (outline_root / "pipeline_latest.json").write_text(json.dumps({"run_id": run_id}, ensure_ascii=True, indent=2), encoding="utf-8")
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
                        "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 2},
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
                                "scenes": [
                                    {
                                        "scene_id": 1,
                                        "summary": "First scene.",
                                        "handoff_mode": "terminal",
                                        "transition_out_anchors": ["door", "rain"],
                                        "threads": [],
                                    }
                                ],
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


def test_create_branch_emits_manifest_and_state_surface(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    manifest = create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )

    branch_manifest = load_branch_manifest(tmp_path, "my_book", "rerun-sec1")
    state_surface = _read_json(supervision_paths.state_surface_latest_path(book_root, "rerun-sec1"))
    status = get_workspace_status(tmp_path, "my_book")
    branch_state = next(branch for branch in status.branches if branch.branch_id == "rerun-sec1")

    assert manifest.branch_id == "rerun-sec1"
    assert branch_manifest.parent_node.branch_id == "main"
    assert state_surface["node"]["branch_id"] == "rerun-sec1"
    assert state_surface["workflow_run_mode"] == "active"
    assert branch_state.status == "active"


def test_create_branch_preserves_requested_scope_in_manifest_and_node(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    manifest = create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=2),
        branch_id="rerun-sec2",
    )

    state_surface = _read_json(supervision_paths.state_surface_latest_path(book_root, "rerun-sec2"))

    assert manifest.selector.chapter == 1
    assert manifest.selector.section == 2
    assert state_surface["node"]["chapter"] == 1
    assert state_surface["node"]["section"] == 2


def test_rerun_freeze_section_on_branch_keeps_main_untouched(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )

    result = rerun_freeze_section_on_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
    )

    main_outline = _read_json(book_root / "outline" / "outline.json")
    branch_outline = _read_json(supervision_paths.branch_snapshot_outline_root(book_root, "rerun-sec1") / "outline.json")
    branch_manifest = load_branch_manifest(tmp_path, "my_book", "rerun-sec1")

    assert result["status"] == "frozen"
    assert main_outline["chapters"][0]["sections"][0]["status"] == "stub"
    assert branch_outline["chapters"][0]["sections"][0]["status"] == "frozen"
    assert branch_manifest.lifecycle_state == "promote_ready"


def test_rerun_freeze_section_on_branch_emits_branch_local_reconciliation(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )

    rerun_freeze_section_on_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
    )

    branch_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, "rerun-sec1"))

    assert branch_execution_result["action"] == "rerun_freeze_section_on_branch"
    assert branch_execution_result["status"] == "promotion_required"
    assert branch_execution_result["details"]["pre_reconciliation_status"] == "promotion_required"
    assert branch_execution_result["details"]["branch_change_status"] == "changed"
    assert branch_execution_result["details"]["pre_revision_id"] != branch_execution_result["details"]["post_revision_id"]
    assert "canonical_change_status" not in branch_execution_result["details"]


def test_rerun_freeze_already_materialized_reports_unchanged_branch_state(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )
    rerun_freeze_section_on_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
    )

    rerun_freeze_section_on_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
    )

    branch_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, "rerun-sec1"))

    assert branch_execution_result["status"] == "promotion_required"
    assert branch_execution_result["details"]["branch_change_status"] == "unchanged"
    assert branch_execution_result["details"]["pre_revision_id"] == branch_execution_result["details"]["post_revision_id"]


def test_branch_refuses_silent_source_switch(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, "run_001")
    _write_run_artifacts(book_root, "run_002")
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", run_id="run_001", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )

    with pytest.raises(ValueError, match="refusing silent source switch"):
        rerun_freeze_section_on_branch(
            workspace=tmp_path,
            book_id="my_book",
            branch_id="rerun-sec1",
            chapter_id=1,
            section_id=1,
            run_id="run_002",
        )


def test_discard_branch_leaves_main_untouched(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )
    main_before = _read_json(book_root / "outline" / "outline.json")

    manifest = discard_branch(tmp_path, "my_book", "rerun-sec1", reason="test discard")

    main_after = _read_json(book_root / "outline" / "outline.json")
    assert manifest.lifecycle_state == "discard"
    assert main_before == main_after
