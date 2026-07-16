from __future__ import annotations

import json
from pathlib import Path

from bookforge.llm.errors import LLMRequestError
from bookforge.llm.logging import llm_log_context, log_llm_error, log_llm_response
from bookforge.llm.types import LLMResponse


def test_llm_response_logging_uses_context_and_writes_companions(tmp_path: Path) -> None:
    response = LLMResponse(
        text='{"ok": true}',
        raw={"provider_payload": True},
        provider="test",
        model="offline",
    )
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User prompt"},
    ]

    with llm_log_context(book_id="my_book", run_id="run_demo"):
        path = log_llm_response(
            tmp_path,
            "write_scene",
            response,
            request={"max_tokens": 100},
            extra={"chapter": 1, "scene": 2},
            messages=messages,
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.parts[-5:-1] == ("my_book", "run_demo", "ch_001", "write_scene")
    assert path.name.startswith("sc_002_write_scene_")
    assert payload["extra"] == {
        "book_id": "my_book",
        "run_id": "run_demo",
        "chapter": 1,
        "scene": 2,
    }
    assert path.with_suffix(".txt").exists()
    assert path.with_suffix(".prompt.txt").exists()


def test_llm_log_context_resets_and_explicit_scope_wins(tmp_path: Path) -> None:
    response = LLMResponse(text="ok", raw={}, provider="test", model="offline")

    with llm_log_context(book_id="context_book", run_id="run_demo"):
        scoped = log_llm_response(
            tmp_path,
            "outline_generate",
            response,
            extra={"book_id": "explicit_book"},
        )
    unscoped = log_llm_response(tmp_path, "author_generate", response)

    assert "explicit_book" in scoped.parts
    assert "context_book" not in scoped.parts
    assert unscoped.parts[-5:-3] == ("global", "unscoped")


def test_llm_error_logging_preserves_request_and_unique_events(tmp_path: Path) -> None:
    error = LLMRequestError(
        status_code=429,
        message="quota",
        retry_after_seconds=1.0,
        quota_violations=[],
        raw_response={"error": "quota"},
    )

    first = log_llm_error(
        tmp_path,
        "write_scene_error",
        error,
        request={"max_tokens": 200},
        extra={"book_id": "my_book"},
    )
    second = log_llm_error(
        tmp_path,
        "write_scene_error",
        error,
        request={"max_tokens": 200},
        extra={"book_id": "my_book"},
    )

    assert first != second
    assert first.exists() and second.exists()
    assert json.loads(first.read_text(encoding="utf-8"))["request"] == {"max_tokens": 200}
