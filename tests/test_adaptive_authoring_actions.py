from __future__ import annotations

import json
from pathlib import Path

from bookforge.branching import create_branch
from bookforge.contracts import ScopeSelector
from bookforge.execution import (
    align_scene_pair_seam_action,
    apply_bridge_scene_insertion_action,
    build_align_scene_pair_seam_request,
    build_apply_bridge_scene_insertion_request,
    build_plan_bridge_scene_insertion_request,
    plan_bridge_scene_insertion_action,
)
from bookforge.query import (
    get_author_loop_envelopes,
    get_book_reader_scene,
    get_branch_artifact_index,
    get_branch_detail,
    get_branch_diff_summary,
    list_execution_options,
)
from bookforge.query.seams import get_chapter_seam_queue, get_scene_pair_seam_detail
from bookforge.section_workflow import freeze_section_from_phase03_artifact, initialize_section_workflow
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
                                "target_scene_count": 2,
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
                                    {"scene_id": 1, "summary": "First scene.", "handoff_mode": "handoff", "threads": []},
                                    {"scene_id": 2, "summary": "Second scene.", "handoff_mode": "terminal", "threads": []},
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


def _write_scene(book_root: Path, scene_id: int, text: str) -> None:
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / f"scene_{scene_id:03d}.md").write_text(text, encoding="utf-8")
    (chapter_dir / f"scene_{scene_id:03d}.meta.json").write_text(
        json.dumps({"scene_id": scene_id}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _branch_with_two_scenes(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="author-branch",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "author-branch")
    _write_scene(branch_root, 1, "Rhea reached the door.\n\nThe lock clicked.")
    _write_scene(branch_root, 2, "The lock clicked.\n\nRhea stepped inside.")
    return branch_root


def _read_last_jsonl(path: Path) -> dict:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    return json.loads(lines[-1])


def test_branch_scene_options_include_pair_alignment_and_bridge_plan(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    options = list_execution_options(
        tmp_path,
        ScopeSelector(book_id="my_book", branch_id="author-branch", workflow_family="section_write", chapter=1, section=1, scene=1),
        prefer_emitted=False,
    )
    by_action = {option.action: option for option in options}

    assert by_action["align_scene_pair_seam"].allowed is True
    assert by_action["align_scene_pair_seam"].details["scene_b_id"] == 2
    assert by_action["align_scene_pair_seam"].mutates_canonical_state is False
    assert by_action["plan_bridge_scene_insertion"].allowed is True
    assert by_action["plan_bridge_scene_insertion"].details["proposal_only"] is True
    assert by_action["apply_bridge_scene_insertion"].allowed is False
    assert by_action["apply_bridge_scene_insertion"].details["refusal_code"] == "missing_bridge_scene_insertion_plan"
    assert "requires an existing bridge scene insertion plan" in by_action["apply_bridge_scene_insertion"].refusal_reason


def test_plan_bridge_scene_insertion_writes_branch_proposal(tmp_path: Path) -> None:
    branch_root = _branch_with_two_scenes(tmp_path)

    request = build_plan_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
        objective="Add a breath before Rhea crosses the threshold.",
    )
    result = plan_bridge_scene_insertion_action(tmp_path, request)

    plan_path = branch_root / result.artifact_paths["bridge_scene_insertion_plan"]
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(tmp_path / "books" / "my_book", "author-branch"))

    assert result.status == "success"
    assert result.details["canonical_changed"] is False
    assert payload["status"] == "proposal"
    assert payload["mutation_policy"] == "does_not_modify_outline_or_prose"
    assert execution_result["action"] == "plan_bridge_scene_insertion"


def test_apply_bridge_scene_insertion_updates_branch_outline_and_shifts_artifacts(tmp_path: Path) -> None:
    branch_root = _branch_with_two_scenes(tmp_path)

    plan_request = build_plan_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
        objective="Add a breath before Rhea crosses the threshold.",
    )
    plan_bridge_scene_insertion_action(tmp_path, plan_request)

    options = list_execution_options(
        tmp_path,
        ScopeSelector(book_id="my_book", branch_id="author-branch", workflow_family="section_write", chapter=1, section=1, scene=1),
        prefer_emitted=False,
    )
    by_action = {option.action: option for option in options}
    assert by_action["apply_bridge_scene_insertion"].allowed is True

    apply_request = build_apply_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
    )
    result = apply_bridge_scene_insertion_action(tmp_path, apply_request)

    outline = json.loads((branch_root / "outline" / "outline.json").read_text(encoding="utf-8"))
    registry = json.loads((branch_root / "outline" / "snapshot_registry.json").read_text(encoding="utf-8"))
    scenes = outline["chapters"][0]["sections"][0]["scenes"]
    scene_ids = [scene["scene_id"] for scene in scenes]
    shifted_scene = branch_root / "draft" / "chapters" / "ch_001" / "scene_003.md"
    bridge_scene = scenes[1]
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(tmp_path / "books" / "my_book", "author-branch"))

    assert result.status == "success"
    assert result.details["canonical_changed"] is False
    assert result.details["inserted_scene_id"] == 2
    assert scene_ids == [1, 2, 3]
    assert bridge_scene["introduced_by"] == "apply_bridge_scene_insertion"
    assert bridge_scene["insertion_status"] == "provisional"
    assert scenes[0]["hands_off_to"] == "1:2"
    assert scenes[2]["consumes_outcome_from"] == "1:2"
    assert shifted_scene.read_text(encoding="utf-8") == "The lock clicked.\n\nRhea stepped inside."
    assert not (branch_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()
    assert registry["chapters"][0]["sections"][0]["scene_ref_end"] == "1:3"
    assert (branch_root / result.artifact_paths["bridge_scene_insertion_apply_report"]).exists()
    assert execution_result["action"] == "apply_bridge_scene_insertion"


def test_apply_bridge_scene_insertion_refresh_surfaces_include_inserted_scene_and_report(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)
    plan_request = build_plan_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
        objective="Add a breath before Rhea crosses the threshold.",
    )
    plan_bridge_scene_insertion_action(tmp_path, plan_request)
    apply_request = build_apply_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
    )
    result = apply_bridge_scene_insertion_action(tmp_path, apply_request)

    artifact_index = get_branch_artifact_index(tmp_path, "my_book", "author-branch")
    diff = get_branch_diff_summary(tmp_path, "my_book", "author-branch")
    reader = get_book_reader_scene(tmp_path, "my_book", 1, 2, branch_id="author-branch")
    detail = get_branch_detail(tmp_path, "my_book", "author-branch", chapter_id=1, section_id=1, scene_id=2)
    records = {record.path: record for record in artifact_index.records}
    changed_paths = {record.path for record in diff.changed_records}
    apply_report = records[result.artifact_paths["bridge_scene_insertion_apply_report"]]
    outline = records[result.artifact_paths["outline"]]
    inserted_scene = next(scene for scene in reader.chapters[0].scenes if scene.scene == 2)
    legal = {action["action"]: action for action in detail.legal_actions}

    assert apply_report.artifact_class == "adaptive_authoring_report"
    assert apply_report.artifact_status == "diagnostic"
    assert outline.artifact_class == "outline"
    assert result.artifact_paths["bridge_scene_insertion_apply_report"] in changed_paths
    assert result.artifact_paths["outline"] in changed_paths
    assert "draft/chapters/ch_001/scene_003.md" in changed_paths
    assert inserted_scene.status == "missing"
    assert inserted_scene.artifact_status == "diagnostic"
    assert inserted_scene.summary == "Add a breath before Rhea crosses the threshold."
    assert reader.selected is not None
    assert reader.selected.status == "missing"
    assert detail.scene_readiness is not None
    assert detail.scene_readiness["recommended_next_action"] == "plan_scene"
    assert legal["plan_scene"]["allowed"] is True


