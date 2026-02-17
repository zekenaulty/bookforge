from pathlib import Path
import json
import shutil
import pytest

from bookforge.llm.errors import LLMRequestError
from bookforge.llm.types import LLMResponse
from bookforge.outline import (
    backup_outline_run,
    generate_outline,
    load_latest_outline_pipeline_report,
    restore_outline_state,
)
from bookforge.workspace import init_book_workspace


class DummyClient:
    def __init__(self, responses: list[str], *, provider: str = "dummy") -> None:
        self._responses = list(responses)
        self._index = 0
        self.messages_history = []
        self.calls = []
        self.provider = provider

    def chat(self, messages, model, temperature=0.7, max_tokens=1024, thinking_level=None):
        self.messages_history.append(messages)
        self.calls.append(
            {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "thinking_level": thinking_level,
            }
        )
        if self._responses:
            index = min(self._index, len(self._responses) - 1)
            text = self._responses[index]
            self._index += 1
        else:
            text = "{}"
        return LLMResponse(
            text=text,
            raw={"candidates": [{"finishReason": "STOP"}]},
            provider="dummy",
            model=model,
        )


class DummyClientWithPause(DummyClient):
    def __init__(self, responses: list[str], *, fail_call_number: int) -> None:
        super().__init__(responses)
        self._call_number = 0
        self._fail_call_number = fail_call_number

    def chat(self, messages, model, temperature=0.7, max_tokens=1024, thinking_level=None):
        self._call_number += 1
        if self._call_number == self._fail_call_number:
            raise LLMRequestError(
                status_code=429,
                message="rate limited",
                retry_after_seconds=1.0,
                quota_violations=[],
                raw_response={},
            )
        return super().chat(
            messages,
            model,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_level=thinking_level,
        )


def _base_outline() -> dict:
    return {
        "schema_version": "1.1",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Introduce pressure.",
                "chapter_role": "hook",
                "stakes_shift": "A threat enters view.",
                "bridge": {"from_prev": "", "to_next": "The city closes in."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Show first contact.",
                        "end_condition": "The threat is confirmed.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "The protagonist reaches the gate.",
                                "type": "setup",
                                "outcome": "The protagonist is flagged at the gate.",
                                "characters": ["CHAR_protagonist"],
                                "threads": ["THREAD_pressure"],
                                "location_start_label": "City Gate",
                                "location_end_label": "City Gate",
                                "location_start": "City Gate",
                                "location_end": "City Gate",
                                "handoff_mode": "direct_continuation",
                                "constraint_state": "free",
                                "transition_in_text": "At the city gate, patrol lanterns sweep the archway.",
                                "transition_in_anchors": ["city gate", "lantern light", "stone archway"],
                                "seam_score": 10,
                                "seam_resolution": "inline_bridge",
                                "end_condition_echo": "The threat is confirmed.",
                            }
                        ],
                    }
                ],
            },
            {
                "chapter_id": 2,
                "title": "Escalation",
                "goal": "Force movement.",
                "chapter_role": "pressure",
                "stakes_shift": "The city turns hostile.",
                "bridge": {"from_prev": "The city closes in.", "to_next": "Escape becomes mandatory."},
                "pacing": {"intensity": 4, "tempo": "rush", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Flight",
                        "intent": "Drive a forced exit.",
                        "end_condition": "The protagonist commits to flight.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "Pursuit starts in the market.",
                                "type": "escalation",
                                "outcome": "The protagonist commits to flight.",
                                "characters": ["CHAR_protagonist"],
                                "threads": ["THREAD_pressure"],
                                "location_start_label": "Market Square",
                                "location_end_label": "Market Square",
                                "location_start": "Market Square",
                                "location_end": "Market Square",
                                "handoff_mode": "direct_continuation",
                                "constraint_state": "pursued",
                                "transition_in_text": "In market square, stall awnings whip as guards push through the crowd.",
                                "transition_in_anchors": ["market square", "stall awnings", "guard shouts"],
                                "seam_score": 15,
                                "seam_resolution": "inline_bridge",
                                "end_condition_echo": "The protagonist commits to flight.",
                            }
                        ],
                    }
                ],
            },
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


