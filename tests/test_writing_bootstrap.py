from __future__ import annotations

import json
from pathlib import Path

from bookforge.branching import create_branch
from bookforge.cli import build_parser
from bookforge.contracts import ScopeSelector, WritingBootstrapStatus
from bookforge.query import get_capability_projection, get_writing_bootstrap_status
from bookforge.section_workflow import freeze_section_from_phase03_artifact, initialize_section_workflow
from bookforge.workspace import init_book_workspace


def _init_book(tmp_path: Path, *, with_intent: bool = True) -> Path:
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
    if with_intent:
        (book_root / "book_intent.json").write_text(
            json.dumps(
                {
                    "schema_version": "book_intent_v1",
                    "intent_id": "intent_001",
                    "book_id": "my_book",
                    "status": "created",
                    "title": "Untitled",
                    "author_ref": "eldrik-vale/v1",
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
    return book_root


def _write_run_artifacts(book_root: Path, run_id: str = "run_001", scene_count: int = 1) -> None:
    scenes = [
        {
            "scene_id": scene_id,
            "summary": "Rhea reaches the door." if scene_id == 1 else "Rhea steps through the door.",
            "type": "setup",
            "outcome": "She is ready to enter." if scene_id == 1 else "She enters.",
            "characters": ["CHAR_protagonist"],
            "threads": [],
            "handoff_mode": "terminal" if scene_id == scene_count else "handoff",
            "transition_out_anchors": ["door"],
        }
        for scene_id in range(1, int(scene_count) + 1)
    ]
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
                        "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": int(scene_count)},
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
                                "target_scene_count": int(scene_count),
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
                                "scenes": scenes,
                            }
                        ],
                    }
                ],
                "characters": [{"character_id": "CHAR_protagonist", "name": "Rhea", "role": "protagonist"}],
                "threads": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def _setup_initialized(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    return book_root


def _setup_frozen(tmp_path: Path) -> Path:
    book_root = _setup_initialized(tmp_path)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    return book_root


def _stage_by_key(status: WritingBootstrapStatus, key: str):
    return {stage.stage_key: stage for stage in status.stages}[key]


def test_writing_bootstrap_recommends_provider_starter_outline_after_book_creation(tmp_path: Path) -> None:
    _init_book(tmp_path)

    status = get_writing_bootstrap_status(tmp_path, "my_book", prefer_emitted=False)

    assert status.status == "setup_required"
    assert status.can_start_writing is False
    assert status.recommended_action == "draft_starter_outline_from_intent"
    assert status.required_approval_class == "provider"
    stage = _stage_by_key(status, "starter_outline")
    assert stage.ready is True
    assert stage.action == "draft_starter_outline_from_intent"
    assert stage.details["details"]["provider_used"] is True
    assert stage.details["details"]["deep_outline_pipeline"] is False


def test_writing_bootstrap_recommends_workflow_init_after_outline_exists(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    status = get_writing_bootstrap_status(tmp_path, "my_book", prefer_emitted=False)

    assert status.status == "setup_required"
    assert status.recommended_action == "initialize_section_workflow"
    assert status.required_approval_class == "canonical"
    stage = _stage_by_key(status, "workflow_registry")
    assert stage.ready is True
    assert stage.action == "initialize_section_workflow"


def test_writing_bootstrap_recommends_freeze_after_workflow_init(tmp_path: Path) -> None:
    _setup_initialized(tmp_path)

    status = get_writing_bootstrap_status(tmp_path, "my_book", prefer_emitted=False)

    assert status.status == "setup_required"
    assert status.recommended_action == "freeze_section_from_phase03_artifact"
    assert status.target_selector["chapter"] == 1
    assert status.target_selector["section"] == 1
    stage = _stage_by_key(status, "section_materialization")
    assert stage.ready is True
    assert stage.action == "freeze_section_from_phase03_artifact"


def test_writing_bootstrap_recommends_branch_after_section_freeze(tmp_path: Path) -> None:
    _setup_frozen(tmp_path)

    status = get_writing_bootstrap_status(tmp_path, "my_book", prefer_emitted=False)

    assert status.status == "setup_required"
    assert status.recommended_action == "create_branch"
    assert status.required_approval_class == "branch"
    stage = _stage_by_key(status, "branch_workspace")
    assert stage.ready is True
    assert stage.action == "create_branch"


def test_writing_bootstrap_reports_ready_to_write_on_branch(tmp_path: Path) -> None:
    _setup_frozen(tmp_path)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="author-branch",
    )

    status = get_writing_bootstrap_status(
        tmp_path,
        "my_book",
        branch_id="author-branch",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        prefer_emitted=False,
    )

    assert status.status == "ready_to_write"
    assert status.can_start_writing is True
    assert status.recommended_action == "continue_scene"
    assert status.target_branch_id == "author-branch"
    assert status.target_selector["branch_id"] == "author-branch"
    stage = _stage_by_key(status, "scene_continue")
    assert stage.ready is True
    assert stage.action == "continue_scene"


def test_writing_bootstrap_projection_and_cli_parser() -> None:
    projection = get_capability_projection()
    by_id = {item.capability_id: item for item in projection.capabilities}
    assert "query.writing_bootstrap_status" in by_id
    assert by_id["query.writing_bootstrap_status"].process_area == "writing"

    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "writing-bootstrap",
            "--book",
            "my_book",
            "--branch-id",
            "author-branch",
            "--chapter",
            "1",
            "--section",
            "1",
            "--scene",
            "1",
            "--json",
        ]
    )

    assert args.func.__name__ == "_workflow_writing_bootstrap"
    assert args.book == "my_book"
    assert args.branch_id == "author-branch"
    assert args.chapter == 1
    assert args.section == 1
    assert args.scene == 1
    assert args.json is True
