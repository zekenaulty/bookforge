from __future__ import annotations

from typing import Any, Dict, List, Optional

from bookforge.pipeline.llm_ops import _lint_status_from_issues
from bookforge.pipeline.state_apply import _ensure_character_continuity_system_state, _apply_bag_updates, _summary_list, _split_invariant_removals, _apply_invariant_removals, _canonical_inventory_invariants, _reconcile_inventory_invariants
from bookforge.pipeline.state_patch import _coerce_character_updates, _coerce_stat_updates


def _normalize_lint_report(report: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(report)
    if "schema_version" not in normalized:
        normalized["schema_version"] = "1.0"

    status = normalized.get("status")
    if not status:
        passed = normalized.get("pass")
        if isinstance(passed, bool):
            normalized["status"] = "pass" if passed else "fail"

    issues: List[Dict[str, Any]] = []
    raw_issues = normalized.get("issues")
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if isinstance(item, dict) and item.get("message"):
                issues.append(item)
            elif item is not None:
                issues.append({"code": "issue", "message": str(item)})

    violations = normalized.get("violations")
    if isinstance(violations, list):
        for item in violations:
            if item is not None:
                issues.append({"code": "violation", "message": str(item), "severity": "error"})

    warnings = normalized.get("warnings")
    if isinstance(warnings, list):
        for item in warnings:
            if item is not None:
                issues.append({"code": "warning", "message": str(item), "severity": "warning"})

    if not isinstance(normalized.get("issues"), list) or issues:
        normalized["issues"] = issues

    for issue in normalized.get("issues", []):
        if isinstance(issue, dict) and not issue.get("severity"):
            issue["severity"] = "warning"

    normalized["status"] = _lint_status_from_issues(normalized.get("issues", []))

    if "status" not in normalized or not normalized.get("status"):
        normalized["status"] = "fail" if normalized.get("issues") else "pass"

    return normalized


def _merged_character_states_for_lint(
    character_states: List[Dict[str, Any]],
    patch: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not isinstance(patch, dict):
        patch = {}
    _coerce_character_updates(patch)
    _coerce_stat_updates(patch)

    updates = patch.get("character_updates", [])
    if not isinstance(updates, list):
        updates = []

    stat_updates = patch.get("character_stat_updates", [])
    if not isinstance(stat_updates, list):
        stat_updates = []

    continuity_updates = patch.get("character_continuity_system_updates", [])
    if not isinstance(continuity_updates, list):
        continuity_updates = []

    summary_removals: List[str] = []
    summary_inventory_canonical: Dict[tuple[str, str], Dict[str, str]] = {}
    summary_update = patch.get("summary_update")
    if isinstance(summary_update, dict):
        must_stay_true = _summary_list(summary_update.get("must_stay_true"))
        summary_removals, summary_additions = _split_invariant_removals(must_stay_true)
        summary_inventory_canonical = _canonical_inventory_invariants(summary_additions)

    merged = []
    for state in character_states:
        if not isinstance(state, dict):
            continue
        merged_state = dict(state)
        char_id = str(merged_state.get("character_id") or "")
        if not char_id:
            merged.append(merged_state)
            continue

        for update in updates:
            if not isinstance(update, dict):
                continue
            if str(update.get("character_id") or "") != char_id:
                continue
            for key, value in update.items():
                if key in {"character_id", "reason", "reason_category", "notes"}:
                    continue
                if key == "inventory" and isinstance(value, list):
                    merged_state["inventory"] = value
                elif key == "containers" and isinstance(value, list):
                    merged_state["containers"] = value
                elif key == "persona_updates" and isinstance(value, list):
                    merged_state["persona_updates"] = value
                elif key == "invariants_add" and isinstance(value, list):
                    merged_state["invariants_add"] = value
                    existing_invariants = merged_state.get("invariants", [])
                    if not isinstance(existing_invariants, list):
                        existing_invariants = []
                    combined_invariants = existing_invariants + [str(item) for item in value if str(item).strip()]
                    deduped_invariants: List[str] = []
                    seen_invariants = set()
                    for invariant in combined_invariants:
                        norm = str(invariant).strip().lower()
                        if not norm or norm in seen_invariants:
                            continue
                        seen_invariants.add(norm)
                        deduped_invariants.append(invariant)
                    merged_state["invariants"] = deduped_invariants
                elif key == "titles" and isinstance(value, list):
                    merged_state["titles"] = value
                elif key == "appearance_updates" and isinstance(value, dict):
                    current_appearance = merged_state.get("appearance_current")
                    if not isinstance(current_appearance, dict):
                        current_appearance = {}
                    set_block = value.get("set") if isinstance(value, dict) else None
                    if isinstance(set_block, dict):
                        atoms = set_block.get("atoms")
                        if isinstance(atoms, dict):
                            existing_atoms = current_appearance.get("atoms")
                            if not isinstance(existing_atoms, dict):
                                existing_atoms = {}
                            existing_atoms.update(atoms)
                            current_appearance["atoms"] = existing_atoms
                        marks = set_block.get("marks")
                        if isinstance(marks, list):
                            current_appearance["marks"] = marks
                        marks_add = set_block.get("marks_add")
                        if isinstance(marks_add, list):
                            existing_marks = current_appearance.get("marks")
                            if not isinstance(existing_marks, list):
                                existing_marks = []
                            for mark in marks_add:
                                if mark not in existing_marks:
                                    existing_marks.append(mark)
                            current_appearance["marks"] = existing_marks
                        alias_map = set_block.get("alias_map")
                        if isinstance(alias_map, dict):
                            current_appearance["alias_map"] = alias_map
                    merged_state["appearance_current"] = current_appearance
                else:
                    merged_state[key] = value

        for update in stat_updates:
            if not isinstance(update, dict):
                continue
            if str(update.get("character_id") or "") != char_id:
                continue
            set_block = update.get("set")
            delta_block = update.get("delta")
            if set_block is None and delta_block is None:
                continue
            stats = merged_state.get("stats")
            if not isinstance(stats, dict):
                stats = {}
            if isinstance(set_block, dict):
                stats.update(set_block)
            if isinstance(delta_block, dict):
                for key, value in delta_block.items():
                    try:
                        stats[key] = (stats.get(key) or 0) + value
                    except TypeError:
                        stats[key] = value
            merged_state["stats"] = stats

        continuity = _ensure_character_continuity_system_state(merged_state)
        for update in continuity_updates:
            if not isinstance(update, dict):
                continue
            if str(update.get("character_id") or "") != char_id:
                continue
            _apply_bag_updates(continuity, update)
        merged_state["character_continuity_system_state"] = continuity
        _ensure_character_continuity_system_state(merged_state)

        existing_invariants = merged_state.get("invariants", [])
        if isinstance(existing_invariants, list):
            if summary_removals:
                existing_invariants = _apply_invariant_removals(existing_invariants, summary_removals)
            if summary_inventory_canonical:
                subject_tokens = {char_id.lower()}
                state_name = str(merged_state.get("name") or "").strip().lower()
                if state_name:
                    subject_tokens.add(state_name)
                canonical_for_character = {
                    key: value
                    for key, value in summary_inventory_canonical.items()
                    if key[0] in subject_tokens
                }
                if canonical_for_character:
                    existing_invariants = _reconcile_inventory_invariants(
                        existing_invariants,
                        canonical_for_character,
                        merged_state.get("inventory"),
                        merged_state.get("containers"),
                    )
            merged_state["invariants"] = existing_invariants

        merged.append(merged_state)

    return merged


def _post_state_with_character_continuity(
    post_state: Dict[str, Any],
    character_states: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not isinstance(post_state, dict):
        post_state = {}
    if not isinstance(character_states, list):
        return dict(post_state)

    continuity_map: Dict[str, Dict[str, Any]] = {}
    for state in character_states:
        if not isinstance(state, dict):
            continue
        char_id = str(state.get("character_id") or "").strip()
        continuity = state.get("character_continuity_system_state")
        if not char_id or not isinstance(continuity, dict):
            continue
        continuity_map[char_id] = continuity

    if not continuity_map:
        return dict(post_state)

    merged = dict(post_state)
    continuity_system = merged.get("continuity_system")
    if not isinstance(continuity_system, dict):
        continuity_system = {}
    else:
        continuity_system = dict(continuity_system)
    continuity_system["characters"] = continuity_map
    merged["continuity_system"] = continuity_system
    return merged

