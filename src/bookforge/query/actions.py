from __future__ import annotations

from typing import List, Optional, Tuple

from bookforge.contracts import BranchManifest, ExecutionOption, MAIN_BRANCH_ID, ScopeSelector

from . import _common
from .scene_phase import get_scene_phase_readiness
from .workspace import current_main_node, get_section_status, get_workspace_status


def _resolved_branch_id(selector: ScopeSelector) -> str:
    return str(selector.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID


def _workflow_initialized(book_root) -> bool:
    outline_root = _common.outline_root(book_root)
    return (outline_root / "outline.json").exists() and (outline_root / "snapshot_registry.json").exists()


def _load_branch_manifest(book_root, branch_id: str) -> Optional[BranchManifest]:
    payload = _common.read_json(_common.branch_manifest_path(book_root, branch_id))
    if not isinstance(payload, dict):
        return None
    try:
        return BranchManifest.from_dict(payload)
    except ValueError:
        return None


def _evaluate_initialize_workflow(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "initialize_section_workflow only supports main-branch execution.", {}
    latest_run_id = _common.latest_outline_run_id(book_root)
    if not latest_run_id:
        return False, "No outline pipeline run is available to initialize workflow state.", {}
    if _workflow_initialized(book_root):
        return False, "Workflow is already initialized; use a narrower section-local action.", {"run_id": latest_run_id}
    return True, None, {"run_id": latest_run_id}


def _evaluate_resume_paused_section(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "resume_paused_section only supports main-branch execution.", {}
    status = get_workspace_status(workspace, book_id, prefer_emitted=prefer_emitted)
    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        return False, "No live main-branch node is available for resume.", {}
    if live_node.workflow_family != "section_write":
        return False, "resume_paused_section requires an active paused section_write node.", {
            "current_workflow_family": live_node.workflow_family,
        }
    if not status.pause_marker:
        return False, "resume_paused_section requires a current pause marker.", {}
    active_section = status.active_section if isinstance(status.active_section, dict) else None
    if not isinstance(active_section, dict):
        return False, "resume_paused_section requires an active frozen section.", {}
    chapter_id = int(active_section.get("chapter_id", 0) or 0)
    section_id = int(active_section.get("section_id", 0) or 0)
    if selector.chapter is not None and selector.chapter != chapter_id:
        return False, "Requested chapter does not match the active paused section.", {
            "active_chapter": chapter_id,
            "active_section": section_id,
        }
    if selector.section is not None and selector.section != section_id:
        return False, "Requested section does not match the active paused section.", {
            "active_chapter": chapter_id,
            "active_section": section_id,
        }
    section_status = get_section_status(workspace, book_id, chapter_id, section_id) or {}
    normalized_section_status = str(section_status.get("status") or "").strip().lower()
    if normalized_section_status != "frozen":
        return False, "resume_paused_section requires the active section to remain frozen.", {
            "section_status": section_status.get("status"),
        }
    return True, None, {"active_chapter": chapter_id, "active_section": section_id}


def _evaluate_freeze_section(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "freeze_section_from_phase03_artifact only supports main-branch execution.", {}
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before a section can be frozen.", {}
    if selector.chapter is None or selector.section is None:
        return False, "freeze_section_from_phase03_artifact requires chapter and section scope.", {}
    section_status = get_section_status(workspace, book_id, selector.chapter, selector.section) or {}
    normalized_status = str(section_status.get("status") or "").strip().lower()
    if normalized_status == "locked":
        return False, "Selected section is already locked.", {"section_status": section_status.get("status")}
    if normalized_status == "frozen":
        return False, "Selected section is already frozen.", {"section_status": section_status.get("status")}
    return True, None, {
        "chapter_id": int(selector.chapter),
        "section_id": int(selector.section),
        "section_status": section_status.get("status"),
    }


def _evaluate_finalize_chapter(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "finalize_chapter_from_locked_sections only supports main-branch execution.", {}
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before a chapter can be finalized.", {}
    if selector.chapter is None:
        return False, "finalize_chapter_from_locked_sections requires chapter scope.", {}
    if selector.section is not None:
        return False, "finalize_chapter_from_locked_sections requires chapter scope without section scope.", {}

    registry = _common.load_registry(book_root)
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    target_chapter = None
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if chapter_id == int(selector.chapter):
            target_chapter = chapter
            break
    if not isinstance(target_chapter, dict):
        return False, f"Chapter {int(selector.chapter)} does not exist in workflow state.", {}

    sections = target_chapter.get("sections") if isinstance(target_chapter.get("sections"), list) else []
    total_sections = 0
    locked_sections = 0
    section_statuses = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        total_sections += 1
        status = str(section.get("status") or "").strip().lower()
        if status == "locked":
            locked_sections += 1
        section_statuses.append(
            {
                "section_id": int(section.get("section_id", 0) or 0),
                "status": status or None,
            }
        )
    if total_sections <= 0:
        return False, f"Chapter {int(selector.chapter)} does not have any workflow sections.", {}
    if locked_sections != total_sections:
        return False, f"Chapter {int(selector.chapter)} is not ready for finalization; all sections must be locked.", {
            "chapter_status": target_chapter.get("chapter_status"),
            "locked_sections": locked_sections,
            "total_sections": total_sections,
            "sections": section_statuses,
        }
    return True, None, {
        "chapter_id": int(selector.chapter),
        "chapter_status": target_chapter.get("chapter_status"),
        "locked_sections": locked_sections,
        "total_sections": total_sections,
    }


def _evaluate_lock_section(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "lock_section_from_written_state only supports main-branch execution.", {}
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before a section can be locked.", {}
    if selector.chapter is None or selector.section is None:
        return False, "lock_section_from_written_state requires chapter and section scope.", {}
    section_status = get_section_status(workspace, book_id, selector.chapter, selector.section) or {}
    normalized_status = str(section_status.get("status") or "").strip().lower()
    if normalized_status == "locked":
        return True, None, {
            "chapter_id": int(selector.chapter),
            "section_id": int(selector.section),
            "section_status": section_status.get("status"),
            "already_locked": True,
        }
    if normalized_status != "frozen":
        return False, "lock_section_from_written_state requires the selected section to be frozen.", {
            "section_status": section_status.get("status"),
        }
    scene_ref_start = str(section_status.get("scene_ref_start") or "").strip()
    scene_ref_end = str(section_status.get("scene_ref_end") or "").strip()
    if ":" not in scene_ref_start or ":" not in scene_ref_end:
        return False, "Selected frozen section does not have a valid scene range.", {
            "scene_ref_start": section_status.get("scene_ref_start"),
            "scene_ref_end": section_status.get("scene_ref_end"),
        }
    _, scene_start_text = scene_ref_start.split(":", 1)
    _, scene_end_text = scene_ref_end.split(":", 1)
    try:
        scene_start = int(scene_start_text)
        scene_end = int(scene_end_text)
    except ValueError:
        return False, "Selected frozen section does not have an integer scene range.", {
            "scene_ref_start": section_status.get("scene_ref_start"),
            "scene_ref_end": section_status.get("scene_ref_end"),
        }
    chapter_dir = _common.book_root(workspace, book_id) / "draft" / "chapters" / f"ch_{int(selector.chapter):03d}"
    missing = []
    for scene_id in range(scene_start, scene_end + 1):
        prose_path = chapter_dir / f"scene_{scene_id:03d}.md"
        meta_path = chapter_dir / f"scene_{scene_id:03d}.meta.json"
        if not prose_path.exists():
            missing.append(prose_path.as_posix())
        if not meta_path.exists():
            missing.append(meta_path.as_posix())
    if missing:
        return False, "Selected frozen section is missing written scene artifacts required for lock.", {
            "chapter_id": int(selector.chapter),
            "section_id": int(selector.section),
            "missing_artifacts": missing,
        }
    return True, None, {
        "chapter_id": int(selector.chapter),
        "section_id": int(selector.section),
        "section_status": section_status.get("status"),
        "scene_ref_start": scene_ref_start,
        "scene_ref_end": scene_ref_end,
    }


def _evaluate_write_section(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "write_frozen_section only supports main-branch execution.", {}
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before a frozen section can be written.", {}
    if selector.chapter is None or selector.section is None:
        return False, "write_frozen_section requires chapter and section scope.", {}

    status = get_workspace_status(workspace, book_id, prefer_emitted=prefer_emitted)
    if status.pause_marker:
        return False, "write_frozen_section refuses when a pause marker is present; use resume_paused_section.", {
            "pause_marker": status.pause_marker,
        }

    active_section = status.active_section if isinstance(status.active_section, dict) else None
    if not isinstance(active_section, dict):
        return False, "write_frozen_section requires an active frozen section.", {}

    active_chapter = int(active_section.get("chapter_id", 0) or 0)
    active_section_id = int(active_section.get("section_id", 0) or 0)
    if int(selector.chapter) != active_chapter or int(selector.section) != active_section_id:
        return False, "Requested scope does not match the active frozen section.", {
            "active_chapter": active_chapter,
            "active_section": active_section_id,
        }

    section_status = get_section_status(workspace, book_id, selector.chapter, selector.section) or {}
    normalized_status = str(section_status.get("status") or "").strip().lower()
    if normalized_status == "locked":
        return False, "Selected section is already locked.", {"section_status": section_status.get("status")}
    if normalized_status != "frozen":
        return False, "write_frozen_section requires the selected section to be frozen.", {
            "section_status": section_status.get("status"),
        }

    scene_ref_start = str(section_status.get("scene_ref_start") or "").strip()
    scene_ref_end = str(section_status.get("scene_ref_end") or "").strip()
    if ":" not in scene_ref_start or ":" not in scene_ref_end:
        return False, "Selected frozen section does not have a valid scene range.", {
            "scene_ref_start": section_status.get("scene_ref_start"),
            "scene_ref_end": section_status.get("scene_ref_end"),
        }
    _, scene_start_text = scene_ref_start.split(":", 1)
    _, scene_end_text = scene_ref_end.split(":", 1)
    try:
        scene_start = int(scene_start_text)
        scene_end = int(scene_end_text)
    except ValueError:
        return False, "Selected frozen section does not have an integer scene range.", {
            "scene_ref_start": section_status.get("scene_ref_start"),
            "scene_ref_end": section_status.get("scene_ref_end"),
        }
    chapter_dir = _common.book_root(workspace, book_id) / "draft" / "chapters" / f"ch_{int(selector.chapter):03d}"
    missing = []
    for scene_id in range(scene_start, scene_end + 1):
        prose_path = chapter_dir / f"scene_{scene_id:03d}.md"
        meta_path = chapter_dir / f"scene_{scene_id:03d}.meta.json"
        if not prose_path.exists():
            missing.append(prose_path.as_posix())
        if not meta_path.exists():
            missing.append(meta_path.as_posix())
    if not missing:
        return False, "Selected frozen section already has complete scene artifacts; use lock_section_from_written_state.", {
            "chapter_id": int(selector.chapter),
            "section_id": int(selector.section),
            "scene_ref_start": scene_ref_start,
            "scene_ref_end": scene_ref_end,
        }
    return True, None, {
        "chapter_id": int(selector.chapter),
        "section_id": int(selector.section),
        "section_status": section_status.get("status"),
        "scene_ref_start": scene_ref_start,
        "scene_ref_end": scene_ref_end,
        "missing_artifact_count": len(missing),
    }


def _evaluate_create_branch(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "create_branch only supports derivation from main in the first extracted lifecycle slice.", {}
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before a derived branch can be created.", {}
    live_node = current_main_node(workspace, book_id, prefer_emitted=False)
    if live_node is None:
        return False, "No live main-branch node is available for branch creation.", {}
    return True, None, {
        "current_workflow_family": live_node.workflow_family,
        "chapter": selector.chapter if selector.chapter is not None else live_node.chapter,
        "section": selector.section if selector.section is not None else live_node.section,
        "prefer_emitted": bool(prefer_emitted),
    }


def _evaluate_create_assembly_branch(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "create_assembly_branch only supports main-branch derivation.", {}
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before an assembly branch can be created.", {}
    fork_group_id = str(selector.fork_group_id or "").strip()
    if not fork_group_id:
        return False, "create_assembly_branch requires fork-group scope.", {}

    sibling_details = []
    for branch_id in _common.list_branch_ids(book_root):
        manifest = _load_branch_manifest(book_root, branch_id)
        if manifest is None or str(manifest.fork_group_id or "").strip() != fork_group_id:
            continue
        sibling_details.append(
            {
                "branch_id": manifest.branch_id,
                "lifecycle_state": manifest.lifecycle_state,
                "merge_operation": manifest.merge_operation,
            }
        )
    if len(sibling_details) < 2:
        return False, f"Fork group {fork_group_id} does not have enough sibling branches for assembly.", {
            "fork_group_id": fork_group_id,
            "sibling_count": len(sibling_details),
            "siblings": sibling_details,
        }
    return True, None, {
        "fork_group_id": fork_group_id,
        "sibling_count": len(sibling_details),
        "siblings": sibling_details,
        "chapter": selector.chapter,
    }


def _evaluate_discard_branch(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    branch_id = _resolved_branch_id(selector)
    if branch_id == MAIN_BRANCH_ID:
        return False, "discard_branch requires a derived branch scope.", {}
    manifest = _load_branch_manifest(book_root, branch_id)
    if manifest is None:
        return False, f"Branch {branch_id} does not exist.", {}
    if manifest.lifecycle_state in {"discard", "promoted"}:
        return False, f"Branch {branch_id} is already in terminal lifecycle state {manifest.lifecycle_state}.", {
            "lifecycle_state": manifest.lifecycle_state,
        }
    return True, None, {
        "branch_id": manifest.branch_id,
        "lifecycle_state": manifest.lifecycle_state,
        "merge_operation": manifest.merge_operation,
        "branch_role": manifest.branch_role,
    }


def _evaluate_promote_branch(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    branch_id = _resolved_branch_id(selector)
    if branch_id == MAIN_BRANCH_ID:
        return False, "promote_branch_to_main requires a derived branch scope.", {}
    manifest = _load_branch_manifest(book_root, branch_id)
    if manifest is None:
        return False, f"Branch {branch_id} does not exist.", {}
    if manifest.lifecycle_state == "promoted":
        return False, f"Branch {branch_id} is already promoted.", {
            "lifecycle_state": manifest.lifecycle_state,
        }
    if manifest.lifecycle_state == "discard":
        return False, f"Branch {branch_id} is already discarded.", {
            "lifecycle_state": manifest.lifecycle_state,
        }
    if manifest.lifecycle_state not in {"promote_ready", "assembled_pending_promotion"}:
        return False, f"Branch {branch_id} is not ready for promotion.", {
            "lifecycle_state": manifest.lifecycle_state,
            "merge_operation": manifest.merge_operation,
            "validation_status": manifest.validation_status,
        }
    if manifest.merge_operation == "assembly" and manifest.validation_status != "passed":
        return False, f"Assembly branch {branch_id} requires passed validation before promotion.", {
            "lifecycle_state": manifest.lifecycle_state,
            "merge_operation": manifest.merge_operation,
            "validation_status": manifest.validation_status,
        }
    return True, None, {
        "branch_id": manifest.branch_id,
        "lifecycle_state": manifest.lifecycle_state,
        "merge_operation": manifest.merge_operation,
        "validation_status": manifest.validation_status,
    }


def _evaluate_record_assembly_validation(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    branch_id = _resolved_branch_id(selector)
    if branch_id == MAIN_BRANCH_ID:
        return False, "record_assembly_validation requires a derived assembly branch scope.", {}
    manifest = _load_branch_manifest(book_root, branch_id)
    if manifest is None:
        return False, f"Branch {branch_id} does not exist.", {}
    if manifest.merge_operation != "assembly":
        return False, f"Branch {branch_id} is not an assembly branch.", {
            "merge_operation": manifest.merge_operation,
            "lifecycle_state": manifest.lifecycle_state,
        }
    if manifest.lifecycle_state not in {"active", "needs_review"}:
        return False, f"Assembly branch {branch_id} is not in a validation-recordable state.", {
            "merge_operation": manifest.merge_operation,
            "lifecycle_state": manifest.lifecycle_state,
            "validation_status": manifest.validation_status,
        }
    return True, None, {
        "branch_id": manifest.branch_id,
        "merge_operation": manifest.merge_operation,
        "lifecycle_state": manifest.lifecycle_state,
        "validation_status": manifest.validation_status,
    }


def _evaluate_write_scene_prose(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "write_scene_prose only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "write_scene_prose"), None)
    if action_row is None:
        return False, "write_scene_prose readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def _evaluate_plan_scene(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "plan_scene only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "plan_scene"), None)
    if action_row is None:
        return False, "plan_scene readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def _evaluate_preflight_scene_state(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "preflight_scene_state only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "preflight_scene_state"), None)
    if action_row is None:
        return False, "preflight_scene_state readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def _evaluate_generate_continuity_pack(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "generate_continuity_pack only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "generate_continuity_pack"), None)
    if action_row is None:
        return False, "generate_continuity_pack readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def _evaluate_state_repair_scene_patch(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "state_repair_scene_patch only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "state_repair_scene_patch"), None)
    if action_row is None:
        return False, "state_repair_scene_patch readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def _evaluate_lint_scene_prose(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "lint_scene_prose only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "lint_scene_prose"), None)
    if action_row is None:
        return False, "lint_scene_prose readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def _evaluate_repair_scene_prose(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "repair_scene_prose only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "repair_scene_prose"), None)
    if action_row is None:
        return False, "repair_scene_prose readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def _evaluate_apply_scene_commit(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "apply_scene_commit only supports main-branch execution.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    action_row = next((item for item in readiness.actions if item.action == "apply_scene_commit"), None)
    if action_row is None:
        return False, "apply_scene_commit readiness is unavailable for the selected scope.", {}
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": readiness.recommended_next_action,
        "mutation_scope": action_row.mutation_scope,
        "missing_prerequisites": list(action_row.missing_prerequisites),
        "available_inputs": list(action_row.available_inputs),
        "existing_outputs": [item.to_dict() for item in action_row.existing_outputs],
    }
    return bool(action_row.legal and action_row.ready), action_row.refusal_reason, details


