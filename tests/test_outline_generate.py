from pathlib import Path
import json
import pytest

from bookforge.llm.types import LLMResponse
from bookforge.outline import generate_outline, OutlinePhaseFailure, load_latest_outline_pipeline_report
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


def _basic_outline() -> dict:
    return {
        "schema_version": "1.1",
        "characters": [
            {
                "character_id": "CHAR_new_character_name",
                "name": "new_character_name",
                "pronouns": "he/him",
                "role": "protagonist",
                "intro": {"chapter": 1, "scene": 1},
            }
        ],
        "threads": [
            {"thread_id": "THREAD_prophecy", "label": "The call", "status": "open"}
        ],
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Introduce the quest.",
                "chapter_role": "hook",
                "stakes_shift": "The summons arrives.",
                "bridge": {"from_prev": "", "to_next": "The hero accepts."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Spark the inciting incident.",
                        "end_condition": "The summons is accepted.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "The call arrives.",
                                "type": "setup",
                                "outcome": "The hero receives and accepts the summons.",
                                "characters": ["CHAR_new_character_name"],
                                "introduces": ["CHAR_new_character_name"],
                                "threads": ["THREAD_prophecy"],
                                "location_start_id": "LOC_OFFICE_BREAKROOM",
                                "location_end_id": "LOC_OFFICE_BREAKROOM",
                                "location_start": "Office Breakroom",
                                "location_end": "Office Breakroom",
                                "handoff_mode": "direct_continuation",
                                "constraint_state": "free",
                                "transition_in_text": "Artie is still in the office breakroom as the summons hits.",
                                "transition_in_anchors": ["office", "breakroom", "summons"],
                                "seam_score": 10,
                                "seam_resolution": "inline_bridge",
                                "end_condition_echo": "The summons is accepted.",
                            }
                        ],
                    }
                ],
            },
            {
                "chapter_id": 2,
                "title": "Crossing",
                "goal": "Commit to the journey.",
                "chapter_role": "journey",
                "stakes_shift": "The path narrows.",
                "bridge": {"from_prev": "The hero accepts.", "to_next": "The first trial looms."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Departure",
                        "intent": "Leave home behind.",
                        "end_condition": "Departure is irreversible.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "They depart.",
                                "type": "transition",
                                "outcome": "The journey begins and home is left behind.",
                                "characters": ["CHAR_new_character_name"],
                                "threads": ["THREAD_prophecy"],
                                "location_start_id": "LOC_CITY_GATE",
                                "location_end_id": "LOC_ROAD_OUTSKIRTS",
                                "location_start": "City Gate",
                                "location_end": "Road Outskirts",
                                "handoff_mode": "direct_continuation",
                                "constraint_state": "free",
                                "transition_in_text": "At dawn, they leave through the city gate and commit to the road.",
                                "transition_in_anchors": ["dawn", "gate", "road"],
                                "seam_score": 12,
                                "seam_resolution": "inline_bridge",
                                "end_condition_echo": "Departure is irreversible.",
                            }
                        ],
                    }
                ],
            },
        ],
    }


def _phase_01_spine() -> dict:
    outline = _basic_outline()
    chapters = []
    for chapter in outline["chapters"]:
        chapters.append(
            {
                "chapter_id": chapter["chapter_id"],
                "title": chapter["title"],
                "goal": chapter["goal"],
                "chapter_role": chapter["chapter_role"],
                "stakes_shift": chapter["stakes_shift"],
                "bridge": chapter["bridge"],
                "pacing": chapter["pacing"],
            }
        )
    return {"schema_version": "spine_v1", "chapters": chapters}


def _phase_02_sections() -> dict:
    outline = _basic_outline()
    chapters = []
    for chapter in outline["chapters"]:
        sections = []
        for section in chapter["sections"]:
            sections.append(
                {
                    "section_id": section["section_id"],
                    "title": section["title"],
                    "intent": section["intent"],
                    "section_role": "setup",
                    "target_scene_count": len(section["scenes"]),
                    "end_condition": section["end_condition"],
                }
            )
        chapters.append({"chapter_id": chapter["chapter_id"], "sections": sections})
    return {"schema_version": "sections_v1", "chapters": chapters}


def _phase_03_outline() -> dict:
    return _basic_outline()


def _phase_04_wrapper() -> dict:
    return {
        "schema_version": "transition_refine_v1",
        "outline": _basic_outline(),
        "phase_report": {
            "orphan_outcomes_before": 0,
            "orphan_outcomes_after": 0,
            "weak_handoffs_after": 0,
            "edits_applied": [],
            "transition_hint_compliance": [{"hint_id": "HINT_1", "satisfied": True, "evidence_scene_refs": ["1:1"]}],
        },
    }


def _phase_05_wrapper() -> dict:
    return {
        "schema_version": "cast_refine_v1",
        "outline": _basic_outline(),
        "cast_report": {
            "core_character_ids": ["CHAR_new_character_name"],
            "supporting_character_ids": [],
            "episodic_character_ids": [],
            "recurring_without_job_count": 0,
            "edits_applied": [],
        },
    }


def _phase_06_outline() -> dict:
    return _basic_outline()


def _pipeline_responses() -> list[str]:
    return [
        json.dumps(_phase_01_spine()),
        json.dumps(_phase_02_sections()),
        json.dumps(_phase_03_outline()),
        json.dumps(_phase_04_wrapper()),
        json.dumps(_phase_05_wrapper()),
        json.dumps(_phase_06_outline()),
    ]


