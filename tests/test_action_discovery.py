from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.branching import create_assembly_branch, create_branch, rerun_freeze_section_on_branch
from bookforge.llm.errors import LLMRequestError, QuotaViolation
from bookforge.memory.continuity import save_style_anchor, style_anchor_path
from bookforge.pipeline.run_logging import _write_latest_run_pointer
from bookforge.pipeline.phase_history import _record_phase_success, _write_phase_artifact
from bookforge.query import legal_next_actions, list_execution_options
from bookforge.contracts import ScopeSelector
from bookforge.runner import PAUSE_EXIT_CODE, _pause_on_quota
from bookforge.section_workflow import freeze_section_from_phase03_artifact, initialize_section_workflow
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
                                        "summary": "First scene.",
                                        "handoff_mode": "terminal",
                                        "transition_out_anchors": ["door"],
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


def _setup_paused_section(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    run_id = "writer_run_001"
    _write_latest_run_pointer(book_root, run_id)
    state_path = book_root / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
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


def _write_scene_artifacts(book_root: Path, chapter_id: int, scene_id: int, *, text: str) -> None:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / f"scene_{scene_id:03d}.md").write_text(text, encoding="utf-8")
    (chapter_dir / f"scene_{scene_id:03d}.meta.json").write_text(
        json.dumps({"scene_id": scene_id}, ensure_ascii=True, indent=2),
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


def _record_artifact(book_root: Path, chapter: int, scene: int, phase: str, name: str, payload, *, as_json: bool = True, artifact_key: str) -> None:
    path = _write_phase_artifact(book_root, chapter, scene, name, payload, as_json=as_json)
    _record_phase_success(
        book_root,
        chapter,
        scene,
        phase,
        {artifact_key: path.relative_to(book_root).as_posix()},
    )


def _record_write_pair(book_root: Path, prose: str = "Rhea forced the lock open.") -> None:
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", prose, as_json=False)
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


def _record_repair_pair(book_root: Path, prose: str = "Rhea forced the lock open cleanly.") -> None:
    prose_path = _write_phase_artifact(book_root, 1, 1, "repair_prose", prose, as_json=False)
    patch_path = _write_phase_artifact(
        book_root,
        1,
        1,
        "repair_patch",
        {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
        as_json=True,
    )
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


def test_list_execution_options_prefers_initialize_before_workflow_exists(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    selector = ScopeSelector(book_id="my_book", branch_id="main")
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["initialize_section_workflow"].allowed is True
    assert by_action["create_branch"].allowed is False
    assert by_action["freeze_section_from_phase03_artifact"].allowed is False
    assert by_action["resume_paused_section"].allowed is False
    assert "paused section_write node" in (by_action["resume_paused_section"].refusal_reason or "")

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == ["initialize_section_workflow"]


def test_list_execution_options_prefers_freeze_after_init_before_write_pause(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["initialize_section_workflow"].allowed is False
    assert by_action["create_branch"].allowed is True
    assert by_action["create_assembly_branch"].allowed is False
    assert by_action["finalize_chapter_from_locked_sections"].allowed is False
    assert by_action["freeze_section_from_phase03_artifact"].allowed is True
    assert by_action["resume_paused_section"].allowed is False

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == ["create_branch", "freeze_section_from_phase03_artifact"]


def test_list_execution_options_prefers_resume_for_paused_writer_state(tmp_path: Path) -> None:
    _setup_paused_section(tmp_path)

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["initialize_section_workflow"].allowed is False
    assert by_action["create_branch"].allowed is True
    assert by_action["freeze_section_from_phase03_artifact"].allowed is False
    assert by_action["resume_paused_section"].allowed is True
    assert by_action["resume_paused_section"].details["active_chapter"] == 1
    assert by_action["resume_paused_section"].details["active_section"] == 1

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == ["create_branch", "resume_paused_section"]


def test_list_execution_options_for_active_derived_branch_prefers_discard(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="rerun-sec1",
    )

    selector = ScopeSelector(book_id="my_book", branch_id="rerun-sec1", chapter=1, section=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["discard_branch"].allowed is True
    assert by_action["promote_branch_to_main"].allowed is False

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == ["discard_branch"]


def test_list_execution_options_for_promotion_ready_branch_includes_promote(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="rerun-sec1",
    )
    rerun_freeze_section_on_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
    )

    selector = ScopeSelector(book_id="my_book", branch_id="rerun-sec1", chapter=1, section=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["discard_branch"].allowed is True
    assert by_action["promote_branch_to_main"].allowed is True
    assert by_action["promote_branch_to_main"].details["lifecycle_state"] == "promote_ready"

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == ["discard_branch", "promote_branch_to_main"]


def test_list_execution_options_for_active_assembly_branch_includes_validation(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-b",
        fork_group_id="fg-1",
    )
    assembly = create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1)

    selector = ScopeSelector(book_id="my_book", branch_id=assembly.branch_id, chapter=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["discard_branch"].allowed is True
    assert by_action["record_assembly_validation"].allowed is True
    assert by_action["promote_branch_to_main"].allowed is False
    assert by_action["record_assembly_validation"].details["merge_operation"] == "assembly"

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == ["discard_branch", "record_assembly_validation"]


def test_list_execution_options_for_main_scope_with_fork_group_includes_assembly_creation(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-b",
        fork_group_id="fg-1",
    )

    selector = ScopeSelector(book_id="my_book", branch_id="main", fork_group_id="fg-1", chapter=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["create_assembly_branch"].allowed is True
    assert by_action["create_assembly_branch"].details["fork_group_id"] == "fg-1"
    assert by_action["create_assembly_branch"].details["sibling_count"] == 2

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "create_assembly_branch",
    ]


def test_list_execution_options_for_locked_chapter_includes_finalize(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    registry_path = book_root / "outline" / "snapshot_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["chapters"][0]["chapter_status"] = "finalized"
    registry["chapters"][0]["sections"][0]["status"] = "locked"
    registry["chapters"][0]["sections"][0]["scene_ref_start"] = "1:1"
    registry["chapters"][0]["sections"][0]["scene_ref_end"] = "1:1"
    registry_path.write_text(json.dumps(registry, ensure_ascii=True, indent=2), encoding="utf-8")

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["finalize_chapter_from_locked_sections"].allowed is True
    assert by_action["finalize_chapter_from_locked_sections"].details["chapter_id"] == 1
    assert by_action["finalize_chapter_from_locked_sections"].details["locked_sections"] == 1
    assert by_action["finalize_chapter_from_locked_sections"].details["chapter_status"] == "finalized"

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "finalize_chapter_from_locked_sections",
    ]


def test_list_execution_options_for_frozen_section_with_written_artifacts_includes_lock(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _write_scene_artifacts(book_root, 1, 1, text="Rhea crossed the threshold.")

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["lock_section_from_written_state"].allowed is True
    assert by_action["write_frozen_section"].allowed is False
    assert by_action["lock_section_from_written_state"].details["chapter_id"] == 1
    assert by_action["lock_section_from_written_state"].details["section_id"] == 1
    assert by_action["lock_section_from_written_state"].details["scene_ref_start"] == "1:1"
    assert by_action["lock_section_from_written_state"].details["scene_ref_end"] == "1:1"
    assert by_action["finalize_chapter_from_locked_sections"].allowed is False

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "lock_section_from_written_state",
    ]


def test_list_execution_options_for_active_frozen_section_includes_write(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["write_frozen_section"].allowed is True
    assert by_action["write_frozen_section"].details["chapter_id"] == 1
    assert by_action["write_frozen_section"].details["section_id"] == 1
    assert by_action["write_frozen_section"].details["scene_ref_start"] == "1:1"
    assert by_action["write_frozen_section"].details["scene_ref_end"] == "1:1"
    assert by_action["lock_section_from_written_state"].allowed is False

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
    ]


def test_list_execution_options_for_active_scene_includes_write_scene_prose(tmp_path: Path) -> None:
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

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["plan_scene"].allowed is False
    assert by_action["write_scene_prose"].allowed is True
    assert by_action["write_scene_prose"].mutates_canonical_state is False
    assert by_action["write_scene_prose"].requires_expected_node is True
    assert by_action["write_scene_prose"].details["scene_status"] == "continuity_ready"
    assert by_action["write_scene_prose"].details["recommended_next_action"] == "write_scene_prose"
    assert by_action["write_scene_prose"].details["available_inputs"] == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "style_anchor",
    ]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "write_scene_prose",
    ]


def test_list_execution_options_for_prose_generated_scene_includes_state_repair(tmp_path: Path) -> None:
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

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["state_repair_scene_patch"].allowed is True
    assert by_action["state_repair_scene_patch"].mutates_canonical_state is False
    assert by_action["state_repair_scene_patch"].requires_expected_node is True
    assert by_action["state_repair_scene_patch"].details["scene_status"] == "prose_generated"
    assert by_action["state_repair_scene_patch"].details["recommended_next_action"] == "state_repair_scene_patch"
    assert by_action["state_repair_scene_patch"].details["available_inputs"] == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "write_prose",
        "write_patch",
    ]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "state_repair_scene_patch",
    ]


def test_list_execution_options_for_state_repaired_scene_includes_lint(tmp_path: Path) -> None:
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

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["lint_scene_prose"].allowed is True
    assert by_action["lint_scene_prose"].mutates_canonical_state is False
    assert by_action["lint_scene_prose"].requires_expected_node is True
    assert by_action["lint_scene_prose"].details["scene_status"] == "state_repaired"
    assert by_action["lint_scene_prose"].details["recommended_next_action"] == "lint_scene_prose"
    assert by_action["lint_scene_prose"].details["available_inputs"] == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "write_prose",
        "state_repair_patch",
    ]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "lint_scene_prose",
    ]


