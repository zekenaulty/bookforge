from __future__ import annotations

import json
from pathlib import Path

from bookforge.branching import create_branch
from bookforge.cli import build_parser
from bookforge.contracts import ScopeSelector
from bookforge.query import (
    get_book_reader_anchor,
    get_book_reader_scene,
    get_branch_artifact_index,
    get_branch_detail,
    get_branch_diff_summary,
    get_branch_inventory,
    get_recovery_anchor_candidates,
    get_recovery_plan_preview,
    list_book_cards,
)
from bookforge.supervision import paths as supervision_paths
from bookforge.section_workflow import freeze_section_from_phase03_artifact, initialize_section_workflow
from bookforge.workspace import init_book_workspace


def _init_book(tmp_path: Path) -> Path:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")
    return init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="The Test Book",
        genre=["fantasy"],
        targets={"chapters": 1},
        series_id=None,
    )


def _write_run_artifacts(book_root: Path, run_id: str = "run_001") -> None:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (outline_root / "pipeline_latest.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    (run_dir / "outline_spine_v1.json").write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "chapter_id": 1,
                        "title": "Opening",
                        "goal": "Start.",
                        "chapter_role": "hook",
                        "stakes_shift": "Pressure rises.",
                        "bridge": {"from_prev": "", "to_next": "Next."},
                        "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                    }
                ]
            }
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
                                "intent": "Arrive.",
                                "section_role": "setup",
                                "target_scene_count": 1,
                                "end_condition": "Door opens.",
                            }
                        ],
                    }
                ]
            }
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
                                "intent": "Arrive.",
                                "end_condition": "Door opens.",
                                "scenes": [{"scene_id": 1, "title": "Scene One", "summary": "First scene."}],
                            }
                        ],
                    }
                ],
                "characters": [{"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"}],
                "threads": [],
            }
        ),
        encoding="utf-8",
    )


def _materialize_written_scene(book_root: Path) -> None:
    scene_dir = book_root / "draft" / "chapters" / "ch_001"
    scene_dir.mkdir(parents=True, exist_ok=True)
    (scene_dir / "scene_001.md").write_text("Rhea opened the door.", encoding="utf-8")
    (scene_dir / "scene_001.meta.json").write_text(
        json.dumps({"summary": "Rhea opens the door."}),
        encoding="utf-8",
    )
    (book_root / "draft" / "chapters" / "ch_001.md").write_text(
        "# Chapter 1: Opening\n\nRhea opened the door.",
        encoding="utf-8",
    )


