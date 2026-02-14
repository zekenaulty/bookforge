from copy import deepcopy

from bookforge.outline import _apply_phase04_transition_policy, _validate_phase_payload


def _phase04_payload_two_scenes() -> dict:
    return {
        "schema_version": "transition_refine_v1",
        "outline": {
            "schema_version": "1.1",
            "chapters": [
                {
                    "chapter_id": 1,
                    "title": "Checkpoint",
                    "goal": "Move from gate pressure to tavern fallout.",
                    "chapter_role": "pressure",
                    "stakes_shift": "Public attention increases.",
                    "bridge": {"from_prev": "", "to_next": "A social threat emerges."},
                    "pacing": {"intensity": 4, "tempo": "steady", "expected_scene_count": 2},
                    "sections": [
                        {
                            "section_id": 1,
                            "title": "Gate",
                            "intent": "Scan and detain the protagonist.",
                            "scenes": [
                                {
                                    "scene_id": 1,
                                    "summary": "The gate scan flags Artie as anomalous.",
                                    "type": "escalation",
                                    "outcome": "A scan anomaly forces temporary detention.",
                                    "characters": ["CHAR_artie"],
                                    "location_start": "Oakhaven Gate",
                                    "location_end": "Oakhaven Gate",
                                    "constraint_state": "detained",
                                },
                                {
                                    "scene_id": 2,
                                    "summary": "Artie is seated at Barnaby's tavern under watch.",
                                    "type": "aftermath",
                                    "outcome": "Release under watch pushes him into local politics.",
                                    "characters": ["CHAR_artie"],
                                    "location_start": "Barnaby Tavern",
                                    "location_end": "Barnaby Tavern",
                                    "constraint_state": "free",
                                    "handoff_mode": "detained_then_release",
                                },
                            ],
                        }
                    ],
                }
            ],
            "characters": [
                {
                    "character_id": "CHAR_artie",
                    "name": "Artie",
                    "pronouns": "he/him",
                    "role": "protagonist",
                    "intro": {"chapter": 1, "scene": 1},
                }
            ],
        },
        "phase_report": {
            "orphan_outcomes_before": 1,
            "orphan_outcomes_after": 1,
            "weak_handoffs_after": 1,
            "orphan_scene_refs_after": ["1:1"],
            "weak_handoff_refs_after": ["1:1"],
            "edits_applied": [],
        },
    }


def test_phase04_policy_fills_required_transition_contract() -> None:
    payload = _phase04_payload_two_scenes()
    refined = _apply_phase04_transition_policy(
        deepcopy(payload),
        exact_scene_count=False,
        allow_transition_scene_insertions=False,
        transition_insert_budget_per_chapter=0,
    )

    scenes = refined["outline"]["chapters"][0]["sections"][0]["scenes"]
    assert len(scenes) == 2
    assert scenes[0]["hands_off_to"] == "1:2"
    assert scenes[1]["consumes_outcome_from"] == "1:1"
    assert isinstance(scenes[0]["seam_score"], int)
    assert scenes[0]["seam_resolution"] in {"inline_bridge", "micro_scene", "full_scene"}
    assert isinstance(scenes[0]["transition_in_anchors"], list)
    assert len(scenes[0]["transition_in_anchors"]) >= 3
    assert refined["phase_report"]["orphan_outcomes_after"] == 0
    assert refined["phase_report"]["weak_handoffs_after"] == 0
    assert isinstance(refined["phase_report"].get("blocked_by_budget"), list)


def test_phase04_policy_inserts_transition_scene_when_budget_allows() -> None:
    payload = _phase04_payload_two_scenes()
    refined = _apply_phase04_transition_policy(
        deepcopy(payload),
        exact_scene_count=False,
        allow_transition_scene_insertions=True,
        transition_insert_budget_per_chapter=1,
    )

    scenes = refined["outline"]["chapters"][0]["sections"][0]["scenes"]
    assert len(scenes) == 3
    assert any(scene.get("inserted_by_pipeline") is True for scene in scenes)
    assert [scene.get("scene_id") for scene in scenes] == [1, 2, 3]
    assert scenes[0]["hands_off_to"] == "1:2"
    assert scenes[1]["consumes_outcome_from"] == "1:1"
    assert scenes[1]["hands_off_to"] == "1:3"
    assert scenes[2]["consumes_outcome_from"] == "1:2"


def test_phase04_policy_exact_mode_conflict_fails_validation() -> None:
    payload = _phase04_payload_two_scenes()
    refined = _apply_phase04_transition_policy(
        deepcopy(payload),
        exact_scene_count=True,
        allow_transition_scene_insertions=True,
        transition_insert_budget_per_chapter=1,
    )

    validation = _validate_phase_payload(
        phase_id="phase_04_transition_causality_refinement",
        payload=refined,
        handoffs={},
        strict_transition_hints=False,
        strict_transition_bridges=False,
        transition_hint_ids=[],
        scene_count_range=None,
        exact_scene_count=True,
    )
    assert validation["status"] == "fail"
    assert any(item.get("code") == "exact_scene_count_transition_conflict" for item in validation["errors"])