def test_list_execution_options_for_passing_lint_scene_includes_commit(tmp_path: Path) -> None:
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

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["apply_scene_commit"].allowed is True
    assert by_action["apply_scene_commit"].mutates_canonical_state is True
    assert by_action["apply_scene_commit"].requires_expected_node is True
    assert by_action["apply_scene_commit"].details["scene_status"] == "linted"
    assert by_action["apply_scene_commit"].details["recommended_next_action"] == "apply_scene_commit"
    assert by_action["apply_scene_commit"].details["available_inputs"] == [
        "scene_card",
        "write_prose",
        "state_repair_patch",
        "passing_lint_report",
    ]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "apply_scene_commit",
    ]


def test_list_execution_options_for_failing_lint_scene_includes_repair(tmp_path: Path) -> None:
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

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["repair_scene_prose"].allowed is True
    assert by_action["repair_scene_prose"].mutates_canonical_state is False
    assert by_action["repair_scene_prose"].requires_expected_node is True
    assert by_action["repair_scene_prose"].details["scene_status"] == "lint_failed"
    assert by_action["repair_scene_prose"].details["recommended_next_action"] == "repair_scene_prose"
    assert by_action["repair_scene_prose"].details["available_inputs"] == [
        "scene_card",
        "write_prose",
        "repairable_lint_report",
    ]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "repair_scene_prose",
    ]


