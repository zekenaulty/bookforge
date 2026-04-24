from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
import json

from bookforge.config.env import load_config
from bookforge.characters import refresh_appearance_projections
from bookforge.contracts import (
    ExecutionRequest,
    ExecutionResult,
    MAIN_BRANCH_ID,
    ProducedArtifactReceipt,
    ScopeSelector,
    TimelineNodeRef,
)
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.memory.continuity import load_style_anchor, style_anchor_path
from bookforge.phases.continuity_phase import _generate_continuity_pack
from bookforge.phases.lint_phase import _lint_scene
from bookforge.phases.plan import plan_scene as _plan_scene
from bookforge.phases.preflight_phase import _scene_state_preflight
from bookforge.phases.repair_phase import _repair_scene
from bookforge.phases.state_repair_phase import _state_repair
from bookforge.phases.write_phase import _write_scene
from bookforge.pipeline.durable import _apply_durable_state_updates, _durable_mutation_payload
from bookforge.pipeline.io import _write_scene_files
from bookforge.pipeline.outline import _build_character_registry, _build_thread_registry, _outline_summary
from bookforge.pipeline.phase_history import _load_phase_history, _record_phase_success, _write_phase_artifact
from bookforge.pipeline.scene_phase_artifacts import load_scene_phase_artifact_state
from bookforge.pipeline.scene import _load_character_states
from bookforge.pipeline.config import _lint_mode
from bookforge.pipeline.state_apply import (
    _apply_character_stat_updates,
    _apply_character_updates,
    _apply_state_patch,
    _compile_chapter_markdown,
    _rollup_chapter_summary,
    _summary_from_state,
    _update_bible,
)
from bookforge.query import current_main_node
from bookforge.query.scene_phase import get_scene_phase_readiness as _get_scene_phase_readiness
from bookforge.supervision import (
    RuntimeIssue,
    capture_main_branch_snapshot,
    emit_reconciled_main_branch_contracts,
    paths as supervision_paths,
)
from bookforge.util.schema import validate_json


def _now_token() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_relpath(book_root: Path, path: Path) -> str:
    try:
        return path.relative_to(book_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _append_execution_result(book_root: Path, result: ExecutionResult) -> None:
    path = supervision_paths.execution_results_path(book_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result.to_dict(), ensure_ascii=True) + "\n")


def _phase_artifact_path(book_root: Path, phase_history: Dict[str, Any], phase: str, artifact_key: str) -> Optional[Path]:
    phases = phase_history.get("phases") if isinstance(phase_history, dict) else None
    if not isinstance(phases, dict):
        return None
    entry = phases.get(phase)
    if not isinstance(entry, dict):
        return None
    artifacts = entry.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    raw_path = artifacts.get(artifact_key)
    if not raw_path:
        return None
    candidate = Path(str(raw_path))
    if not candidate.is_absolute():
        candidate = book_root / candidate
    return candidate if candidate.exists() else None


def _build_execution_node(
    *,
    live_node: TimelineNodeRef,
    chapter_id: int,
    section_id: Optional[int],
    scene_id: int,
    phase_id: str,
) -> TimelineNodeRef:
    return TimelineNodeRef(
        book_id=live_node.book_id,
        workflow_family="section_write",
        source_run_id=live_node.source_run_id,
        branch_id=live_node.branch_id,
        fork_group_id=live_node.fork_group_id,
        chapter=chapter_id,
        section=section_id,
        scene=scene_id,
        phase_id=phase_id,
        turn_id=None,
        revision_id=live_node.revision_id,
    )


