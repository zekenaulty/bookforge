from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from bookforge.contracts import BranchManifest

from . import _common
from .lineage import materialization_source_for_section
from .workspace import current_main_node, get_workspace_status


@dataclass(frozen=True, slots=True)
class IntegrityIssue:
    code: str
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class IntegrityVerdict:
    status: str
    issues: List[IntegrityIssue]


def _normalized_name(value: str) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def _load_branch_manifest(book_root, branch_id: str) -> Optional[BranchManifest]:
    payload = _common.read_json(_common.branch_manifest_path(book_root, branch_id))
    if not isinstance(payload, dict):
        return None
    try:
        return BranchManifest.from_dict(payload)
    except ValueError:
        return None


def _source_outline_payload(book_root, run_id: Optional[str]) -> Dict[str, object]:
    resolved_run_id = str(run_id or "").strip()
    if not resolved_run_id:
        return {}
    run_dir = _common.outline_root(book_root) / "pipeline_runs" / resolved_run_id
    for name in (
        "outline_final_v1_1.json",
        "outline_cast_refined_v1_1.json",
        "outline_seams_hygiened_v1_1.json",
        "outline_handoff_normalized_v1_1.json",
        "outline_draft_v1_1.json",
    ):
        payload = _common.read_json(run_dir / name)
        if isinstance(payload, dict):
            return payload
    return {}


def _find_section(outline: Dict[str, object], chapter_id: int, section_id: int) -> Optional[Dict[str, object]]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if _common.coerce_int((chapter or {}).get("chapter_id")) != int(chapter_id):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if _common.coerce_int((section or {}).get("section_id")) == int(section_id):
                return section if isinstance(section, dict) else None
    return None


def _normalize_section_for_compare(section: Dict[str, object]) -> Dict[str, object]:
    return {
        "section_id": _common.coerce_int(section.get("section_id")),
        "title": str(section.get("title") or "").strip(),
        "intent": str(section.get("intent") or "").strip(),
        "end_condition": str(section.get("end_condition") or "").strip(),
        "scenes": list(section.get("scenes") if isinstance(section.get("scenes"), list) else []),
    }