def _broken_outline_extra_data_json() -> str:
    outline = _phase_06_outline()
    reordered = {
        "schema_version": outline["schema_version"],
        "chapters": outline["chapters"],
        "threads": outline["threads"],
        "characters": outline["characters"],
    }
    raw = json.dumps(reordered)
    parts = raw.rsplit('], "threads"', 1)
    return ']}, "threads"'.join(parts)


def _broken_outline_json() -> str:
    outline = _phase_06_outline()
    reordered = {
        "schema_version": outline["schema_version"],
        "chapters": outline["chapters"],
        "threads": outline["threads"],
        "characters": outline["characters"],
    }
    raw = json.dumps(reordered)
    raw = raw.replace('}]}]}, {"chapter_id": 2', '}]}], "chapter_id": 2', 1)
    raw = raw.replace('}]}]}], "threads"', '}]}], "threads"', 1)
    return raw


def _pipeline_responses_with_final(final_response: str) -> list[str]:
    responses = _pipeline_responses()
    responses[-1] = final_response
    return responses


def test_generate_outline_writes_files(tmp_path: Path) -> None:
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

    client = DummyClient(_pipeline_responses())
    outline_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        client=client,
        model="dummy",
    )

    assert outline_path.exists()
    assert (outline_path.parent / "chapters" / "ch_001.json").exists()
    assert (outline_path.parent / "chapters" / "ch_002.json").exists()
    assert (outline_path.parent / "characters.json").exists()


def test_generate_outline_includes_prompt_file(tmp_path: Path) -> None:
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

    prompt_path = tmp_path / "outline_prompt.txt"
    prompt_path.write_text("A ruined city hides the true heir.", encoding="utf-8")

    client = DummyClient(_pipeline_responses())
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        prompt_file=prompt_path,
        client=client,
        model="dummy",
    )

    assert client.messages_history
    first_call_messages = client.messages_history[0]
    user_messages = [msg for msg in first_call_messages if msg.get("role") == "user"]
    assert user_messages
    assert "A ruined city hides the true heir." in user_messages[0].get("content", "")


def test_generate_outline_strict_transition_hints_requires_schema(tmp_path: Path) -> None:
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

    hints_path = tmp_path / "transition_hints_invalid.json"
    hints_path.write_text(json.dumps({"raw": "not valid"}), encoding="utf-8")

    client = DummyClient(_pipeline_responses())
    with pytest.raises(ValueError, match="Invalid --transition-hints-file"):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            new_version=False,
            transition_hints_file=hints_path,
            strict_transition_hints=True,
            client=client,
            model="dummy",
        )


def test_generate_outline_strict_transition_hints_valid(tmp_path: Path) -> None:
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

    hints_path = tmp_path / "transition_hints_valid.json"
    hints_path.write_text(
        json.dumps({"hints": [{"hint_id": "HINT_1", "hint": "Maintain chapter opening bridge."}]}),
        encoding="utf-8",
    )

    client = DummyClient(_pipeline_responses())
    outline_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        transition_hints_file=hints_path,
        strict_transition_hints=True,
        client=client,
        model="dummy",
    )

    assert outline_path.exists()


def test_generate_outline_resume_reuses_successful_phases(tmp_path: Path) -> None:
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

    first_client = DummyClient(_pipeline_responses())
    first_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        client=first_client,
        model="dummy",
    )
    assert first_path.exists()
    assert len(first_client.messages_history) == 6

    resume_client = DummyClient(_pipeline_responses())
    resume_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        resume=True,
        client=resume_client,
        model="dummy",
    )
    assert resume_path.exists()
    assert len(resume_client.messages_history) == 0


def test_generate_outline_from_phase_backtracks_missing_dependencies(tmp_path: Path) -> None:
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

    client = DummyClient(_pipeline_responses())
    handoff_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        from_phase="phase_04_transition_causality_refinement",
        to_phase="phase_04_transition_causality_refinement",
        client=client,
        model="dummy",
    )

    assert handoff_path.name == "outline_transitions_refined_v1_1.json"
    assert len(client.messages_history) == 4


def test_generate_outline_resume_fingerprint_mismatch_blocks(tmp_path: Path) -> None:
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

    first_client = DummyClient(_pipeline_responses())
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        client=first_client,
        model="dummy",
    )

    prompt_path = tmp_path / "outline_prompt_changed.txt"
    prompt_path.write_text("Changed resume fingerprint input.", encoding="utf-8")

    resume_client = DummyClient(_pipeline_responses())
    with pytest.raises(ValueError, match="Resume fingerprint mismatch"):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            resume=True,
            prompt_file=prompt_path,
            client=resume_client,
            model="dummy",
        )


def test_generate_outline_strict_json_rejects_malformed_final_output(tmp_path: Path) -> None:
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

    client = DummyClient(_pipeline_responses_with_final(_broken_outline_json()))
    with pytest.raises(OutlinePhaseFailure):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            new_version=False,
            client=client,
            model="dummy",
        )
    report_path, report = load_latest_outline_pipeline_report(workspace=tmp_path, book_id="my_book")
    assert report_path is not None
    assert report.get("overall_status") == "ERROR"
    assert any(str(code) == "json_parse" for code in report.get("reason_codes", []))


def test_generate_outline_strict_json_rejects_extra_data_before_threads(tmp_path: Path) -> None:
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

    client = DummyClient(_pipeline_responses_with_final(_broken_outline_extra_data_json()))
    with pytest.raises(OutlinePhaseFailure):
        generate_outline(
            workspace=tmp_path,
            book_id="my_book",
            new_version=False,
            client=client,
            model="dummy",
        )
    report_path, report = load_latest_outline_pipeline_report(workspace=tmp_path, book_id="my_book")
    assert report_path is not None
    assert report.get("overall_status") == "ERROR"
    assert any(str(code) == "json_parse" for code in report.get("reason_codes", []))
