from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from bookforge.contracts import MAIN_BRANCH_ID, RecoveryAnchor, RecoveryBranchHealth, RecoveryReceipt, RecoveryScope
from bookforge.supervision import paths as supervision_paths

from . import _common
from .outline_lineage import OutlineArtifactObservation, SectionLineageRow, get_outline_lineage_audit, get_section_lineage_matrix
from .workspace import current_execution_node


RECOVERY_DIRNAME = "recovery"
RECOVERY_MANIFEST_FILENAME = "recovery_manifest.json"
RECOVERY_RECEIPTS_FILENAME = "recovery_receipts.jsonl"
PROMOTION_REMOVALS_FILENAME = "promotion_removals.json"
SEMANTIC_REVIEW_FILENAME = "recovery_semantic_review.json"
DOWNSTREAM_REVIEW_FILENAME = "downstream_dependency_review.json"


@dataclass(frozen=True, slots=True)
class RecoveryAnchorCandidate:
    candidate_id: str
    anchor: RecoveryAnchor
    label: str
    description: str
    trust_level: str
    risk_level: str
    selectable: bool
    requires_human_decision: bool
    auto_selectable: bool
    affected_scopes: List[Dict[str, int]]
    evidence_paths: List[str] = field(default_factory=list)
    missing_scopes: List[Dict[str, int]] = field(default_factory=list)
    differing_scopes: List[Dict[str, int]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    schema_version: str = "recovery_anchor_candidate_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "anchor": self.anchor.to_dict(),
            "label": self.label,
            "description": self.description,
            "trust_level": self.trust_level,
            "risk_level": self.risk_level,
            "selectable": self.selectable,
            "requires_human_decision": self.requires_human_decision,
            "auto_selectable": self.auto_selectable,
            "affected_scopes": [dict(scope) for scope in self.affected_scopes],
            "evidence_paths": list(self.evidence_paths),
            "missing_scopes": [dict(scope) for scope in self.missing_scopes],
            "differing_scopes": [dict(scope) for scope in self.differing_scopes],
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class RecoveryAnchorCandidateReport:
    book_id: str
    branch_id: str
    status: str
    affected_scopes: List[Dict[str, int]]
    candidates: List[RecoveryAnchorCandidate]
    recommended_candidate_id: Optional[str]
    auto_selected_candidate_id: Optional[str]
    human_decision_required: bool
    decision_rule: str
    warnings: List[str] = field(default_factory=list)
    source: str = "bookforge.query.recovery.anchor_candidates.v1"
    schema_version: str = "recovery_anchor_candidate_report_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "source": self.source,
            "status": self.status,
            "affected_scopes": [dict(scope) for scope in self.affected_scopes],
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "recommended_candidate_id": self.recommended_candidate_id,
            "auto_selected_candidate_id": self.auto_selected_candidate_id,
            "human_decision_required": self.human_decision_required,
            "decision_rule": self.decision_rule,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class RecoveryPlanStep:
    order: int
    action: str
    summary: str
    command: Optional[str]
    mutation_class: str
    approval_required: bool
    expected_receipt: Optional[str]
    status: str = "planned"
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "recovery_plan_step_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "order": self.order,
            "action": self.action,
            "summary": self.summary,
            "command": self.command,
            "mutation_class": self.mutation_class,
            "approval_required": self.approval_required,
            "expected_receipt": self.expected_receipt,
            "status": self.status,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class RecoveryPlanPreview:
    book_id: str
    branch_id: Optional[str]
    status: str
    selected_anchor: Optional[RecoveryAnchor]
    affected_scopes: List[Dict[str, int]]
    steps: List[RecoveryPlanStep]
    blocked_reason: Optional[str]
    anchor_report: RecoveryAnchorCandidateReport
    approval_required: bool
    warnings: List[str] = field(default_factory=list)
    source: str = "bookforge.query.recovery.plan_preview.v1"
    schema_version: str = "recovery_plan_preview_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "source": self.source,
            "status": self.status,
            "selected_anchor": self.selected_anchor.to_dict() if self.selected_anchor else None,
            "affected_scopes": [dict(scope) for scope in self.affected_scopes],
            "steps": [step.to_dict() for step in self.steps],
            "blocked_reason": self.blocked_reason,
            "anchor_report": self.anchor_report.to_dict(),
            "approval_required": self.approval_required,
            "warnings": list(self.warnings),
        }


def recovery_dir(book_root: Path, branch_id: str) -> Path:
    return supervision_paths.branch_dir(book_root, branch_id) / RECOVERY_DIRNAME


def recovery_manifest_path(book_root: Path, branch_id: str) -> Path:
    return recovery_dir(book_root, branch_id) / RECOVERY_MANIFEST_FILENAME


def recovery_receipts_path(book_root: Path, branch_id: str) -> Path:
    return recovery_dir(book_root, branch_id) / RECOVERY_RECEIPTS_FILENAME


def promotion_removals_path(book_root: Path, branch_id: str) -> Path:
    return recovery_dir(book_root, branch_id) / PROMOTION_REMOVALS_FILENAME


def recovery_semantic_review_path(book_root: Path, branch_id: str) -> Path:
    return recovery_dir(book_root, branch_id) / SEMANTIC_REVIEW_FILENAME


def downstream_dependency_review_path(book_root: Path, branch_id: str) -> Path:
    return recovery_dir(book_root, branch_id) / DOWNSTREAM_REVIEW_FILENAME


def _book_root(workspace: Path, book_id: str) -> Path:
    return Path(workspace) / "books" / book_id


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_receipts(path: Path) -> List[RecoveryReceipt]:
    if not path.exists():
        return []
    receipts: List[RecoveryReceipt] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            receipts.append(RecoveryReceipt.from_dict(json.loads(line)))
        except (ValueError, json.JSONDecodeError):
            continue
    return receipts


def _relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _successful_recovery_actions(receipts: List[RecoveryReceipt]) -> set[str]:
    return {receipt.action for receipt in receipts if receipt.status in {"success", "no_op"}}


def get_recovery_manifest(workspace: Path, book_id: str, *, branch_id: str) -> Dict[str, Any]:
    resolved = str(branch_id or "").strip()
    if not resolved or resolved == MAIN_BRANCH_ID:
        return {}
    return _read_json(recovery_manifest_path(_book_root(workspace, book_id), resolved))


