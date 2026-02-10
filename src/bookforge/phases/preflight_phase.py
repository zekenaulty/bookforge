from __future__ import annotations

from typing import Any, Dict, List

from bookforge.llm.client import LLMClient
from bookforge.memory.durable_state import load_item_registry, load_plot_devices
from bookforge.pipeline.config import _durable_slice_max_expansions, _preflight_max_tokens
from bookforge.pipeline.durable import _durable_state_context, _apply_durable_state_updates
from bookforge.pipeline.io import _snapshot_character_states_before_preflight
from bookforge.pipeline.llm_ops import _chat
from bookforge.pipeline.parse import _extract_json
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.io import _log_scope
from bookforge.prompt.renderer import render_template_file
from bookforge.pipeline.state_patch import _normalize_state_patch_for_validation, _sanitize_preflight_patch
from bookforge.pipeline.log import _status
from bookforge.util.schema import validate_json


def _scene_state_preflight(
    client: LLMClient,
    book_root: Any,
    scene_card: Dict[str, Any],
    continuity_pack: Dict[str, Any],
    character_states: List[Dict[str, Any]],
    state: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    item_registry: Dict[str, Any],
    plot_devices: Dict[str, Any],
    lint_mode: str,
) -> Dict[str, Any]:
    preflight_template = _resolve_template(book_root, "preflight")
    system_prompt = _system_prompt_for_phase(book_root, "preflight")

    message = render_template_file(
        preflight_template,
        {
            "scene_card": scene_card,
            "continuity_pack": continuity_pack,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
            "state": state,
            "summary": state.get("summary", {}),
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
        max_tokens=_preflight_max_tokens(),
        phase="preflight",
        scope=_log_scope(book_root, state),
    )

    raw = response.text or ""
    patch = _extract_json(raw)
    if patch is None:
        raise ValueError("No JSON object found in response.")

    patch = _normalize_state_patch_for_validation(patch)
    validate_json("state_patch", patch)
    patch = _sanitize_preflight_patch(patch)

    snapshot_count = _snapshot_character_states_before_preflight(book_root, state, character_states)
    _status(f"Character state snapshots written: {snapshot_count}")

    preflight_item_registry = load_item_registry(book_root)
    preflight_plot_devices = load_plot_devices(book_root)
    preflight_durable = _durable_state_context(
        preflight_item_registry,
        preflight_plot_devices,
        scene_card=scene_card,
        item_registry=item_registry,
        plot_devices=plot_devices,
        max_expand=_durable_slice_max_expansions(),
    )

    _apply_durable_state_updates(
        book_root,
        patch,
        preflight_durable,
        scene_card,
        state,
        character_states,
        lint_mode=lint_mode,
        phase="preflight",
    )

    _status("Preflight alignment complete OK")

    return patch