def _phase_01() -> dict:
    return {
        "schema_version": "spine_v1",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Introduce pressure.",
                "chapter_role": "hook",
                "stakes_shift": "A threat enters view.",
                "bridge": {"from_prev": "", "to_next": "The city closes in."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
            },
            {
                "chapter_id": 2,
                "title": "Escalation",
                "goal": "Force movement.",
                "chapter_role": "pressure",
                "stakes_shift": "The city turns hostile.",
                "bridge": {"from_prev": "The city closes in.", "to_next": "Escape becomes mandatory."},
                "pacing": {"intensity": 4, "tempo": "rush", "expected_scene_count": 1},
            },
        ],
    }


def _phase_02() -> dict:
    return {
        "schema_version": "sections_v1",
        "chapters": [
            {
                "chapter_id": 1,
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Show first contact.",
                        "section_role": "setup",
                        "target_scene_count": 1,
                        "end_condition": "The threat is confirmed.",
                    }
                ],
            },
            {
                "chapter_id": 2,
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Flight",
                        "intent": "Drive a forced exit.",
                        "section_role": "escalation",
                        "target_scene_count": 1,
                        "end_condition": "The protagonist commits to flight.",
                    }
                ],
            },
        ],
    }


def _phase_04a() -> dict:
    return _phase_04a_for_chapter(1)


def _outline_for_chapter(chapter_id: int) -> dict:
    outline = _base_outline()
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    selected = [chapter for chapter in chapters if isinstance(chapter, dict) and int(chapter.get("chapter_id", 0) or 0) == int(chapter_id)]
    return {
        "schema_version": "1.1",
        "chapters": selected,
        "characters": outline.get("characters", []),
        "threads": outline.get("threads", []),
    }


def _phase_04a_for_chapter(chapter_id: int) -> dict:
    return {
        "schema_version": "transition_refine_v1",
        "outline": _outline_for_chapter(chapter_id),
        "phase_report": {
            "orphan_outcomes_before": 0,
            "orphan_outcomes_after": 0,
            "weak_handoffs_after": 0,
            "orphan_scene_refs_after": [],
            "weak_handoff_refs_after": [],
            "candidate_seams": [],
            "edits_applied": [],
        },
    }


def _phase_04b() -> dict:
    return _phase_04b_for_chapter(1)


def _phase_04b_for_chapter(chapter_id: int) -> dict:
    return {
        "schema_version": "transition_refine_v1",
        "outline": _outline_for_chapter(chapter_id),
        "phase_report": {
            "inserted_scene_refs": [],
            "resolved_candidates": [],
            "blocked_by_budget": [],
            "downgraded_resolution": [],
            "unresolved_required_insertions": [],
            "edits_applied": [],
        },
    }


def _phase_04a_for_chapter_with_candidates(
    chapter_id: int,
    candidate_seams: list[dict],
) -> dict:
    payload = _phase_04a_for_chapter(chapter_id)
    payload["phase_report"]["candidate_seams"] = candidate_seams
    return payload


def _phase_04b_for_chapter_with_report(
    chapter_id: int,
    *,
    resolved_candidates: list[dict] | None = None,
    inserted_scene_refs: list[str] | None = None,
) -> dict:
    payload = _phase_04b_for_chapter(chapter_id)
    payload["phase_report"]["resolved_candidates"] = resolved_candidates or []
    payload["phase_report"]["inserted_scene_refs"] = inserted_scene_refs or []
    return payload


def _phase_05() -> dict:
    return _phase_05_for_chapter(1)


def _phase_05_for_chapter(chapter_id: int) -> dict:
    return {
        "schema_version": "cast_refine_v1",
        "outline": _outline_for_chapter(chapter_id),
        "cast_report": {
            "core_character_ids": ["CHAR_protagonist"],
            "supporting_character_ids": [],
            "episodic_character_ids": [],
            "recurring_without_job_count": 0,
            "edits_applied": [],
        },
    }


def _phase_06_for_chapter(chapter_id: int) -> dict:
    return _outline_for_chapter(chapter_id)


