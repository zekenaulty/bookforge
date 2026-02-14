from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast
import hashlib
import json
import re
import shutil

from bookforge.config.env import load_config
from bookforge.characters import characters_ready, generate_characters, resolve_character_state_path, ensure_character_index, create_character_state_path, refresh_appearance_projections
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.types import LLMResponse, Message
from bookforge.memory.continuity import (
    continuity_pack_path,
    load_style_anchor,
    save_continuity_pack,
    save_style_anchor,
    style_anchor_path,
)
from bookforge.phases.plan import plan_scene
from bookforge.phases.preflight_phase import _scene_state_preflight
from bookforge.phases.continuity_phase import _generate_continuity_pack
from bookforge.phases.write_phase import _write_scene
from bookforge.phases.repair_phase import _repair_scene
from bookforge.phases.state_repair_phase import _state_repair
from bookforge.phases.lint_phase import _lint_scene
from bookforge.prompt.renderer import render_template_file
from bookforge.pipeline.config import _style_anchor_max_tokens, _durable_slice_max_expansions, _lint_mode
from bookforge.pipeline.outline import _outline_summary, _build_character_registry, _build_thread_registry, _character_name_map, _character_id_map
from bookforge.pipeline.scene import _scene_cast_ids_from_outline, _load_character_states, _parse_until
from bookforge.pipeline.state_apply import _summary_from_state, _apply_state_patch, _apply_character_updates, _apply_character_stat_updates, _update_bible, _rollup_chapter_summary, _compile_chapter_markdown
from bookforge.pipeline.durable import _apply_durable_state_updates
from bookforge.pipeline.io import _load_json, _snapshot_character_states_before_preflight, _log_scope, _write_scene_files
from bookforge.pipeline.phase_history import _load_phase_history, _record_phase_success, _write_phase_artifact
from bookforge.pipeline.run_logging import _current_run_id, _write_latest_run_pointer, _run_log_path, _append_run_log
from bookforge.pipeline.lint import _lint_issue_entries, _lint_has_issue_code
from bookforge.pipeline.llm_ops import _chat
from bookforge.pipeline.prompts import _resolve_template
from bookforge.pipeline.lint import _pov_drift_issues, _stat_mismatch_issues, _durable_scene_constraint_issues
from bookforge.pipeline.parse import _extract_authoritative_surfaces
from bookforge.pipeline.state_patch import _coerce_character_updates
from bookforge.pipeline.state_patch import _coerce_inventory_alignment_updates
from bookforge.pipeline.state_patch import _coerce_transfer_updates
from bookforge.pipeline.state_patch import _coerce_stat_updates
from bookforge.pipeline.lint import _heuristic_invariant_issues, _linked_durable_consistency_issues
from bookforge.pipeline.durable import _durable_state_context
from bookforge.pipeline.parse import _extract_prose_and_patch
from bookforge.pipeline.log import _status, _now_iso, set_run_log_path
from bookforge.util.schema import validate_json
from bookforge.outline import load_latest_outline_pipeline_report, format_outline_pipeline_summary

PAUSE_EXIT_CODE = 75

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


