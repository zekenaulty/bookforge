from copy import deepcopy

from bookforge.phases.outline.validators import (
    route_phase04_candidates,
    validate_phase_04b,
)


def _outline_wrapper() -> dict:
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
                            "end_condition": "Release under watch pushes him into local politics.",
                            "scenes": [
                                {
                                    "scene_id": 1,
                                    "summary": "The gate scan flags Artie as anomalous.",
                                    "type": "escalation",
                                    "outcome": "A scan anomaly forces temporary detention.",
                                    "characters": ["CHAR_artie"],
                                    "location_start_label": "Oakhaven Gate",
                                    "location_end_label": "Oakhaven Gate",
                                    "location_start": "Oakhaven Gate",
                                    "location_end": "Oakhaven Gate",
                                    "location_start_id": "LOC_OAKHAVEN_GATE_AA11BB",
                                    "location_end_id": "LOC_OAKHAVEN_GATE_AA11BB",
                                    "handoff_mode": "detained_then_release",
                                    "constraint_state": "detained",
                                    "transition_in_text": "At the gate checkpoint, guards isolate Artie for anomaly review.",
                                    "transition_in_anchors": ["gate checkpoint", "guard cordon", "anomaly scanner"],
                                    "transition_out_text": "Under guard escort, Artie is moved toward Barnaby's tavern.",
                                    "transition_out_anchors": ["guard escort", "stone avenue", "tavern sign"],
                                    "hands_off_to": "1:2",
                                    "seam_score": 78,
                                    "seam_resolution": "micro_scene",
                                },
                                {
                                    "scene_id": 2,
                                    "summary": "Artie is seated at Barnaby's tavern under watch.",
                                    "type": "aftermath",
                                    "outcome": "Release under watch pushes him into local politics.",
                                    "characters": ["CHAR_artie"],
                                    "location_start_label": "Barnaby Tavern",
                                    "location_end_label": "Barnaby Tavern",
                                    "location_start": "Barnaby Tavern",
                                    "location_end": "Barnaby Tavern",
                                    "location_start_id": "LOC_BARNABY_TAVERN_CC22DD",
                                    "location_end_id": "LOC_BARNABY_TAVERN_CC22DD",
                                    "handoff_mode": "detained_then_release",
                                    "constraint_state": "free",
                                    "transition_in_text": "After processing, guards release Artie into Barnaby's tavern under observation.",
                                    "transition_in_anchors": ["processing desk", "release stamp", "barnaby tavern"],
                                    "consumes_outcome_from": "1:1",
                                    "seam_score": 22,
                                    "seam_resolution": "inline_bridge",
                                    "end_condition_echo": "Release under watch pushes him into local politics.",
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
            "threads": [],
        },
        "phase_report": {
            "resolved_candidates": [
                {
                    "from_scene_ref": "1:1",
                    "to_scene_ref": "1:2",
                    "requested_resolution": "micro_scene",
                    "resolution": "micro_scene",
                    "inserted_scene_ref": "1:2",
                }
            ],
            "inserted_scene_refs": ["1:2"],
            "unresolved_required_insertions": [],
        },
    }


def test_route_phase04_candidates_exact_mode_conflict() -> None:
    routing = route_phase04_candidates(
        candidate_seams=[
            {
                "from_scene_ref": "1:1",
                "to_scene_ref": "1:2",
                "seam_score": 80,
                "requested_resolution": "micro_scene",
            }
        ],
        exact_scene_count=True,
        allow_transition_scene_insertions=True,
        transition_insert_budget_per_chapter=2,
    )
    assert routing["selected"] == []
    assert len(routing["exact_conflicts"]) == 1


def test_phase04b_validation_requires_selected_resolution() -> None:
    payload = _outline_wrapper()
    selected = [
        {
            "from_scene_ref": "1:1",
            "to_scene_ref": "1:2",
            "requested_resolution": "micro_scene",
        }
    ]
    result = validate_phase_04b(
        payload,
        sections_payload={
            "chapters": [
                {
                    "chapter_id": 1,
                    "sections": [
                        {
                            "section_id": 1,
                            "end_condition": "Release under watch pushes him into local politics.",
                        }
                    ],
                }
            ]
        },
        strict_transition_bridges=True,
        selected_candidates=selected,
    )
    assert result.status == "pass"

    broken = deepcopy(payload)
    broken["phase_report"]["resolved_candidates"] = []
    result_broken = validate_phase_04b(
        broken,
        sections_payload={
            "chapters": [
                {
                    "chapter_id": 1,
                    "sections": [
                        {
                            "section_id": 1,
                            "end_condition": "Release under watch pushes him into local politics.",
                        }
                    ],
                }
            ]
        },
        strict_transition_bridges=True,
        selected_candidates=selected,
    )
    assert result_broken.status == "fail"
    assert any(item.get("code") == "transition_insertion_required" for item in result_broken.errors)


def test_phase04b_validation_rejects_downgraded_resolution() -> None:
    payload = _outline_wrapper()
    payload["phase_report"]["downgraded_resolution"] = [
        {
            "from_scene_ref": "1:1",
            "to_scene_ref": "1:2",
            "requested_resolution": "micro_scene",
            "resolution": "inline_bridge",
            "reason": "not allowed",
        }
    ]
    selected = [
        {
            "from_scene_ref": "1:1",
            "to_scene_ref": "1:2",
            "requested_resolution": "micro_scene",
        }
    ]
    result = validate_phase_04b(
        payload,
        sections_payload={
            "chapters": [
                {
                    "chapter_id": 1,
                    "sections": [
                        {
                            "section_id": 1,
                            "end_condition": "Release under watch pushes him into local politics.",
                        }
                    ],
                }
            ]
        },
        strict_transition_bridges=True,
        selected_candidates=selected,
    )
    assert result.status == "fail"
    assert any(item.get("code") == "transition_downgrade_forbidden" for item in result.errors)


def test_phase04b_validation_requires_inserted_scene_ref_on_selected_insertions() -> None:
    payload = _outline_wrapper()
    payload["phase_report"]["resolved_candidates"] = [
        {
            "from_scene_ref": "1:1",
            "to_scene_ref": "1:2",
            "requested_resolution": "micro_scene",
            "resolution": "micro_scene",
        }
    ]
    payload["phase_report"]["inserted_scene_refs"] = []
    selected = [
        {
            "from_scene_ref": "1:1",
            "to_scene_ref": "1:2",
            "requested_resolution": "micro_scene",
        }
    ]
    result = validate_phase_04b(
        payload,
        sections_payload={
            "chapters": [
                {
                    "chapter_id": 1,
                    "sections": [
                        {
                            "section_id": 1,
                            "end_condition": "Release under watch pushes him into local politics.",
                        }
                    ],
                }
            ]
        },
        strict_transition_bridges=True,
        selected_candidates=selected,
    )
    assert result.status == "fail"
    assert any(item.get("code") == "transition_insertion_missing_scene_ref" for item in result.errors)
