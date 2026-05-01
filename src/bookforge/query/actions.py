from __future__ import annotations

from typing import List, Optional, Tuple

from bookforge.contracts import BranchManifest, ExecutionOption, MAIN_BRANCH_ID, ScopeSelector
from bookforge.pipeline.scene_phase_artifacts import load_scene_phase_artifact_state

from . import _common
from .appearance import list_appearance_projection_views
from .book_intent import list_book_intents
from .outline_lineage import get_outline_lineage_audit
from .recovery import get_recovery_branch_health, get_recovery_manifest, get_recovery_semantic_review_readiness
from .scene_phase import get_scene_phase_readiness
from .setting import get_scene_setting_projection
from .visual import get_visual_asset_index
from .workspace import current_execution_node, current_main_node, get_section_status, get_workspace_status, get_workspace_status_for_branch

AUTHOR_LIBRARY_SCOPE_ID = "__author_library__"
BOOK_INTENT_LIBRARY_SCOPE_ID = "__book_intents__"


def _resolved_branch_id(selector: ScopeSelector) -> str:
    return str(selector.branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID


def _is_author_assets_selector(selector: ScopeSelector) -> bool:
    return selector.book_id == AUTHOR_LIBRARY_SCOPE_ID or selector.workflow_family == "author_assets"


def _is_book_intent_selector(selector: ScopeSelector) -> bool:
    return selector.book_id == BOOK_INTENT_LIBRARY_SCOPE_ID or selector.workflow_family == "book_intent"


def _author_asset_options() -> List[ExecutionOption]:
    return [
        ExecutionOption(
            action="create_author",
            summary="Create a versioned BookForge author persona from influences or an author brief.",
            branch_policy="main_only",
            workflow_family="author_assets",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=True,
            selector_requirements=["book_id", "details.influences_or_prompt"],
            details={
                "library_scope_id": AUTHOR_LIBRARY_SCOPE_ID,
                "artifact_status_after_success": "authoritative",
                "versioned": True,
            },
        ),
        ExecutionOption(
            action="refine_author",
            summary="Refine an existing BookForge author persona into a new version without overwriting prior versions.",
            branch_policy="main_only",
            workflow_family="author_assets",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=True,
            selector_requirements=["book_id", "details.author_ref", "details.instructions_or_prompt"],
            details={
                "library_scope_id": AUTHOR_LIBRARY_SCOPE_ID,
                "artifact_status_after_success": "authoritative",
                "versioned": True,
                "overwrite_behavior": "creates_new_version",
            },
        ),
    ]


def _book_intent_options(workspace) -> List[ExecutionOption]:
    intents = list_book_intents(workspace)
    draft_count = sum(1 for record in intents if record.intent.status == "draft")
    approved_count = sum(1 for record in intents if record.intent.status == "approved")
    created_count = sum(1 for record in intents if record.intent.status == "created")
    common_details = {
        "library_scope_id": BOOK_INTENT_LIBRARY_SCOPE_ID,
        "intent_count": len(intents),
        "draft_count": draft_count,
        "approved_count": approved_count,
        "created_count": created_count,
    }
    return [
        ExecutionOption(
            action="draft_book_intent",
            summary="Create a provisional BookIntent from an author-only seed, title, author, genre, and synopsis fields.",
            branch_policy="main_only",
            workflow_family="book_intent",
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=True,
            selector_requirements=["book_id", "details.title", "details.author_ref", "details.genre", "details.seed_text_or_seed_file"],
            details={
                **common_details,
                "artifact_status_after_success": "provisional",
                "canonical_book_created": False,
            },
        ),
        ExecutionOption(
            action="approve_book_intent",
            summary="Approve a drafted BookIntent so it can be used to create a canonical BookForge book workspace.",
            branch_policy="main_only",
            workflow_family="book_intent",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=draft_count > 0,
            selector_requirements=["book_id", "details.intent_ref"],
            refusal_reason=None if draft_count > 0 else "No draft BookIntent is available to approve.",
            details={
                **common_details,
                "artifact_status_after_success": "authoritative",
                "approval_required": True,
            },
        ),
        ExecutionOption(
            action="create_book_from_intent",
            summary="Create a canonical BookForge book workspace from an approved BookIntent.",
            branch_policy="main_only",
            workflow_family="book_intent",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=approved_count > 0,
            selector_requirements=["book_id", "details.intent_ref"],
            refusal_reason=None if approved_count > 0 else "No approved BookIntent is available to create a book from.",
            details={
                **common_details,
                "artifact_status_after_success": "authoritative",
                "canonical_transition": "author_only_seed_to_book_scope",
            },
        ),
    ]


_LINEAGE_BLOCKED_MAIN_ACTIONS = {
    "draft_starter_outline_from_intent",
    "freeze_section_from_phase03_artifact",
    "write_frozen_section",
    "lock_section_from_written_state",
    "finalize_chapter_from_locked_sections",
    "resume_paused_section",
    "plan_scene",
    "preflight_scene_state",
    "generate_continuity_pack",
    "write_scene_prose",
    "state_repair_scene_patch",
    "lint_scene_prose",
    "repair_scene_prose",
    "apply_scene_commit",
    "continue_scene",
    "align_scene_pair_seam",
    "plan_bridge_scene_insertion",
    "apply_bridge_scene_insertion",
    "refresh_character_appearance_projection",
    "draft_scene_setting_projection",
    "extract_scene_setting_from_prose",
}


def _lineage_blocked_option(option: ExecutionOption, details: dict) -> ExecutionOption:
    merged_details = dict(option.details)
    merged_details.update(details)
    return ExecutionOption(
        action=option.action,
        summary=option.summary,
        branch_policy=option.branch_policy,
        workflow_family=option.workflow_family,
        mutates_canonical_state=option.mutates_canonical_state,
        requires_expected_node=option.requires_expected_node,
        allowed=False,
        selector_requirements=list(option.selector_requirements),
        refusal_reason="Book has outline lineage chimera risk; inspect outline lineage and create a recovery branch before mutating main.",
        details=merged_details,
    )


def _apply_lineage_safety_gate(workspace, book_id: str, branch_id: str, options: List[ExecutionOption]) -> List[ExecutionOption]:
    if branch_id != MAIN_BRANCH_ID:
        return options
    audit = get_outline_lineage_audit(workspace, book_id, branch_id=branch_id)
    if audit.status != "chimera_risk":
        return options
    details = {
        "integrity_status": audit.status,
        "affected_scopes": [
            {"chapter_id": row.chapter_id, "section_id": row.section_id, "class": row.suspected_contamination_class}
            for row in audit.affected_sections[:10]
        ],
        "affected_scope_count": len(audit.affected_sections),
        "first_technical_divergence": audit.first_technical_divergence,
        "first_visible_story_divergence": audit.first_visible_story_divergence,
        "recommended_safe_next_action": "outline_lineage_audit",
    }
    gated: List[ExecutionOption] = []
    for option in options:
        if option.action in _LINEAGE_BLOCKED_MAIN_ACTIONS:
            gated.append(_lineage_blocked_option(option, details))
        else:
            gated.append(option)
    return gated


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


def _execution_book_root(book_root, branch_id: str):
    if str(branch_id or MAIN_BRANCH_ID).strip() == MAIN_BRANCH_ID:
        return book_root
    from bookforge.supervision import paths as supervision_paths

    return supervision_paths.branch_snapshot_root(book_root, branch_id)


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


def _evaluate_draft_starter_outline_from_intent(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "draft_starter_outline_from_intent only supports main-branch execution.", {}
    if not book_root.exists():
        return False, f"Book workspace not found: {book_id}", {}
    intent = _common.read_json(book_root / "book_intent.json") or {}
    if not intent:
        return False, "draft_starter_outline_from_intent requires a canonical book created from a BookIntent.", {}
    if str(intent.get("status") or "").strip() != "created":
        return False, "draft_starter_outline_from_intent requires a created BookIntent.", {
            "book_intent_status": intent.get("status"),
        }
    latest_run_id = _common.latest_outline_run_id(book_root)
    if latest_run_id:
        return False, "An outline pipeline run already exists for this book.", {
            "run_id": latest_run_id,
            "next_recommended_action": "initialize_section_workflow",
        }
    if _workflow_initialized(book_root):
        return False, "Workflow is already initialized; use narrower workflow actions.", {}
    book = _common.read_json(book_root / "book.json") or {}
    targets = book.get("targets") if isinstance(book.get("targets"), dict) else {}
    return True, None, {
        "book_intent_id": intent.get("intent_id"),
        "workflow_family": "thin_outline",
        "starter_outline": True,
        "provider_used": True,
        "deep_outline_pipeline": False,
        "target_chapters": targets.get("chapters"),
        "next_recommended_action": "initialize_section_workflow",
        "produced_artifacts": [
            "outline_spine_v1.json",
            "outline_sections_v1.json",
            "outline_final_v1_1.json",
            "outline_pipeline_report.json",
        ],
        "produced_artifact_statuses": ["authoritative", "diagnostic"],
    }


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
    branch_id = _resolved_branch_id(selector)
    execution_root = _execution_book_root(book_root, branch_id)
    if branch_id != MAIN_BRANCH_ID:
        manifest = _load_branch_manifest(book_root, branch_id)
        if manifest is None:
            return False, f"Branch {branch_id} does not exist.", {"branch_id": branch_id}
        if manifest.lifecycle_state in {"discard", "promoted"}:
            return False, f"Branch {branch_id} is already in terminal lifecycle state {manifest.lifecycle_state}.", {
                "branch_id": branch_id,
                "lifecycle_state": manifest.lifecycle_state,
            }
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before a chapter can be finalized.", {}
    if selector.chapter is None:
        return False, "finalize_chapter_from_locked_sections requires chapter scope.", {}
    if selector.section is not None:
        return False, "finalize_chapter_from_locked_sections requires chapter scope without section scope.", {}

    registry = _common.load_registry(execution_root)
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
        "branch_id": branch_id,
        "mutation_scope": "canonical" if branch_id == MAIN_BRANCH_ID else "branch_authoritative",
    }


def _evaluate_lock_section(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    branch_id = _resolved_branch_id(selector)
    execution_root = _execution_book_root(book_root, branch_id)
    if branch_id != MAIN_BRANCH_ID:
        manifest = _load_branch_manifest(book_root, branch_id)
        if manifest is None:
            return False, f"Branch {branch_id} does not exist.", {"branch_id": branch_id}
        if manifest.lifecycle_state in {"discard", "promoted"}:
            return False, f"Branch {branch_id} is already in terminal lifecycle state {manifest.lifecycle_state}.", {
                "branch_id": branch_id,
                "lifecycle_state": manifest.lifecycle_state,
            }
    if not _workflow_initialized(book_root):
        return False, "Workflow must be initialized before a section can be locked.", {}
    if selector.chapter is None or selector.section is None:
        return False, "lock_section_from_written_state requires chapter and section scope.", {}
    section_status = get_section_status(workspace, book_id, selector.chapter, selector.section, branch_id=branch_id) or {}
    normalized_status = str(section_status.get("status") or "").strip().lower()
    if normalized_status == "locked":
        return True, None, {
            "chapter_id": int(selector.chapter),
            "section_id": int(selector.section),
            "section_status": section_status.get("status"),
            "already_locked": True,
            "branch_id": branch_id,
            "mutation_scope": "canonical" if branch_id == MAIN_BRANCH_ID else "branch_authoritative",
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
    chapter_dir = execution_root / "draft" / "chapters" / f"ch_{int(selector.chapter):03d}"
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
        "branch_id": branch_id,
        "mutation_scope": "canonical" if branch_id == MAIN_BRANCH_ID else "branch_authoritative",
    }


def _evaluate_write_section(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    branch_id = _resolved_branch_id(selector)
    execution_root = _execution_book_root(book_root, branch_id)
    if branch_id != MAIN_BRANCH_ID:
        manifest = _load_branch_manifest(book_root, branch_id)
        if manifest is None:
            return False, f"Branch {branch_id} does not exist.", {}
        if manifest.lifecycle_state in {"discard", "promoted"}:
            return False, f"Branch {branch_id} is already in terminal lifecycle state {manifest.lifecycle_state}.", {
                "branch_id": branch_id,
                "lifecycle_state": manifest.lifecycle_state,
            }
    if not _workflow_initialized(execution_root):
        return False, "Workflow must be initialized before a frozen section can be written.", {}
    if selector.chapter is None or selector.section is None:
        return False, "write_frozen_section requires chapter and section scope.", {}

    status = get_workspace_status_for_branch(workspace, book_id, branch_id=branch_id, prefer_emitted=prefer_emitted)
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

    section_status = get_section_status(workspace, book_id, selector.chapter, selector.section, branch_id=branch_id) or {}
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
    chapter_dir = execution_root / "draft" / "chapters" / f"ch_{int(selector.chapter):03d}"
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
        "scene_start": scene_start,
        "scene_end": scene_end,
        "scene_count": scene_end - scene_start + 1,
        "missing_artifact_count": len(missing),
        "branch_id": branch_id,
        "mutation_scope": "canonical" if branch_id == MAIN_BRANCH_ID else "branch_authoritative",
        "macro_kind": "section_write_range",
        "broad_macro": True,
        "not_for_single_scene_requests": True,
        "preferred_single_scene_action": "continue_scene",
        "step_count_per_call": "all missing scenes in the selected frozen section",
        "runs_until": "selected frozen section terminal scene",
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


def _evaluate_plan_visual_asset(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if not book_root.exists():
        return False, f"Book workspace not found: {book_id}", {}
    branch_id = _resolved_branch_id(selector)
    if branch_id != MAIN_BRANCH_ID and _load_branch_manifest(book_root, branch_id) is None:
        return False, f"Branch {branch_id} does not exist.", {"branch_id": branch_id}
    return True, None, {
        "branch_id": branch_id,
        "workflow_family": "visual_assets",
        "requires_prompt_text": True,
        "readiness_source": "visual_action_readiness",
        "default_provider_model": "nano-banana",
        "supported_purposes": [
            "background_layer",
            "character_reference",
            "character_in_scene",
            "scene_illustration",
            "style_transfer",
        ],
        "produced_artifacts": ["visual_prompt_plan"],
        "produced_artifact_statuses": ["provisional"],
    }


def _evaluate_generate_visual_asset(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    book_root = _common.book_root(workspace, book_id)
    if not book_root.exists():
        return False, f"Book workspace not found: {book_id}", {}
    branch_id = _resolved_branch_id(selector)
    if branch_id != MAIN_BRANCH_ID and _load_branch_manifest(book_root, branch_id) is None:
        return False, f"Branch {branch_id} does not exist.", {"branch_id": branch_id}
    try:
        visual_index = get_visual_asset_index(workspace, book_id, branch_id=branch_id)
    except Exception as exc:
        return False, f"Visual asset index is unavailable: {exc}", {"branch_id": branch_id}
    prompt_plans = [item.to_dict() for item in visual_index.prompt_plans]
    details = {
        "branch_id": branch_id,
        "workflow_family": "visual_assets",
        "requires_prompt_plan_path": True,
        "requires_allow_spend": True,
        "approval_required": True,
        "readiness_source": "visual_action_readiness",
        "prompt_plan_count": len(prompt_plans),
        "available_prompt_plans": prompt_plans[:20],
        "produced_artifacts": ["visual_image", "visual_asset_manifest"],
        "produced_artifact_statuses": ["provisional", "diagnostic"],
        "existing_asset_count": len(visual_index.assets),
    }
    if not prompt_plans:
        return False, "generate_visual_asset requires an existing visual prompt plan.", details
    return True, None, details


def _evaluate_create_recovery_branch(workspace, book_id: str, selector: ScopeSelector) -> Tuple[bool, Optional[str], dict]:
    if _resolved_branch_id(selector) != MAIN_BRANCH_ID:
        return False, "create_recovery_branch only derives from main.", {}
    audit = get_outline_lineage_audit(workspace, book_id)
    affected = [{"chapter_id": row.chapter_id, "section_id": row.section_id} for row in audit.affected_sections]
    if not affected and selector.workflow_family == "recovery_import" and selector.chapter is not None:
        scoped = {"chapter_id": int(selector.chapter)}
        if selector.section is not None:
            scoped["section_id"] = int(selector.section)
        if selector.scene is not None:
            scoped["scene_id"] = int(selector.scene)
        affected = [scoped]
    if not affected:
        return False, "create_recovery_branch requires affected lineage scopes or an explicit selector scope.", {
            "integrity_status": audit.status,
        }
    return True, None, {
        "integrity_status": audit.status,
        "affected_scopes": affected,
        "affected_scope_count": len(affected),
        "requires_anchor": True,
        "approval_required": True,
        "approval_reasons": ["recovery anchor selection"] + (["broad recovery radius"] if len(affected) > 1 else []),
        "broad_recovery_radius": len(affected) > 1,
    }


def _recovery_receipt_actions(workspace, book_id: str, branch_id: str) -> set[str]:
    try:
        health = get_recovery_branch_health(workspace, book_id, branch_id=branch_id)
    except Exception:
        return set()
    return {receipt.action for receipt in health.receipts}


def _recovery_scope_count(manifest: dict) -> int:
    scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
    return len(scope.get("affected_scopes") or [])


def _recovery_approval_metadata(action: str, manifest: dict) -> dict:
    scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
    scopes = [item for item in (scope.get("affected_scopes") or []) if isinstance(item, dict)]
    scope_count = len(scopes)
    broad_scope = scope_count > 1 or any("section_id" not in item for item in scopes)
    reasons = []
    action_reasons = {
        "create_recovery_branch": "recovery anchor selection",
        "quarantine_artifacts": "destructive cleanup/quarantine",
        "invalidate_scope_outputs": "scope output invalidation",
        "rebuild_state_scope": "state/projection rebuild",
        "redraft_scope": "scope redraft",
        "promote_recovery_branch": "promotion to main",
    }
    action_reason = action_reasons.get(action)
    if action_reason:
        reasons.append(action_reason)
    if broad_scope:
        reasons.append("broad recovery radius")
    return {
        "approval_required": bool(reasons),
        "approval_reasons": reasons,
        "broad_recovery_radius": bool(broad_scope),
        "affected_scope_count": scope_count,
    }


def _evaluate_recovery_branch_action(workspace, book_id: str, selector: ScopeSelector, action: str) -> Tuple[bool, Optional[str], dict]:
    branch_id = _resolved_branch_id(selector)
    if branch_id == MAIN_BRANCH_ID:
        return False, f"{action} requires a derived recovery branch.", {}
    manifest = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    if not manifest:
        return False, f"{action} requires a recovery branch manifest.", {"branch_id": branch_id}
    receipt_actions = _recovery_receipt_actions(workspace, book_id, branch_id)
    details = {
        "branch_id": branch_id,
        "receipt_actions": sorted(receipt_actions),
        "anchor": manifest.get("anchor"),
        "scope": manifest.get("scope"),
        **_recovery_approval_metadata(action, manifest),
    }
    if action == "quarantine_artifacts":
        if action in receipt_actions:
            return False, "quarantine_artifacts already has a receipt for this branch.", details
        return True, None, details
    if action == "normalize_outline_scope":
        if action in receipt_actions:
            return False, "normalize_outline_scope already has a receipt for this branch.", details
        return True, None, details
    if action == "invalidate_scope_outputs":
        if "normalize_outline_scope" not in receipt_actions:
            return False, "invalidate_scope_outputs requires normalized outline scope first.", details
        if action in receipt_actions:
            return False, "invalidate_scope_outputs already has a receipt for this branch.", details
        return True, None, details
    if action == "rebuild_state_scope":
        if "normalize_outline_scope" not in receipt_actions:
            return False, "rebuild_state_scope requires normalized outline scope first.", details
        if "invalidate_scope_outputs" not in receipt_actions:
            return False, "rebuild_state_scope requires invalidated scope outputs first.", details
        if action in receipt_actions:
            return False, "rebuild_state_scope already has a receipt for this branch.", details
        return True, None, details
    if action == "redraft_scope":
        if "rebuild_state_scope" not in receipt_actions:
            return False, "redraft_scope requires rebuilt state scope first.", details
        if action in receipt_actions:
            return False, "redraft_scope already has a receipt for this branch.", details
        return True, None, details
    if action == "validate_recovery_branch":
        if "quarantine_artifacts" not in receipt_actions:
            return False, "validate_recovery_branch requires quarantine_artifacts first.", details
        if "normalize_outline_scope" not in receipt_actions:
            return False, "validate_recovery_branch requires normalized outline scope first.", details
        if "invalidate_scope_outputs" not in receipt_actions:
            return False, "validate_recovery_branch requires invalidated scope outputs first.", details
        if "rebuild_state_scope" not in receipt_actions:
            return False, "validate_recovery_branch requires rebuilt state scope first.", details
        if "redraft_scope" not in receipt_actions:
            return False, "validate_recovery_branch requires redrafted scope first.", details
        return True, None, details
    if action == "review_recovery_semantics":
        readiness = get_recovery_semantic_review_readiness(workspace, book_id, branch_id=branch_id)
        review_details = {
            **details,
            "semantic_review_ready": bool(readiness.get("ready")),
            "semantic_review_status": readiness.get("status"),
            "semantic_validation_status": readiness.get("semantic_validation_status"),
            "present_outputs": readiness.get("present_outputs", []),
            "mutation_scope": readiness.get("mutation_scope"),
        }
        if not readiness.get("ready"):
            blockers = readiness.get("blockers") or []
            return False, "; ".join(str(item) for item in blockers) or "review_recovery_semantics is not ready.", review_details
        return True, None, review_details
    if action == "review_downstream_dependencies":
        readiness = get_recovery_semantic_review_readiness(workspace, book_id, branch_id=branch_id)
        scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
        downstream_scopes = [dict(item) for item in scope.get("downstream_scopes", []) if isinstance(item, dict)]
        review_details = {
            **details,
            "semantic_review_ready": bool(readiness.get("ready")),
            "semantic_review_status": readiness.get("status"),
            "downstream_scopes": downstream_scopes,
            "downstream_scope_count": len(downstream_scopes),
            "mutation_scope": readiness.get("mutation_scope"),
        }
        if not readiness.get("ready"):
            blockers = readiness.get("blockers") or []
            return False, "; ".join(str(item) for item in blockers) or "review_downstream_dependencies is not ready.", review_details
        return True, None, review_details
    if action == "promote_recovery_branch":
        health = get_recovery_branch_health(workspace, book_id, branch_id=branch_id)
        if health.status != "healthy":
            return False, "promote_recovery_branch requires healthy recovery branch validation.", {
                **details,
                "health_status": health.status,
                "blockers": health.blockers,
                "warnings": health.warnings,
            }
        return True, None, {**details, "health_status": health.status}
    return False, f"Unknown recovery action: {action}", details


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
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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


def _evaluate_refresh_character_appearance_projection(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    resolved_branch_id = _resolved_branch_id(selector)
    if selector.chapter is None or selector.scene is None:
        return False, "refresh_character_appearance_projection requires chapter and scene scope.", {}
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    if node is None:
        return False, f"No current node is available for branch {resolved_branch_id}.", {}
    views = list_appearance_projection_views(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=selector.chapter,
        section_id=selector.section,
        scene_id=selector.scene,
        prefer_emitted=prefer_emitted,
    )
    return True, None, {
        "chapter_id": selector.chapter,
        "section_id": selector.section,
        "scene_id": selector.scene,
        "mutation_scope": "derived_projection",
        "character_count": len(views),
        "missing_count": sum(1 for view in views if view.appearance_status == "missing"),
        "stale_count": sum(1 for view in views if view.appearance_status == "stale"),
        "artifact_status": "derived",
        "statuses": [
            {
                "character_id": view.character_id,
                "appearance_status": view.appearance_status,
                "artifact_status": view.artifact_status,
                "staleness_reason": view.staleness_reason,
            }
            for view in views
        ],
    }


def _current_or_committed_prose_path(book_root, chapter: int, scene: int):
    artifact_state = load_scene_phase_artifact_state(book_root, int(chapter), int(scene))
    if artifact_state.current_prose_path is not None:
        return artifact_state.current_prose_path
    committed = book_root / "draft" / "chapters" / f"ch_{int(chapter):03d}" / f"scene_{int(scene):03d}.md"
    return committed if committed.exists() else None


def _evaluate_draft_scene_setting_projection(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    resolved_branch_id = _resolved_branch_id(selector)
    if selector.chapter is None or selector.scene is None:
        return False, "draft_scene_setting_projection requires chapter and scene scope.", {}
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    if node is None:
        return False, f"No current node is available for branch {resolved_branch_id}.", {}
    setting = get_scene_setting_projection(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=int(selector.chapter),
        section_id=selector.section,
        scene_id=int(selector.scene),
        prefer_emitted=prefer_emitted,
    )
    return True, None, {
        "chapter_id": selector.chapter,
        "section_id": selector.section,
        "scene_id": selector.scene,
        "mutation_scope": "provisional_projection",
        "current_setting_status": setting.setting_status,
        "current_source_mode": setting.source_mode,
        "current_artifact_status": setting.artifact_status,
        "artifact_status": "provisional",
    }


def _evaluate_extract_scene_setting_from_prose(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    resolved_branch_id = _resolved_branch_id(selector)
    if selector.chapter is None or selector.scene is None:
        return False, "extract_scene_setting_from_prose requires chapter and scene scope.", {}
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    if node is None:
        return False, f"No current node is available for branch {resolved_branch_id}.", {}
    book_root = _execution_book_root(_common.book_root(workspace, book_id), resolved_branch_id)
    prose_path = _current_or_committed_prose_path(book_root, int(selector.chapter), int(selector.scene))
    if prose_path is None:
        return False, "extract_scene_setting_from_prose requires existing scene prose.", {
            "chapter_id": selector.chapter,
            "section_id": selector.section,
            "scene_id": selector.scene,
            "mutation_scope": "derived_projection",
            "missing_prerequisites": ["scene_prose"],
        }
    return True, None, {
        "chapter_id": selector.chapter,
        "section_id": selector.section,
        "scene_id": selector.scene,
        "mutation_scope": "derived_projection",
        "available_inputs": ["scene_prose"],
        "source_prose_path": prose_path.relative_to(book_root).as_posix(),
        "artifact_status": "derived",
    }


def _evaluate_plan_scene(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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
    resolved_branch_id = _resolved_branch_id(selector)
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
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


def _evaluate_continue_scene(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    resolved_branch_id = _resolved_branch_id(selector)
    if selector.chapter is None or selector.scene is None:
        return False, "continue_scene requires chapter and scene scope.", {}
    readiness = get_scene_phase_readiness(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=selector.chapter,
        scene_id=selector.scene,
        section_id=selector.section,
        prefer_emitted=prefer_emitted,
    )
    recommended = readiness.recommended_next_action
    action_row = next((item for item in readiness.actions if item.action == recommended), None)
    details = {
        "chapter_id": readiness.selector.chapter,
        "section_id": readiness.selector.section,
        "scene_id": readiness.selector.scene,
        "scene_status": readiness.scene_status,
        "recommended_next_action": recommended,
        "macro_kind": "single_recommended_scene_phase_step",
        "child_actions": [item.action for item in readiness.actions],
        "ready_child_action": recommended,
        "after_success_query": "scene_phase_readiness",
    }
    if action_row is not None:
        details.update(
            {
                "child_mutation_scope": action_row.mutation_scope,
                "available_inputs": list(action_row.available_inputs),
                "missing_prerequisites": list(action_row.missing_prerequisites),
            }
        )
    if not recommended:
        return False, "No ready recommended scene-phase action is available for the selected scene.", details
    return bool(action_row and action_row.legal and action_row.ready), action_row.refusal_reason if action_row else None, details


def _chapter_scene_ids(outline: dict, chapter_id: int) -> List[int]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            current = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current != int(chapter_id):
            continue
        scene_ids: List[int] = []
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for index, scene in enumerate(scenes, start=1):
                if not isinstance(scene, dict):
                    continue
                try:
                    scene_ids.append(int(scene.get("scene_id") or scene.get("beat_id") or scene.get("id") or index))
                except (TypeError, ValueError):
                    continue
        return scene_ids
    return []


def _adjacent_scene_id(workspace, book_id: str, branch_id: str, chapter_id: int, scene_id: int) -> Optional[int]:
    book_root = _common.execution_book_root(_common.book_root(workspace, book_id), branch_id)
    outline = _common.load_outline(book_root)
    scene_ids = _chapter_scene_ids(outline, chapter_id)
    for index, current in enumerate(scene_ids):
        if current == int(scene_id) and index + 1 < len(scene_ids):
            return scene_ids[index + 1]
    return None


def _scene_markdown_exists(workspace, book_id: str, branch_id: str, chapter_id: int, scene_id: int) -> bool:
    book_root = _common.execution_book_root(_common.book_root(workspace, book_id), branch_id)
    return (book_root / "draft" / "chapters" / f"ch_{int(chapter_id):03d}" / f"scene_{int(scene_id):03d}.md").exists()


def _evaluate_align_scene_pair_seam(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    del prefer_emitted
    branch_id = _resolved_branch_id(selector)
    if branch_id == MAIN_BRANCH_ID:
        return False, "align_scene_pair_seam requires a derived branch; canonical main is never rewritten directly.", {}
    if selector.chapter is None or selector.scene is None:
        return False, "align_scene_pair_seam requires chapter and scene scope.", {}
    scene_b_id = _adjacent_scene_id(workspace, book_id, branch_id, int(selector.chapter), int(selector.scene))
    details = {
        "chapter_id": int(selector.chapter),
        "scene_a_id": int(selector.scene),
        "scene_b_id": scene_b_id,
        "mutation_scope": "branch_authoritative",
        "artifact_status_after_success": "authoritative",
        "canonical_changed": False,
        "pair_window_policy": "scene_a_tail_and_scene_b_head_only",
    }
    if scene_b_id is None:
        return False, "No adjacent next scene exists in the selected chapter outline.", details
    missing = []
    if not _scene_markdown_exists(workspace, book_id, branch_id, int(selector.chapter), int(selector.scene)):
        missing.append(f"scene_{int(selector.scene):03d}.md")
    if not _scene_markdown_exists(workspace, book_id, branch_id, int(selector.chapter), int(scene_b_id)):
        missing.append(f"scene_{int(scene_b_id):03d}.md")
    if missing:
        return False, "Both adjacent scene prose files must exist before seam alignment.", {**details, "missing_scene_files": missing}
    return True, None, details


def _evaluate_plan_bridge_scene_insertion(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    del prefer_emitted
    branch_id = _resolved_branch_id(selector)
    if branch_id == MAIN_BRANCH_ID:
        return False, "plan_bridge_scene_insertion requires a derived branch; bridge insertion planning is branch-local.", {
            "refusal_code": "branch_required",
            "mutation_scope": "branch_provisional",
            "canonical_changed": False,
        }
    if selector.chapter is None or selector.scene is None:
        return False, "plan_bridge_scene_insertion requires chapter and scene scope.", {
            "refusal_code": "missing_chapter_or_scene_scope",
            "mutation_scope": "branch_provisional",
            "canonical_changed": False,
        }
    scene_b_id = _adjacent_scene_id(workspace, book_id, branch_id, int(selector.chapter), int(selector.scene))
    details = {
        "chapter_id": int(selector.chapter),
        "scene_a_id": int(selector.scene),
        "scene_b_id": scene_b_id,
        "mutation_scope": "branch_provisional",
        "artifact_status_after_success": "provisional",
        "canonical_changed": False,
        "proposal_only": True,
        "does_not_modify_outline_or_prose": True,
    }
    if scene_b_id is None:
        details["refusal_code"] = "no_adjacent_scene"
        return False, "No adjacent next scene exists in the selected chapter outline.", details
    return True, None, details


def _bridge_plan_path(workspace, book_id: str, branch_id: str, chapter_id: int, scene_a_id: int, scene_b_id: int):
    book_root = _common.execution_book_root(_common.book_root(workspace, book_id), branch_id)
    return book_root / "draft" / "context" / "bridge_scenes" / f"ch_{int(chapter_id):03d}" / f"bridge_after_scene_{int(scene_a_id):03d}_before_{int(scene_b_id):03d}.json"


def _evaluate_apply_bridge_scene_insertion(workspace, book_id: str, selector: ScopeSelector, *, prefer_emitted: bool) -> Tuple[bool, Optional[str], dict]:
    del prefer_emitted
    branch_id = _resolved_branch_id(selector)
    if branch_id == MAIN_BRANCH_ID:
        return False, "apply_bridge_scene_insertion requires a derived branch; bridge insertion is branch-local.", {
            "refusal_code": "branch_required",
            "mutation_scope": "branch_authoritative",
            "canonical_changed": False,
        }
    if selector.chapter is None or selector.scene is None:
        return False, "apply_bridge_scene_insertion requires chapter and scene scope.", {
            "refusal_code": "missing_chapter_or_scene_scope",
            "mutation_scope": "branch_authoritative",
            "canonical_changed": False,
        }
    scene_b_id = _adjacent_scene_id(workspace, book_id, branch_id, int(selector.chapter), int(selector.scene))
    details = {
        "chapter_id": int(selector.chapter),
        "scene_a_id": int(selector.scene),
        "scene_b_id": scene_b_id,
        "mutation_scope": "branch_authoritative",
        "artifact_status_after_success": "authoritative",
        "canonical_changed": False,
        "renumbering_policy": "branch_local_shift_following_integer_scene_ids",
        "same_section_only": True,
    }
    if scene_b_id is None:
        details["refusal_code"] = "no_adjacent_scene"
        return False, "No adjacent next scene exists in the selected chapter outline.", details
    plan_path = _bridge_plan_path(workspace, book_id, branch_id, int(selector.chapter), int(selector.scene), int(scene_b_id))
    details["bridge_plan_path"] = str(plan_path)
    if not plan_path.exists():
        details["refusal_code"] = "missing_bridge_scene_insertion_plan"
        return False, "apply_bridge_scene_insertion requires an existing bridge scene insertion plan.", details
    return True, None, details


def list_execution_options(workspace, selector: ScopeSelector, *, prefer_emitted: bool = True) -> List[ExecutionOption]:
    book_id = selector.book_id
    if _is_author_assets_selector(selector):
        return _author_asset_options()
    if _is_book_intent_selector(selector):
        return _book_intent_options(workspace)
    resolved_branch_id = _resolved_branch_id(selector)
    if selector.workflow_family == "visual_assets":
        plan_visual_allowed, plan_visual_refusal, plan_visual_details = _evaluate_plan_visual_asset(
            workspace,
            book_id,
            selector,
        )
        generate_visual_allowed, generate_visual_refusal, generate_visual_details = _evaluate_generate_visual_asset(
            workspace,
            book_id,
            selector,
        )
        return [
            ExecutionOption(
                action="plan_visual_asset",
                summary="Create a provisional visual prompt plan for a book, scene, author, or branch-scoped visual asset.",
                branch_policy="any",
                workflow_family="visual_assets",
                mutates_canonical_state=False,
                requires_expected_node=False,
                allowed=plan_visual_allowed,
                selector_requirements=["book_id", "details.prompt_text"],
                refusal_reason=plan_visual_refusal,
                details=plan_visual_details,
            ),
            ExecutionOption(
                action="generate_visual_asset",
                summary="Generate a provisional visual asset from an existing visual prompt plan after explicit spend approval.",
                branch_policy="any",
                workflow_family="visual_assets",
                mutates_canonical_state=False,
                requires_expected_node=False,
                allowed=generate_visual_allowed,
                selector_requirements=["book_id", "details.prompt_plan_path", "details.allow_spend"],
                refusal_reason=generate_visual_refusal,
                details=generate_visual_details,
            ),
        ]
    starter_outline_allowed, starter_outline_refusal, starter_outline_details = _evaluate_draft_starter_outline_from_intent(
        workspace,
        book_id,
        selector,
    )
    init_allowed, init_refusal, init_details = _evaluate_initialize_workflow(workspace, book_id, selector)
    create_branch_allowed, create_branch_refusal, create_branch_details = _evaluate_create_branch(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    create_recovery_allowed, create_recovery_refusal, create_recovery_details = _evaluate_create_recovery_branch(
        workspace,
        book_id,
        selector,
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
    quarantine_artifacts_allowed, quarantine_artifacts_refusal, quarantine_artifacts_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "quarantine_artifacts",
    )
    normalize_outline_allowed, normalize_outline_refusal, normalize_outline_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "normalize_outline_scope",
    )
    invalidate_outputs_allowed, invalidate_outputs_refusal, invalidate_outputs_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "invalidate_scope_outputs",
    )
    rebuild_state_allowed, rebuild_state_refusal, rebuild_state_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "rebuild_state_scope",
    )
    redraft_scope_allowed, redraft_scope_refusal, redraft_scope_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "redraft_scope",
    )
    validate_recovery_allowed, validate_recovery_refusal, validate_recovery_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "validate_recovery_branch",
    )
    review_recovery_semantics_allowed, review_recovery_semantics_refusal, review_recovery_semantics_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "review_recovery_semantics",
    )
    review_downstream_dependencies_allowed, review_downstream_dependencies_refusal, review_downstream_dependencies_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "review_downstream_dependencies",
    )
    promote_recovery_allowed, promote_recovery_refusal, promote_recovery_details = _evaluate_recovery_branch_action(
        workspace,
        book_id,
        selector,
        "promote_recovery_branch",
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
    appearance_projection_allowed, appearance_projection_refusal, appearance_projection_details = _evaluate_refresh_character_appearance_projection(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    draft_setting_allowed, draft_setting_refusal, draft_setting_details = _evaluate_draft_scene_setting_projection(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    extract_setting_allowed, extract_setting_refusal, extract_setting_details = _evaluate_extract_scene_setting_from_prose(
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
    continue_scene_allowed, continue_scene_refusal, continue_scene_details = _evaluate_continue_scene(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    align_pair_allowed, align_pair_refusal, align_pair_details = _evaluate_align_scene_pair_seam(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    bridge_plan_allowed, bridge_plan_refusal, bridge_plan_details = _evaluate_plan_bridge_scene_insertion(
        workspace,
        book_id,
        selector,
        prefer_emitted=prefer_emitted,
    )
    bridge_apply_allowed, bridge_apply_refusal, bridge_apply_details = _evaluate_apply_bridge_scene_insertion(
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
            action="continue_scene",
            summary="Execute the single recommended next scene-phase action for the selected scene and return a wrapper receipt.",
            branch_policy="any",
            workflow_family="section_write",
            mutates_canonical_state=bool(
                resolved_branch_id == MAIN_BRANCH_ID
                and continue_scene_details.get("child_mutation_scope") == "canonical"
            ),
            requires_expected_node=True,
            allowed=continue_scene_allowed,
            selector_requirements=["book_id", "chapter", "scene"],
            refusal_reason=continue_scene_refusal,
            details=continue_scene_details,
        ),
        ExecutionOption(
            action="draft_starter_outline_from_intent",
            summary="Author a thin starter outline from the created BookIntent and emit immutable run artifacts.",
            branch_policy="main_only",
            workflow_family="thin_outline",
            mutates_canonical_state=True,
            requires_expected_node=False,
            allowed=starter_outline_allowed,
            selector_requirements=["book_id"],
            refusal_reason=starter_outline_refusal,
            details=starter_outline_details,
        ),
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
            action="create_recovery_branch",
            summary=(
                "Create an isolated recovery branch, record the explicit timeline anchor and affected scope, "
                "and leave cleanup/normalization to later recovery actions."
            ),
            branch_policy="main_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=create_recovery_allowed,
            selector_requirements=["book_id"],
            refusal_reason=create_recovery_refusal,
            details=create_recovery_details,
        ),
        ExecutionOption(
            action="finalize_chapter_from_locked_sections",
            summary="Run pairwise seam repair and chapter finalization for a locked chapter in the selected execution root.",
            branch_policy="any",
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
            summary="Lock one frozen section after all required scene prose and meta artifacts exist in the selected execution root.",
            branch_policy="any",
            workflow_family="section_local_outline",
            mutates_canonical_state=resolved_branch_id == MAIN_BRANCH_ID,
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
            action="create_recovery_branch",
            summary=(
                "Create an isolated recovery branch, record the explicit timeline anchor and affected scope, "
                "and leave cleanup/normalization to later recovery actions."
            ),
            branch_policy="main_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=False,
            allowed=create_recovery_allowed,
            selector_requirements=["book_id"],
            refusal_reason=create_recovery_refusal,
            details=create_recovery_details,
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
            action="quarantine_artifacts",
            summary="Move stale or invalid recovery-scope artifacts out of the active branch snapshot and record promotion removals.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=quarantine_artifacts_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=quarantine_artifacts_refusal,
            details=quarantine_artifacts_details,
        ),
        ExecutionOption(
            action="normalize_outline_scope",
            summary="Replace affected branch outline scopes from the selected recovery anchor and rebuild outline projections.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=normalize_outline_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=normalize_outline_refusal,
            details=normalize_outline_details,
        ),
        ExecutionOption(
            action="invalidate_scope_outputs",
            summary="Quarantine prose and generated artifacts for affected branch scopes before redraft.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=invalidate_outputs_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=invalidate_outputs_refusal,
            details=invalidate_outputs_details,
        ),
        ExecutionOption(
            action="rebuild_state_scope",
            summary="Rebuild branch-local state and projection baselines from the normalized outline before validation.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=rebuild_state_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=rebuild_state_refusal,
            details=rebuild_state_details,
        ),
        ExecutionOption(
            action="redraft_scope",
            summary="Redraft affected recovery scopes inside the branch using the existing scoped section writer.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=redraft_scope_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=redraft_scope_refusal,
            details=redraft_scope_details,
        ),
        ExecutionOption(
            action="validate_recovery_branch",
            summary="Validate a recovery branch after normalization and invalidation before it may promote to main.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=validate_recovery_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=validate_recovery_refusal,
            details=validate_recovery_details,
        ),
        ExecutionOption(
            action="review_recovery_semantics",
            summary="Emit a diagnostic semantic recovery review artifact after structural recovery validation.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=review_recovery_semantics_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=review_recovery_semantics_refusal,
            details=review_recovery_semantics_details,
        ),
        ExecutionOption(
            action="review_downstream_dependencies",
            summary="Emit a diagnostic downstream dependency review artifact for a structurally recovered branch.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=False,
            requires_expected_node=True,
            allowed=review_downstream_dependencies_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=review_downstream_dependencies_refusal,
            details=review_downstream_dependencies_details,
        ),
        ExecutionOption(
            action="promote_recovery_branch",
            summary="Promote a validated recovery branch to main, including recorded removals of invalid canonical artifacts.",
            branch_policy="derived_only",
            workflow_family="recovery_import",
            mutates_canonical_state=True,
            requires_expected_node=True,
            allowed=promote_recovery_allowed,
            selector_requirements=["book_id", "branch_id"],
            refusal_reason=promote_recovery_refusal,
            details=promote_recovery_details,
        ),
    ]
    if resolved_branch_id != MAIN_BRANCH_ID and selector.section is not None:
        options.append(
            ExecutionOption(
                action="lock_section_from_written_state",
                summary="Lock one frozen section inside the selected branch after all required scene prose and meta artifacts exist.",
                branch_policy="any",
                workflow_family="section_local_outline",
                mutates_canonical_state=False,
                requires_expected_node=False,
                allowed=lock_allowed,
                selector_requirements=["book_id", "chapter", "section"],
                refusal_reason=lock_refusal,
                details=lock_details,
            )
        )
    if resolved_branch_id != MAIN_BRANCH_ID and selector.chapter is not None and selector.section is None:
        options.append(
            ExecutionOption(
                action="finalize_chapter_from_locked_sections",
                summary="Run pairwise seam repair and chapter finalization inside the selected branch.",
                branch_policy="any",
                workflow_family="section_local_outline",
                mutates_canonical_state=False,
                requires_expected_node=False,
                allowed=finalize_allowed,
                selector_requirements=["book_id", "chapter"],
                refusal_reason=finalize_refusal,
                details=finalize_details,
            )
        )
    if selector.scene is not None:
        if resolved_branch_id != MAIN_BRANCH_ID:
            options.append(
                ExecutionOption(
                    action="align_scene_pair_seam",
                    summary="Re-author the seam between the selected scene and its next adjacent scene inside a branch.",
                    branch_policy="derived_only",
                    workflow_family="section_write",
                    mutates_canonical_state=False,
                    requires_expected_node=True,
                    allowed=align_pair_allowed,
                    selector_requirements=["book_id", "branch_id", "chapter", "scene"],
                    refusal_reason=align_pair_refusal,
                    details=align_pair_details,
                )
            )
            options.append(
                ExecutionOption(
                    action="plan_bridge_scene_insertion",
                    summary="Create a provisional branch-local plan for inserting an adaptive bridge scene after the selected scene.",
                    branch_policy="derived_only",
                    workflow_family="section_write",
                    mutates_canonical_state=False,
                    requires_expected_node=True,
                    allowed=bridge_plan_allowed,
                    selector_requirements=["book_id", "branch_id", "chapter", "scene"],
                    refusal_reason=bridge_plan_refusal,
                    details=bridge_plan_details,
                )
            )
            options.append(
                ExecutionOption(
                    action="apply_bridge_scene_insertion",
                    summary="Apply a planned adaptive bridge scene insertion to the selected branch outline and scene sequence.",
                    branch_policy="derived_only",
                    workflow_family="section_write",
                    mutates_canonical_state=False,
                    requires_expected_node=True,
                    allowed=bridge_apply_allowed,
                    selector_requirements=["book_id", "branch_id", "chapter", "scene"],
                    refusal_reason=bridge_apply_refusal,
                    details=bridge_apply_details,
                )
            )
        options.append(
            ExecutionOption(
                action="plan_scene",
                summary="Generate a provisional scene card for the active cursor scene without auto-running downstream phases.",
                branch_policy="any",
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
                branch_policy="any",
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
                branch_policy="any",
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
                branch_policy="any",
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
                action="refresh_character_appearance_projection",
                summary="Derive a scene/cast-scoped appearance projection without mutating character truth.",
                branch_policy="any",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=appearance_projection_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=appearance_projection_refusal,
                details=appearance_projection_details,
            )
        )
        options.append(
            ExecutionOption(
                action="draft_scene_setting_projection",
                summary="Record a provisional author-drafted setting/background projection for the selected scene.",
                branch_policy="any",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=draft_setting_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=draft_setting_refusal,
                details=draft_setting_details,
            )
        )
        options.append(
            ExecutionOption(
                action="extract_scene_setting_from_prose",
                summary="Record a derived setting/background projection from existing scene prose.",
                branch_policy="any",
                workflow_family="section_write",
                mutates_canonical_state=False,
                requires_expected_node=True,
                allowed=extract_setting_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=extract_setting_refusal,
                details=extract_setting_details,
            )
        )
        options.append(
            ExecutionOption(
                action="state_repair_scene_patch",
                summary="Generate a provisional corrected state patch for the active cursor scene without linting, repairing prose, or committing.",
                branch_policy="any",
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
                branch_policy="any",
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
                branch_policy="any",
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
                branch_policy="any",
                workflow_family="section_write",
                mutates_canonical_state=resolved_branch_id == MAIN_BRANCH_ID,
                requires_expected_node=True,
                allowed=apply_scene_commit_allowed,
                selector_requirements=["book_id", "chapter", "scene"],
                refusal_reason=apply_scene_commit_refusal,
                details=apply_scene_commit_details,
            )
        )
    return _apply_lineage_safety_gate(workspace, book_id, resolved_branch_id, options)


def legal_next_actions(workspace, selector: ScopeSelector, *, prefer_emitted: bool = True) -> List[ExecutionOption]:
    return [option for option in list_execution_options(workspace, selector, prefer_emitted=prefer_emitted) if option.allowed]
