from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bookforge.contracts import (
    MAIN_BRANCH_ID,
    ExecutionOption,
    ScopeSelector,
    WritingBootstrapStage,
    WritingBootstrapStatus,
)

from . import _common
from .actions import list_execution_options
from .branches import get_branch_inventory
from .outline_lineage import get_outline_lineage_audit
from .writing import get_next_writing_target


def _target_selector(
    book_id: str,
    *,
    branch_id: Optional[str] = None,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    workflow_family: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"book_id": book_id}
    if branch_id:
        payload["branch_id"] = branch_id
    if workflow_family:
        payload["workflow_family"] = workflow_family
    if chapter_id is not None:
        payload["chapter"] = int(chapter_id)
    if section_id is not None:
        payload["section"] = int(section_id)
    if scene_id is not None:
        payload["scene"] = int(scene_id)
    return payload


def _stage(
    stage_key: str,
    label: str,
    *,
    status: str,
    ready: bool = False,
    action: Optional[str] = None,
    approval_class: Optional[str] = None,
    target_selector: Optional[Dict[str, Any]] = None,
    blocked_reason: Optional[str] = None,
    evidence_refs: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> WritingBootstrapStage:
    return WritingBootstrapStage(
        stage_key=stage_key,
        label=label,
        status=status,
        ready=ready,
        action=action,
        approval_class=approval_class,
        target_selector=target_selector or {},
        blocked_reason=blocked_reason,
        evidence_refs=evidence_refs or [],
        details=details or {},
    )


def _artifact_ref(book_root: Path, path: Path, artifact_status: str, artifact_class: str) -> Dict[str, Any]:
    try:
        relpath = path.relative_to(book_root).as_posix()
    except ValueError:
        relpath = path.as_posix()
    return {
        "path": relpath,
        "exists": path.exists(),
        "artifact_status": artifact_status,
        "artifact_class": artifact_class,
    }


def _section_rows(registry: Dict[str, Any]) -> List[Tuple[int, Dict[str, Any]]]:
    rows: List[Tuple[int, Dict[str, Any]]] = []
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _common.coerce_int(chapter.get("chapter_id"))
        if chapter_id is None:
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if isinstance(section, dict) and _common.coerce_int(section.get("section_id")) is not None:
                rows.append((int(chapter_id), section))
    rows.sort(key=lambda item: (item[0], int(item[1].get("section_id") or 0)))
    return rows


def _find_section(registry: Dict[str, Any], chapter_id: Optional[int], section_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if chapter_id is None or section_id is None:
        return None
    for row_chapter, section in _section_rows(registry):
        if row_chapter == int(chapter_id) and _common.coerce_int(section.get("section_id")) == int(section_id):
            return section
    return None


def _section_scene_start(section: Optional[Dict[str, Any]]) -> Optional[int]:
    if not isinstance(section, dict):
        return None
    value = str(section.get("scene_ref_start") or "").strip()
    if ":" in value:
        _, scene_text = value.split(":", 1)
        return _common.coerce_int(scene_text)
    scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
    if scenes and isinstance(scenes[0], dict):
        return _common.coerce_int(scenes[0].get("scene_id") or scenes[0].get("beat_id") or 1)
    return None


def _first_target_section(
    registry: Dict[str, Any],
    chapter_id: Optional[int],
    section_id: Optional[int],
) -> Tuple[Optional[int], Optional[int], Optional[Dict[str, Any]]]:
    if chapter_id is not None and section_id is not None:
        return int(chapter_id), int(section_id), _find_section(registry, chapter_id, section_id)
    rows = _section_rows(registry)
    if not rows:
        return chapter_id, section_id, None
    for row_chapter, section in rows:
        status = str(section.get("status") or "").strip().lower()
        if status != "locked":
            return row_chapter, _common.coerce_int(section.get("section_id")), section
    row_chapter, section = rows[0]
    return row_chapter, _common.coerce_int(section.get("section_id")), section


def _option_for(workspace: Path, selector: ScopeSelector, action_key: str, *, prefer_emitted: bool) -> Optional[ExecutionOption]:
    try:
        for option in list_execution_options(workspace, selector, prefer_emitted=prefer_emitted):
            if option.action == action_key:
                return option
    except Exception:
        return None
    return None


def _option_details(option: Optional[ExecutionOption]) -> Dict[str, Any]:
    if option is None:
        return {"option_available": False}
    return {
        "option_available": True,
        "allowed": bool(option.allowed),
        "branch_policy": option.branch_policy,
        "workflow_family": option.workflow_family,
        "mutates_canonical_state": bool(option.mutates_canonical_state),
        "requires_expected_node": bool(option.requires_expected_node),
        "selector_requirements": list(option.selector_requirements),
        "refusal_reason": option.refusal_reason,
        "details": dict(option.details),
    }


def _preferred_branch(
    workspace: Path,
    book_id: str,
    *,
    branch_id: Optional[str],
    chapter_id: Optional[int],
    section_id: Optional[int],
) -> Tuple[Optional[str], Optional[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    try:
        inventory = get_branch_inventory(workspace, book_id)
    except Exception as exc:
        return None, None, [f"branch_inventory_unavailable:{exc}"]

    if branch_id and branch_id != MAIN_BRANCH_ID:
        for record in inventory.branches:
            if record.branch_id == branch_id:
                return record.branch_id, record.to_dict(), warnings
        return branch_id, None, [f"branch_not_found:{branch_id}"]

    candidates = []
    for record in inventory.branches:
        lifecycle = str(record.lifecycle_state or "").strip().lower()
        if lifecycle in {"discard", "promoted"} or record.stale_parent:
            continue
        selector = record.selector if isinstance(record.selector, dict) else {}
        if chapter_id is not None and _common.coerce_int(selector.get("chapter")) not in {None, int(chapter_id)}:
            continue
        if section_id is not None and _common.coerce_int(selector.get("section")) not in {None, int(section_id)}:
            continue
        candidates.append(record)
    if candidates:
        record = sorted(candidates, key=lambda item: item.branch_id)[0]
        return record.branch_id, record.to_dict(), warnings
    return None, None, warnings


def _has_outline_lineage_material(book_root: Path) -> bool:
    outline_root = _common.outline_root(book_root)
    return any(
        path.exists()
        for path in (
            outline_root / "pipeline_latest.json",
            outline_root / "snapshot_registry.json",
            outline_root / "section_drafts",
            outline_root / "outline.json",
            outline_root / "chapters",
        )
    )


def _integrity_block_stage(workspace: Path, book_id: str, book_root: Path) -> Tuple[Optional[WritingBootstrapStage], List[str], Dict[str, Any]]:
    if not _has_outline_lineage_material(book_root):
        return None, [], {}
    try:
        audit = get_outline_lineage_audit(workspace, book_id)
    except Exception as exc:
        return None, [f"outline_lineage_audit_unavailable:{exc}"], {}
    details = {
        "outline_lineage_status": audit.status,
        "affected_scope_count": len(audit.affected_sections),
        "first_technical_divergence": audit.first_technical_divergence,
        "first_visible_story_divergence": audit.first_visible_story_divergence,
        "blocked_actions": list(audit.blocked_actions),
    }
    if audit.status == "chimera_risk":
        return (
            _stage(
                "outline_integrity",
                "Outline integrity",
                status="blocked",
                ready=False,
                action="outline_lineage_audit",
                approval_class="none",
                target_selector=_target_selector(book_id),
                blocked_reason="Book has outline lineage contamination; writing bootstrap is blocked until recovery is planned.",
                evidence_refs=["query.outline_lineage_audit", "query.outline_repair_candidates"],
                details=details,
            ),
            [],
            details,
        )
    if audit.status != "healthy":
        return (
            _stage(
                "outline_integrity",
                "Outline integrity",
                status="attention_required",
                ready=False,
                action="outline_lineage_audit",
                approval_class="none",
                target_selector=_target_selector(book_id),
                blocked_reason="Book has outline lineage warnings; inspect before starting new writing work.",
                evidence_refs=["query.outline_lineage_audit"],
                details=details,
            ),
            ["outline_integrity_attention_required"],
            details,
        )
    return (
        _stage(
            "outline_integrity",
            "Outline integrity",
            status="complete",
            ready=False,
            evidence_refs=["query.outline_lineage_audit"],
            details=details,
        ),
        [],
        details,
    )


def _result(
    *,
    book_id: str,
    status: str,
    can_start_writing: bool,
    stages: List[WritingBootstrapStage],
    recommended_action: Optional[str],
    required_approval_class: Optional[str],
    target_selector: Optional[Dict[str, Any]],
    target_branch_id: Optional[str],
    blocked_reason: Optional[str],
    artifact_refs: List[Dict[str, Any]],
    warnings: List[str],
    details: Dict[str, Any],
) -> WritingBootstrapStatus:
    return WritingBootstrapStatus(
        book_id=book_id,
        status=status,
        can_start_writing=can_start_writing,
        recommended_action=recommended_action,
        required_approval_class=required_approval_class,
        target_selector=target_selector or {},
        target_branch_id=target_branch_id,
        blocked_reason=blocked_reason,
        stages=stages,
        artifact_refs=artifact_refs,
        warnings=warnings,
        details=details,
    )


def get_writing_bootstrap_status(
    workspace,
    book_id: str,
    *,
    branch_id: Optional[str] = None,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    prefer_emitted: bool = True,
) -> WritingBootstrapStatus:
    """Return a read-only setup-to-writing status for a book.

    This is the bridge between BookIntent creation and branch-local authoring. It
    reports the next valid setup or writing action without calling a provider and
    without mutating outline, workflow, branch, or prose artifacts.
    """

    workspace_path = Path(workspace)
    canonical_book_root = _common.book_root(workspace_path, book_id)
    artifact_refs: List[Dict[str, Any]] = []
    warnings: List[str] = []
    stages: List[WritingBootstrapStage] = []
    details: Dict[str, Any] = {
        "static_dynamic_boundary": "This query reports status only; callers must execute the recommended action separately.",
        "expected_sequence": [
            "draft_starter_outline_from_intent",
            "initialize_section_workflow",
            "freeze_section_from_phase03_artifact",
            "create_branch",
            "continue_scene",
        ],
    }

    if not canonical_book_root.exists():
        stages.append(
            _stage(
                "book_workspace",
                "Book workspace",
                status="blocked",
                blocked_reason=f"Book workspace not found: {book_id}",
                target_selector=_target_selector(book_id),
                evidence_refs=["query.book_cards"],
            )
        )
        return _result(
            book_id=book_id,
            status="blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action=None,
            required_approval_class=None,
            target_selector=_target_selector(book_id),
            target_branch_id=None,
            blocked_reason=f"Book workspace not found: {book_id}",
            artifact_refs=[],
            warnings=[],
            details=details,
        )

    book_path = canonical_book_root / "book.json"
    intent_path = canonical_book_root / "book_intent.json"
    artifact_refs.extend(
        [
            _artifact_ref(canonical_book_root, book_path, "authoritative", "book_manifest"),
            _artifact_ref(canonical_book_root, intent_path, "authoritative", "book_intent"),
        ]
    )
    stages.append(
        _stage(
            "book_workspace",
            "Book workspace",
            status="complete",
            ready=False,
            evidence_refs=["query.book_cards"],
            details={"book_path": "book.json"},
        )
    )

    intent = _common.read_json(intent_path) or {}
    intent_status = str(intent.get("status") or "").strip()
    latest_run_id = _common.latest_outline_run_id(canonical_book_root)
    if intent and intent_status == "created":
        stages.append(
            _stage(
                "book_intent",
                "Created BookIntent",
                status="complete",
                evidence_refs=["query.book_intent"],
                details={"intent_id": intent.get("intent_id"), "status": intent_status},
            )
        )
    else:
        if latest_run_id:
            warnings.append("book_intent_missing_or_not_created_for_existing_outline")
            stages.append(
                _stage(
                    "book_intent",
                    "Created BookIntent",
                    status="not_applicable",
                    ready=False,
                    evidence_refs=["query.book_intent"],
                    blocked_reason=None,
                    details={
                        "intent_id": intent.get("intent_id"),
                        "status": intent_status or None,
                        "reason": "Existing outline artifacts are present, so bootstrap continues as a legacy or pre-intent book.",
                    },
                )
            )
        else:
            blocked = "Book has no created BookIntent; create or approve a BookIntent before starter outline generation."
            if intent:
                blocked = "BookIntent exists but is not created."
            stages.append(
                _stage(
                    "book_intent",
                    "Created BookIntent",
                    status="blocked",
                    ready=False,
                    action="create_book_from_intent",
                    approval_class="canonical",
                    target_selector=_target_selector(book_id),
                    blocked_reason=blocked,
                    evidence_refs=["query.book_intent", "action.create_book_from_intent"],
                    details={"intent_id": intent.get("intent_id"), "status": intent_status or None},
                )
            )
            return _result(
                book_id=book_id,
                status="blocked",
                can_start_writing=False,
                stages=stages,
                recommended_action="create_book_from_intent",
                required_approval_class="canonical",
                target_selector=_target_selector(book_id),
                target_branch_id=None,
                blocked_reason=blocked,
                artifact_refs=artifact_refs,
                warnings=warnings,
                details=details,
            )
    if latest_run_id:
        run_dir = canonical_book_root / "outline" / "pipeline_runs" / latest_run_id
        artifact_refs.extend(
            [
                _artifact_ref(canonical_book_root, run_dir / "outline_spine_v1.json", "authoritative", "outline_spine"),
                _artifact_ref(canonical_book_root, run_dir / "outline_sections_v1.json", "authoritative", "outline_sections"),
                _artifact_ref(canonical_book_root, run_dir / "outline_final_v1_1.json", "authoritative", "outline_final"),
                _artifact_ref(canonical_book_root, run_dir / "outline_pipeline_report.json", "diagnostic", "outline_report"),
                _artifact_ref(canonical_book_root, canonical_book_root / "outline" / "pipeline_latest.json", "diagnostic", "outline_pointer"),
            ]
        )
        stages.append(
            _stage(
                "starter_outline",
                "Starter outline",
                status="complete",
                evidence_refs=["action.draft_starter_outline_from_intent", "query.outline_lineage_audit"],
                details={"run_id": latest_run_id},
            )
        )
    else:
        selector = ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID, workflow_family="thin_outline")
        option = _option_for(workspace_path, selector, "draft_starter_outline_from_intent", prefer_emitted=prefer_emitted)
        allowed = bool(option and option.allowed)
        blocked = option.refusal_reason if option else "draft_starter_outline_from_intent is not available."
        stages.append(
            _stage(
                "starter_outline",
                "Starter outline",
                status="ready" if allowed else "blocked",
                ready=allowed,
                action="draft_starter_outline_from_intent",
                approval_class="provider",
                target_selector=_target_selector(book_id, workflow_family="thin_outline"),
                blocked_reason=None if allowed else blocked,
                evidence_refs=["action.draft_starter_outline_from_intent", "readiness.legal_next_actions"],
                details=_option_details(option),
            )
        )
        return _result(
            book_id=book_id,
            status="setup_required" if allowed else "blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action="draft_starter_outline_from_intent",
            required_approval_class="provider",
            target_selector=_target_selector(book_id, workflow_family="thin_outline"),
            target_branch_id=None,
            blocked_reason=None if allowed else blocked,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )

    integrity_stage, integrity_warnings, integrity_details = _integrity_block_stage(workspace_path, book_id, canonical_book_root)
    warnings.extend(integrity_warnings)
    if integrity_stage is not None:
        stages.append(integrity_stage)
        details["outline_integrity"] = integrity_details
        if integrity_stage.status == "blocked":
            return _result(
                book_id=book_id,
                status="blocked",
                can_start_writing=False,
                stages=stages,
                recommended_action=integrity_stage.action,
                required_approval_class=integrity_stage.approval_class,
                target_selector=integrity_stage.target_selector,
                target_branch_id=None,
                blocked_reason=integrity_stage.blocked_reason,
                artifact_refs=artifact_refs,
                warnings=warnings,
                details=details,
            )

    registry = _common.load_registry(canonical_book_root)
    registry_path = canonical_book_root / "outline" / "snapshot_registry.json"
    artifact_refs.append(_artifact_ref(canonical_book_root, registry_path, "authoritative", "workflow_registry"))
    registry_sections = _section_rows(registry)
    details["workflow_section_count"] = len(registry_sections)

    if not registry_sections:
        selector = ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID, workflow_family="section_local_outline")
        option = _option_for(workspace_path, selector, "initialize_section_workflow", prefer_emitted=prefer_emitted)
        allowed = bool(option and option.allowed)
        blocked = option.refusal_reason if option else "initialize_section_workflow is not available."
        stages.append(
            _stage(
                "workflow_registry",
                "Section workflow registry",
                status="ready" if allowed else "blocked",
                ready=allowed,
                action="initialize_section_workflow",
                approval_class="canonical",
                target_selector=_target_selector(book_id, workflow_family="section_local_outline"),
                blocked_reason=None if allowed else blocked,
                evidence_refs=["action.initialize_section_workflow", "readiness.legal_next_actions"],
                details=_option_details(option),
            )
        )
        return _result(
            book_id=book_id,
            status="setup_required" if allowed else "blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action="initialize_section_workflow",
            required_approval_class="canonical",
            target_selector=_target_selector(book_id, workflow_family="section_local_outline"),
            target_branch_id=None,
            blocked_reason=None if allowed else blocked,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )

    stages.append(
        _stage(
            "workflow_registry",
            "Section workflow registry",
            status="complete",
            evidence_refs=["action.initialize_section_workflow", "query.workflow_snapshot"],
            details={"section_count": len(registry_sections)},
        )
    )

    target_chapter, target_section, section = _first_target_section(registry, chapter_id, section_id)
    if target_chapter is None or target_section is None or section is None:
        blocked = "No target section could be resolved from workflow registry."
        stages.append(
            _stage(
                "section_materialization",
                "Section materialization",
                status="blocked",
                blocked_reason=blocked,
                target_selector=_target_selector(book_id, chapter_id=chapter_id, section_id=section_id),
                evidence_refs=["query.workflow_snapshot"],
            )
        )
        return _result(
            book_id=book_id,
            status="blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action=None,
            required_approval_class=None,
            target_selector=_target_selector(book_id, chapter_id=chapter_id, section_id=section_id),
            target_branch_id=None,
            blocked_reason=blocked,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )

    section_status = str(section.get("status") or "").strip().lower()
    target_scene = scene_id or _section_scene_start(section)
    section_selector = _target_selector(book_id, chapter_id=target_chapter, section_id=target_section)
    if section_status in {"frozen", "locked"}:
        stages.append(
            _stage(
                "section_materialization",
                "Section materialization",
                status="complete",
                target_selector=section_selector,
                evidence_refs=["action.freeze_section_from_phase03_artifact", "query.workflow_snapshot"],
                details={"section_status": section_status, "scene_start": target_scene},
            )
        )
    else:
        selector = ScopeSelector(
            book_id=book_id,
            branch_id=MAIN_BRANCH_ID,
            workflow_family="section_local_outline",
            chapter=target_chapter,
            section=target_section,
        )
        option = _option_for(workspace_path, selector, "freeze_section_from_phase03_artifact", prefer_emitted=prefer_emitted)
        allowed = bool(option and option.allowed)
        blocked = option.refusal_reason if option else "freeze_section_from_phase03_artifact is not available."
        stages.append(
            _stage(
                "section_materialization",
                "Section materialization",
                status="ready" if allowed else "blocked",
                ready=allowed,
                action="freeze_section_from_phase03_artifact",
                approval_class="canonical",
                target_selector=section_selector,
                blocked_reason=None if allowed else blocked,
                evidence_refs=["action.freeze_section_from_phase03_artifact", "readiness.legal_next_actions"],
                details={**_option_details(option), "section_status": section_status or None},
            )
        )
        return _result(
            book_id=book_id,
            status="setup_required" if allowed else "blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action="freeze_section_from_phase03_artifact",
            required_approval_class="canonical",
            target_selector=section_selector,
            target_branch_id=None,
            blocked_reason=None if allowed else blocked,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )

    resolved_branch_id, branch_record, branch_warnings = _preferred_branch(
        workspace_path,
        book_id,
        branch_id=branch_id,
        chapter_id=target_chapter,
        section_id=target_section,
    )
    warnings.extend(branch_warnings)
    if branch_id and branch_id != MAIN_BRANCH_ID and branch_record is None:
        blocked = f"Requested branch was not found: {branch_id}"
        stages.append(
            _stage(
                "branch_workspace",
                "Branch workspace",
                status="blocked",
                target_selector=_target_selector(
                    book_id,
                    branch_id=branch_id,
                    chapter_id=target_chapter,
                    section_id=target_section,
                    scene_id=target_scene,
                    workflow_family="section_write",
                ),
                blocked_reason=blocked,
                evidence_refs=["query.branch_inventory"],
            )
        )
        return _result(
            book_id=book_id,
            status="blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action=None,
            required_approval_class=None,
            target_selector=stages[-1].target_selector,
            target_branch_id=branch_id,
            blocked_reason=blocked,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )
    if branch_record is None:
        selector = ScopeSelector(
            book_id=book_id,
            branch_id=MAIN_BRANCH_ID,
            workflow_family="section_write",
            chapter=target_chapter,
            section=target_section,
            scene=target_scene,
        )
        option = _option_for(workspace_path, selector, "create_branch", prefer_emitted=prefer_emitted)
        allowed = bool(option and option.allowed)
        blocked = option.refusal_reason if option else "create_branch is not available."
        stages.append(
            _stage(
                "branch_workspace",
                "Branch workspace",
                status="ready" if allowed else "blocked",
                ready=allowed,
                action="create_branch",
                approval_class="branch",
                target_selector=_target_selector(
                    book_id,
                    branch_id=MAIN_BRANCH_ID,
                    chapter_id=target_chapter,
                    section_id=target_section,
                    scene_id=target_scene,
                    workflow_family="section_write",
                ),
                blocked_reason=None if allowed else blocked,
                evidence_refs=["action.create_branch", "query.branch_inventory", "readiness.legal_next_actions"],
                details=_option_details(option),
            )
        )
        return _result(
            book_id=book_id,
            status="setup_required" if allowed else "blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action="create_branch",
            required_approval_class="branch",
            target_selector=stages[-1].target_selector,
            target_branch_id=None,
            blocked_reason=None if allowed else blocked,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )

    resolved_branch_id = resolved_branch_id or str(branch_record.get("branch_id") or "")
    stages.append(
        _stage(
            "branch_workspace",
            "Branch workspace",
            status="complete",
            target_selector=_target_selector(
                book_id,
                branch_id=resolved_branch_id,
                chapter_id=target_chapter,
                section_id=target_section,
                scene_id=target_scene,
                workflow_family="section_write",
            ),
            evidence_refs=["query.branch_inventory", "query.branch_detail"],
            details={"branch": branch_record},
        )
    )

    try:
        target = get_next_writing_target(
            workspace_path,
            book_id,
            branch_id=resolved_branch_id,
            chapter_id=target_chapter,
            section_id=target_section,
            scene_id=target_scene,
            prefer_emitted=prefer_emitted,
        )
    except Exception as exc:
        blocked = f"Next writing target is unavailable: {exc}"
        stages.append(
            _stage(
                "scene_continue",
                "Scene continuation",
                status="blocked",
                target_selector=_target_selector(
                    book_id,
                    branch_id=resolved_branch_id,
                    chapter_id=target_chapter,
                    section_id=target_section,
                    scene_id=target_scene,
                    workflow_family="section_write",
                ),
                blocked_reason=blocked,
                evidence_refs=["query.next_writing_target"],
            )
        )
        return _result(
            book_id=book_id,
            status="blocked",
            can_start_writing=False,
            stages=stages,
            recommended_action=None,
            required_approval_class=None,
            target_selector=stages[-1].target_selector,
            target_branch_id=resolved_branch_id,
            blocked_reason=blocked,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )

    scene_selector = target.selector.to_dict()
    if target.can_continue and target.recommended_action == "continue_scene":
        stages.append(
            _stage(
                "scene_continue",
                "Scene continuation",
                status="ready",
                ready=True,
                action="continue_scene",
                approval_class="branch",
                target_selector=scene_selector,
                evidence_refs=["query.next_writing_target", "readiness.writing_gate_status", "action.continue_scene"],
                details={"next_writing_target": target.to_dict()},
            )
        )
        return _result(
            book_id=book_id,
            status="ready_to_write",
            can_start_writing=True,
            stages=stages,
            recommended_action="continue_scene",
            required_approval_class="branch",
            target_selector=scene_selector,
            target_branch_id=resolved_branch_id,
            blocked_reason=None,
            artifact_refs=artifact_refs,
            warnings=warnings,
            details=details,
        )

    stages.append(
        _stage(
            "scene_continue",
            "Scene continuation",
            status="blocked" if not target.book_complete else "complete",
            ready=False,
            action=target.recommended_action,
            approval_class="branch" if target.recommended_action else None,
            target_selector=scene_selector,
            blocked_reason=target.blocked_reason,
            evidence_refs=["query.next_writing_target", "readiness.writing_gate_status"],
            details={"next_writing_target": target.to_dict()},
        )
    )
    return _result(
        book_id=book_id,
        status="blocked" if not target.book_complete else "complete",
        can_start_writing=False,
        stages=stages,
        recommended_action=target.recommended_action,
        required_approval_class="branch" if target.recommended_action else None,
        target_selector=scene_selector,
        target_branch_id=resolved_branch_id,
        blocked_reason=target.blocked_reason,
        artifact_refs=artifact_refs,
        warnings=warnings,
        details=details,
    )
