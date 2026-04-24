from __future__ import annotations

import json
from pathlib import Path

from bookforge.memory.continuity import save_style_anchor, style_anchor_path
from bookforge.pipeline.phase_history import _record_phase_success, _write_phase_artifact
from bookforge.query import get_scene_phase_readiness
from bookforge.section_workflow import freeze_section_from_phase03_artifact, initialize_section_workflow
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


def _record_artifact(book_root: Path, chapter: int, scene: int, phase: str, name: str, payload, *, as_json: bool = True, artifact_key: str) -> None:
    path = _write_phase_artifact(book_root, chapter, scene, name, payload, as_json=as_json)
    _record_phase_success(
        book_root,
        chapter,
        scene,
        phase,
        {artifact_key: path.relative_to(book_root).as_posix()},
    )


def _record_write_pair(book_root: Path, prose: str = "Draft scene prose.", patch: dict | None = None) -> None:
    write_patch = patch or {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []}
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


def _record_repair_pair(book_root: Path, prose: str = "Repaired scene prose.", patch: dict | None = None) -> None:
    repair_patch = patch or {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []}
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


def _setup_frozen_scene(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    freeze_section_from_phase03_artifact(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)
    return book_root


def test_scene_phase_readiness_recommends_plan_for_active_cursor_scene(tmp_path: Path) -> None:
    _setup_frozen_scene(tmp_path)

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "unstarted"
    assert readiness.recommended_next_action == "plan_scene"
    assert by_action["plan_scene"].ready is True
    assert by_action["write_scene_prose"].ready is False
    assert by_action["write_scene_prose"].missing_prerequisites == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "style_anchor",
    ]


def test_scene_phase_readiness_recommends_write_when_prereqs_exist(tmp_path: Path) -> None:
    book_root = _setup_frozen_scene(tmp_path)
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

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "continuity_ready"
    assert readiness.recommended_next_action == "write_scene_prose"
    assert by_action["write_scene_prose"].ready is True
    assert by_action["write_scene_prose"].recommended is True
    assert by_action["write_scene_prose"].available_inputs == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "style_anchor",
    ]


def test_scene_phase_readiness_surfaces_provisional_write_outputs(tmp_path: Path) -> None:
    book_root = _setup_frozen_scene(tmp_path)
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
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Draft scene prose.", as_json=False)
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

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "prose_generated"
    assert readiness.recommended_next_action == "state_repair_scene_patch"
    assert by_action["write_scene_prose"].ready is False
    assert by_action["state_repair_scene_patch"].ready is True
    assert by_action["state_repair_scene_patch"].recommended is True
    assert by_action["state_repair_scene_patch"].available_inputs == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "write_prose",
        "write_patch",
    ]
    assert [item.artifact_status for item in by_action["write_scene_prose"].existing_outputs] == [
        "provisional",
        "provisional",
    ]


def test_scene_phase_readiness_surfaces_state_repair_outputs(tmp_path: Path) -> None:
    book_root = _setup_frozen_scene(tmp_path)
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
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Draft scene prose.", as_json=False)
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

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "state_repaired"
    assert readiness.recommended_next_action == "lint_scene_prose"
    assert by_action["state_repair_scene_patch"].ready is False
    assert by_action["lint_scene_prose"].ready is True
    assert by_action["lint_scene_prose"].recommended is True
    assert [item.artifact_status for item in by_action["state_repair_scene_patch"].existing_outputs] == [
        "provisional",
    ]


def test_scene_phase_readiness_surfaces_lint_outputs(tmp_path: Path) -> None:
    book_root = _setup_frozen_scene(tmp_path)
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
    prose_path = _write_phase_artifact(book_root, 1, 1, "write_prose", "Draft scene prose.", as_json=False)
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

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "linted"
    assert readiness.recommended_next_action == "apply_scene_commit"
    assert by_action["lint_scene_prose"].ready is False
    assert by_action["repair_scene_prose"].ready is False
    assert by_action["apply_scene_commit"].ready is True
    assert by_action["apply_scene_commit"].recommended is True
    assert by_action["apply_scene_commit"].available_inputs == [
        "scene_card",
        "write_prose",
        "state_repair_patch",
        "passing_lint_report",
    ]
    assert [item.artifact_status for item in by_action["lint_scene_prose"].existing_outputs] == [
        "provisional",
    ]


def test_scene_phase_readiness_surfaces_failing_lint_as_repair_ready(tmp_path: Path) -> None:
    book_root = _setup_frozen_scene(tmp_path)
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

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "lint_failed"
    assert readiness.recommended_next_action == "repair_scene_prose"
    assert by_action["lint_scene_prose"].ready is False
    assert by_action["repair_scene_prose"].ready is True
    assert by_action["repair_scene_prose"].recommended is True
    assert by_action["repair_scene_prose"].available_inputs == [
        "scene_card",
        "write_prose",
        "repairable_lint_report",
    ]


def test_scene_phase_readiness_reopens_state_repair_after_new_repair_outputs(tmp_path: Path) -> None:
    book_root = _setup_frozen_scene(tmp_path)
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

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "repair_generated"
    assert readiness.recommended_next_action == "state_repair_scene_patch"
    assert by_action["state_repair_scene_patch"].ready is True
    assert by_action["state_repair_scene_patch"].recommended is True
    assert by_action["lint_scene_prose"].ready is False
    assert by_action["repair_scene_prose"].ready is False
    assert by_action["state_repair_scene_patch"].available_inputs == [
        "scene_card",
        "preflight_patch",
        "continuity_pack",
        "repair_prose",
        "repair_patch",
    ]


def test_scene_phase_readiness_reopens_repair_after_post_repair_lint_fail(tmp_path: Path) -> None:
    book_root = _setup_frozen_scene(tmp_path)
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
    _record_artifact(
        book_root,
        1,
        1,
        "state_repair",
        "state_repair_patch",
        {"summary_update": {"last_scene": ["repaired state"]}, "character_updates": [], "character_continuity_system_updates": []},
        artifact_key="patch",
    )
    _record_artifact(
        book_root,
        1,
        1,
        "lint",
        "lint_report",
        {"schema_version": "1.0", "status": "fail", "issues": [{"code": "still_overlap"}], "mode": "llm"},
        artifact_key="report",
    )

    readiness = get_scene_phase_readiness(
        tmp_path,
        "my_book",
        chapter_id=1,
        scene_id=1,
        section_id=1,
        prefer_emitted=False,
    )

    by_action = {item.action: item for item in readiness.actions}
    assert readiness.scene_status == "lint_failed"
    assert readiness.recommended_next_action == "repair_scene_prose"
    assert by_action["repair_scene_prose"].ready is True
    assert by_action["repair_scene_prose"].available_inputs == [
        "scene_card",
        "repair_prose",
        "repairable_lint_report",
    ]
