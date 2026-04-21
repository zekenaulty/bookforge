from __future__ import annotations

import json
from pathlib import Path

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


def test_run_loop_replans_exact_scene_when_loaded_scene_card_mismatches(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    planned_calls: list[tuple[int | None, int | None]] = []
    executed_cards: list[tuple[int, int]] = []

    def _plan_scene(workspace, book_id, chapter=None, scene=None, client=None, model=None):
        planned_calls.append((chapter, scene))
        payload = _scene_card(chapter or 1, scene or 2)
        path = book_root / "draft" / "scenes" / f"planned_{len(planned_calls):03d}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return path

    def _write_scene(*args, **kwargs):
        scene_card = args[3]
        executed_cards.append((int(scene_card["chapter"]), int(scene_card["scene"])))
        patch = {
            "summary_update": {},
            "character_updates": [],
            "character_continuity_system_updates": [],
        }
        return "A clean scene draft.", patch

    monkeypatch.setattr("bookforge.runner.load_config", lambda: {})
    monkeypatch.setattr("bookforge.runner.get_llm_client", lambda config, phase=None: object())
    monkeypatch.setattr("bookforge.runner.resolve_model", lambda phase, config: "dummy")
    monkeypatch.setattr("bookforge.runner.characters_ready", lambda book_root_arg: True)
    monkeypatch.setattr("bookforge.runner._ensure_style_anchor", lambda *args, **kwargs: "Style anchor.")
    monkeypatch.setattr("bookforge.runner.plan_scene", _plan_scene)
    monkeypatch.setattr(
        "bookforge.runner._scene_state_preflight",
        lambda *args, **kwargs: {"summary_update": {}, "character_updates": [], "character_continuity_system_updates": []},
    )
    monkeypatch.setattr("bookforge.runner._generate_continuity_pack", lambda *args, **kwargs: {"ok": True})
    monkeypatch.setattr("bookforge.runner._write_scene", _write_scene)
    monkeypatch.setattr("bookforge.runner._state_repair", lambda *args, **kwargs: args[7])
    monkeypatch.setattr(
        "bookforge.runner._lint_scene",
        lambda *args, **kwargs: {"schema_version": "1.0", "status": "pass", "issues": []},
    )
    monkeypatch.setattr("bookforge.runner._load_character_states", lambda *args, **kwargs: [])
    monkeypatch.setattr("bookforge.runner._snapshot_character_states_before_preflight", lambda *args, **kwargs: [])
    monkeypatch.setattr("bookforge.runner.refresh_appearance_projections", lambda *args, **kwargs: [])
    monkeypatch.setattr("bookforge.runner._apply_state_patch", lambda state, patch, chapter_end=False: state)
    monkeypatch.setattr("bookforge.runner._apply_character_updates", lambda *args, **kwargs: None)
    monkeypatch.setattr("bookforge.runner._apply_character_stat_updates", lambda *args, **kwargs: None)
    monkeypatch.setattr("bookforge.runner._apply_durable_updates_or_pause", lambda *args, **kwargs: False)
    monkeypatch.setattr("bookforge.runner._update_bible", lambda *args, **kwargs: None)
    monkeypatch.setattr("bookforge.runner._rollup_chapter_summary", lambda *args, **kwargs: None)
    monkeypatch.setattr("bookforge.runner._compile_chapter_markdown", lambda *args, **kwargs: None)

    run_loop(workspace=tmp_path, book_id="my_book", steps=1)

    assert planned_calls == [(None, None), (1, 1)]
    assert executed_cards == [(1, 1)]

    meta_path = book_root / "draft" / "chapters" / "ch_001" / "scene_001.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["chapter"] == 1
    assert meta["scene"] == 1
