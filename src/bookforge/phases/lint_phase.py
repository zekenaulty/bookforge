from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.llm.client import LLMClient
from bookforge.llm.types import Message
from bookforge.pipeline.config import _lint_max_tokens, _lint_mode
from bookforge.pipeline.durable import _durable_state_context
from bookforge.pipeline.io import _log_scope
from bookforge.pipeline.lint import _stat_mismatch_issues, _pov_drift_issues, _heuristic_invariant_issues, _durable_scene_constraint_issues, _linked_durable_consistency_issues, _merged_character_states_for_lint, _normalize_lint_report
from bookforge.pipeline.llm_ops import _chat, _json_retry_count, _lint_status_from_issues
from bookforge.pipeline.parse import _extract_authoritative_surfaces, _extract_json
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.continuity import _global_continuity_stats
from bookforge.pipeline.state_apply import _summary_from_state
from bookforge.prompt.renderer import render_template_file
from bookforge.util.schema import validate_json


def _lint_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    pre_state: Dict[str, Any],
    post_state: Dict[str, Any],
    patch: Dict[str, Any],
    scene_card: Dict[str, Any],
    pre_invariants: List[str],
    post_invariants: List[str],
    character_states: List[Dict[str, Any]],
    pov: Optional[str],
    client: LLMClient,
    model: str,
    durable_expand_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if not isinstance(pre_state, dict):
        pre_state = {}
    if not isinstance(post_state, dict):
        post_state = {}
    if not isinstance(patch, dict):
        patch = {}
    if not isinstance(scene_card, dict):
        scene_card = {}
    if not isinstance(character_states, list):
        character_states = []
    template = _resolve_template(book_root, "lint.md")
    lint_character_states = _merged_character_states_for_lint(character_states, patch)
    durable_post = _durable_state_context(book_root, post_state, scene_card, durable_expand_ids)
    authoritative_surfaces = _extract_authoritative_surfaces(prose)
    prompt = render_template_file(
        template,
        {
            "prose": prose,
            "pre_state": pre_state,
            "post_state": post_state,
            "pre_summary": _summary_from_state(pre_state),
            "post_summary": _summary_from_state(post_state),
            "pre_invariants": pre_invariants,
            "post_invariants": post_invariants,
            "authoritative_surfaces": authoritative_surfaces,
            "item_registry": durable_post.get("item_registry", {}),
            "plot_devices": durable_post.get("plot_devices", {}),
            "character_states": lint_character_states,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": _system_prompt_for_phase(system_path, book_root / "outline" / "outline.json", "lint")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "lint_scene",
        client,
        messages,
        model=model,
        temperature=0.0,
        max_tokens=_lint_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    retries = _json_retry_count()
    attempt = 0
    while True:
        try:
            report = _extract_json(response.text)
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
                f"lint_scene_json_retry{attempt + 1}",
                client,
                retry_messages,
                model=model,
                temperature=0.0,
                max_tokens=_lint_max_tokens(),
                log_extra=_log_scope(book_root, scene_card),
            )
            attempt += 1

    if not isinstance(report, dict):
        raise ValueError("Lint output must be a JSON object.")

    report = _normalize_lint_report(report)

    heuristic_issues = _stat_mismatch_issues(
        prose,
        lint_character_states,
        _global_continuity_stats(post_state),
        authoritative_surfaces=authoritative_surfaces,
    )
    extra_issues = _pov_drift_issues(prose, pov, strict=_lint_mode() == "strict")
    durable_issues = _durable_scene_constraint_issues(prose, scene_card, durable_post)
    durable_issues += _linked_durable_consistency_issues(durable_post)
    combined = heuristic_issues + extra_issues + durable_issues
    if combined:
        report["issues"] = list(report.get("issues", [])) + combined
        report["status"] = _lint_status_from_issues(report.get("issues", []))
        report.setdefault("mode", "heuristic")
    else:
        report["status"] = _lint_status_from_issues(report.get("issues", []))
    validate_json(report, "lint_report")
    return report







