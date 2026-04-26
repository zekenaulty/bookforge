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
from bookforge.pipeline.config import _style_anchor_max_tokens, _durable_slice_max_expansions, _lint_mode, _lint_repair_max_passes
from bookforge.pipeline.outline import _outline_summary, _build_character_registry, _build_thread_registry, _character_name_map, _character_id_map
from bookforge.pipeline.scene import _scene_cast_ids_from_outline, _load_character_states, _parse_until
from bookforge.pipeline.state_apply import _summary_from_state, _apply_state_patch, _apply_character_updates, _apply_character_stat_updates, _update_bible, _rollup_chapter_summary, _compile_chapter_markdown
from bookforge.pipeline.durable import _apply_durable_state_updates
from bookforge.pipeline.io import _load_json, _snapshot_character_states_before_preflight, _log_scope, _write_scene_files
from bookforge.pipeline.phase_history import _load_phase_history, _record_phase_success, _write_phase_artifact
from bookforge.pipeline.run_logging import _current_run_id, _write_latest_run_pointer, _run_log_path, _append_run_log, _write_run_progress
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
from bookforge.contracts import MAIN_BRANCH_ID
from bookforge.supervision import (
    RuntimeIssue,
    capture_main_branch_snapshot,
    capture_surface_snapshot,
    emit_reconciled_main_branch_contracts,
    emit_reconciled_branch_contracts,
    paths as supervision_paths,
)
from bookforge.util.schema import validate_json
from bookforge.outline import (
    load_latest_outline_pipeline_report,
    format_outline_pipeline_summary,
)

PAUSE_EXIT_CODE = 75


def _execution_book_root(workspace: Path, book_id: str, branch_id: str) -> Path:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_branch_id == MAIN_BRANCH_ID:
        return workspace / "books" / book_id
    return supervision_paths.branch_snapshot_root(workspace / "books" / book_id, resolved_branch_id)


def _execution_context(book_root: Path) -> Tuple[Path, str, str]:
    if (
        book_root.name == "snapshot"
        and len(book_root.parents) >= 5
        and book_root.parent.parent.name == "branches"
        and book_root.parent.parent.parent.name == "supervision"
    ):
        canonical_root = book_root.parents[4]
        return canonical_root.parent.parent, canonical_root.name, book_root.parent.name
    return book_root.parent.parent, book_root.name, MAIN_BRANCH_ID


def _capture_execution_snapshot(workspace: Path, book_id: str, branch_id: str):
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_branch_id == MAIN_BRANCH_ID:
        return capture_main_branch_snapshot(workspace, book_id)
    return capture_surface_snapshot(workspace, book_id, branch_id=resolved_branch_id)