def test_apply_bridge_scene_insertion_refuses_main_branch(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    request = build_apply_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="main",
    )
    result = apply_bridge_scene_insertion_action(tmp_path, request)

    assert result.status == "hard_fail"
    assert result.details["failure_code"] == "branch_required"
    assert result.details["canonical_changed"] is False


def test_apply_bridge_scene_insertion_legal_action_blocks_without_adjacent_pair(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    options = list_execution_options(
        tmp_path,
        ScopeSelector(book_id="my_book", branch_id="author-branch", workflow_family="section_write", chapter=1, section=1, scene=2),
        prefer_emitted=False,
    )
    by_action = {option.action: option for option in options}

    assert by_action["apply_bridge_scene_insertion"].allowed is False
    assert by_action["apply_bridge_scene_insertion"].details["scene_b_id"] is None
    assert by_action["apply_bridge_scene_insertion"].details["refusal_code"] == "no_adjacent_scene"
    assert "No adjacent next scene exists" in by_action["apply_bridge_scene_insertion"].refusal_reason


def test_apply_bridge_scene_insertion_rejects_stale_expected_node(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    first_plan_request = build_plan_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
        objective="Add a breath before Rhea crosses the threshold.",
    )
    plan_bridge_scene_insertion_action(tmp_path, first_plan_request)
    apply_request = build_apply_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
    )
    second_plan_request = build_plan_bridge_scene_insertion_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
        objective="Refresh the bridge proposal before applying.",
    )
    plan_bridge_scene_insertion_action(tmp_path, second_plan_request)

    result = apply_bridge_scene_insertion_action(tmp_path, apply_request)

    assert result.status == "hard_fail"
    assert result.details["failure_code"] == "stale_write"
    assert result.details["canonical_changed"] is False


