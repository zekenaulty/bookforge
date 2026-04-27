from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bookforge import section_workflow as sw
from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID
from bookforge.query.recovery import get_recovery_manifest
from bookforge.supervision import RuntimeIssue, capture_surface_snapshot

from .recovery_common import (
    advance_recovery_node,
    book_root,
    emit_result,
    execution_root,
    load_recovery_scope,
    read_json,
    relative,
    write_receipt,
)
from .scoped import build_write_section_request, write_frozen_section


def _chapter(outline: Dict[str, Any], chapter_id: int) -> Optional[Dict[str, Any]]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if isinstance(chapter, dict) and int(chapter.get("chapter_id", 0) or 0) == int(chapter_id):
            return chapter
    return None


def _section(chapter: Dict[str, Any], section_id: int) -> Optional[Dict[str, Any]]:
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if isinstance(section, dict) and int(section.get("section_id", 0) or 0) == int(section_id):
            return section
    return None


def _target_sections(scope, outline: Dict[str, Any]) -> List[Tuple[int, int]]:
    targets: List[Tuple[int, int]] = []
    for item in scope.affected_scopes:
        chapter_id = int(item["chapter_id"])
        chapter = _chapter(outline, chapter_id)
        if chapter is None:
            continue
        if "section_id" in item:
            targets.append((chapter_id, int(item["section_id"])))
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if isinstance(section, dict) and int(section.get("section_id", 0) or 0) >= 1:
                targets.append((chapter_id, int(section["section_id"])))
    return sorted(set(targets))


def _scene_range(section: Dict[str, Any]) -> Tuple[int, int]:
    scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
    scene_ids = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        try:
            scene_ids.append(int(scene.get("scene_id")))
        except (TypeError, ValueError):
            continue
    if not scene_ids:
        raise ValueError("redraft_scope requires normalized sections with at least one scene.")
    return min(scene_ids), max(scene_ids)


def _find_registry_chapter(registry: Dict[str, Any], chapter_id: int) -> Dict[str, Any]:
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if isinstance(chapter, dict) and int(chapter.get("chapter_id", 0) or 0) == int(chapter_id):
            return chapter
    raise ValueError(f"Registry chapter not found: {chapter_id}")


def _find_registry_section(registry: Dict[str, Any], chapter_id: int, section_id: int) -> Dict[str, Any]:
    chapter = _find_registry_chapter(registry, chapter_id)
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    for section in sections:
        if isinstance(section, dict) and int(section.get("section_id", 0) or 0) == int(section_id):
            return section
    raise ValueError(f"Registry section not found: {chapter_id}:{section_id}")


def _freeze_branch_section_for_redraft(branch_root: Path, chapter_id: int, section_id: int) -> Dict[str, Any]:
    outline = read_json(branch_root / "outline" / "outline.json")
    registry = read_json(branch_root / "outline" / sw.REGISTRY_FILENAME)
    chapter = _chapter(outline, chapter_id)
    if chapter is None:
        raise ValueError(f"Normalized outline does not contain chapter {chapter_id}.")
    section = _section(chapter, section_id)
    if section is None:
        raise ValueError(f"Normalized outline does not contain section {chapter_id}:{section_id}.")
    scene_start, scene_end = _scene_range(section)
    section["status"] = "frozen"
    registry_section = _find_registry_section(registry, chapter_id, section_id)
    registry_section["status"] = "frozen"
    registry_section["scene_ref_start"] = f"{chapter_id}:{scene_start}"
    registry_section["scene_ref_end"] = f"{chapter_id}:{scene_end}"
    registry["active_section"] = {"chapter_id": chapter_id, "section_id": section_id, "status": "frozen"}
    registry_chapter = _find_registry_chapter(registry, chapter_id)
    registry_chapter["chapter_status"] = "in_progress"
    paths = sw._write_workflow_state(branch_root, outline, registry)
    return {
        "chapter_id": chapter_id,
        "section_id": section_id,
        "scene_start": scene_start,
        "scene_end": scene_end,
        "artifact_paths": {key: relative(branch_root, path) for key, path in paths.items()},
    }


def redraft_scope(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "redraft_scope":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("redraft_scope requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    branch_root = execution_root(root, branch_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    scope = load_recovery_scope(manifest)
    outline = read_json(branch_root / "outline" / "outline.json")
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)

    redrafted: List[Dict[str, Any]] = []
    for chapter_id, section_id in _target_sections(scope, outline):
        prepared = _freeze_branch_section_for_redraft(branch_root, chapter_id, section_id)
        write_request = build_write_section_request(
            workspace,
            book_id,
            chapter_id=chapter_id,
            section_id=section_id,
            branch_id=branch_id,
        )
        result = write_frozen_section(workspace, write_request)
        prepared["write_result_status"] = result.status
        prepared["write_result_id"] = result.result_id
        if result.status not in {"success", "no_op"}:
            advance_recovery_node(workspace, book_id, branch_id, "redraft_scope")
            receipt = write_receipt(
                workspace,
                book_id,
                branch_id,
                action="redraft_scope",
                status=result.status,
                message=f"Redraft paused or failed at section {chapter_id}:{section_id}.",
                details={"redrafted_scopes": redrafted, "failed_scope": prepared, "write_result": result.to_dict()},
            )
            return emit_result(
                workspace,
                book_id,
                request,
                status=result.status,
                message=f"Redraft paused or failed at section {chapter_id}:{section_id}.",
                receipt=receipt,
                before_snapshot=before_snapshot,
                runtime_issue=RuntimeIssue(
                    category="recovery_mode_required",
                    code="redraft_scope_incomplete",
                    severity="high",
                    message=f"Redraft did not complete for section {chapter_id}:{section_id}.",
                    details={"write_result_status": result.status},
                ),
            )
        redrafted.append(prepared)

    if not redrafted:
        advance_recovery_node(workspace, book_id, branch_id, "redraft_scope")
        receipt = write_receipt(
            workspace,
            book_id,
            branch_id,
            action="redraft_scope",
            status="no_op",
            message="No recovery scopes were available to redraft.",
            details={"redrafted_scopes": []},
        )
        return emit_result(
            workspace,
            book_id,
            request,
            status="no_op",
            message="No recovery scopes were available to redraft.",
            receipt=receipt,
            before_snapshot=before_snapshot,
        )

    advance_recovery_node(workspace, book_id, branch_id, "redraft_scope")
    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="redraft_scope",
        status="success",
        message=f"Redrafted {len(redrafted)} recovery scope(s) inside branch {branch_id}.",
        details={"redrafted_scopes": redrafted},
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status="success",
        message=f"Redrafted {len(redrafted)} recovery scope(s) inside branch {branch_id}.",
        receipt=receipt,
        before_snapshot=before_snapshot,
    )
