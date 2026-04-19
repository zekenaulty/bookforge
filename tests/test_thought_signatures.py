from __future__ import annotations

import json
from pathlib import Path

from bookforge.llm.logging import log_llm_response, prior_response_content_array_metadata
from bookforge.llm.signatures import purge_signatures
from bookforge.llm.storage import signature_active_path
from bookforge.llm.types import LLMResponse


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_signature_active_intent_outcome(tmp_path: Path) -> None:
    workspace = tmp_path
    response_t1 = LLMResponse(
        text="ok",
        raw={},
        provider="gemini",
        model="test",
        assistant_parts=[{"text": "ok", "thoughtSignature": "sig-t1"}],
    )
    log_llm_response(
        workspace,
        "outline_phase_04a_transition_seam_analysis_chapter_001_attempt1",
        response_t1,
        request={"model": "test", "temperature": 0.2, "max_tokens": 10},
        extra={"book_id": "book", "phase_id": "phase_04a_transition_seam_analysis", "turn_id": "T1", "chapter": 1},
        messages=[],
    )

    response_t2 = LLMResponse(
        text="ok",
        raw={},
        provider="gemini",
        model="test",
        assistant_parts=[{"text": "ok", "thoughtSignature": "sig-t2"}],
    )
    log_llm_response(
        workspace,
        "outline_phase_04a_transition_seam_analysis_chapter_001_attempt2",
        response_t2,
        request={"model": "test", "temperature": 0.2, "max_tokens": 10},
        extra={"book_id": "book", "phase_id": "phase_04a_transition_seam_analysis", "turn_id": "T2", "chapter": 1},
        messages=[],
    )

    active_path = signature_active_path(workspace)
    assert active_path.exists()
    payload = _read_json(active_path)
    phase_bucket = payload["by_phase"]["phase_04a_transition_seam_analysis"]
    assert phase_bucket["intent"]["signature_id"] != phase_bucket["outcome"]["signature_id"]
    assert phase_bucket["intent"]["turn_id"] == "T1"
    assert phase_bucket["outcome"]["turn_id"] == "T2"


def test_purge_signatures_filters_by_book(tmp_path: Path) -> None:
    workspace = tmp_path
    response = LLMResponse(
        text="ok",
        raw={},
        provider="gemini",
        model="test",
        assistant_parts=[{"text": "ok", "thoughtSignature": "sig"}],
    )
    log_llm_response(
        workspace,
        "outline_phase_04a_transition_seam_analysis_chapter_001_attempt1",
        response,
        request={"model": "test", "temperature": 0.2, "max_tokens": 10},
        extra={"book_id": "book-a", "phase_id": "phase_04a_transition_seam_analysis", "turn_id": "T1", "chapter": 1},
        messages=[],
    )
    log_llm_response(
        workspace,
        "outline_phase_04a_transition_seam_analysis_chapter_001_attempt1",
        response,
        request={"model": "test", "temperature": 0.2, "max_tokens": 10},
        extra={"book_id": "book-b", "phase_id": "phase_04a_transition_seam_analysis", "turn_id": "T1", "chapter": 1},
        messages=[],
    )

    result = purge_signatures(workspace, book_id="book-a")

    assert result["removed"] == 1
    payload = _read_json(signature_active_path(workspace))
    assert payload["by_phase"]["phase_04a_transition_seam_analysis"]["intent"]["book_id"] == "book-b"


def test_prior_response_content_array_metadata_extracts_signature_details() -> None:
    metadata = prior_response_content_array_metadata(
        [
            {"text": "plan"},
            {"text": "hidden", "thoughtSignature": "sig-1"},
        ]
    )

    assert metadata["prior_response_content_array_reused"] is True
    assert metadata["prior_response_content_array_source"] == "prior_turn_model_response"
    assert metadata["prior_response_content_array_part_count"] == 2
    assert metadata["prior_response_content_array_signature_count"] == 1
    assert metadata["prior_response_content_array_signature_part_indexes"] == [1]
    assert isinstance(metadata["prior_response_content_array_sha256"], str)
    assert len(metadata["prior_response_content_array_sha256"]) == 64
