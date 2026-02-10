from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.config.env import read_int_env
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message


DEFAULT_EMPTY_RESPONSE_RETRIES = 2
DEFAULT_REQUEST_ERROR_RETRIES = 1
DEFAULT_REQUEST_ERROR_BACKOFF_SECONDS = 2.0
DEFAULT_REQUEST_ERROR_MAX_SLEEP = 60.0
DEFAULT_JSON_RETRY_COUNT = 1


def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _empty_response_retries() -> int:
    return max(0, _int_env("BOOKFORGE_EMPTY_RESPONSE_RETRIES", DEFAULT_EMPTY_RESPONSE_RETRIES))


def _request_error_retries() -> int:
    return max(0, _int_env("BOOKFORGE_REQUEST_ERROR_RETRIES", DEFAULT_REQUEST_ERROR_RETRIES))


def _json_retry_count() -> int:
    return max(0, _int_env("BOOKFORGE_JSON_RETRY_COUNT", DEFAULT_JSON_RETRY_COUNT))


def _response_truncated(response: LLMResponse) -> bool:
    raw = response.raw
    if not isinstance(raw, dict):
        return False
    if response.provider == "gemini":
        candidates = raw.get("candidates", [])
        if not candidates:
            return False
        finish = candidates[0].get("finishReason")
        return str(finish).upper() == "MAX_TOKENS"
    if response.provider == "openai":
        choice = raw.get("choices", [{}])[0]
        finish = choice.get("finish_reason")
        return str(finish).lower() == "length"
    return False


def _lint_status_from_issues(issues: List[Dict[str, Any]]) -> str:
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        if str(issue.get("severity") or "").strip().lower() == "error":
            return "fail"
    return "pass"


def _state_patch_schema_retry_message(error: ValueError, *, prose_required: bool) -> str:
    base = (
        "Your previous STATE_PATCH JSON failed schema validation: "
        f"{error}. Return corrected output that fully satisfies the state_patch schema."
    )
    rules = (
        "Critical rules: every transfer_updates entry must be an object with item_id and "
        "reason (string); item_registry_updates and plot_device_updates must be ARRAYS of "
        "objects with item_id/device_id (do not output a single object keyed by id); "
        "all *_updates arrays must contain objects, never strings."
    )
    if prose_required:
        return base + " Return PROSE plus STATE_PATCH. Output format: PROSE: <text> then STATE_PATCH: <json>. No markdown. " + rules
    return base + " Return ONLY the corrected JSON object. No prose, no markdown, no commentary. " + rules


def _chat(
    workspace: Path,
    label: str,
    client: LLMClient,
    messages: List[Message],
    model: str,
    temperature: float,
    max_tokens: int,
    log_extra: Optional[Dict[str, Any]] = None,
) -> LLMResponse:
    key_slot = getattr(client, "key_slot", None)
    merged_extra: Dict[str, Any] = {}
    if log_extra:
        merged_extra.update(log_extra)
    if key_slot:
        merged_extra["key_slot"] = key_slot
    extra = merged_extra or None
    request = {"model": model, "temperature": temperature, "max_tokens": max_tokens}
    retries = _empty_response_retries()
    error_retries = _request_error_retries()
    attempt = 0
    error_attempt = 0
    while True:
        try:
            response = client.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        except LLMRequestError as exc:
            if should_log_llm():
                log_llm_error(workspace, f"{label}_error", exc, request=request, messages=messages, extra=extra)
            if exc.status_code in {429, 500, 502, 503, 504} and error_attempt < error_retries:
                delay = exc.retry_after_seconds
                if delay is None:
                    delay = DEFAULT_REQUEST_ERROR_BACKOFF_SECONDS * (2 ** error_attempt)
                delay = min(delay, DEFAULT_REQUEST_ERROR_MAX_SLEEP)
                if delay > 0:
                    time.sleep(delay)
                error_attempt += 1
                continue
            raise
        label_used = label if attempt == 0 else f"{label}_retry{attempt}"
        if should_log_llm():
            log_llm_response(workspace, label_used, response, request=request, messages=messages, extra=extra)
        if str(response.text).strip() or attempt >= retries:
            return response
        attempt += 1