def _pipeline_responses() -> list[str]:
    return [
        json.dumps(_phase_01()),
        json.dumps(_phase_02()),
        json.dumps(_base_outline()),
        json.dumps(_phase_04a_for_chapter(1)),
        json.dumps(_phase_04a_for_chapter(2)),
        json.dumps(_phase_04b_for_chapter(1)),
        json.dumps(_phase_04b_for_chapter(2)),
        json.dumps(_phase_05_for_chapter(1)),
        json.dumps(_phase_05_for_chapter(2)),
        json.dumps(_phase_06_for_chapter(1)),
        json.dumps(_phase_06_for_chapter(2)),
    ]


def _init_book(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 2},
        series_id=None,
    )


def _latest_run_dir(tmp_path: Path) -> Path:
    run_root = tmp_path / "books" / "my_book" / "outline" / "pipeline_runs"
    return sorted(run_root.iterdir())[-1]


def test_generate_outline_pipeline_writes_files(tmp_path: Path) -> None:
    _init_book(tmp_path)

    client = DummyClient(_pipeline_responses())
    outline_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        client=client,
        model="dummy",
    )

    assert outline_path.exists()
    assert (outline_path.parent / "chapters" / "ch_001.json").exists()
    assert (outline_path.parent / "chapters" / "ch_002.json").exists()
    assert (outline_path.parent / "pipeline_runs").exists()
    assert len(client.messages_history) == 11

    report_path, report = load_latest_outline_pipeline_report(workspace=tmp_path, book_id="my_book")
    assert report_path is not None
    assert report.get("overall_status") in {"SUCCESS", "SUCCESS_WITH_WARNINGS"}


def test_generate_outline_resume_reuses_successful_steps(tmp_path: Path) -> None:
    _init_book(tmp_path)

    first_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=first_client, model="dummy")
    assert len(first_client.messages_history) == 11

    resume_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", resume=True, client=resume_client, model="dummy")
    assert len(resume_client.messages_history) == 0


def test_generate_outline_phase_rerun_uses_previous_dependencies(tmp_path: Path) -> None:
    _init_book(tmp_path)

    baseline_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=baseline_client, model="dummy")

    rerun_client = DummyClient(
        [
            json.dumps(_phase_04a_for_chapter(1)),
            json.dumps(_phase_04a_for_chapter(2)),
            json.dumps(_phase_04b_for_chapter(1)),
            json.dumps(_phase_04b_for_chapter(2)),
        ]
    )
    handoff_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        rerun=True,
        from_phase="phase_04_transition_causality_refinement",
        to_phase="phase_04_transition_causality_refinement",
        client=rerun_client,
        model="dummy",
    )

    assert handoff_path.name in {"outline.json", "outline_transitions_refined_v1_1.json"}
    assert len(rerun_client.messages_history) == 4


def test_generate_outline_from_phase_without_dependencies_fails(tmp_path: Path) -> None:
    _init_book(tmp_path)

    client = DummyClient([json.dumps(_phase_04a_for_chapter(1)), json.dumps(_phase_04b_for_chapter(1))])
    with pytest.raises(FileNotFoundError):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            from_phase="phase_04_transition_causality_refinement",
            to_phase="phase_04_transition_causality_refinement",
            client=client,
            model="dummy",
        )


def test_generate_outline_phase4a_resume_restarts_at_failed_chapter(tmp_path: Path) -> None:
    _init_book(tmp_path)

    first_client = DummyClientWithPause(_pipeline_responses(), fail_call_number=5)
    with pytest.raises(RuntimeError):
        generate_outline(workspace=tmp_path, book_id="my_book", client=first_client, model="dummy")

    resume_client = DummyClient([json.dumps(_phase_04a_for_chapter(2))])
    handoff_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        resume=True,
        from_phase="phase_04a_transition_seam_analysis",
        to_phase="phase_04a_transition_seam_analysis",
        client=resume_client,
        model="dummy",
    )
    assert handoff_path.name in {"outline.json", "phase_04a_transition_seam_analysis_output.json"}
    assert len(resume_client.messages_history) == 1