def get_recovery_anchor_candidates(
    workspace: Path,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> RecoveryAnchorCandidateReport:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    audit = get_outline_lineage_audit(workspace, book_id, branch_id=resolved_branch_id)
    matrix = audit.section_matrix or get_section_lineage_matrix(workspace, book_id, branch_id=resolved_branch_id)
    affected_rows = [row for row in matrix if row.suspected_contamination_class != "healthy"]
    affected_scopes = [{"chapter_id": row.chapter_id, "section_id": row.section_id} for row in affected_rows]
    candidates: List[RecoveryAnchorCandidate] = []
    if not affected_rows:
        candidates.append(
            RecoveryAnchorCandidate(
                candidate_id="inspect_only",
                anchor=RecoveryAnchor(anchor_type="shelf", description="No recovery anchor required."),
                label="No recovery required",
                description="No contaminated outline scopes were detected.",
                trust_level="high",
                risk_level="low",
                selectable=True,
                requires_human_decision=False,
                auto_selectable=True,
                affected_scopes=[],
                reasons=["outline lineage audit is healthy"],
            )
        )
        return RecoveryAnchorCandidateReport(
            book_id=book_id,
            branch_id=resolved_branch_id,
            status="healthy",
            affected_scopes=[],
            candidates=candidates,
            recommended_candidate_id="inspect_only",
            auto_selected_candidate_id="inspect_only",
            human_decision_required=False,
            decision_rule="No contaminated scopes were found; no recovery branch should be created.",
        )

    declared = _candidate_from_rows(
        "declared_source_run",
        label="Declared source run",
        anchor=RecoveryAnchor(
            anchor_type="declared_source_run",
            source_run_id=audit.declared_source_run_id,
            artifact_family="declared_source_run",
            description="Use the immutable outline run declared by the workflow registry.",
        ),
        rows=affected_rows,
        baseline_label="declared_source_run",
    )
    if declared:
        candidates.append(declared)

    if audit.latest_outline_run_id and audit.latest_outline_run_id != audit.declared_source_run_id:
        latest = _candidate_from_rows(
            "latest_outline_run",
            label="Latest outline run",
            anchor=RecoveryAnchor(
                anchor_type="latest_outline_run",
                source_run_id=audit.latest_outline_run_id,
                artifact_family="latest_outline_run",
                description="Use the latest immutable outline run present in the workspace.",
            ),
            rows=affected_rows,
            baseline_label="declared_source_run",
        )
        if latest:
            candidates.append(latest)

    frozen = _candidate_from_rows(
        "frozen_chapter_projection",
        label="Frozen chapter projection",
        anchor=RecoveryAnchor(
            anchor_type="frozen_chapter_projection",
            artifact_family="frozen_chapter_projection",
            description="Use frozen chapter projections already materialized in the section workflow.",
        ),
        rows=affected_rows,
        baseline_label="declared_source_run",
    )
    if frozen:
        candidates.append(frozen)

    selectable_non_shelf = [candidate for candidate in candidates if candidate.selectable and candidate.anchor.anchor_type != "shelf"]
    manual = RecoveryAnchorCandidate(
        candidate_id="manual_hybrid",
        anchor=RecoveryAnchor(anchor_type="manual_hybrid", description="Human-selected hybrid timeline; BookForge will not auto-select this."),
        label="Manual hybrid",
        description="Use only when multiple coherent timelines contain material worth manually reconciling.",
        trust_level="unknown",
        risk_level="high",
        selectable=True,
        requires_human_decision=True,
        auto_selectable=False,
        affected_scopes=affected_scopes,
        reasons=["manual hybrid requires explicit author/operator decision"],
    )
    shelf = RecoveryAnchorCandidate(
        candidate_id="shelf",
        anchor=RecoveryAnchor(anchor_type="shelf", description="Do not repair automatically."),
        label="Shelf book",
        description="Leave the book unchanged when no timeline anchor is trustworthy.",
        trust_level="safe_no_mutation",
        risk_level="low",
        selectable=True,
        requires_human_decision=True,
        auto_selectable=False,
        affected_scopes=affected_scopes,
        reasons=["shelving avoids further canonical mutation"],
    )
    candidates.extend([manual, shelf])
    recommended = _recommended_anchor_candidate(candidates)
    auto_selected = _auto_selected_anchor_id(selectable_non_shelf)
    manual_needed = auto_selected is None
    return RecoveryAnchorCandidateReport(
        book_id=book_id,
        branch_id=resolved_branch_id,
        status="auto_selected" if auto_selected else "needs_human_choice",
        affected_scopes=affected_scopes,
        candidates=candidates,
        recommended_candidate_id=recommended.candidate_id if recommended else None,
        auto_selected_candidate_id=auto_selected,
        human_decision_required=manual_needed,
        decision_rule=(
            "Only one coherent non-shelf timeline is selectable; Nanda may auto-select it."
            if auto_selected
            else "Multiple or zero coherent non-shelf timeline anchors exist; Nanda must ask the user which timeline to inhabit."
        ),
        warnings=_anchor_warnings(audit, candidates),
    )


def get_recovery_plan_preview(
    workspace: Path,
    book_id: str,
    *,
    anchor_type: Optional[str] = None,
    source_run_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    salvage_policy: str = "none",
) -> RecoveryPlanPreview:
    report = get_recovery_anchor_candidates(workspace, book_id)
    selected = _selected_anchor_from_report(report, anchor_type=anchor_type, source_run_id=source_run_id)
    if selected is None:
        return RecoveryPlanPreview(
            book_id=book_id,
            branch_id=branch_id,
            status="needs_anchor_decision",
            selected_anchor=None,
            affected_scopes=report.affected_scopes,
            steps=[],
            blocked_reason="No recovery anchor was selected and BookForge could not auto-select exactly one safe non-shelf anchor.",
            anchor_report=report,
            approval_required=True,
            warnings=list(report.warnings),
        )
    if selected.anchor_type == "shelf":
        return RecoveryPlanPreview(
            book_id=book_id,
            branch_id=branch_id,
            status="shelf_recommended",
            selected_anchor=selected,
            affected_scopes=report.affected_scopes,
            steps=[
                RecoveryPlanStep(
                    order=1,
                    action="shelf_book",
                    summary="Do not mutate BookForge state. Keep the book quarantined for manual review.",
                    command=None,
                    mutation_class="no_op",
                    approval_required=False,
                    expected_receipt=None,
                )
            ],
            blocked_reason=None,
            anchor_report=report,
            approval_required=False,
            warnings=list(report.warnings),
        )
    branch_arg = branch_id or "<new-recovery-branch>"
    affected_args = " ".join(f"--affected-scope {scope['chapter_id']}:{scope['section_id']}" for scope in report.affected_scopes)
    source_arg = f" --source-run-id {selected.source_run_id}" if selected.source_run_id else ""
    branch_opt = f" --branch-id {branch_id}" if branch_id else ""
    create_command = (
        f"bookforge workflow create-recovery-branch --book {book_id} --anchor-type {selected.anchor_type}"
        f"{source_arg}{branch_opt} --salvage-policy {salvage_policy} {affected_args}".strip()
    )
    branch_initial_state = {
        "cleanliness_status": "isolated_not_clean",
        "note": (
            "Branch creation snapshots current main and materializes outline evidence. "
            "The selected anchor is recorded for later normalization; it is not applied by branch creation."
        ),
        "cleanup_required_before_clean": [
            "quarantine_artifacts",
            "normalize_outline_scope",
            "invalidate_scope_outputs",
            "rebuild_state_scope",
            "redraft_scope",
            "validate_recovery_branch",
        ],
    }
    steps = [
        RecoveryPlanStep(
            1,
            "create_recovery_branch",
            "Create isolated recovery branch and record selected anchor; branch is not clean until later recovery steps complete.",
            create_command,
            "branch_mutation",
            True,
            "execution_result_v1",
            details={"branch_initial_state": branch_initial_state},
        ),
        RecoveryPlanStep(2, "quarantine_artifacts", "Quarantine polluted/stale outline artifacts inside the recovery branch.", f"bookforge workflow quarantine-artifacts --book {book_id} --branch-id {branch_arg}", "branch_mutation", True, "recovery_receipt_v1"),
        RecoveryPlanStep(3, "normalize_outline_scope", "Normalize affected outline scopes from the selected anchor.", f"bookforge workflow normalize-outline-scope --book {book_id} --branch-id {branch_arg}", "branch_mutation", True, "recovery_receipt_v1"),
        RecoveryPlanStep(4, "invalidate_scope_outputs", "Invalidate prose/state/projection outputs made untrustworthy by the repaired outline.", f"bookforge workflow invalidate-scope-outputs --book {book_id} --branch-id {branch_arg}", "branch_mutation", True, "recovery_receipt_v1"),
        RecoveryPlanStep(5, "rebuild_state_scope", "Rebuild branch-local state and projections for the repaired timeline.", f"bookforge workflow rebuild-state-scope --book {book_id} --branch-id {branch_arg}", "branch_mutation", False, "recovery_receipt_v1"),
        RecoveryPlanStep(6, "redraft_scope", "Redraft impacted prose scopes against the normalized outline.", f"bookforge workflow redraft-scope --book {book_id} --branch-id {branch_arg}", "branch_mutation", True, "recovery_receipt_v1"),
        RecoveryPlanStep(7, "review_recovery_semantics", "Run semantic recovery review before validation.", f"bookforge workflow review-recovery-semantics --book {book_id} --branch-id {branch_arg}", "diagnostic_only", False, "recovery_receipt_v1"),
        RecoveryPlanStep(8, "review_downstream_dependencies", "Review downstream dependency risk after redraft.", f"bookforge workflow review-downstream-dependencies --book {book_id} --branch-id {branch_arg}", "diagnostic_only", False, "recovery_receipt_v1"),
        RecoveryPlanStep(9, "validate_recovery_branch", "Validate branch health before promotion.", f"bookforge workflow validate-recovery-branch --book {book_id} --branch-id {branch_arg}", "diagnostic_only", False, "execution_result_v1"),
        RecoveryPlanStep(10, "promote_recovery_branch", "Promote validated branch to main and apply recorded removals.", f"bookforge workflow promote-recovery-branch --book {book_id} --branch-id {branch_arg}", "promotion", True, "execution_result_v1"),
    ]
    return RecoveryPlanPreview(
        book_id=book_id,
        branch_id=branch_id,
        status="ready",
        selected_anchor=selected,
        affected_scopes=report.affected_scopes,
        steps=steps,
        blocked_reason=None,
        anchor_report=report,
        approval_required=True,
        warnings=list(report.warnings),
    )


def _scope_dict(row: SectionLineageRow) -> Dict[str, int]:
    return {"chapter_id": int(row.chapter_id), "section_id": int(row.section_id)}


def _observation(row: SectionLineageRow, label: str) -> Optional[OutlineArtifactObservation]:
    return next((item for item in row.candidate_artifacts if item.label == label), None)


def _candidate_from_rows(
    candidate_id: str,
    *,
    label: str,
    anchor: RecoveryAnchor,
    rows: List[SectionLineageRow],
    baseline_label: str,
) -> Optional[RecoveryAnchorCandidate]:
    if not rows:
        return None
    missing: List[Dict[str, int]] = []
    differing: List[Dict[str, int]] = []
    paths: List[str] = []
    reasons: List[str] = []
    for row in rows:
        candidate = _observation(row, candidate_id)
        baseline = _observation(row, baseline_label)
        scope = _scope_dict(row)
        if candidate is None or not candidate.exists or not candidate.section_hash:
            missing.append(scope)
            continue
        if candidate.path:
            paths.append(candidate.path)
        if baseline and baseline.section_hash and candidate.section_hash != baseline.section_hash:
            differing.append(scope)
    selectable = not missing
    if missing:
        reasons.append(f"missing candidate data for {len(missing)} affected scope(s)")
    if differing:
        reasons.append(f"differs from declared source run in {len(differing)} affected scope(s)")
    if selectable and not differing:
        reasons.append("candidate matches declared source run for all affected scopes")
    elif selectable:
        reasons.append("candidate is complete but represents a different timeline than the declared source run")
    trust = _candidate_trust(candidate_id, selectable=selectable, differing=differing)
    risk = "low" if trust == "high" else "medium" if trust in {"medium", "complete_different_timeline"} else "high"
    return RecoveryAnchorCandidate(
        candidate_id=candidate_id,
        anchor=anchor,
        label=label,
        description=anchor.description or label,
        trust_level=trust,
        risk_level=risk,
        selectable=selectable,
        requires_human_decision=bool(differing) or trust != "high",
        auto_selectable=selectable and trust == "high",
        affected_scopes=[_scope_dict(row) for row in rows],
        evidence_paths=sorted(set(paths)),
        missing_scopes=missing,
        differing_scopes=differing,
        reasons=reasons,
    )


def _candidate_trust(candidate_id: str, *, selectable: bool, differing: List[Dict[str, int]]) -> str:
    if not selectable:
        return "incomplete"
    if candidate_id == "declared_source_run":
        return "high"
    if differing:
        return "complete_different_timeline"
    if candidate_id == "frozen_chapter_projection":
        return "medium"
    return "medium"


def _recommended_anchor_candidate(candidates: List[RecoveryAnchorCandidate]) -> Optional[RecoveryAnchorCandidate]:
    selectable = [candidate for candidate in candidates if candidate.selectable and candidate.anchor.anchor_type not in {"manual_hybrid", "shelf"}]
    if not selectable:
        return next((candidate for candidate in candidates if candidate.candidate_id == "shelf"), None)
    ranked = {"high": 0, "medium": 1, "complete_different_timeline": 2, "incomplete": 3}
    return sorted(selectable, key=lambda item: (ranked.get(item.trust_level, 99), item.risk_level, item.candidate_id))[0]


def _auto_selected_anchor_id(selectable_non_shelf: List[RecoveryAnchorCandidate]) -> Optional[str]:
    if len(selectable_non_shelf) == 1 and selectable_non_shelf[0].auto_selectable:
        return selectable_non_shelf[0].candidate_id
    declared = next((candidate for candidate in selectable_non_shelf if candidate.candidate_id == "declared_source_run"), None)
    if declared is not None and declared.auto_selectable:
        alternate_timelines = [
            candidate for candidate in selectable_non_shelf
            if candidate.candidate_id != declared.candidate_id and candidate.differing_scopes
        ]
        if not alternate_timelines:
            return declared.candidate_id
    return None


def _anchor_warnings(audit: Any, candidates: List[RecoveryAnchorCandidate]) -> List[str]:
    warnings: List[str] = []
    if audit.first_visible_story_divergence:
        warnings.append("visible_story_divergence_detected")
    if audit.character_cohort_conflicts:
        warnings.append("character_cohort_conflicts_detected")
    selectable = [candidate for candidate in candidates if candidate.selectable and candidate.anchor.anchor_type not in {"manual_hybrid", "shelf"}]
    if len(selectable) > 1:
        if any(candidate.differing_scopes for candidate in selectable):
            warnings.append("multiple_selectable_timeline_anchors")
        else:
            warnings.append("multiple_selectable_artifact_anchors_same_timeline")
    if not selectable:
        warnings.append("no_selectable_timeline_anchor")
    return _dedupe(warnings)


def _selected_anchor_from_report(
    report: RecoveryAnchorCandidateReport,
    *,
    anchor_type: Optional[str],
    source_run_id: Optional[str],
) -> Optional[RecoveryAnchor]:
    if anchor_type:
        for candidate in report.candidates:
            if candidate.anchor.anchor_type != anchor_type:
                continue
            if source_run_id and candidate.anchor.source_run_id != source_run_id:
                continue
            if candidate.selectable:
                return candidate.anchor
        return None
    if report.auto_selected_candidate_id:
        for candidate in report.candidates:
            if candidate.candidate_id == report.auto_selected_candidate_id:
                return candidate.anchor
    return None


def _dedupe(values: List[str]) -> List[str]:
    seen: set[str] = set()
    deduped: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _parse_scene_ref(value: Any) -> Optional[int]:
    text = str(value or "").strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    try:
        number = int(text)
    except (TypeError, ValueError):
        return None
    return number if number >= 1 else None


def _scene_ids_for_section(registry: Dict[str, Any], chapter_id: int, section_id: int) -> List[int]:
    chapters = registry.get("chapters") if isinstance(registry.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict) or _common.coerce_int(chapter.get("chapter_id")) != int(chapter_id):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict) or _common.coerce_int(section.get("section_id")) != int(section_id):
                continue
            start = _parse_scene_ref(section.get("scene_ref_start"))
            end = _parse_scene_ref(section.get("scene_ref_end"))
            if start is None or end is None or end < start:
                return []
            return list(range(start, end + 1))
    return []


