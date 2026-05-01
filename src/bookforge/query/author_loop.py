from __future__ import annotations

from typing import Any, Dict, List, Optional

from bookforge.contracts import (
    AuthorLoopEnvelopeOption,
    AuthorLoopEnvelopeOptions,
    MAIN_BRANCH_ID,
    ScopeSelector,
)

from .writing import get_next_writing_target, get_writing_gate_status


DEFAULT_STOP_CONDITIONS = [
    "completed_scope",
    "user_cancel_requested",
    "needs_user_choice",
    "no_legal_action",
    "budget_exhausted",
    "provider_failed",
    "branch_stale",
    "canonical_approval_required",
    "book_complete",
    "tool_unavailable",
]

REFRESH_QUERY_ORDER = [
    "branch_detail",
    "branch_artifact_index",
    "branch_diff_summary",
    "book_reader_scene",
    "next_writing_target",
    "writing_gate_status",
    "scene_phase_readiness",
    "legal_actions",
]

BOOKFORGE_CHILD_STOP_REASONS = [
    "no_legal_action",
    "provider_failed",
    "branch_stale",
    "tool_unavailable",
    "completed_scope",
]

NANDA_PARENT_STOP_REASONS = [
    "user_cancel_requested",
    "needs_user_choice",
    "budget_exhausted",
    "canonical_approval_required",
    "book_complete",
]


def _gate_by_key(gates, key: str):
    return next((gate for gate in gates if gate.gate_key == key), None)


def _mutation_scope(branch_id: str, *, may_touch_canonical: bool) -> str:
    if branch_id == MAIN_BRANCH_ID and may_touch_canonical:
        return "canonical"
    return "branch_local"


def _selector_for(target_selector: ScopeSelector, *, chapter: Optional[int], section: Optional[int], scene: Optional[int]) -> ScopeSelector:
    return ScopeSelector(
        book_id=target_selector.book_id,
        branch_id=target_selector.branch_id,
        workflow_family="section_write",
        chapter=chapter,
        section=section,
        scene=scene,
    )


def _ready_actions_from_gates(gates) -> Dict[str, str]:
    return {gate.gate_key: str(gate.action or "") for gate in gates if bool(gate.ready) and gate.action}