def test_generate_outline_resume_pause_does_not_create_unknown_step(tmp_path: Path) -> None:
    _init_book(tmp_path)
    baseline_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=baseline_client, model="dummy")

    pause_client_first = DummyClientWithPause(
        [json.dumps(_phase_04b_for_chapter(1))], fail_call_number=1
    )
    with pytest.raises(RuntimeError):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            rerun=True,
            from_phase="phase_04b_transition_execution",
            to_phase="phase_04b_transition_execution",
            client=pause_client_first,
            model="dummy",
        )

    pause_client_resume = DummyClientWithPause(
        [json.dumps(_phase_04b_for_chapter(1))], fail_call_number=1
    )
    with pytest.raises(RuntimeError):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            resume=True,
            from_phase="phase_04b_transition_execution",
            to_phase="phase_04b_transition_execution",
            client=pause_client_resume,
            model="dummy",
        )

    run_root = tmp_path / "books" / "my_book" / "outline" / "pipeline_runs"
    latest_run = sorted(run_root.iterdir())[-1]
    history = json.loads((latest_run / "phase_history.json").read_text(encoding="utf-8"))
    steps = history.get("steps", {}) if isinstance(history.get("steps"), dict) else {}
    assert "unknown" not in steps
    assert (
        steps.get("phase_04b_transition_execution", {}).get("status")
        == "paused"
    )


def test_generate_outline_force_full_rerun_reexecutes_successful_chapters(tmp_path: Path) -> None:
    _init_book(tmp_path)
    baseline_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=baseline_client, model="dummy")

    rerun_client = DummyClient(
        [json.dumps(_phase_04a_for_chapter(1)), json.dumps(_phase_04a_for_chapter(2))]
    )
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        resume=True,
        from_phase="phase_04a_transition_seam_analysis",
        to_phase="phase_04a_transition_seam_analysis",
        force_phase_full_rerun=True,
        client=rerun_client,
        model="dummy",
    )
    assert len(rerun_client.messages_history) == 2


def test_generate_outline_phase4a_resume_retries_exhausted_failed_chapter(tmp_path: Path) -> None:
    _init_book(tmp_path)
    baseline_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=baseline_client, model="dummy")

    failing_rerun_client = DummyClient(
        [
            json.dumps(_phase_04a_for_chapter(1)),
            "not-json",
            "still-not-json",
        ]
    )
    with pytest.raises(Exception):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            rerun=True,
            from_phase="phase_04a_transition_seam_analysis",
            to_phase="phase_04a_transition_seam_analysis",
            client=failing_rerun_client,
            model="dummy",
        )

    resume_client = DummyClient([json.dumps(_phase_04a_for_chapter(2))])
    handoff_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        resume=True,
        from_phase="phase_04a_transition_seam_analysis",
        to_phase="phase_04a_transition_seam_analysis",
        client=resume_client,
        model="dummy",
    )
    assert handoff_path.name in {"outline.json", "phase_04a_transition_seam_analysis_output.json"}
    assert len(resume_client.messages_history) == 1


def test_generate_outline_chapter_scoped_phase_requires_chapter_template_tokens(tmp_path: Path) -> None:
    _init_book(tmp_path)
    baseline_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=baseline_client, model="dummy")

    template_path = (
        tmp_path
        / "books"
        / "my_book"
        / "prompts"
        / "templates"
        / "outline_phase_04a_transition_seam_analysis.md"
    )
    text = template_path.read_text(encoding="utf-8")
    text = text.replace("{{chapter_target_id}}", "")
    template_path.write_text(text, encoding="utf-8")

    rerun_client = DummyClient([json.dumps(_phase_04a_for_chapter(1))])
    with pytest.raises(ValueError):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            rerun=True,
            from_phase="phase_04a_transition_seam_analysis",
            to_phase="phase_04a_transition_seam_analysis",
            client=rerun_client,
            model="dummy",
        )
    assert len(rerun_client.messages_history) == 0


def test_outline_backup_run_creates_manifest_and_snapshot(tmp_path: Path) -> None:
    _init_book(tmp_path)
    client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=client, model="dummy")

    backup_dir = backup_outline_run(workspace=tmp_path, book_id="my_book")
    manifest_path = backup_dir / "backup_manifest.json"
    snapshot_outline = backup_dir / "outline_snapshot" / "outline.json"
    snapshot_chapter = backup_dir / "outline_snapshot" / "chapters" / "ch_001.json"
    pipeline_report = backup_dir / "pipeline_run" / "outline_pipeline_report.json"

    assert manifest_path.exists()
    assert snapshot_outline.exists()
    assert snapshot_chapter.exists()
    assert pipeline_report.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("schema_version") == "outline_backup_manifest_v1"
    assert manifest.get("source_run_id")
    assert manifest.get("outline_hash")