def _scope_key(chapter_id: int, section_id: Optional[int]) -> str:
    if section_id is None:
        return f"ch_{int(chapter_id):03d}"
    return f"ch_{int(chapter_id):03d}_sec_{int(section_id):03d}"


def _scene_ids_from_manifest_range(manifest: Dict[str, Any], chapter_id: int, section_id: Optional[int]) -> List[int]:
    ranges = manifest.get("scope_output_ranges") if isinstance(manifest.get("scope_output_ranges"), dict) else {}
    row = ranges.get(_scope_key(chapter_id, section_id)) if isinstance(ranges, dict) else None
    if not isinstance(row, dict):
        return []
    scene_ids: List[int] = []
    for value in row.get("scene_ids") or []:
        try:
            scene_id = int(value)
        except (TypeError, ValueError):
            continue
        if scene_id >= 1:
            scene_ids.append(scene_id)
    return sorted(set(scene_ids))


def get_scope_invalidation_preview(
    workspace: Path,
    book_id: str,
    *,
    branch_id: str,
    scope: Optional[RecoveryScope] = None,
) -> Dict[str, Any]:
    book_root = _book_root(workspace, book_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    if scope is None and isinstance(manifest.get("scope"), dict):
        try:
            scope = RecoveryScope.from_dict(manifest["scope"])
        except ValueError:
            scope = None
    execution_root = _common.execution_book_root(book_root, branch_id)
    affected = scope.affected_scopes if scope is not None else []
    paths: List[str] = []
    registry = _common.load_registry(execution_root)
    for item in affected:
        chapter_id = int(item["chapter_id"])
        section_id = item.get("section_id")
        chapter_dir = execution_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
        if not chapter_dir.exists():
            continue
        if section_id is None:
            paths.extend(path.relative_to(execution_root).as_posix() for path in sorted(chapter_dir.glob("scene_*")) if path.is_file())
            for suffix in (".md", ".provisional.md", ".fixed.md", ".original.md", ".seam_report.json"):
                chapter_file = execution_root / "draft" / "chapters" / f"ch_{chapter_id:03d}{suffix}"
                if chapter_file.exists():
                    paths.append(chapter_file.relative_to(execution_root).as_posix())
            continue
        scene_ids = _scene_ids_from_manifest_range(manifest, chapter_id, int(section_id))
        if not scene_ids:
            scene_ids = _scene_ids_for_section(registry, chapter_id, int(section_id))
        for scene_id in scene_ids:
            for path in sorted(chapter_dir.glob(f"scene_{scene_id:03d}*")):
                if path.is_file():
                    paths.append(path.relative_to(execution_root).as_posix())
    return {
        "schema_version": "scope_invalidation_preview_v1",
        "book_id": book_id,
        "branch_id": branch_id,
        "affected_scopes": [dict(item) for item in affected],
        "candidate_paths": sorted(set(paths)),
    }


def _prose_paths_for_scopes(execution_root: Path, manifest: Dict[str, Any], scopes: List[Dict[str, int]]) -> List[str]:
    paths: List[str] = []
    registry = _common.load_registry(execution_root)
    for item in scopes:
        chapter_id = int(item["chapter_id"])
        section_id = item.get("section_id")
        chapter_dir = execution_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
        if not chapter_dir.exists():
            continue
        if section_id is None:
            paths.extend(path.relative_to(execution_root).as_posix() for path in sorted(chapter_dir.glob("scene_*")) if path.is_file())
            for suffix in (".md", ".provisional.md", ".fixed.md", ".original.md", ".seam_report.json"):
                chapter_file = execution_root / "draft" / "chapters" / f"ch_{chapter_id:03d}{suffix}"
                if chapter_file.exists():
                    paths.append(chapter_file.relative_to(execution_root).as_posix())
            continue
        scene_ids = _scene_ids_from_manifest_range(manifest, chapter_id, int(section_id))
        if not scene_ids:
            scene_ids = _scene_ids_for_section(registry, chapter_id, int(section_id))
        for scene_id in scene_ids:
            for path in sorted(chapter_dir.glob(f"scene_{scene_id:03d}*")):
                if path.is_file():
                    paths.append(path.relative_to(execution_root).as_posix())
    return sorted(set(paths))


def _append_files_under(root: Path, rel_dir: str, paths: List[str]) -> None:
    base = root / rel_dir
    if not base.exists():
        return
    if base.is_file():
        paths.append(rel_dir)
        return
    for path in sorted(base.rglob("*")):
        if path.is_file():
            paths.append(path.relative_to(root).as_posix())


def _affected_chapters(scope: Optional[RecoveryScope]) -> List[int]:
    if scope is None:
        return []
    chapters = []
    for item in scope.affected_scopes + scope.downstream_scopes:
        try:
            chapters.append(int(item["chapter_id"]))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(set(chapter for chapter in chapters if chapter >= 1))


def _affected_scene_ids(manifest: Dict[str, Any], scope: Optional[RecoveryScope], registry: Dict[str, Any]) -> Dict[int, List[int]]:
    scene_ids_by_chapter: Dict[int, List[int]] = {}
    if scope is None:
        return scene_ids_by_chapter
    for item in scope.affected_scopes + scope.downstream_scopes:
        try:
            chapter_id = int(item["chapter_id"])
        except (KeyError, TypeError, ValueError):
            continue
        section_id = item.get("section_id")
        if section_id is None:
            continue
        scene_ids = _scene_ids_from_manifest_range(manifest, chapter_id, int(section_id))
        if not scene_ids:
            scene_ids = _scene_ids_for_section(registry, chapter_id, int(section_id))
        if scene_ids:
            current = scene_ids_by_chapter.setdefault(chapter_id, [])
            current.extend(scene_ids)
    return {chapter: sorted(set(scene_ids)) for chapter, scene_ids in scene_ids_by_chapter.items()}


def get_state_rebuild_preview(
    workspace: Path,
    book_id: str,
    *,
    branch_id: str,
) -> Dict[str, Any]:
    resolved = str(branch_id or "").strip()
    book_root = _book_root(workspace, book_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=resolved) if resolved else {}
    scope: Optional[RecoveryScope] = None
    if isinstance(manifest.get("scope"), dict):
        try:
            scope = RecoveryScope.from_dict(manifest["scope"])
        except ValueError:
            scope = None
    execution_root = _common.execution_book_root(book_root, resolved or MAIN_BRANCH_ID)
    registry = _common.load_registry(execution_root)
    affected_chapters = _affected_chapters(scope)
    scene_ids_by_chapter = _affected_scene_ids(manifest, scope, registry)
    paths: List[str] = []

    for rel_path in (
        "state.json",
        "draft/context/bible.md",
        "draft/context/last_excerpt.md",
        "draft/context/continuity_pack.json",
        "draft/context/run_paused.json",
        "draft/context/item_registry.json",
        "draft/context/plot_devices.json",
        "draft/context/durable_commits.json",
    ):
        if (execution_root / rel_path).exists():
            paths.append(rel_path)

    for rel_dir in (
        "draft/context/characters",
        "draft/context/continuity_history",
        "draft/context/items",
        "draft/context/plot_devices",
    ):
        _append_files_under(execution_root, rel_dir, paths)

    for chapter_id in affected_chapters:
        for rel_path in (
            f"draft/context/chapter_summaries/ch_{chapter_id:03d}.json",
            f"draft/context/chapter_seams/ch_{chapter_id:03d}",
            f"draft/context/settings/ch_{chapter_id:03d}",
            f"draft/context/appearance/ch_{chapter_id:03d}",
        ):
            _append_files_under(execution_root, rel_path, paths)
        for scene_id in scene_ids_by_chapter.get(chapter_id, []):
            for rel_path in (
                f"draft/context/phase_history/ch{chapter_id:03d}_sc{scene_id:03d}.json",
                f"draft/context/phase_history/ch{chapter_id:03d}_sc{scene_id:03d}",
            ):
                _append_files_under(execution_root, rel_path, paths)
    return {
        "schema_version": "state_rebuild_preview_v1",
        "book_id": book_id,
        "branch_id": resolved,
        "rebuild_mode": "full_book_context_reset_from_normalized_outline",
        "affected_scopes": [dict(item) for item in scope.affected_scopes] if scope is not None else [],
        "downstream_scopes": [dict(item) for item in scope.downstream_scopes] if scope is not None else [],
        "affected_chapters": affected_chapters,
        "affected_scene_ids": {str(key): value for key, value in scene_ids_by_chapter.items()},
        "candidate_paths": sorted(set(paths)),
        "rebuilt_outputs": [
            "state.json",
            "draft/context/characters/index.json",
            "draft/context/bible.md",
            "draft/context/last_excerpt.md",
            "draft/context/item_registry.json",
            "draft/context/plot_devices.json",
            "draft/context/durable_commits.json",
            "draft/context/items/index.json",
            "draft/context/plot_devices/index.json",
        ],
    }


def _impact_item(
    *,
    family: str,
    rel_path: str,
    root: Path,
    recommended_action: str,
    mutation_supported: bool,
    note: str,
) -> Dict[str, Any]:
    return {
        "family": family,
        "path": rel_path,
        "artifact_status": "diagnostic",
        "exists": (root / rel_path).exists(),
        "safe_as_canonical": False,
        "recommended_action": recommended_action,
        "mutation_supported": mutation_supported,
        "note": note,
    }


def _classify_state_family(rel_path: str) -> str:
    path = rel_path.replace("\\", "/")
    if path.startswith("draft/context/chapter_summaries/") or path.startswith("draft/context/chapter_seams/"):
        return "continuity"
    if path.startswith("draft/context/continuity_history/") or path in {"draft/context/bible.md", "draft/context/last_excerpt.md"}:
        return "continuity"
    if path.startswith("draft/context/settings/") or path.startswith("draft/context/appearance/"):
        return "projection"
    if path.startswith("draft/context/phase_history/"):
        return "projection"
    return "state"


def _series_candidate_paths(workspace: Path, execution_root: Path) -> List[str]:
    book_payload = _read_json(execution_root / "book.json")
    series_ref = str(book_payload.get("series_ref") or "").strip()
    series_id = str(book_payload.get("series_id") or "").strip()
    if series_ref:
        series_root = workspace / series_ref
        rel_prefix = series_ref.replace("\\", "/").strip("/")
    elif series_id:
        series_root = workspace / "series" / series_id
        rel_prefix = f"series/{series_id}"
    else:
        return []
    if not series_root.exists():
        return []
    paths: List[str] = []
    for path in sorted(series_root.rglob("*")):
        if path.is_file():
            paths.append(f"{rel_prefix}/{path.relative_to(series_root).as_posix()}")
    return paths


def _blast_radius_scope_groups(scope: Optional[RecoveryScope]) -> Dict[str, Any]:
    affected = [dict(item) for item in scope.affected_scopes] if scope is not None else []
    downstream = [dict(item) for item in scope.downstream_scopes] if scope is not None else []
    return {
        "affected": affected,
        "downstream": downstream,
        "prose_invalidation_scope": affected,
        "state_rebuild_scope": affected + downstream,
        "downstream_trace_status": "manifest_declared_only" if downstream else "none_declared",
        "downstream_trace_note": (
            "Downstream scopes are declared by the recovery manifest; semantic dependency tracing after redraft is not implemented yet."
            if downstream
            else "No downstream scopes are declared by the recovery manifest."
        ),
    }


def get_recovery_blast_radius(
    workspace: Path,
    book_id: str,
    *,
    branch_id: str,
) -> Dict[str, Any]:
    resolved = str(branch_id or "").strip()
    book_root = _book_root(workspace, book_id)
    execution_root = _common.execution_book_root(book_root, resolved or MAIN_BRANCH_ID)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=resolved) if resolved else {}
    scope: Optional[RecoveryScope] = None
    if isinstance(manifest.get("scope"), dict):
        try:
            scope = RecoveryScope.from_dict(manifest["scope"])
        except ValueError:
            scope = None
    prose_preview = get_scope_invalidation_preview(workspace, book_id, branch_id=resolved, scope=scope)
    state_preview = get_state_rebuild_preview(workspace, book_id, branch_id=resolved)
    impacts: List[Dict[str, Any]] = []

    for rel_path in prose_preview.get("candidate_paths") or []:
        impacts.append(
            _impact_item(
                family="prose",
                rel_path=str(rel_path),
                root=execution_root,
                recommended_action="invalidate_scope_outputs",
                mutation_supported=True,
                note="Affected branch-local prose/generated scene artifact; quarantine before redraft.",
            )
        )

    for rel_path in state_preview.get("candidate_paths") or []:
        family = _classify_state_family(str(rel_path))
        impacts.append(
            _impact_item(
                family=family,
                rel_path=str(rel_path),
                root=execution_root,
                recommended_action="rebuild_state_scope",
                mutation_supported=True,
                note="Affected branch-local state/projection artifact; quarantine before rebuilding branch state.",
            )
        )

    for rel_path in _series_candidate_paths(workspace, execution_root):
        impacts.append(
            {
                "family": "series",
                "path": rel_path,
                "artifact_status": "diagnostic",
                "exists": (Path(workspace) / rel_path).exists(),
                "safe_as_canonical": False,
                "recommended_action": "future_series_scope_rebuild",
                "mutation_supported": False,
                "note": "Series canon is outside the current recovery branch mutation set; Nanda should include it in impact reports when timeline facts changed.",
            }
        )

    downstream_scopes = [dict(item) for item in scope.downstream_scopes] if scope is not None else []
    for rel_path in _prose_paths_for_scopes(execution_root, manifest, downstream_scopes):
        impacts.append(
            {
                "family": "downstream_review",
                "path": rel_path,
                "artifact_status": "diagnostic",
                "exists": (execution_root / rel_path).exists(),
                "safe_as_canonical": False,
                "recommended_action": "author_review_downstream_scope",
                "mutation_supported": False,
                "note": "Manifest-declared downstream scope artifact; review after recovery/redraft before treating downstream continuity as trusted.",
            }
        )

    families: Dict[str, Dict[str, Any]] = {}
    for impact in impacts:
        family = str(impact.get("family") or "unknown")
        row = families.setdefault(
            family,
            {
                "candidate_count": 0,
                "paths": [],
                "mutation_supported": bool(impact.get("mutation_supported")),
                "recommended_actions": [],
            },
        )
        row["candidate_count"] += 1
        row["paths"].append(impact["path"])
        action = str(impact.get("recommended_action") or "").strip()
        if action and action not in row["recommended_actions"]:
            row["recommended_actions"].append(action)
        row["mutation_supported"] = bool(row["mutation_supported"]) or bool(impact.get("mutation_supported"))

    return {
        "schema_version": "recovery_blast_radius_v1",
        "book_id": book_id,
        "branch_id": resolved,
        "affected_scopes": [dict(item) for item in scope.affected_scopes] if scope is not None else [],
        "downstream_scopes": [dict(item) for item in scope.downstream_scopes] if scope is not None else [],
        "scope_groups": _blast_radius_scope_groups(scope),
        "families": families,
        "artifact_impacts": impacts,
        "total_candidate_count": len(impacts),
        "mutation_supported_families": sorted(family for family, row in families.items() if row.get("mutation_supported")),
        "unsupported_families": sorted(family for family, row in families.items() if not row.get("mutation_supported")),
    }


