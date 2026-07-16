from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional
import json
import re

from .errors import LLMRequestError
from .storage import llm_log_dir, llm_log_path
from .types import LLMResponse, Message
from bookforge.config.env import read_env_value


_LLM_LOG_CONTEXT: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "bookforge_llm_log_context",
    default=None,
)


def _extract_text_payload(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _loose_pretty_text(text: str) -> str:
    indent = 0
    in_string = False
    escape = False
    lines = []
    line = []

    def emit_line() -> None:
        if line:
            lines.append("".join(line).rstrip())
            line.clear()

    def append_indent() -> None:
        line.append("  " * indent)

    append_indent()

    for ch in text:
        if in_string:
            line.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            line.append(ch)
            continue

        if ch in '{[':
            line.append(ch)
            emit_line()
            indent += 1
            append_indent()
            continue
        if ch in '}]':
            emit_line()
            indent = max(indent - 1, 0)
            append_indent()
            line.append(ch)
            continue
        if ch == ',':
            line.append(ch)
            emit_line()
            append_indent()
            continue
        if ch == ':':
            line.append(': ')
            continue
        if ch.isspace():
            continue
        line.append(ch)

    emit_line()
    return "\n".join(lines).strip()


def _pretty_text_payload(text: str) -> str:
    payload = _extract_text_payload(text)
    if not payload:
        return ""
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        stripped = payload.lstrip()
        if stripped.startswith("{") or stripped.startswith("["):
            return _loose_pretty_text(payload)
        return payload
    return json.dumps(parsed, ensure_ascii=True, indent=2)


@contextmanager
def llm_log_context(**extra: Any) -> Iterator[None]:
    merged = dict(_LLM_LOG_CONTEXT.get() or {})
    merged.update(extra)
    token = _LLM_LOG_CONTEXT.set(merged)
    try:
        yield
    finally:
        _LLM_LOG_CONTEXT.reset(token)


def _effective_extra(extra: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    merged = dict(_LLM_LOG_CONTEXT.get() or {})
    if extra:
        merged.update(extra)
    return merged or None


def _split_prompt_messages(messages: Optional[list[Message]]) -> tuple[str, list[Message]]:
    if not messages:
        return "", []
    system_parts: list[str] = []
    non_system: list[Message] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", ""))
        content = str(msg.get("content", ""))
        if role == "system":
            if content.strip():
                system_parts.append(content)
        else:
            non_system.append({"role": role, "content": content})
    return "\n\n".join(system_parts), non_system


def _format_prompt_text(system_text: str, non_system: list[Message]) -> str:
    sections: list[str] = []
    if system_text:
        sections.append("SYSTEM:")
        sections.append(system_text)
    for msg in non_system:
        role = str(msg.get("role", "") or "unknown").upper()
        content = str(msg.get("content", ""))
        sections.append(f"{role}:")
        sections.append(content)
    return "\n\n".join(sections).strip()


def _write_prompt_log(log_path: Path, system_text: str, non_system: list[Message]) -> None:
    if not system_text and not non_system:
        return
    prompt_path = log_path.with_suffix('.prompt.txt')
    prompt_path.write_text(_format_prompt_text(system_text, non_system), encoding='utf-8')


def _write_pretty_text_log(log_path: Path, text: str) -> None:
    pretty_path = log_path.with_suffix('.txt')
    pretty_path.write_text(_pretty_text_payload(text), encoding='utf-8')


def should_log_llm() -> bool:
    flag = read_env_value("BOOKFORGE_LOG_LLM") or ""
    flag = str(flag).strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _format_error_payload(error: LLMRequestError) -> Dict[str, Any]:
    return {
        "status_code": error.status_code,
        "message": error.message,
        "retry_after_seconds": error.retry_after_seconds,
        "quota_violations": [
            {
                "quota_metric": item.quota_metric,
                "quota_id": item.quota_id,
                "quota_dimensions": item.quota_dimensions,
                "quota_value": item.quota_value,
            }
            for item in error.quota_violations
        ],
    }


def _write_error_text_log(log_path: Path, error: LLMRequestError) -> None:
    pretty_path = log_path.with_suffix(".txt")
    if isinstance(error.raw_response, (dict, list)):
        pretty = json.dumps(error.raw_response, ensure_ascii=True, indent=2)
    else:
        pretty = str(error.raw_response)
    pretty_path.write_text(pretty, encoding="utf-8")

def log_llm_response(
    workspace: Path,
    label: str,
    response: LLMResponse,
    request: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
    messages: Optional[list[Message]] = None,
) -> Path:
    effective_extra = _effective_extra(extra)
    log_path = llm_log_path(workspace, label=label, extra=effective_extra)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    system_text = ""
    non_system: list[Message] = []
    if messages:
        system_text, non_system = _split_prompt_messages(messages)
    payload: Dict[str, Any] = {
        "label": label,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "provider": response.provider,
        "model": response.model,
        "text": response.text,
        "raw": response.raw,
    }
    if request:
        payload["request"] = request
    if effective_extra:
        payload["extra"] = effective_extra
    if system_text or non_system:
        payload["prompt"] = {
            "system": system_text,
            "messages": non_system,
        }
    log_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    try:
        _write_pretty_text_log(log_path, response.text)
    except OSError:
        pass
    try:
        _write_prompt_log(log_path, system_text, non_system)
    except OSError:
        pass
    return log_path

def log_llm_error(
    workspace: Path,
    label: str,
    error: LLMRequestError,
    request: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
    messages: Optional[list[Message]] = None,
) -> Path:
    effective_extra = _effective_extra(extra)
    log_path = llm_log_path(workspace, label=label, extra=effective_extra)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    system_text = ""
    non_system: list[Message] = []
    if messages:
        system_text, non_system = _split_prompt_messages(messages)
    payload: Dict[str, Any] = {
        "label": label,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "error": _format_error_payload(error),
        "raw": error.raw_response,
    }
    if request:
        payload["request"] = request
    if effective_extra:
        payload["extra"] = effective_extra
    if system_text or non_system:
        payload["prompt"] = {
            "system": system_text,
            "messages": non_system,
        }
    log_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    try:
        _write_error_text_log(log_path, error)
    except OSError:
        pass
    try:
        _write_prompt_log(log_path, system_text, non_system)
    except OSError:
        pass
    return log_path