def test_outline_restore_state_from_run_id(tmp_path: Path) -> None:
    _init_book(tmp_path)
    client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=client, model="dummy")

    outline_root = tmp_path / "books" / "my_book" / "outline"
    latest = json.loads((outline_root / "pipeline_latest.json").read_text(encoding="utf-8"))
    run_id = str(latest.get("run_id"))

    (outline_root / "outline.json").unlink()
    shutil.rmtree(outline_root / "chapters")

    restored = restore_outline_state(
        workspace=tmp_path,
        book_id="my_book",
        run_id=run_id,
    )
    assert restored.exists()
    assert (outline_root / "chapters" / "ch_001.json").exists()


def test_outline_restore_state_from_backup_path(tmp_path: Path) -> None:
    _init_book(tmp_path)
    client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=client, model="dummy")
    backup_dir = backup_outline_run(workspace=tmp_path, book_id="my_book")

    outline_root = tmp_path / "books" / "my_book" / "outline"
    (outline_root / "outline.json").unlink()
    shutil.rmtree(outline_root / "chapters")

    restored = restore_outline_state(
        workspace=tmp_path,
        book_id="my_book",
        backup_path=backup_dir,
    )
    assert restored.exists()
    assert (outline_root / "chapters" / "ch_001.json").exists()


def test_generate_outline_phase_thinking_env_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init_book(tmp_path)
    env_values = {
        "OUTLINE_PHASE_01_THINKING_LEVEL": "low",
        "OUTLINE_PHASE_02_THINKING_LEVEL": "medium",
        "OUTLINE_PHASE_03_THINKING_LEVEL": "high",
        "OUTLINE_PHASE_04A_THINKING_LEVEL": "minimal",
        "OUTLINE_PHASE_04B_THINKING_LEVEL": "low",
        "OUTLINE_PHASE_05_THINKING_LEVEL": "medium",
        "OUTLINE_PHASE_06_THINKING_LEVEL": "high",
    }
    monkeypatch.setattr("bookforge.outline.read_env_value", lambda key: env_values.get(key))

    client = DummyClient(_pipeline_responses(), provider="gemini")
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        client=client,
        model="gemini-3-flash-preview",
    )
    levels = [str(call.get("thinking_level")) for call in client.calls]
    assert levels == [
        "low",
        "medium",
        "high",
        "minimal",
        "minimal",
        "low",
        "low",
        "medium",
        "medium",
        "high",
        "high",
    ]


def test_generate_outline_phase04b_input_uses_phase04a_selected_insertions(tmp_path: Path) -> None:
    _init_book(tmp_path)
    client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=client, model="dummy")

    latest_run = _latest_run_dir(tmp_path)
    phase04a_path = latest_run / "phase_04a_output.json"
    phase04a = json.loads(phase04a_path.read_text(encoding="utf-8"))
    phase04a["phase_report"] = {
        "candidate_seams": [
            {
                "from_scene_ref": "1:1",
                "to_scene_ref": "1:2",
                "seam_score": 90,
                "requested_resolution": "full_scene",
                "reason": "forced test insertion",
            }
        ]
    }
    phase04a_path.write_text(json.dumps(phase04a, ensure_ascii=False, indent=2), encoding="utf-8")

    rerun_client = DummyClient(
        [
            json.dumps(
                _phase_04b_for_chapter_with_report(
                    1,
                    resolved_candidates=[
                        {
                            "from_scene_ref": "1:1",
                            "to_scene_ref": "1:2",
                        }
                    ],
                    inserted_scene_refs=["1:2"],
                )
            ),
            json.dumps(_phase_04b_for_chapter_with_report(2)),
        ]
    )
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        rerun=True,
        from_phase="phase_04b_transition_execution",
        to_phase="phase_04b_transition_execution",
        client=rerun_client,
        model="dummy",
    )

    rerun_dir = _latest_run_dir(tmp_path)
    chapter_input = json.loads(
        (rerun_dir / "phase_04b_transition_execution_chapter_001_input.json").read_text(
            encoding="utf-8"
        )
    )
    selected = (
        chapter_input.get("render_values", {}).get("phase_04_selected_candidates_json")
        if isinstance(chapter_input.get("render_values"), dict)
        else []
    )
    assert isinstance(selected, list)
    assert any(
        isinstance(item, dict)
        and item.get("from_scene_ref") == "1:1"
        and item.get("to_scene_ref") == "1:2"
        and item.get("requested_resolution") == "full_scene"
        for item in selected
    )