def _hash_id(*parts: str) -> str:
    seed = "|".join(parts)
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _result_for_request(
    *,
    request: ExecutionRequest,
    node: TimelineNodeRef,
    status: str,
    message: str,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts: Optional[List[ProducedArtifactReceipt]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    return ExecutionResult(
        result_id=_hash_id(
            request.selector.book_id,
            request.request_id,
            status,
            node.revision_id,
            _now_token(),
        ),
        action=request.action,
        status=status,
        node=node,
        selector=request.selector,
        message=message,
        artifact_paths=dict(artifact_paths or {}),
        produced_artifacts=list(produced_artifacts or []),
        details=dict(details or {}),
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def _emit_reconciled_result_for_request(
    *,
    workspace: Path,
    book_id: str,
    request: ExecutionRequest,
    before_snapshot,
    status: str,
    message: str,
    artifact_paths: Optional[Dict[str, str]] = None,
    produced_artifacts: Optional[List[ProducedArtifactReceipt]] = None,
    runtime_issue: Optional[RuntimeIssue] = None,
    details: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    bundle = emit_reconciled_main_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        before_snapshot=before_snapshot,
        action=request.action,
        result_status=status,
        request_id=request.request_id,
        message=message,
        runtime_issues=[runtime_issue] if runtime_issue else None,
        artifact_paths=dict(artifact_paths or {}),
        produced_artifacts=list(produced_artifacts or []),
        details=dict(details or {}),
    )
    if bundle.execution_result is not None:
        return bundle.execution_result
    node = current_main_node(workspace, book_id, prefer_emitted=False) or request.expected_node
    if node is None:
        raise ValueError("Unable to resolve node for reconciled scene action result.")
    return ExecutionResult(
        result_id=_hash_id(
            request.selector.book_id,
            request.request_id,
            status,
            node.revision_id,
            _now_token(),
        ),
        action=request.action,
        status=status,
        node=node,
        selector=request.selector,
        message=message,
        artifact_paths=dict(artifact_paths or {}),
        produced_artifacts=list(produced_artifacts or []),
        details=dict(details or {}),
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def _classify_live_node_mismatch(
    expected_node: Optional[TimelineNodeRef],
    live_node: Optional[TimelineNodeRef],
    *,
    action: str,
) -> tuple[str, str]:
    if expected_node is None or live_node is None:
        return (
            "scope_contract_violation",
            "Live node does not match the expected execution scope.",
        )
    expected = expected_node.to_dict()
    live = live_node.to_dict()
    comparable_keys = (
        "book_id",
        "workflow_family",
        "source_run_id",
        "branch_id",
        "fork_group_id",
        "chapter",
        "section",
        "scene",
        "phase_id",
        "turn_id",
    )
    if all(expected.get(key) == live.get(key) for key in comparable_keys) and expected.get("revision_id") != live.get("revision_id"):
        return (
            "stale_write",
            f"Requested {action} target has been superseded by a newer main-branch revision.",
        )
    return (
        "scope_contract_violation",
        "Live node does not match the expected execution scope.",
    )


def _unsupported_preflight_reasons(preflight_patch: Dict[str, Any]) -> List[str]:
    reasons: List[str] = []
    if isinstance(preflight_patch.get("character_updates"), list) and preflight_patch.get("character_updates"):
        reasons.append("preflight patch contains provisional character_updates")
    if isinstance(preflight_patch.get("character_continuity_system_updates"), list) and preflight_patch.get("character_continuity_system_updates"):
        reasons.append("preflight patch contains provisional character_continuity_system_updates")
    if _durable_mutation_payload(preflight_patch):
        reasons.append("preflight patch contains provisional durable mutations")
    return reasons


def _chapter_end_status(chapter_order: List[int], scene_counts: Dict[int, int], chapter_id: int, scene_id: int) -> tuple[bool, int, int, bool]:
    chapter_total = scene_counts.get(chapter_id)
    chapter_end = isinstance(chapter_total, int) and chapter_total > 0 and scene_id >= chapter_total
    cursor_override = None
    if chapter_total and scene_id < chapter_total:
        return chapter_end, chapter_id, scene_id + 1, False
    if chapter_id in chapter_order:
        index = chapter_order.index(chapter_id)
        if index + 1 < len(chapter_order):
            return chapter_end, chapter_order[index + 1], 1, False
    return chapter_end, chapter_id + 1, 1, True


def _write_scene_phase_pause_marker(
    *,
    book_root: Path,
    phase: str,
    chapter_id: int,
    section_id: Optional[int],
    scene_id: int,
    error: LLMRequestError,
) -> Path:
    context_dir = book_root / "draft" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "book_id": book_root.name,
        "phase": phase,
        "chapter": chapter_id,
        "section": section_id,
        "scene": scene_id,
        "status_code": error.status_code,
        "message": error.message,
        "retry_after_seconds": error.retry_after_seconds,
        "created_at": _now_token(),
    }
    path = context_dir / "scene_phase_paused.json"
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _durable_expand_ids_from_request(request: ExecutionRequest) -> List[str]:
    raw_ids = request.details.get("durable_expand_ids")
    if not isinstance(raw_ids, list):
        return []
    normalized: List[str] = []
    for item in raw_ids:
        token = str(item or "").strip()
        if token and token not in normalized:
            normalized.append(token)
    return normalized


def build_plan_scene_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for plan_scene.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="plan_scene",
    )
    request_seed = "|".join(
        [
            book_id,
            "plan_scene",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="plan_scene",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def build_write_scene_prose_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for write_scene_prose.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="write_scene_prose",
    )
    request_seed = "|".join(
        [
            book_id,
            "write_scene_prose",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="write_scene_prose",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def build_generate_continuity_pack_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for generate_continuity_pack.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="generate_continuity_pack",
    )
    request_seed = "|".join(
        [
            book_id,
            "generate_continuity_pack",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="generate_continuity_pack",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def build_state_repair_scene_patch_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for state_repair_scene_patch.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="state_repair_scene_patch",
    )
    request_seed = "|".join(
        [
            book_id,
            "state_repair_scene_patch",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="state_repair_scene_patch",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def build_lint_scene_prose_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for lint_scene_prose.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="lint_scene_prose",
    )
    request_seed = "|".join(
        [
            book_id,
            "lint_scene_prose",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="lint_scene_prose",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def build_repair_scene_prose_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for repair_scene_prose.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="repair_scene_prose",
    )
    request_seed = "|".join(
        [
            book_id,
            "repair_scene_prose",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="repair_scene_prose",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def build_apply_scene_commit_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for apply_scene_commit.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="apply_scene_commit",
    )
    request_seed = "|".join(
        [
            book_id,
            "apply_scene_commit",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="apply_scene_commit",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def build_preflight_scene_state_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
) -> ExecutionRequest:
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("No current main-branch node is available for preflight_scene_state.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=MAIN_BRANCH_ID,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="preflight_scene_state",
    )
    request_seed = "|".join(
        [
            book_id,
            "preflight_scene_state",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="preflight_scene_state",
        selector=selector,
        expected_node=node,
        branch_id=MAIN_BRANCH_ID,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
        },
    )


def plan_scene_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "plan_scene":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("plan_scene only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("plan_scene requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="plan_scene",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for plan_scene.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="plan_scene",
    )

    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="plan_scene",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    plan_readiness = next((item for item in readiness.actions if item.action == "plan_scene"), None)
    if plan_readiness is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="plan_scene readiness could not be resolved.",
            details={**scope_details, "failure_code": "plan_scene_readiness_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    if not plan_readiness.legal or not plan_readiness.ready:
        status = "no_op" if plan_readiness.existing_outputs else "hard_fail"
        message = plan_readiness.refusal_reason or "plan_scene is not ready for the active scene."
        result = _result_for_request(
            request=request,
            node=execution_node,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in plan_readiness.existing_outputs},
            produced_artifacts=list(plan_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "plan_scene_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(plan_readiness.missing_prerequisites),
                "available_inputs": list(plan_readiness.available_inputs),
            },
        )
        _append_execution_result(book_root, result)
        return result

    try:
        scene_card_path = _plan_scene(
            workspace=workspace,
            book_id=book_id,
            chapter=chapter_id,
            scene=scene_id,
        )
    except LLMRequestError as exc:
        pause_path = _write_scene_phase_pause_marker(
            book_root=book_root,
            phase="plan_scene",
            chapter_id=chapter_id,
            section_id=section_id,
            scene_id=scene_id,
            error=exc,
        )
        produced_artifacts = [
            ProducedArtifactReceipt(
                artifact_key="scene_phase_pause_marker",
                label="Scene-phase pause marker",
                artifact_status="diagnostic",
                path=_artifact_relpath(book_root, pause_path),
                format="application/json",
                consumable=False,
                resumable=True,
                replaceable=True,
                details={"phase": "plan_scene"},
            )
        ]
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="retryable_pause",
            message=str(exc),
            artifact_paths={"scene_phase_pause_marker": _artifact_relpath(book_root, pause_path)},
            produced_artifacts=produced_artifacts,
            details={
                **scope_details,
                "failure_code": "provider_retry_exhausted",
                "status_code": exc.status_code,
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )
        _append_execution_result(book_root, result)
        return result

    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "plan",
        {"scene_card": _artifact_relpath(book_root, scene_card_path)},
    )

    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="scene_card",
            label="Scene card",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, scene_card_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"phase": "plan"},
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="plan_scene produced a provisional scene card.",
        artifact_paths={"scene_card": _artifact_relpath(book_root, scene_card_path)},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "recommended_next_action": "preflight_scene_state",
        },
    )
    _append_execution_result(book_root, result)
    return result


def generate_continuity_pack(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "generate_continuity_pack":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("generate_continuity_pack only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("generate_continuity_pack requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="generate_continuity_pack",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for generate_continuity_pack.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="generate_continuity_pack",
    )

    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="generate_continuity_pack",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    continuity_readiness = next((item for item in readiness.actions if item.action == "generate_continuity_pack"), None)
    if continuity_readiness is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="generate_continuity_pack readiness could not be resolved.",
            details={**scope_details, "failure_code": "continuity_readiness_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    if not continuity_readiness.legal or not continuity_readiness.ready:
        status = "no_op" if continuity_readiness.existing_outputs else "hard_fail"
        message = continuity_readiness.refusal_reason or "generate_continuity_pack is not ready for the active scene."
        result = _result_for_request(
            request=request,
            node=execution_node,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in continuity_readiness.existing_outputs},
            produced_artifacts=list(continuity_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "continuity_pack_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(continuity_readiness.missing_prerequisites),
                "available_inputs": list(continuity_readiness.available_inputs),
            },
        )
        _append_execution_result(book_root, result)
        return result

    phase_history = _load_phase_history(book_root, chapter_id, scene_id)
    scene_card_path = _phase_artifact_path(book_root, phase_history, "plan", "scene_card")
    preflight_patch_path = _phase_artifact_path(book_root, phase_history, "preflight", "patch")
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if scene_card_path is None or preflight_patch_path is None or not state_path.exists() or not outline_path.exists() or not system_path.exists():
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="generate_continuity_pack requires scene_card, preflight_patch, state.json, outline.json, and prompts/system_v1.md.",
            details={
                **scope_details,
                "failure_code": "core_inputs_missing",
                "scene_card_path": _artifact_relpath(book_root, scene_card_path) if scene_card_path else None,
                "preflight_patch_path": _artifact_relpath(book_root, preflight_patch_path) if preflight_patch_path else None,
                "state_exists": state_path.exists(),
                "outline_exists": outline_path.exists(),
                "system_prompt_exists": system_path.exists(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    scene_card = _load_json(scene_card_path)
    preflight_patch = _load_json(preflight_patch_path)
    unsupported_preflight = _unsupported_preflight_reasons(preflight_patch)
    if unsupported_preflight:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="generate_continuity_pack cannot yet materialize the preflight patch truthfully for this scene.",
            details={
                **scope_details,
                "failure_code": "unsupported_preflight_materialization",
                "reasons": unsupported_preflight,
            },
        )
        _append_execution_result(book_root, result)
        return result

    state = _load_json(state_path)
    working_state = json.loads(json.dumps(state))
    working_state = _apply_state_patch(working_state, preflight_patch, chapter_end=False)
    outline = _load_json(outline_path)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    character_states = _load_character_states(book_root, scene_card)

    config = load_config()
    continuity_client = get_llm_client(config, phase="continuity")
    continuity_model = resolve_model("continuity", config)
    durable_expand_ids = _durable_expand_ids_from_request(request)

    try:
        pack = _generate_continuity_pack(
            workspace,
            book_root,
            system_path,
            working_state,
            scene_card,
            character_registry,
            thread_registry,
            character_states,
            continuity_client,
            continuity_model,
            durable_expand_ids=durable_expand_ids,
        )
    except LLMRequestError as exc:
        pause_path = _write_scene_phase_pause_marker(
            book_root=book_root,
            phase="generate_continuity_pack",
            chapter_id=chapter_id,
            section_id=section_id,
            scene_id=scene_id,
            error=exc,
        )
        produced_artifacts = [
            ProducedArtifactReceipt(
                artifact_key="scene_phase_pause_marker",
                label="Scene-phase pause marker",
                artifact_status="diagnostic",
                path=_artifact_relpath(book_root, pause_path),
                format="application/json",
                consumable=False,
                resumable=True,
                replaceable=True,
                details={"phase": "generate_continuity_pack"},
            )
        ]
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="retryable_pause",
            message=str(exc),
            artifact_paths={"scene_phase_pause_marker": _artifact_relpath(book_root, pause_path)},
            produced_artifacts=produced_artifacts,
            details={
                **scope_details,
                "failure_code": "provider_retry_exhausted",
                "status_code": exc.status_code,
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )
        _append_execution_result(book_root, result)
        return result

    pack_path = _write_phase_artifact(book_root, chapter_id, scene_id, "continuity_pack", pack, as_json=True)
    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "continuity_pack",
        {"pack": _artifact_relpath(book_root, pack_path)},
    )
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="continuity_pack",
            label="Continuity pack",
            artifact_status="derived",
            path=_artifact_relpath(book_root, pack_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"phase": "continuity_pack"},
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="generate_continuity_pack produced a derived continuity pack.",
        artifact_paths={"continuity_pack": _artifact_relpath(book_root, pack_path)},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "recommended_next_action": "write_scene_prose",
            "pre_revision_id": live_node.revision_id,
            "post_revision_id": live_node.revision_id,
        },
    )
    _append_execution_result(book_root, result)
    return result


def preflight_scene_state(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "preflight_scene_state":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("preflight_scene_state only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("preflight_scene_state requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="preflight_scene_state",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for preflight_scene_state.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="preflight_scene_state",
    )

    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="preflight_scene_state",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    preflight_readiness = next((item for item in readiness.actions if item.action == "preflight_scene_state"), None)
    if preflight_readiness is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="preflight_scene_state readiness could not be resolved.",
            details={**scope_details, "failure_code": "preflight_readiness_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    if not preflight_readiness.legal or not preflight_readiness.ready:
        status = "no_op" if preflight_readiness.existing_outputs else "hard_fail"
        message = preflight_readiness.refusal_reason or "preflight_scene_state is not ready for the active scene."
        result = _result_for_request(
            request=request,
            node=execution_node,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in preflight_readiness.existing_outputs},
            produced_artifacts=list(preflight_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "preflight_scene_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(preflight_readiness.missing_prerequisites),
                "available_inputs": list(preflight_readiness.available_inputs),
            },
        )
        _append_execution_result(book_root, result)
        return result

    phase_history = _load_phase_history(book_root, chapter_id, scene_id)
    scene_card_path = _phase_artifact_path(book_root, phase_history, "plan", "scene_card")
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if scene_card_path is None or not state_path.exists() or not outline_path.exists() or not system_path.exists():
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="preflight_scene_state requires scene_card, state.json, outline.json, and prompts/system_v1.md.",
            details={
                **scope_details,
                "failure_code": "core_inputs_missing",
                "scene_card_path": _artifact_relpath(book_root, scene_card_path) if scene_card_path else None,
                "state_exists": state_path.exists(),
                "outline_exists": outline_path.exists(),
                "system_prompt_exists": system_path.exists(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    scene_card = _load_json(scene_card_path)
    state = _load_json(state_path)
    outline = _load_json(outline_path)
    chapter_order, scene_counts = _outline_summary(outline)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    character_states = _load_character_states(book_root, scene_card)

    config = load_config()
    preflight_client = get_llm_client(config, phase="preflight")
    preflight_model = resolve_model("preflight", config)
    durable_expand_ids = _durable_expand_ids_from_request(request)

    try:
        patch = _scene_state_preflight(
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
            durable_expand_ids=durable_expand_ids,
        )
    except LLMRequestError as exc:
        pause_path = _write_scene_phase_pause_marker(
            book_root=book_root,
            phase="preflight_scene_state",
            chapter_id=chapter_id,
            section_id=section_id,
            scene_id=scene_id,
            error=exc,
        )
        produced_artifacts = [
            ProducedArtifactReceipt(
                artifact_key="scene_phase_pause_marker",
                label="Scene-phase pause marker",
                artifact_status="diagnostic",
                path=_artifact_relpath(book_root, pause_path),
                format="application/json",
                consumable=False,
                resumable=True,
                replaceable=True,
                details={"phase": "preflight_scene_state"},
            )
        ]
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="retryable_pause",
            message=str(exc),
            artifact_paths={"scene_phase_pause_marker": _artifact_relpath(book_root, pause_path)},
            produced_artifacts=produced_artifacts,
            details={
                **scope_details,
                "failure_code": "provider_retry_exhausted",
                "status_code": exc.status_code,
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )
        _append_execution_result(book_root, result)
        return result

    patch_path = _write_phase_artifact(book_root, chapter_id, scene_id, "preflight_patch", patch, as_json=True)
    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "preflight",
        {"patch": _artifact_relpath(book_root, patch_path)},
    )
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="preflight_patch",
            label="Preflight state patch",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, patch_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"phase": "preflight"},
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="preflight_scene_state produced a provisional state patch.",
        artifact_paths={"preflight_patch": _artifact_relpath(book_root, patch_path)},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "recommended_next_action": "generate_continuity_pack",
            "pre_revision_id": live_node.revision_id,
            "post_revision_id": live_node.revision_id,
        },
    )
    _append_execution_result(book_root, result)
    return result


def write_scene_prose(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "write_scene_prose":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("write_scene_prose only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("write_scene_prose requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="write_scene_prose",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for write_scene_prose.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="write_scene_prose",
    )

    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="write_scene_prose",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    write_readiness = next((item for item in readiness.actions if item.action == "write_scene_prose"), None)
    if write_readiness is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="write_scene_prose readiness could not be resolved.",
            details={**scope_details, "failure_code": "write_scene_readiness_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    if not write_readiness.legal or not write_readiness.ready:
        status = "no_op" if write_readiness.existing_outputs else "hard_fail"
        message = write_readiness.refusal_reason or "write_scene_prose is not ready for the active scene."
        result = _result_for_request(
            request=request,
            node=execution_node,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in write_readiness.existing_outputs},
            produced_artifacts=list(write_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "write_scene_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(write_readiness.missing_prerequisites),
                "available_inputs": list(write_readiness.available_inputs),
            },
        )
        _append_execution_result(book_root, result)
        return result

    phase_history = _load_phase_history(book_root, chapter_id, scene_id)
    scene_card_path = _phase_artifact_path(book_root, phase_history, "plan", "scene_card")
    preflight_patch_path = _phase_artifact_path(book_root, phase_history, "preflight", "patch")
    continuity_pack_path = _phase_artifact_path(book_root, phase_history, "continuity_pack", "pack")
    if scene_card_path is None or preflight_patch_path is None or continuity_pack_path is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="write_scene_prose could not resolve required phase artifacts.",
            details={
                **scope_details,
                "failure_code": "phase_artifacts_missing",
                "scene_card_path": _artifact_relpath(book_root, scene_card_path) if scene_card_path else None,
                "preflight_patch_path": _artifact_relpath(book_root, preflight_patch_path) if preflight_patch_path else None,
                "continuity_pack_path": _artifact_relpath(book_root, continuity_pack_path) if continuity_pack_path else None,
            },
        )
        _append_execution_result(book_root, result)
        return result

    style_anchor = load_style_anchor(style_anchor_path(book_root))
    if not style_anchor.strip():
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="write_scene_prose requires an existing style anchor.",
            details={**scope_details, "failure_code": "style_anchor_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    preflight_patch = _load_json(preflight_patch_path)
    unsupported_preflight = _unsupported_preflight_reasons(preflight_patch)
    if unsupported_preflight:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="write_scene_prose cannot yet materialize the preflight patch truthfully for this scene.",
            details={
                **scope_details,
                "failure_code": "unsupported_preflight_materialization",
                "reasons": unsupported_preflight,
            },
        )
        _append_execution_result(book_root, result)
        return result

    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if not state_path.exists() or not outline_path.exists() or not system_path.exists():
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="write_scene_prose requires state.json, outline.json, and prompts/system_v1.md.",
            details={
                **scope_details,
                "failure_code": "core_inputs_missing",
                "state_exists": state_path.exists(),
                "outline_exists": outline_path.exists(),
                "system_prompt_exists": system_path.exists(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    scene_card = _load_json(scene_card_path)
    continuity_pack = _load_json(continuity_pack_path)
    state = _load_json(state_path)
    working_state = json.loads(json.dumps(state))
    working_state = _apply_state_patch(working_state, preflight_patch, chapter_end=False)
    outline = _load_json(outline_path)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    character_states = _load_character_states(book_root, scene_card)

    config = load_config()
    writer_client = get_llm_client(config, phase="writer")
    writer_model = resolve_model("writer", config)
    durable_expand_ids = _durable_expand_ids_from_request(request)

    try:
        prose, patch = _write_scene(
            workspace,
            book_root,
            system_path,
            scene_card,
            continuity_pack,
            working_state,
            style_anchor,
            character_registry,
            thread_registry,
            character_states,
            writer_client,
            writer_model,
            durable_expand_ids=durable_expand_ids,
        )
    except LLMRequestError as exc:
        pause_path = _write_scene_phase_pause_marker(
            book_root=book_root,
            phase="write_scene_prose",
            chapter_id=chapter_id,
            section_id=section_id,
            scene_id=scene_id,
            error=exc,
        )
        produced_artifacts = [
            ProducedArtifactReceipt(
                artifact_key="scene_phase_pause_marker",
                label="Scene-phase pause marker",
                artifact_status="diagnostic",
                path=_artifact_relpath(book_root, pause_path),
                format="application/json",
                consumable=False,
                resumable=True,
                replaceable=True,
            )
        ]
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="retryable_pause",
            message=str(exc),
            artifact_paths={"scene_phase_pause_marker": _artifact_relpath(book_root, pause_path)},
            produced_artifacts=produced_artifacts,
            details={
                **scope_details,
                "failure_code": "provider_retry_exhausted",
                "status_code": exc.status_code,
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )
        _append_execution_result(book_root, result)
        return result

    prose_path = _write_phase_artifact(book_root, chapter_id, scene_id, "write_prose", prose, as_json=False)
    patch_path = _write_phase_artifact(book_root, chapter_id, scene_id, "write_patch", patch, as_json=True)
    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "write",
        {
            "prose": _artifact_relpath(book_root, prose_path),
            "patch": _artifact_relpath(book_root, patch_path),
        },
    )

    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="write_prose",
            label="Draft prose",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, prose_path),
            format="text/plain",
            consumable=True,
            resumable=True,
            replaceable=True,
        ),
        ProducedArtifactReceipt(
            artifact_key="write_patch",
            label="Write state patch",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, patch_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
        ),
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message=f"Scene {chapter_id}:{scene_id} prose generated as provisional write artifacts.",
        artifact_paths={item.artifact_key: item.path for item in produced_artifacts},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "recommended_next_action": readiness.recommended_next_action,
            "pre_revision_id": live_node.revision_id,
            "post_revision_id": live_node.revision_id,
        },
    )
    _append_execution_result(book_root, result)
    return result


