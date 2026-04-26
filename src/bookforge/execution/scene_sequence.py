from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from bookforge.contracts import ExecutionRequest
from bookforge.contracts import MAIN_BRANCH_ID
from bookforge.query import current_execution_node

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
