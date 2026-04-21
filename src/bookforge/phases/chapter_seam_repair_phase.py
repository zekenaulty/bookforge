from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.llm.client import LLMClient
from bookforge.llm.logging import prior_response_content_array_metadata
from bookforge.llm.types import Message
from bookforge.pipeline.config import _repair_max_tokens
from bookforge.pipeline.io import _log_scope
from bookforge.pipeline.llm_ops import _chat, _json_retry_count, _response_truncated
from bookforge.pipeline.parse import _extract_json
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.thinking import resolve_turn_thinking_level
from bookforge.prompt.renderer import render_template_file


def _parse_chapter_seam_repair_payload(text: str) -> Dict[str, Any]:
    payload = _extract_json(text)
    payload.setdefault("schema_version", "chapter_seam_repair_v1")
    payload.setdefault("status", "repaired")
    payload.setdefault("notes", [])
    scene_a_tail = payload.get("scene_a_tail")
    scene_b_head = payload.get("scene_b_head")
    notes = payload.get("notes")
    if not isinstance(scene_a_tail, str) or not scene_a_tail.strip():
        raise ValueError("chapter seam repair payload requires non-empty scene_a_tail.")
    if not isinstance(scene_b_head, str) or not scene_b_head.strip():
        raise ValueError("chapter seam repair payload requires non-empty scene_b_head.")
    if not isinstance(notes, list):
        raise ValueError("chapter seam repair payload notes must be an array.")
    return payload


def _repair_chapter_seam_pair(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    pair_payload: Dict[str, Any],
    issues: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "chapter_seam_repair.md")
    prompt = render_template_file(
        template,
        {
            "pair_payload": pair_payload,
            "issues": issues,
        },
    )

    chapter_id = pair_payload.get("chapter_id")
    from_scene_id = pair_payload.get("scene_a", {}).get("scene_id")
    from_scene_ref = pair_payload.get("scene_a", {}).get("scene_ref")
    to_scene_ref = pair_payload.get("scene_b", {}).get("scene_ref")
    log_extra = _log_scope(book_root, {"chapter": chapter_id, "scene": from_scene_id})
    log_extra = {
        **log_extra,
        "phase_id": "chapter_seam_repair",
        "from_scene_ref": from_scene_ref,
        "to_scene_ref": to_scene_ref,
    }

    base_messages: List[Message] = [
        {"role": "system", "content": _system_prompt_for_phase(system_path, book_root / "outline" / "outline.json", "repair")},
        {"role": "user", "content": prompt},
    ]

    t1_level = resolve_turn_thinking_level("repair", "T1")
    t2_level = resolve_turn_thinking_level("repair", "T2")

    t1_parts: Optional[List[Dict[str, Any]]] = None
    t1_retry_message: Optional[str] = None
    t1_attempt = 0
    while True:
        t1_messages = list(base_messages)
        t1_messages.append(
            {
                "role": "user",
                "content": (
                    "THINKING PHASE: Plan the seam rewrite only. "
                    "Do NOT emit the repair JSON. Return ONLY a small JSON object: "
                    "{\"status\":\"ready_to_execute\",\"notes\":[],\"warnings\":[],\"edge_count\":0}."
                ),
            }
        )
        if t1_retry_message:
            t1_messages.append({"role": "user", "content": t1_retry_message})
        response = _chat(
            workspace,
            "chapter_seam_repair_t1",
            client,
            t1_messages,
            model=model,
            temperature=0.2,
            max_tokens=_repair_max_tokens(),
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

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            t2_messages = list(base_messages)
            if t1_parts and str(getattr(client, "provider", "")).lower() == "gemini":
                t2_messages.append({"role": "assistant", "parts": t1_parts})
            t2_log_extra = {
                **log_extra,
                "turn_id": "T2",
                **prior_response_content_array_metadata(t1_parts),
            }
            t2_messages.append(
                {
                    "role": "user",
                    "content": "EXECUTION PHASE: Emit the chapter seam repair JSON only. Output JSON only.",
                }
            )
            if attempt > 0:
                t2_messages.append(
                    {
                        "role": "user",
                        "content": "Return ONLY the JSON object. No prose, no markdown, no commentary.",
                    }
                )
            response = _chat(
                workspace,
                "chapter_seam_repair",
                client,
                t2_messages,
                model=model,
                temperature=0.2,
                max_tokens=_repair_max_tokens(),
                thinking_level=t2_level,
                log_extra=t2_log_extra,
            )
            return _parse_chapter_seam_repair_payload(response.text or "")
        except ValueError as exc:
            if attempt >= retries:
                extra = ""
                if _response_truncated(response):
                    extra = " Model output hit MAX_TOKENS during chapter seam repair."
                raise ValueError(f"{exc}{extra}") from exc
            attempt += 1
