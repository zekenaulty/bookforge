from pathlib import Path
import json
import pytest

from bookforge.llm.types import LLMResponse
from bookforge.outline import generate_outline, load_latest_outline_pipeline_report
from bookforge.workspace import init_book_workspace


class DummyClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.messages_history = []

    def chat(self, messages, model, temperature=0.7, max_tokens=1024):
        self.messages_history.append(messages)
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
    return {
        "schema_version": "transition_refine_v1",
        "outline": _base_outline(),
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
    return {
        "schema_version": "transition_refine_v1",
        "outline": _base_outline(),
        "phase_report": {
            "inserted_scene_refs": [],
            "resolved_candidates": [],
            "blocked_by_budget": [],
            "downgraded_resolution": [],
            "unresolved_required_insertions": [],
            "edits_applied": [],
        },
    }


def _phase_05() -> dict:
    return {
        "schema_version": "cast_refine_v1",
        "outline": _base_outline(),
        "cast_report": {
            "core_character_ids": ["CHAR_protagonist"],
            "supporting_character_ids": [],
            "episodic_character_ids": [],
            "recurring_without_job_count": 0,
            "edits_applied": [],
        },
    }


def _pipeline_responses() -> list[str]:
    return [
        json.dumps(_phase_01()),
        json.dumps(_phase_02()),
        json.dumps(_base_outline()),
        json.dumps(_phase_04a()),
        json.dumps(_phase_04b()),
        json.dumps(_phase_05()),
        json.dumps(_base_outline()),
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
    assert len(client.messages_history) == 7

    report_path, report = load_latest_outline_pipeline_report(workspace=tmp_path, book_id="my_book")
    assert report_path is not None
    assert report.get("overall_status") in {"SUCCESS", "SUCCESS_WITH_WARNINGS"}


def test_generate_outline_resume_reuses_successful_steps(tmp_path: Path) -> None:
    _init_book(tmp_path)

    first_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=first_client, model="dummy")
    assert len(first_client.messages_history) == 7

    resume_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", resume=True, client=resume_client, model="dummy")
    assert len(resume_client.messages_history) == 0


def test_generate_outline_phase_rerun_uses_previous_dependencies(tmp_path: Path) -> None:
    _init_book(tmp_path)

    baseline_client = DummyClient(_pipeline_responses())
    generate_outline(workspace=tmp_path, book_id="my_book", client=baseline_client, model="dummy")

    rerun_client = DummyClient([json.dumps(_phase_04a()), json.dumps(_phase_04b())])
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
    assert len(rerun_client.messages_history) == 2


def test_generate_outline_from_phase_without_dependencies_fails(tmp_path: Path) -> None:
    _init_book(tmp_path)

    client = DummyClient([json.dumps(_phase_04a()), json.dumps(_phase_04b())])
    with pytest.raises(FileNotFoundError):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            from_phase="phase_04_transition_causality_refinement",
            to_phase="phase_04_transition_causality_refinement",
            client=client,
            model="dummy",
        )
