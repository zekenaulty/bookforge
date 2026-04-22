from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .lineage import get_source_run, materialization_source_for_section
from .workspace import get_workspace_status


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    book_id: str
    workflow_family: Optional[str]
    run_mode: str
    branch_id: str
    fork_group_id: Optional[str]
    last_explicit_action: Optional[str]
    source_artifact_class: Optional[str]
    source_artifact_path: Optional[str]


def get_workflow_snapshot(workspace, book_id: str, *, prefer_emitted: bool = True) -> WorkflowSnapshot:
    status = get_workspace_status(workspace, book_id, prefer_emitted=prefer_emitted)
    node = status.current_node
    pause = status.pause_marker or {}
    progress = status.progress_heartbeat or {}
    active_section = status.active_section or {}

    if pause:
        run_mode = "paused"
    elif progress:
        run_mode = str(progress.get("status") or "running").strip() or "running"
    else:
        run_mode = "idle"

    chapter = active_section.get("chapter_id")
    section = active_section.get("section_id")
    source = None
    if chapter is not None and section is not None:
        source = materialization_source_for_section(workspace, book_id, int(chapter), int(section))
    if source is None and node and node.chapter is not None and node.section is not None:
        source = materialization_source_for_section(workspace, book_id, node.chapter, node.section)
    if source is None:
        source = get_source_run(workspace, book_id)

    return WorkflowSnapshot(
        book_id=book_id,
        workflow_family=node.workflow_family if node else None,
        run_mode=run_mode,
        branch_id=node.branch_id if node else "main",
        fork_group_id=node.fork_group_id if node else None,
        last_explicit_action=str(progress.get("phase") or pause.get("phase") or pause.get("step_id") or "").strip() or None,
        source_artifact_class=str((source or {}).get("artifact_class") or "").strip() or None,
        source_artifact_path=str((source or {}).get("anchor_path") or (source or {}).get("path") or "").strip() or None,
    )