def _resolve_artifact_path(book_root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = book_root / value
    return path

def _artifact_relpath(book_root: Path, path: Path) -> str:
    try:
        return path.relative_to(book_root).as_posix()
    except ValueError:
        return path.as_posix()

def _phase_artifacts_for_resume(phase_history: Dict[str, Any], phase: str, required: List[str], book_root: Path) -> Optional[Dict[str, Path]]:
    phases = phase_history.get("phases") if isinstance(phase_history, dict) else None
    if not isinstance(phases, dict):
        return None
    entry = phases.get(phase)
    if not isinstance(entry, dict):
        return None
    if entry.get("status") != "success":
        return None
    artifacts = entry.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    resolved: Dict[str, Path] = {}
    for key in required:
        raw = artifacts.get(key)
        if not raw:
            return None
        path = _resolve_artifact_path(book_root, str(raw))
        if not path.exists():
            return None
        resolved[key] = path
    return resolved

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



def _normalize_scene_card_ui_gate(scene_card: Dict[str, Any]) -> None:
    if not isinstance(scene_card, dict):
        return
    ui_mechanics = scene_card.get("ui_mechanics_expected")
    if isinstance(ui_mechanics, list):
        ui_mechanics = [str(item) for item in ui_mechanics if str(item).strip()]
    else:
        ui_mechanics = []

    ui_allowed = scene_card.get("ui_allowed")
    if isinstance(ui_allowed, str):
        lowered = ui_allowed.strip().lower()
        if lowered in {"true", "yes", "1", "on"}:
            ui_allowed = True
        elif lowered in {"false", "no", "0", "off"}:
            ui_allowed = False
        else:
            ui_allowed = None
    if not isinstance(ui_allowed, bool):
        ui_allowed = bool(ui_mechanics)

    if ui_allowed is False:
        ui_mechanics = []

    scene_card["ui_allowed"] = ui_allowed
    scene_card["ui_mechanics_expected"] = ui_mechanics
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

def run_loop(
    workspace: Path,
    book_id: str,
    steps: Optional[int] = None,
    until: Optional[str] = None,
    resume: bool = False,
    ack_outline_attention_items: bool = False,
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

    run_id = _current_run_id()
    _write_latest_run_pointer(book_root, run_id)
    set_run_log_path(_run_log_path(book_root, run_id))
    _append_run_log(book_root, run_id, f"run_id: {run_id}")
    _append_run_log(book_root, run_id, f"book_id: {book_id}")
    _append_run_log(book_root, run_id, f"started_at: {_now_iso()}")

    book = _load_json(book_path)
    outline = _load_json(outline_path)
    validate_json(outline, "outline")

    report_path, outline_report = load_latest_outline_pipeline_report(workspace=workspace, book_id=book_id)
    if outline_report:
        requires_attention = bool(outline_report.get("requires_user_attention", False))
        strict_blocking = bool(outline_report.get("strict_blocking", False))
        if requires_attention:
            summary = format_outline_pipeline_summary(outline_report, report_path=report_path).rstrip()
            if summary:
                _status(summary)
            if strict_blocking:
                raise ValueError(
                    "Outline report requires strict attention handling; run is blocked until outline issues are resolved."
                )
            if not ack_outline_attention_items:
                raise ValueError(
                    "Outline report requires attention; re-run with --ack-outline-attention-items after review."
                )
            _append_run_log(book_root, run_id, "outline_attention_ack=true")
        else:
            _append_run_log(book_root, run_id, "outline_attention_ack=false")

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
        phase_history = _load_phase_history(book_root, chapter, scene) if resume else None

        if _cursor_beyond_target(chapter, scene, target, scene_counts):
            break
        if steps_remaining is not None and steps_remaining <= 0:
            break

        scene_card_path = None
        if resume and phase_history:
            resume_artifacts = _phase_artifacts_for_resume(phase_history, "plan", ["scene_card"], book_root)
            if resume_artifacts:
                scene_card_path = resume_artifacts["scene_card"]
        if scene_card_path is None:
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
            _record_phase_success(book_root, chapter, scene, "plan", {"scene_card": _artifact_relpath(book_root, scene_card_path)})
            _status(f"Planned scene card: ch{chapter:03d} sc{scene:03d} OK")
        else:
            _status(f"Using existing scene card: ch{chapter:03d} sc{scene:03d}")
        scene_card = _load_json(scene_card_path)
        _normalize_scene_card_ui_gate(scene_card)
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
        if cast_ids:
            try:
                refreshed = refresh_appearance_projections(book_root, cast_ids)
                if refreshed:
                    _status(f"Appearance projections refreshed: {len(refreshed)}")
            except LLMRequestError as exc:
                _pause_on_quota(book_root, state_path, state, "appearance_projection", exc, scene_card)

        _status(f"Preflight state alignment: ch{chapter_num:03d} sc{scene_num:03d}...")
        preflight_patch = None
        if resume and phase_history:
            resume_artifacts = _phase_artifacts_for_resume(phase_history, "preflight", ["patch"], book_root)
            if resume_artifacts:
                preflight_patch = _load_json(resume_artifacts["patch"])
        if preflight_patch is None:
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
            artifact_path = _write_phase_artifact(book_root, chapter_num, scene_num, "preflight_patch", preflight_patch, as_json=True)
            _record_phase_success(book_root, chapter_num, scene_num, "preflight", {"patch": _artifact_relpath(book_root, artifact_path)})
        else:
            _status("Using preflight patch from phase history")
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
        continuity_pack = None
        if resume and phase_history:
            resume_artifacts = _phase_artifacts_for_resume(phase_history, "continuity_pack", ["pack"], book_root)
            if resume_artifacts:
                continuity_pack = _load_json(resume_artifacts["pack"])
        if continuity_pack is None:
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
            artifact_path = _write_phase_artifact(book_root, chapter_num, scene_num, "continuity_pack", continuity_pack, as_json=True)
            _record_phase_success(book_root, chapter_num, scene_num, "continuity_pack", {"pack": _artifact_relpath(book_root, artifact_path)})
        else:
            _status("Using continuity pack from phase history")
        _status("Continuity pack ready OK")

        base_invariants = book.get("invariants", []) if isinstance(book.get("invariants", []), list) else []

        _status(f"Writing scene: ch{chapter_num:03d} sc{scene_num:03d}...")
        prose = None
        patch = None
        if resume and phase_history:
            resume_artifacts = _phase_artifacts_for_resume(phase_history, "write", ["prose", "patch"], book_root)
            if resume_artifacts:
                prose = resume_artifacts["prose"].read_text(encoding="utf-8")
                patch = _load_json(resume_artifacts["patch"])
        if prose is None or patch is None:
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
            prose_path = _write_phase_artifact(book_root, chapter_num, scene_num, "write_prose", prose, as_json=False)
            patch_path = _write_phase_artifact(book_root, chapter_num, scene_num, "write_patch", patch, as_json=True)
            _record_phase_success(book_root, chapter_num, scene_num, "write", {"prose": _artifact_relpath(book_root, prose_path), "patch": _artifact_relpath(book_root, patch_path)})
        else:
            _status("Using write artifacts from phase history")
        _status("Write complete OK")

        _status(f"Repairing state: ch{chapter_num:03d} sc{scene_num:03d}...")
        state_repair_resumed = False
        if resume and phase_history:
            resume_repair = _phase_artifacts_for_resume(phase_history, "repair", ["prose", "patch"], book_root)
            if resume_repair:
                prose = resume_repair["prose"].read_text(encoding="utf-8")
                patch = _load_json(resume_repair["patch"])
            resume_state_repair = _phase_artifacts_for_resume(phase_history, "state_repair", ["patch"], book_root)
            if resume_state_repair:
                patch = _load_json(resume_state_repair["patch"])
                state_repair_resumed = True
        if not state_repair_resumed:
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
            patch_path = _write_phase_artifact(book_root, chapter_num, scene_num, "state_repair_patch", patch, as_json=True)
            _record_phase_success(book_root, chapter_num, scene_num, "state_repair", {"patch": _artifact_relpath(book_root, patch_path)})
        else:
            _status("Using state_repair patch from phase history")
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
        lint_report = None
        if lint_mode != "off" and resume and phase_history:
            resume_artifacts = _phase_artifacts_for_resume(phase_history, "lint", ["report"], book_root)
            if resume_artifacts:
                lint_report = _load_json(resume_artifacts["report"])
                _status("Using lint report from phase history")

        if lint_mode == "off":
            lint_report = {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "off"}
            _status("Linting disabled (mode=off).")
        else:
            if lint_report is None:
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
                report_path = _write_phase_artifact(book_root, chapter_num, scene_num, "lint_report", lint_report, as_json=True)
                _record_phase_success(book_root, chapter_num, scene_num, "lint", {"report": _artifact_relpath(book_root, report_path)})
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
                prose_path = _write_phase_artifact(book_root, chapter_num, scene_num, "repair_prose", prose, as_json=False)
                patch_path = _write_phase_artifact(book_root, chapter_num, scene_num, "repair_patch", patch, as_json=True)
                _record_phase_success(book_root, chapter_num, scene_num, "repair", {"prose": _artifact_relpath(book_root, prose_path), "patch": _artifact_relpath(book_root, patch_path)})
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
                patch_path = _write_phase_artifact(book_root, chapter_num, scene_num, "state_repair_patch", patch, as_json=True)
                _record_phase_success(book_root, chapter_num, scene_num, "state_repair", {"patch": _artifact_relpath(book_root, patch_path)})
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
                report_path = _write_phase_artifact(book_root, chapter_num, scene_num, "lint_report", lint_report, as_json=True)
                _record_phase_success(book_root, chapter_num, scene_num, "lint", {"report": _artifact_relpath(book_root, report_path)})
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
        if has_char_updates:
            appearance_ids: List[str] = []
            for update in updates:
                if not isinstance(update, dict):
                    continue
                if update.get("appearance_updates") is None:
                    continue
                char_id = str(update.get("character_id") or "").strip()
                if char_id:
                    appearance_ids.append(char_id)
            if appearance_ids:
                try:
                    refreshed = refresh_appearance_projections(book_root, appearance_ids, force=True)
                    if refreshed:
                        _status(f"Appearance projections refreshed: {len(refreshed)}")
                except LLMRequestError as exc:
                    _pause_on_quota(book_root, state_path, state, "appearance_projection", exc, scene_card)

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









































































