def list_execution_options(workspace, selector: ScopeSelector, *, prefer_emitted: bool = True) -> List[ExecutionOption]:
    book_id = selector.book_id
    resolved_branch_id = _resolved_branch_id(selector)
    init_allowed, init_refusal, init_details = _evaluate_initialize_workflow(workspace, book_id, selector)
    create_branch_allowed, create_branch_refusal, create_branch_details = _evaluate_create_branch(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    create_assembly_allowed, create_assembly_refusal, create_assembly_details = _evaluate_create_assembly_branch(
        workspace,
        book_id,
        selector,
    )
    finalize_allowed, finalize_refusal, finalize_details = _evaluate_finalize_chapter(
        workspace,
        book_id,
        selector,
    )
    write_allowed, write_refusal, write_details = _evaluate_write_section(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    lock_allowed, lock_refusal, lock_details = _evaluate_lock_section(
        workspace,
        book_id,
        selector,
    )
    discard_branch_allowed, discard_branch_refusal, discard_branch_details = _evaluate_discard_branch(
        workspace,
        book_id,
        selector,
    )
    promote_branch_allowed, promote_branch_refusal, promote_branch_details = _evaluate_promote_branch(
        workspace,
        book_id,
        selector,
    )
    validate_assembly_allowed, validate_assembly_refusal, validate_assembly_details = _evaluate_record_assembly_validation(
        workspace,
        book_id,
        selector,
    )
    plan_scene_allowed, plan_scene_refusal, plan_scene_details = _evaluate_plan_scene(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    preflight_allowed, preflight_refusal, preflight_details = _evaluate_preflight_scene_state(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    continuity_allowed, continuity_refusal, continuity_details = _evaluate_generate_continuity_pack(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    write_scene_allowed, write_scene_refusal, write_scene_details = _evaluate_write_scene_prose(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    state_repair_allowed, state_repair_refusal, state_repair_details = _evaluate_state_repair_scene_patch(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    lint_scene_allowed, lint_scene_refusal, lint_scene_details = _evaluate_lint_scene_prose(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    repair_scene_allowed, repair_scene_refusal, repair_scene_details = _evaluate_repair_scene_prose(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    apply_scene_commit_allowed, apply_scene_commit_refusal, apply_scene_commit_details = _evaluate_apply_scene_commit(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    freeze_allowed, freeze_refusal, freeze_details = _evaluate_freeze_section(workspace, book_id, selector)
    resume_allowed, resume_refusal, resume_details = _evaluate_resume_paused_section(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    options = [
        ExecutionOption(
            action="initialize_section_workflow",
            summary="Initialize canonical workflow state from an immutable outline run.",
            branch_policy="main_only",
            workflow_family="section_local_outline",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=init_allowed,
            selector_requirements=["book_id"],
            refusal_reason=init_refusal,
            details=init_details,
        ),
        ExecutionOption(
            action="create_branch",
            summary="Create a derived branch from the current main-branch scope for isolated rerun or recovery work.",
            branch_policy="main_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=create_branch_allowed,
            selector_requirements=["book_id"],
            refusal_reason=create_branch_refusal,
            details=create_branch_details,
        ),
        ExecutionOption(
            action="finalize_chapter_from_locked_sections",
            summary="Run pairwise seam repair and chapter finalization for a locked chapter on main.",
            branch_policy="main_only",
            workflow_family="section_local_outline",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=finalize_allowed,
            selector_requirements=["book_id", "chapter"],
            refusal_reason=finalize_refusal,
            details=finalize_details,
        ),
        ExecutionOption(
            action="lock_section_from_written_state",
            summary="Lock one frozen section after all required scene prose and meta artifacts exist.",
            branch_policy="main_only",
            workflow_family="section_local_outline",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=lock_allowed,
            selector_requirements=["book_id", "chapter", "section"],
            refusal_reason=lock_refusal,
            details=lock_details,
        ),
        ExecutionOption(
            action="write_frozen_section",
            summary="Run the section_write loop for the active frozen section through its terminal scene without locking it.",
            branch_policy="main_only",
            workflow_family="section_write",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=write_allowed,
            selector_requirements=["book_id", "chapter", "section"],
            refusal_reason=write_refusal,
            details=write_details,
        ),
        ExecutionOption(
            action="create_assembly_branch",
            summary="Create an assembly branch from an existing fork group so sibling results can be validated before promotion.",
            branch_policy="main_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=create_assembly_allowed,
            selector_requirements=["book_id", "fork_group_id"],
            refusal_reason=create_assembly_refusal,
            details=create_assembly_details,
        ),
        ExecutionOption(
            action="discard_branch",
            summary="Discard a derived branch without mutating canonical state.",
            branch_policy="derived_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=discard_branch_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=discard_branch_refusal,
            details=discard_branch_details,
        ),
        ExecutionOption(
            action="promote_branch_to_main",
            summary="Promote a promotion-ready derived branch back onto canonical main state.",
            branch_policy="derived_only",
            workflow_family=None,
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=promote_branch_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=promote_branch_refusal,
            details=promote_branch_details,
        ),
        ExecutionOption(
            action="record_assembly_validation",
            summary="Record pass/fail validation on an assembly branch before promotion eligibility is re-evaluated.",
            branch_policy="derived_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=validate_assembly_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=validate_assembly_refusal,
            details=validate_assembly_details,
        ),
        ExecutionOption(
            action="freeze_section_from_phase03_artifact",
            summary="Freeze one section into canonical outline state from the declared source run.",
            branch_policy="main_only",
            workflow_family="section_local_outline",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=freeze_allowed,
            selector_requirements=["book_id", "chapter", "section"],
            refusal_reason=freeze_refusal,
            details=freeze_details,
        ),
        ExecutionOption(
            action="resume_paused_section",
            summary="Resume the currently paused main-branch section_write node and lock the section if it exits cleanly.",
            branch_policy="main_only",
            workflow_family="section_write",
            mutates_canonical_state=True,
            requires_expected_node=True,
            allowed=resume_allowed,
            selector_requirements=["book_id"],
            refusal_reason=resume_refusal,
            details=resume_details,
        ),
    ] if resolved_branch_id == MAIN_BRANCH_ID else [
        ExecutionOption(
            action="initialize_section_workflow",
            summary="Initialize canonical workflow state from an immutable outline run.",
            branch_policy="main_only",
            workflow_family="section_local_outline",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=init_allowed,
            selector_requirements=["book_id"],
            refusal_reason=init_refusal,
            details=init_details,
        ),
        ExecutionOption(
            action="create_branch",
            summary="Create a derived branch from the current main-branch scope for isolated rerun or recovery work.",
            branch_policy="main_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=create_branch_allowed,
            selector_requirements=["book_id"],
            refusal_reason=create_branch_refusal,
            details=create_branch_details,
        ),
        ExecutionOption(
            action="create_assembly_branch",
            summary="Create an assembly branch from an existing fork group so sibling results can be validated before promotion.",
            branch_policy="main_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=create_assembly_allowed,
            selector_requirements=["book_id", "fork_group_id"],
            refusal_reason=create_assembly_refusal,
            details=create_assembly_details,
        ),
        ExecutionOption(
            action="discard_branch",
            summary="Discard a derived branch without mutating canonical state.",
            branch_policy="derived_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=discard_branch_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=discard_branch_refusal,
            details=discard_branch_details,
        ),
        ExecutionOption(
            action="promote_branch_to_main",
            summary="Promote a promotion-ready derived branch back onto canonical main state.",
            branch_policy="derived_only",
            workflow_family=None,
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=promote_branch_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=promote_branch_refusal,
            details=promote_branch_details,
        ),
        ExecutionOption(
            action="record_assembly_validation",
            summary="Record pass/fail validation on an assembly branch before promotion eligibility is re-evaluated.",
            branch_policy="derived_only",
            workflow_family=None,
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=validate_assembly_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=validate_assembly_refusal,
            details=validate_assembly_details,
        ),
    ]
    if resolved_branch_id == MAIN_BRANCH_ID and selector.scene is not None:
        options.append(
            ExecutionOption(
                action="plan_scene",
                summary="Generate a provisional scene card for the active cursor scene without auto-running downstream phases.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=plan_scene_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=plan_scene_refusal,
                details=plan_scene_details,
            )
        )
        options.append(
            ExecutionOption(
                action="preflight_scene_state",
                summary="Generate a provisional preflight state patch for the active cursor scene without applying it.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=preflight_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=preflight_refusal,
                details=preflight_details,
            )
        )
        options.append(
            ExecutionOption(
                action="generate_continuity_pack",
                summary="Generate a derived continuity pack for the active cursor scene without auto-running prose or repair.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=continuity_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=continuity_refusal,
                details=continuity_details,
            )
        )
        options.append(
            ExecutionOption(
                action="write_scene_prose",
                summary="Generate provisional prose for the active cursor scene without auto-running lint, repair, or commit.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=write_scene_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=write_scene_refusal,
                details=write_scene_details,
            )
        )
        options.append(
            ExecutionOption(
                action="state_repair_scene_patch",
                summary="Generate a provisional corrected state patch for the active cursor scene without linting, repairing prose, or committing.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=state_repair_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=state_repair_refusal,
                details=state_repair_details,
            )
        )
        options.append(
            ExecutionOption(
                action="lint_scene_prose",
                summary="Generate a provisional lint report for the active cursor scene without repairing prose or committing.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=lint_scene_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=lint_scene_refusal,
                details=lint_scene_details,
            )
        )
        options.append(
            ExecutionOption(
                action="repair_scene_prose",
                summary="Generate provisional repaired prose and patch artifacts for the active cursor scene without rerunning state repair, lint, or commit.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=repair_scene_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=repair_scene_refusal,
                details=repair_scene_details,
            )
        )
        options.append(
            ExecutionOption(
                action="apply_scene_commit",
                summary="Commit the active cursor scene's latest passing provisional baseline into canonical state and authoritative scene artifacts.",
                branch_policy="main_only",
                workflow_family="section_write",
                mutates_canonical_state=True,
                requires_expected_node=True,
                allowed=apply_scene_commit_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=apply_scene_commit_refusal,
                details=apply_scene_commit_details,
            )
        )
    return options


def legal_next_actions(workspace, selector: ScopeSelector, *, prefer_emitted: bool = True) -> List[ExecutionOption]:
    return [option for option in list_execution_options(workspace, selector, prefer_emitted=prefer_emitted) if option.allowed]
