from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from bookforge import section_workflow as sw
from bookforge.contracts import TimelineNodeRef, execution_result_for_branch_lifecycle
from bookforge.supervision import capture_surface_snapshot, emit_reconciled_branch_contracts

from .branching_store import (
    _book_root,
    _branch_outline_root,
    _branch_snapshot_root,
    _evolve_manifest,
    _load_manifest,
    _read_json,
    _revision_token,
    _write_branch_node,
    _write_json,
    _write_manifest,
)


def rerun_freeze_section_on_branch(
    workspace: Path,
    book_id: str,
    branch_id: str,
    chapter_id: int,
    section_id: int,
    *,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    book_root = _book_root(workspace, book_id)
    manifest = _load_manifest(book_root, branch_id)
    resolved_run_id = str(run_id or manifest.source_run_id).strip()
    if resolved_run_id != manifest.source_run_id:
        raise ValueError(
            f"Branch {branch_id} is pinned to source run {manifest.source_run_id}; refusing silent source switch to {resolved_run_id}."
        )

    snapshot_root = _branch_snapshot_root(book_root, branch_id)
    outline_path = _branch_outline_root(book_root, branch_id) / "outline.json"
    registry_path = _branch_outline_root(book_root, branch_id) / sw.REGISTRY_FILENAME
    if not outline_path.exists() or not registry_path.exists():
        raise FileNotFoundError(f"Branch snapshot is incomplete for {branch_id}.")

    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    outline = _read_json(outline_path)
    registry = _read_json(registry_path)
    _, run_dir = sw._pipeline_run_dir(book_root, resolved_run_id)
    sw._assert_freeze_preconditions(registry, chapter_id, section_id)
    registry_section = sw._find_registry_section(registry, chapter_id, section_id)
    outline_section = sw._find_outline_section(outline, chapter_id, section_id)
    current_status = str(registry_section.get("status") or outline_section.get("status") or "").strip().lower()
    if current_status in {"frozen", "locked"}:
        manifest = _evolve_manifest(manifest, lifecycle_state="promote_ready")
        _write_manifest(book_root, manifest)
        emit_reconciled_branch_contracts(
            workspace=workspace,
            book_id=book_id,
            branch_id=branch_id,
            before_snapshot=before_snapshot,
            action="rerun_freeze_section_on_branch",
            result_status=execution_result_for_branch_lifecycle("promote_ready"),
            message=f"Branch section {chapter_id}:{section_id} already materialized.",
        )
        return {"status": current_status, "updated": False}

    phase03 = sw._find_phase03_section(run_dir, chapter_id, section_id)
    phase03_payload = phase03["payload"]
    phase03_section = phase03["section"]
    scenes = phase03_section.get("scenes") if isinstance(phase03_section.get("scenes"), list) else []
    if not scenes:
        raise ValueError(f"Cannot freeze empty section {chapter_id}:{section_id}.")

    outline_section.update(
        {
            "title": str(phase03_section.get("title") or outline_section.get("title") or "").strip(),
            "intent": str(phase03_section.get("intent") or outline_section.get("intent") or "").strip(),
            "end_condition": str(phase03_section.get("end_condition") or outline_section.get("end_condition") or "").strip(),
            "status": "frozen",
            "scenes": scenes,
        }
    )
    outline["characters"] = sw._merge_registry_items(
        list(outline.get("characters") if isinstance(outline.get("characters"), list) else []),
        list(phase03_payload.get("characters") if isinstance(phase03_payload.get("characters"), list) else []),
        "character_id",
    )
    outline["threads"] = sw._merge_registry_items(
        list(outline.get("threads") if isinstance(outline.get("threads"), list) else []),
        list(phase03_payload.get("threads") if isinstance(phase03_payload.get("threads"), list) else []),
        "thread_id",
    )
    sw._normalize_chapter_scene_graph(book_root=snapshot_root, outline=outline, registry=registry, chapter_id=chapter_id)

    scene_start, scene_end = sw._section_scene_range(outline_section)
    if scene_start is None or scene_end is None:
        raise ValueError(f"Unable to derive scene range for branch section {chapter_id}:{section_id}.")
    boundary_path = sw._emit_boundary_artifact(snapshot_root, outline, chapter_id, section_id)
    registry_section["status"] = "frozen"
    registry_section["scene_ref_start"] = f"{chapter_id}:{scene_start}"
    registry_section["scene_ref_end"] = f"{chapter_id}:{scene_end}"
    registry_section["boundary_artifact"] = sw._registry_relpath(snapshot_root, boundary_path)
    registry["active_section"] = {"chapter_id": chapter_id, "section_id": section_id, "status": "frozen"}

    state_path = snapshot_root / "state.json"
    if state_path.exists():
        state = _read_json(state_path)
        cursor = state.get("cursor") if isinstance(state.get("cursor"), dict) else {}
        current_chapter = int(cursor.get("chapter", 0) or 0)
        current_scene = int(cursor.get("scene", 0) or 0)
        if current_chapter <= 0 or current_scene <= 0:
            state["cursor"] = {"chapter": chapter_id, "scene": scene_start}
        state["status"] = "OUTLINED"
        _write_json(state_path, state)

    paths = sw._write_workflow_state(snapshot_root, outline, registry)
    branch_node = TimelineNodeRef(
        book_id=book_id,
        workflow_family="section_local_outline",
        source_run_id=manifest.source_run_id,
        branch_id=branch_id,
        fork_group_id=manifest.fork_group_id,
        chapter=chapter_id,
        section=section_id,
        scene=scene_end,
        phase_id="freeze_section_from_phase03_artifact",
        turn_id=None,
        revision_id=_revision_token(),
    )
    _write_branch_node(book_root, branch_node)
    manifest = _evolve_manifest(
        manifest,
        lifecycle_state="promote_ready",
        workflow_family=branch_node.workflow_family,
    )
    _write_manifest(book_root, manifest)
    emit_reconciled_branch_contracts(
        workspace=workspace,
        book_id=book_id,
        branch_id=branch_id,
        before_snapshot=before_snapshot,
        action="rerun_freeze_section_on_branch",
        result_status=execution_result_for_branch_lifecycle("promote_ready"),
        message=f"Section {chapter_id}:{section_id} rerun on branch {branch_id}.",
        artifact_paths={
            "outline": outline_path.relative_to(book_root).as_posix(),
            "registry": registry_path.relative_to(book_root).as_posix(),
            "boundary_artifact": boundary_path.relative_to(book_root).as_posix(),
        },
        details={
            "run_id": resolved_run_id,
            "chapter_id": chapter_id,
            "section_id": section_id,
        },
    )
    return {
        "status": "frozen",
        "updated": True,
        "outline_path": str(paths["outline"]),
        "registry_path": str(paths["registry"]),
        "boundary_artifact": str(boundary_path),
    }