def test_list_execution_options_reopens_state_repair_after_repair_outputs(tmp_path: Path) -> None:
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
    _record_write_pair(book_root, prose="Original draft prose.")
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
    _record_repair_pair(book_root, prose="Repaired draft prose.")

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["state_repair_scene_patch"].allowed is True
    assert by_action["state_repair_scene_patch"].details["scene_status"] == "repair_generated"
    assert by_action["state_repair_scene_patch"].details["recommended_next_action"] == "state_repair_scene_patch"
    assert by_action["state_repair_scene_patch"].details["available_inputs"] == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "repair_prose",
        "repair_patch",
    ]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "state_repair_scene_patch",
    ]


def test_list_execution_options_for_unstarted_scene_includes_plan_scene(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["plan_scene"].allowed is True
    assert by_action["plan_scene"].mutates_canonical_state is False
    assert by_action["plan_scene"].requires_expected_node is True
    assert by_action["plan_scene"].details["scene_status"] == "unstarted"
    assert by_action["plan_scene"].details["recommended_next_action"] == "plan_scene"

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "plan_scene",
    ]


def test_list_execution_options_for_planned_scene_includes_preflight_scene_state(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    _record_artifact(book_root, 1, 1, "plan", "scene_card", _scene_card(), artifact_key="scene_card")

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["plan_scene"].allowed is False
    assert by_action["preflight_scene_state"].allowed is True
    assert by_action["preflight_scene_state"].mutates_canonical_state is False
    assert by_action["preflight_scene_state"].requires_expected_node is True
    assert by_action["preflight_scene_state"].details["scene_status"] == "planned"
    assert by_action["preflight_scene_state"].details["recommended_next_action"] == "preflight_scene_state"
    assert by_action["preflight_scene_state"].details["available_inputs"] == ["scene_card", "state_base"]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "preflight_scene_state",
    ]


