from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bookforge.contracts import ProducedArtifactReceipt, ScenePhaseActionReadiness, ScenePhaseReadiness, ScopeSelector
from bookforge.memory.continuity import load_style_anchor, style_anchor_path
from bookforge.pipeline.scene_phase_artifacts import ScenePhaseArtifactState, load_scene_phase_artifact_state

from . import _common
from .workspace import current_main_node, get_section_status, get_workspace_status


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_relpath(book_root: Path, path: Path) -> str:
    try:
        return path.relative_to(book_root).as_posix()
    except ValueError:
        return path.as_posix()


def _receipt(
    *,
    book_root: Path,
    artifact_key: str,
    label: str,
    artifact_status: str,
    path: Path,
    format: Optional[str],
    consumable: bool,
    resumable: bool,
    replaceable: bool,
    details: Optional[Dict[str, Any]] = None,
) -> ProducedArtifactReceipt:
    return ProducedArtifactReceipt(
        artifact_key=artifact_key,
        label=label,
        artifact_status=artifact_status,
        path=_artifact_relpath(book_root, path),
        format=format,
        consumable=consumable,
        resumable=resumable,
        replaceable=replaceable,
        details=dict(details or {}),
    )


def _parse_scene_ref(value: object) -> Tuple[Optional[int], Optional[int]]:
    text = str(value or "").strip()
    if ":" not in text:
        return None, None
    chapter_text, scene_text = text.split(":", 1)
    return _common.coerce_int(chapter_text), _common.coerce_int(scene_text)


def _section_scene_bounds(section_status: Dict[str, object]) -> Tuple[Optional[int], Optional[int]]:
    _, scene_start = _parse_scene_ref(section_status.get("scene_ref_start"))
    _, scene_end = _parse_scene_ref(section_status.get("scene_ref_end"))
    return scene_start, scene_end


def _scene_within_bounds(scene_id: int, start: Optional[int], end: Optional[int]) -> bool:
    if start is None or end is None:
        return False
    return int(start) <= int(scene_id) <= int(end)


def _artifact_details(*, phase: str, current: bool, superseded: bool, version_ns: int) -> Dict[str, Any]:
    return {
        "phase": phase,
        "current": bool(current),
        "superseded": bool(superseded),
        "version_ns": int(version_ns or 0),
    }


def _artifact_version(path: Optional[Path]) -> int:
    if not isinstance(path, Path) or not path.exists():
        return 0
    return int(path.stat().st_mtime_ns)


def _prose_labels(artifact_state: ScenePhaseArtifactState) -> Tuple[str, str]:
    if artifact_state.current_prose_phase == "repair":
        return "repair_prose", "repair_patch"
    return "write_prose", "write_patch"


