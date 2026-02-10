from __future__ import annotations

from typing import Any, Dict, List

from bookforge.llm.client import LLMClient
from bookforge.pipeline.config import _continuity_max_tokens
from bookforge.pipeline.llm_ops import _chat
from bookforge.pipeline.parse import _extract_json
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.io import _log_scope
from bookforge.prompt.renderer import render_template_file
from bookforge.pipeline.log import _status


def _generate_continuity_pack(
    client: LLMClient,
    book_root: Any,
    scene_card: Dict[str, Any],
    state: Dict[str, Any],
    continuity_pack: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    item_registry: Dict[str, Any],
    plot_devices: Dict[str, Any],
) -> Dict[str, Any]:
    continuity_template = _resolve_template(book_root, "continuity_pack")
    system_prompt = _system_prompt_for_phase(book_root, "continuity")

    message = render_template_file(
        continuity_template,
        {
            "scene_card": scene_card,
            "state": state,
            "summary": state.get("summary", {}),
            "continuity_pack": continuity_pack,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "item_registry": item_registry,
            "plot_devices": plot_devices,
        },
    )

    response = _chat(
        client,
        [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        max_tokens=_continuity_max_tokens(),
        phase="continuity_pack",
        scope=_log_scope(book_root, state),
    )

    raw = response.text or ""
    patch = _extract_json(raw)
    if patch is None:
        raise ValueError("No JSON object found in response.")

    if not isinstance(patch, dict):
        raise ValueError("Continuity pack must be a JSON object.")

    _status("Continuity pack ready OK")

    return patch

