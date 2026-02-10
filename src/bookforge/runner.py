from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast
import hashlib
import json
import re
import shutil

from bookforge.config.env import load_config
from bookforge.characters import characters_ready, generate_characters, resolve_character_state_path, ensure_character_index, create_character_state_path
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.types import LLMResponse, Message
from bookforge.memory.continuity import (
    ContinuityPack,
    continuity_pack_path,
    load_style_anchor,
    save_continuity_pack,
    save_style_anchor,
    style_anchor_path,
)
from bookforge.memory.durable_state import (
    ensure_durable_state_files,
    load_durable_commits,
    load_item_registry,
    load_plot_devices,
    save_durable_commits,
    save_item_registry,
    save_plot_devices,
    snapshot_item_registry,
    snapshot_plot_devices,
)
from bookforge.phases.plan import plan_scene
from bookforge.phases.preflight_phase import _scene_state_preflight
from bookforge.phases.continuity_phase import _generate_continuity_pack
from bookforge.phases.write_phase import _write_scene
from bookforge.phases.repair_phase import _repair_scene
from bookforge.phases.state_repair_phase import _state_repair
from bookforge.phases.lint_phase import _lint_scene
from bookforge.prompt.renderer import render_template_file
from bookforge.pipeline.parse import _extract_json, _extract_prose_and_patch, _extract_authoritative_surfaces
from bookforge.pipeline.config import _write_max_tokens, _lint_max_tokens, _repair_max_tokens, _state_repair_max_tokens, _continuity_max_tokens, _preflight_max_tokens, _style_anchor_max_tokens, _durable_slice_max_expansions, _lint_mode
from bookforge.pipeline.outline import _chapter_scene_count, _outline_summary, _build_character_registry, _build_thread_registry, _character_name_map, _character_id_map
from bookforge.pipeline.scene import _scene_cast_ids_from_outline, _load_character_states, _normalize_continuity_pack, _parse_until
from bookforge.pipeline.state_patch import _normalize_state_patch_for_validation, _sanitize_preflight_patch, _coerce_summary_update, _coerce_character_updates, _coerce_stat_updates, _coerce_transfer_updates, _coerce_inventory_alignment_updates, _coerce_registry_updates, _fill_character_update_context, _fill_character_continuity_update_context, _migrate_numeric_invariants
from bookforge.pipeline.state_apply import _summary_list, _summary_from_state, _apply_state_patch, _apply_character_updates, _apply_character_stat_updates, _apply_bag_updates, _ensure_character_continuity_system_state, _update_bible, _rollup_chapter_summary, _compile_chapter_markdown
from bookforge.pipeline.durable import _durable_state_context, _apply_durable_state_updates
from bookforge.pipeline.io import _load_json, _snapshot_character_states_before_preflight, _log_scope, _write_scene_files
from bookforge.pipeline.lint import _stat_mismatch_issues, _pov_drift_issues, _heuristic_invariant_issues, _durable_scene_constraint_issues, _linked_durable_consistency_issues, _lint_issue_entries, _lint_has_issue_code
from bookforge.pipeline.llm_ops import _chat, _response_truncated, _json_retry_count, _state_patch_schema_retry_message, _lint_status_from_issues
from bookforge.pipeline.prompts import _resolve_template, _system_prompt_for_phase
from bookforge.pipeline.log import _status, _now_iso
from bookforge.util.schema import validate_json

PAUSE_EXIT_CODE = 75



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