def get_scene_phase_readiness(
    workspace,
    book_id: str,
    *,
    chapter_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    section_id: Optional[int] = None,
    prefer_emitted: bool = True,
) -> ScenePhaseReadiness:
    book_root = _common.book_root(workspace, book_id)
    status = get_workspace_status(workspace, book_id, prefer_emitted=prefer_emitted)
    node = current_main_node(workspace, book_id, prefer_emitted=prefer_emitted)

    cursor = status.cursor if isinstance(status.cursor, dict) else {}
    cursor_chapter = _common.coerce_int(cursor.get("chapter"))
    cursor_scene = _common.coerce_int(cursor.get("scene"))
    active_section = status.active_section if isinstance(status.active_section, dict) else None
    active_chapter = _common.coerce_int((active_section or {}).get("chapter_id"))
    active_section_id = _common.coerce_int((active_section or {}).get("section_id"))

    resolved_chapter = chapter_id or cursor_chapter or active_chapter
    resolved_scene = scene_id or cursor_scene
    resolved_section = section_id or active_section_id

    selector = ScopeSelector(
        book_id=book_id,
        branch_id="main",
        workflow_family="section_write",
        chapter=resolved_chapter,
        section=resolved_section,
        scene=resolved_scene,
    )

    active_section_status = (
        get_section_status(workspace, book_id, active_chapter, active_section_id)
        if active_chapter is not None and active_section_id is not None
        else None
    )
    scene_start, scene_end = _section_scene_bounds(active_section_status or {})

    scope_refusal: Optional[str] = None
    if resolved_chapter is None or resolved_scene is None:
        scope_refusal = "Scene-phase readiness requires a resolved chapter and scene."
    elif not isinstance(active_section, dict):
        scope_refusal = "No active frozen section is available for scene-phase actions."
    elif str(active_section.get("status") or "").strip().lower() != "frozen":
        scope_refusal = "Scene-phase actions require the active section to remain frozen."
    elif cursor_chapter is None or cursor_scene is None:
        scope_refusal = "Scene-phase actions require a current cursor."
    elif int(resolved_chapter) != int(cursor_chapter) or int(resolved_scene) != int(cursor_scene):
        scope_refusal = "Scene-phase actions currently only support the active cursor scene."
    elif active_chapter is None or active_section_id is None:
        scope_refusal = "Scene-phase actions require a resolved active section."
    elif resolved_section is not None and int(resolved_section) != int(active_section_id):
        scope_refusal = "Requested section does not match the active frozen section."
    elif not _scene_within_bounds(int(resolved_scene), scene_start, scene_end):
        scope_refusal = "Requested scene is outside the active frozen section range."

    artifact_state = (
        load_scene_phase_artifact_state(book_root, int(resolved_chapter), int(resolved_scene))
        if resolved_chapter is not None and resolved_scene is not None
        else ScenePhaseArtifactState(
            phase_history={"phases": {}},
            scene_card_path=None,
            preflight_patch_path=None,
            continuity_pack_path=None,
            write_prose_path=None,
            write_patch_path=None,
            repair_prose_path=None,
            repair_patch_path=None,
            state_repair_patch_path=None,
            lint_report_path=None,
            write_version=0,
            repair_version=0,
            state_repair_version=0,
            lint_version=0,
            current_prose_phase=None,
            current_prose_path=None,
            current_patch_path=None,
            current_prose_version=0,
            state_repair_current=False,
            lint_current=False,
            lint_status=None,
        )
    )

    scene_card_path = artifact_state.scene_card_path
    preflight_patch_path = artifact_state.preflight_patch_path
    continuity_pack_path = artifact_state.continuity_pack_path
    write_prose_path = artifact_state.write_prose_path
    write_patch_path = artifact_state.write_patch_path
    repair_prose_path = artifact_state.repair_prose_path
    repair_patch_path = artifact_state.repair_patch_path
    state_repair_patch_path = artifact_state.state_repair_patch_path
    lint_report_path = artifact_state.lint_report_path

    committed_prose_path = None
    committed_meta_path = None
    if resolved_chapter is not None and resolved_scene is not None:
        chapter_dir = book_root / "draft" / "chapters" / f"ch_{int(resolved_chapter):03d}"
        prose_candidate = chapter_dir / f"scene_{int(resolved_scene):03d}.md"
        meta_candidate = chapter_dir / f"scene_{int(resolved_scene):03d}.meta.json"
        if prose_candidate.exists():
            committed_prose_path = prose_candidate
        if meta_candidate.exists():
            committed_meta_path = meta_candidate

    style_anchor_text = load_style_anchor(style_anchor_path(book_root))
    style_anchor_exists = bool(style_anchor_text.strip())

    scene_card_receipts = (
        [
            _receipt(
                book_root=book_root,
                artifact_key="scene_card",
                label="Scene card",
                artifact_status="provisional",
                path=scene_card_path,
                format="application/json",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(phase="plan", current=True, superseded=False, version_ns=_artifact_version(scene_card_path)),
            )
        ]
        if scene_card_path is not None
        else []
    )
    preflight_receipts = (
        [
            _receipt(
                book_root=book_root,
                artifact_key="preflight_patch",
                label="Preflight state patch",
                artifact_status="provisional",
                path=preflight_patch_path,
                format="application/json",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(phase="preflight", current=True, superseded=False, version_ns=_artifact_version(preflight_patch_path)),
            )
        ]
        if preflight_patch_path is not None
        else []
    )
    continuity_receipts = (
        [
            _receipt(
                book_root=book_root,
                artifact_key="continuity_pack",
                label="Continuity pack",
                artifact_status="derived",
                path=continuity_pack_path,
                format="application/json",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(
                    phase="continuity_pack",
                    current=True,
                    superseded=False,
                    version_ns=_artifact_version(continuity_pack_path),
                ),
            )
        ]
        if continuity_pack_path is not None
        else []
    )
    write_receipts: List[ProducedArtifactReceipt] = []
    if write_prose_path is not None:
        write_receipts.append(
            _receipt(
                book_root=book_root,
                artifact_key="write_prose",
                label="Draft prose",
                artifact_status="provisional",
                path=write_prose_path,
                format="text/plain",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(
                    phase="write",
                    current=artifact_state.current_prose_phase == "write",
                    superseded=artifact_state.current_prose_phase == "repair",
                    version_ns=artifact_state.write_version,
                ),
            )
        )
    if write_patch_path is not None:
        write_receipts.append(
            _receipt(
                book_root=book_root,
                artifact_key="write_patch",
                label="Write state patch",
                artifact_status="provisional",
                path=write_patch_path,
                format="application/json",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(
                    phase="write",
                    current=artifact_state.current_prose_phase == "write",
                    superseded=artifact_state.current_prose_phase == "repair",
                    version_ns=artifact_state.write_version,
                ),
            )
        )
    repair_receipts: List[ProducedArtifactReceipt] = []
    if repair_prose_path is not None:
        repair_receipts.append(
            _receipt(
                book_root=book_root,
                artifact_key="repair_prose",
                label="Repaired prose",
                artifact_status="provisional",
                path=repair_prose_path,
                format="text/plain",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(
                    phase="repair",
                    current=artifact_state.current_prose_phase == "repair",
                    superseded=False,
                    version_ns=artifact_state.repair_version,
                ),
            )
        )
    if repair_patch_path is not None:
        repair_receipts.append(
            _receipt(
                book_root=book_root,
                artifact_key="repair_patch",
                label="Repair state patch",
                artifact_status="provisional",
                path=repair_patch_path,
                format="application/json",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(
                    phase="repair",
                    current=artifact_state.current_prose_phase == "repair",
                    superseded=False,
                    version_ns=artifact_state.repair_version,
                ),
            )
        )
    state_repair_receipts = (
        [
            _receipt(
                book_root=book_root,
                artifact_key="state_repair_patch",
                label="State repair patch",
                artifact_status="provisional",
                path=state_repair_patch_path,
                format="application/json",
                consumable=True,
                resumable=True,
                replaceable=True,
                details=_artifact_details(
                    phase="state_repair",
                    current=artifact_state.state_repair_current,
                    superseded=bool(state_repair_patch_path is not None and not artifact_state.state_repair_current),
                    version_ns=artifact_state.state_repair_version,
                ),
            )
        ]
        if state_repair_patch_path is not None
        else []
    )
    lint_receipts = (
        [
            _receipt(
                book_root=book_root,
                artifact_key="lint_report",
                label="Lint report",
                artifact_status="provisional",
                path=lint_report_path,
                format="application/json",
                consumable=True,
                resumable=True,
                replaceable=True,
                details={
                    **_artifact_details(
                        phase="lint",
                        current=artifact_state.lint_current,
                        superseded=bool(lint_report_path is not None and not artifact_state.lint_current),
                        version_ns=artifact_state.lint_version,
                    ),
                    "lint_status": artifact_state.lint_status,
                },
            )
        ]
        if lint_report_path is not None
        else []
    )
    committed_receipts: List[ProducedArtifactReceipt] = []
    if committed_prose_path is not None:
        committed_receipts.append(
            _receipt(
                book_root=book_root,
                artifact_key="scene_prose",
                label="Committed scene prose",
                artifact_status="authoritative",
                path=committed_prose_path,
                format="text/markdown",
                consumable=True,
                resumable=False,
                replaceable=False,
            )
        )
    if committed_meta_path is not None:
        committed_receipts.append(
            _receipt(
                book_root=book_root,
                artifact_key="scene_meta",
                label="Committed scene metadata",
                artifact_status="authoritative",
                path=committed_meta_path,
                format="application/json",
                consumable=True,
                resumable=False,
                replaceable=False,
            )
        )

    scene_status = "unstarted"
    if committed_receipts:
        scene_status = "committed"
    elif artifact_state.lint_current:
        scene_status = "lint_failed" if str(artifact_state.lint_status or "").lower() == "fail" else "linted"
    elif artifact_state.state_repair_current:
        scene_status = "state_repaired"
    elif artifact_state.current_prose_phase == "repair":
        scene_status = "repair_generated"
    elif artifact_state.current_prose_phase == "write":
        scene_status = "prose_generated"
    elif continuity_receipts:
        scene_status = "continuity_ready"
    elif preflight_receipts:
        scene_status = "preflighted"
    elif scene_card_receipts:
        scene_status = "planned"

    base_details = {
        "current_cursor_chapter": cursor_chapter,
        "current_cursor_scene": cursor_scene,
        "active_section_chapter": active_chapter,
        "active_section_id": active_section_id,
        "scene_ref_start": (active_section_status or {}).get("scene_ref_start"),
        "scene_ref_end": (active_section_status or {}).get("scene_ref_end"),
        "current_prose_phase": artifact_state.current_prose_phase,
        "state_repair_current": artifact_state.state_repair_current,
        "lint_current": artifact_state.lint_current,
        "lint_status": artifact_state.lint_status,
    }

    def build_action(
        *,
        action: str,
        mutation_scope: str,
        prerequisites: List[Tuple[str, bool]],
        existing_outputs: List[ProducedArtifactReceipt],
        superseded_outputs: Optional[List[ProducedArtifactReceipt]] = None,
        refusal_reason: Optional[str] = None,
        extra_details: Optional[Dict[str, Any]] = None,
    ) -> ScenePhaseActionReadiness:
        details = dict(base_details)
        if isinstance(extra_details, dict) and extra_details:
            details.update(extra_details)
        if superseded_outputs:
            details["superseded_outputs"] = [item.to_dict() for item in superseded_outputs]
        if scope_refusal:
            return ScenePhaseActionReadiness(
                action=action,
                legal=False,
                ready=False,
                mutation_scope=mutation_scope,
                missing_prerequisites=[label for label, present in prerequisites if not present],
                available_inputs=[label for label, present in prerequisites if present],
                existing_outputs=existing_outputs,
                refusal_reason=scope_refusal,
                details=details,
            )

        missing = [label for label, present in prerequisites if not present]
        available = [label for label, present in prerequisites if present]
        if existing_outputs:
            return ScenePhaseActionReadiness(
                action=action,
                legal=True,
                ready=False,
                mutation_scope=mutation_scope,
                missing_prerequisites=missing,
                available_inputs=available,
                existing_outputs=existing_outputs,
                refusal_reason=refusal_reason or f"{action} output already exists for the active scene.",
                details=details,
            )
        if missing:
            return ScenePhaseActionReadiness(
                action=action,
                legal=True,
                ready=False,
                mutation_scope=mutation_scope,
                missing_prerequisites=missing,
                available_inputs=available,
                existing_outputs=existing_outputs,
                refusal_reason=refusal_reason or f"{action} is missing required inputs.",
                details=details,
            )
        return ScenePhaseActionReadiness(
            action=action,
            legal=True,
            ready=True,
            mutation_scope=mutation_scope,
            missing_prerequisites=[],
            available_inputs=available,
            existing_outputs=existing_outputs,
            details=details,
        )

    current_prose_receipts = repair_receipts if artifact_state.current_prose_phase == "repair" else write_receipts
    current_prose_label, current_patch_label = _prose_labels(artifact_state)
    repair_ready = artifact_state.lint_current and str(artifact_state.lint_status or "").lower() == "fail" and artifact_state.lint_version > artifact_state.repair_version
    state_repair_stale = bool(state_repair_receipts and not artifact_state.state_repair_current)
    lint_stale = bool(lint_receipts and not artifact_state.lint_current)

    actions = [
        build_action(
            action="plan_scene",
            mutation_scope="provisional",
            prerequisites=[("outline_scene_context", True), ("state_base", True), ("active_frozen_section", active_section is not None)],
            existing_outputs=scene_card_receipts,
        ),
        build_action(
            action="preflight_scene_state",
            mutation_scope="provisional",
            prerequisites=[("scene_card", scene_card_path is not None), ("state_base", True)],
            existing_outputs=preflight_receipts,
        ),
        build_action(
            action="generate_continuity_pack",
            mutation_scope="derived",
            prerequisites=[("scene_card", scene_card_path is not None), ("preflight_patch", preflight_patch_path is not None)],
            existing_outputs=continuity_receipts,
        ),
        build_action(
            action="write_scene_prose",
            mutation_scope="provisional",
            prerequisites=[
                ("scene_card", scene_card_path is not None),
                ("preflight_patch", preflight_patch_path is not None),
                ("continuity_pack", continuity_pack_path is not None),
                ("style_anchor", style_anchor_exists),
            ],
            existing_outputs=committed_receipts or current_prose_receipts,
        ),
        build_action(
            action="state_repair_scene_patch",
            mutation_scope="provisional",
            prerequisites=[
                ("scene_card", scene_card_path is not None),
                ("preflight_patch", preflight_patch_path is not None),
                ("continuity_pack", continuity_pack_path is not None),
                (current_prose_label, artifact_state.current_prose_path is not None),
                (current_patch_label, artifact_state.current_patch_path is not None),
            ],
            existing_outputs=state_repair_receipts if not state_repair_stale else [],
            superseded_outputs=state_repair_receipts if state_repair_stale else [],
            refusal_reason="state_repair_scene_patch output already matches the latest provisional prose baseline.",
        ),
        build_action(
            action="lint_scene_prose",
            mutation_scope="provisional",
            prerequisites=[
                ("scene_card", scene_card_path is not None),
                ("preflight_patch", preflight_patch_path is not None),
                ("continuity_pack", continuity_pack_path is not None),
                (current_prose_label, artifact_state.current_prose_path is not None),
                ("state_repair_patch", artifact_state.state_repair_current),
            ],
            existing_outputs=lint_receipts if not lint_stale else [],
            superseded_outputs=lint_receipts if lint_stale else [],
            refusal_reason="lint_scene_prose output already matches the latest provisional state-repair patch.",
        ),
        build_action(
            action="repair_scene_prose",
            mutation_scope="provisional",
            prerequisites=[
                ("scene_card", scene_card_path is not None),
                (current_prose_label, artifact_state.current_prose_path is not None),
                ("repairable_lint_report", artifact_state.lint_current and str(artifact_state.lint_status or "").lower() == "fail"),
            ],
            existing_outputs=repair_receipts if not repair_ready and repair_receipts else [],
            refusal_reason=(
                "repair_scene_prose requires the latest lint report to fail before another repair pass can run."
                if artifact_state.lint_current and str(artifact_state.lint_status or "").lower() != "fail"
                else "repair_scene_prose output already matches the latest failing lint report."
            ),
            extra_details={"consumes_current_lint_status": artifact_state.lint_status},
        ),
        build_action(
            action="apply_scene_commit",
            mutation_scope="canonical",
            prerequisites=[
                ("scene_card", scene_card_path is not None),
                (current_prose_label, artifact_state.current_prose_path is not None),
                ("state_repair_patch", artifact_state.state_repair_current),
                ("passing_lint_report", artifact_state.lint_current and str(artifact_state.lint_status or "").lower() == "pass"),
            ],
            existing_outputs=committed_receipts,
            refusal_reason=(
                "apply_scene_commit requires the latest lint report to pass before canonical mutation can proceed."
                if artifact_state.lint_current and str(artifact_state.lint_status or "").lower() != "pass"
                else "apply_scene_commit output already exists for the active scene."
            ),
            extra_details={"consumes_current_lint_status": artifact_state.lint_status},
        ),
    ]

    recommended_next_action = next((item.action for item in actions if item.legal and item.ready), None)
    actions = [
        ScenePhaseActionReadiness(
            action=item.action,
            legal=item.legal,
            ready=item.ready,
            mutation_scope=item.mutation_scope,
            missing_prerequisites=item.missing_prerequisites,
            available_inputs=item.available_inputs,
            existing_outputs=item.existing_outputs,
            refusal_reason=item.refusal_reason,
            recommended=bool(recommended_next_action and item.action == recommended_next_action),
            details=item.details,
        )
        for item in actions
    ]

    return ScenePhaseReadiness(
        book_id=book_id,
        selector=selector,
        node=node,
        scene_status=scene_status,
        recommended_next_action=recommended_next_action,
        actions=actions,
        updated_at=_now_iso(),
    )