def state_repair_scene_patch(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "state_repair_scene_patch":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("state_repair_scene_patch only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("state_repair_scene_patch requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="state_repair_scene_patch",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for state_repair_scene_patch.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="state_repair_scene_patch",
    )

    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="state_repair_scene_patch",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    repair_readiness = next((item for item in readiness.actions if item.action == "state_repair_scene_patch"), None)
    if repair_readiness is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="state_repair_scene_patch readiness could not be resolved.",
            details={**scope_details, "failure_code": "state_repair_readiness_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    if not repair_readiness.legal or not repair_readiness.ready:
        status = "no_op" if repair_readiness.existing_outputs else "hard_fail"
        message = repair_readiness.refusal_reason or "state_repair_scene_patch is not ready for the active scene."
        result = _result_for_request(
            request=request,
            node=execution_node,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in repair_readiness.existing_outputs},
            produced_artifacts=list(repair_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "state_repair_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(repair_readiness.missing_prerequisites),
                "available_inputs": list(repair_readiness.available_inputs),
            },
        )
        _append_execution_result(book_root, result)
        return result

    artifact_state = load_scene_phase_artifact_state(book_root, chapter_id, scene_id)
    scene_card_path = artifact_state.scene_card_path
    preflight_patch_path = artifact_state.preflight_patch_path
    continuity_pack_path = artifact_state.continuity_pack_path
    source_prose_path = artifact_state.current_prose_path
    source_patch_path = artifact_state.current_patch_path
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if (
        scene_card_path is None
        or preflight_patch_path is None
        or continuity_pack_path is None
        or source_prose_path is None
        or source_patch_path is None
        or not state_path.exists()
        or not outline_path.exists()
        or not system_path.exists()
    ):
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="state_repair_scene_patch requires scene_card, preflight_patch, continuity_pack, current prose, current prose patch, state.json, outline.json, and prompts/system_v1.md.",
            details={
                **scope_details,
                "failure_code": "core_inputs_missing",
                "scene_card_path": _artifact_relpath(book_root, scene_card_path) if scene_card_path else None,
                "preflight_patch_path": _artifact_relpath(book_root, preflight_patch_path) if preflight_patch_path else None,
                "continuity_pack_path": _artifact_relpath(book_root, continuity_pack_path) if continuity_pack_path else None,
                "current_prose_phase": artifact_state.current_prose_phase,
                "source_prose_path": _artifact_relpath(book_root, source_prose_path) if source_prose_path else None,
                "source_patch_path": _artifact_relpath(book_root, source_patch_path) if source_patch_path else None,
                "state_exists": state_path.exists(),
                "outline_exists": outline_path.exists(),
                "system_prompt_exists": system_path.exists(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    preflight_patch = _load_json(preflight_patch_path)
    unsupported_preflight = _unsupported_preflight_reasons(preflight_patch)
    if unsupported_preflight:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="state_repair_scene_patch cannot yet materialize the preflight patch truthfully for this scene.",
            details={
                **scope_details,
                "failure_code": "unsupported_preflight_materialization",
                "reasons": unsupported_preflight,
            },
        )
        _append_execution_result(book_root, result)
        return result

    scene_card = _load_json(scene_card_path)
    continuity_pack = _load_json(continuity_pack_path)
    source_patch = _load_json(source_patch_path)
    prose = source_prose_path.read_text(encoding="utf-8")
    state = _load_json(state_path)
    working_state = json.loads(json.dumps(state))
    working_state = _apply_state_patch(working_state, preflight_patch, chapter_end=False)
    outline = _load_json(outline_path)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    character_states = _load_character_states(book_root, scene_card)

    config = load_config()
    repair_client = get_llm_client(config, phase="state_repair")
    repair_model = resolve_model("state_repair", config)
    durable_expand_ids = _durable_expand_ids_from_request(request)

    try:
        patch = _state_repair(
            workspace,
            book_root,
            system_path,
            prose,
            working_state,
            scene_card,
            continuity_pack,
            source_patch,
            character_registry,
            thread_registry,
            character_states,
            repair_client,
            repair_model,
            durable_expand_ids=durable_expand_ids,
        )
    except LLMRequestError as exc:
        pause_path = _write_scene_phase_pause_marker(
            book_root=book_root,
            phase="state_repair_scene_patch",
            chapter_id=chapter_id,
            section_id=section_id,
            scene_id=scene_id,
            error=exc,
        )
        produced_artifacts = [
            ProducedArtifactReceipt(
                artifact_key="scene_phase_pause_marker",
                label="Scene-phase pause marker",
                artifact_status="diagnostic",
                path=_artifact_relpath(book_root, pause_path),
                format="application/json",
                consumable=False,
                resumable=True,
                replaceable=True,
                details={"phase": "state_repair_scene_patch"},
            )
        ]
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="retryable_pause",
            message=str(exc),
            artifact_paths={"scene_phase_pause_marker": _artifact_relpath(book_root, pause_path)},
            produced_artifacts=produced_artifacts,
            details={
                **scope_details,
                "failure_code": "provider_retry_exhausted",
                "status_code": exc.status_code,
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )
        _append_execution_result(book_root, result)
        return result

    patch_path = _write_phase_artifact(book_root, chapter_id, scene_id, "state_repair_patch", patch, as_json=True)
    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "state_repair",
        {"patch": _artifact_relpath(book_root, patch_path)},
    )
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="state_repair_patch",
            label="State repair patch",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, patch_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"phase": "state_repair"},
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="state_repair_scene_patch produced a provisional corrected state patch.",
        artifact_paths={"state_repair_patch": _artifact_relpath(book_root, patch_path)},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "recommended_next_action": "lint_scene_prose",
            "source_prose_phase": artifact_state.current_prose_phase,
            "pre_revision_id": live_node.revision_id,
            "post_revision_id": live_node.revision_id,
        },
    )
    _append_execution_result(book_root, result)
    return result


