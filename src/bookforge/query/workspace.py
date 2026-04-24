from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bookforge.contracts import TimelineNodeRef
from . import _common


_WRITE_PHASES = {
    "characters_generate",
    "style_anchor",
    "plan",
    "plan_scene",
    "preflight",
    "scene_state_preflight",
    "continuity_pack",
    "write",
    "write_scene",
    "repair",
    "repair_scene",
    "state_repair",
    "lint",
    "lint_scene",
    "apply_state",
    "persist_scene",
    "appearance_projection",
    "compile_chapter",
    "cursor_advance",
    "run_complete",
}


@dataclass(frozen=True, slots=True)
class BranchState:
    branch_id: str
    fork_group_id: Optional[str]
    status: Optional[str]
    parent_node: Optional[TimelineNodeRef]
    current_node: Optional[TimelineNodeRef]
    manifest_path: str


@dataclass(frozen=True, slots=True)
class WorkspaceStatus:
    book_id: str
    state_status: Optional[str]
    cursor: Dict[str, Any]
    source_run_id: Optional[str]
    active_section: Optional[Dict[str, Any]]
    current_node: Optional[TimelineNodeRef]
    pause_marker: Optional[Dict[str, Any]]
    progress_heartbeat: Optional[Dict[str, Any]]
    branches: List[BranchState]
    chapter_status_counts: Dict[str, int]


def _load_branch_state(book_root, branch_id: str) -> BranchState:
    manifest_path = _common.branch_manifest_path(book_root, branch_id)
    manifest = _common.read_json(manifest_path) or {}
    current_payload = _common.read_json(_common.branch_current_node_path(book_root, branch_id))
    parent_payload = manifest.get("parent_node") if isinstance(manifest.get("parent_node"), dict) else None
    parent_node = TimelineNodeRef.from_dict(parent_payload) if parent_payload else None
    current_node = TimelineNodeRef.from_dict(current_payload) if isinstance(current_payload, dict) else None
    return BranchState(
        branch_id=branch_id,
        fork_group_id=_common.first_non_empty([manifest.get("fork_group_id")]),
        status=_common.first_non_empty([manifest.get("lifecycle_state"), manifest.get("status")]),
        parent_node=parent_node,
        current_node=current_node,
        manifest_path=manifest_path.as_posix(),
    )


def _infer_main_family(
    book_root,
    *,
    progress: Optional[Dict[str, Any]],
    pause: Optional[Dict[str, Any]],
    outline_pause: Optional[Dict[str, Any]],
    registry: Dict[str, Any],
) -> Optional[str]:
    progress_phase = str((progress or {}).get("phase") or "").strip()
    progress_status = str((progress or {}).get("status") or "").strip().lower()
    pause_phase = str((pause or {}).get("phase") or "").strip()
    registry_time = _common.payload_timestamp(registry)
    write_time_candidates = []
    if progress_phase in _WRITE_PHASES:
        progress_time = _common.payload_timestamp(progress)
        if progress_time is not None:
            write_time_candidates.append(progress_time)
    if pause_phase in _WRITE_PHASES:
        pause_time = _common.payload_timestamp(pause)
        if pause_time is not None:
            write_time_candidates.append(pause_time)
    latest_write_time = max(write_time_candidates) if write_time_candidates else None
    if pause_phase in _WRITE_PHASES or (progress_status == "paused" and progress_phase in _WRITE_PHASES):
        return "section_write"
    if progress_phase in _WRITE_PHASES:
        if latest_write_time is None or registry_time is None or latest_write_time > registry_time:
            return "section_write"
    if registry:
        return "section_local_outline"
    if progress_phase in _WRITE_PHASES or pause_phase in _WRITE_PHASES:
        return "section_write"
    if outline_pause or _common.latest_outline_run_id(book_root):
        return "deep_outline"
    return None


def _load_emitted_main_node(book_root) -> Optional[TimelineNodeRef]:
    payload = _common.read_json(_common.main_current_node_path(book_root))
    if not isinstance(payload, dict):
        return None
    try:
        return TimelineNodeRef.from_dict(payload)
    except ValueError:
        return None


def _execution_book_root(book_root, branch_id: str):
    from bookforge.supervision import paths as supervision_paths
    resolved_branch_id = str(branch_id or "main").strip() or "main"
    if resolved_branch_id == "main":
        return book_root
    return supervision_paths.branch_snapshot_root(book_root, resolved_branch_id)


def _load_branch_node(book_root, branch_id: str) -> Optional[TimelineNodeRef]:
    if not branch_id or branch_id == "main":
        return None
    payload = _common.read_json(_common.branch_current_node_path(book_root, branch_id))
    if not isinstance(payload, dict):
        return None
    try:
        return TimelineNodeRef.from_dict(payload)
    except ValueError:
        return None