def _emit_reconciled_execution_contracts(
    *,
    workspace: Path,
    book_id: str,
    branch_id: str,
    before_snapshot,
    action: str,
    result_status: str,
    message: str,
    runtime_issues=None,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts=None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
):
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_branch_id == MAIN_BRANCH_ID:
        return emit_reconciled_main_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            before_snapshot=before_snapshot,
            action=action,
            result_status=result_status,
            request_id=request_id,
            message=message,
            runtime_issues=runtime_issues,
            artifact_paths=artifact_paths,
            produced_artifacts=produced_artifacts,
            details=details,
        )
    return emit_reconciled_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=resolved_branch_id,
        before_snapshot=before_snapshot,
        action=action,
        result_status=result_status,
        request_id=request_id,
        message=message,
        runtime_issues=runtime_issues,
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details=details,
    )

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
    _, context_book_id, branch_id = _execution_context(book_root)
    payload: Dict[str, Any] = {
        "book_id": context_book_id,
        "branch_id": branch_id,
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


def _emit_pause_contracts(
    *,
    book_root: Path,
    before_snapshot,
    phase: str,
    message: str,
    runtime_issue: RuntimeIssue,
    pause_path: Path,
    state_path: Path,
    scene_card: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    workspace, context_book_id, branch_id = _execution_context(book_root)
    artifact_paths: Dict[str, str] = {
        "pause_marker": _artifact_relpath(book_root, pause_path),
        "state": _artifact_relpath(book_root, state_path),
    }
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        scene = _maybe_int(scene_card.get("scene"))
        if chapter is not None and scene is not None:
            prose_path = book_root / "draft" / "chapters" / f"ch_{chapter:03d}" / f"scene_{scene:03d}.md"
            if prose_path.exists():
                artifact_paths["scene_prose"] = _artifact_relpath(book_root, prose_path)
    _emit_reconciled_execution_contracts(
        workspace=workspace,
        book_id=context_book_id,
        branch_id=branch_id,
        before_snapshot=before_snapshot,
        action="run_loop",
        result_status="retryable_pause",
        message=message,
        runtime_issues=[runtime_issue],
        artifact_paths=artifact_paths,
        details={"phase": str(phase).strip(), **dict(details or {})},
    )


def _pause_on_reason(
    book_root: Path,
    state_path: Path,
    state: Optional[Dict[str, Any]],
    run_id: Optional[str],
    phase: str,
    reason_code: str,
    message: str,
    scene_card: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    workspace, context_book_id, branch_id = _execution_context(book_root)
    before_snapshot = _capture_execution_snapshot(workspace, context_book_id, branch_id)
    if state is not None:
        try:
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception:
            pass
    if run_id:
        progress_payload: Dict[str, Any] = {
            "book_id": context_book_id,
            "branch_id": branch_id,
            "status": "paused",
            "phase": str(phase).strip(),
            "reason_code": str(reason_code).strip(),
            "message": str(message).strip(),
        }
        if scene_card:
            chapter = _maybe_int(scene_card.get("chapter"))
            scene = _maybe_int(scene_card.get("scene"))
            section = _maybe_int(scene_card.get("section_id"))
            if chapter is not None:
                progress_payload["chapter"] = chapter
            if scene is not None:
                progress_payload["scene"] = scene
            if section is not None:
                progress_payload["section"] = section
        _write_run_progress(book_root, run_id, progress_payload)
    pause_path = _write_reason_pause_marker(book_root, phase, reason_code, message, scene_card, details)
    _emit_pause_contracts(
        book_root=book_root,
        before_snapshot=before_snapshot,
        phase=phase,
        message=message,
        runtime_issue=RuntimeIssue(
            category="recovery_mode_required",
            code=str(reason_code).strip() or "recovery_mode_required",
            severity="high",
            message=message,
            details=dict(details or {}),
        ),
        pause_path=pause_path,
        state_path=state_path,
        scene_card=scene_card,
        details={"reason_code": str(reason_code).strip() or None},
    )
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
    _, context_book_id, branch_id = _execution_context(book_root)
    payload: Dict[str, Any] = {
        "book_id": context_book_id,
        "branch_id": branch_id,
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
    run_id: Optional[str],
    phase: str,
    error: LLMRequestError,
    scene_card: Optional[Dict[str, Any]] = None,
) -> None:
    workspace, context_book_id, branch_id = _execution_context(book_root)
    before_snapshot = _capture_execution_snapshot(workspace, context_book_id, branch_id)
    if error.status_code != 429 and not error.quota_violations:
        raise error
    if state is not None:
        try:
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception:
            pass
    progress_payload: Dict[str, Any] = {
        "book_id": context_book_id,
        "branch_id": branch_id,
        "status": "paused",
        "phase": str(phase).strip(),
        "reason_code": "quota",
        "message": str(error),
        "retry_after_seconds": error.retry_after_seconds,
    }
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        scene = _maybe_int(scene_card.get("scene"))
        section = _maybe_int(scene_card.get("section_id"))
        if chapter is not None:
            progress_payload["chapter"] = chapter
        if scene is not None:
            progress_payload["scene"] = scene
        if section is not None:
            progress_payload["section"] = section
    if run_id:
        _write_run_progress(book_root, run_id, progress_payload)
    pause_path = _write_pause_marker(book_root, phase, error, scene_card)
    _emit_pause_contracts(
        book_root=book_root,
        before_snapshot=before_snapshot,
        phase=phase,
        message=str(error),
        runtime_issue=RuntimeIssue(
            category="provider_retry_exhausted",
            code="quota_exhausted" if error.quota_violations or error.status_code == 429 else "provider_retry_exhausted",
            severity="high",
            message=str(error),
            details={
                "status_code": error.status_code,
                "retry_after_seconds": error.retry_after_seconds,
            },
        ),
        pause_path=pause_path,
        state_path=state_path,
        scene_card=scene_card,
        details={
            "status_code": error.status_code,
            "retry_after_seconds": error.retry_after_seconds,
        },
    )
    _status(f"Run paused due to quota in phase '{phase}': {error}")
    raise SystemExit(PAUSE_EXIT_CODE)

def _apply_durable_updates_or_pause(
    book_root: Path,
    state_path: Path,
    state: Optional[Dict[str, Any]],
    run_id: Optional[str],
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
            run_id=run_id,
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


def _scene_result_artifact_path(book_root: Path, result: ExecutionResult, artifact_key: str) -> Optional[Path]:
    raw_path = result.artifact_paths.get(artifact_key)
    if not raw_path:
        return None
    candidate = Path(str(raw_path))
    if not candidate.is_absolute():
        candidate = book_root / candidate
    return candidate if candidate.exists() else None


def _dispatch_scene_phase_action(*args, **kwargs):
    from bookforge.execution.scene_sequence import run_scene_phase_action

    return run_scene_phase_action(*args, **kwargs)


def _write_scene_action_pause_marker(
    book_root: Path,
    phase: str,
    result: ExecutionResult,
    scene_card: Optional[Dict[str, Any]] = None,
) -> Path:
    context_dir = book_root / "draft" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    details = result.details if isinstance(result.details, dict) else {}
    _, context_book_id, branch_id = _execution_context(book_root)
    payload: Dict[str, Any] = {
        "book_id": context_book_id,
        "branch_id": branch_id,
        "phase": str(phase).strip(),
        "status_code": details.get("status_code"),
        "message": result.message,
        "retry_after_seconds": details.get("retry_after_seconds"),
        "created_at": _now_iso(),
    }
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        scene = _maybe_int(scene_card.get("scene"))
        section = _maybe_int(scene_card.get("section_id"))
        if chapter is not None:
            payload["chapter"] = chapter
        if scene is not None:
            payload["scene"] = scene
        if section is not None:
            payload["section"] = section
    pause_path = context_dir / "run_paused.json"
    pause_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return pause_path


def _pause_on_scene_action_result(
    *,
    book_root: Path,
    state_path: Path,
    state: Optional[Dict[str, Any]],
    run_id: Optional[str],
    phase: str,
    result: ExecutionResult,
    scene_card: Optional[Dict[str, Any]] = None,
) -> None:
    workspace, context_book_id, branch_id = _execution_context(book_root)
    before_snapshot = _capture_execution_snapshot(workspace, context_book_id, branch_id)
    if state is not None:
        try:
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception:
            pass
    details = result.details if isinstance(result.details, dict) else {}
    progress_payload: Dict[str, Any] = {
        "book_id": context_book_id,
        "branch_id": branch_id,
        "status": "paused",
        "phase": str(phase).strip(),
        "reason_code": str(details.get("failure_code") or "provider_retry_exhausted").strip(),
        "message": result.message,
        "retry_after_seconds": details.get("retry_after_seconds"),
    }
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        scene = _maybe_int(scene_card.get("scene"))
        section = _maybe_int(scene_card.get("section_id"))
        if chapter is not None:
            progress_payload["chapter"] = chapter
        if scene is not None:
            progress_payload["scene"] = scene
        if section is not None:
            progress_payload["section"] = section
    if run_id:
        _write_run_progress(book_root, run_id, progress_payload)
    pause_path = _write_scene_action_pause_marker(book_root, phase, result, scene_card)
    _emit_pause_contracts(
        book_root=book_root,
        before_snapshot=before_snapshot,
        phase=phase,
        message=result.message,
        runtime_issue=RuntimeIssue(
            category="provider_retry_exhausted",
            code=str(details.get("failure_code") or "provider_retry_exhausted").strip() or "provider_retry_exhausted",
            severity="high",
            message=result.message,
            details={
                "status_code": details.get("status_code"),
                "retry_after_seconds": details.get("retry_after_seconds"),
                "action": result.action,
            },
        ),
        pause_path=pause_path,
        state_path=state_path,
        scene_card=scene_card,
        details={
            "status_code": details.get("status_code"),
            "retry_after_seconds": details.get("retry_after_seconds"),
            "action": result.action,
        },
    )
    _status(f"Run paused in phase '{phase}': {result.message}")
    raise SystemExit(PAUSE_EXIT_CODE)


def _run_scene_via_actions(
    *,
    workspace: Path,
    book_root: Path,
    book_id: str,
    state_path: Path,
    outline: Dict[str, Any],
    run_id: str,
    chapter_num: int,
    scene_num: int,
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    update_progress,
    branch_id: str = MAIN_BRANCH_ID,
) -> None:
    durable_expand_ids: set[str] = set()
    durable_expand_attempts = 0
    durable_expand_max = _durable_slice_max_expansions()
    max_repair_passes = max(_lint_repair_max_passes(), durable_expand_max)

    section_id: Optional[int] = None
    scene_card: Optional[Dict[str, Any]] = None

    def execute(action: str, *, progress_phase: str, start_message: str, done_message: str, repair_pass: Optional[int] = None) -> ExecutionResult:
        nonlocal section_id, scene_card
        update_progress(
            status="running",
            phase=progress_phase,
            chapter=chapter_num,
            scene=scene_num,
            section=section_id,
            scene_card=scene_card,
            repair_pass=repair_pass,
            repair_pass_limit=max_repair_passes if repair_pass is not None else None,
            message=start_message,
        )
        _status(f"{start_message}: ch{chapter_num:03d} sc{scene_num:03d}...")
        result = _dispatch_scene_phase_action(
            workspace,
            book_id,
            action,
            chapter_id=chapter_num,
            scene_id=scene_num,
            section_id=section_id,
            branch_id=branch_id,
            extra_details={"durable_expand_ids": sorted(durable_expand_ids)},
        )
        if result.status == "retryable_pause":
            state_payload = _load_json(state_path) if state_path.exists() else None
            _pause_on_scene_action_result(
                book_root=book_root,
                state_path=state_path,
                state=state_payload,
                run_id=run_id,
                phase=progress_phase,
                result=result,
                scene_card=scene_card,
            )
        if result.status == "hard_fail":
            raise ValueError(result.message)

        artifact_path = None
        if result.artifact_paths:
            first_key = next(iter(result.artifact_paths.keys()))
            artifact_path = _scene_result_artifact_path(book_root, result, first_key)
        if result.status == "no_op":
            _status(f"{done_message} reused existing outputs")
        else:
            _status(f"{done_message} OK")
        update_progress(
            status="running",
            phase=progress_phase,
            chapter=chapter_num,
            scene=scene_num,
            section=section_id,
            scene_card=scene_card,
            repair_pass=repair_pass,
            repair_pass_limit=max_repair_passes if repair_pass is not None else None,
            artifact_path=artifact_path,
            message=done_message,
        )
        return result

    plan_result = execute(
        "plan_scene",
        progress_phase="plan_scene",
        start_message="Planning scene",
        done_message="Scene card ready",
    )
    scene_card_path = _scene_result_artifact_path(book_root, plan_result, "scene_card")
    if scene_card_path is None:
        raise ValueError("plan_scene did not leave a scene card artifact for the active scene.")
    scene_card = _load_json(scene_card_path)
    _normalize_scene_card_ui_gate(scene_card)
    validate_json(scene_card, "scene_card")
    section_id = _maybe_int(scene_card.get("section_id"))

    cast_ids = scene_card.get("cast_present_ids", []) if isinstance(scene_card, dict) else []
    if not isinstance(cast_ids, list):
        cast_ids = []
    cast_ids = [str(item) for item in cast_ids if str(item).strip()]
    if not cast_ids:
        derived = _scene_cast_ids_from_outline(outline, chapter_num, scene_num)
        if derived:
            scene_card["cast_present_ids"] = derived
            cast_ids = list(derived)
    if cast_ids and not scene_card.get("cast_present"):
        name_map = _character_name_map(_build_character_registry(outline))
        scene_card["cast_present"] = [name_map.get(item, item) for item in cast_ids]
    scene_card_path.write_text(json.dumps(scene_card, ensure_ascii=True, indent=2), encoding="utf-8")

    update_progress(
        status="running",
        phase="scene_ready",
        chapter=chapter_num,
        scene=scene_num,
        section=section_id,
        scene_card=scene_card,
        artifact_path=scene_card_path,
        message="Scene card resolved.",
    )

    if cast_ids:
        try:
            refreshed = refresh_appearance_projections(book_root, cast_ids)
            if refreshed:
                _status(f"Appearance projections refreshed: {len(refreshed)}")
        except LLMRequestError as exc:
            _pause_on_quota(book_root, state_path, _load_json(state_path), run_id, "appearance_projection", exc, scene_card)

    execute(
        "preflight_scene_state",
        progress_phase="preflight_scene_state",
        start_message="Preflight state alignment",
        done_message="Preflight alignment complete",
    )
    execute(
        "generate_continuity_pack",
        progress_phase="generate_continuity_pack",
        start_message="Generating continuity pack",
        done_message="Continuity pack ready",
    )
    execute(
        "write_scene_prose",
        progress_phase="write_scene_prose",
        start_message="Writing scene",
        done_message="Write complete",
    )
    execute(
        "state_repair_scene_patch",
        progress_phase="state_repair_scene_patch",
        start_message="Repairing state",
        done_message="State repair complete",
    )
    lint_result = execute(
        "lint_scene_prose",
        progress_phase="lint_scene_prose",
        start_message="Linting scene",
        done_message="Lint complete",
    )
    lint_report_path = _scene_result_artifact_path(book_root, lint_result, "lint_report")
    if lint_report_path is None:
        raise ValueError("lint_scene_prose did not leave a lint report artifact for the active scene.")
    lint_report = _load_json(lint_report_path)
    _status(f"Lint status: {lint_report.get('status', 'unknown')}")

    repair_passes = 0
    if _lint_mode() != "off" and lint_report.get("status") == "fail":
        while repair_passes < max_repair_passes:
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

            repair_passes += 1
            execute(
                "repair_scene_prose",
                progress_phase="repair_scene_prose",
                start_message="Repairing scene",
                done_message="Repair complete",
                repair_pass=repair_passes,
            )
            execute(
                "state_repair_scene_patch",
                progress_phase="state_repair_scene_patch",
                start_message="Repairing state",
                done_message="State repair complete",
                repair_pass=repair_passes,
            )
            lint_result = execute(
                "lint_scene_prose",
                progress_phase="lint_scene_prose",
                start_message="Linting scene",
                done_message="Lint complete",
                repair_pass=repair_passes,
            )
            lint_report_path = _scene_result_artifact_path(book_root, lint_result, "lint_report")
            if lint_report_path is None:
                raise ValueError("lint_scene_prose did not leave a lint report artifact after repair.")
            lint_report = _load_json(lint_report_path)
            _status(f"Lint status: {lint_report.get('status', 'unknown')}")
            if lint_report.get("status") != "fail":
                break
            if _lint_mode() == "strict":
                if not _lint_has_issue_code(lint_report, "durable_slice_missing"):
                    break
                requested_ids = _durable_slice_retry_ids(lint_report)
                new_ids = [item for item in requested_ids if item not in durable_expand_ids]
                if not new_ids or durable_expand_attempts >= durable_expand_max:
                    break

        if lint_report.get("status") == "fail" and _lint_mode() == "strict":
            if _lint_has_issue_code(lint_report, "durable_slice_missing"):
                state_payload = _load_json(state_path) if state_path.exists() else None
                _pause_on_reason(
                    book_root,
                    state_path,
                    state_payload,
                    run_id,
                    "lint_scene_prose",
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

    execute(
        "apply_scene_commit",
        progress_phase="apply_scene_commit",
        start_message="Applying scene commit",
        done_message="Scene commit complete",
    )

    updated_state = _load_json(state_path)
    next_cursor = updated_state.get("cursor", {}) if isinstance(updated_state.get("cursor"), dict) else {}
    next_chapter = _maybe_int(next_cursor.get("chapter")) or chapter_num
    next_scene = _maybe_int(next_cursor.get("scene")) or scene_num
    _status(f"Advancing cursor -> ch{next_chapter:03d} sc{next_scene:03d}")
    update_progress(
        status="running",
        phase="cursor_advance",
        chapter=next_chapter,
        scene=next_scene,
        section=section_id,
        scene_card=scene_card,
        message="Cursor advanced to next scene.",
    )

def _run_write_scope(
    workspace: Path,
    book_id: str,
    steps: Optional[int] = None,
    until: Optional[str] = None,
    resume: bool = False,
    ack_outline_attention_items: bool = False,
    force_outline_gate_bypass: bool = False,
    branch_id: str = MAIN_BRANCH_ID,
) -> None:
    branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    book_root = _execution_book_root(workspace, book_id, branch_id)
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
    before_snapshot = _capture_execution_snapshot(workspace, book_id, branch_id)

    run_id = _current_run_id()
    run_log_path = _run_log_path(book_root, run_id)
    _write_latest_run_pointer(book_root, run_id)
    set_run_log_path(run_log_path)
    _append_run_log(book_root, run_id, f"run_id: {run_id}")
    _append_run_log(book_root, run_id, f"book_id: {book_id}")
    _append_run_log(book_root, run_id, f"started_at: {_now_iso()}")
    pause_marker_path = book_root / "draft" / "context" / "run_paused.json"
    if pause_marker_path.exists():
        pause_marker_path.unlink()

    def update_progress(
        *,
        status: str,
        phase: str,
        chapter: Optional[int] = None,
        scene: Optional[int] = None,
        section: Optional[int] = None,
        turn: Optional[str] = None,
        repair_pass: Optional[int] = None,
        repair_pass_limit: Optional[int] = None,
        message: Optional[str] = None,
        artifact_path: Optional[Path] = None,
        scene_card: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "book_id": book_id,
            "status": str(status).strip(),
            "phase": str(phase).strip(),
            "run_log_path": _artifact_relpath(book_root, run_log_path),
        }
        if message:
            payload["message"] = str(message).strip()
        if scene_card:
            chapter = chapter if chapter is not None else _maybe_int(scene_card.get("chapter"))
            scene = scene if scene is not None else _maybe_int(scene_card.get("scene"))
            section = section if section is not None else _maybe_int(scene_card.get("section_id"))
        if chapter is not None:
            payload["chapter"] = int(chapter)
        if scene is not None:
            payload["scene"] = int(scene)
        if section is not None:
            payload["section"] = int(section)
        if turn:
            payload["turn"] = str(turn).strip()
        if repair_pass is not None:
            payload["repair_pass"] = int(repair_pass)
        if repair_pass_limit is not None:
            payload["repair_pass_limit"] = int(repair_pass_limit)
        if artifact_path is not None:
            payload["last_artifact_path"] = _artifact_relpath(book_root, artifact_path)
        _write_run_progress(book_root, run_id, payload)

    update_progress(status="starting", phase="run_init", message="Run initialized.")

    book = _load_json(book_path)
    outline = _load_json(outline_path)
    validate_json(outline, "outline")

    report_path, outline_report = load_latest_outline_pipeline_report(
        workspace=workspace,
        book_id=book_id,
    )
    outline_attention_ack = False
    if not outline_report:
        if not force_outline_gate_bypass:
            raise ValueError(
                "WRITE GATED: outline pipeline report is missing or unreadable. "
                "Run outline generation first, or use --force-outline-gate-bypass for testing."
            )
        _status(
            "WRITE GATE BYPASS ENABLED: continuing without a readable outline pipeline report."
        )
        _append_run_log(book_root, run_id, "outline_gate_bypass=true reason=missing_report")
    else:
        overall_status = str(outline_report.get("overall_status") or "UNKNOWN").strip().upper()
        requires_attention = bool(outline_report.get("requires_user_attention", False))
        attention_items = (
            outline_report.get("attention_items")
            if isinstance(outline_report.get("attention_items"), list)
            else []
        )
        strict_blocking = any(
            isinstance(item, dict) and str(item.get("severity") or "").strip().lower() == "error"
            for item in attention_items
        )
        summary = format_outline_pipeline_summary(outline_report, report_path=report_path).rstrip()
        if summary:
            _status(summary)

        if overall_status not in {"SUCCESS", "SUCCESS_WITH_WARNINGS"}:
            if not force_outline_gate_bypass:
                raise ValueError(
                    "WRITE GATED: latest outline pipeline status is "
                    f"{overall_status}. Resolve outline pipeline issues before writing. "
                    f"Report: {report_path}"
                )
            _status(
                "WRITE GATE BYPASS ENABLED: continuing despite outline pipeline status "
                f"{overall_status}. Report: {report_path}"
            )
            _append_run_log(
                book_root,
                run_id,
                f"outline_gate_bypass=true reason=status_{overall_status.lower()}",
            )

        if requires_attention:
            if strict_blocking:
                if not force_outline_gate_bypass:
                    raise ValueError(
                        "WRITE GATED: outline report requires strict attention handling; "
                        "resolve outline issues before writing."
                    )
                _status("WRITE GATE BYPASS ENABLED: strict outline attention gate bypassed.")
                _append_run_log(book_root, run_id, "outline_gate_bypass=true reason=strict_attention")
            elif not ack_outline_attention_items and not force_outline_gate_bypass:
                raise ValueError(
                    "WRITE GATED: outline report requires attention. "
                    "Re-run with --ack-outline-attention-items only after review."
                )
            outline_attention_ack = bool(ack_outline_attention_items)

    _append_run_log(
        book_root,
        run_id,
        f"outline_attention_ack={'true' if outline_attention_ack else 'false'}",
    )
    if not force_outline_gate_bypass:
        _append_run_log(book_root, run_id, "outline_gate_bypass=false")
    update_progress(
        status="running",
        phase="outline_gate",
        message="Outline gate checks complete.",
    )

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
            _pause_on_quota(book_root, state_path, None, run_id, "characters_generate", exc)
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
        _pause_on_quota(book_root, state_path, None, run_id, "style_anchor", exc)
    update_progress(
        status="running",
        phase="style_anchor",
        message="Style anchor ready.",
    )

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

        _run_scene_via_actions(
            workspace=workspace,
            book_root=book_root,
            book_id=book_id,
            state_path=state_path,
            outline=outline,
            run_id=run_id,
            chapter_num=chapter,
            scene_num=scene,
            chapter_order=chapter_order,
            scene_counts=scene_counts,
            update_progress=update_progress,
            branch_id=branch_id,
        )

        if steps_remaining is not None:
            steps_remaining -= 1

    final_state = _load_json(state_path)
    final_cursor = final_state.get("cursor", {}) if isinstance(final_state.get("cursor"), dict) else {}
    update_progress(
        status="complete" if str(final_state.get("status") or "").strip().upper() == "COMPLETE" else "idle",
        phase="run_complete",
        chapter=_maybe_int(final_cursor.get("chapter")),
        scene=_maybe_int(final_cursor.get("scene")),
        message="Run loop exited cleanly.",
    )
    _emit_reconciled_execution_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        before_snapshot=before_snapshot,
        action="run_loop",
        result_status="success",
        message="Run loop exited cleanly.",
        artifact_paths={
            "state": _artifact_relpath(book_root, state_path),
            "outline": _artifact_relpath(book_root, outline_path),
            "run_log": _artifact_relpath(book_root, run_log_path),
        },
        details={
            "final_state_status": str(final_state.get("status") or "").strip(),
            "final_chapter": _maybe_int(final_cursor.get("chapter")),
            "final_scene": _maybe_int(final_cursor.get("scene")),
        },
    )


def _set_cursor_for_scene_range(
    state_path: Path,
    *,
    chapter_id: int,
    scene_start: int,
    scene_end: int,
) -> None:
    if not state_path.exists():
        return
    state = _load_json(state_path)
    cursor = state.get("cursor") if isinstance(state.get("cursor"), dict) else {}
    current_chapter = _maybe_int(cursor.get("chapter")) or 0
    current_scene = _maybe_int(cursor.get("scene")) or 0
    if current_chapter == chapter_id and scene_start <= current_scene <= scene_end:
        return
    state["cursor"] = {"chapter": chapter_id, "scene": scene_start}
    state["status"] = "OUTLINED"
    validate_json(state, "state")
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")


def run_section_range(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    section_id: int,
    scene_start: int,
    scene_end: int,
    resume: bool = False,
    ack_outline_attention_items: bool = False,
    force_outline_gate_bypass: bool = False,
    branch_id: str = MAIN_BRANCH_ID,
) -> None:
    if scene_start <= 0 or scene_end <= 0 or scene_end < scene_start:
        raise ValueError("run_section_range requires a valid inclusive scene range.")
    branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    book_root = _execution_book_root(workspace, book_id, branch_id)
    state_path = book_root / "state.json"
    if not resume:
        _set_cursor_for_scene_range(
            state_path,
            chapter_id=chapter_id,
            scene_start=scene_start,
            scene_end=scene_end,
        )
    _run_write_scope(
        workspace=workspace,
        book_id=book_id,
        until=f"chapter:{chapter_id}:scene:{scene_end}",
        resume=resume,
        ack_outline_attention_items=ack_outline_attention_items,
        force_outline_gate_bypass=force_outline_gate_bypass,
        branch_id=branch_id,
    )


def run_loop(
    workspace: Path,
    book_id: str,
    steps: Optional[int] = None,
    until: Optional[str] = None,
    resume: bool = False,
    ack_outline_attention_items: bool = False,
    force_outline_gate_bypass: bool = False,
    branch_id: str = MAIN_BRANCH_ID,
) -> None:
    _run_write_scope(
        workspace=workspace,
        book_id=book_id,
        steps=steps,
        until=until,
        resume=resume,
        ack_outline_attention_items=ack_outline_attention_items,
        force_outline_gate_bypass=force_outline_gate_bypass,
        branch_id=branch_id,
    )

def run() -> None:
    raise NotImplementedError("Use run_loop via CLI.")










































