def test_list_execution_options_for_preflighted_scene_includes_generate_continuity_pack(tmp_path: Path) -> None:
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

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)

    by_action = {option.action: option for option in options}
    assert by_action["generate_continuity_pack"].allowed is True
    assert by_action["generate_continuity_pack"].mutates_canonical_state is False
    assert by_action["generate_continuity_pack"].requires_expected_node is True
    assert by_action["generate_continuity_pack"].details["scene_status"] == "preflighted"
    assert by_action["generate_continuity_pack"].details["recommended_next_action"] == "generate_continuity_pack"
    assert by_action["generate_continuity_pack"].details["available_inputs"] == ["scene_card", "preflight_patch"]

    legal = legal_next_actions(tmp_path, selector, prefer_emitted=False)
    assert [option.action for option in legal] == [
        "create_branch",
        "write_frozen_section",
        "generate_continuity_pack",
    ]


def test_cli_parser_accepts_workflow_legal_actions_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "legal-actions",
            "--book",
            "my_book",
            "--branch-id",
            "rerun-sec1",
            "--fork-group-id",
            "fg-1",
            "--chapter",
            "1",
            "--section",
            "1",
            "--scene",
            "2",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "legal-actions"
    assert args.book == "my_book"
    assert args.branch_id == "rerun-sec1"
    assert args.fork_group_id == "fg-1"
    assert args.chapter == 1
    assert args.section == 1
    assert args.scene == 2


def test_cli_parser_accepts_workflow_scene_readiness_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "scene-readiness",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "scene-readiness"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_plan_scene_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "plan-scene",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "plan-scene"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_preflight_scene_state_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "preflight-scene-state",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "preflight-scene-state"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_generate_continuity_pack_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "generate-continuity-pack",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "generate-continuity-pack"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_state_repair_scene_patch_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "state-repair-scene-patch",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "state-repair-scene-patch"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_lint_scene_prose_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "lint-scene-prose",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "lint-scene-prose"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_repair_scene_prose_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "repair-scene-prose",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "repair-scene-prose"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_apply_scene_commit_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "apply-scene-commit",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "apply-scene-commit"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1


def test_cli_parser_accepts_workflow_write_section_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "write-section",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--section",
            "1",
            "--ack-outline-attention-items",
            "--force-outline-gate-bypass",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "write-section"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.section == 1
    assert args.ack_outline_attention_items is True
    assert args.force_outline_gate_bypass is True


def test_cli_parser_accepts_workflow_write_scene_prose_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "write-scene-prose",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--scene",
            "2",
            "--section",
            "1",
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "write-scene-prose"
    assert args.book == "my_book"
    assert args.chapter == 1
    assert args.scene == 2
    assert args.section == 1
