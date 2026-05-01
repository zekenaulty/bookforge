from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import hashlib
import json

from bookforge.contracts import ExecutionRequest, ExecutionResult, ScopeSelector
from bookforge.contracts import MAIN_BRANCH_ID
from bookforge.query import current_execution_node, get_scene_phase_readiness
from bookforge.supervision import paths as supervision_paths

from .scene_actions import (
    apply_scene_commit,
    build_apply_scene_commit_request,
    build_generate_continuity_pack_request,
    build_lint_scene_prose_request,
    build_plan_scene_request,
    build_preflight_scene_state_request,
    build_repair_scene_prose_request,
    build_state_repair_scene_patch_request,
    build_write_scene_prose_request,
    generate_continuity_pack,
    lint_scene_prose,
    plan_scene_action,
    preflight_scene_state,
    repair_scene_prose,
    state_repair_scene_patch,
    write_scene_prose,
)

SceneRequestBuilder = Callable[..., ExecutionRequest]
SceneActionExecutor = Callable[[Any, ExecutionRequest], Any]


def _now_token() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


_BUILDERS: Dict[str, SceneRequestBuilder] = {
    "plan_scene": build_plan_scene_request,
    "preflight_scene_state": build_preflight_scene_state_request,
    "generate_continuity_pack": build_generate_continuity_pack_request,
    "write_scene_prose": build_write_scene_prose_request,
    "state_repair_scene_patch": build_state_repair_scene_patch_request,
    "lint_scene_prose": build_lint_scene_prose_request,
    "repair_scene_prose": build_repair_scene_prose_request,
    "apply_scene_commit": build_apply_scene_commit_request,
}


_EXECUTORS: Dict[str, SceneActionExecutor] = {
    "plan_scene": plan_scene_action,
    "preflight_scene_state": preflight_scene_state,
    "generate_continuity_pack": generate_continuity_pack,
    "write_scene_prose": write_scene_prose,
    "state_repair_scene_patch": state_repair_scene_patch,
    "lint_scene_prose": lint_scene_prose,
    "repair_scene_prose": repair_scene_prose,
    "apply_scene_commit": apply_scene_commit,
}


def _request_with_details(request: ExecutionRequest, extra_details: Optional[Dict[str, Any]]) -> ExecutionRequest:
    merged_details = dict(request.details)
    if isinstance(extra_details, dict) and extra_details:
        merged_details.update(extra_details)
    return ExecutionRequest(
        request_id=request.request_id,
        action=request.action,
        selector=request.selector,
        expected_node=request.expected_node,
        branch_id=request.branch_id,
        requested_at=request.requested_at,
        details=merged_details,
        schema_version=request.schema_version,
    )


def build_continue_scene_request(
    workspace,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for continue_scene on branch {resolved_branch_id}.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="continue_scene",
    )
    return ExecutionRequest(
        request_id=_hash_id(
            book_id,
            "continue_scene",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            resolved_branch_id,
            node.revision_id,
            _now_token(),
        ),
        action="continue_scene",
        selector=selector,
        expected_node=node,
        branch_id=resolved_branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
            "macro_kind": "single_recommended_scene_phase_step",
        },
    )


def build_live_scene_phase_request(
    workspace,
    book_id: str,
    action: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
    extra_details: Optional[Dict[str, Any]] = None,
) -> ExecutionRequest:
    builder = _BUILDERS.get(action)
    if builder is None:
        raise ValueError(f"Unsupported scene-phase action: {action}")
    request = builder(
        workspace,
        book_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        branch_id=branch_id,
    )
    if isinstance(extra_details, dict) and extra_details:
        request = _request_with_details(request, extra_details)
    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if live_node is None:
        return request
    return ExecutionRequest(
        request_id=request.request_id,
        action=request.action,
        selector=request.selector,
        expected_node=live_node,
        branch_id=request.branch_id,
        requested_at=request.requested_at,
        details=dict(request.details),
        schema_version=request.schema_version,
    )