def test_bookforge_reader_query_returns_canonical_scene_text(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _materialize_written_scene(book_root)

    view = get_book_reader_scene(tmp_path, "my_book", 1, 1)
    payload = view.to_dict()

    assert payload["canonical_query_available"] is True
    assert payload["selected"]["text"] == "Rhea opened the door."
    assert payload["selected"]["artifact_status"] == "authoritative"
    assert payload["chapters"][0]["scenes"][0]["title"] == "Scene One"


def test_bookforge_reader_anchor_returns_scene_span_with_hashes(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _materialize_written_scene(book_root)

    anchor = get_book_reader_anchor(
        tmp_path,
        "my_book",
        1,
        scene_id=1,
        start_offset=5,
        end_offset=15,
    )
    payload = anchor.to_dict()

    assert payload["schema_version"] == "book_reader_anchor_v1"
    assert payload["reader_status"] == "canonical_current"
    assert payload["artifact_status"] == "authoritative"
    assert payload["text"] == "opened the"
    assert payload["span_start"] == 5
    assert payload["span_end"] == 15
    assert len(payload["source_hash"]) == 64
    assert len(payload["selected_hash"]) == 64
    assert payload["valid_as_mutation_target"] is True
    assert payload["invalid_reason"] is None
    assert payload["details"]["branch_local_required_for_mutation"] is True


def test_bookforge_reader_anchor_is_branch_scoped_and_not_main_text(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _materialize_written_scene(book_root)
    create_branch(
        tmp_path,
        "my_book",
        ScopeSelector(book_id="my_book", chapter=1, scene=1),
        branch_id="reader-branch",
        merge_operation="promotion",
        branch_role="rerun",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "reader-branch")
    branch_scene = branch_root / "draft" / "chapters" / "ch_001" / "scene_001.md"
    branch_scene.write_text("Branch Rhea opened a different door.", encoding="utf-8")

    anchor = get_book_reader_anchor(tmp_path, "my_book", 1, scene_id=1, branch_id="reader-branch", start_offset=0, end_offset=11)
    main_anchor = get_book_reader_anchor(tmp_path, "my_book", 1, scene_id=1, start_offset=0, end_offset=11)

    assert anchor.reader_status == "branch_current"
    assert anchor.text == "Branch Rhea"
    assert anchor.execution_source_path == "draft/chapters/ch_001/scene_001.md"
    assert anchor.details["branch_scoped"] is True
    assert anchor.valid_as_mutation_target is True
    assert main_anchor.reader_status == "canonical_current"
    assert main_anchor.text == "Rhea opened"


def test_bookforge_reader_anchor_marks_chapter_anchor_inspect_only(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _materialize_written_scene(book_root)

    anchor = get_book_reader_anchor(tmp_path, "my_book", 1)

    assert anchor.kind == "chapter_draft"
    assert anchor.reader_status == "canonical_current"
    assert anchor.valid_as_mutation_target is False
    assert anchor.invalid_reason == "chapter_level_anchor_requires_scene_scope"
    assert anchor.allowed_mutation_scopes == []


def test_bookforge_reader_anchor_reports_invalid_spans_without_throwing(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _materialize_written_scene(book_root)

    anchor = get_book_reader_anchor(tmp_path, "my_book", 1, scene_id=1, start_offset=500, end_offset=501)

    assert anchor.reader_status == "invalid_span"
    assert anchor.valid_as_mutation_target is False
    assert anchor.invalid_reason == "span_offsets_out_of_range"
    assert anchor.text == ""


def test_book_cards_and_branch_inventory_are_queryable(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        tmp_path,
        "my_book",
        ScopeSelector(book_id="my_book", chapter=1, section=1),
        branch_id="test-branch",
        merge_operation="promotion",
        branch_role="rerun",
    )

    cards = list_book_cards(tmp_path)
    inventory = get_branch_inventory(tmp_path, "my_book")
    detail = get_branch_detail(tmp_path, "my_book", "test-branch", chapter_id=1, section_id=1)
    artifact_index = get_branch_artifact_index(tmp_path, "my_book", "test-branch")
    diff_summary = get_branch_diff_summary(tmp_path, "my_book", "test-branch")

    assert cards[0].book_id == "my_book"
    assert cards[0].title == "The Test Book"
    assert cards[0].branch_count == 1
    assert inventory.branches[0].branch_id == "test-branch"
    assert inventory.branches[0].stale_parent is False
    assert detail.branch_id == "test-branch"
    assert detail.branch_record is not None
    assert detail.branch_record.branch_id == "test-branch"
    assert detail.workspace_status["book_id"] == "my_book"
    assert any(action["action"] == "discard_branch" for action in detail.legal_actions)
    assert artifact_index.branch_id == "test-branch"
    assert artifact_index.records
    assert artifact_index.relationship_counts
    assert diff_summary.status == "no_changes"


def test_reader_book_and_branch_cli_commands_parse() -> None:
    parser = build_parser()

    book_list = parser.parse_args(["book", "list", "--json"])
    reader = parser.parse_args(["book", "reader", "--book", "my_book", "--chapter", "1", "--scene", "1", "--json"])
    reader_anchor = parser.parse_args(["book", "reader-anchor", "--book", "my_book", "--chapter", "1", "--scene", "1", "--start-offset", "0", "--end-offset", "10", "--json"])
    inventory = parser.parse_args(["workflow", "branch-inventory", "--book", "my_book", "--json"])
    branch_detail = parser.parse_args(["workflow", "branch-detail", "--book", "my_book", "--branch-id", "test-branch", "--chapter", "1", "--section", "1", "--json"])
    artifact_index = parser.parse_args(["workflow", "branch-artifact-index", "--book", "my_book", "--branch-id", "test-branch", "--json"])
    branch_diff = parser.parse_args(["workflow", "branch-diff-summary", "--book", "my_book", "--branch-id", "test-branch", "--json"])
    anchors = parser.parse_args(["workflow", "recovery-anchor-candidates", "--book", "my_book", "--json"])
    plan = parser.parse_args(["workflow", "recovery-plan-preview", "--book", "my_book", "--anchor-type", "declared_source_run", "--json"])

    assert book_list.book_command == "list"
    assert reader.book_command == "reader"
    assert reader.chapter == 1
    assert reader.scene == 1
    assert reader_anchor.book_command == "reader-anchor"
    assert reader_anchor.start_offset == 0
    assert reader_anchor.end_offset == 10
    assert inventory.workflow_command == "branch-inventory"
    assert branch_detail.workflow_command == "branch-detail"
    assert branch_detail.branch_id == "test-branch"
    assert artifact_index.workflow_command == "branch-artifact-index"
    assert artifact_index.branch_id == "test-branch"
    assert branch_diff.workflow_command == "branch-diff-summary"
    assert anchors.workflow_command == "recovery-anchor-candidates"
    assert plan.workflow_command == "recovery-plan-preview"


def test_recovery_anchor_candidates_auto_select_single_valid_timeline(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    outline_path = book_root / "outline" / "outline.json"
    payload = json.loads(outline_path.read_text(encoding="utf-8"))
    payload["chapters"][0]["sections"][0]["title"] = "Polluted Section"
    outline_path.write_text(json.dumps(payload), encoding="utf-8")

    report = get_recovery_anchor_candidates(tmp_path, "my_book")
    preview = get_recovery_plan_preview(tmp_path, "my_book")

    assert report.status == "auto_selected"
    assert report.auto_selected_candidate_id == "declared_source_run"
    assert report.human_decision_required is False
    assert report.affected_scopes == [{"chapter_id": 1, "section_id": 1}]
    assert preview.status == "ready"
    assert preview.selected_anchor is not None
    assert preview.selected_anchor.anchor_type == "declared_source_run"
    assert preview.steps[0].details["branch_initial_state"]["cleanliness_status"] == "isolated_not_clean"
    assert "not applied by branch creation" in preview.steps[0].details["branch_initial_state"]["note"]
    assert [step.action for step in preview.steps][:4] == [
        "create_recovery_branch",
        "quarantine_artifacts",
        "normalize_outline_scope",
        "invalidate_scope_outputs",
    ]
