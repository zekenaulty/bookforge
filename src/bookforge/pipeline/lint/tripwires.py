from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

from bookforge.pipeline.parse import _extract_ui_stat_lines, _strip_dialogue, _find_first_match_evidence


def _lint_issue_entries(report: Dict[str, Any], code: Optional[str] = None) -> List[Dict[str, Any]]:
    raw = report.get("issues") if isinstance(report, dict) else []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for issue in raw:
        if not isinstance(issue, dict):
            continue
        if code is not None and str(issue.get("code") or "").strip() != code:
            continue
        out.append(issue)
    return out


def _lint_has_issue_code(report: Dict[str, Any], code: str) -> bool:
    return bool(_lint_issue_entries(report, code))




def _ui_gate_issues(
    scene_card: Dict[str, Any],
    authoritative_surfaces: Optional[List[Dict[str, Any]]],
    prose: Optional[str] = None,
    *,
    strict: bool = False,
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    if not isinstance(scene_card, dict):
        return issues
    ui_allowed = scene_card.get("ui_allowed")
    ui_mechanics = scene_card.get("ui_mechanics_expected")
    if not isinstance(ui_mechanics, list):
        ui_mechanics = []

    has_ui = bool(authoritative_surfaces)
    inline_evidence = None

    def _is_ui_token(token: str) -> bool:
        inner = token.strip()[1:-1].strip() if token.startswith("[") and token.endswith("]") else token.strip()
        if not inner:
            return False
        if re.search(r"\d", inner):
            return True
        lower = inner.lower()
        keywords = (
            "system", "warning", "error", "alert", "notification", "objective", "quest", "level",
            "title", "status", "reward", "item", "inventory", "location", "map", "combat",
            "critical", "damage", "attack", "skill", "class", "rank", "stamina", "hp", "mp",
            "xp", "experience", "aggro", "cooldown", "effect", "resource"
        )
        if any(lower.startswith(key) for key in keywords):
            return True
        if ":" in inner:
            key = inner.split(":", 1)[0].strip().lower()
            if key in keywords:
                return True
        return False

    if not has_ui and prose:
        for line_no, raw_line in enumerate(str(prose).splitlines(), start=1):
            line = str(raw_line)
            for match in re.finditer(r"\[[^\[\]]+\]", line):
                token = match.group(0)
                if _is_ui_token(token):
                    inline_evidence = {"line": line_no, "excerpt": line.strip()}
                    break
            if inline_evidence:
                break

    if ui_allowed is None:
        if ui_mechanics:
            return issues
        if has_ui or inline_evidence:
            evidence = inline_evidence
            if has_ui:
                surface = authoritative_surfaces[0]
                evidence = {"line": surface.get("line"), "excerpt": surface.get("text")}
            issues.append({
                "code": "ui_gate_unknown",
                "message": "UI blocks appear but scene_card.ui_allowed is missing; set ui_allowed explicitly in the scene card.",
                "severity": "warning",
                "evidence": evidence,
            })
        return issues

    if not isinstance(ui_allowed, bool):
        ui_allowed = bool(ui_mechanics)

    if ui_allowed is False:
        if has_ui:
            surface = authoritative_surfaces[0]
            evidence = {"line": surface.get("line"), "excerpt": surface.get("text")}
            severity = "error" if strict else "warning"
            issues.append({
                "code": "ui_gate_violation",
                "message": "UI blocks appear but scene_card.ui_allowed=false. Remove UI or set ui_allowed=true when System/UI is active.",
                "severity": severity,
                "evidence": evidence,
            })
        elif inline_evidence:
            issues.append({
                "code": "ui_gate_violation",
                "message": "Inline UI-shaped token appears but scene_card.ui_allowed=false. Avoid bracketed UI in narrative prose or set ui_allowed=true when System/UI is active.",
                "severity": "warning",
                "evidence": inline_evidence,
            })

    return issues


def _internal_id_issues(prose: str, *, strict: bool = False) -> List[Dict[str, Any]]:
    if not prose:
        return []
    pattern = r"\b(?:CHAR_[A-Z0-9_]+|ITEM_[A-Z0-9_]+|THREAD_[A-Z0-9_]+|DEVICE_[A-Z0-9_]+|hand_left|hand_right)\b"
    evidence = _find_first_match_evidence(pattern, prose)
    if not evidence:
        return []
    severity = "error" if strict else "warning"
    return [{
        "code": "prose_internal_id",
        "message": "Prose includes internal id or container code; use human-readable phrasing instead.",
        "severity": severity,
        "evidence": evidence,
    }]
def _stat_mismatch_issues(
    prose: str,
    character_states: List[Dict[str, Any]],
    run_stats: Optional[Dict[str, Any]],
    authoritative_surfaces: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    if authoritative_surfaces is not None:
        ui_stat_lines = _extract_ui_stat_lines(prose, authoritative_surfaces=authoritative_surfaces)
    else:
        ui_stat_lines = _extract_ui_stat_lines(prose, authoritative_surfaces=None)

    if not ui_stat_lines:
        return issues

    def _normalize_key(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
        return cleaned.strip("_")

    def _observed_value(line: Dict[str, Any]) -> Any:
        current = line.get("current")
        maximum = line.get("max")
        if maximum is None:
            return current
        return {"current": current, "max": maximum}

    def _values_match(observed: Any, expected: Any) -> bool:
        if isinstance(expected, dict):
            if not isinstance(observed, dict):
                return False
            for key in ("current", "max", "value", "locked"):
                if key in expected and expected.get(key) != observed.get(key):
                    return False
            return True
        return observed == expected

    def _stats_for_state(state: Dict[str, Any]) -> Dict[str, Any]:
        stats = state.get("stats") if isinstance(state, dict) else None
        if not isinstance(stats, dict):
            stats = state.get("character_continuity_system_state", {}).get("stats") if isinstance(state, dict) else None
        return stats if isinstance(stats, dict) else {}

    def _owner_from_key(key: str) -> Optional[Dict[str, Any]]:
        key_lower = key.lower().strip()
        for state in character_states:
            if not isinstance(state, dict):
                continue
            name = str(state.get("name") or "").strip()
            if name and key_lower.startswith(name.lower() + " "):
                return state
            cid = str(state.get("character_id") or "").strip()
            if cid and key_lower.startswith(cid.lower() + " "):
                return state
        return None

    run_stat_map = run_stats if isinstance(run_stats, dict) else {}

    for line in ui_stat_lines:
        key_raw = str(line.get("key") or "").strip()
        if not key_raw:
            continue
        observed = _observed_value(line)
        owner_state = _owner_from_key(key_raw)
        if owner_state is not None:
            owner_name = str(owner_state.get("name") or owner_state.get("character_id") or "").strip()
            stat_key = key_raw[len(owner_name):].strip()
            stat_key = _normalize_key(stat_key)
            stats = _stats_for_state(owner_state)
            if stat_key in stats:
                expected = stats.get(stat_key)
                if not _values_match(observed, expected):
                    issues.append({
                        "code": "stat_mismatch",
                        "message": f"UI shows {key_raw}={line.get('current')}/{line.get('max')} but character state has {expected}.",
                        "severity": "warning",
                    })
            else:
                issues.append({
                    "code": "stat_unowned",
                    "message": f"UI shows {key_raw} but no matching stat exists in state.",
                    "severity": "warning",
                })
            continue

        stat_key = _normalize_key(key_raw)
        candidates: List[Dict[str, Any]] = []
        for state in character_states:
            stats = _stats_for_state(state)
            if stat_key in stats:
                candidates.append(stats)

        if len(candidates) == 0:
            if stat_key in run_stat_map:
                expected = run_stat_map.get(stat_key)
                if not _values_match(observed, expected):
                    issues.append({
                        "code": "stat_mismatch",
                        "message": f"UI shows {key_raw} but run state has {expected}.",
                        "severity": "warning",
                    })
            else:
                issues.append({
                    "code": "stat_unowned",
                    "message": f"UI shows {key_raw} but no matching stat exists in state.",
                    "severity": "warning",
                })
            continue

        if len(candidates) > 1:
            if any(_values_match(observed, cand.get(stat_key)) for cand in candidates):
                continue
            # ambiguous multi-cast without owner label: skip to avoid false positives
            continue

        expected = candidates[0].get(stat_key)
        if not _values_match(observed, expected):
            issues.append({
                "code": "stat_mismatch",
                "message": f"UI shows {key_raw} but character state has {expected}.",
                "severity": "warning",
            })

    return issues


def _pov_drift_issues(prose: str, pov: Optional[str], *, strict: bool = False) -> List[Dict[str, Any]]:
    pov = str(pov or "").strip().lower()
    if pov not in {"third_limited", "third", "third_person"}:
        return []
    text = _strip_dialogue(prose)
    if not text:
        return []
    evidence = _find_first_match_evidence(r"\b(I|I'm|I've|I'd|me|my|mine)\b", text)
    if not evidence:
        return []
    severity = "error" if strict else "warning"
    return [{
        "code": "pov_drift",
        "message": "Prose uses first-person POV ('I', 'my', 'myself') which contradicts the Book Constitution requirement for 'third_limited'.",
        "severity": severity,
        "evidence": evidence,
    }]


def _heuristic_invariant_issues(
    prose: str,
    summary_update: Dict[str, Any],
    pre_invariants: List[str],
    post_invariants: Optional[List[str]],
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    text = _strip_dialogue(prose)
    invariants_for_contradiction = pre_invariants
    if not invariants_for_contradiction:
        return issues

    summary_events = summary_update.get("key_events") if isinstance(summary_update, dict) else None
    summary_text = " ".join(str(item) for item in summary_events) if isinstance(summary_events, list) else ""
    combined_text = f"{text} {summary_text}".strip()

    def _has_any(text_val: str, tokens: List[str]) -> bool:
        lowered = text_val.lower()
        return any(token and token in lowered for token in tokens)

    def _all_tokens(text_val: str, tokens: List[str]) -> bool:
        lowered = text_val.lower()
        return all(token and token in lowered for token in tokens)

    def _tokens_from_name(name: str) -> List[str]:
        parts = re.split(r"[^a-zA-Z0-9]+", name.lower())
        return [part for part in parts if part]

    action_verbs = [
        "acquire",
        "acquired",
        "retrieve",
        "retrieved",
        "take",
        "took",
        "obtain",
        "obtained",
        "unfurl",
        "unfurled",
        "bind",
        "bound",
        "binding",
        "claim",
        "claimed",
        "enter",
        "entered",
    ]

    for invariant in invariants_for_contradiction:
        if not isinstance(invariant, str):
            continue
        if "milestone:" in invariant:
            token = invariant.split("milestone:", 1)[-1].strip().lower()
            if "=" not in token:
                continue
            name, status = [part.strip() for part in token.split("=", 1)]
            tokens = _tokens_from_name(name)
            if not tokens:
                continue
            if status == "done":
                if _all_tokens(combined_text, tokens) or (_has_any(combined_text, tokens) and _has_any(combined_text, action_verbs)):
                    issues.append({
                        "code": "milestone_duplicate",
                        "message": f"Prose depicts the '{name}' milestone, which is already marked as DONE in the state invariants.",
                        "severity": "error",
                    })
            if status == "not_yet":
                if _has_any(combined_text, tokens) and _has_any(combined_text, action_verbs):
                    issues.append({
                        "code": "milestone_future",
                        "message": f"Prose depicts the '{name}' milestone before it is allowed (NOT_YET).",
                        "severity": "error",
                    })
            continue

        if "present" in invariant.lower() or "physical" in invariant.lower():
            subject_tokens = _tokens_from_name(invariant)
            contradiction_tokens = ["dissolve", "dissolved", "shatter", "shattered", "destroyed", "consumed", "gone", "vanish", "vanished"]
            if _has_any(combined_text, subject_tokens) and _has_any(combined_text, contradiction_tokens):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Invariant '{invariant}' is contradicted by scene events.",
                    "severity": "error",
                })
    return issues


def _durable_scene_constraint_issues(
    prose: str,
    scene_card: Dict[str, Any],
    durable: Dict[str, Any],
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    if not isinstance(scene_card, dict):
        return issues

    constraints: Dict[str, Any] = {}
    if isinstance(scene_card.get("durable_constraints"), dict):
        constraints.update(scene_card.get("durable_constraints"))
    for key in (
        "required_in_custody",
        "required_scene_accessible",
        "required_visible_on_page",
        "forbidden_visible",
        "device_presence",
    ):
        if key not in constraints and key in scene_card:
            constraints[key] = scene_card.get(key)

    item_registry = durable.get("item_registry") if isinstance(durable, dict) else None
    plot_devices = durable.get("plot_devices") if isinstance(durable, dict) else None

    def _items_map() -> Dict[str, Dict[str, Any]]:
        if not isinstance(item_registry, dict):
            return {}
        items = item_registry.get("items")
        if not isinstance(items, list):
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for entry in items:
            if isinstance(entry, dict):
                item_id = str(entry.get("item_id") or "").strip()
                if item_id:
                    out[item_id] = entry
        return out

    def _devices_map() -> Dict[str, Dict[str, Any]]:
        if not isinstance(plot_devices, dict):
            return {}
        devices = plot_devices.get("devices")
        if not isinstance(devices, list):
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for entry in devices:
            if isinstance(entry, dict):
                device_id = str(entry.get("device_id") or "").strip()
                if device_id:
                    out[device_id] = entry
        return out

    item_map = _items_map()
    device_map = _devices_map()

    def _is_item_token(value: str) -> bool:
        return str(value).strip().upper().startswith("ITEM_")

    def _is_device_token(value: str) -> bool:
        return str(value).strip().upper().startswith("DEVICE_")

    def _resolve_item(token: str) -> Optional[Dict[str, Any]]:
        token = str(token).strip()
        if _is_device_token(token):
            return None
        if token in item_map:
            return item_map[token]
        for entry in item_map.values():
            names = {str(entry.get("name") or "").strip().lower()}
            names.add(str(entry.get("display_name") or "").strip().lower())
            aliases = entry.get("aliases")
            if isinstance(aliases, list):
                for alias in aliases:
                    names.add(str(alias).strip().lower())
            if token.lower() in names:
                return entry
        return None

    def _resolve_device(token: str) -> Optional[Dict[str, Any]]:
        token = str(token).strip()
        if _is_item_token(token):
            return None
        if token in device_map:
            return device_map[token]
        for entry in device_map.values():
            names = {str(entry.get("name") or "").strip().lower()}
            names.add(str(entry.get("display_name") or "").strip().lower())
            aliases = entry.get("aliases")
            if isinstance(aliases, list):
                for alias in aliases:
                    names.add(str(alias).strip().lower())
            if token.lower() in names:
                return entry
        return None

    required = constraints.get("required_in_custody")
    if isinstance(required, list):
        for token in required:
            entry = _resolve_item(token)
            if not entry:
                issues.append({
                    "code": "durable_slice_missing",
                    "message": f"Required item '{token}' is not present in the durable registry slice.",
                    "severity": "error",
                })
                continue

    required_access = constraints.get("required_scene_accessible")
    if isinstance(required_access, list):
        for token in required_access:
            entry = _resolve_item(token)
            if not entry:
                issues.append({
                    "code": "durable_slice_missing",
                    "message": f"Required item '{token}' is not present in the durable registry slice.",
                    "severity": "error",
                })
                continue
            if entry.get("derived_scene_accessible") is False:
                issues.append({
                    "code": "durable_required_inaccessible",
                    "message": f"Required item '{token}' is not scene-accessible ({entry.get('derived_access_reason')}).",
                    "severity": "error",
                })

    forbidden = constraints.get("forbidden_visible")
    if isinstance(forbidden, list):
        for token in forbidden:
            entry = _resolve_item(token)
            if not entry:
                continue
            if entry.get("derived_visible") is True:
                issues.append({
                    "code": "durable_forbidden_visible",
                    "message": f"Item '{token}' is visible but forbidden in scene constraints.",
                    "severity": "error",
                })

    required_visible = constraints.get("required_visible_on_page")
    if isinstance(required_visible, list):
        for token in required_visible:
            entry = _resolve_item(token)
            if not entry:
                issues.append({
                    "code": "durable_slice_missing",
                    "message": f"Required item '{token}' is not present in the durable registry slice.",
                    "severity": "error",
                })
                continue
            names = [str(entry.get("name") or "").strip()]
            display = str(entry.get("display_name") or "").strip()
            if display:
                names.append(display)
            aliases = entry.get("aliases")
            if isinstance(aliases, list):
                names.extend(str(alias).strip() for alias in aliases)
            lowered = prose.lower()
            if not any(name and name.lower() in lowered for name in names):
                issues.append({
                    "code": "durable_required_visible_missing",
                    "message": f"Required item '{token}' is not visibly mentioned in prose.",
                    "severity": "error",
                })

    device_presence = constraints.get("device_presence")
    if isinstance(device_presence, list):
        for token in device_presence:
            if _is_item_token(token):
                entry = _resolve_item(token)
                if not entry:
                    issues.append({
                        "code": "durable_slice_missing",
                        "message": f"Required item '{token}' is not present in the durable registry slice.",
                        "severity": "error",
                    })
                continue
            entry = _resolve_device(token)
            if not entry:
                issues.append({
                    "code": "durable_slice_missing",
                    "message": f"Required plot device '{token}' is not present in the durable registry slice.",
                    "severity": "error",
                })

    return issues


def _linked_durable_consistency_issues(durable: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    if not isinstance(durable, dict):
        return issues

    item_registry = durable.get("item_registry")
    plot_devices = durable.get("plot_devices")
    if not isinstance(item_registry, dict) or not isinstance(plot_devices, dict):
        return issues

    items = item_registry.get("items")
    devices = plot_devices.get("devices")
    if not isinstance(items, list) or not isinstance(devices, list):
        return issues

    item_map = {}
    for entry in items:
        if isinstance(entry, dict):
            item_id = str(entry.get("item_id") or "").strip()
            if item_id:
                item_map[item_id] = entry

    device_map = {}
    for entry in devices:
        if isinstance(entry, dict):
            device_id = str(entry.get("device_id") or "").strip()
            if device_id:
                device_map[device_id] = entry

    def _tombstoned(entry: Dict[str, Any]) -> bool:
        tags = entry.get("state_tags")
        if not isinstance(tags, list):
            return False
        lowered = {str(tag).strip().lower() for tag in tags if str(tag).strip()}
        return bool(lowered.intersection({"destroyed", "consumed", "lost", "retired"}))

    for item_id, item in item_map.items():
        linked_device_id = str(item.get("linked_device_id") or "").strip()
        if not linked_device_id:
            continue
        device = device_map.get(linked_device_id)
        if not device:
            issues.append({
                "code": "durable_link_missing",
                "message": f"Item '{item_id}' references missing plot device '{linked_device_id}'.",
                "severity": "warning",
            })
            continue
        if _tombstoned(item) and str(device.get("activation_state") or "").strip().lower() in {"active", "online", "enabled"}:
            issues.append({
                "code": "durable_link_state_conflict",
                "message": f"Item '{item_id}' is tombstoned but linked plot device '{linked_device_id}' is active.",
                "severity": "error",
            })

    for device_id, device in device_map.items():
        linked_item_id = str(device.get("linked_item_id") or "").strip()
        if not linked_item_id:
            continue
        item = item_map.get(linked_item_id)
        if not item:
            issues.append({
                "code": "durable_link_missing",
                "message": f"Plot device '{device_id}' references missing item '{linked_item_id}'.",
                "severity": "warning",
            })
            continue
        if _tombstoned(item) and str(device.get("activation_state") or "").strip().lower() in {"active", "online", "enabled"}:
            issues.append({
                "code": "durable_link_state_conflict",
                "message": f"Plot device '{device_id}' is active while linked item '{linked_item_id}' is tombstoned.",
                "severity": "error",
            })

    return issues


