from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import re

from bookforge.llm.client import LLMClient
from bookforge.llm.types import Message
from bookforge.pipeline.config import _lint_max_tokens, _lint_mode
from bookforge.pipeline.durable import _durable_state_context
from bookforge.pipeline.io import _log_scope
from bookforge.pipeline.lint import _stat_mismatch_issues, _pov_drift_issues, _heuristic_invariant_issues, _durable_scene_constraint_issues, _linked_durable_consistency_issues, _merged_character_states_for_lint, _post_state_with_character_continuity, _normalize_lint_report, _ui_gate_issues, _internal_id_issues
from bookforge.pipeline.llm_ops import _chat, _json_retry_count, _lint_status_from_issues
from bookforge.pipeline.parse import _extract_authoritative_surfaces, _extract_json
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.continuity import _global_continuity_stats
from bookforge.pipeline.state_apply import _summary_from_state
from bookforge.prompt.renderer import render_template_file
from bookforge.util.schema import validate_json




def _invariant_conflict_issue(post_invariants: List[str], character_states: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(post_invariants, list) or not post_invariants:
        return None
    state_map: Dict[str, Dict[str, Any]] = {}
    subjects: List[str] = []
    for state in character_states:
        if not isinstance(state, dict):
            continue
        name = str(state.get("name") or "").strip()
        cid = str(state.get("character_id") or "").strip()
        if name:
            state_map[name.lower()] = state
            subjects.append(name)
        if cid:
            state_map[cid.lower()] = state
            if cid not in subjects:
                subjects.append(cid)
    single_subject = subjects[0] if len(subjects) == 1 else None

    def _subject_for_line(line: str) -> Optional[str]:
        lowered = line.lower()
        for state in character_states:
            if not isinstance(state, dict):
                continue
            name = str(state.get("name") or "").strip()
            cid = str(state.get("character_id") or "").strip()
            if name and name.lower() in lowered:
                return name
            if cid and cid.lower() in lowered:
                return cid
        return single_subject

    def _state_for_subject(subject: Optional[str]) -> Optional[Dict[str, Any]]:
        if not subject:
            return None
        return state_map.get(subject.lower())

    def _stats_for_state(state: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(state, dict):
            return {}
        stats = state.get("stats")
        if not isinstance(stats, dict):
            stats = state.get("character_continuity_system_state", {}).get("stats")
        return stats if isinstance(stats, dict) else {}

    def _extract_state_hp(state: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not state:
            return None
        stats = _stats_for_state(state)
        hp = stats.get("hp")
        if isinstance(hp, dict):
            current = hp.get("current")
            maximum = hp.get("max")
            if current is None:
                current = hp.get("value")
            if maximum is None:
                maximum = hp.get("maximum")
            if current is None and maximum is None:
                return None
            return {"current": current, "max": maximum}
        if hp is None:
            return None
        return {"current": hp, "max": None}

    def _extract_state_crit(state: Optional[Dict[str, Any]]) -> Optional[Any]:
        if not state:
            return None
        stats = _stats_for_state(state)
        for key in ("crit_rate", "critical_rate", "crit", "criticality"):
            if key not in stats:
                continue
            value = stats.get(key)
            if isinstance(value, dict):
                value = value.get("value", value.get("current"))
            return value
        return None

    hp_values: Dict[str, set] = {}
    crit_values: Dict[str, set] = {}

    for idx, raw in enumerate(post_invariants, start=1):
        if not isinstance(raw, str):
            continue
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith("REMOVE:"):
            continue
        subject = _subject_for_line(line)
        if not subject:
            continue
        state = _state_for_subject(subject)

        hp_match = re.search(r"(?i)\bHP\b[^0-9]*(\d+)\s*/\s*(\d+)", line)
        if hp_match:
            current = int(hp_match.group(1))
            maximum = int(hp_match.group(2))
            seen = hp_values.setdefault(subject, set())
            value = f"{current}/{maximum}"
            if seen and value not in seen:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"Conflicting HP invariants detected for {subject} (multiple HP values in must_stay_true).",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }
            seen.add(value)
            state_hp = _extract_state_hp(state)
            if state_hp is None:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"State snapshot for {subject} lacks HP stats while must_stay_true declares HP {value}.",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }
            if state_hp.get("current") != current or (state_hp.get("max") is not None and state_hp.get("max") != maximum):
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"State snapshot for {subject} disagrees with must_stay_true HP {value}.",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }
            continue

        hp_match = re.search(r"(?i)\bHP\b[^0-9]*(\d+)", line)
        if hp_match:
            current = int(hp_match.group(1))
            seen = hp_values.setdefault(subject, set())
            value = str(current)
            if seen and value not in seen:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"Conflicting HP invariants detected for {subject} (multiple HP values in must_stay_true).",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }
            seen.add(value)
            state_hp = _extract_state_hp(state)
            if state_hp is None:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"State snapshot for {subject} lacks HP stats while must_stay_true declares HP {value}.",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }
            if state_hp.get("current") != current:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"State snapshot for {subject} disagrees with must_stay_true HP {value}.",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }

        crit_match = re.search(r"(?i)\bcrit(?:ical)?\s*rate\b[^0-9]*(\d+)", line)
        if crit_match:
            value = int(crit_match.group(1))
            seen = crit_values.setdefault(subject, set())
            if seen and value not in seen:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"Conflicting Crit Rate invariants detected for {subject} (multiple values in must_stay_true).",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }
            seen.add(value)
            state_crit = _extract_state_crit(state)
            if state_crit is None:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"State snapshot for {subject} lacks Crit Rate while must_stay_true declares {value}%.",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }
            try:
                state_val = int(state_crit)
            except (TypeError, ValueError):
                state_val = state_crit
            if state_val != value:
                return {
                    "code": "pipeline_state_incoherent",
                    "message": f"State snapshot for {subject} disagrees with must_stay_true Crit Rate {value}%.",
                    "severity": "error",
                    "evidence": {"line": idx, "excerpt": line},
                }

    return None


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
    appearance_check = patch.get("_appearance_check", {})
    lint_character_states = _merged_character_states_for_lint(character_states, patch)
    lint_post_state = _post_state_with_character_continuity(post_state, lint_character_states)
    durable_post = _durable_state_context(book_root, post_state, scene_card, durable_expand_ids)
    authoritative_surfaces = _extract_authoritative_surfaces(prose)
    prompt = render_template_file(
        template,
        {
            "prose": prose,
            "pre_state": pre_state,
            "post_state": lint_post_state,
            "pre_summary": _summary_from_state(pre_state),
            "post_summary": _summary_from_state(lint_post_state),
            "pre_invariants": pre_invariants,
            "post_invariants": post_invariants,
            "authoritative_surfaces": authoritative_surfaces,
            "scene_card": scene_card,
            "appearance_check": appearance_check,
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

    incoherent_issue = _invariant_conflict_issue(post_invariants, lint_character_states)
    if incoherent_issue:
        report["issues"] = [incoherent_issue]
        report["status"] = "fail"
        validate_json(report, "lint_report")
        return report

    heuristic_issues = _stat_mismatch_issues(
        prose,
        lint_character_states,
        _global_continuity_stats(post_state),
        authoritative_surfaces=authoritative_surfaces,
    )
    extra_issues = _pov_drift_issues(prose, pov, strict=_lint_mode() == "strict")
    durable_issues = _durable_scene_constraint_issues(prose, scene_card, durable_post)
    durable_issues += _linked_durable_consistency_issues(durable_post)
    ui_gate_issues = _ui_gate_issues(scene_card, authoritative_surfaces, prose, strict=_lint_mode() == "strict")
    internal_id_issues = _internal_id_issues(prose, strict=_lint_mode() == "strict")
    combined = heuristic_issues + extra_issues + durable_issues + ui_gate_issues + internal_id_issues
    if combined:
        report["issues"] = list(report.get("issues", [])) + combined
        report["status"] = _lint_status_from_issues(report.get("issues", []))
        report.setdefault("mode", "heuristic")
    else:
        report["status"] = _lint_status_from_issues(report.get("issues", []))
    for issue in report.get("issues", []):
        if isinstance(issue, dict) and str(issue.get("code") or "").strip() == "pipeline_state_incoherent":
            report["issues"] = [issue]
            report["status"] = "fail"
            break
    validate_json(report, "lint_report")
    return report







