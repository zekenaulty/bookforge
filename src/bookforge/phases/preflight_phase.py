from __future__ import annotations

from typing import Any, Dict, List, Optional

from bookforge.llm.client import LLMClient
from bookforge.pipeline.config import _preflight_max_tokens
from bookforge.pipeline.llm_ops import _chat
from bookforge.pipeline.parse import _extract_json
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

    response = _chat(
        workspace,
        "preflight",
        client,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        model=model,
        temperature=0.2,
        max_tokens=_preflight_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    raw = response.text or ""
    patch = _extract_json(raw)
    if patch is None:
        raise ValueError("No JSON object found in response.")

    patch = _normalize_state_patch_for_validation(patch, scene_card)
    validate_json(patch, "state_patch")
    patch = _sanitize_preflight_patch(patch)

    return patch
