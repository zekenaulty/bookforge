from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.llm.client import LLMClient
from bookforge.llm.types import Message
from bookforge.pipeline.config import _continuity_max_tokens
from bookforge.pipeline.durable import _durable_state_context
from bookforge.pipeline.io import _log_scope
from bookforge.pipeline.llm_ops import _chat
from bookforge.pipeline.parse import _extract_json
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.state_apply import _summary_from_state, _summary_list
from bookforge.prompt.renderer import render_template_file


def _generate_continuity_pack(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
    durable_expand_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    continuity_template = _resolve_template(book_root, "continuity_pack.md")
    system_prompt = _system_prompt_for_phase(system_path, book_root / "outline" / "outline.json", "continuity_pack")

    summary = _summary_from_state(state)
    recent_facts = _summary_list(summary.get("key_facts_ring", []))
    durable = _durable_state_context(book_root, state, scene_card, durable_expand_ids)

    message = render_template_file(
        continuity_template,
        {
            "scene_card": scene_card,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "state": state,
            "summary": summary,
            "recent_facts": recent_facts,
            "item_registry": durable.get("item_registry", {}),
            "plot_devices": durable.get("plot_devices", {}),
        },
    )

    response = _chat(
        workspace,
        "continuity_pack",
        client,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        model=model,
        temperature=0.2,
        max_tokens=_continuity_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    raw = response.text or ""
    pack = _extract_json(raw)
    if pack is None:
        raise ValueError("No JSON object found in response.")
    if not isinstance(pack, dict):
        raise ValueError("Continuity pack must be a JSON object.")
    return pack
