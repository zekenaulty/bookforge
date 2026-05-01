from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from bookforge.contracts import MAIN_BRANCH_ID, NextWritingTarget, ScopeSelector, WritingGate, WritingGateStatus

from . import _common
from .scene_phase import get_scene_phase_readiness
from .workspace import current_execution_node, get_workspace_status_for_branch


def _parse_scene_ref(value: object) -> Tuple[Optional[int], Optional[int]]:
    text = str(value or "").strip()
    if ":" not in text:
        return None, None
    chapter_text, scene_text = text.split(":", 1)
    return _common.coerce_int(chapter_text), _common.coerce_int(scene_text)


def _section_scene_bounds(section: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    _, start = _parse_scene_ref(section.get("scene_ref_start"))
    _, end = _parse_scene_ref(section.get("scene_ref_end"))
    return start, end


def _section_ref(chapter_id: int, section: Dict[str, Any]) -> Dict[str, Any]:
    section_id = _common.coerce_int(section.get("section_id"))
    start, end = _section_scene_bounds(section)
    return {
        "chapter": int(chapter_id),
        "section": int(section_id) if section_id is not None else None,
        "status": str(section.get("status") or "").strip() or None,
        "title": str(section.get("title") or "").strip() or None,
        "scene_ref_start": section.get("scene_ref_start"),
        "scene_ref_end": section.get("scene_ref_end"),
        "scene_start": start,
        "scene_end": end,
    }


def _scene_ref(
    *,
    chapter_id: int,
    section_id: Optional[int],
    scene_id: int,
    section: Optional[Dict[str, Any]] = None,
    scene_status: Optional[str] = None,
    recommended_next_action: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chapter": int(chapter_id),
        "section": int(section_id) if section_id is not None else None,
        "scene": int(scene_id),
    }
    if section is not None:
        payload["section_status"] = str(section.get("status") or "").strip() or None
        payload["section_title"] = str(section.get("title") or "").strip() or None
    if scene_status:
        payload["scene_status"] = scene_status
    if recommended_next_action:
        payload["recommended_next_action"] = recommended_next_action
    return payload


def _chapter_ref(chapter: Dict[str, Any]) -> Dict[str, Any]:
    chapter_id = _common.coerce_int(chapter.get("chapter_id"))
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    return {
        "chapter": int(chapter_id) if chapter_id is not None else None,
        "title": str(chapter.get("title") or "").strip() or None,
        "status": str(chapter.get("chapter_status") or "").strip() or None,
        "section_count": len([item for item in sections if isinstance(item, dict)]),
    }


def _chapters(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    return [chapter for chapter in chapters if isinstance(chapter, dict)]


def _section_rows(registry: Dict[str, Any]) -> List[Tuple[int, Dict[str, Any]]]:
    rows: List[Tuple[int, Dict[str, Any]]] = []
    for chapter in _chapters(registry):
        chapter_id = _common.coerce_int(chapter.get("chapter_id"))
        if chapter_id is None:
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if isinstance(section, dict) and _common.coerce_int(section.get("section_id")) is not None:
                rows.append((chapter_id, section))
    rows.sort(key=lambda item: (item[0], int(item[1].get("section_id") or 0)))
    return rows


def _find_chapter(registry: Dict[str, Any], chapter_id: int) -> Optional[Dict[str, Any]]:
    for chapter in _chapters(registry):
        if _common.coerce_int(chapter.get("chapter_id")) == int(chapter_id):
            return chapter
    return None


def _find_section(registry: Dict[str, Any], chapter_id: Optional[int], section_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if chapter_id is None or section_id is None:
        return None
    chapter = _find_chapter(registry, int(chapter_id))
    if not isinstance(chapter, dict):
        return None
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if isinstance(section, dict) and _common.coerce_int(section.get("section_id")) == int(section_id):
            return section
    return None


def _find_section_for_scene(registry: Dict[str, Any], chapter_id: int, scene_id: int) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    chapter = _find_chapter(registry, chapter_id)
    if not isinstance(chapter, dict):
        return None, None
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        start, end = _section_scene_bounds(section)
        if start is not None and end is not None and int(start) <= int(scene_id) <= int(end):
            return _common.coerce_int(section.get("section_id")), section
    return None, None


def _first_incomplete_section(registry: Dict[str, Any]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    for chapter_id, section in _section_rows(registry):
        if str(section.get("status") or "").strip().lower() != "locked":
            return chapter_id, section
    return None, None


def _next_incomplete_section(registry: Dict[str, Any], chapter_id: int, section_id: int) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    rows = _section_rows(registry)
    seen_current = False
    for row_chapter, section in rows:
        row_section = _common.coerce_int(section.get("section_id"))
        if row_chapter == int(chapter_id) and row_section == int(section_id):
            seen_current = True
            continue
        if seen_current and str(section.get("status") or "").strip().lower() != "locked":
            return row_chapter, section
    return None, None


def _first_unfinalized_chapter(registry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for chapter in _chapters(registry):
        if str(chapter.get("chapter_status") or "").strip().lower() != "finalized":
            return chapter
    return None


def _all_sections_locked(registry: Dict[str, Any]) -> bool:
    rows = _section_rows(registry)
    return bool(rows) and all(str(section.get("status") or "").strip().lower() == "locked" for _, section in rows)


def _book_complete(registry: Dict[str, Any]) -> bool:
    chapters = _chapters(registry)
    return bool(chapters) and _all_sections_locked(registry) and all(
        str(chapter.get("chapter_status") or "").strip().lower() == "finalized"
        for chapter in chapters
    )


def _target_for_section_start(chapter_id: int, section: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    section_id = _common.coerce_int(section.get("section_id"))
    start, _ = _section_scene_bounds(section)
    if section_id is None or start is None:
        return None
    return _scene_ref(chapter_id=chapter_id, section_id=section_id, scene_id=start, section=section)


def _target_status_for_branch(status_branches: List[Any], branch_id: str) -> Optional[str]:
    for branch in status_branches:
        if getattr(branch, "branch_id", None) == branch_id:
            return getattr(branch, "status", None)
    return None


def _chapter_dir(book_root, chapter_id: int):
    return book_root / "draft" / "chapters" / f"ch_{int(chapter_id):03d}"


def _scene_committed(book_root, chapter_id: int, scene_id: int) -> bool:
    chapter_dir = _chapter_dir(book_root, chapter_id)
    return (
        (chapter_dir / f"scene_{int(scene_id):03d}.md").exists()
        and (chapter_dir / f"scene_{int(scene_id):03d}.meta.json").exists()
    )


def _section_commit_state(book_root, chapter_id: int, section: Dict[str, Any]) -> Dict[str, Any]:
    start, end = _section_scene_bounds(section)
    scene_ids = list(range(int(start), int(end) + 1)) if start is not None and end is not None else []
    committed = [scene_id for scene_id in scene_ids if _scene_committed(book_root, chapter_id, scene_id)]
    missing = [scene_id for scene_id in scene_ids if scene_id not in committed]
    return {
        "scene_start": start,
        "scene_end": end,
        "scene_ids": scene_ids,
        "committed_scenes": committed,
        "missing_scenes": missing,
        "complete": bool(scene_ids) and not missing,
    }


def _chapter_lock_state(registry: Dict[str, Any], chapter_id: int) -> Dict[str, Any]:
    chapter = _find_chapter(registry, chapter_id)
    sections = chapter.get("sections") if isinstance(chapter, dict) and isinstance(chapter.get("sections"), list) else []
    locked: List[int] = []
    unlocked: List[Dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = _common.coerce_int(section.get("section_id"))
        if section_id is None:
            continue
        status = str(section.get("status") or "").strip().lower()
        if status == "locked":
            locked.append(section_id)
        else:
            unlocked.append({"section": section_id, "status": status or None})
    return {
        "locked_sections": locked,
        "unlocked_sections": unlocked,
        "complete": bool(sections) and not unlocked,
    }


def _gate(
    gate_key: str,
    label: str,
    *,
    status: str,
    ready: bool,
    scope: Optional[Dict[str, Any]] = None,
    action: Optional[str] = None,
    blocked_reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> WritingGate:
    return WritingGate(
        gate_key=gate_key,
        label=label,
        status=status,
        ready=ready,
        scope=scope or {},
        action=action,
        blocked_reason=blocked_reason,
        details=details or {},
    )


def get_next_writing_target(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    prefer_emitted: bool = True,
) -> NextWritingTarget:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    canonical_book_root = _common.book_root(workspace, book_id)
    book_root = _common.execution_book_root(canonical_book_root, resolved_branch_id)
    registry = _common.load_registry(book_root)
    status = get_workspace_status_for_branch(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        prefer_emitted=prefer_emitted,
    )
    node = current_execution_node(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        prefer_emitted=prefer_emitted,
    )
    cursor = status.cursor if isinstance(status.cursor, dict) else {}
    active_section = status.active_section if isinstance(status.active_section, dict) else None
    active_chapter = _common.coerce_int((active_section or {}).get("chapter_id"))
    active_section_id = _common.coerce_int((active_section or {}).get("section_id"))
    cursor_chapter = _common.coerce_int(cursor.get("chapter"))
    cursor_scene = _common.coerce_int(cursor.get("scene"))

    resolved_chapter = chapter_id or cursor_chapter or active_chapter
    resolved_section = section_id or active_section_id
    resolved_scene = scene_id or cursor_scene

    if resolved_scene is None and resolved_chapter is not None and resolved_section is not None:
        section = _find_section(registry, resolved_chapter, resolved_section)
        if section is not None:
            resolved_scene, _ = _section_scene_bounds(section)

    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family="section_write",
        chapter=resolved_chapter,
        section=resolved_section,
        scene=resolved_scene,
    )

    details: Dict[str, Any] = {
        "branch_lifecycle_state": _target_status_for_branch(status.branches, resolved_branch_id),
        "cursor": dict(cursor),
        "active_section": dict(active_section) if isinstance(active_section, dict) else None,
        "source_run_id": status.source_run_id,
    }

    if resolved_branch_id != MAIN_BRANCH_ID and details["branch_lifecycle_state"] in {"discard", "promoted"}:
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=selector,
            node=node,
            status="blocked",
            book_complete=False,
            can_continue=False,
            blocked_reason=f"Branch {resolved_branch_id} is {details['branch_lifecycle_state']} and is not write-ready.",
            details=details,
        )

    if not _section_rows(registry):
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=selector,
            node=node,
            status="blocked",
            book_complete=False,
            can_continue=False,
            blocked_reason="No section workflow registry is available.",
            details=details,
        )

    if _book_complete(registry):
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=selector,
            node=node,
            status="complete",
            book_complete=True,
            can_continue=False,
            recommended_action=None,
            blocked_reason="Book is complete.",
            details=details,
        )

    if not isinstance(active_section, dict):
        next_chapter_id, next_section = _first_incomplete_section(registry)
        next_section_ref = _section_ref(next_chapter_id, next_section) if next_chapter_id is not None and next_section is not None else None
        unfinalized = _first_unfinalized_chapter(registry)
        recommended = None
        blocked = "No active frozen section is available for scene writing."
        if next_section is not None and str(next_section.get("status") or "").strip().lower() == "stub":
            recommended = "freeze_section_from_phase03_artifact"
            blocked = "Next section must be frozen before scene writing can continue."
        elif next_section is None and unfinalized is not None:
            recommended = "finalize_chapter_from_locked_sections"
            blocked = "All sections are locked, but a chapter still needs finalization."
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=selector,
            node=node,
            status="blocked",
            book_complete=False,
            can_continue=False,
            next_section=next_section_ref,
            next_chapter=_chapter_ref(unfinalized) if unfinalized is not None else None,
            recommended_action=recommended,
            blocked_reason=blocked,
            details=details,
        )

    active_status = str(active_section.get("status") or "").strip().lower()
    if active_status != "frozen":
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=selector,
            node=node,
            status="blocked",
            book_complete=False,
            can_continue=False,
            blocked_reason="Active section is not frozen.",
            details=details,
        )

    if resolved_chapter is None or resolved_scene is None:
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=selector,
            node=node,
            status="blocked",
            book_complete=False,
            can_continue=False,
            blocked_reason="Unable to resolve a current scene target.",
            details=details,
        )

    section_for_scene_id, section_for_scene = _find_section_for_scene(registry, int(resolved_chapter), int(resolved_scene))
    if section_for_scene is None:
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=selector,
            node=node,
            status="blocked",
            book_complete=False,
            can_continue=False,
            blocked_reason="Current scene is outside the active section range.",
            details=details,
        )

    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=int(resolved_chapter),
        scene_id=int(resolved_scene),
        section_id=section_for_scene_id,
        prefer_emitted=prefer_emitted,
    )
    current_scene = _scene_ref(
        chapter_id=int(resolved_chapter),
        section_id=section_for_scene_id,
        scene_id=int(resolved_scene),
        section=section_for_scene,
        scene_status=readiness.scene_status,
        recommended_next_action=readiness.recommended_next_action,
    )
    details["scene_readiness_status"] = readiness.scene_status
    details["scene_readiness_recommended_next_action"] = readiness.recommended_next_action

    start, end = _section_scene_bounds(section_for_scene)
    if readiness.scene_status == "committed" and end is not None and int(resolved_scene) < int(end):
        next_scene_id = int(resolved_scene) + 1
        next_scene = _scene_ref(
            chapter_id=int(resolved_chapter),
            section_id=section_for_scene_id,
            scene_id=next_scene_id,
            section=section_for_scene,
        )
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=ScopeSelector(
                book_id=book_id,
                branch_id=resolved_branch_id,
                workflow_family="section_write",
                chapter=int(resolved_chapter),
                section=section_for_scene_id,
                scene=next_scene_id,
            ),
            node=node,
            status="ready",
            book_complete=False,
            can_continue=True,
            current_scene=current_scene,
            next_scene=next_scene,
            recommended_action="continue_scene",
            details=details,
        )

    if readiness.scene_status == "committed":
        next_chapter_id, next_section = _next_incomplete_section(registry, int(resolved_chapter), int(section_for_scene_id or 0))
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=readiness.selector,
            node=readiness.node or node,
            status="blocked",
            book_complete=False,
            can_continue=False,
            current_scene=current_scene,
            next_section=_section_ref(next_chapter_id, next_section) if next_chapter_id is not None and next_section is not None else None,
            recommended_action="lock_section_from_written_state",
            blocked_reason="Current section has no remaining uncommitted scene target; lock the section before continuing.",
            details=details,
        )

    if readiness.recommended_next_action:
        return NextWritingTarget(
            book_id=book_id,
            branch_id=resolved_branch_id,
            selector=readiness.selector,
            node=readiness.node or node,
            status="ready",
            book_complete=False,
            can_continue=True,
            current_scene=current_scene,
            recommended_action="continue_scene",
            details=details,
        )

    return NextWritingTarget(
        book_id=book_id,
        branch_id=resolved_branch_id,
        selector=readiness.selector,
        node=readiness.node or node,
        status="blocked",
        book_complete=False,
        can_continue=False,
        current_scene=current_scene,
        blocked_reason="No ready scene-phase action is available for the current scene.",
        details=details,
    )