def get_author_loop_envelopes(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    prefer_emitted: bool = True,
) -> AuthorLoopEnvelopeOptions:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    target = get_next_writing_target(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        prefer_emitted=prefer_emitted,
    )
    gates = get_writing_gate_status(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=target.selector.chapter or chapter_id,
        section_id=target.selector.section or section_id,
        scene_id=target.selector.scene or scene_id,
        prefer_emitted=prefer_emitted,
    )
    selector = target.selector
    ready_actions = _ready_actions_from_gates(gates.gates)
    scene_gate = _gate_by_key(gates.gates, "scene_continue")
    section_gate = _gate_by_key(gates.gates, "section_lock")
    chapter_gate = _gate_by_key(gates.gates, "chapter_finalize")
    book_gate = _gate_by_key(gates.gates, "book_continue")

    envelopes: List[AuthorLoopEnvelopeOption] = []
    scene_ready = bool(scene_gate and scene_gate.ready)
    scene_blocked = None if scene_ready else (scene_gate.blocked_reason if scene_gate else target.blocked_reason)
    chapter = selector.chapter or chapter_id
    section = selector.section or section_id
    scene = selector.scene or scene_id

    envelopes.append(
        AuthorLoopEnvelopeOption(
            envelope_key="continue_one_step",
            label="Continue one recommended scene step",
            selector=_selector_for(selector, chapter=chapter, section=section, scene=scene),
            branch_id=resolved_branch_id,
            ready=scene_ready,
            target_action="continue_scene" if scene_ready else None,
            allowed_actions=["continue_scene"],
            max_steps_hint=1,
            max_duration_seconds_hint=900,
            mutation_scope=_mutation_scope(resolved_branch_id, may_touch_canonical=True),
            canonical_changed=False,
            approval_required=resolved_branch_id == MAIN_BRANCH_ID,
            stop_conditions=DEFAULT_STOP_CONDITIONS,
            blocked_reason=scene_blocked,
            details={
                "ready_actions": ready_actions,
                "target_status": target.status,
                "refresh_required_between_steps": True,
                "refresh_query_order": REFRESH_QUERY_ORDER,
                "child_action_count_per_step": 1,
            },
        )
    )
    envelopes.append(
        AuthorLoopEnvelopeOption(
            envelope_key="continue_scene",
            label="Continue current scene until the scene stops",
            selector=_selector_for(selector, chapter=chapter, section=section, scene=scene),
            branch_id=resolved_branch_id,
            ready=scene_ready,
            target_action="continue_scene" if scene_ready else None,
            allowed_actions=["continue_scene"],
            max_steps_hint=8,
            max_duration_seconds_hint=3600,
            mutation_scope=_mutation_scope(resolved_branch_id, may_touch_canonical=True),
            canonical_changed=False,
            approval_required=resolved_branch_id == MAIN_BRANCH_ID,
            stop_conditions=DEFAULT_STOP_CONDITIONS,
            blocked_reason=scene_blocked,
            details={
                "stop_after": "scene reaches no recommended scene-phase action",
                "refresh_required_between_steps": True,
                "refresh_query_order": REFRESH_QUERY_ORDER,
                "child_action_count_per_step": 1,
            },
        )
    )

    section_ready = scene_ready or bool(section_gate and section_gate.ready)
    envelopes.append(
        AuthorLoopEnvelopeOption(
            envelope_key="continue_section",
            label="Continue current section until lock-ready or locked",
            selector=_selector_for(selector, chapter=chapter, section=section, scene=None),
            branch_id=resolved_branch_id,
            ready=section_ready and chapter is not None and section is not None,
            target_action="continue_scene" if scene_ready else (section_gate.action if section_gate and section_gate.ready else None),
            allowed_actions=["continue_scene", "lock_section_from_written_state"],
            max_steps_hint=64,
            max_duration_seconds_hint=14400,
            mutation_scope=_mutation_scope(resolved_branch_id, may_touch_canonical=True),
            canonical_changed=False,
            approval_required=resolved_branch_id == MAIN_BRANCH_ID,
            stop_conditions=DEFAULT_STOP_CONDITIONS,
            blocked_reason=None if section_ready else (section_gate.blocked_reason if section_gate else gates.blocked_reason),
            details={
                "scene_gate": scene_gate.to_dict() if scene_gate else None,
                "section_gate": section_gate.to_dict() if section_gate else None,
                "refresh_required_between_steps": True,
                "refresh_query_order": REFRESH_QUERY_ORDER,
                "child_action_count_per_step": 1,
            },
        )
    )

    chapter_ready = section_ready or bool(chapter_gate and chapter_gate.ready)
    envelopes.append(
        AuthorLoopEnvelopeOption(
            envelope_key="continue_chapter",
            label="Continue current chapter until finalization-ready or finalized",
            selector=_selector_for(selector, chapter=chapter, section=None, scene=None),
            branch_id=resolved_branch_id,
            ready=chapter_ready and chapter is not None,
            target_action="continue_scene" if scene_ready else (chapter_gate.action if chapter_gate and chapter_gate.ready else None),
            allowed_actions=[
                "continue_scene",
                "lock_section_from_written_state",
                "align_scene_pair_seam",
                "plan_bridge_scene_insertion",
                "apply_bridge_scene_insertion",
                "finalize_chapter_from_locked_sections",
            ],
            max_steps_hint=240,
            max_duration_seconds_hint=43200,
            mutation_scope=_mutation_scope(resolved_branch_id, may_touch_canonical=True),
            canonical_changed=False,
            approval_required=resolved_branch_id == MAIN_BRANCH_ID,
            stop_conditions=DEFAULT_STOP_CONDITIONS,
            blocked_reason=None if chapter_ready else (chapter_gate.blocked_reason if chapter_gate else gates.blocked_reason),
            details={
                "chapter_gate": chapter_gate.to_dict() if chapter_gate else None,
                "book_gate": book_gate.to_dict() if book_gate else None,
                "refresh_required_between_steps": True,
                "refresh_query_order": REFRESH_QUERY_ORDER,
                "child_action_count_per_step": 1,
            },
        )
    )

    recommended = next((item.envelope_key for item in envelopes if item.ready), None)
    details: Dict[str, Any] = {
        "static_dynamic_boundary": "Envelope support is static-ish; readiness is per selected scope and must be re-queried before every step.",
        "resume_rule": "A resumed loop must refresh branch detail, reader state, legal actions, writing gates, and prior receipts before acting.",
        "refresh_required_between_steps": True,
        "refresh_query_order": REFRESH_QUERY_ORDER,
        "cancellation_policy": "Cancel requests stop scheduling new child actions; any in-flight child may finish and its receipt/artifacts remain branch-local.",
        "stop_reason_ownership": {
            "bookforge_child_step": BOOKFORGE_CHILD_STOP_REASONS,
            "nanda_parent_loop": NANDA_PARENT_STOP_REASONS,
        },
        "book_complete": bool(target.book_complete),
        "ready_actions": ready_actions,
    }
    return AuthorLoopEnvelopeOptions(
        book_id=book_id,
        branch_id=resolved_branch_id,
        selector=selector,
        node=target.node,
        target=target,
        writing_gates=gates,
        envelopes=envelopes,
        recommended_envelope=recommended,
        details=details,
    )