def get_salvage_candidates(workspace: Path, book_id: str, *, scope: RecoveryScope) -> Dict[str, Any]:
    book_root = _book_root(workspace, book_id)
    preview = get_scope_invalidation_preview(workspace, book_id, branch_id=MAIN_BRANCH_ID, scope=scope)
    candidates = [
        {
            "path": rel_path,
            "artifact_status": "diagnostic",
            "salvage_policy": scope.salvage_policy,
            "safe_as_canonical": False,
        }
        for rel_path in preview["candidate_paths"]
        if (book_root / rel_path).is_file()
    ]
    return {
        "schema_version": "salvage_candidates_v1",
        "book_id": book_id,
        "affected_scopes": [dict(item) for item in scope.affected_scopes],
        "candidates": candidates,
    }


def get_recovery_plan_readiness(
    workspace: Path,
    book_id: str,
    *,
    branch_id: str,
    impact_report_ref: Optional[str] = None,
) -> Dict[str, Any]:
    resolved = str(branch_id or "").strip()
    audit = get_outline_lineage_audit(workspace, book_id, branch_id=MAIN_BRANCH_ID)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=resolved) if resolved else {}
    blockers: List[str] = []
    if not resolved or resolved == MAIN_BRANCH_ID:
        blockers.append("recovery requires a derived branch")
    if audit.status == "healthy" and not manifest:
        blockers.append("no contaminated lineage is present on main")
    if not manifest:
        blockers.append("recovery branch manifest is missing")
    scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
    affected_scopes = [dict(item) for item in scope.get("affected_scopes", []) if isinstance(item, dict)]
    approval_reasons = []
    if manifest:
        anchor = manifest.get("anchor") if isinstance(manifest.get("anchor"), dict) else {}
        if anchor.get("anchor_type"):
            approval_reasons.append("recovery anchor selection")
        if len(affected_scopes) > 1 or any("section_id" not in item for item in affected_scopes):
            approval_reasons.append("broad recovery radius")
    return {
        "schema_version": "recovery_plan_readiness_v1",
        "book_id": book_id,
        "branch_id": resolved,
        "ready": not blockers,
        "blockers": blockers,
        "impact_report_ref": impact_report_ref,
        "main_integrity_status": audit.status,
        "manifest_present": bool(manifest),
        "affected_scopes": affected_scopes,
        "approval_required": bool(approval_reasons),
        "approval_reasons": approval_reasons,
        "recommended_next_action": "normalize_outline_scope" if not blockers else "create_recovery_branch",
    }