def get_writing_gate_status(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    prefer_emitted: bool = True,
) -> WritingGateStatus:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    canonical_book_root = _common.book_root(workspace, book_id)
    book_root = _common.execution_book_root(canonical_book_root, resolved_branch_id)
    registry = _common.load_registry(book_root)
    target = get_next_writing_target(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        prefer_emitted=prefer_emitted,
    )
    selector = target.selector
    resolved_chapter = selector.chapter or chapter_id
    resolved_section = selector.section or section_id
    resolved_scene = selector.scene or scene_id
    section = _find_section(registry, resolved_chapter, resolved_section)
    if section is None and resolved_chapter is not None and resolved_scene is not None:
        resolved_section, section = _find_section_for_scene(registry, int(resolved_chapter), int(resolved_scene))
    chapter = _find_chapter(registry, int(resolved_chapter)) if resolved_chapter is not None else None

    gates: List[WritingGate] = []

    scene_scope = {
        "chapter": int(resolved_chapter) if resolved_chapter is not None else None,
        "section": int(resolved_section) if resolved_section is not None else None,
        "scene": int(resolved_scene) if resolved_scene is not None else None,
    }
    scene_ready = bool(target.can_continue and target.recommended_action == "continue_scene")
    gates.append(
        _gate(
            "scene_continue",
            "Continue current scene",
            status="ready" if scene_ready else ("complete" if target.book_complete else "blocked"),
            ready=scene_ready,
            scope=scene_scope,
            action="continue_scene" if scene_ready else None,
            blocked_reason=None if scene_ready else (target.blocked_reason or "No ready scene-phase action is available."),
            details={
                "next_writing_target_status": target.status,
                "next_writing_target_recommended_action": target.recommended_action,
                "current_scene": target.current_scene,
            },
        )
    )

    section_scope = {
        "chapter": int(resolved_chapter) if resolved_chapter is not None else None,
        "section": int(resolved_section) if resolved_section is not None else None,
    }
    if section is None or resolved_chapter is None or resolved_section is None:
        gates.append(
            _gate(
                "section_lock",
                "Lock section",
                status="not_applicable",
                ready=False,
                scope=section_scope,
                blocked_reason="No section scope is resolved.",
            )
        )
    else:
        section_status = str(section.get("status") or "").strip().lower()
        commit_state = _section_commit_state(book_root, int(resolved_chapter), section)
        if section_status == "locked":
            gates.append(
                _gate(
                    "section_lock",
                    "Lock section",
                    status="complete",
                    ready=False,
                    scope=section_scope,
                    details={**commit_state, "section_status": section_status},
                )
            )
        elif section_status == "frozen" and commit_state["complete"]:
            gates.append(
                _gate(
                    "section_lock",
                    "Lock section",
                    status="ready",
                    ready=True,
                    scope=section_scope,
                    action="lock_section_from_written_state",
                    details={
                        **commit_state,
                        "section_status": section_status,
                        "mutation_scope": "canonical" if resolved_branch_id == MAIN_BRANCH_ID else "branch_authoritative",
                    },
                )
            )
        else:
            gates.append(
                _gate(
                    "section_lock",
                    "Lock section",
                    status="blocked",
                    ready=False,
                    scope=section_scope,
                    blocked_reason=(
                        "Section must be frozen before it can be locked."
                        if section_status != "frozen"
                        else "Section still has uncommitted scene artifacts."
                    ),
                    details={**commit_state, "section_status": section_status},
                )
            )

    chapter_scope = {"chapter": int(resolved_chapter) if resolved_chapter is not None else None}
    if chapter is None or resolved_chapter is None:
        gates.append(
            _gate(
                "chapter_finalize",
                "Finalize chapter",
                status="not_applicable",
                ready=False,
                scope=chapter_scope,
                blocked_reason="No chapter scope is resolved.",
            )
        )
    else:
        chapter_status = str(chapter.get("chapter_status") or "").strip().lower()
        lock_state = _chapter_lock_state(registry, int(resolved_chapter))
        if chapter_status == "finalized":
            gates.append(
                _gate(
                    "chapter_finalize",
                    "Finalize chapter",
                    status="complete",
                    ready=False,
                    scope=chapter_scope,
                    details={**lock_state, "chapter_status": chapter_status},
                )
            )
        elif lock_state["complete"]:
            gates.append(
                _gate(
                    "chapter_finalize",
                    "Finalize chapter",
                    status="ready",
                    ready=True,
                    scope=chapter_scope,
                    action="finalize_chapter_from_locked_sections",
                    details={
                        **lock_state,
                        "chapter_status": chapter_status,
                        "mutation_scope": "canonical" if resolved_branch_id == MAIN_BRANCH_ID else "branch_authoritative",
                    },
                )
            )
        else:
            gates.append(
                _gate(
                    "chapter_finalize",
                    "Finalize chapter",
                    status="blocked",
                    ready=False,
                    scope=chapter_scope,
                    blocked_reason="Chapter has sections that are not locked.",
                    details={**lock_state, "chapter_status": chapter_status},
                )
            )

    if target.book_complete:
        gates.append(
            _gate(
                "book_continue",
                "Continue book",
                status="complete",
                ready=False,
                action=None,
                blocked_reason="Book is complete.",
            )
        )
    elif target.recommended_action:
        gates.append(
            _gate(
                "book_continue",
                "Continue book",
                status="ready",
                ready=True,
                action=target.recommended_action,
                blocked_reason=None,
                details={
                    "target_status": target.status,
                    "target_blocked_reason": target.blocked_reason,
                    "target_can_continue_scene": bool(target.can_continue),
                },
            )
        )
    else:
        gates.append(
            _gate(
                "book_continue",
                "Continue book",
                status="blocked",
                ready=False,
                blocked_reason=target.blocked_reason or "No next writing action is available.",
                details={"target_status": target.status},
            )
        )

    if target.book_complete:
        gates.append(
            _gate(
                "manuscript_export",
                "Export manuscript",
                status="blocked",
                ready=False,
                blocked_reason="Manuscript export and quality gates are not implemented yet.",
                details={"book_complete": True, "designed_gap": "gap.compile_export_quality"},
            )
        )
    else:
        gates.append(
            _gate(
                "manuscript_export",
                "Export manuscript",
                status="blocked",
                ready=False,
                blocked_reason="Book must be complete before manuscript export can be considered.",
                details={"book_complete": False, "designed_gap": "gap.compile_export_quality"},
            )
        )

    ready_actions = [gate.action for gate in gates if gate.ready and gate.action]
    recommended_next_action = ready_actions[0] if ready_actions else None
    can_continue = any(gate.gate_key == "book_continue" and gate.ready for gate in gates)
    blocked_reason = None
    if not can_continue:
        book_gate = next((gate for gate in gates if gate.gate_key == "book_continue"), None)
        blocked_reason = book_gate.blocked_reason if book_gate else target.blocked_reason

    return WritingGateStatus(
        book_id=book_id,
        branch_id=resolved_branch_id,
        selector=selector,
        node=target.node,
        book_complete=target.book_complete,
        can_continue=can_continue,
        recommended_next_action=recommended_next_action,
        blocked_reason=blocked_reason,
        gates=gates,
        details={
            "next_writing_target": target.to_dict(),
            "implemented_export_gate": False,
        },
    )