def get_integrity_verdict(workspace, book_id: str, *, prefer_emitted: bool = True) -> IntegrityVerdict:
    book_root = _common.book_root(workspace, book_id)
    status = get_workspace_status(workspace, book_id, prefer_emitted=prefer_emitted)
    registry = _common.load_registry(book_root)
    outline = _common.load_outline(book_root)
    issues: List[IntegrityIssue] = []

    emitted_main = current_main_node(workspace, book_id, prefer_emitted=True) if prefer_emitted else None
    live_main = current_main_node(workspace, book_id, prefer_emitted=False)
    if prefer_emitted and emitted_main is not None and live_main is not None:
        emitted_signature = (
            emitted_main.workflow_family,
            emitted_main.source_run_id,
            emitted_main.chapter,
            emitted_main.section,
            emitted_main.scene,
            emitted_main.phase_id,
            emitted_main.turn_id,
        )
        live_signature = (
            live_main.workflow_family,
            live_main.source_run_id,
            live_main.chapter,
            live_main.section,
            live_main.scene,
            live_main.phase_id,
            live_main.turn_id,
        )
        if emitted_signature != live_signature:
            issues.append(
                IntegrityIssue(
                    code="workflow_family_contamination",
                    severity="high",
                    message=(
                        "Emitted main-node supervision surface does not match live runtime truth: "
                        f"emitted {emitted_main.workflow_family}@{emitted_main.source_run_id} "
                        f"vs live {live_main.workflow_family}@{live_main.source_run_id}."
                    ),
                )
            )

    latest_run_id = _common.latest_outline_run_id(book_root)
    source_run_id = str(registry.get("source_run_id") or "").strip()
    if source_run_id and latest_run_id and source_run_id != latest_run_id:
        issues.append(
            IntegrityIssue(
                code="source_run_mismatch",
                severity="high",
                message=f"Workflow source_run_id={source_run_id} differs from latest outline run {latest_run_id}.",
            )
        )

    section_drafts_dir = _common.outline_root(book_root) / "section_drafts"
    if source_run_id and section_drafts_dir.exists() and any(section_drafts_dir.glob("*.json")):
        issues.append(
            IntegrityIssue(
                code="stale_section_drafts_present",
                severity="medium",
                message="Section draft artifacts still exist beside materialized workflow state.",
            )
        )

    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    characters = outline.get("characters") if isinstance(outline.get("characters"), list) else []
    seen_names: dict[str, str] = {}
    for character in characters:
        if not isinstance(character, dict):
            continue
        name = str(character.get("name") or "").strip()
        if not name:
            continue
        normalized = _normalized_name(name)
        if normalized in seen_names and seen_names[normalized] != str(character.get("character_id") or "").strip():
            issues.append(
                IntegrityIssue(
                    code="duplicate_character_name",
                    severity="high",
                    message=f"Multiple character ids share the normalized name '{name}'.",
                )
            )
            break
        seen_names[normalized] = str(character.get("character_id") or "").strip()

    source_outline = _source_outline_payload(book_root, source_run_id or latest_run_id)
    if source_outline:
        for chapter in chapters:
            chapter_id = _common.coerce_int(chapter.get("chapter_id"))
            sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
            for section in sections:
                section_id = _common.coerce_int(section.get("section_id"))
                section_status = str(section.get("status") or "").strip().lower()
                if chapter_id is None or section_id is None or section_status not in {"frozen", "locked"}:
                    continue
                source_section = _find_section(source_outline, chapter_id, section_id)
                if not isinstance(source_section, dict):
                    issues.append(
                        IntegrityIssue(
                            code="overscoped_recovery",
                            severity="high",
                            message=f"Materialized section {chapter_id}:{section_id} is missing from declared source run {source_run_id or latest_run_id}.",
                        )
                    )
                    break
                if _normalize_section_for_compare(section) != _normalize_section_for_compare(source_section):
                    issues.append(
                        IntegrityIssue(
                            code="overscoped_recovery",
                            severity="high",
                            message=f"Materialized section {chapter_id}:{section_id} no longer matches declared source run {source_run_id or latest_run_id}.",
                        )
                    )
                    break
            if any(issue.code == "overscoped_recovery" for issue in issues):
                break

    fork_groups: Dict[str, list[BranchManifest]] = {}
    for branch_id in _common.list_branch_ids(book_root):
        manifest = _load_branch_manifest(book_root, branch_id)
        if manifest is None or manifest.lifecycle_state in {"discard", "promoted"}:
            continue
        if live_main is not None and manifest.parent_node.branch_id == "main" and manifest.parent_snapshot_revision != live_main.revision_id:
            issues.append(
                IntegrityIssue(
                    code="stale_parent",
                    severity="high",
                    message=f"Branch {manifest.branch_id} was derived from main revision {manifest.parent_snapshot_revision} but current main revision is {live_main.revision_id}.",
                )
            )
        if manifest.fork_group_id:
            fork_groups.setdefault(manifest.fork_group_id, []).append(manifest)

    for fork_group_id, manifests in fork_groups.items():
        if len(manifests) < 2:
            continue
        parent_signatures = {
            (
                manifest.parent_snapshot_revision,
                manifest.parent_node.source_run_id,
                manifest.parent_node.branch_id,
                manifest.parent_node.revision_id,
            )
            for manifest in manifests
        }
        if len(parent_signatures) > 1:
            issues.append(
                IntegrityIssue(
                    code="branch_fork_contamination",
                    severity="high",
                    message=f"Fork group {fork_group_id} contains sibling branches with different parent lineage anchors.",
                )
            )
            break

    for chapter in chapters:
        chapter_id = _common.coerce_int(chapter.get("chapter_id"))
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            section_id = _common.coerce_int(section.get("section_id"))
            section_status = str(section.get("status") or "").strip().lower()
            if chapter_id is None or section_id is None or section_status not in {"frozen", "locked"}:
                continue
            source = materialization_source_for_section(workspace, book_id, chapter_id, section_id) or {}
            artifact_class = str(source.get("artifact_class") or "").strip()
            if artifact_class == "mutable_compatibility_view":
                issues.append(
                    IntegrityIssue(
                        code="mutable_source_materialization",
                        severity="high",
                        message=f"Section {chapter_id}:{section_id} appears to rely on mutable compatibility state.",
                    )
                )
                break
        if any(issue.code == "mutable_source_materialization" for issue in issues):
            break

    if issues:
        high = any(issue.severity == "high" for issue in issues)
        return IntegrityVerdict(status="chimera_risk" if high else "attention_required", issues=issues)
    return IntegrityVerdict(status="healthy", issues=[])
