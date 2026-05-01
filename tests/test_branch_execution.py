from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.branching import (
    create_branch,
    discard_branch,
    load_branch_manifest,
    promote_branch_to_parent,
    rebase_branch,
    rerun_freeze_section_on_branch,
)
from bookforge.contracts import ScopeSelector
from bookforge.execution import apply_scene_commit, build_apply_scene_commit_request, build_write_section_request, write_frozen_section
from bookforge.pipeline.phase_history import _record_phase_success, _write_phase_artifact
from bookforge.query import get_scene_phase_readiness, get_workspace_status, get_workspace_status_for_branch, list_execution_options
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


def _scene_card() -> dict:
    return {
        "schema_version": "1.1",
        "scene_id": "SC_001_001",
        "chapter": 1,
        "scene": 1,
        "section_id": 1,
        "scene_target": "First scene.",
        "goal": "Open the door.",
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
        "cast_present_ids": ["rhea_mercer"],
        "cast_present": ["Rhea Mercer"],
    }


def _record_artifact(book_root: Path, chapter: int, scene: int, phase: str, name: str, payload, *, as_json: bool = True, artifact_key: str) -> None:
    path = _write_phase_artifact(book_root, chapter, scene, name, payload, as_json=as_json)
    _record_phase_success(
        book_root,
        chapter,
        scene,
        phase,
        {artifact_key: path.relative_to(book_root).as_posix()},
    )


def _record_branch_commit_prereqs(branch_root: Path) -> None:
    patch = {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []}
    _record_artifact(branch_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")
    prose_path = _write_phase_artifact(branch_root, 1, 1, "write_prose", "Branch-local scene prose.", as_json=False)
    patch_path = _write_phase_artifact(branch_root, 1, 1, "write_patch", patch, as_json=True)
    _record_phase_success(
        branch_root,
        1,
        1,
        "write",
        {
            "prose": prose_path.relative_to(branch_root).as_posix(),
            "patch": patch_path.relative_to(branch_root).as_posix(),
        },
    )
    _record_artifact(branch_root, 1, 1, "state_repair", "state_repair_patch", patch, artifact_key="patch")
    _record_artifact(
        branch_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "llm"},
        artifact_key="report",
    )


def _write_committed_scene(book_root: Path, text: str) -> None:
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / "scene_001.md").write_text(text, encoding="utf-8")
    (chapter_dir / "scene_001.meta.json").write_text(
        json.dumps({"scene_id": 1, "chapter": 1}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


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


def test_get_workspace_status_for_branch_reads_branch_snapshot_and_node(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )

    status = get_workspace_status_for_branch(tmp_path, "my_book", branch_id="rerun-sec1", prefer_emitted=False)

    assert status.current_node is not None
    assert status.current_node.branch_id == "rerun-sec1"
    assert status.source_run_id == "run_001"
    assert status.active_section is not None


def test_branch_scene_phase_readiness_uses_branch_scope_not_main_cursor(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="rerun-sec1",
    )
    state_path = book_root / "state.json"
    state = _read_json(state_path)
    state["cursor"] = {"chapter": 9, "scene": 3}
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        prefer_emitted=False,
    )
    options = list_execution_options(
        tmp_path,
        ScopeSelector(book_id="my_book", branch_id="rerun-sec1", workflow_family="section_write", chapter=1, section=1, scene=1),
        prefer_emitted=False,
    )

    assert readiness.selector.branch_id == "rerun-sec1"
    assert readiness.scene_status == "unstarted"
    assert readiness.recommended_next_action == "plan_scene"
    assert all("active cursor scene" not in str(action.refusal_reason or "") for action in readiness.actions)
    assert any(option.action == "plan_scene" for option in options)


def test_unknown_branch_scene_phase_readiness_refuses_without_main_fallback(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        branch_id="missing-branch",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        prefer_emitted=False,
    )

    assert readiness.selector.branch_id == "missing-branch"
    assert readiness.recommended_next_action is None
    assert readiness.actions
    assert all(action.legal is False for action in readiness.actions)
    assert {action.refusal_reason for action in readiness.actions} == {"Branch missing-branch does not exist."}


def test_branch_apply_scene_commit_writes_only_to_branch_snapshot(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="rewrite-scene1",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "rewrite-scene1")
    _record_branch_commit_prereqs(branch_root)

    request = build_apply_scene_commit_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        branch_id="rewrite-scene1",
    )
    result = apply_scene_commit(tmp_path, request)

    main_scene = book_root / "draft" / "chapters" / "ch_001" / "scene_001.md"
    branch_scene = branch_root / "draft" / "chapters" / "ch_001" / "scene_001.md"
    execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, "rewrite-scene1"))

    assert result.status == "success"
    assert result.node.branch_id == "rewrite-scene1"
    assert branch_scene.read_text(encoding="utf-8").strip() == "Branch-local scene prose."
    assert not main_scene.exists()
    assert execution_result["action"] == "apply_scene_commit"
    assert execution_result["node"]["branch_id"] == "rewrite-scene1"
    assert "canonical_change_status" not in execution_result["details"]
    assert execution_result["details"]["canonical_changed"] is False
    assert execution_result["details"]["branch_change_status"] == "changed"


