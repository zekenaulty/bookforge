from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.llm.client import LLMClient
from bookforge.llm.types import Message
from bookforge.pipeline.config import _state_repair_max_tokens
from bookforge.pipeline.durable import _durable_state_context
from bookforge.pipeline.appearance import _with_derived_attire
from bookforge.pipeline.io import _log_scope
from bookforge.pipeline.llm_ops import _chat, _json_retry_count, _state_patch_schema_retry_message
from bookforge.pipeline.parse import _extract_json
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.state_apply import _summary_from_state
from bookforge.pipeline.state_patch import _normalize_state_patch_for_validation
from bookforge.prompt.renderer import render_template_file
from bookforge.util.schema import validate_json


def _state_repair(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    continuity_pack: Dict[str, Any],
    draft_patch: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
    durable_expand_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "state_repair.md")
    durable = _durable_state_context(book_root, state, scene_card, durable_expand_ids)
    derived_character_states = _with_derived_attire(character_states, durable.get("item_registry", {}))
    prompt = render_template_file(
        template,
        {
            "prose": prose,
            "state": state,
            "summary": _summary_from_state(state),
            "scene_card": scene_card,
            "continuity_pack": continuity_pack,
            "draft_patch": draft_patch,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": derived_character_states,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": _system_prompt_for_phase(system_path, book_root / "outline" / "outline.json", "state_repair")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "state_repair",
        client,
        messages,
        model=model,
        temperature=0.2,
        max_tokens=_state_repair_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            patch = _extract_json(response.text)
            break
        except ValueError as exc:
            if attempt >= retries:
                raise exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return ONLY the JSON object. No prose, no markdown, no commentary.",
            })
            response = _chat(
                workspace,
                f"state_repair_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.2,
                max_tokens=_state_repair_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1
    schema_attempt = 0
    while True:
        patch = _normalize_state_patch_for_validation(patch, scene_card)
        try:
            validate_json(patch, "state_patch")
            return patch
        except ValueError as exc:
            if schema_attempt >= retries:
                raise
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": _state_patch_schema_retry_message(exc, prose_required=False),
            })
            response = _chat(
                workspace,
                f"state_repair_schema_retry{schema_attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.2,
                max_tokens=_state_repair_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            patch = _extract_json(response.text)
            schema_attempt += 1


