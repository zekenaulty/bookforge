from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from bookforge.runner import run_loop
from bookforge.workspace import init_book_workspace


def _outline_payload() -> dict:
    return {
        "schema_version": "1.1",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Start the story.",
                "chapter_role": "hook",
                "stakes_shift": "The pressure appears.",
                "bridge": {"from_prev": "", "to_next": "The next problem arrives."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Get inside.",
                        "end_condition": "The door opens.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "The protagonist reaches the door.",
                                "type": "setup",
                                "outcome": "The protagonist is ready to enter.",
                                "characters": ["CHAR_protagonist"],
                                "threads": ["THREAD_pressure"],
                                "location_start_label": "Front Gate",
                                "location_end_label": "Front Gate",
                                "location_start": "Front Gate",
                                "location_end": "Front Gate",
                                "location_start_id": "LOC_FRONT_GATE_ABC123",
                                "location_end_id": "LOC_FRONT_GATE_ABC123",
                                "handoff_mode": "terminal",
                                "constraint_state": "free",
                                "transition_in_text": "At the front gate, the action begins immediately.",
                                "transition_in_anchors": ["front gate", "storm", "steel lock"],
                                "seam_score": 10,
                                "seam_resolution": "inline_bridge",
                                "end_condition_echo": "The door opens.",
                            }
                        ],
                    }
                ],
            }
        ],
        "characters": [
            {
                "character_id": "CHAR_protagonist",
                "name": "Protagonist",
                "pronouns": "they/them",
                "role": "lead",
                "intro": {"chapter": 1, "scene": 1},
            }
        ],
        "threads": [{"thread_id": "THREAD_pressure", "label": "Pressure", "status": "open"}],
    }


def _scene_card(chapter: int, scene: int) -> dict:
    return {
        "schema_version": "1.1",
        "scene_id": f"SC_{chapter:03d}_{scene:03d}",
        "chapter": chapter,
        "scene": scene,
        "section_id": 1,
        "scene_target": "The protagonist reaches the door.",
        "goal": "Get inside.",
        "conflict": "The lock resists.",
        "required_callbacks": [],
        "constraints": [],
        "end_condition": "The door opens.",
        "location_start_id": "LOC_FRONT_GATE_ABC123",
        "location_end_id": "LOC_FRONT_GATE_ABC123",
        "location_start": "Front Gate",
        "location_end": "Front Gate",
        "handoff_mode": "terminal",
        "constraint_state": "free",
        "transition_in_text": "At the front gate, the action begins immediately.",
        "transition_in_anchors": ["front gate", "storm", "steel lock"],
        "seam_score": 10,
        "seam_resolution": "inline_bridge",
        "timeline_scope": "present",
        "ontological_scope": "real",
        "required_in_custody": [],
        "required_scene_accessible": [],
        "required_visible_on_page": [],
        "forbidden_visible": [],
        "device_presence": [],
        "ui_allowed": False,
        "ui_mechanics_expected": [],
        "cast_present_ids": ["CHAR_protagonist"],
        "cast_present": ["Protagonist"],
    }


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
    outline_root = book_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)
    (outline_root / "outline.json").write_text(
        json.dumps(_outline_payload(), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    run_id = "test_run"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "book_id": "my_book",
        "run_id": run_id,
        "timestamp": "2026-04-21T00:00:00Z",
        "overall_status": "SUCCESS",
        "requires_user_attention": False,
        "phase_failed": "",
        "reason_codes": [],
        "attempt_usage": {},
        "attention_items": [],
    }
    (run_dir / "outline_pipeline_report.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (outline_root / "outline_pipeline_report_latest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "updated_at": "2026-04-21T00:00:00Z",
                "path": f"pipeline_runs/{run_id}/outline_pipeline_report.json",
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return book_root


def test_run_loop_routes_scene_through_extracted_scene_actions(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    action_calls: list[str] = []

    def _fake_scene_action(
        workspace,
        book_id,
        action,
        *,
        chapter_id,
        scene_id,
        section_id=None,
        branch_id="main",
        extra_details=None,
    ):
        action_calls.append(action)
        if action == "plan_scene":
            payload = _scene_card(chapter_id, scene_id)
            path = book_root / "draft" / "scenes" / "planned_001.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
            return SimpleNamespace(
                action=action,
                status="success",
                message="planned",
                artifact_paths={"scene_card": path.relative_to(book_root).as_posix()},
                details={},
            )
        if action == "lint_scene_prose":
            report_path = book_root / "draft" / "context" / "lint_scene_001.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps({"schema_version": "1.0", "status": "pass", "issues": []}, ensure_ascii=True, indent=2),
                encoding="utf-8",
            )
            return SimpleNamespace(
                action=action,
                status="success",
                message="linted",
                artifact_paths={"lint_report": report_path.relative_to(book_root).as_posix()},
                details={},
            )
        if action == "apply_scene_commit":
            chapter_dir = book_root / "draft" / "chapters" / "ch_001"
            chapter_dir.mkdir(parents=True, exist_ok=True)
            (chapter_dir / "scene_001.md").write_text("A clean scene draft.", encoding="utf-8")
            (chapter_dir / "scene_001.meta.json").write_text(
                json.dumps({"chapter": 1, "scene": 1, "status": "committed"}, ensure_ascii=True, indent=2),
                encoding="utf-8",
            )
            state_path = book_root / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["cursor"] = {"chapter": 2, "scene": 1}
            state["status"] = "COMPLETE"
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        return SimpleNamespace(
            action=action,
            status="success",
            message="ok",
            artifact_paths={},
            details={},
        )

    monkeypatch.setattr("bookforge.runner.load_config", lambda: {})
    monkeypatch.setattr("bookforge.runner.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.runner.resolve_model", lambda phase, config: "dummy")
    monkeypatch.setattr("bookforge.runner.characters_ready", lambda book_root_arg: True)
    monkeypatch.setattr("bookforge.runner._ensure_style_anchor", lambda *args, **kwargs: "Style anchor.")
    monkeypatch.setattr("bookforge.runner.refresh_appearance_projections", lambda *args, **kwargs: [])
    monkeypatch.setattr("bookforge.runner._dispatch_scene_phase_action", _fake_scene_action)

    run_loop(workspace=tmp_path, book_id="my_book", steps=1)

    assert action_calls == [
        "plan_scene",
        "preflight_scene_state",
        "generate_continuity_pack",
        "write_scene_prose",
        "state_repair_scene_patch",
        "lint_scene_prose",
        "apply_scene_commit",
    ]

    meta_path = book_root / "draft" / "chapters" / "ch_001" / "scene_001.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["chapter"] == 1
    assert meta["scene"] == 1