def run_scene_phase_action(
    workspace,
    book_id: str,
    action: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
    extra_details: Optional[Dict[str, Any]] = None,
):
    request = build_live_scene_phase_request(
        workspace,
        book_id,
        action,
        chapter_id=chapter_id,
        scene_id=scene_id,
        section_id=section_id,
        branch_id=branch_id,
        extra_details=extra_details,
    )
    executor = _EXECUTORS.get(action)
    if executor is None:
        raise ValueError(f"Unsupported scene-phase action: {action}")
    return executor(workspace, request)


def continue_scene(workspace, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "continue_scene":
        raise ValueError("Unsupported execution action.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("continue_scene requires chapter and scene scope.")
    branch_id = str(request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    section_id = request.selector.section
    before = get_scene_phase_readiness(
        workspace,
        request.selector.book_id,
        branch_id=branch_id,
        chapter_id=int(request.selector.chapter),
        scene_id=int(request.selector.scene),
        section_id=section_id,
        prefer_emitted=False,
    )
    child_action = before.recommended_next_action
    if not child_action:
        result = _wrapper_result(
            workspace=workspace,
            request=request,
            branch_id=branch_id,
            status="no_op",
            message="No ready recommended scene-phase action is available for the selected scene.",
            child_result=None,
            before_readiness=before,
            after_readiness=before,
        )
        _append_execution_result(workspace, request.selector.book_id, branch_id, result)
        return result

    child_result = run_scene_phase_action(
        workspace,
        request.selector.book_id,
        child_action,
        chapter_id=int(request.selector.chapter),
        scene_id=int(request.selector.scene),
        section_id=section_id,
        branch_id=branch_id,
    )
    after = get_scene_phase_readiness(
        workspace,
        request.selector.book_id,
        branch_id=branch_id,
        chapter_id=int(request.selector.chapter),
        scene_id=int(request.selector.scene),
        section_id=section_id,
        prefer_emitted=False,
    )
    result = _wrapper_result(
        workspace=workspace,
        request=request,
        branch_id=branch_id,
        status=child_result.status,
        message=f"Continued scene by executing {child_action}.",
        child_result=child_result,
        before_readiness=before,
        after_readiness=after,
    )
    _append_execution_result(workspace, request.selector.book_id, branch_id, result)
    return result


def _wrapper_result(
    *,
    workspace,
    request: ExecutionRequest,
    branch_id: str,
    status: str,
    message: str,
    child_result,
    before_readiness,
    after_readiness,
) -> ExecutionResult:
    node = None
    if child_result is not None:
        node = child_result.node
    if node is None:
        node = current_execution_node(workspace, request.selector.book_id, branch_id=branch_id, prefer_emitted=False) or request.expected_node
    if node is None:
        raise ValueError("Unable to resolve node for continue_scene result.")
    before_child_row = None
    if child_result is not None:
        before_child_row = next((item for item in before_readiness.actions if item.action == child_result.action), None)
    child_canonical_status = str((child_result.details or {}).get("canonical_change_status") or "").strip().lower() if child_result is not None else ""
    produced_artifact_refs = _produced_artifact_refs(child_result)
    stop_reason = _loop_stop_reason(child_result=child_result, after_readiness=after_readiness)
    next_recommended_action = None if stop_reason else after_readiness.recommended_next_action
    pre_readiness_ref = _readiness_ref(before_readiness)
    post_readiness_ref = _readiness_ref(after_readiness)
    canonical_changed = bool(branch_id == MAIN_BRANCH_ID and child_canonical_status in {"canonical", "changed"})
    loop_step_receipt = {
        "schema_version": "author_loop_step_receipt_v1",
        "step_index": 1,
        "pre_readiness_ref": pre_readiness_ref,
        "post_readiness_ref": post_readiness_ref,
        "action_run": child_result.action if child_result is not None else None,
        "child_result_ref": child_result.result_id if child_result is not None else None,
        "child_request_ref": child_result.request_id if child_result is not None else None,
        "child_status": child_result.status if child_result is not None else None,
        "produced_artifact_refs": produced_artifact_refs,
        "canonical_changed": canonical_changed,
        "next_recommended_action": next_recommended_action,
        "stop_reason": stop_reason,
    }
    details = {
        "macro_kind": "single_recommended_scene_phase_step",
        "child_action": child_result.action if child_result is not None else None,
        "child_status": child_result.status if child_result is not None else None,
        "pre_readiness_ref": pre_readiness_ref,
        "post_readiness_ref": post_readiness_ref,
        "before_scene_status": before_readiness.scene_status,
        "before_recommended_next_action": before_readiness.recommended_next_action,
        "after_scene_status": after_readiness.scene_status,
        "after_recommended_next_action": after_readiness.recommended_next_action,
        "recommended_next_action": next_recommended_action,
        "stop_reason": stop_reason,
        "branch_id": branch_id,
        "child_mutation_scope": before_child_row.mutation_scope if before_child_row is not None else None,
        "canonical_changed": canonical_changed,
        "child_result_id": child_result.result_id if child_result is not None else None,
        "child_request_id": child_result.request_id if child_result is not None else None,
        "produced_artifact_refs": produced_artifact_refs,
        "author_loop_step_receipt": loop_step_receipt,
    }
    return ExecutionResult(
        result_id=_hash_id(
            request.selector.book_id,
            request.request_id,
            status,
            node.revision_id,
            _now_token(),
        ),
        action="continue_scene",
        status=status,
        node=node,
        selector=request.selector,
        message=message,
        artifact_paths=dict(child_result.artifact_paths) if child_result is not None else {},
        produced_artifacts=list(child_result.produced_artifacts) if child_result is not None else [],
        details=details,
        emitted_at=_now_token(),
        request_id=request.request_id,
    )


def _append_execution_result(workspace, book_id: str, branch_id: str, result: ExecutionResult) -> None:
    book_root = Path(workspace) / "books" / book_id
    path = supervision_paths.execution_results_path(book_root, branch_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result.to_dict(), ensure_ascii=True) + "\n")


def _readiness_ref(readiness) -> Dict[str, Any]:
    node = getattr(readiness, "node", None)
    ready_actions = [
        item.action
        for item in getattr(readiness, "actions", [])
        if bool(getattr(item, "legal", False)) and bool(getattr(item, "ready", False))
    ]
    return {
        "schema_version": "scene_phase_readiness_ref_v1",
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "ready_actions": ready_actions,
        "node_revision_id": node.revision_id if node is not None else None,
        "node_branch_id": node.branch_id if node is not None else None,
        "updated_at": readiness.updated_at,
    }


def _produced_artifact_refs(child_result) -> list[Dict[str, Any]]:
    if child_result is None:
        return []
    refs = []
    for artifact in child_result.produced_artifacts:
        refs.append(
            {
                "artifact_key": artifact.artifact_key,
                "artifact_status": artifact.artifact_status,
                "path": artifact.path,
                "consumable": bool(artifact.consumable),
                "resumable": bool(artifact.resumable),
                "replaceable": bool(artifact.replaceable),
            }
        )
    return refs


def _loop_stop_reason(*, child_result, after_readiness) -> Optional[str]:
    if child_result is None:
        return "no_legal_action"
    status = str(child_result.status or "").strip().lower()
    details = child_result.details or {}
    failure_code = str(details.get("failure_code") or "").strip().lower()
    action = str(getattr(child_result, "action", "") or "").strip()
    if status == "retryable_pause":
        return "provider_failed"
    if failure_code in {"stale_write", "stale_parent", "branch_stale"}:
        return "branch_stale"
    if status in {"hard_fail", "integrity_degraded"}:
        return "tool_unavailable"
    if status == "success" and action == "apply_scene_commit":
        return "completed_scope"
    if after_readiness.recommended_next_action:
        return None
    return "completed_scope"