def _chapter_status_counts(registry: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        status = str(chapter.get("chapter_status") or "").strip()
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def current_main_node(workspace, book_id: str, *, prefer_emitted: bool = True) -> Optional[TimelineNodeRef]:
    book_root = _common.book_root(workspace, book_id)
    if prefer_emitted:
        emitted = _load_emitted_main_node(book_root)
        if emitted is not None:
            return emitted
    registry = _common.load_registry(book_root)
    state = _common.load_book_state(book_root)
    _, progress = _common.latest_run_progress(book_root)
    pause = _common.state_pause_marker(book_root)
    outline_pause = _common.latest_outline_pause_marker(book_root)
    workflow_family = _infer_main_family(book_root, progress=progress, pause=pause, outline_pause=outline_pause, registry=registry)
    source_run_id = _common.first_non_empty([registry.get("source_run_id"), _common.latest_outline_run_id(book_root)])
    if not workflow_family or not source_run_id:
        return None

    active_section = registry.get("active_section") if isinstance(registry.get("active_section"), dict) else {}
    cursor = state.get("cursor") if isinstance(state.get("cursor"), dict) else {}
    chapter = _common.coerce_int((progress or {}).get("chapter")) or _common.coerce_int((pause or {}).get("chapter"))
    chapter = chapter or _common.coerce_int(active_section.get("chapter_id")) or _common.coerce_int(cursor.get("chapter"))
    section = _common.coerce_int((progress or {}).get("section")) or _common.coerce_int(active_section.get("section_id"))
    scene = _common.coerce_int((progress or {}).get("scene")) or _common.coerce_int((pause or {}).get("scene")) or _common.coerce_int(cursor.get("scene"))
    phase_id = _common.first_non_empty([(progress or {}).get("phase"), (pause or {}).get("phase"), (outline_pause or {}).get("step_id")])
    turn_id = _common.first_non_empty([(progress or {}).get("turn")])
    revision_id = _common.compact_revision(progress, pause, outline_pause, registry, state)

    return TimelineNodeRef(
        book_id=book_id,
        workflow_family=workflow_family,
        source_run_id=source_run_id,
        branch_id="main",
        fork_group_id=None,
        chapter=chapter,
        section=section,
        scene=scene,
        phase_id=phase_id,
        turn_id=turn_id,
        revision_id=revision_id,
    )


def current_execution_node(
    workspace,
    book_id: str,
    *,
    branch_id: str = "main",
    prefer_emitted: bool = True,
) -> Optional[TimelineNodeRef]:
    resolved_branch_id = str(branch_id or "main").strip() or "main"
    if resolved_branch_id == "main":
        return current_main_node(workspace, book_id, prefer_emitted=prefer_emitted)
    book_root = _common.book_root(workspace, book_id)
    return _load_branch_node(book_root, resolved_branch_id)


def get_section_status(
    workspace,
    book_id: str,
    chapter_id: int,
    section_id: int,
    *,
    branch_id: str = "main",
) -> Optional[Dict[str, Any]]:
    book_root = _common.book_root(workspace, book_id)
    registry = _common.load_registry(_execution_book_root(book_root, branch_id))
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if _common.coerce_int(chapter.get("chapter_id")) != int(chapter_id):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if _common.coerce_int(section.get("section_id")) == int(section_id):
                return section
    return None


def get_workspace_status(workspace, book_id: str, *, prefer_emitted: bool = True) -> WorkspaceStatus:
    book_root = _common.book_root(workspace, book_id)
    return get_workspace_status_for_branch(
        workspace,
        book_id,
        branch_id="main",
        prefer_emitted=prefer_emitted,
    )


def get_workspace_status_for_branch(
    workspace,
    book_id: str,
    *,
    branch_id: str = "main",
    prefer_emitted: bool = True,
) -> WorkspaceStatus:
    book_root = _common.book_root(workspace, book_id)
    execution_root = _execution_book_root(book_root, branch_id)
    state = _common.load_book_state(execution_root)
    registry = _common.load_registry(execution_root)
    _, progress = _common.latest_run_progress(execution_root)
    pause = _common.state_pause_marker(execution_root) or _common.latest_outline_pause_marker(execution_root)
    branches = [_load_branch_state(book_root, branch_id) for branch_id in _common.list_branch_ids(book_root)]
    current_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=prefer_emitted)
    source_run_id = _common.first_non_empty(
        [
            registry.get("source_run_id"),
            current_node.source_run_id if current_node is not None else None,
            _common.latest_outline_run_id(execution_root),
        ]
    )
    return WorkspaceStatus(
        book_id=book_id,
        state_status=_common.first_non_empty([state.get("status")]),
        cursor=state.get("cursor") if isinstance(state.get("cursor"), dict) else {},
        source_run_id=source_run_id,
        active_section=registry.get("active_section") if isinstance(registry.get("active_section"), dict) else None,
        current_node=current_node,
        pause_marker=pause,
        progress_heartbeat=progress,
        branches=branches,
        chapter_status_counts=_chapter_status_counts(registry),
    )