def lint_scene_prose(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "lint_scene_prose":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("lint_scene_prose only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("lint_scene_prose requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="lint_scene_prose",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for lint_scene_prose.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="lint_scene_prose",
    )

    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="lint_scene_prose",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    lint_readiness = next((item for item in readiness.actions if item.action == "lint_scene_prose"), None)
    if lint_readiness is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="lint_scene_prose readiness could not be resolved.",
            details={**scope_details, "failure_code": "lint_readiness_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    if not lint_readiness.legal or not lint_readiness.ready:
        status = "no_op" if lint_readiness.existing_outputs else "hard_fail"
        message = lint_readiness.refusal_reason or "lint_scene_prose is not ready for the active scene."
        result = _result_for_request(
            request=request,
            node=execution_node,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in lint_readiness.existing_outputs},
            produced_artifacts=list(lint_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "lint_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(lint_readiness.missing_prerequisites),
                "available_inputs": list(lint_readiness.available_inputs),
            },
        )
        _append_execution_result(book_root, result)
        return result

    artifact_state = load_scene_phase_artifact_state(book_root, chapter_id, scene_id)
    scene_card_path = artifact_state.scene_card_path
    preflight_patch_path = artifact_state.preflight_patch_path
    continuity_pack_path = artifact_state.continuity_pack_path
    source_prose_path = artifact_state.current_prose_path
    state_repair_patch_path = artifact_state.state_repair_patch_path if artifact_state.state_repair_current else None
    state_path = book_root / "state.json"
    book_path = book_root / "book.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if (
        scene_card_path is None
        or preflight_patch_path is None
        or continuity_pack_path is None
        or source_prose_path is None
        or state_repair_patch_path is None
        or not state_path.exists()
        or not book_path.exists()
        or not system_path.exists()
    ):
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="lint_scene_prose requires scene_card, preflight_patch, continuity_pack, current prose, current state_repair_patch, state.json, book.json, and prompts/system_v1.md.",
            details={
                **scope_details,
                "failure_code": "core_inputs_missing",
                "scene_card_path": _artifact_relpath(book_root, scene_card_path) if scene_card_path else None,
                "preflight_patch_path": _artifact_relpath(book_root, preflight_patch_path) if preflight_patch_path else None,
                "continuity_pack_path": _artifact_relpath(book_root, continuity_pack_path) if continuity_pack_path else None,
                "current_prose_phase": artifact_state.current_prose_phase,
                "source_prose_path": _artifact_relpath(book_root, source_prose_path) if source_prose_path else None,
                "state_repair_patch_path": _artifact_relpath(book_root, state_repair_patch_path) if state_repair_patch_path else None,
                "state_exists": state_path.exists(),
                "book_exists": book_path.exists(),
                "system_prompt_exists": system_path.exists(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    preflight_patch = _load_json(preflight_patch_path)
    unsupported_preflight = _unsupported_preflight_reasons(preflight_patch)
    if unsupported_preflight:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="lint_scene_prose cannot yet materialize the preflight patch truthfully for this scene.",
            details={
                **scope_details,
                "failure_code": "unsupported_preflight_materialization",
                "reasons": unsupported_preflight,
            },
        )
        _append_execution_result(book_root, result)
        return result

    scene_card = _load_json(scene_card_path)
    prose = source_prose_path.read_text(encoding="utf-8")
    state_repair_patch = _load_json(state_repair_patch_path)
    state = _load_json(state_path)
    pre_lint_state = json.loads(json.dumps(state))
    pre_lint_state = _apply_state_patch(pre_lint_state, preflight_patch, chapter_end=False)
    lint_state = json.loads(json.dumps(pre_lint_state))
    lint_state = _apply_state_patch(lint_state, state_repair_patch, chapter_end=False)
    book_payload = _load_json(book_path)
    base_invariants = book_payload.get("invariants", []) if isinstance(book_payload.get("invariants", []), list) else []
    pre_summary = _summary_from_state(pre_lint_state)
    pre_invariants = list(base_invariants)
    pre_invariants += pre_summary.get("must_stay_true", [])
    pre_invariants += pre_summary.get("key_facts_ring", [])
    post_summary = _summary_from_state(lint_state)
    post_invariants = list(base_invariants)
    post_invariants += post_summary.get("must_stay_true", [])
    post_invariants += post_summary.get("key_facts_ring", [])
    character_states = _load_character_states(book_root, scene_card)

    if _lint_mode() == "off":
        report = {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "off"}
    else:
        config = load_config()
        linter_client = get_llm_client(config, phase="linter")
        linter_model = resolve_model("linter", config)
        durable_expand_ids = _durable_expand_ids_from_request(request)
        try:
            report = _lint_scene(
                workspace,
                book_root,
                system_path,
                prose,
                pre_lint_state,
                lint_state,
                state_repair_patch,
                scene_card,
                pre_invariants,
                post_invariants,
                character_states,
                book_payload.get("pov"),
                linter_client,
                linter_model,
                durable_expand_ids=durable_expand_ids,
            )
        except LLMRequestError as exc:
            pause_path = _write_scene_phase_pause_marker(
                book_root=book_root,
                phase="lint_scene_prose",
                chapter_id=chapter_id,
                section_id=section_id,
                scene_id=scene_id,
                error=exc,
            )
            produced_artifacts = [
                ProducedArtifactReceipt(
                    artifact_key="scene_phase_pause_marker",
                    label="Scene-phase pause marker",
                    artifact_status="diagnostic",
                    path=_artifact_relpath(book_root, pause_path),
                    format="application/json",
                    consumable=False,
                    resumable=True,
                    replaceable=True,
                    details={"phase": "lint_scene_prose"},
                )
            ]
            result = _result_for_request(
                request=request,
                node=execution_node,
                status="retryable_pause",
                message=str(exc),
                artifact_paths={"scene_phase_pause_marker": _artifact_relpath(book_root, pause_path)},
                produced_artifacts=produced_artifacts,
                details={
                    **scope_details,
                    "failure_code": "provider_retry_exhausted",
                    "status_code": exc.status_code,
                    "retry_after_seconds": exc.retry_after_seconds,
                },
            )
            _append_execution_result(book_root, result)
            return result

    report_path = _write_phase_artifact(book_root, chapter_id, scene_id, "lint_report", report, as_json=True)
    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "lint",
        {"report": _artifact_relpath(book_root, report_path)},
    )
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="lint_report",
            label="Lint report",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, report_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"phase": "lint"},
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message=f"lint_scene_prose produced a provisional lint report with status {report.get('status', 'unknown')}.",
        artifact_paths={"lint_report": _artifact_relpath(book_root, report_path)},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "lint_status": report.get("status"),
            "recommended_next_action": "repair_scene_prose" if report.get("status") == "fail" else "apply_scene_commit",
            "source_prose_phase": artifact_state.current_prose_phase,
            "pre_revision_id": live_node.revision_id,
            "post_revision_id": live_node.revision_id,
        },
    )
    _append_execution_result(book_root, result)
    return result