def test_generate_outline_resume_phase5_reports_existing_phase04_seam_metrics(tmp_path: Path) -> None:
    _init_book(tmp_path)
    phase04_candidates_ch1 = [
        {
            "from_scene_ref": "1:1",
            "to_scene_ref": "1:2",
            "seam_score": 90,
            "requested_resolution": "full_scene",
            "reason": "phase04 metric test",
        }
    ]
    phase04_candidates_ch2 = [
        {
            "from_scene_ref": "2:1",
            "to_scene_ref": "2:2",
            "seam_score": 40,
            "requested_resolution": "inline_bridge",
            "reason": "phase04 metric test",
        }
    ]

    first_client = DummyClient(
        [
            json.dumps(_phase_01()),
            json.dumps(_phase_02()),
            json.dumps(_base_outline()),
            json.dumps(_phase_04a_for_chapter_with_candidates(1, phase04_candidates_ch1)),
            json.dumps(_phase_04a_for_chapter_with_candidates(2, phase04_candidates_ch2)),
            json.dumps(
                _phase_04b_for_chapter_with_report(
                    1,
                    resolved_candidates=[
                        {"from_scene_ref": "1:1", "to_scene_ref": "1:2"}
                    ],
                    inserted_scene_refs=["1:2"],
                )
            ),
            json.dumps(_phase_04b_for_chapter_with_report(2)),
            json.dumps(_phase_05_for_chapter(1)),
            json.dumps(_phase_05_for_chapter(2)),
            json.dumps(_phase_06_for_chapter(1)),
            json.dumps(_phase_06_for_chapter(2)),
        ]
    )
    generate_outline(workspace=tmp_path, book_id="my_book", client=first_client, model="dummy")

    resume_client = DummyClient(
        [
            json.dumps(_phase_05_for_chapter(1)),
            json.dumps(_phase_05_for_chapter(2)),
            json.dumps(_phase_06_for_chapter(1)),
            json.dumps(_phase_06_for_chapter(2)),
        ]
    )
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        resume=True,
        from_phase="phase_05_cast_function_refinement",
        to_phase="phase_06_thread_payoff_refinement",
        client=resume_client,
        model="dummy",
    )

    report_path, report = load_latest_outline_pipeline_report(workspace=tmp_path, book_id="my_book")
    assert report_path is not None
    seam = report.get("seam_outcomes", {}) if isinstance(report, dict) else {}
    assert int(seam.get("candidates", 0) or 0) > 0
    assert int(seam.get("selected", 0) or 0) > 0


def test_generate_outline_success_clears_pause_marker_and_unknown_step(tmp_path: Path) -> None:
    _init_book(tmp_path)
    client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=client, model="dummy")

    run_dir = _latest_run_dir(tmp_path)
    history_path = run_dir / "phase_history.json"
    history = json.loads(history_path.read_text(encoding="utf-8"))
    history.setdefault("steps", {})["unknown"] = {
        "status": "paused",
        "attempts": 1,
        "logical_phase": "unknown",
        "validation": {"status": "fail", "errors": [], "warnings": [], "metrics": {}},
    }
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "pipeline_run_paused.json").write_text(
        json.dumps({"step_id": "unknown"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    resume_client = DummyClient(
        [
            json.dumps(_phase_05_for_chapter(1)),
            json.dumps(_phase_05_for_chapter(2)),
            json.dumps(_phase_06_for_chapter(1)),
            json.dumps(_phase_06_for_chapter(2)),
        ]
    )
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        resume=True,
        from_phase="phase_05_cast_function_refinement",
        to_phase="phase_06_thread_payoff_refinement",
        client=resume_client,
        model="dummy",
    )

    updated_history = json.loads(history_path.read_text(encoding="utf-8"))
    updated_steps = (
        updated_history.get("steps", {})
        if isinstance(updated_history.get("steps"), dict)
        else {}
    )
    assert "unknown" not in updated_steps
    assert not (run_dir / "pipeline_run_paused.json").exists()