def test_align_scene_pair_seam_action_uses_branch_snapshot_only(tmp_path: Path, monkeypatch) -> None:
    branch_root = _branch_with_two_scenes(tmp_path)

    def _stub_align(book_root: Path, outline: dict, chapter_num: int, scene_a_id: int, scene_b_id: int) -> dict:
        assert book_root == branch_root
        assert chapter_num == 1
        assert scene_a_id == 1
        assert scene_b_id == 2
        report_path = book_root / "draft" / "context" / "chapter_seams" / "ch_001" / "pair_001_002_seam_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"status": "aligned"}, ensure_ascii=True, indent=2), encoding="utf-8")
        _write_scene(book_root, 1, "Rhea reached the door, and the lock clicked once.")
        _write_scene(book_root, 2, "Rhea stepped inside without replaying the lock.")
        return {
            "status": "aligned",
            "report_path": report_path.relative_to(book_root).as_posix(),
            "repair_action_count": 1,
            "issue_counts_before": {"error": 1, "warning": 0, "total": 1},
            "issue_counts_after": {"error": 0, "warning": 0, "total": 0},
            "scene_artifacts": [
                {
                    "scene_ref": "1:1",
                    "current_path": "draft/chapters/ch_001/scene_001.md",
                    "original_path": "draft/chapters/ch_001/scene_001.original.md",
                    "fixed_path": "draft/chapters/ch_001/scene_001.fixed.md",
                },
                {
                    "scene_ref": "1:2",
                    "current_path": "draft/chapters/ch_001/scene_002.md",
                    "original_path": "draft/chapters/ch_001/scene_002.original.md",
                    "fixed_path": "draft/chapters/ch_001/scene_002.fixed.md",
                },
            ],
        }

    monkeypatch.setattr("bookforge.execution.adaptive_authoring.align_scene_pair_seam", _stub_align)
    request = build_align_scene_pair_seam_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        branch_id="author-branch",
    )
    result = align_scene_pair_seam_action(tmp_path, request)

    main_scene = tmp_path / "books" / "my_book" / "draft" / "chapters" / "ch_001" / "scene_001.md"
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(tmp_path / "books" / "my_book", "author-branch"))

    assert result.status == "success"
    assert result.details["canonical_changed"] is False
    assert "replaying the lock" in (branch_root / "draft" / "chapters" / "ch_001" / "scene_002.md").read_text(encoding="utf-8")
    assert not main_scene.exists()
    assert execution_result["action"] == "align_scene_pair_seam"


