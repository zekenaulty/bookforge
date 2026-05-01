from __future__ import annotations

import json
from pathlib import Path

from bookforge.branching import create_branch
from bookforge.contracts import ScopeSelector
from bookforge.cli import build_parser
from bookforge.query import get_next_writing_target, get_writing_gate_status
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


def _setup_branch_two_scenes(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, scene_count=2)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="author-branch",
    )
    branch_root = supervision_paths.branch_snapshot_root(book_root, "author-branch")
    _write_committed_scene(branch_root, 1, 1)
    return branch_root


def _write_committed_scene(book_root: Path, chapter_id: int, scene_id: int) -> None:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / f"scene_{scene_id:03d}.md").write_text("Committed scene prose.", encoding="utf-8")
    (chapter_dir / f"scene_{scene_id:03d}.meta.json").write_text(
        json.dumps({"scene_id": scene_id}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _gate_by_key(status, key: str):
    return {gate.gate_key: gate for gate in status.gates}[key]


def test_next_writing_target_reports_ready_current_scene(tmp_path: Path) -> None:
    _setup_frozen(tmp_path)

    target = get_next_writing_target(tmp_path, "my_book", chapter_id=1, section_id=1, scene_id=1, prefer_emitted=False)

    assert target.status == "ready"
    assert target.can_continue is True
    assert target.book_complete is False
    assert target.recommended_action == "continue_scene"
    assert target.current_scene == {
        "chapter": 1,
        "section": 1,
        "scene": 1,
        "section_status": "frozen",
        "section_title": "Arrival",
        "scene_status": "unstarted",
        "recommended_next_action": "plan_scene",
    }


def test_next_writing_target_blocks_until_section_is_frozen(tmp_path: Path) -> None:
    _setup_initialized(tmp_path)

    target = get_next_writing_target(tmp_path, "my_book", prefer_emitted=False)

    assert target.status == "blocked"
    assert target.can_continue is False
    assert target.recommended_action == "freeze_section_from_phase03_artifact"
    assert target.next_section is not None
    assert target.next_section["chapter"] == 1
    assert target.next_section["section"] == 1
    assert target.blocked_reason == "Next section must be frozen before scene writing can continue."


def test_next_writing_target_stops_at_section_lock_gate_after_terminal_scene_commit(tmp_path: Path) -> None:
    book_root = _setup_frozen(tmp_path)
    _write_committed_scene(book_root, 1, 1)

    target = get_next_writing_target(tmp_path, "my_book", chapter_id=1, section_id=1, scene_id=1, prefer_emitted=False)

    assert target.status == "blocked"
    assert target.can_continue is False
    assert target.recommended_action == "lock_section_from_written_state"
    assert target.current_scene is not None
    assert target.current_scene["scene_status"] == "committed"
    assert target.blocked_reason == "Current section has no remaining uncommitted scene target; lock the section before continuing."


def test_next_writing_target_advances_to_next_scene_on_branch_after_commit(tmp_path: Path) -> None:
    _setup_branch_two_scenes(tmp_path)

    target = get_next_writing_target(
        tmp_path,
        "my_book",
        branch_id="author-branch",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        prefer_emitted=False,
    )

    assert target.status == "ready"
    assert target.can_continue is True
    assert target.recommended_action == "continue_scene"
    assert target.selector.branch_id == "author-branch"
    assert target.selector.scene == 2
    assert target.current_scene is not None
    assert target.current_scene["scene_status"] == "committed"
    assert target.next_scene == {
        "chapter": 1,
        "section": 1,
        "scene": 2,
        "section_status": "frozen",
        "section_title": "Arrival",
    }


def test_writing_gate_status_reports_scene_continue_gate(tmp_path: Path) -> None:
    _setup_frozen(tmp_path)

    status = get_writing_gate_status(tmp_path, "my_book", chapter_id=1, section_id=1, scene_id=1, prefer_emitted=False)
    scene_gate = _gate_by_key(status, "scene_continue")
    section_gate = _gate_by_key(status, "section_lock")

    assert status.can_continue is True
    assert status.recommended_next_action == "continue_scene"
    assert scene_gate.ready is True
    assert scene_gate.action == "continue_scene"
    assert section_gate.ready is False
    assert section_gate.blocked_reason == "Section still has uncommitted scene artifacts."


def test_writing_gate_status_reports_section_lock_ready(tmp_path: Path) -> None:
    book_root = _setup_frozen(tmp_path)
    _write_committed_scene(book_root, 1, 1)

    status = get_writing_gate_status(tmp_path, "my_book", chapter_id=1, section_id=1, scene_id=1, prefer_emitted=False)
    section_gate = _gate_by_key(status, "section_lock")
    book_gate = _gate_by_key(status, "book_continue")

    assert status.can_continue is True
    assert status.recommended_next_action == "lock_section_from_written_state"
    assert section_gate.status == "ready"
    assert section_gate.ready is True
    assert section_gate.action == "lock_section_from_written_state"
    assert book_gate.action == "lock_section_from_written_state"


def test_writing_gate_status_reports_book_complete_but_export_gap(tmp_path: Path) -> None:
    book_root = _setup_initialized(tmp_path)
    registry_path = book_root / "outline" / "snapshot_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["chapters"][0]["chapter_status"] = "finalized"
    registry["chapters"][0]["sections"][0]["status"] = "locked"
    registry_path.write_text(json.dumps(registry, ensure_ascii=True, indent=2), encoding="utf-8")

    status = get_writing_gate_status(tmp_path, "my_book", chapter_id=1, section_id=1, prefer_emitted=False)
    book_gate = _gate_by_key(status, "book_continue")
    export_gate = _gate_by_key(status, "manuscript_export")

    assert status.book_complete is True
    assert status.can_continue is False
    assert book_gate.status == "complete"
    assert export_gate.status == "blocked"
    assert export_gate.blocked_reason == "Manuscript export and quality gates are not implemented yet."


def test_cli_parser_accepts_workflow_next_writing_target_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "next-writing-target",
            "--book",
            "my_book",
            "--branch-id",
            "draft-1",
            "--chapter",
            "1",
            "--section",
            "1",
            "--scene",
            "1",
            "--json",
        ]
    )

    assert args.func.__name__ == "_workflow_next_writing_target"
    assert args.book == "my_book"
    assert args.branch_id == "draft-1"
    assert args.chapter == 1
    assert args.section == 1
    assert args.scene == 1
    assert args.json is True


def test_cli_parser_accepts_workflow_writing_gates_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "writing-gates",
            "--book",
            "my_book",
            "--branch-id",
            "draft-1",
            "--chapter",
            "1",
            "--section",
            "1",
            "--scene",
            "1",
            "--json",
        ]
    )

    assert args.func.__name__ == "_workflow_writing_gates"
    assert args.book == "my_book"
    assert args.branch_id == "draft-1"
    assert args.chapter == 1
    assert args.section == 1
    assert args.scene == 1
    assert args.json is True
