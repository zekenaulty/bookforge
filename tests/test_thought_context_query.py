from __future__ import annotations

from pathlib import Path

from bookforge.llm.signatures import append_signature_records
from bookforge.query import get_thought_context_projection


def test_thought_context_projection_filters_relevant_t1_signatures(tmp_path: Path) -> None:
    append_signature_records(
        tmp_path,
        [
            {
                "signature_id": "sig-ch1-plan",
                "created_at": "2026-04-20T00:00:00Z",
                "book_id": "book",
                "workflow_family": "section_write",
                "phase_id": "plan_scene",
                "turn_id": "T1",
                "chapter_id": 1,
                "label": "plan",
            },
            {
                "signature_id": "sig-scene-write",
                "created_at": "2026-04-20T00:01:00Z",
                "book_id": "book",
                "workflow_family": "section_write",
                "phase_id": "write_scene",
                "turn_id": "T1",
                "chapter_id": 1,
                "scene_id": 2,
                "label": "write",
            },
            {
                "signature_id": "sig-t2-ignored",
                "created_at": "2026-04-20T00:02:00Z",
                "book_id": "book",
                "workflow_family": "section_write",
                "phase_id": "write_scene",
                "turn_id": "T2",
                "chapter_id": 1,
                "scene_id": 2,
            },
            {
                "signature_id": "sig-other-book",
                "created_at": "2026-04-20T00:03:00Z",
                "book_id": "other",
                "workflow_family": "section_write",
                "phase_id": "write_scene",
                "turn_id": "T1",
                "chapter_id": 1,
                "scene_id": 2,
            },
        ],
    )

    view = get_thought_context_projection(
        tmp_path,
        "book",
        chapter_id=1,
        scene_id=2,
        workflow_family="section_write",
    )

    ids = [item["signature_id"] for item in view.selected_signatures]
    assert ids == ["sig-ch1-plan", "sig-scene-write"]
    assert view.turn_id == "T1"
    assert view.artifact_status == "diagnostic"
    assert "execution receipts remain the truth of what happened" in view.limitations


def test_thought_context_projection_can_filter_phase_and_limit(tmp_path: Path) -> None:
    append_signature_records(
        tmp_path,
        [
            {
                "signature_id": "sig-1",
                "book_id": "book",
                "workflow_family": "section_write",
                "phase_id": "write_scene",
                "turn_id": "T1",
                "chapter_id": 3,
                "scene_id": 1,
            },
            {
                "signature_id": "sig-2",
                "book_id": "book",
                "workflow_family": "section_write",
                "phase_id": "write_scene",
                "turn_id": "T1",
                "chapter_id": 3,
                "scene_id": 1,
            },
            {
                "signature_id": "sig-plan",
                "book_id": "book",
                "workflow_family": "section_write",
                "phase_id": "plan_scene",
                "turn_id": "T1",
                "chapter_id": 3,
                "scene_id": 1,
            },
        ],
    )

    view = get_thought_context_projection(
        tmp_path,
        "book",
        chapter_id=3,
        scene_id=1,
        workflow_family="section_write",
        phase_id="write_scene",
        limit=1,
    )

    assert [item["signature_id"] for item in view.candidate_signatures] == ["sig-1", "sig-2"]
    assert [item["signature_id"] for item in view.selected_signatures] == ["sig-2"]
    assert view.selector.phase_id == "write_scene"
