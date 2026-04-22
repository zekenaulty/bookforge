from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.branching import create_assembly_branch, create_branch, rerun_freeze_section_on_branch
from bookforge.llm.errors import LLMRequestError, QuotaViolation
from bookforge.pipeline.run_logging import _write_latest_run_pointer
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
        ]
    )

    assert args.command == "workflow"
    assert args.workflow_command == "legal-actions"
    assert args.book == "my_book"
    assert args.branch_id == "rerun-sec1"
    assert args.fork_group_id == "fg-1"
    assert args.chapter == 1
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
