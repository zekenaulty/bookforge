from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.branching import create_branch
from bookforge.contracts import ExecutionRequest, ExecutionResult, ScenePhaseActionReadiness, ScenePhaseReadiness, ScopeSelector, TimelineNodeRef
from bookforge.execution import (
    apply_scene_commit,
    build_apply_scene_commit_request,
    build_continue_scene_request,
    build_generate_continuity_pack_request,
    build_lint_scene_prose_request,
    build_plan_scene_request,
    build_preflight_scene_state_request,
    build_repair_scene_prose_request,
    build_state_repair_scene_patch_request,
    build_write_scene_prose_request,
    continue_scene,
    generate_continuity_pack,
    lint_scene_prose,
    plan_scene_action,
    preflight_scene_state,
    repair_scene_prose,
    state_repair_scene_patch,
    write_scene_prose,
)
from bookforge.llm.signatures import append_signature_records
from bookforge.memory.continuity import save_style_anchor, style_anchor_path
from bookforge.pipeline.phase_history import _record_phase_success, _write_phase_artifact
from bookforge.query import get_branch_artifact_index, get_branch_diff_summary, get_next_writing_target
from bookforge.section_workflow import freeze_section_from_phase03_artifact, initialize_section_workflow
from bookforge.supervision import paths as supervision_paths
from bookforge.workspace import init_book_workspace


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
    system_path = book_root / "prompts" / "system_v1.md"
    if not system_path.exists():
        system_path.write_text("System prompt.", encoding="utf-8")
    return book_root


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
                                "scenes": [
                                    {
                                        "scene_id": 1,
                                        "summary": "Rhea reaches the door.",
                                        "type": "setup",
                                        "outcome": "She is ready to enter.",
                                        "characters": ["CHAR_protagonist"],
                                        "threads": [],
                                        "handoff_mode": "terminal",
                                        "transition_out_anchors": ["door"],
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "characters": [
                    {
                        "character_id": "CHAR_protagonist",
                        "name": "Rhea",
                        "role": "protagonist",
                    }
                ],
                "threads": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def _scene_card() -> dict:
    return {
        "schema_version": "1.1",
        "scene_id": "SC_001_001",
        "chapter": 1,
        "scene": 1,
        "section_id": 1,
        "scene_target": "Rhea reaches the door.",
        "goal": "Get inside.",
        "conflict": "The lock resists.",
        "required_callbacks": [],
        "constraints": [],
        "end_condition": "The door opens.",
        "location_start": "Front Gate",
        "location_end": "Front Gate",
        "handoff_mode": "terminal",
        "constraint_state": "free",
        "transition_in_text": "Rhea reaches the front gate in the rain.",
        "transition_in_anchors": ["front gate", "rain", "lock"],
        "ui_allowed": False,
        "ui_mechanics_expected": [],
        "cast_present_ids": ["CHAR_protagonist"],
        "cast_present": ["Rhea"],
    }


def _read_last_jsonl(path: Path) -> dict:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    return json.loads(lines[-1])


def _read_jsonl(path: Path) -> list[dict]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


def _record_artifact(book_root: Path, chapter: int, scene: int, phase: str, name: str, payload, *, as_json: bool = True, artifact_key: str) -> None:
    path = _write_phase_artifact(book_root, chapter, scene, name, payload, as_json=as_json)
    _record_phase_success(
        book_root,
        chapter,
        scene,
        phase,
        {artifact_key: path.relative_to(book_root).as_posix()},
    )


def _record_write_pair(book_root: Path, prose: str = "Rhea forced the lock open.", patch: dict | None = None) -> None:
    write_patch = patch or {
        "summary_update": {"last_scene": ["Rhea forced the lock open."]},
        "character_updates": [],
        "character_continuity_system_updates": [],
    }
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", prose, as_json=False)
    patch_path = _write_phase_artifact(book_root, 1, 1, "write_patch", write_patch, as_json=True)
    _record_phase_success(
        book_root,
        1,
        1,
        "write",
        {
            "prose": prose_path.relative_to(book_root).as_posix(),
            "patch": patch_path.relative_to(book_root).as_posix(),
        },
    )


def _record_repair_pair(book_root: Path, prose: str = "Rhea forced the lock open cleanly.", patch: dict | None = None) -> None:
    repair_patch = patch or {
        "summary_update": {"last_scene": ["Rhea forced the lock open cleanly."]},
        "character_updates": [],
        "character_continuity_system_updates": [],
    }
    prose_path = _write_phase_artifact(book_root, 1, 1, "repair_prose", prose, as_json=False)
    patch_path = _write_phase_artifact(book_root, 1, 1, "repair_patch", repair_patch, as_json=True)
    _record_phase_success(
        book_root,
        1,
        1,
        "repair",
        {
            "prose": prose_path.relative_to(book_root).as_posix(),
            "patch": patch_path.relative_to(book_root).as_posix(),
        },
    )


def _setup_scene_with_prereqs(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _record_artifact(book_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    _record_artifact(
        book_root,
        1,
        1,
        "preflight",
        "preflight_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "continuity_pack",
        "continuity_pack",
        {
            "scene_end_anchor": "The lock clicks.",
            "constraints": [],
            "open_threads": [],
            "cast_present": ["Rhea"],
            "location": "Front Gate",
            "next_action": "Open the door.",
            "summary": {},
        },
        artifact_key="pack",
    )
    save_style_anchor(style_anchor_path(book_root), "Tight close third-person.")
    return book_root


def _write_projection_context_artifacts(tmp_path: Path, book_root: Path) -> None:
    character_state_rel = "draft/context/characters/protagonist.state.json"
    character_dir = book_root / "draft" / "context" / "characters"
    character_dir.mkdir(parents=True, exist_ok=True)
    (character_dir / "index.json").write_text(
        json.dumps(
            {
                "characters": [
                    {
                        "character_id": "CHAR_protagonist",
                        "state_path": character_state_rel,
                    }
                ]
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (book_root / character_state_rel).write_text(
        json.dumps(
            {
                "character_id": "CHAR_protagonist",
                "name": "Rhea",
                "appearance_current": {"summary": "Rain-dark cloak and scraped knuckles."},
                "last_touched": {"chapter": 1, "scene": 1},
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    setting_dir = book_root / "draft" / "context" / "settings" / "ch_001" / "scene_001"
    setting_dir.mkdir(parents=True, exist_ok=True)
    (setting_dir / "author_drafted.setting.json").write_text(
        json.dumps(
            {
                "location_label": "Front Gate",
                "background_details": ["Rain beads on the ironwork."],
                "sensory_anchors": ["rain", "cold iron"],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    append_signature_records(
        tmp_path,
        [
            {
                "schema_version": "thought_signature_v1",
                "signature_id": "sig-write-t1",
                "created_at": "2026-04-26T12:00:00Z",
                "book_id": "my_book",
                "workflow_family": "section_write",
                "phase_id": "write_scene_prose",
                "turn_id": "T1",
                "chapter_id": 1,
                "scene_id": 1,
                "label": "write_scene_prose_t1",
            }
        ],
    )


def test_write_scene_prose_generates_provisional_receipts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    _write_projection_context_artifacts(tmp_path, book_root)

    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "writer-model")
    monkeypatch.setattr(
        "bookforge.execution.scene_actions._write_scene",
        lambda *args, **kwargs: (
            "Rhea slammed her palm against the lock until the bolt snapped free.",
            {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        ),
    )

    request = build_write_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = write_scene_prose(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "write_scene_prose"
    assert [item.artifact_status for item in result.produced_artifacts] == ["provisional", "provisional"]
    assert execution_result["action"] == "write_scene_prose"
    assert execution_result["status"] == "success"
    assert len(execution_result["produced_artifacts"]) == 2
    scene_context = execution_result["details"]["scene_context_projection"]
    assert scene_context["projection_status"] == "available"
    assert scene_context["used_as_prompt_input"] is False
    assert scene_context["availability"]["appearance_available"] is True
    assert scene_context["setting"]["source_mode"] == "author_drafted"
    assert scene_context["thought_context"]["selected_signatures"][0]["signature_id"] == "sig-write-t1"
    assert not (book_root / "draft" / "chapters" / "ch_001" / "scene_001.md").exists()


def test_plan_scene_action_generates_provisional_scene_card_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    def _fake_plan_scene(*args, **kwargs):
        return _write_phase_artifact(book_root, 1, 1, "scene_card", _scene_card(), as_json=True)

    monkeypatch.setattr("bookforge.execution.scene_actions._plan_scene", _fake_plan_scene)

    request = build_plan_scene_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = plan_scene_action(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "plan_scene"
    assert [item.artifact_status for item in result.produced_artifacts] == ["provisional"]
    assert execution_result["action"] == "plan_scene"
    assert execution_result["status"] == "success"
    assert execution_result["produced_artifacts"][0]["artifact_key"] == "scene_card"


def test_continue_scene_executes_one_recommended_child_and_records_wrapper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    def _fake_plan_scene(*args, **kwargs):
        return _write_phase_artifact(book_root, 1, 1, "scene_card", _scene_card(), as_json=True)

    monkeypatch.setattr("bookforge.execution.scene_actions._plan_scene", _fake_plan_scene)

    request = build_continue_scene_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = continue_scene(tmp_path, request)
    execution_results = _read_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "continue_scene"
    assert result.details["macro_kind"] == "single_recommended_scene_phase_step"
    assert result.details["child_action"] == "plan_scene"
    assert result.details["child_status"] == "success"
    assert result.details["before_scene_status"] == "unstarted"
    assert result.details["before_recommended_next_action"] == "plan_scene"
    assert result.details["after_scene_status"] == "planned"
    assert result.details["after_recommended_next_action"] == "preflight_scene_state"
    assert result.details["recommended_next_action"] == "preflight_scene_state"
    assert result.details["stop_reason"] is None
    assert result.details["pre_readiness_ref"]["scene_status"] == "unstarted"
    assert result.details["post_readiness_ref"]["scene_status"] == "planned"
    assert result.details["child_mutation_scope"] == "provisional"
    assert result.details["canonical_changed"] is False
    assert result.details["produced_artifact_refs"][0]["artifact_key"] == "scene_card"
    assert result.details["produced_artifact_refs"][0]["artifact_status"] == "provisional"
    step_receipt = result.details["author_loop_step_receipt"]
    assert step_receipt["schema_version"] == "author_loop_step_receipt_v1"
    assert step_receipt["action_run"] == "plan_scene"
    assert step_receipt["child_status"] == "success"
    assert step_receipt["canonical_changed"] is False
    assert step_receipt["next_recommended_action"] == "preflight_scene_state"
    assert step_receipt["stop_reason"] is None
    assert step_receipt["produced_artifact_refs"][0]["artifact_key"] == "scene_card"
    assert [item.artifact_key for item in result.produced_artifacts] == ["scene_card"]
    assert execution_results[-2]["action"] == "plan_scene"
    assert execution_results[-1]["action"] == "continue_scene"
    assert execution_results[-1]["details"]["child_result_id"] == execution_results[-2]["result_id"]
    assert execution_results[-1]["details"]["stop_reason"] is None


def test_continue_scene_branch_local_heartbeat_preserves_main_and_exposes_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="heartbeat-branch",
        merge_operation="promotion",
        branch_role="authoring_heartbeat",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "heartbeat-branch")

    def _fake_plan_scene(*args, **kwargs):
        return _write_phase_artifact(branch_root, 1, 1, "scene_card", _scene_card(), as_json=True)

    monkeypatch.setattr("bookforge.execution.scene_actions._plan_scene", _fake_plan_scene)

    request = build_continue_scene_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        branch_id="heartbeat-branch",
    )
    result = continue_scene(tmp_path, request)
    branch_results = _read_jsonl(supervision_paths.execution_results_path(book_root, "heartbeat-branch"))
    main_scene_card = book_root / result.artifact_paths["scene_card"]
    branch_scene_card = branch_root / result.artifact_paths["scene_card"]
    artifact_index = get_branch_artifact_index(tmp_path, "my_book", "heartbeat-branch")
    diff = get_branch_diff_summary(tmp_path, "my_book", "heartbeat-branch")
    target = get_next_writing_target(
        tmp_path,
        "my_book",
        branch_id="heartbeat-branch",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        prefer_emitted=False,
    )
    records = {record.path: record for record in artifact_index.records}
    changed_paths = {record.path for record in diff.changed_records}

    assert result.status == "success"
    assert result.action == "continue_scene"
    assert result.selector.branch_id == "heartbeat-branch"
    assert result.details["child_action"] == "plan_scene"
    assert result.details["canonical_changed"] is False
    assert result.details["author_loop_step_receipt"]["canonical_changed"] is False
    assert result.details["author_loop_step_receipt"]["next_recommended_action"] == "preflight_scene_state"
    assert branch_results[-2]["action"] == "plan_scene"
    assert branch_results[-1]["action"] == "continue_scene"
    assert not main_scene_card.exists()
    assert branch_scene_card.exists()
    assert records[result.artifact_paths["scene_card"]].branch_relationship == "branch_only"
    assert records[result.artifact_paths["scene_card"]].artifact_class == "scene_phase_artifact"
    assert records[result.artifact_paths["scene_card"]].artifact_status == "provisional"
    assert result.artifact_paths["scene_card"] in changed_paths
    assert target.branch_id == "heartbeat-branch"
    assert target.status == "ready"
    assert target.recommended_action == "continue_scene"
    assert target.details["scene_readiness_recommended_next_action"] == "preflight_scene_state"


def test_continue_scene_branch_local_commit_reports_completed_scope(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="heartbeat-branch",
        merge_operation="promotion",
        branch_role="authoring_heartbeat",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "heartbeat-branch")
    _record_artifact(branch_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    _record_artifact(
        branch_root,
        1,
        1,
        "preflight",
        "preflight_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        branch_root,
        1,
        1,
        "continuity_pack",
        "continuity_pack",
        {
            "scene_end_anchor": "The lock clicks.",
            "constraints": [],
            "open_threads": [],
            "cast_present": ["Rhea"],
            "location": "Front Gate",
            "next_action": "Open the door.",
            "summary": {},
        },
        artifact_key="pack",
    )
    _record_write_pair(branch_root)
    _record_artifact(
        branch_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        branch_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "smoke"},
        artifact_key="report",
    )

    request = build_continue_scene_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        branch_id="heartbeat-branch",
    )
    result = continue_scene(tmp_path, request)
    target = get_next_writing_target(
        tmp_path,
        "my_book",
        branch_id="heartbeat-branch",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        prefer_emitted=False,
    )

    assert result.status == "success"
    assert result.details["child_action"] == "apply_scene_commit"
    assert result.details["canonical_changed"] is False
    assert result.details["stop_reason"] == "completed_scope"
    assert result.details["recommended_next_action"] is None
    assert result.details["author_loop_step_receipt"]["stop_reason"] == "completed_scope"
    assert result.details["author_loop_step_receipt"]["next_recommended_action"] is None
    assert target.status == "blocked"
    assert target.recommended_action == "lock_section_from_written_state"


def test_continue_scene_no_ready_child_reports_no_legal_action_stop_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_book(tmp_path)
    selector = ScopeSelector(
        book_id="my_book",
        branch_id="main",
        workflow_family="section_write",
        chapter=1,
        section=1,
        scene=1,
        phase_id="continue_scene",
    )
    node = TimelineNodeRef(
        book_id="my_book",
        workflow_family="section_write",
        source_run_id="run_001",
        branch_id="main",
        chapter=1,
        section=1,
        scene=1,
        phase_id="continue_scene",
        revision_id="rev_001",
    )
    readiness = ScenePhaseReadiness(
        book_id="my_book",
        selector=selector,
        node=node,
        scene_status="committed",
        actions=[],
        recommended_next_action=None,
        updated_at="2026-04-28T00:00:00Z",
    )
    request = ExecutionRequest(
        request_id="continue-noop",
        action="continue_scene",
        selector=selector,
        expected_node=node,
        branch_id="main",
        requested_at="2026-04-28T00:00:00Z",
        details={},
    )

    monkeypatch.setattr("bookforge.execution.scene_sequence.current_execution_node", lambda *args, **kwargs: node)
    monkeypatch.setattr("bookforge.execution.scene_sequence.get_scene_phase_readiness", lambda *args, **kwargs: readiness)

    result = continue_scene(tmp_path, request)

    assert result.status == "no_op"
    assert result.details["child_action"] is None
    assert result.details["stop_reason"] == "no_legal_action"
    assert result.details["pre_readiness_ref"]["scene_status"] == "committed"
    assert result.details["post_readiness_ref"]["recommended_next_action"] is None
    assert result.details["produced_artifact_refs"] == []
    assert result.details["author_loop_step_receipt"]["stop_reason"] == "no_legal_action"
    assert result.details["author_loop_step_receipt"]["action_run"] is None


@pytest.mark.parametrize(
    ("child_status", "child_details", "after_recommended_action", "expected_stop_reason"),
    [
        ("retryable_pause", {}, "plan_scene", "provider_failed"),
        ("hard_fail", {"failure_code": "stale_write"}, "plan_scene", "branch_stale"),
        ("hard_fail", {}, "plan_scene", "tool_unavailable"),
        ("integrity_degraded", {}, "plan_scene", "tool_unavailable"),
        ("success", {}, None, "completed_scope"),
    ],
)
def test_continue_scene_maps_child_outcome_to_loop_stop_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    child_status: str,
    child_details: dict,
    after_recommended_action: str | None,
    expected_stop_reason: str,
) -> None:
    _init_book(tmp_path)
    selector = ScopeSelector(
        book_id="my_book",
        branch_id="author-branch",
        workflow_family="section_write",
        chapter=1,
        section=1,
        scene=1,
        phase_id="continue_scene",
    )
    node = TimelineNodeRef(
        book_id="my_book",
        workflow_family="section_write",
        source_run_id="run_001",
        branch_id="author-branch",
        chapter=1,
        section=1,
        scene=1,
        phase_id="continue_scene",
        revision_id="rev_001",
    )
    before = ScenePhaseReadiness(
        book_id="my_book",
        selector=selector,
        node=node,
        scene_status="ready",
        actions=[
            ScenePhaseActionReadiness(
                action="plan_scene",
                legal=True,
                ready=True,
                mutation_scope="provisional",
                recommended=True,
            )
        ],
        recommended_next_action="plan_scene",
        updated_at="2026-04-28T00:00:00Z",
    )
    after = ScenePhaseReadiness(
        book_id="my_book",
        selector=selector,
        node=node,
        scene_status="after-child",
        actions=[],
        recommended_next_action=after_recommended_action,
        updated_at="2026-04-28T00:00:01Z",
    )
    child_result = ExecutionResult(
        result_id="child-result",
        action="plan_scene",
        status=child_status,
        node=node,
        selector=selector,
        message="child outcome",
        details=child_details,
        request_id="child-request",
    )
    request = ExecutionRequest(
        request_id="continue-stop-map",
        action="continue_scene",
        selector=selector,
        expected_node=node,
        branch_id="author-branch",
        requested_at="2026-04-28T00:00:00Z",
        details={},
    )
    readiness_results = iter([before, after])

    monkeypatch.setattr("bookforge.execution.scene_sequence.current_execution_node", lambda *args, **kwargs: node)
    monkeypatch.setattr("bookforge.execution.scene_sequence.get_scene_phase_readiness", lambda *args, **kwargs: next(readiness_results))
    monkeypatch.setattr("bookforge.execution.scene_sequence.run_scene_phase_action", lambda *args, **kwargs: child_result)

    result = continue_scene(tmp_path, request)

    assert result.details["stop_reason"] == expected_stop_reason
    assert result.details["author_loop_step_receipt"]["stop_reason"] == expected_stop_reason
    assert result.details["author_loop_step_receipt"]["child_status"] == child_status
    assert result.details["author_loop_step_receipt"]["canonical_changed"] is False


def test_plan_scene_action_returns_no_op_when_scene_card_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    scene_path = book_root / "draft" / "chapters" / "ch_001" / "scene_001.meta.json"
    scene_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.write_text(json.dumps(_scene_card(), ensure_ascii=True, indent=2), encoding="utf-8")
    _record_phase_success(
        book_root,
        1,
        1,
        "plan",
        {"scene_card": scene_path.relative_to(book_root).as_posix()},
    )

    monkeypatch.setattr(
        "bookforge.execution.scene_actions._plan_scene",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    request = build_plan_scene_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = plan_scene_action(tmp_path, request)

    assert result.status == "no_op"
    assert result.produced_artifacts[0].artifact_key == "scene_card"


def test_preflight_scene_state_generates_provisional_patch_receipt_without_applying_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _record_artifact(book_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    state_path = book_root / "state.json"
    before_state = json.loads(state_path.read_text(encoding="utf-8"))

    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "preflight-model")
    monkeypatch.setattr(
        "bookforge.execution.scene_actions._scene_state_preflight",
        lambda *args, **kwargs: {
            "summary_update": {"current": "Rhea studies the lock."},
            "character_updates": [],
            "character_continuity_system_updates": [],
        },
    )

    request = build_preflight_scene_state_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = preflight_scene_state(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "preflight_scene_state"
    assert [item.artifact_status for item in result.produced_artifacts] == ["provisional"]
    assert result.produced_artifacts[0].artifact_key == "preflight_patch"
    assert json.loads(state_path.read_text(encoding="utf-8")) == before_state
    assert execution_result["action"] == "preflight_scene_state"
    assert execution_result["status"] == "success"


def test_preflight_scene_state_returns_no_op_when_patch_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _record_artifact(book_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    _record_artifact(
        book_root,
        1,
        1,
        "preflight",
        "preflight_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )

    monkeypatch.setattr(
        "bookforge.execution.scene_actions._scene_state_preflight",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    request = build_preflight_scene_state_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = preflight_scene_state(tmp_path, request)

    assert result.status == "no_op"
    assert result.produced_artifacts[0].artifact_key == "preflight_patch"


def test_generate_continuity_pack_produces_derived_receipt_without_applying_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _record_artifact(book_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    _record_artifact(
        book_root,
        1,
        1,
        "preflight",
        "preflight_patch",
        {"summary_update": {"current": "Rhea studies the lock."}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    state_path = book_root / "state.json"
    before_state = json.loads(state_path.read_text(encoding="utf-8"))

    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "continuity-model")
    monkeypatch.setattr(
        "bookforge.execution.scene_actions._generate_continuity_pack",
        lambda *args, **kwargs: {
            "scene_end_anchor": "The lock clicks.",
            "constraints": [],
            "open_threads": [],
            "cast_present": ["Rhea"],
            "location": "Front Gate",
            "next_action": "Open the door.",
            "summary": {"current": "Rhea studies the lock."},
        },
    )

    request = build_generate_continuity_pack_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = generate_continuity_pack(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "generate_continuity_pack"
    assert [item.artifact_status for item in result.produced_artifacts] == ["derived"]
    assert result.produced_artifacts[0].artifact_key == "continuity_pack"
    assert json.loads(state_path.read_text(encoding="utf-8")) == before_state
    assert execution_result["action"] == "generate_continuity_pack"
    assert execution_result["status"] == "success"
    assert execution_result["produced_artifacts"][0]["artifact_status"] == "derived"


def test_generate_continuity_pack_returns_no_op_when_pack_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _record_artifact(book_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    _record_artifact(
        book_root,
        1,
        1,
        "preflight",
        "preflight_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "continuity_pack",
        "continuity_pack",
        {"scene_end_anchor": "The lock clicks."},
        artifact_key="pack",
    )

    monkeypatch.setattr(
        "bookforge.execution.scene_actions._generate_continuity_pack",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    request = build_generate_continuity_pack_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = generate_continuity_pack(tmp_path, request)

    assert result.status == "no_op"
    assert result.produced_artifacts[0].artifact_key == "continuity_pack"
    assert result.produced_artifacts[0].artifact_status == "derived"


def test_generate_continuity_pack_refuses_unsupported_preflight_materialization(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _record_artifact(book_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    _record_artifact(
        book_root,
        1,
        1,
        "preflight",
        "preflight_patch",
        {
            "summary_update": {},
            "character_updates": [{"character_id": "CHAR_protagonist", "notes": "Moved."}],
            "character_continuity_system_updates": [],
        },
        artifact_key="patch",
    )

    request = build_generate_continuity_pack_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = generate_continuity_pack(tmp_path, request)

    assert result.status == "hard_fail"
    assert result.details["failure_code"] == "unsupported_preflight_materialization"


def test_write_scene_prose_returns_no_op_when_outputs_already_exist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Existing draft prose.", as_json=False)
    patch_path = _write_phase_artifact(
        book_root,
        1,
        1,
        "write_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        as_json=True,
    )
    _record_phase_success(
        book_root,
        1,
        1,
        "write",
        {
            "prose": prose_path.relative_to(book_root).as_posix(),
            "patch": patch_path.relative_to(book_root).as_posix(),
        },
    )

    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "writer-model")

    request = build_write_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = write_scene_prose(tmp_path, request)

    assert result.status == "no_op"
    assert [item.artifact_status for item in result.produced_artifacts] == ["provisional", "provisional"]


def test_write_scene_prose_refuses_unsupported_preflight_materialization(tmp_path: Path) -> None:
    _setup_scene_with_prereqs(tmp_path)
    book_root = tmp_path / "books" / "my_book"
    preflight_path = _write_phase_artifact(
        book_root,
        1,
        1,
        "preflight_patch",
        {
            "summary_update": {},
            "character_updates": [{"character_id": "CHAR_protagonist", "notes": "Moved."}],
            "character_continuity_system_updates": [],
        },
        as_json=True,
    )
    _record_phase_success(
        book_root,
        1,
        1,
        "preflight",
        {"patch": preflight_path.relative_to(book_root).as_posix()},
    )

    request = build_write_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = write_scene_prose(tmp_path, request)

    assert result.status == "hard_fail"
    assert result.details["failure_code"] == "unsupported_preflight_materialization"


def test_state_repair_scene_patch_generates_provisional_receipt_without_applying_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Rhea forced the lock open.", as_json=False)
    patch_path = _write_phase_artifact(
        book_root,
        1,
        1,
        "write_patch",
        {"summary_update": {"last_scene": ["Rhea forced the lock open."]}, "character_updates": [], "character_continuity_system_updates": []},
        as_json=True,
    )
    _record_phase_success(
        book_root,
        1,
        1,
        "write",
        {
            "prose": prose_path.relative_to(book_root).as_posix(),
            "patch": patch_path.relative_to(book_root).as_posix(),
        },
    )
    state_path = book_root / "state.json"
    before_state = json.loads(state_path.read_text(encoding="utf-8"))

    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "state-repair-model")
    monkeypatch.setattr(
        "bookforge.execution.scene_actions._state_repair",
        lambda *args, **kwargs: {
            "summary_update": {"last_scene": ["Rhea forced the lock open cleanly."]},
            "character_updates": [],
            "character_continuity_system_updates": [],
        },
    )

    request = build_state_repair_scene_patch_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = state_repair_scene_patch(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "state_repair_scene_patch"
    assert [item.artifact_status for item in result.produced_artifacts] == ["provisional"]
    assert result.produced_artifacts[0].artifact_key == "state_repair_patch"
    assert json.loads(state_path.read_text(encoding="utf-8")) == before_state
    assert execution_result["action"] == "state_repair_scene_patch"
    assert execution_result["status"] == "success"


def test_state_repair_scene_patch_returns_no_op_when_patch_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Rhea forced the lock open.", as_json=False)
    patch_path = _write_phase_artifact(
        book_root,
        1,
        1,
        "write_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        as_json=True,
    )
    _record_phase_success(
        book_root,
        1,
        1,
        "write",
        {
            "prose": prose_path.relative_to(book_root).as_posix(),
            "patch": patch_path.relative_to(book_root).as_posix(),
        },
    )
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )

    monkeypatch.setattr(
        "bookforge.execution.scene_actions._state_repair",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    request = build_state_repair_scene_patch_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = state_repair_scene_patch(tmp_path, request)

    assert result.status == "no_op"
    assert result.produced_artifacts[0].artifact_key == "state_repair_patch"
    assert result.produced_artifacts[0].artifact_status == "provisional"


def test_lint_scene_prose_generates_provisional_report_without_applying_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Rhea forced the lock open.", as_json=False)
    write_patch_path = _write_phase_artifact(
        book_root,
        1,
        1,
        "write_patch",
        {"summary_update": {"last_scene": ["Rhea forced the lock open."]}, "character_updates": [], "character_continuity_system_updates": []},
        as_json=True,
    )
    _record_phase_success(
        book_root,
        1,
        1,
        "write",
        {
            "prose": prose_path.relative_to(book_root).as_posix(),
            "patch": write_patch_path.relative_to(book_root).as_posix(),
        },
    )
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["Rhea forced the lock open cleanly."]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    state_path = book_root / "state.json"
    before_state = json.loads(state_path.read_text(encoding="utf-8"))

    monkeypatch.setattr("bookforge.execution.scene_actions._lint_mode", lambda: "strict")
    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "linter-model")
    monkeypatch.setattr(
        "bookforge.execution.scene_actions._lint_scene",
        lambda *args, **kwargs: {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "llm"},
    )

    request = build_lint_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = lint_scene_prose(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "lint_scene_prose"
    assert [item.artifact_status for item in result.produced_artifacts] == ["provisional"]
    assert result.produced_artifacts[0].artifact_key == "lint_report"
    assert json.loads(state_path.read_text(encoding="utf-8")) == before_state
    assert execution_result["action"] == "lint_scene_prose"
    assert execution_result["status"] == "success"
    assert execution_result["details"]["lint_status"] == "pass"


def test_lint_scene_prose_returns_no_op_when_report_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Rhea forced the lock open.", as_json=False)
    write_patch_path = _write_phase_artifact(
        book_root,
        1,
        1,
        "write_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        as_json=True,
    )
    _record_phase_success(
        book_root,
        1,
        1,
        "write",
        {
            "prose": prose_path.relative_to(book_root).as_posix(),
            "patch": write_patch_path.relative_to(book_root).as_posix(),
        },
    )
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "llm"},
        artifact_key="report",
    )

    monkeypatch.setattr(
        "bookforge.execution.scene_actions._lint_scene",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    request = build_lint_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = lint_scene_prose(tmp_path, request)

    assert result.status == "no_op"
    assert result.produced_artifacts[0].artifact_key == "lint_report"
    assert result.produced_artifacts[0].artifact_status == "provisional"


def test_repair_scene_prose_generates_provisional_receipts_without_applying_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    _record_write_pair(book_root)
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["Rhea forced the lock open cleanly."]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "fail", "issues": [{"code": "pacing_overlap"}], "mode": "llm"},
        artifact_key="report",
    )
    state_path = book_root / "state.json"
    before_state = json.loads(state_path.read_text(encoding="utf-8"))

    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "repair-model")
    monkeypatch.setattr(
        "bookforge.execution.scene_actions._repair_scene",
        lambda *args, **kwargs: (
            "Rhea forced the lock open without repeating the prior beat.",
            {
                "summary_update": {"last_scene": ["Rhea forced the lock open without repeating the prior beat."]},
                "character_updates": [],
                "character_continuity_system_updates": [],
            },
        ),
    )

    request = build_repair_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = repair_scene_prose(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert result.status == "success"
    assert result.action == "repair_scene_prose"
    assert [item.artifact_key for item in result.produced_artifacts] == ["repair_prose", "repair_patch"]
    assert [item.artifact_status for item in result.produced_artifacts] == ["provisional", "provisional"]
    assert json.loads(state_path.read_text(encoding="utf-8")) == before_state
    assert execution_result["action"] == "repair_scene_prose"
    assert execution_result["status"] == "success"


def test_repair_scene_prose_returns_no_op_when_current_repair_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    _record_write_pair(book_root)
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "fail", "issues": [{"code": "pacing_overlap"}], "mode": "llm"},
        artifact_key="report",
    )
    _record_repair_pair(book_root)

    monkeypatch.setattr(
        "bookforge.execution.scene_actions._repair_scene",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    request = build_repair_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = repair_scene_prose(tmp_path, request)

    assert result.status == "no_op"
    assert result.produced_artifacts[0].artifact_key == "repair_prose"
    assert result.produced_artifacts[0].artifact_status == "provisional"


def test_state_repair_scene_patch_uses_latest_repair_outputs_when_repair_is_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    _record_write_pair(book_root, prose="Original draft prose.")
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["Original draft prose."]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "fail", "issues": [{"code": "pacing_overlap"}], "mode": "llm"},
        artifact_key="report",
    )
    _record_repair_pair(
        book_root,
        prose="Repaired draft prose.",
        patch={"summary_update": {"last_scene": ["Repaired draft prose."]}, "character_updates": [], "character_continuity_system_updates": []},
    )

    captured: dict[str, object] = {}
    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "state-repair-model")

    def _capture_state_repair(*args, **kwargs):
        captured["prose"] = args[3]
        captured["source_patch"] = args[7]
        return {"summary_update": {"last_scene": ["post-repair state"]}, "character_updates": [], "character_continuity_system_updates": []}

    monkeypatch.setattr("bookforge.execution.scene_actions._state_repair", _capture_state_repair)

    request = build_state_repair_scene_patch_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = state_repair_scene_patch(tmp_path, request)

    assert result.status == "success"
    assert captured["prose"] == "Repaired draft prose."
    assert captured["source_patch"] == {
        "summary_update": {"last_scene": ["Repaired draft prose."]},
        "character_updates": [],
        "character_continuity_system_updates": [],
    }


def test_lint_scene_prose_uses_latest_repair_prose_when_repair_is_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    _record_write_pair(book_root, prose="Original draft prose.")
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["Original draft prose."]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "fail", "issues": [{"code": "pacing_overlap"}], "mode": "llm"},
        artifact_key="report",
    )
    _record_repair_pair(
        book_root,
        prose="Repaired draft prose.",
        patch={"summary_update": {"last_scene": ["Repaired draft prose."]}, "character_updates": [], "character_continuity_system_updates": []},
    )
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["post-repair state"]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )

    captured: dict[str, object] = {}
    monkeypatch.setattr("bookforge.execution.scene_actions._lint_mode", lambda: "strict")
    monkeypatch.setattr("bookforge.execution.scene_actions.load_config", lambda: {})
    monkeypatch.setattr("bookforge.execution.scene_actions.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.execution.scene_actions.resolve_model", lambda phase, config: "linter-model")

    def _capture_lint(*args, **kwargs):
        captured["prose"] = args[3]
        return {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "llm"}

    monkeypatch.setattr("bookforge.execution.scene_actions._lint_scene", _capture_lint)

    request = build_lint_scene_prose_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = lint_scene_prose(tmp_path, request)

    assert result.status == "success"
    assert captured["prose"] == "Repaired draft prose."


def test_apply_scene_commit_commits_latest_passing_provisional_scene_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    _record_write_pair(
        book_root,
        prose="Original draft prose.",
        patch={"summary_update": {"last_scene": ["Original draft prose."]}, "character_updates": [], "character_continuity_system_updates": []},
    )
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["Original draft prose."]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "fail", "issues": [{"code": "pacing_overlap"}], "mode": "llm"},
        artifact_key="report",
    )
    _record_repair_pair(
        book_root,
        prose="Repaired draft prose.",
        patch={"summary_update": {"last_scene": ["Repaired draft prose."]}, "character_updates": [], "character_continuity_system_updates": []},
    )
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["post-repair state"]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "llm"},
        artifact_key="report",
    )

    monkeypatch.setattr("bookforge.execution.scene_actions.refresh_appearance_projections", lambda *args, **kwargs: [])

    request = build_apply_scene_commit_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = apply_scene_commit(tmp_path, request)
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))
    state = json.loads((book_root / "state.json").read_text(encoding="utf-8"))
    prose_path = book_root / "draft" / "chapters" / "ch_001" / "scene_001.md"
    meta_path = book_root / "draft" / "chapters" / "ch_001" / "scene_001.meta.json"
    chapter_markdown = book_root / "draft" / "chapters" / "ch_001.md"

    assert result.status == "success"
    assert result.action == "apply_scene_commit"
    assert prose_path.read_text(encoding="utf-8").strip() == "Repaired draft prose."
    assert meta_path.exists()
    assert chapter_markdown.exists()
    assert state["status"] == "COMPLETE"
    assert result.details["source_prose_phase"] == "repair"
    assert result.details["canonical_change_status"] == "canonical"
    assert result.details["canonical_changed"] is True
    assert [item.artifact_key for item in result.produced_artifacts[:3]] == ["state", "scene_prose", "scene_meta"]
    assert execution_result["action"] == "apply_scene_commit"
    assert execution_result["status"] == "success"
    assert execution_result["details"]["canonical_change_status"] == "canonical"
    assert execution_result["details"]["canonical_changed"] is True


def test_apply_scene_commit_returns_no_op_when_scene_is_already_committed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_root = _setup_scene_with_prereqs(tmp_path)
    _record_write_pair(book_root)
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "llm"},
        artifact_key="report",
    )
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / "scene_001.md").write_text("Committed prose.\n", encoding="utf-8")
    (chapter_dir / "scene_001.meta.json").write_text(json.dumps({"scene_id": 1}, ensure_ascii=True, indent=2), encoding="utf-8")

    monkeypatch.setattr(
        "bookforge.execution.scene_actions._write_scene_files",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    request = build_apply_scene_commit_request(tmp_path, "my_book", chapter_id=1, scene_id=1, section_id=1)
    result = apply_scene_commit(tmp_path, request)

    assert result.status == "no_op"
    assert [item.artifact_key for item in result.produced_artifacts] == ["scene_prose", "scene_meta"]
    assert all(item.artifact_status == "authoritative" for item in result.produced_artifacts)