def _recommended_next_recovery_action(actions: set[str], blockers: List[str]) -> str:
    if "create_recovery_branch" not in actions:
        return "create_recovery_branch"
    if "quarantine_artifacts" not in actions:
        return "quarantine_artifacts"
    if "normalize_outline_scope" not in actions:
        return "normalize_outline_scope"
    if "invalidate_scope_outputs" not in actions:
        return "invalidate_scope_outputs"
    if "rebuild_state_scope" not in actions:
        return "rebuild_state_scope"
    if "redraft_scope" not in actions:
        return "redraft_scope"
    if "validate_recovery_branch" not in actions:
        return "validate_recovery_branch"
    if blockers:
        return "inspect_recovery_blockers"
    return "promote_recovery_branch"


def _recovery_approval_requirements(manifest: Dict[str, Any], actions: set[str]) -> Dict[str, Any]:
    scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
    affected_scopes = [dict(item) for item in scope.get("affected_scopes", []) if isinstance(item, dict)]
    broad_scope = len(affected_scopes) > 1 or any("section_id" not in item for item in affected_scopes)
    pending = []
    if "create_recovery_branch" in actions:
        pending.append("recovery anchor selection")
    if "quarantine_artifacts" not in actions:
        pending.append("destructive cleanup/quarantine")
    if "invalidate_scope_outputs" not in actions:
        pending.append("scope output invalidation")
    if "rebuild_state_scope" not in actions:
        pending.append("state/projection rebuild")
    if "redraft_scope" not in actions:
        pending.append("scope redraft")
    if "validate_recovery_branch" in actions:
        pending.append("promotion to main")
    if broad_scope:
        pending.append("broad recovery radius")
    return {
        "approval_required": bool(pending),
        "approval_reasons": sorted(set(pending)),
        "broad_recovery_radius": broad_scope,
        "affected_scopes": affected_scopes,
    }


