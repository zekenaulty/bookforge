from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bookforge.llm.client import LLMClient
from bookforge.llm.types import Message
from bookforge.pipeline.config import _repair_max_tokens
from bookforge.pipeline.durable import _durable_state_context
from bookforge.pipeline.io import _log_scope
from bookforge.pipeline.llm_ops import _chat, _response_truncated, _json_retry_count, _state_patch_schema_retry_message
from bookforge.pipeline.parse import _extract_prose_and_patch, _extract_appearance_check
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.state_patch import _normalize_state_patch_for_validation
from bookforge.prompt.renderer import render_template_file
from bookforge.util.schema import validate_json


def _repair_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    lint_report: Dict[str, Any],
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
    durable_expand_ids: Optional[List[str]] = None,
) -> Tuple[str, Dict[str, Any]]:
    template = _resolve_template(book_root, "repair.md")
    durable = _durable_state_context(book_root, state, scene_card, durable_expand_ids)
    prompt = render_template_file(
        template,
        {
            "issues": lint_report.get("issues", []),
            "prose": prose,
            "state": state,
            "scene_card": scene_card,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": _system_prompt_for_phase(system_path, book_root / "outline" / "outline.json", "repair")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "repair_scene",
        client,
        messages,
        model=model,
        temperature=0.4,
        max_tokens=_repair_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            prose, patch = _extract_prose_and_patch(response.text)
            appearance_check = _extract_appearance_check(response.text)
            if appearance_check:
                patch["_appearance_check"] = appearance_check
            break
        except ValueError as exc:
            if attempt >= retries:
                extra = ""
                if _response_truncated(response):
                    extra = f" Model output hit MAX_TOKENS ({_repair_max_tokens()}); increase BOOKFORGE_REPAIR_MAX_TOKENS."
                raise ValueError(f"{exc}{extra}") from exc
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": "Return PROSE plus a STATE_PATCH JSON block. Output format: PROSE: <text> then STATE_PATCH: <json>. No markdown.",
            })
            response = _chat(
                workspace,
                f"repair_scene_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.4,
                max_tokens=_repair_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1

    schema_attempt = 0
    while True:
        patch = _normalize_state_patch_for_validation(patch, scene_card)
        try:
            validate_json(patch, "state_patch")
            return prose, patch
        except ValueError as exc:
            if schema_attempt >= retries:
                raise
            retry_messages = list(messages)
            retry_messages.append({
                "role": "user",
                "content": _state_patch_schema_retry_message(exc, prose_required=True),
            })
            response = _chat(
                workspace,
                f"repair_scene_schema_retry{schema_attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.4,
                max_tokens=_repair_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            prose, patch = _extract_prose_and_patch(response.text)
            appearance_check = _extract_appearance_check(response.text)
            if appearance_check:
                patch["_appearance_check"] = appearance_check
            schema_attempt += 1

