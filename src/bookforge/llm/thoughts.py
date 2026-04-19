from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from bookforge.config.env import load_config
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_response, should_log_llm
from bookforge.llm.signatures import load_signature_ledger, select_signature, load_signature_index
from bookforge.llm.storage import (
    current_thoughts_latest_path,
    current_thoughts_timestamped_path,
)
from bookforge.llm.types import Message
from bookforge.util.json_extract import extract_json


CURRENT_THOUGHTS_SYSTEM = (
    "You are a reflective assistant. Return a concise JSON summary of your current context. "
    "Use the provided schema only."
)

CUSTOM_THOUGHTS_SYSTEM = (
    "You are a reflective assistant. Reconstruct working context from the provided reasoning seed. "
    "Follow the user's instruction exactly. If the user asks for JSON, return JSON only."
)

CURRENT_THOUGHTS_USER = (
    "Reconstruct your current working context and provide a JSON object with:\n"
    "current_objectives, active_constraints, recent_decisions, assumptions, "
    "open_questions, recommended_next_steps.\n"
    "Use arrays of short strings. Output JSON only."
)


def _load_assistant_parts(workspace: Path, record: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    path_value = record.get("assistant_parts_path")
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = (workspace / path).resolve()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, list) else None


def _build_messages(
    provider: str,
    assistant_parts: Optional[List[Dict[str, Any]]],
    *,
    system_prompt: str,
    user_prompt: str,
) -> List[Message]:
    messages: List[Message] = [
        {"role": "system", "content": system_prompt},
    ]
    if assistant_parts and provider == "gemini":
        messages.append({"role": "assistant", "parts": assistant_parts})
    messages.append({"role": "user", "content": user_prompt})
    return messages


def format_thought_response(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    try:
        payload = extract_json(raw, label="Current thoughts response", require_object=False)
    except Exception:
        try:
            payload = json.loads(raw)
        except Exception:
            return raw
    return json.dumps(payload, ensure_ascii=True, indent=2)


def list_signatures(
    workspace: Path,
    *,
    book_id: Optional[str] = None,
    phase_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    records = load_signature_ledger(workspace, limit=None)
    filtered: List[Dict[str, Any]] = []
    for record in records:
        if book_id and str(record.get("book_id") or "") != str(book_id):
            continue
        if phase_id and str(record.get("phase_id") or "") != str(phase_id):
            continue
        if turn_id and str(record.get("turn_id") or "") != str(turn_id):
            continue
        if chapter_id and str(record.get("chapter_id") or "") != str(chapter_id):
            continue
        filtered.append(record)
    if limit and limit > 0:
        return filtered[-limit:]
    return filtered


def run_current_thoughts(
    workspace: Path,
    *,
    model_phase: str = "planner",
    signature_id: Optional[str] = None,
    phase_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    book_id: Optional[str] = None,
    use_global_author: bool = False,
    user_prompt: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.2,
    thinking_level: Optional[str] = None,
) -> Dict[str, Any]:
    config = load_config()
    client = get_llm_client(config, phase=model_phase)
    model = resolve_model(model_phase, config)
    selected = select_signature(
        workspace,
        signature_id=signature_id,
        phase_id=phase_id,
        turn_id=turn_id,
        chapter_id=chapter_id,
        book_id=book_id,
        global_author=use_global_author,
    )
    if not selected:
        index_payload = load_signature_index(workspace)
        active = index_payload.get("latest")
        if isinstance(active, dict):
            selected = active
    assistant_parts = _load_assistant_parts(workspace, selected) if selected else None
    prompt_text = str(user_prompt or CURRENT_THOUGHTS_USER).strip() or CURRENT_THOUGHTS_USER
    system_text = CUSTOM_THOUGHTS_SYSTEM if user_prompt else CURRENT_THOUGHTS_SYSTEM
    messages = _build_messages(
        str(client.provider).lower(),
        assistant_parts,
        system_prompt=system_text,
        user_prompt=prompt_text,
    )
    response = client.chat(
        messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        thinking_level=thinking_level,
    )
    log_extra: Dict[str, Any] = {
        "phase_id": "current_thoughts",
    }
    if selected:
        log_extra["signature_id"] = selected.get("signature_id")
        log_extra["signature_scope"] = selected.get("scope")
    if should_log_llm():
        selected_book_id = selected.get("book_id") if isinstance(selected, dict) else None
        selected_chapter_id = selected.get("chapter_id") if isinstance(selected, dict) else None
        selected_scene_id = selected.get("scene_id") if isinstance(selected, dict) else None
        if selected_book_id:
            log_extra["book_id"] = selected_book_id
        if selected_chapter_id is not None:
            log_extra["chapter"] = selected_chapter_id
        if selected_scene_id is not None:
            log_extra["scene"] = selected_scene_id
        log_llm_response(
            workspace,
            "current_thoughts",
            response,
            request={
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "thinking_level": thinking_level,
                "user_prompt": prompt_text,
            },
            messages=messages,
            extra=log_extra,
        )
    selected_book_id = selected.get("book_id") if isinstance(selected, dict) else None
    selected_chapter_id = selected.get("chapter_id") if isinstance(selected, dict) else None
    latest_path = current_thoughts_latest_path(workspace)
    history_path = current_thoughts_timestamped_path(
        workspace,
        book_id=selected_book_id,
        chapter_id=selected_chapter_id,
    )
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "current_thoughts_v1",
        "model": model,
        "provider": client.provider,
        "signature_id": selected.get("signature_id") if selected else None,
        "book_id": selected_book_id,
        "chapter_id": selected_chapter_id,
        "prompt_text": prompt_text,
        "response_text": response.text,
        "formatted_response_text": format_thought_response(response.text),
    }
    latest_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    history_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return {
        "output_path": latest_path,
        "history_path": history_path,
        "response_text": response.text,
        "formatted_text": format_thought_response(response.text),
        "signature_id": selected.get("signature_id") if isinstance(selected, dict) else None,
        "prompt_text": prompt_text,
    }