def test_nested_scene_branch_promotes_to_parent_without_touching_main(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="chapter-branch",
    )
    child_manifest = create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="chapter-branch", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="scene-branch",
    )
    child_root = supervision_paths.branch_snapshot_root(book_root, "scene-branch")
    _record_branch_commit_prereqs(child_root)
    request = build_apply_scene_commit_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        branch_id="scene-branch",
    )
    apply_scene_commit(tmp_path, request)

    promoted = promote_branch_to_parent(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="scene-branch",
        target_branch_id="chapter-branch",
    )

    parent_scene = supervision_paths.branch_snapshot_root(book_root, "chapter-branch") / "draft" / "chapters" / "ch_001" / "scene_001.md"
    main_scene = book_root / "draft" / "chapters" / "ch_001" / "scene_001.md"
    parent_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, "chapter-branch"))

    assert child_manifest.parent_node.branch_id == "chapter-branch"
    assert promoted.lifecycle_state == "promoted"
    assert parent_scene.read_text(encoding="utf-8").strip() == "Branch-local scene prose."
    assert not main_scene.exists()
    assert parent_execution_result["action"] == "promote_branch_to_parent"
    assert parent_execution_result["details"]["target_branch_id"] == "chapter-branch"


def test_branch_apply_scene_commit_rewrites_existing_branch_scene_with_original_backup(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _write_committed_scene(book_root, "Original main scene.")
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="rewrite-existing",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "rewrite-existing")
    _record_branch_commit_prereqs(branch_root)

    request = build_apply_scene_commit_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        branch_id="rewrite-existing",
    )
    result = apply_scene_commit(tmp_path, request)

    branch_scene = branch_root / "draft" / "chapters" / "ch_001" / "scene_001.md"
    original_backup = branch_root / "draft" / "chapters" / "ch_001" / "scene_001.original.md"
    main_scene = book_root / "draft" / "chapters" / "ch_001" / "scene_001.md"

    assert result.status == "success"
    assert branch_scene.read_text(encoding="utf-8").strip() == "Branch-local scene prose."
    assert original_backup.read_text(encoding="utf-8") == "Original main scene."
    assert main_scene.read_text(encoding="utf-8") == "Original main scene."


def test_branch_write_section_runs_against_branch_snapshot_only(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="section-write-branch",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "section-write-branch")

    def _stub_run_section_range(**kwargs):
        assert kwargs["workspace"] == tmp_path
        assert kwargs["book_id"] == "my_book"
        assert kwargs["chapter_id"] == 1
        assert kwargs["section_id"] == 1
        assert kwargs["scene_start"] == 1
        assert kwargs["scene_end"] == 1
        assert kwargs["branch_id"] == "section-write-branch"
        _write_committed_scene(branch_root, "Branch section prose.")

    monkeypatch.setattr("bookforge.execution.scoped.run_section_range", _stub_run_section_range)

    request = build_write_section_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        branch_id="section-write-branch",
    )
    result = write_frozen_section(tmp_path, request)

    assert result.details["pre_reconciliation_status"] == "success"
    assert result.node.branch_id == "section-write-branch"
    assert (branch_root / "draft" / "chapters" / "ch_001" / "scene_001.md").read_text(encoding="utf-8") == "Branch section prose."
    assert not (book_root / "draft" / "chapters" / "ch_001" / "scene_001.md").exists()


def test_rebase_branch_creates_refreshed_child_from_updated_parent(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="chapter-branch",
    )
    child_manifest = create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="chapter-branch", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="scene-branch",
    )
    parent_root = supervision_paths.branch_snapshot_root(book_root, "chapter-branch")
    _record_branch_commit_prereqs(parent_root)
    request = build_apply_scene_commit_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        branch_id="chapter-branch",
    )
    apply_scene_commit(tmp_path, request)

    rebased = rebase_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="scene-branch",
        new_branch_id="scene-branch-rebased",
    )

    old_manifest = load_branch_manifest(tmp_path, "my_book", "scene-branch")
    parent_manifest = load_branch_manifest(tmp_path, "my_book", "chapter-branch")

    assert child_manifest.parent_snapshot_revision != parent_manifest.parent_snapshot_revision
    assert old_manifest.lifecycle_state == "discard"
    assert old_manifest.validation_message == "Rebased into scene-branch-rebased; old branch discarded."
    assert rebased.branch_id == "scene-branch-rebased"
    assert rebased.parent_node.branch_id == "chapter-branch"
    assert rebased.parent_snapshot_revision != child_manifest.parent_snapshot_revision


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
    assert branch_execution_result["details"]["canonical_changed"] is False
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
