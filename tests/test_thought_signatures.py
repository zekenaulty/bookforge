from __future__ import annotations

import json
from pathlib import Path

from bookforge.llm.logging import log_llm_response
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

    active_path = workspace / "logs" / "llm" / "thought_signature_active.json"
    assert active_path.exists()
    payload = _read_json(active_path)
    phase_bucket = payload["by_phase"]["phase_04a_transition_seam_analysis"]
    assert phase_bucket["intent"]["signature_id"] != phase_bucket["outcome"]["signature_id"]
    assert phase_bucket["intent"]["turn_id"] == "T1"
    assert phase_bucket["outcome"]["turn_id"] == "T2"