def get_recovery_semantic_review_readiness(workspace: Path, book_id: str, *, branch_id: str) -> Dict[str, Any]:
    resolved = str(branch_id or "").strip()
    book_root = _book_root(workspace, book_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=resolved) if resolved else {}
    receipts = _read_receipts(recovery_receipts_path(book_root, resolved)) if resolved else []
    successful_actions = _successful_recovery_actions(receipts)
    review_path = recovery_semantic_review_path(book_root, resolved) if resolved else book_root / SEMANTIC_REVIEW_FILENAME
    health = get_recovery_branch_health(workspace, book_id, branch_id=resolved) if resolved else None

    blockers: List[str] = []
    if not resolved or resolved == MAIN_BRANCH_ID:
        blockers.append("semantic recovery review requires a derived recovery branch")
    if not manifest:
        blockers.append("recovery branch manifest is missing")

    for required in (
        "create_recovery_branch",
        "quarantine_artifacts",
        "normalize_outline_scope",
        "invalidate_scope_outputs",
        "rebuild_state_scope",
        "redraft_scope",
        "validate_recovery_branch",
    ):
        if required not in successful_actions:
            blockers.append(f"missing successful receipt: {required}")

    if health is not None and health.status != "healthy":
        blockers.append("recovery branch structural health is not healthy")

    structural_health_status = health.status if health is not None else "unknown"
    semantic_validation = (
        health.details.get("semantic_validation")
        if health is not None and isinstance(health.details.get("semantic_validation"), dict)
        else None
    )
    review_exists = review_path.exists() if resolved else False
    present_outputs = []
    if review_exists:
        present_outputs.append(
            {
                "path": _relpath(review_path, book_root),
                "artifact_status": "diagnostic",
                "family": "semantic_recovery_review",
            }
        )

    next_action = "review_recovery_semantics" if not blockers else _recommended_next_recovery_action(successful_actions, blockers)
    return {
        "schema_version": "recovery_semantic_review_readiness_v1",
        "book_id": book_id,
        "branch_id": resolved,
        "ready": not blockers,
        "status": "ready" if not blockers else "blocked",
        "artifact_status": "diagnostic",
        "mutation_scope": "diagnostic_only",
        "blockers": blockers,
        "available_inputs": [
            "recovery_manifest",
            "recovery_receipts",
            "recovery_branch_health",
            "normalized_outline",
            "redrafted_prose",
            "state_projection_context",
            "recovery_blast_radius",
        ],
        "present_outputs": present_outputs,
        "missing_inputs": blockers,
        "structural_health_status": structural_health_status,
        "semantic_validation_status": semantic_validation.get("status") if isinstance(semantic_validation, dict) else None,
        "semantic_validation": semantic_validation,
        "recommended_next_action": next_action,
    }


