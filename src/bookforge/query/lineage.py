from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from bookforge.contracts import ScopeSelector, TimelineNodeRef, classify_source_artifact

from . import _common
from .workspace import current_main_node, get_workspace_status


def _preferred_run_anchor(run_dir: Path) -> Optional[Path]:
    for name in ("outline_final_v1_1.json", "outline_seams_hygiened_v1_1.json", "outline_sections_v1.json", "outline_spine_v1.json"):
        candidate = run_dir / name
        if candidate.exists():
            return candidate
    return None


def get_source_run(workspace, book_id: str, run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    book_root = _common.book_root(workspace, book_id)
    resolved_run_id = run_id or _common.latest_outline_run_id(book_root)
    if not resolved_run_id:
        return None
    run_dir = _common.outline_root(book_root) / "pipeline_runs" / resolved_run_id
    if not run_dir.exists():
        return None
    anchor = _preferred_run_anchor(run_dir)
    if anchor is None:
        return None
    return {
        "book_id": book_id,
        "run_id": resolved_run_id,
        "run_dir": run_dir.as_posix(),
        "anchor_path": anchor.as_posix(),
        "artifact_class": classify_source_artifact(anchor).value,
    }


def get_frozen_chapter_projection(workspace, book_id: str, chapter_id: int) -> Optional[Dict[str, Any]]:
    book_root = _common.book_root(workspace, book_id)
    path = _common.outline_root(book_root) / "chapters" / f"ch_{int(chapter_id):03d}.json"
    if not path.exists():
        return None
    return {
        "chapter_id": int(chapter_id),
        "path": path.as_posix(),
        "artifact_class": classify_source_artifact(path).value,
    }


def get_section_draft_lineage(workspace, book_id: str, chapter_id: int, section_id: int) -> Optional[Dict[str, Any]]:
    book_root = _common.book_root(workspace, book_id)
    path = _common.outline_root(book_root) / "section_drafts" / f"ch_{int(chapter_id):03d}_sec_{int(section_id):03d}_phase03.json"
    if not path.exists():
        return None
    return {
        "chapter_id": int(chapter_id),
        "section_id": int(section_id),
        "path": path.as_posix(),
        "artifact_class": classify_source_artifact(path).value,
    }


def materialization_source_for_section(workspace, book_id: str, chapter_id: int, section_id: int) -> Optional[Dict[str, Any]]:
    source_run = get_source_run(workspace, book_id)
    if source_run:
        return source_run
    chapter_projection = get_frozen_chapter_projection(workspace, book_id, chapter_id)
    if chapter_projection:
        return chapter_projection
    section_draft = get_section_draft_lineage(workspace, book_id, chapter_id, section_id)
    if section_draft:
        return section_draft
    book_root = _common.book_root(workspace, book_id)
    outline_path = _common.outline_root(book_root) / "outline.json"
    if outline_path.exists():
        return {
            "path": outline_path.as_posix(),
            "artifact_class": classify_source_artifact(outline_path).value,
        }
    return None


def resolve_scope_selector(workspace, selector: ScopeSelector) -> Optional[TimelineNodeRef]:
    status = get_workspace_status(workspace, selector.book_id)
    if selector.branch_id and selector.branch_id != "main":
        for branch in status.branches:
            if branch.branch_id == selector.branch_id:
                node = branch.current_node
                break
        else:
            return None
    elif selector.fork_group_id:
        node = None
        for branch in status.branches:
            if branch.fork_group_id == selector.fork_group_id and branch.current_node is not None:
                node = branch.current_node
                break
        if node is None:
            return None
    else:
        node = current_main_node(workspace, selector.book_id)
        if node is None:
            return None

    if selector.workflow_family and node.workflow_family != selector.workflow_family:
        return None
    if selector.chapter is not None and node.chapter != selector.chapter:
        return None
    if selector.section is not None and node.section != selector.section:
        return None
    if selector.scene is not None and node.scene != selector.scene:
        return None
    if selector.phase_id is not None and node.phase_id != selector.phase_id:
        return None
    if selector.turn_id is not None and node.turn_id != selector.turn_id:
        return None
    return node