def repair_scene_prose(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "repair_scene_prose":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("repair_scene_prose only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("repair_scene_prose requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="repair_scene_prose",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for repair_scene_prose.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="repair_scene_prose",
    )

    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="repair_scene_prose",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    repair_readiness = next((item for item in readiness.actions if item.action == "repair_scene_prose"), None)
    if repair_readiness is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="repair_scene_prose readiness could not be resolved.",
            details={**scope_details, "failure_code": "repair_readiness_missing"},
        )
        _append_execution_result(book_root, result)
        return result

    if not repair_readiness.legal or not repair_readiness.ready:
        status = "no_op" if repair_readiness.existing_outputs else "hard_fail"
        message = repair_readiness.refusal_reason or "repair_scene_prose is not ready for the active scene."
        result = _result_for_request(
            request=request,
            node=execution_node,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in repair_readiness.existing_outputs},
            produced_artifacts=list(repair_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "repair_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(repair_readiness.missing_prerequisites),
                "available_inputs": list(repair_readiness.available_inputs),
            },
        )
        _append_execution_result(book_root, result)
        return result

    artifact_state = load_scene_phase_artifact_state(book_root, chapter_id, scene_id)
    scene_card_path = artifact_state.scene_card_path
    source_prose_path = artifact_state.current_prose_path
    lint_report_path = artifact_state.lint_report_path if artifact_state.lint_current else None
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if (
        scene_card_path is None
        or source_prose_path is None
        or lint_report_path is None
        or not state_path.exists()
        or not outline_path.exists()
        or not system_path.exists()
    ):
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="repair_scene_prose requires scene_card, current prose, current failing lint report, state.json, outline.json, and prompts/system_v1.md.",
            details={
                **scope_details,
                "failure_code": "core_inputs_missing",
                "scene_card_path": _artifact_relpath(book_root, scene_card_path) if scene_card_path else None,
                "current_prose_phase": artifact_state.current_prose_phase,
                "source_prose_path": _artifact_relpath(book_root, source_prose_path) if source_prose_path else None,
                "lint_report_path": _artifact_relpath(book_root, lint_report_path) if lint_report_path else None,
                "state_exists": state_path.exists(),
                "outline_exists": outline_path.exists(),
                "system_prompt_exists": system_path.exists(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    scene_card = _load_json(scene_card_path)
    prose = source_prose_path.read_text(encoding="utf-8")
    lint_report = _load_json(lint_report_path)
    state = _load_json(state_path)
    outline = _load_json(outline_path)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    character_states = _load_character_states(book_root, scene_card)

    config = load_config()
    repair_client = get_llm_client(config, phase="repair")
    repair_model = resolve_model("repair", config)
    durable_expand_ids = _durable_expand_ids_from_request(request)

    try:
        repaired_prose, repaired_patch = _repair_scene(
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
            durable_expand_ids=durable_expand_ids,
        )
    except LLMRequestError as exc:
        pause_path = _write_scene_phase_pause_marker(
            book_root=book_root,
            phase="repair_scene_prose",
            chapter_id=chapter_id,
            section_id=section_id,
            scene_id=scene_id,
            error=exc,
        )
        produced_artifacts = [
            ProducedArtifactReceipt(
                artifact_key="scene_phase_pause_marker",
                label="Scene-phase pause marker",
                artifact_status="diagnostic",
                path=_artifact_relpath(book_root, pause_path),
                format="application/json",
                consumable=False,
                resumable=True,
                replaceable=True,
                details={"phase": "repair_scene_prose"},
            )
        ]
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="retryable_pause",
            message=str(exc),
            artifact_paths={"scene_phase_pause_marker": _artifact_relpath(book_root, pause_path)},
            produced_artifacts=produced_artifacts,
            details={
                **scope_details,
                "failure_code": "provider_retry_exhausted",
                "status_code": exc.status_code,
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )
        _append_execution_result(book_root, result)
        return result

    prose_path = _write_phase_artifact(book_root, chapter_id, scene_id, "repair_prose", repaired_prose, as_json=False)
    patch_path = _write_phase_artifact(book_root, chapter_id, scene_id, "repair_patch", repaired_patch, as_json=True)
    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "repair",
        {
            "prose": _artifact_relpath(book_root, prose_path),
            "patch": _artifact_relpath(book_root, patch_path),
        },
    )
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="repair_prose",
            label="Repaired prose",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, prose_path),
            format="text/plain",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"phase": "repair"},
        ),
        ProducedArtifactReceipt(
            artifact_key="repair_patch",
            label="Repair state patch",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, patch_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={"phase": "repair"},
        ),
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="repair_scene_prose produced provisional repaired prose and patch artifacts.",
        artifact_paths={item.artifact_key: item.path for item in produced_artifacts},
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "lint_status": artifact_state.lint_status,
            "recommended_next_action": "state_repair_scene_patch",
            "source_prose_phase": artifact_state.current_prose_phase,
            "pre_revision_id": live_node.revision_id,
            "post_revision_id": live_node.revision_id,
        },
    )
    _append_execution_result(book_root, result)
    return result