def _normalize_stat_key(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
    return cleaned.strip("_")


def _parse_stat_value(raw: str) -> Any:
    if raw is None:
        return None
    text = str(raw).strip()
    locked = "locked" in text.lower()
    text = re.sub(r"\(.*?\)", "", text).strip()
    if "/" in text:
        parts = [part.strip() for part in text.split("/", 1)]
        if len(parts) == 2 and parts[0].replace(".", "", 1).isdigit() and parts[1].replace(".", "", 1).isdigit():
            current = float(parts[0]) if "." in parts[0] else int(parts[0])
            maximum = float(parts[1]) if "." in parts[1] else int(parts[1])
            result = {"current": current, "max": maximum}
            if locked:
                result["locked"] = True
            return result
    numeric = text.replace("%", "").strip()
    if numeric.replace(".", "", 1).isdigit():
        value = float(numeric) if "." in numeric else int(numeric)
        if text.endswith("%"):
            value = f"{value}%"
        if locked:
            return {"value": value, "locked": True}
        return value
    return text


def _upsert_continuity_update(updates: list, character_id: str) -> dict:
    for update in updates:
        if isinstance(update, dict) and str(update.get("character_id") or "") == character_id:
            return update
    new_item = {"character_id": character_id, "set": {}, "delta": {}}
    updates.append(new_item)
    return new_item


def _upsert_global_continuity_update(updates: list) -> dict:
    for update in updates:
        if isinstance(update, dict):
            return update
    new_item = {"set": {}, "delta": {}}
    updates.append(new_item)
    return new_item


def _merge_continuity_update_block(target: Dict[str, Any], key: str, payload: Any) -> None:
    if payload is None:
        return
    if isinstance(payload, dict):
        target.setdefault(key, {})
        existing = target.get(key)
        if not isinstance(existing, dict):
            target[key] = dict(payload)
            return
        for sub_key, sub_value in payload.items():
            existing[sub_key] = sub_value
        target[key] = existing
        return
    target[key] = payload


def _coerce_legacy_family_update_into_continuity(target: Dict[str, Any], legacy_update: Dict[str, Any], family_key: str) -> None:
    target.setdefault("set", {})
    target.setdefault("delta", {})

    direct = legacy_update.get(family_key)
    if isinstance(direct, (dict, list, str, int, float)):
        _merge_continuity_update_block(target["set"], family_key, direct)

    set_block = legacy_update.get("set")
    if isinstance(set_block, dict):
        _merge_continuity_update_block(target["set"], family_key, set_block)

    delta_block = legacy_update.get("delta")
    if isinstance(delta_block, dict):
        _merge_continuity_update_block(target["delta"], family_key, delta_block)

    reason = legacy_update.get("reason")
    if isinstance(reason, str) and reason.strip() and not target.get("reason"):
        target["reason"] = reason.strip()


def _append_continuity_list_item(target_set: Dict[str, Any], key: str, value: str) -> None:
    if key == "titles":
        existing = target_set.get("titles")
        normalized_existing = _normalize_titles_value(existing)
        title = _normalize_title_entry(value)
        if title:
            normalized_existing.append(title)
        target_set["titles"] = _normalize_titles_value(normalized_existing)
        return
    existing = target_set.get(key)
    if isinstance(existing, list):
        if value not in existing:
            existing.append(value)
            target_set[key] = existing
        return
    target_set[key] = [value]

def _stat_key_aliases() -> Dict[str, str]:
    return {
        "critical_hit_rate": "crit_rate",
        "crit_rate": "crit_rate",
        "critical_rate": "crit_rate",
        "hp": "hp",
        "stamina": "stamina",
        "mp": "mp",
        "mana": "mp",
        "level": "level",
    }


def _merged_character_states_for_lint(
    character_states: List[Dict[str, Any]],
    patch: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not isinstance(patch, dict) or not isinstance(character_states, list):
        return character_states
    updates = patch.get("character_continuity_system_updates")
    character_updates = patch.get("character_updates")
    if not isinstance(updates, list) and not isinstance(character_updates, list):
        return character_states

    merged = json.loads(json.dumps(character_states))
    index = {}
    for idx, state in enumerate(merged):
        if not isinstance(state, dict):
            continue
        char_id = str(state.get("character_id") or "").strip()
        if char_id:
            index[char_id] = idx

    if isinstance(updates, list):
        for update in updates:
            if not isinstance(update, dict):
                continue
            char_id = str(update.get("character_id") or "").strip()
            if not char_id or char_id not in index:
                continue
            state = merged[index[char_id]]
            if not isinstance(state, dict):
                continue
            continuity = _ensure_character_continuity_system_state(state)
            _apply_bag_updates(continuity, update)
            state["character_continuity_system_state"] = continuity

    if isinstance(character_updates, list):
        for update in character_updates:
            if not isinstance(update, dict):
                continue
            char_id = str(update.get("character_id") or "").strip()
            if not char_id or char_id not in index:
                continue
            state = merged[index[char_id]]
            if not isinstance(state, dict):
                continue
            inventory = update.get("inventory")
            if isinstance(inventory, list):
                state["inventory"] = inventory
            containers = update.get("containers")
            if isinstance(containers, list):
                state["containers"] = containers
            invariants_add = update.get("invariants_add")
            if isinstance(invariants_add, list):
                existing = state.get("invariants", [])
                if not isinstance(existing, list):
                    existing = []
                combined = existing + [str(item) for item in invariants_add if str(item).strip()]
                deduped = []
                seen = set()
                for item in combined:
                    key = str(item).strip().lower()
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    deduped.append(item)
                state["invariants"] = deduped

    return merged


def _scene_card_ids(scene_card: Dict[str, Any], key: str) -> List[str]:
    values = scene_card.get(key)
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _entry_aliases(entry: Dict[str, Any]) -> List[str]:
    aliases = entry.get("aliases")
    if not isinstance(aliases, list):
        return []
    return [str(value).strip() for value in aliases if str(value).strip()]


def _entry_mentioned_on_page(prose: str, entry: Dict[str, Any], id_key: str) -> bool:
    if not isinstance(entry, dict):
        return False
    tokens: List[str] = []
    primary_id = str(entry.get(id_key) or "").strip()
    if primary_id:
        tokens.append(primary_id)
    for key in ("display_name", "name", "item_name", "item", "label"):
        value = str(entry.get(key) or "").strip()
        if value:
            tokens.append(value)
    tokens.extend(_entry_aliases(entry))

    text = prose.lower()
    for token in tokens:
        normalized = token.strip().lower()
        if not normalized:
            continue
        if " " in normalized:
            if normalized in text:
                return True
        else:
            if re.search(r"\b" + re.escape(normalized) + r"\b", text):
                return True
    return False


def _global_continuity_stats(state: Dict[str, Any]) -> Dict[str, Any]:
    continuity = state.get("global_continuity_system_state")
    if isinstance(continuity, dict):
        stats = continuity.get("stats")
        if isinstance(stats, dict):
            return stats
    legacy = state.get("run_stats")
    return legacy if isinstance(legacy, dict) else {}
def _contains_any(text: str, terms: List[str]) -> bool:
    for term in terms:
        if not term:
            continue
        if " " in term:
            if term in text:
                return True
        else:
            if re.search(r"\b" + re.escape(term) + r"\b", text):
                return True
    return False


def _cursor_beyond_target(
    chapter: int,
    scene: int,
    target: Tuple[Optional[int], Optional[int]],
    scene_counts: Dict[int, int],
) -> bool:
    target_chapter, target_scene = target
    if target_chapter is None:
        return False
    if chapter > target_chapter:
        return True
    if chapter < target_chapter:
        return False
    if target_scene is None:
        target_scene = scene_counts.get(target_chapter, 0)
    if target_scene <= 0:
        return False
    return scene > target_scene


def _advance_cursor(
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    chapter: int,
    scene: int,
) -> Tuple[int, int, bool]:
    total_scenes = scene_counts.get(chapter, 0)
    if total_scenes and scene < total_scenes:
        return chapter, scene + 1, False
    if chapter in chapter_order:
        index = chapter_order.index(chapter)
        if index + 1 < len(chapter_order):
            return chapter_order[index + 1], 1, False
    return chapter + 1, 1, True


def _existing_scene_card(state: Dict[str, Any], book_root: Path) -> Optional[Path]:
    plan_data = state.get("plan", {}) if isinstance(state.get("plan"), dict) else {}
    rel_path = plan_data.get("scene_card")
    if not rel_path:
        return None
    path = book_root / rel_path
    if not path.exists():
        return None

    cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
    chapter = int(cursor.get("chapter", 0) or 0)
    scene = int(cursor.get("scene", 0) or 0)
    try:
        card = _load_json(path)
    except Exception:
        return None
    card_chapter = int(card.get("chapter", 0) or 0)
    card_scene = int(card.get("scene", 0) or 0)
    if chapter and scene and (card_chapter != chapter or card_scene != scene):
        return None
    return path



def _author_fragment_path(workspace: Path, author_ref: str) -> Path:
    parts = [part for part in author_ref.split("/") if part]
    if len(parts) != 2:
        raise ValueError("author_ref must look like <author_slug>/vN")
    return workspace / "authors" / parts[0] / parts[1] / "system_fragment.md"


def _maybe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _previous_scene_ref(
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    chapter: int,
    scene: int,
) -> Optional[Tuple[int, int]]:
    if scene > 1:
        return chapter, scene - 1
    if chapter in chapter_order:
        idx = chapter_order.index(chapter)
        if idx > 0:
            prev_chapter = chapter_order[idx - 1]
            prev_count = int(scene_counts.get(prev_chapter, 0) or 0)
            if prev_count > 0:
                return prev_chapter, prev_count
    return None


def _scene_prose_path(book_root: Path, chapter: int, scene: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{chapter:03d}" / f"scene_{scene:03d}.md"


def _read_scene_prose(book_root: Path, chapter: int, scene: int) -> str:
    path = _scene_prose_path(book_root, chapter, scene)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _last_appearance_for_character(
    book_root: Path,
    outline: Dict[str, Any],
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    chapter: int,
    scene: int,
    character_id: str,
) -> Optional[Dict[str, Any]]:
    pointer = _previous_scene_ref(chapter_order, scene_counts, chapter, scene)
    while pointer is not None:
        ref_ch, ref_sc = pointer
        cast_ids = _scene_cast_ids_from_outline(outline, ref_ch, ref_sc)
        if character_id in cast_ids:
            prose = _read_scene_prose(book_root, ref_ch, ref_sc)
            if prose.strip():
                return {
                    "character_id": character_id,
                    "chapter": ref_ch,
                    "scene": ref_sc,
                    "prose": prose,
                }
        pointer = _previous_scene_ref(chapter_order, scene_counts, ref_ch, ref_sc)
    return None


def _build_preflight_context(
    book_root: Path,
    outline: Dict[str, Any],
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    scene_card: Dict[str, Any],
) -> Dict[str, Any]:
    chapter = _maybe_int(scene_card.get("chapter")) or 0
    scene = _maybe_int(scene_card.get("scene")) or 0
    cast_ids = scene_card.get("cast_present_ids", [])
    if not isinstance(cast_ids, list):
        cast_ids = []
    cast_ids = [str(item) for item in cast_ids if str(item).strip()]

    immediate_previous: Dict[str, Any] = {"available": False}
    immediate_cast_ids: List[str] = []
    previous = _previous_scene_ref(chapter_order, scene_counts, chapter, scene)
    if previous is not None:
        prev_ch, prev_sc = previous
        prose = _read_scene_prose(book_root, prev_ch, prev_sc)
        immediate_previous = {
            "available": bool(prose.strip()),
            "chapter": prev_ch,
            "scene": prev_sc,
            "prose": prose,
        }
        immediate_cast_ids = _scene_cast_ids_from_outline(outline, prev_ch, prev_sc)

    cast_last_appearance: List[Dict[str, Any]] = []
    for char_id in cast_ids:
        if char_id in immediate_cast_ids:
            continue
        item = _last_appearance_for_character(
            book_root,
            outline,
            chapter_order,
            scene_counts,
            chapter,
            scene,
            char_id,
        )
        if item:
            cast_last_appearance.append(item)

    return {
        "immediate_previous_scene": immediate_previous,
        "cast_last_appearance": cast_last_appearance,
    }


def _durable_slice_retry_ids(report: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for issue in _lint_issue_entries(report, "durable_slice_missing"):
        hint = str(issue.get("retry_hint") or "").strip()
        prefix = "expand_durable_slice:id:"
        if not hint.startswith(prefix):
            continue
        token = hint[len(prefix):].strip()
        if token and token not in ids:
            ids.append(token)
    return ids


def _write_reason_pause_marker(
    book_root: Path,
    phase: str,
    reason_code: str,
    message: str,
    scene_card: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Path:
    context_dir = book_root / "draft" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "book_id": book_root.name,
        "phase": str(phase).strip(),
        "reason_code": str(reason_code).strip(),
        "message": str(message).strip(),
        "created_at": _now_iso(),
    }
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        scene = _maybe_int(scene_card.get("scene"))
        if chapter is not None:
            payload["chapter"] = chapter
        if scene is not None:
            payload["scene"] = scene
    if isinstance(details, dict) and details:
        payload["details"] = details
    pause_path = context_dir / "run_paused.json"
    pause_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return pause_path


def _pause_on_reason(
    book_root: Path,
    state_path: Path,
    state: Optional[Dict[str, Any]],
    phase: str,
    reason_code: str,
    message: str,
    scene_card: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    if state is not None:
        try:
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception:
            pass
    _write_reason_pause_marker(book_root, phase, reason_code, message, scene_card, details)
    _status(f"Run paused ({reason_code}) in phase '{phase}': {message}")
    raise SystemExit(PAUSE_EXIT_CODE)


def _write_pause_marker(
    book_root: Path,
    phase: str,
    error: LLMRequestError,
    scene_card: Optional[Dict[str, Any]] = None,
) -> Path:
    context_dir = book_root / "draft" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "book_id": book_root.name,
        "phase": phase,
        "status_code": error.status_code,
        "message": error.message,
        "retry_after_seconds": error.retry_after_seconds,
        "quota_violations": [
            {
                "quota_metric": item.quota_metric,
                "quota_id": item.quota_id,
                "quota_dimensions": item.quota_dimensions,
                "quota_value": item.quota_value,
            }
            for item in error.quota_violations
        ],
        "created_at": _now_iso(),
    }
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        scene = _maybe_int(scene_card.get("scene"))
        if chapter is not None:
            payload["chapter"] = chapter
        if scene is not None:
            payload["scene"] = scene
    pause_path = context_dir / "run_paused.json"
    pause_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return pause_path


def _pause_on_quota(
    book_root: Path,
    state_path: Path,
    state: Optional[Dict[str, Any]],
    phase: str,
    error: LLMRequestError,
    scene_card: Optional[Dict[str, Any]] = None,
) -> None:
    if error.status_code != 429 and not error.quota_violations:
        raise error
    if state is not None:
        try:
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception:
            pass
    _write_pause_marker(book_root, phase, error, scene_card)
    _status(f"Run paused due to quota in phase '{phase}': {error}")
    raise SystemExit(PAUSE_EXIT_CODE)


def _apply_durable_updates_or_pause(
    book_root: Path,
    state_path: Path,
    state: Optional[Dict[str, Any]],
    patch: Dict[str, Any],
    chapter: int,
    scene: int,
    phase: str,
    scene_card: Optional[Dict[str, Any]] = None,
) -> bool:
    try:
        return _apply_durable_state_updates(
            book_root=book_root,
            patch=patch,
            chapter=chapter,
            scene=scene,
            phase=phase,
            state=state,
            scene_card=scene_card,
        )
    except ValueError as exc:
        msg = str(exc).strip() or "Durable apply validation failed."
        code = "durable_apply_validation_failed"
        if "Chronology conflict" in msg:
            code = "durable_chronology_conflict"
        _pause_on_reason(
            book_root=book_root,
            state_path=state_path,
            state=state,
            phase=f"durable_apply_{phase}",
            reason_code=code,
            message=msg,
            scene_card=scene_card,
            details={
                "chapter": int(chapter),
                "scene": int(scene),
                "phase": str(phase),
            },
        )
    return False



def _fallback_style_anchor(author_fragment: str) -> str:
    cleaned = re.sub(r"^You are [^.]+\.\s*", "", author_fragment, flags=re.IGNORECASE).strip()
    if cleaned:
        return cleaned
    return "Write in tight third-person limited with concrete sensory detail and forward motion."


def _ensure_style_anchor(
    workspace: Path,
    book_root: Path,
    book: Dict[str, Any],
    system_path: Path,
    client: LLMClient,
    model: str,
) -> str:
    anchor_path = style_anchor_path(book_root)
    existing = load_style_anchor(anchor_path)
    if existing.strip():
        return existing
    author_ref = str(book.get("author_ref", ""))
    fragment_path = _author_fragment_path(workspace, author_ref)
    if not fragment_path.exists():
        raise FileNotFoundError(f"Author fragment not found: {fragment_path}")
    author_fragment = fragment_path.read_text(encoding="utf-8")

    template = _resolve_template(book_root, "style_anchor.md")
    prompt = render_template_file(
        template,
        {
            "author_fragment": author_fragment,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "style_anchor",
        client,
        messages,
        model=model,
        temperature=0.7,
        max_tokens=_style_anchor_max_tokens(),
        log_extra=_log_scope(book_root),
    )
    text = response.text.strip()
    if not text:
        retry_prompt = (
            prompt
            + "\n\nOutput must be non-empty and 200-400 words."
            + " If you are unsure, write 8-12 sentences of neutral prose with no names."
        )
        retry_messages: List[Message] = [
            {"role": "system", "content": system_path.read_text(encoding="utf-8")},
            {"role": "user", "content": retry_prompt},
        ]
        response = _chat(
            workspace,
            "style_anchor_retry",
            client,
            retry_messages,
            model=model,
            temperature=0.7,
            max_tokens=_style_anchor_max_tokens(),
            log_extra=_log_scope(book_root),
        )
        text = response.text.strip()
    if not text:
        text = _fallback_style_anchor(author_fragment)
    if not text:
        raise ValueError("Style anchor generation returned empty output.")
    save_style_anchor(anchor_path, text)
    return text


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
    report = _normalize_lint_report(report)
    summary_update = patch.get("summary_update") if isinstance(patch, dict) else {}
    if not isinstance(summary_update, dict):
        summary_update = {}
    heuristic_issues = _heuristic_invariant_issues(prose, summary_update, pre_invariants, post_invariants)
    lint_character_states = _merged_character_states_for_lint(character_states, patch)
    extra_issues = _stat_mismatch_issues(
        prose,
        lint_character_states,
        _global_continuity_stats(post_state),
        authoritative_surfaces=authoritative_surfaces,
    )
    extra_issues += _pov_drift_issues(prose, pov, strict=_lint_mode() == "strict")
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


def run_loop(
    workspace: Path,
    book_id: str,
    steps: Optional[int] = None,
    until: Optional[str] = None,
    resume: bool = False,
) -> None:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    book_path = book_root / "book.json"
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"

    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state.json: {state_path}")
    if not outline_path.exists():
        raise FileNotFoundError(f"Missing outline.json: {outline_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    book = _load_json(book_path)
    outline = _load_json(outline_path)
    validate_json(outline, "outline")

    chapter_order, scene_counts = _outline_summary(outline)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    if not chapter_order:
        raise ValueError("Outline is missing chapters; cannot run writer loop.")

    target = _parse_until(until)
    if steps is None and target == (None, None):
        steps_remaining: Optional[int] = 1
    else:
        steps_remaining = steps

    config = load_config()
    planner_client = get_llm_client(config, phase="planner")
    continuity_client = get_llm_client(config, phase="continuity")
    preflight_client = get_llm_client(config, phase="preflight")
    writer_client = get_llm_client(config, phase="writer")
    repair_client = get_llm_client(config, phase="repair")
    state_repair_client = get_llm_client(config, phase="state_repair")
    linter_client = get_llm_client(config, phase="linter")
    planner_model = resolve_model("planner", config)
    continuity_model = resolve_model("continuity", config)
    preflight_model = resolve_model("preflight", config)

    if not characters_ready(book_root):
        try:
            generate_characters(workspace=workspace, book_id=book_id)
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, None, "characters_generate", exc)
    writer_model = resolve_model("writer", config)
    repair_model = resolve_model("repair", config)
    state_repair_model = resolve_model("state_repair", config)
    linter_model = resolve_model("linter", config)

    try:
        style_anchor = _ensure_style_anchor(
            workspace,
            book_root,
            book,
            system_path,
            writer_client,
            writer_model,
        )
    except LLMRequestError as exc:
        _pause_on_quota(book_root, state_path, None, "style_anchor", exc)

    while True:
        state = _load_json(state_path)
        cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
        chapter = int(cursor.get("chapter", 0) or 0)
        scene = int(cursor.get("scene", 0) or 0)

        if chapter <= 0:
            chapter = chapter_order[0]
        if scene <= 0:
            scene = 1

        if _cursor_beyond_target(chapter, scene, target, scene_counts):
            break
        if steps_remaining is not None and steps_remaining <= 0:
            break

        scene_card_path = _existing_scene_card(state, book_root) if resume else None
        if scene_card_path is None:
            _status(f"Planning chapter {chapter} scene {scene}...")
            try:
                scene_card_path = plan_scene(
                    workspace=workspace,
                    book_id=book_id,
                    client=planner_client,
                    model=planner_model,
                )
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "plan_scene", exc)
            _status(f"Planned scene card: ch{chapter:03d} sc{scene:03d} OK")
        else:
            _status(f"Using existing scene card: ch{chapter:03d} sc{scene:03d}")

        scene_card = _load_json(scene_card_path)
        validate_json(scene_card, "scene_card")
        chapter_num = int(scene_card.get("chapter", chapter))
        scene_num = int(scene_card.get("scene", scene))

        cast_ids = scene_card.get("cast_present_ids", []) if isinstance(scene_card, dict) else []
        if not isinstance(cast_ids, list):
            cast_ids = []
        cast_ids = [str(item) for item in cast_ids if str(item).strip()]
        if not cast_ids:
            derived = _scene_cast_ids_from_outline(outline, chapter_num, scene_num)
            if not derived:
                name_map = _character_id_map(character_registry)
                cast_names = scene_card.get("cast_present", []) if isinstance(scene_card, dict) else []
                if not isinstance(cast_names, list):
                    cast_names = []
                for name in cast_names:
                    mapped = name_map.get(str(name).strip().lower())
                    if mapped:
                        derived.append(mapped)
            if derived:
                scene_card["cast_present_ids"] = derived
                cast_ids = list(derived)
        if cast_ids and not scene_card.get("cast_present"):
            name_map = _character_name_map(character_registry)
            scene_card["cast_present"] = [name_map.get(item, item) for item in cast_ids]

        state = _load_json(state_path)

        chapter_total = scene_counts.get(chapter_num)
        chapter_end = isinstance(chapter_total, int) and chapter_total > 0 and scene_num >= chapter_total

        durable_expand_ids: set[str] = set()
        durable_expand_attempts = 0
        durable_expand_max = _durable_slice_max_expansions()

        _status(f"Loading character states (cast only): ch{chapter_num:03d} sc{scene_num:03d}...")
        character_states = _load_character_states(book_root, scene_card)
        _status("Character states loaded OK")
        snapshots = _snapshot_character_states_before_preflight(book_root, scene_card)
        if snapshots:
            _status(f"Character state snapshots written: {len(snapshots)}")

        _status(f"Preflight state alignment: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            preflight_patch = _scene_state_preflight(
                workspace,
                book_root,
                system_path,
                scene_card,
                state,
                outline,
                chapter_order,
                scene_counts,
                character_registry,
                thread_registry,
                character_states,
                preflight_client,
                preflight_model,
                durable_expand_ids=sorted(durable_expand_ids),
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "scene_state_preflight", exc, scene_card)

        state = _apply_state_patch(state, preflight_patch, chapter_end=False)
        _apply_character_updates(book_root, preflight_patch, chapter_num, scene_num)
        _apply_character_stat_updates(book_root, preflight_patch)
        if _apply_durable_updates_or_pause(
            book_root=book_root,
            state_path=state_path,
            state=state,
            patch=preflight_patch,
            chapter=chapter_num,
            scene=scene_num,
            phase="preflight",
            scene_card=scene_card,
        ):
            _status("Durable state updated (preflight) OK")
        character_states = _load_character_states(book_root, scene_card)
        _status("Preflight alignment complete OK")

        _status(f"Generating continuity pack: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            continuity_pack = _generate_continuity_pack(
                workspace,
                book_root,
                system_path,
                state,
                scene_card,
                character_registry,
                thread_registry,
                character_states,
                continuity_client,
                continuity_model,
                durable_expand_ids=sorted(durable_expand_ids),
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "continuity_pack", exc, scene_card)
        _status("Continuity pack ready OK")

        base_invariants = book.get("invariants", []) if isinstance(book.get("invariants", []), list) else []

        _status(f"Writing scene: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            prose, patch = _write_scene(
                workspace,
                book_root,
                system_path,
                scene_card,
                continuity_pack,
                state,
                style_anchor,
                character_registry,
                thread_registry,
                character_states,
                writer_client,
                writer_model,
                durable_expand_ids=sorted(durable_expand_ids),
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "write_scene", exc, scene_card)
        _status("Write complete OK")

        _status(f"Repairing state: ch{chapter_num:03d} sc{scene_num:03d}...")
        try:
            patch = _state_repair(
                workspace,
                book_root,
                system_path,
                prose,
                state,
                scene_card,
                continuity_pack,
                patch,
                character_registry,
                thread_registry,
                character_states,
                state_repair_client,
                state_repair_model,
                durable_expand_ids=sorted(durable_expand_ids),
            )
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, state, "state_repair", exc, scene_card)
        _status("State repair complete OK")

        pre_lint_state = json.loads(json.dumps(state))
        pre_summary = _summary_from_state(pre_lint_state)
        pre_invariants = list(base_invariants)
        pre_invariants += pre_summary.get("must_stay_true", [])
        pre_invariants += pre_summary.get("key_facts_ring", [])

        lint_state = json.loads(json.dumps(state))
        lint_state = _apply_state_patch(lint_state, patch, chapter_end=chapter_end)
        post_summary = _summary_from_state(lint_state)
        post_invariants = list(base_invariants)
        post_invariants += post_summary.get("must_stay_true", [])
        post_invariants += post_summary.get("key_facts_ring", [])

        lint_mode = _lint_mode()

        if lint_mode == "off":
            lint_report = {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "off"}
            _status("Linting disabled (mode=off).")
        else:
            _status(f"Linting scene: ch{chapter_num:03d} sc{scene_num:03d}...")
            try:
                lint_report = _lint_scene(
                    workspace,
                    book_root,
                    system_path,
                    prose,
                    pre_lint_state,
                    lint_state,
                    patch,
                    scene_card,
                    pre_invariants,
                    post_invariants,
                    character_states,
                    book.get("pov"),
                    linter_client,
                    linter_model,
                    durable_expand_ids=sorted(durable_expand_ids),
                )
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "lint_scene", exc, scene_card)
            _status(f"Lint status: {lint_report.get('status', 'unknown')}")

        write_attempts = 1
        if lint_mode != "off" and lint_report.get("status") == "fail":
            while True:
                if _lint_has_issue_code(lint_report, "durable_slice_missing"):
                    requested_ids = _durable_slice_retry_ids(lint_report)
                    new_ids = [item for item in requested_ids if item not in durable_expand_ids]
                    if new_ids and durable_expand_attempts < durable_expand_max:
                        capacity = max(0, durable_expand_max - durable_expand_attempts)
                        selected = new_ids[:capacity]
                        durable_expand_ids.update(selected)
                        durable_expand_attempts += len(selected)
                        _status(
                            "Expanding durable slice ("
                            + f"{durable_expand_attempts}/{durable_expand_max}"
                            + "): "
                            + ", ".join(selected)
                        )

                _status(f"Repairing scene: ch{chapter_num:03d} sc{scene_num:03d}...")
                try:
                    prose, patch = _repair_scene(
                        workspace,
                        book_root,
                        system_path,
                        prose,
                        lint_report,
                        state,
                        scene_card,
                        character_registry,
                        thread_registry,
                        character_states,
                        repair_client,
                        repair_model,
                        durable_expand_ids=sorted(durable_expand_ids),
                    )
                except LLMRequestError as exc:
                    _pause_on_quota(book_root, state_path, state, "repair_scene", exc, scene_card)
                _status("Repair complete OK")
                write_attempts += 1

                _status(f"Repairing state: ch{chapter_num:03d} sc{scene_num:03d}...")
                try:
                    patch = _state_repair(
                        workspace,
                        book_root,
                        system_path,
                        prose,
                        state,
                        scene_card,
                        continuity_pack,
                        patch,
                        character_registry,
                        thread_registry,
                        character_states,
                        state_repair_client,
                        state_repair_model,
                        durable_expand_ids=sorted(durable_expand_ids),
                    )
                except LLMRequestError as exc:
                    _pause_on_quota(book_root, state_path, state, "state_repair", exc, scene_card)
                _status("State repair complete OK")

                pre_lint_state = json.loads(json.dumps(state))
                pre_summary = _summary_from_state(pre_lint_state)
                pre_invariants = list(base_invariants)
                pre_invariants += pre_summary.get("must_stay_true", [])
                pre_invariants += pre_summary.get("key_facts_ring", [])

                lint_state = json.loads(json.dumps(state))
                lint_state = _apply_state_patch(lint_state, patch, chapter_end=chapter_end)
                post_summary = _summary_from_state(lint_state)
                post_invariants = list(base_invariants)
                post_invariants += post_summary.get("must_stay_true", [])
                post_invariants += post_summary.get("key_facts_ring", [])

                _status(f"Linting scene: ch{chapter_num:03d} sc{scene_num:03d}...")
                try:
                    lint_report = _lint_scene(
                        workspace,
                        book_root,
                        system_path,
                        prose,
                        pre_lint_state,
                        lint_state,
                        patch,
                        scene_card,
                        pre_invariants,
                        post_invariants,
                        character_states,
                        book.get("pov"),
                        linter_client,
                        linter_model,
                        durable_expand_ids=sorted(durable_expand_ids),
                    )
                except LLMRequestError as exc:
                    _pause_on_quota(book_root, state_path, state, "lint_scene", exc, scene_card)
                _status(f"Lint status: {lint_report.get('status', 'unknown')}")

                if lint_report.get("status") != "fail":
                    break
                if lint_mode != "strict":
                    break
                if not _lint_has_issue_code(lint_report, "durable_slice_missing"):
                    break
                requested_ids = _durable_slice_retry_ids(lint_report)
                new_ids = [item for item in requested_ids if item not in durable_expand_ids]
                if not new_ids:
                    break
                if durable_expand_attempts >= durable_expand_max:
                    break

            if lint_report.get("status") == "fail" and lint_mode == "strict":
                if _lint_has_issue_code(lint_report, "durable_slice_missing"):
                    _pause_on_reason(
                        book_root,
                        state_path,
                        state,
                        "lint_scene",
                        "durable_slice_missing",
                        "Durable canonical context is missing one or more required ids; run paused to avoid retry thrash.",
                        scene_card,
                        details={
                            "issues": _lint_issue_entries(lint_report, "durable_slice_missing"),
                            "durable_expand_attempts": durable_expand_attempts,
                            "durable_expand_max": durable_expand_max,
                            "expanded_ids": sorted(durable_expand_ids),
                        },
                    )
                raise ValueError("Lint failed after repair; see lint logs for details.")

        chapter_total = scene_counts.get(chapter_num)
        chapter_end = isinstance(chapter_total, int) and chapter_total > 0 and scene_num >= chapter_total

        _status("Applying state patch...")
        state = _apply_state_patch(state, patch, chapter_end=chapter_end)
        _status("State updated OK")

        updates = patch.get("character_updates") if isinstance(patch, dict) else None
        continuity_updates = patch.get("character_continuity_system_updates") if isinstance(patch, dict) else None
        has_char_updates = isinstance(updates, list) and len(updates) > 0
        has_continuity_updates = isinstance(continuity_updates, list) and len(continuity_updates) > 0
        if has_char_updates or has_continuity_updates:
            _status("Updating character states...")
            if has_char_updates:
                _apply_character_updates(book_root, patch, chapter_num, scene_num)
            if has_continuity_updates:
                _apply_character_stat_updates(book_root, patch)
            _status("Character states updated OK")

        if _apply_durable_updates_or_pause(
            book_root=book_root,
            state_path=state_path,
            state=state,
            patch=patch,
            chapter=chapter_num,
            scene=scene_num,
            phase="scene",
            scene_card=scene_card,
        ):
            _status("Durable state updated OK")

        cursor_override = patch.get("cursor_advance") if isinstance(patch.get("cursor_advance"), dict) else None
        if cursor_override:
            next_chapter = int(cursor_override.get("chapter", chapter_num) or chapter_num)
            next_scene = int(cursor_override.get("scene", scene_num + 1) or (scene_num + 1))
            completed = False
        else:
            next_chapter, next_scene, completed = _advance_cursor(
                chapter_order,
                scene_counts,
                chapter_num,
                scene_num,
            )

        _status("Persisting scene files...")
        _write_scene_files(
            book_root,
            chapter_num,
            scene_num,
            prose,
            scene_card,
            patch,
            lint_report,
            write_attempts,
        )
        _status("Scene files written OK")

        _update_bible(book_root, patch)

        if chapter_end:
            _status(f"Rolling up chapter summary: ch{chapter_num:03d}...")
            _rollup_chapter_summary(book_root, state, chapter_num)
            _status(f"Compiling chapter: ch{chapter_num:03d}...")
            _compile_chapter_markdown(book_root, outline, chapter_num)
            _status("Chapter compiled OK")

        _status(f"Advancing cursor -> ch{next_chapter:03d} sc{next_scene:03d}")
        state["cursor"] = {"chapter": next_chapter, "scene": next_scene}
        if completed:
            state["status"] = "COMPLETE"
        else:
            state["status"] = "DRAFTING"

        validate_json(state, "state")
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

        if steps_remaining is not None:
            steps_remaining -= 1


def run() -> None:
    raise NotImplementedError("Use run_loop via CLI.")






























































