def test_author_loop_envelopes_expose_section_and_chapter_shapes(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    envelopes = get_author_loop_envelopes(
        tmp_path,
        "my_book",
        branch_id="author-branch",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        prefer_emitted=False,
    )
    by_key = {item.envelope_key: item for item in envelopes.envelopes}

    assert "continue_one_step" in by_key
    assert "continue_section" in by_key
    assert "continue_chapter" in by_key
    assert "align_scene_pair_seam" in by_key["continue_chapter"].allowed_actions
    assert "user_cancel_requested" in by_key["continue_section"].stop_conditions
    assert envelopes.details["refresh_required_between_steps"] is True
    assert envelopes.details["refresh_query_order"][0] == "branch_detail"
    assert "provider_failed" in envelopes.details["stop_reason_ownership"]["bookforge_child_step"]
    assert "budget_exhausted" in envelopes.details["stop_reason_ownership"]["nanda_parent_loop"]
    assert by_key["continue_one_step"].details["child_action_count_per_step"] == 1
    assert by_key["continue_section"].details["refresh_required_between_steps"] is True


def test_chapter_seam_queue_lists_ready_branch_pairs_and_blocks_main(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    branch_queue = get_chapter_seam_queue(tmp_path, "my_book", branch_id="author-branch", chapter_id=1, prefer_emitted=False)
    main_queue = get_chapter_seam_queue(tmp_path, "my_book", branch_id="main", chapter_id=1, prefer_emitted=False)

    assert branch_queue.status == "ready"
    assert branch_queue.ready_count == 1
    assert branch_queue.recommended_pair["scene_a_id"] == 1
    assert branch_queue.recommended_pair["scene_b_id"] == 2
    assert branch_queue.items[0].action == "align_scene_pair_seam"
    assert branch_queue.items[0].scene_a_exists is True
    assert branch_queue.items[0].scene_b_exists is True
    assert main_queue.status == "blocked"
    assert main_queue.items[0].action is None
    assert "branch-only" in main_queue.items[0].blocked_reason


def test_chapter_seam_queue_marks_existing_aligned_report(tmp_path: Path) -> None:
    branch_root = _branch_with_two_scenes(tmp_path)
    report_path = branch_root / "draft" / "context" / "chapter_seams" / "ch_001" / "pair_001_002_seam_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "scene_pair_seam_report_v1",
                "chapter_id": 1,
                "scene_a_id": 1,
                "scene_b_id": 2,
                "status": "aligned",
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    queue = get_chapter_seam_queue(tmp_path, "my_book", branch_id="author-branch", chapter_id=1, prefer_emitted=False)

    assert queue.status == "aligned"
    assert queue.ready_count == 0
    assert queue.aligned_count == 1
    assert queue.items[0].status == "aligned"
    assert queue.items[0].report_status == "aligned"
    assert queue.items[0].action is None


def test_scene_pair_seam_detail_reports_ready_pair_without_report(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    detail = get_scene_pair_seam_detail(
        tmp_path,
        "my_book",
        branch_id="author-branch",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        prefer_emitted=False,
    )

    assert detail.status == "ready"
    assert detail.report_found is False
    assert detail.action == "align_scene_pair_seam"
    assert detail.pair is not None
    assert detail.pair.scene_a_exists is True
    assert detail.pair.scene_b_exists is True


def test_scene_pair_seam_detail_surfaces_existing_report_payload(tmp_path: Path) -> None:
    branch_root = _branch_with_two_scenes(tmp_path)
    report_path = branch_root / "draft" / "context" / "chapter_seams" / "ch_001" / "pair_001_002_seam_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "schema_version": "scene_pair_seam_report_v1",
        "chapter_id": 1,
        "scene_a_id": 1,
        "scene_b_id": 2,
        "status": "attention_required",
        "repair_action_count": 2,
        "before": {"issue_counts": {"error": 2, "warning": 1, "total": 3}},
        "after": {"issue_counts": {"error": 1, "warning": 0, "total": 1}},
        "scene_artifacts": [{"scene_ref": "1:1", "current_path": "draft/chapters/ch_001/scene_001.md"}],
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=True, indent=2), encoding="utf-8")

    detail = get_scene_pair_seam_detail(
        tmp_path,
        "my_book",
        branch_id="author-branch",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        prefer_emitted=False,
    )
    summary = get_scene_pair_seam_detail(
        tmp_path,
        "my_book",
        branch_id="author-branch",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=2,
        include_report=False,
        prefer_emitted=False,
    )

    assert detail.status == "attention_required"
    assert detail.report_found is True
    assert detail.report_status == "attention_required"
    assert detail.issue_counts_before["error"] == 2
    assert detail.issue_counts_after["error"] == 1
    assert detail.repair_action_count == 2
    assert detail.scene_artifacts[0]["scene_ref"] == "1:1"
    assert detail.report["schema_version"] == "scene_pair_seam_report_v1"
    assert summary.report is None


def test_scene_pair_seam_detail_blocks_non_adjacent_pair(tmp_path: Path) -> None:
    _branch_with_two_scenes(tmp_path)

    detail = get_scene_pair_seam_detail(
        tmp_path,
        "my_book",
        branch_id="author-branch",
        chapter_id=1,
        scene_a_id=1,
        scene_b_id=3,
        prefer_emitted=False,
    )

    assert detail.status == "blocked"
    assert detail.pair is None
    assert "not adjacent" in detail.blocked_reason