def get_recovery_semantic_review(workspace: Path, book_id: str, *, branch_id: str) -> Dict[str, Any]:
    resolved = str(branch_id or "").strip()
    book_root = _book_root(workspace, book_id)
    readiness = get_recovery_semantic_review_readiness(workspace, book_id, branch_id=resolved)
    review_path = recovery_semantic_review_path(book_root, resolved) if resolved else book_root / SEMANTIC_REVIEW_FILENAME
    manifest = get_recovery_manifest(workspace, book_id, branch_id=resolved) if resolved else {}
    node = current_execution_node(workspace, book_id, branch_id=resolved, prefer_emitted=False) if resolved else None
    if not review_path.exists():
        scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
        return {
            "schema_version": "recovery_semantic_review_v1",
            "book_id": book_id,
            "branch_id": resolved,
            "node": node.to_dict() if node else None,
            "artifact_status": "diagnostic",
            "status": "not_started",
            "review_scope": {
                "affected_scopes": [dict(item) for item in scope.get("affected_scopes", []) if isinstance(item, dict)],
                "downstream_scopes": [dict(item) for item in scope.get("downstream_scopes", []) if isinstance(item, dict)],
            },
            "readiness": readiness,
            "reviewed_artifacts": [],
            "findings": [],
            "blocked_actions": [] if readiness["ready"] else ["review_recovery_semantics"],
            "recommended_next_action": readiness["recommended_next_action"],
            "confidence": "none",
            "review_limitations": ["semantic review artifact has not been emitted yet"],
        }

    payload = _read_json(review_path)
    if not payload:
        return {
            "schema_version": "recovery_semantic_review_v1",
            "book_id": book_id,
            "branch_id": resolved,
            "node": node.to_dict() if node else None,
            "artifact_status": "diagnostic",
            "status": "review_failed",
            "readiness": readiness,
            "reviewed_artifacts": [],
            "findings": [
                {
                    "category": "missing_evidence",
                    "severity": "error",
                    "message": "Semantic review artifact exists but could not be decoded.",
                    "artifact": _relpath(review_path, book_root),
                }
            ],
            "blocked_actions": ["promote_recovery_branch"],
            "recommended_next_action": "rerun_recovery_semantic_review",
            "confidence": "none",
            "review_limitations": ["semantic review artifact is unreadable"],
        }

    merged = dict(payload)
    merged.setdefault("schema_version", "recovery_semantic_review_v1")
    merged.setdefault("book_id", book_id)
    merged.setdefault("branch_id", resolved)
    merged.setdefault("node", node.to_dict() if node else None)
    merged.setdefault("artifact_status", "diagnostic")
    merged.setdefault("status", "reviewed_attention_required")
    merged.setdefault("reviewed_artifacts", [])
    merged.setdefault("findings", [])
    merged.setdefault("blocked_actions", [])
    merged.setdefault("recommended_next_action", "inspect_recovery_semantic_review")
    merged.setdefault("confidence", "unknown")
    merged.setdefault("review_limitations", [])
    merged["readiness"] = readiness
    return merged