def apply_scene_commit(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "apply_scene_commit":
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError("apply_scene_commit only supports main-branch execution.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("apply_scene_commit requires chapter and scene scope.")

    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = Path(workspace) / "books" / book_id
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node or TimelineNodeRef(
            book_id=book_id,
            workflow_family="section_write",
            source_run_id="unknown",
            branch_id="main",
            revision_id="unresolved",
            chapter=chapter_id,
            section=section_id,
            scene=scene_id,
            phase_id="apply_scene_commit",
        )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message="No live main-branch node is available for apply_scene_commit.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    before_snapshot = capture_main_branch_snapshot(workspace, book_id)
    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="apply_scene_commit",
        )
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=message,
            runtime_issue=RuntimeIssue(
                category=failure_code,
                code=failure_code,
                severity="high",
                message=message,
                details={
                    "expected_node": request.expected_node.to_dict(),
                    "live_node": live_node.to_dict(),
                },
            ),
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )

    readiness = _get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        prefer_emitted=False,
    )
    commit_readiness = next((item for item in readiness.actions if item.action == "apply_scene_commit"), None)
    if commit_readiness is None:
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message="apply_scene_commit readiness could not be resolved.",
            details={**scope_details, "failure_code": "commit_readiness_missing"},
        )

    if not commit_readiness.legal or not commit_readiness.ready:
        status = "no_op" if commit_readiness.existing_outputs else "hard_fail"
        message = commit_readiness.refusal_reason or "apply_scene_commit is not ready for the active scene."
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status=status,
            message=message,
            artifact_paths={item.artifact_key: item.path for item in commit_readiness.existing_outputs},
            produced_artifacts=list(commit_readiness.existing_outputs),
            details={
                **scope_details,
                "failure_code": "commit_not_ready",
                "scene_status": readiness.scene_status,
                "recommended_next_action": readiness.recommended_next_action,
                "missing_prerequisites": list(commit_readiness.missing_prerequisites),
                "available_inputs": list(commit_readiness.available_inputs),
            },
        )

    artifact_state = load_scene_phase_artifact_state(book_root, chapter_id, scene_id)
    scene_card_path = artifact_state.scene_card_path
    source_prose_path = artifact_state.current_prose_path
    state_repair_patch_path = artifact_state.state_repair_patch_path if artifact_state.state_repair_current else None
    lint_report_path = artifact_state.lint_report_path if artifact_state.lint_current else None
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    if (
        scene_card_path is None
        or source_prose_path is None
        or state_repair_patch_path is None
        or lint_report_path is None
        or not state_path.exists()
        or not outline_path.exists()
    ):
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message="apply_scene_commit requires scene_card, current prose, current state_repair_patch, current passing lint report, state.json, and outline.json.",
            details={
                **scope_details,
                "failure_code": "core_inputs_missing",
                "scene_card_path": _artifact_relpath(book_root, scene_card_path) if scene_card_path else None,
                "current_prose_phase": artifact_state.current_prose_phase,
                "source_prose_path": _artifact_relpath(book_root, source_prose_path) if source_prose_path else None,
                "state_repair_patch_path": _artifact_relpath(book_root, state_repair_patch_path) if state_repair_patch_path else None,
                "lint_report_path": _artifact_relpath(book_root, lint_report_path) if lint_report_path else None,
                "state_exists": state_path.exists(),
                "outline_exists": outline_path.exists(),
            },
        )

    scene_card = _load_json(scene_card_path)
    prose = source_prose_path.read_text(encoding="utf-8")
    patch = _load_json(state_repair_patch_path)
    lint_report = _load_json(lint_report_path)
    outline = _load_json(outline_path)
    state = _load_json(state_path)
    chapter_order, scene_counts = _outline_summary(outline)
    if not chapter_order:
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message="Outline is missing chapters; apply_scene_commit cannot advance canonical state.",
            details={**scope_details, "failure_code": "outline_missing_chapters"},
        )

    chapter_end, next_chapter, next_scene, completed = _chapter_end_status(
        chapter_order,
        scene_counts,
        chapter_id,
        scene_id,
    )
    state = _apply_state_patch(state, patch, chapter_end=chapter_end)

    updates = patch.get("character_updates") if isinstance(patch, dict) else None
    continuity_updates = patch.get("character_continuity_system_updates") if isinstance(patch, dict) else None
    has_char_updates = isinstance(updates, list) and len(updates) > 0
    has_continuity_updates = isinstance(continuity_updates, list) and len(continuity_updates) > 0
    if has_char_updates:
        _apply_character_updates(book_root, patch, chapter_id, scene_id)
    if has_continuity_updates:
        _apply_character_stat_updates(book_root, patch)

    appearance_ids: List[str] = []
    if has_char_updates:
        for update in updates:
            if not isinstance(update, dict):
                continue
            if update.get("appearance_updates") is None:
                continue
            char_id = str(update.get("character_id") or "").strip()
            if char_id:
                appearance_ids.append(char_id)

    refreshed_appearance_ids: List[str] = []
    state_relpath = _artifact_relpath(book_root, state_path)
    if appearance_ids:
        try:
            refreshed_appearance_ids = refresh_appearance_projections(book_root, appearance_ids, force=True)
        except LLMRequestError as exc:
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
            pause_path = _write_scene_phase_pause_marker(
                book_root=book_root,
                phase="apply_scene_commit",
                chapter_id=chapter_id,
                section_id=section_id,
                scene_id=scene_id,
                error=exc,
            )
            produced_artifacts = [
                ProducedArtifactReceipt(
                    artifact_key="state",
                    label="Canonical state",
                    artifact_status="authoritative",
                    path=state_relpath,
                    format="application/json",
                    consumable=True,
                    resumable=False,
                    replaceable=True,
                    details={"phase": "commit"},
                ),
                ProducedArtifactReceipt(
                    artifact_key="scene_phase_pause_marker",
                    label="Scene-phase pause marker",
                    artifact_status="diagnostic",
                    path=_artifact_relpath(book_root, pause_path),
                    format="application/json",
                    consumable=False,
                    resumable=True,
                    replaceable=True,
                    details={"phase": "apply_scene_commit"},
                ),
            ]
            return _emit_reconciled_result_for_request(
                workspace=workspace,
                book_id=book_id,
                request=request,
                before_snapshot=before_snapshot,
                status="retryable_pause",
                message=str(exc),
                artifact_paths={
                    "state": state_relpath,
                    "scene_phase_pause_marker": _artifact_relpath(book_root, pause_path),
                },
                produced_artifacts=produced_artifacts,
                runtime_issue=RuntimeIssue(
                    category="provider_retry_exhausted",
                    code="provider_retry_exhausted",
                    severity="high",
                    message=str(exc),
                    details={
                        "status_code": exc.status_code,
                        "retry_after_seconds": exc.retry_after_seconds,
                    },
                ),
                details={
                    **scope_details,
                    "failure_code": "provider_retry_exhausted",
                    "status_code": exc.status_code,
                    "retry_after_seconds": exc.retry_after_seconds,
                    "source_prose_phase": artifact_state.current_prose_phase,
                },
            )

    try:
        durable_updated = _apply_durable_state_updates(
            book_root=book_root,
            patch=patch,
            chapter=chapter_id,
            scene=scene_id,
            phase="scene",
            state=state,
            scene_card=scene_card,
        )
    except ValueError as exc:
        validate_json(state, "state")
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        message = str(exc).strip() or "Durable apply validation failed."
        code = "durable_chronology_conflict" if "Chronology conflict" in message else "durable_apply_validation_failed"
        produced_artifacts = [
            ProducedArtifactReceipt(
                artifact_key="state",
                label="Canonical state",
                artifact_status="authoritative",
                path=state_relpath,
                format="application/json",
                consumable=True,
                resumable=False,
                replaceable=True,
                details={"phase": "commit"},
            )
        ]
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="hard_fail",
            message=message,
            artifact_paths={"state": state_relpath},
            produced_artifacts=produced_artifacts,
            runtime_issue=RuntimeIssue(
                category="scope_contract_violation",
                code=code,
                severity="high",
                message=message,
                details={**scope_details, "phase": "scene"},
            ),
            details={
                **scope_details,
                "failure_code": code,
                "source_prose_phase": artifact_state.current_prose_phase,
            },
        )

    write_attempts = 2 if artifact_state.current_prose_phase == "repair" else 1
    try:
        _write_scene_files(
            book_root,
            chapter_id,
            scene_id,
            prose,
            scene_card,
            patch,
            lint_report,
            write_attempts,
        )
    except FileExistsError:
        chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
        committed_receipts = [
            ProducedArtifactReceipt(
                artifact_key="scene_prose",
                label="Committed scene prose",
                artifact_status="authoritative",
                path=_artifact_relpath(book_root, chapter_dir / f"scene_{scene_id:03d}.md"),
                format="text/markdown",
                consumable=True,
                resumable=False,
                replaceable=False,
                details={"phase": "commit"},
            ),
            ProducedArtifactReceipt(
                artifact_key="scene_meta",
                label="Committed scene metadata",
                artifact_status="authoritative",
                path=_artifact_relpath(book_root, chapter_dir / f"scene_{scene_id:03d}.meta.json"),
                format="application/json",
                consumable=True,
                resumable=False,
                replaceable=False,
                details={"phase": "commit"},
            ),
        ]
        return _emit_reconciled_result_for_request(
            workspace=workspace,
            book_id=book_id,
            request=request,
            before_snapshot=before_snapshot,
            status="no_op",
            message="Scene artifacts already exist for this committed scene.",
            artifact_paths={item.artifact_key: item.path for item in committed_receipts},
            produced_artifacts=committed_receipts,
            details={
                **scope_details,
                "failure_code": "scene_already_committed",
                "source_prose_phase": artifact_state.current_prose_phase,
            },
        )

    _update_bible(book_root, patch)

    chapter_summary_path: Optional[Path] = None
    chapter_markdown_path: Optional[Path] = None
    if chapter_end:
        _rollup_chapter_summary(book_root, state, chapter_id)
        chapter_summary_path = book_root / "draft" / "context" / "chapter_summaries" / f"ch_{chapter_id:03d}.json"
        chapter_markdown_path = _compile_chapter_markdown(book_root, outline, chapter_id)

    state["cursor"] = {"chapter": next_chapter, "scene": next_scene}
    state["status"] = "COMPLETE" if completed else "DRAFTING"
    validate_json(state, "state")
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
    scene_prose_path = chapter_dir / f"scene_{scene_id:03d}.md"
    scene_meta_path = chapter_dir / f"scene_{scene_id:03d}.meta.json"
    last_excerpt_path = book_root / "draft" / "context" / "last_excerpt.md"
    bible_path = book_root / "draft" / "context" / "bible.md"

    artifact_paths = {
        "state": state_relpath,
        "scene_prose": _artifact_relpath(book_root, scene_prose_path),
        "scene_meta": _artifact_relpath(book_root, scene_meta_path),
    }
    produced_artifacts = [
        ProducedArtifactReceipt(
            artifact_key="state",
            label="Canonical state",
            artifact_status="authoritative",
            path=state_relpath,
            format="application/json",
            consumable=True,
            resumable=False,
            replaceable=True,
            details={"phase": "commit"},
        ),
        ProducedArtifactReceipt(
            artifact_key="scene_prose",
            label="Committed scene prose",
            artifact_status="authoritative",
            path=_artifact_relpath(book_root, scene_prose_path),
            format="text/markdown",
            consumable=True,
            resumable=False,
            replaceable=False,
            details={"phase": "commit", "source_prose_phase": artifact_state.current_prose_phase},
        ),
        ProducedArtifactReceipt(
            artifact_key="scene_meta",
            label="Committed scene metadata",
            artifact_status="authoritative",
            path=_artifact_relpath(book_root, scene_meta_path),
            format="application/json",
            consumable=True,
            resumable=False,
            replaceable=False,
            details={"phase": "commit", "source_prose_phase": artifact_state.current_prose_phase},
        ),
    ]
    if last_excerpt_path.exists():
        artifact_paths["last_excerpt"] = _artifact_relpath(book_root, last_excerpt_path)
        produced_artifacts.append(
            ProducedArtifactReceipt(
                artifact_key="last_excerpt",
                label="Last excerpt",
                artifact_status="derived",
                path=_artifact_relpath(book_root, last_excerpt_path),
                format="text/markdown",
                consumable=True,
                resumable=False,
                replaceable=True,
                details={"phase": "commit"},
            )
        )
    if bible_path.exists() and isinstance(patch.get("world_updates"), dict) and isinstance(patch.get("world_updates", {}).get("recent_facts"), list):
        artifact_paths["bible"] = _artifact_relpath(book_root, bible_path)
        produced_artifacts.append(
            ProducedArtifactReceipt(
                artifact_key="bible",
                label="World bible",
                artifact_status="derived",
                path=_artifact_relpath(book_root, bible_path),
                format="text/markdown",
                consumable=True,
                resumable=False,
                replaceable=True,
                details={"phase": "commit"},
            )
        )
    if chapter_summary_path is not None and chapter_summary_path.exists():
        artifact_paths["chapter_summary"] = _artifact_relpath(book_root, chapter_summary_path)
        produced_artifacts.append(
            ProducedArtifactReceipt(
                artifact_key="chapter_summary",
                label="Chapter summary",
                artifact_status="derived",
                path=_artifact_relpath(book_root, chapter_summary_path),
                format="application/json",
                consumable=True,
                resumable=False,
                replaceable=True,
                details={"phase": "commit", "chapter_end": True},
            )
        )
    if chapter_markdown_path is not None and chapter_markdown_path.exists():
        artifact_paths["chapter_markdown"] = _artifact_relpath(book_root, chapter_markdown_path)
        produced_artifacts.append(
            ProducedArtifactReceipt(
                artifact_key="chapter_markdown",
                label="Compiled chapter markdown",
                artifact_status="derived",
                path=_artifact_relpath(book_root, chapter_markdown_path),
                format="text/markdown",
                consumable=True,
                resumable=False,
                replaceable=True,
                details={"phase": "commit", "chapter_end": True},
            )
        )

    _record_phase_success(
        book_root,
        chapter_id,
        scene_id,
        "commit",
        artifact_paths,
    )
    return _emit_reconciled_result_for_request(
        workspace=workspace,
        book_id=book_id,
        request=request,
        before_snapshot=before_snapshot,
        status="success",
        message="apply_scene_commit advanced canonical state and persisted authoritative scene artifacts.",
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details={
            **scope_details,
            "scene_status": readiness.scene_status,
            "recommended_next_action": None,
            "source_prose_phase": artifact_state.current_prose_phase,
            "lint_status": artifact_state.lint_status,
            "chapter_end": chapter_end,
            "completed": completed,
            "next_chapter": next_chapter,
            "next_scene": next_scene,
            "write_attempts": write_attempts,
            "durable_state_updated": bool(durable_updated),
            "appearance_refresh_requested_ids": appearance_ids,
            "appearance_refreshed_ids": refreshed_appearance_ids,
            "pre_revision_id": live_node.revision_id,
        },
    )
