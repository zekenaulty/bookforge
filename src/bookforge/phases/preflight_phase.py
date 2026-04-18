from __future__ import annotations

from typing import Any, Dict, List, Optional

from bookforge.llm.client import LLMClient
from bookforge.llm.logging import prior_response_content_array_metadata
from bookforge.llm.types import Message
from bookforge.pipeline.config import _preflight_max_tokens
from bookforge.pipeline.llm_ops import _chat, _json_retry_count
from bookforge.pipeline.parse import _extract_json
from bookforge.pipeline.thinking import resolve_turn_thinking_level
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.io import _log_scope
from bookforge.prompt.renderer import render_template_file
from bookforge.pipeline.state_patch import _normalize_state_patch_for_validation, _sanitize_preflight_patch
from bookforge.util.schema import validate_json


def _scene_state_preflight(
    workspace: Any,
    book_root: Any,
    system_path: Any,
    scene_card: Dict[str, Any],
    state: Dict[str, Any],
    outline: Dict[str, Any],
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
    durable_expand_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    preflight_template = _resolve_template(book_root, "preflight.md")
    system_prompt = _system_prompt_for_phase(system_path, book_root / "outline" / "outline.json", "preflight")

    message = render_template_file(
        preflight_template,
        {
            "scene_card": scene_card,
            "state": state,
            "summary": state.get("summary", {}),
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "outline": outline,
            "chapter_order": chapter_order,
            "scene_counts": scene_counts,
        },
    )

    base_messages: List[Message] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]
    log_extra = _log_scope(book_root, scene_card)
    log_extra = {**log_extra, "phase_id": "preflight"}
    t1_level = resolve_turn_thinking_level("preflight", "T1")
    t2_level = resolve_turn_thinking_level("preflight", "T2")

    t1_parts: Optional[List[Dict[str, Any]]] = None
    t1_retry_message: Optional[str] = None
    t1_attempt = 0
    while True:
        t1_messages = list(base_messages)
        t1_messages.append({
            "role": "user",
            "content": (
                "THINKING PHASE: Analyze the scene state alignment. "
                "Do NOT output the state patch JSON. Return ONLY a small JSON object: "
                "{\"status\":\"ready_to_execute\",\"notes\":[],\"warnings\":[],\"edge_count\":0}."
            ),
        })
        if t1_retry_message:
            t1_messages.append({"role": "user", "content": t1_retry_message})
        response = _chat(
            workspace,
            "preflight_t1",
            client,
            t1_messages,
            model=model,
            temperature=0.2,
            max_tokens=_preflight_max_tokens(),
            thinking_level=t1_level,
            log_extra={**log_extra, "turn_id": "T1"},
        )
        try:
            _extract_json(response.text or "")
            t1_parts = response.assistant_parts if isinstance(response.assistant_parts, list) else None
            break
        except Exception:
            t1_attempt += 1
            if t1_attempt > _json_retry_count():
                raise
            t1_retry_message = "Return ONLY the ready JSON object. No prose, no markdown, no commentary."

    t2_retry_message: Optional[str] = None
    t2_attempt = 0
    while True:
        t2_messages = list(base_messages)
        if t1_parts and str(getattr(client, "provider", "")).lower() == "gemini":
            t2_messages.append({"role": "assistant", "parts": t1_parts})
        t2_log_extra = {
            **log_extra,
            "turn_id": "T2",
            **prior_response_content_array_metadata(t1_parts),
        }
        t2_messages.append({
            "role": "user",
            "content": (
                "EXECUTION PHASE: Emit the state_patch JSON only. "
                "Do NOT include analysis or planning text. Output JSON only."
            ),
        })
        if t2_retry_message:
            t2_messages.append({"role": "user", "content": t2_retry_message})
        response = _chat(
            workspace,
            "preflight",
            client,
            t2_messages,
            model=model,
            temperature=0.2,
            max_tokens=_preflight_max_tokens(),
            thinking_level=t2_level,
            log_extra=t2_log_extra,
        )
        raw = response.text or ""
        patch = _extract_json(raw)
        if patch is not None:
            break
        t2_attempt += 1
        if t2_attempt > _json_retry_count():
            raise ValueError("No JSON object found in response.")
        t2_retry_message = "Return ONLY the JSON object. No prose, no markdown, no commentary."

    patch = _normalize_state_patch_for_validation(patch, scene_card)
    validate_json(patch, "state_patch")
    patch = _sanitize_preflight_patch(patch, scene_card)

    return patch