def get_downstream_dependency_review(workspace: Path, book_id: str, *, branch_id: str) -> Dict[str, Any]:
    resolved = str(branch_id or "").strip()
    book_root = _book_root(workspace, book_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=resolved) if resolved else {}
    scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
    downstream_scopes = [dict(item) for item in scope.get("downstream_scopes", []) if isinstance(item, dict)]
    review_path = downstream_dependency_review_path(book_root, resolved) if resolved else book_root / DOWNSTREAM_REVIEW_FILENAME
    readiness = get_recovery_semantic_review_readiness(workspace, book_id, branch_id=resolved)
    if review_path.exists():
        payload = _read_json(review_path)
        if payload:
            merged = dict(payload)
            merged.setdefault("schema_version", "downstream_dependency_review_v1")
            merged.setdefault("book_id", book_id)
            merged.setdefault("branch_id", resolved)
            merged.setdefault("artifact_status", "diagnostic")
            merged.setdefault("status", "reviewed_attention_required")
            merged["readiness"] = readiness
            return merged
        return {
            "schema_version": "downstream_dependency_review_v1",
            "book_id": book_id,
            "branch_id": resolved,
            "artifact_status": "diagnostic",
            "status": "review_failed",
            "downstream_scopes": downstream_scopes,
            "reviewed_artifacts": [],
            "findings": [
                {
                    "category": "missing_evidence",
                    "severity": "error",
                    "message": "Downstream dependency review artifact exists but could not be decoded.",
                    "artifact": _relpath(review_path, book_root),
                }
            ],
            "readiness": readiness,
            "recommended_next_action": "rerun_downstream_dependency_review",
        }

    blast_radius = get_recovery_blast_radius(workspace, book_id, branch_id=resolved) if resolved else {}
    downstream_artifacts = [
        dict(item)
        for item in blast_radius.get("artifact_impacts", [])
        if isinstance(item, dict) and item.get("family") == "downstream_review"
    ]
    status = "manifest_declared_only" if downstream_scopes else "not_started"
    return {
        "schema_version": "downstream_dependency_review_v1",
        "book_id": book_id,
        "branch_id": resolved,
        "artifact_status": "diagnostic",
        "status": status,
        "downstream_scopes": downstream_scopes,
        "reviewed_artifacts": [],
        "candidate_artifacts": downstream_artifacts,
        "findings": [],
        "readiness": readiness,
        "recommended_next_action": "review_downstream_dependencies" if downstream_scopes else readiness["recommended_next_action"],
        "review_limitations": ["downstream dependency review artifact has not been emitted yet"],
    }


def get_recovery_branch_health(workspace: Path, book_id: str, *, branch_id: str) -> RecoveryBranchHealth:
    resolved = str(branch_id or "").strip()
    book_root = _book_root(workspace, book_id)
    node = current_execution_node(workspace, book_id, branch_id=resolved, prefer_emitted=False) if resolved else None
    receipts = _read_receipts(recovery_receipts_path(book_root, resolved)) if resolved else []
    manifest = get_recovery_manifest(workspace, book_id, branch_id=resolved) if resolved else {}
    blockers: List[str] = []
    warnings: List[str] = []
    if not resolved or resolved == MAIN_BRANCH_ID:
        blockers.append("recovery health requires a derived branch")
    if not manifest:
        blockers.append("recovery manifest is missing")
    actions = {receipt.action for receipt in receipts}
    for required in (
        "create_recovery_branch",
        "quarantine_artifacts",
        "normalize_outline_scope",
        "invalidate_scope_outputs",
        "rebuild_state_scope",
        "redraft_scope",
        "validate_recovery_branch",
    ):
        if required not in actions:
            blockers.append(f"missing receipt: {required}")
    audit = None
    if resolved and resolved != MAIN_BRANCH_ID:
        audit = get_outline_lineage_audit(workspace, book_id, branch_id=resolved)
        if audit.status == "chimera_risk":
            blockers.append("branch still reports chimera_risk")
        elif audit.status == "attention_required":
            warnings.append("branch still has diagnostic outline artifacts")
    next_action = _recommended_next_recovery_action(actions, blockers)
    approval = _recovery_approval_requirements(manifest, actions) if manifest else {
        "approval_required": False,
        "approval_reasons": [],
        "broad_recovery_radius": False,
        "affected_scopes": [],
    }
    latest_validation = next((receipt for receipt in reversed(receipts) if receipt.action == "validate_recovery_branch"), None)
    latest_semantic_review = next((receipt for receipt in reversed(receipts) if receipt.action == "review_recovery_semantics"), None)
    manifest_validation = manifest.get("validation") if isinstance(manifest.get("validation"), dict) else {}
    semantic_validation = (
        latest_semantic_review.details.get("semantic_validation")
        if latest_semantic_review is not None and isinstance(latest_semantic_review.details.get("semantic_validation"), dict)
        else manifest_validation.get("semantic_validation")
        if isinstance(manifest_validation.get("semantic_validation"), dict)
        else latest_validation.details.get("semantic_validation")
        if latest_validation is not None and isinstance(latest_validation.details.get("semantic_validation"), dict)
        else None
    )
    return RecoveryBranchHealth(
        book_id=book_id,
        branch_id=resolved or MAIN_BRANCH_ID,
        node=node,
        status="healthy" if not blockers else "blocked",
        blockers=blockers,
        warnings=warnings,
        receipts=receipts,
        details={
            "manifest": manifest,
            "outline_lineage_status": audit.status if audit else None,
            "receipt_actions": sorted(actions),
            "recommended_next_action": next_action,
            "semantic_validation": semantic_validation,
            "downstream_dependency_review": manifest_validation.get("downstream_dependency_review")
            if isinstance(manifest_validation.get("downstream_dependency_review"), dict)
            else None,
            **approval,
        },
    )
