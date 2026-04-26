from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, ScopeSelector, TimelineNodeRef, classify_source_artifact

from . import _common
from .workspace import current_execution_node


_RUN_ANCHOR_NAMES = (
    "outline_final_v1_1.json",
    "outline_cast_refined_v1_1.json",
    "outline_seams_hygiened_v1_1.json",
    "outline_handoff_normalized_v1_1.json",
    "outline_draft_v1_1.json",
    "outline_sections_v1.json",
)

_VIEW_NAMES = (
    "outline.json",
    "outline.thin.json",
    "outline.toc.json",
    "outline.index.json",
    "outline.appendix.json",
    "characters.json",
    "snapshot_registry.json",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_relpath(book_root: Path, path: Path) -> str:
    try:
        return path.relative_to(book_root).as_posix()
    except ValueError:
        return path.as_posix()


def _hash_payload(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _mtime_iso(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except OSError:
        return None


def _file_size(path: Path) -> Optional[int]:
    if not path.exists():
        return None
    try:
        return int(path.stat().st_size)
    except OSError:
        return None


def _artifact_status(path: Path) -> str:
    artifact_class = classify_source_artifact(path).value
    if artifact_class in {"immutable_lineage_anchor", "frozen_projection"}:
        return "authoritative"
    if artifact_class == "mutable_compatibility_view":
        return "provisional"
    return "diagnostic"


def _read_payload(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    return _common.read_json(path) or {}


def _preferred_run_anchor(outline_root: Path, run_id: Optional[str]) -> Optional[Path]:
    resolved = str(run_id or "").strip()
    if not resolved:
        return None
    run_dir = outline_root / "pipeline_runs" / resolved
    for name in _RUN_ANCHOR_NAMES:
        candidate = run_dir / name
        if candidate.exists():
            return candidate
    return None


def _unwrap_chapter(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("chapter"), dict):
        return payload["chapter"]
    return payload


def _find_section(payload: Dict[str, Any], chapter_id: int, section_id: int) -> Optional[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("section"), dict):
        section = payload["section"]
        if _common.coerce_int(section.get("section_id")) in {None, int(section_id)}:
            return section

    chapter_payload = _unwrap_chapter(payload)
    if _common.coerce_int(chapter_payload.get("chapter_id")) == int(chapter_id):
        sections = chapter_payload.get("sections") if isinstance(chapter_payload.get("sections"), list) else []
        for section in sections:
            if isinstance(section, dict) and _common.coerce_int(section.get("section_id")) == int(section_id):
                return section

    sections = payload.get("sections") if isinstance(payload.get("sections"), list) else []
    for section in sections:
        if isinstance(section, dict) and _common.coerce_int(section.get("section_id")) == int(section_id):
            return section

    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict) or _common.coerce_int(chapter.get("chapter_id")) != int(chapter_id):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if isinstance(section, dict) and _common.coerce_int(section.get("section_id")) == int(section_id):
                return section
    return None


def _all_section_keys(payloads: Iterable[Dict[str, Any]]) -> List[tuple[int, int]]:
    keys: set[tuple[int, int]] = set()
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        chapter_payload = _unwrap_chapter(payload)
        if _common.coerce_int(chapter_payload.get("chapter_id")) is not None:
            chapter_id = int(chapter_payload["chapter_id"])
            sections = chapter_payload.get("sections") if isinstance(chapter_payload.get("sections"), list) else []
            for section in sections:
                section_id = _common.coerce_int((section or {}).get("section_id")) if isinstance(section, dict) else None
                if section_id is not None:
                    keys.add((chapter_id, int(section_id)))
        chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            chapter_id = _common.coerce_int(chapter.get("chapter_id"))
            if chapter_id is None:
                continue
            sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
            for section in sections:
                section_id = _common.coerce_int((section or {}).get("section_id")) if isinstance(section, dict) else None
                if section_id is not None:
                    keys.add((int(chapter_id), int(section_id)))
    return sorted(keys)


def _section_draft_key(path: Path) -> Optional[tuple[int, int]]:
    match = re.search(r"ch_(\d+)_sec_(\d+)_phase03\.json$", path.name)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _scene_characters(scene: Dict[str, Any]) -> List[str]:
    value = scene.get("characters")
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def _normalize_scene(scene: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "scene_id": _common.coerce_int(scene.get("scene_id")),
        "summary": str(scene.get("summary") or "").strip(),
        "outcome": str(scene.get("outcome") or "").strip(),
        "characters": _scene_characters(scene),
        "threads": sorted(str(item).strip() for item in (scene.get("threads") if isinstance(scene.get("threads"), list) else []) if str(item).strip()),
        "hands_off_to": str(scene.get("hands_off_to") or "").strip(),
        "consumes_outcome_from": str(scene.get("consumes_outcome_from") or "").strip(),
        "handoff_mode": str(scene.get("handoff_mode") or "").strip(),
        "end_condition_echo": str(scene.get("end_condition_echo") or "").strip(),
    }


def _normalize_section(section: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(section, dict):
        return None
    scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
    return {
        "section_id": _common.coerce_int(section.get("section_id")),
        "title": str(section.get("title") or "").strip(),
        "intent": str(section.get("intent") or "").strip(),
        "end_condition": str(section.get("end_condition") or "").strip(),
        "scenes": [_normalize_scene(scene) for scene in scenes if isinstance(scene, dict)],
    }


def _compare_fields(section: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    normalized = _normalize_section(section)
    if normalized is None:
        return {}
    scenes = normalized["scenes"]
    character_ids = sorted({char for scene in scenes for char in scene.get("characters", [])})
    return {
        "title": normalized["title"],
        "intent": normalized["intent"],
        "end_condition": normalized["end_condition"],
        "scene_ids": [scene.get("scene_id") for scene in scenes],
        "scene_count": len(scenes),
        "scene_summaries": [scene.get("summary") for scene in scenes],
        "scene_outcomes": [scene.get("outcome") for scene in scenes],
        "character_ids": character_ids,
        "handoff_refs": [
            {
                "scene_id": scene.get("scene_id"),
                "hands_off_to": scene.get("hands_off_to"),
                "consumes_outcome_from": scene.get("consumes_outcome_from"),
                "handoff_mode": scene.get("handoff_mode"),
            }
            for scene in scenes
        ],
        "terminal_echoes": [
            {
                "scene_id": scene.get("scene_id"),
                "end_condition_echo": scene.get("end_condition_echo"),
            }
            for scene in scenes
            if scene.get("end_condition_echo")
        ],
    }


@dataclass(frozen=True, slots=True)
class OutlineArtifactObservation:
    artifact_family: str
    label: str
    path: Optional[str]
    exists: bool
    artifact_class: Optional[str]
    artifact_status: str
    source_run_id: Optional[str] = None
    mtime: Optional[str] = None
    size: Optional[int] = None
    file_hash: Optional[str] = None
    section_hash: Optional[str] = None
    scene_list_hash: Optional[str] = None
    scene_count: Optional[int] = None
    character_ids: List[str] = field(default_factory=list)
    safe_to_consume_as_canonical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_family": self.artifact_family,
            "label": self.label,
            "path": self.path,
            "exists": self.exists,
            "artifact_class": self.artifact_class,
            "artifact_status": self.artifact_status,
            "source_run_id": self.source_run_id,
            "mtime": self.mtime,
            "size": self.size,
            "file_hash": self.file_hash,
            "section_hash": self.section_hash,
            "scene_list_hash": self.scene_list_hash,
            "scene_count": self.scene_count,
            "character_ids": list(self.character_ids),
            "safe_to_consume_as_canonical": self.safe_to_consume_as_canonical,
        }


@dataclass(frozen=True, slots=True)
class SectionLineageRow:
    book_id: str
    selector: ScopeSelector
    chapter_id: int
    section_id: int
    section_title: Optional[str]
    declared_source_run_id: Optional[str]
    latest_outline_run_id: Optional[str]
    workflow_family: Optional[str]
    materialized_status: Optional[str]
    candidate_artifacts: List[OutlineArtifactObservation]
    normalized_section_hashes: Dict[str, Optional[str]]
    normalized_scene_list_hashes: Dict[str, Optional[str]]
    differing_fields: List[str]
    scene_count_delta: Optional[str]
    character_cohort_delta: List[str]
    artifact_mtimes: Dict[str, Optional[str]]
    suspected_contamination_class: str
    recommended_safe_next_action: str
    schema_version: str = "section_lineage_row_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "chapter_id": self.chapter_id,
            "section_id": self.section_id,
            "section_title": self.section_title,
            "declared_source_run_id": self.declared_source_run_id,
            "latest_outline_run_id": self.latest_outline_run_id,
            "workflow_family": self.workflow_family,
            "materialized_status": self.materialized_status,
            "candidate_artifacts": [artifact.to_dict() for artifact in self.candidate_artifacts],
            "normalized_section_hashes": dict(self.normalized_section_hashes),
            "normalized_scene_list_hashes": dict(self.normalized_scene_list_hashes),
            "differing_fields": list(self.differing_fields),
            "scene_count_delta": self.scene_count_delta,
            "character_cohort_delta": list(self.character_cohort_delta),
            "artifact_mtimes": dict(self.artifact_mtimes),
            "suspected_contamination_class": self.suspected_contamination_class,
            "recommended_safe_next_action": self.recommended_safe_next_action,
        }


@dataclass(frozen=True, slots=True)
class StaleOutlineArtifact:
    path: str
    artifact_family: str
    artifact_class: str
    artifact_status: str
    mtime: Optional[str]
    size: Optional[int]
    file_hash: Optional[str]
    chapter_id: Optional[int]
    section_id: Optional[int]
    safe_to_consume_as_canonical: bool
    reason: str
    schema_version: str = "stale_outline_artifact_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "path": self.path,
            "artifact_family": self.artifact_family,
            "artifact_class": self.artifact_class,
            "artifact_status": self.artifact_status,
            "mtime": self.mtime,
            "size": self.size,
            "file_hash": self.file_hash,
            "chapter_id": self.chapter_id,
            "section_id": self.section_id,
            "safe_to_consume_as_canonical": self.safe_to_consume_as_canonical,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class OutlineRepairCandidate:
    action: str
    summary: str
    risk_level: str
    affected_scopes: List[Dict[str, int]]
    source_artifact_family: Optional[str]
    requires_human_decision: bool
    blocked: bool
    reason: str
    expected_writable_scope: Optional[str] = None
    schema_version: str = "outline_repair_candidate_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "action": self.action,
            "summary": self.summary,
            "risk_level": self.risk_level,
            "affected_scopes": [dict(scope) for scope in self.affected_scopes],
            "source_artifact_family": self.source_artifact_family,
            "requires_human_decision": self.requires_human_decision,
            "blocked": self.blocked,
            "reason": self.reason,
            "expected_writable_scope": self.expected_writable_scope,
        }


@dataclass(frozen=True, slots=True)
class OutlineLineageAudit:
    book_id: str
    selector: ScopeSelector
    node: Optional[TimelineNodeRef]
    status: str
    declared_source_run_id: Optional[str]
    latest_outline_run_id: Optional[str]
    generated_at: str
    section_matrix: List[SectionLineageRow]
    stale_artifacts: List[StaleOutlineArtifact]
    repair_candidates: List[OutlineRepairCandidate]
    first_technical_divergence: Optional[Dict[str, int]]
    first_visible_story_divergence: Optional[Dict[str, int]]
    character_cohort_conflicts: List[Dict[str, Any]]
    blocked_actions: List[str]
    schema_version: str = "outline_lineage_audit_v1"

    @property
    def affected_sections(self) -> List[SectionLineageRow]:
        return [row for row in self.section_matrix if row.suspected_contamination_class != "healthy"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "status": self.status,
            "declared_source_run_id": self.declared_source_run_id,
            "latest_outline_run_id": self.latest_outline_run_id,
            "generated_at": self.generated_at,
            "section_matrix": [row.to_dict() for row in self.section_matrix],
            "stale_artifacts": [artifact.to_dict() for artifact in self.stale_artifacts],
            "repair_candidates": [candidate.to_dict() for candidate in self.repair_candidates],
            "first_technical_divergence": dict(self.first_technical_divergence) if self.first_technical_divergence else None,
            "first_visible_story_divergence": dict(self.first_visible_story_divergence) if self.first_visible_story_divergence else None,
            "character_cohort_conflicts": [dict(conflict) for conflict in self.character_cohort_conflicts],
            "affected_scopes": [
                {"chapter_id": row.chapter_id, "section_id": row.section_id}
                for row in self.affected_sections
            ],
            "blocked_actions": list(self.blocked_actions),
        }


def _artifact_observation(
    *,
    book_root: Path,
    artifact_family: str,
    label: str,
    path: Optional[Path],
    section: Optional[Dict[str, Any]],
    source_run_id: Optional[str] = None,
) -> OutlineArtifactObservation:
    exists = bool(path and path.exists())
    normalized = _normalize_section(section)
    scenes = normalized["scenes"] if normalized else []
    character_ids = sorted({char for scene in scenes for char in scene.get("characters", [])})
    artifact_class = classify_source_artifact(path).value if path else None
    status = _artifact_status(path) if path else "diagnostic"
    safe = bool(artifact_class in {"immutable_lineage_anchor", "frozen_projection"})
    return OutlineArtifactObservation(
        artifact_family=artifact_family,
        label=label,
        path=_artifact_relpath(book_root, path) if path else None,
        exists=exists,
        artifact_class=artifact_class,
        artifact_status=status,
        source_run_id=source_run_id,
        mtime=_mtime_iso(path) if path else None,
        size=_file_size(path) if path else None,
        file_hash=_file_hash(path) if path else None,
        section_hash=_hash_payload(normalized) if normalized else None,
        scene_list_hash=_hash_payload(scenes) if normalized else None,
        scene_count=len(scenes) if normalized else None,
        character_ids=character_ids,
        safe_to_consume_as_canonical=safe,
    )


def _row_contamination_class(
    observations: List[OutlineArtifactObservation],
    differing_fields: List[str],
    *,
    section_draft_mtime_newer: bool,
    materialized_status: Optional[str],
) -> str:
    normalized_status = str(materialized_status or "").strip().lower()
    is_materialized = normalized_status in {"frozen", "locked"}
    if not is_materialized:
        if section_draft_mtime_newer and any(item.label == "section_draft" and item.exists for item in observations):
            return "stale_section_draft_present"
        return "healthy"
    existing = {item.label: item for item in observations if item.exists}
    mutable = existing.get("mutable_outline")
    frozen = existing.get("frozen_chapter_projection")
    draft = existing.get("section_draft")
    if (
        mutable is not None
        and (mutable.scene_count or 0) == 0
        and frozen is None
        and draft is None
        and differing_fields
        and all(field.startswith("mutable_outline.") for field in differing_fields)
    ):
        return "healthy"
    if "declared_source_run" in existing:
        if existing["declared_source_run"].section_hash is None:
            return "missing_source_section"
        for label in ("mutable_outline", "frozen_chapter_projection", "section_draft"):
            item = existing.get(label)
            if item and item.section_hash and item.section_hash != existing["declared_source_run"].section_hash:
                if label == "section_draft":
                    return "stale_section_draft_conflict"
                if label == "mutable_outline":
                    return "mutable_outline_drift"
                return "frozen_projection_drift"
    if any(field.endswith(".character_ids") for field in differing_fields):
        return "character_cohort_conflict"
    if section_draft_mtime_newer and "section_draft" in existing:
        return "stale_section_draft_present"
    if differing_fields:
        return "artifact_lineage_conflict"
    return "healthy"


def _first_present_title(observations: List[OutlineArtifactObservation], sections_by_label: Dict[str, Optional[Dict[str, Any]]]) -> Optional[str]:
    for observation in observations:
        section = sections_by_label.get(observation.label)
        if isinstance(section, dict):
            title = str(section.get("title") or "").strip()
            if title:
                return title
    return None


def _differing_fields(
    sections_by_label: Dict[str, Optional[Dict[str, Any]]],
    baseline_label: Optional[str],
) -> List[str]:
    if not baseline_label:
        return []
    baseline = _compare_fields(sections_by_label.get(baseline_label))
    if not baseline:
        return []
    differences: List[str] = []
    for label, section in sections_by_label.items():
        if label == baseline_label or not isinstance(section, dict):
            continue
        current = _compare_fields(section)
        for field, baseline_value in baseline.items():
            if current.get(field) != baseline_value:
                differences.append(f"{label}.{field}")
    return sorted(differences)


def _scene_count_delta(observations: List[OutlineArtifactObservation]) -> Optional[str]:
    counts = {item.label: item.scene_count for item in observations if item.exists and item.scene_count is not None}
    if len(set(counts.values())) <= 1:
        return None
    return ", ".join(f"{label}={count}" for label, count in sorted(counts.items()))


def _character_cohort_delta(observations: List[OutlineArtifactObservation]) -> List[str]:
    cohorts = {
        item.label: tuple(item.character_ids)
        for item in observations
        if item.exists and item.character_ids
    }
    if len(set(cohorts.values())) <= 1:
        return []
    return [f"{label}:{','.join(chars)}" for label, chars in sorted(cohorts.items())]


def _section_draft_newer(observations: List[OutlineArtifactObservation]) -> bool:
    by_label = {item.label: item for item in observations}
    draft = by_label.get("section_draft")
    frozen = by_label.get("frozen_chapter_projection")
    if not draft or not frozen or not draft.mtime or not frozen.mtime:
        return False
    return draft.mtime > frozen.mtime


def _selector(book_id: str, branch_id: str, chapter_id: Optional[int] = None, section_id: Optional[int] = None) -> ScopeSelector:
    return ScopeSelector(
        book_id=book_id,
        branch_id=branch_id,
        workflow_family="section_local_outline",
        chapter=chapter_id,
        section=section_id,
    )


def _lineage_context(workspace, book_id: str, branch_id: str) -> Dict[str, Any]:
    canonical_root = _common.book_root(workspace, book_id)
    book_root = _common.execution_book_root(canonical_root, branch_id)
    outline_root = _common.outline_root(book_root)
    registry = _common.load_registry(book_root)
    declared_source_run_id = str(registry.get("source_run_id") or "").strip() or None
    latest_outline_run_id = _common.latest_outline_run_id(book_root)
    declared_anchor = _preferred_run_anchor(outline_root, declared_source_run_id)
    latest_anchor = _preferred_run_anchor(outline_root, latest_outline_run_id)
    return {
        "canonical_root": canonical_root,
        "book_root": book_root,
        "outline_root": outline_root,
        "registry": registry,
        "outline": _common.load_outline(book_root),
        "declared_source_run_id": declared_source_run_id,
        "latest_outline_run_id": latest_outline_run_id,
        "declared_anchor": declared_anchor,
        "declared_payload": _read_payload(declared_anchor),
        "latest_anchor": latest_anchor,
        "latest_payload": _read_payload(latest_anchor),
    }


def _section_draft_path(outline_root: Path, chapter_id: int, section_id: int) -> Path:
    return outline_root / "section_drafts" / f"ch_{chapter_id:03d}_sec_{section_id:03d}_phase03.json"


def _frozen_chapter_path(outline_root: Path, chapter_id: int) -> Path:
    return outline_root / "chapters" / f"ch_{chapter_id:03d}.json"


def _build_row(
    workspace,
    book_id: str,
    branch_id: str,
    context: Dict[str, Any],
    chapter_id: int,
    section_id: int,
) -> SectionLineageRow:
    outline_root = context["outline_root"]
    book_root = context["book_root"]
    declared_source_run_id = context["declared_source_run_id"]
    latest_outline_run_id = context["latest_outline_run_id"]
    mutable_path = outline_root / "outline.json"
    frozen_path = _frozen_chapter_path(outline_root, chapter_id)
    draft_path = _section_draft_path(outline_root, chapter_id, section_id)

    payloads = {
        "declared_source_run": context["declared_payload"],
        "latest_outline_run": context["latest_payload"],
        "frozen_chapter_projection": _read_payload(frozen_path),
        "mutable_outline": context["outline"],
        "section_draft": _read_payload(draft_path),
    }
    paths = {
        "declared_source_run": context["declared_anchor"],
        "latest_outline_run": context["latest_anchor"],
        "frozen_chapter_projection": frozen_path,
        "mutable_outline": mutable_path,
        "section_draft": draft_path,
    }
    families = {
        "declared_source_run": "declared_source_run",
        "latest_outline_run": "latest_outline_run",
        "frozen_chapter_projection": "frozen_chapter_projection",
        "mutable_outline": "mutable_outline",
        "section_draft": "section_draft",
    }
    source_runs = {
        "declared_source_run": declared_source_run_id,
        "latest_outline_run": latest_outline_run_id,
        "frozen_chapter_projection": None,
        "mutable_outline": None,
        "section_draft": None,
    }
    sections_by_label = {
        label: _find_section(payload, chapter_id, section_id)
        for label, payload in payloads.items()
    }
    observations = [
        _artifact_observation(
            book_root=book_root,
            artifact_family=families[label],
            label=label,
            path=paths[label],
            section=sections_by_label[label],
            source_run_id=source_runs[label],
        )
        for label in ("declared_source_run", "latest_outline_run", "frozen_chapter_projection", "mutable_outline", "section_draft")
    ]
    baseline_label = "declared_source_run" if sections_by_label.get("declared_source_run") else "frozen_chapter_projection"
    diffs = _differing_fields(sections_by_label, baseline_label)
    section_draft_newer = _section_draft_newer(observations)
    registry_section = _find_section(context["registry"], chapter_id, section_id) or {}
    materialized_status = str(registry_section.get("status") or "").strip() or None
    contamination_class = _row_contamination_class(
        observations,
        diffs,
        section_draft_mtime_newer=section_draft_newer,
        materialized_status=materialized_status,
    )
    if contamination_class == "healthy":
        recommended_action = "none"
    elif contamination_class == "stale_section_draft_present":
        recommended_action = "quarantine_stale_section_drafts"
    else:
        recommended_action = "choose_recovery_anchor"
    workflow_family = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=True)
    return SectionLineageRow(
        book_id=book_id,
        selector=_selector(book_id, branch_id, chapter_id, section_id),
        chapter_id=chapter_id,
        section_id=section_id,
        section_title=_first_present_title(observations, sections_by_label),
        declared_source_run_id=declared_source_run_id,
        latest_outline_run_id=latest_outline_run_id,
        workflow_family=workflow_family.workflow_family if workflow_family else None,
        materialized_status=materialized_status,
        candidate_artifacts=observations,
        normalized_section_hashes={item.label: item.section_hash for item in observations},
        normalized_scene_list_hashes={item.label: item.scene_list_hash for item in observations},
        differing_fields=diffs,
        scene_count_delta=_scene_count_delta(observations),
        character_cohort_delta=_character_cohort_delta(observations),
        artifact_mtimes={item.label: item.mtime for item in observations},
        suspected_contamination_class=contamination_class,
        recommended_safe_next_action=recommended_action,
    )


def get_section_lineage_matrix(
    workspace,
    book_id: str,
    *,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    branch_id: str = MAIN_BRANCH_ID,
) -> List[SectionLineageRow]:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    context = _lineage_context(workspace, book_id, resolved_branch_id)
    payloads = [context["declared_payload"], context["latest_payload"], context["outline"], context["registry"]]
    chapters_root = context["outline_root"] / "chapters"
    if chapters_root.exists():
        for path in sorted(chapters_root.glob("ch_*.json")):
            payloads.append(_read_payload(path))
    section_drafts_root = context["outline_root"] / "section_drafts"
    draft_keys: set[tuple[int, int]] = set()
    if section_drafts_root.exists():
        for path in sorted(section_drafts_root.glob("ch_*_sec_*_phase03.json")):
            key = _section_draft_key(path)
            if key:
                draft_keys.add(key)
            payloads.append(_read_payload(path))

    keys = set(_all_section_keys(payloads)) | draft_keys
    if chapter_id is not None:
        keys = {key for key in keys if key[0] == int(chapter_id)}
    if section_id is not None:
        keys = {key for key in keys if key[1] == int(section_id)}
    return [
        _build_row(workspace, book_id, resolved_branch_id, context, ch_id, sec_id)
        for ch_id, sec_id in sorted(keys)
    ]


def _artifact_scope_from_path(path: Path) -> tuple[Optional[int], Optional[int]]:
    draft_key = _section_draft_key(path)
    if draft_key:
        return draft_key
    chapter_match = re.search(r"ch_(\d+)\.json$", path.name)
    if chapter_match:
        return int(chapter_match.group(1)), None
    return None, None


def get_stale_outline_artifact_inventory(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> List[StaleOutlineArtifact]:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    canonical_root = _common.book_root(workspace, book_id)
    book_root = _common.execution_book_root(canonical_root, resolved_branch_id)
    outline_root = _common.outline_root(book_root)
    paths: List[Path] = []
    section_drafts_root = outline_root / "section_drafts"
    if section_drafts_root.exists():
        paths.extend(sorted(section_drafts_root.glob("ch_*_sec_*_phase03.json")))
    for name in _VIEW_NAMES:
        candidate = outline_root / name
        if candidate.exists():
            paths.append(candidate)

    inventory: List[StaleOutlineArtifact] = []
    for path in paths:
        artifact_class = classify_source_artifact(path).value
        artifact_status = _artifact_status(path)
        chapter, section = _artifact_scope_from_path(path)
        if "/section_drafts/" in path.as_posix().replace("\\", "/"):
            family = "section_draft"
            reason = "section-local draft artifact is diagnostic until explicitly selected as recovery input"
        elif artifact_class == "mutable_compatibility_view":
            family = "mutable_compatibility_view"
            reason = "mutable compatibility views must not be used as lineage anchors when immutable or frozen artifacts exist"
        else:
            family = "outline_projection"
            reason = "projection included for lineage comparison"
        inventory.append(
            StaleOutlineArtifact(
                path=_artifact_relpath(book_root, path),
                artifact_family=family,
                artifact_class=artifact_class,
                artifact_status=artifact_status,
                mtime=_mtime_iso(path),
                size=_file_size(path),
                file_hash=_file_hash(path),
                chapter_id=chapter,
                section_id=section,
                safe_to_consume_as_canonical=artifact_class in {"immutable_lineage_anchor", "frozen_projection"},
                reason=reason,
            )
        )
    return inventory


def _affected_scopes(rows: List[SectionLineageRow]) -> List[Dict[str, int]]:
    return [
        {"chapter_id": row.chapter_id, "section_id": row.section_id}
        for row in rows
        if row.suspected_contamination_class != "healthy"
    ]


def get_outline_repair_candidates(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> List[OutlineRepairCandidate]:
    matrix = get_section_lineage_matrix(workspace, book_id, branch_id=branch_id)
    affected = _affected_scopes(matrix)
    has_section_drafts = any(
        any(artifact.label == "section_draft" and artifact.exists for artifact in row.candidate_artifacts)
        for row in matrix
    )
    candidates = [
        OutlineRepairCandidate(
            action="inspect_only",
            summary="Inspect lineage evidence without mutating workspace state.",
            risk_level="low",
            affected_scopes=affected,
            source_artifact_family=None,
            requires_human_decision=False,
            blocked=False,
            reason="Read-only inspection is always safe.",
            expected_writable_scope=None,
        )
    ]
    if not affected:
        return candidates

    candidates.append(
        OutlineRepairCandidate(
            action="choose_recovery_anchor",
            summary="Choose which artifact lineage should become the recovery source.",
            risk_level="medium",
            affected_scopes=affected,
            source_artifact_family=None,
            requires_human_decision=True,
            blocked=False,
            reason="BookForge found conflicting outline lineages and needs an explicit recovery source before mutation.",
            expected_writable_scope=None,
        )
    )
    candidates.append(
        OutlineRepairCandidate(
            action="create_recovery_branch_from_selected_lineage",
            summary="Create a branch-scoped recovery workspace from the selected artifact lineage.",
            risk_level="medium",
            affected_scopes=affected,
            source_artifact_family="selected_by_human",
            requires_human_decision=True,
            blocked=True,
            reason="Requires a selected recovery anchor and a later mutation-capable recovery story.",
            expected_writable_scope="derived_branch",
        )
    )
    candidates.append(
        OutlineRepairCandidate(
            action="restore_affected_sections_from_declared_source_run",
            summary="Restore affected section materialization from the declared immutable source run in a recovery branch.",
            risk_level="high",
            affected_scopes=affected,
            source_artifact_family="declared_source_run",
            requires_human_decision=True,
            blocked=True,
            reason="Read-only audit step cannot restore sections; this must run later with backups and receipts.",
            expected_writable_scope="derived_branch",
        )
    )
    candidates.append(
        OutlineRepairCandidate(
            action="restore_affected_sections_from_frozen_chapter_projection",
            summary="Restore affected section materialization from frozen chapter projections in a recovery branch.",
            risk_level="high",
            affected_scopes=affected,
            source_artifact_family="frozen_chapter_projection",
            requires_human_decision=True,
            blocked=True,
            reason="Frozen projections may be the coherent candidate source, but mutation requires an explicit recovery action.",
            expected_writable_scope="derived_branch",
        )
    )
    if has_section_drafts:
        candidates.append(
            OutlineRepairCandidate(
                action="quarantine_stale_section_drafts",
                summary="Move stale section draft artifacts out of canonical discovery paths with a receipt.",
                risk_level="medium",
                affected_scopes=affected,
                source_artifact_family="section_draft",
                requires_human_decision=True,
                blocked=True,
                reason="Quarantine is a mutation and must be performed by a later recovery action.",
                expected_writable_scope="canonical_or_branch_with_backup",
            )
        )
    candidates.append(
        OutlineRepairCandidate(
            action="shelf_book",
            summary="Leave the book unchanged and mark it unsuitable for automatic repair.",
            risk_level="low",
            affected_scopes=affected,
            source_artifact_family=None,
            requires_human_decision=True,
            blocked=False,
            reason="If no source lineage is trustworthy, shelving avoids contaminating canonical state further.",
            expected_writable_scope=None,
        )
    )
    return candidates


def _first_technical_divergence(rows: List[SectionLineageRow]) -> Optional[Dict[str, int]]:
    for row in rows:
        if row.suspected_contamination_class != "healthy":
            return {"chapter_id": row.chapter_id, "section_id": row.section_id}
    return None


def _visible_story_divergence(rows: List[SectionLineageRow]) -> Optional[Dict[str, int]]:
    previous: Optional[tuple[str, ...]] = None
    for row in sorted(rows, key=lambda item: (item.chapter_id, item.section_id)):
        mutable = next((artifact for artifact in row.candidate_artifacts if artifact.label == "mutable_outline"), None)
        current = tuple(mutable.character_ids) if mutable and mutable.character_ids else None
        if current is None:
            continue
        if previous is not None and current != previous:
            return {"chapter_id": row.chapter_id, "section_id": row.section_id}
        previous = current
    return None


def _character_cohort_conflicts(rows: List[SectionLineageRow]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    for row in rows:
        if not row.character_cohort_delta:
            continue
        conflicts.append(
            {
                "chapter_id": row.chapter_id,
                "section_id": row.section_id,
                "cohorts": list(row.character_cohort_delta),
            }
        )
    visible = _visible_story_divergence(rows)
    if visible is not None:
        conflicts.append(
            {
                "chapter_id": visible["chapter_id"],
                "section_id": visible["section_id"],
                "cohorts": ["mutable_outline_cohort_switch"],
                "visible_story_divergence": True,
            }
        )
    return conflicts


def get_outline_lineage_audit(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> OutlineLineageAudit:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    context = _lineage_context(workspace, book_id, resolved_branch_id)
    matrix = get_section_lineage_matrix(workspace, book_id, branch_id=resolved_branch_id)
    stale_artifacts = get_stale_outline_artifact_inventory(workspace, book_id, branch_id=resolved_branch_id)
    repair_candidates = get_outline_repair_candidates(workspace, book_id, branch_id=resolved_branch_id)
    first_technical = _first_technical_divergence(matrix)
    first_visible = _visible_story_divergence(matrix)
    conflicts = _character_cohort_conflicts(matrix)
    affected = [row for row in matrix if row.suspected_contamination_class != "healthy"]
    status = "chimera_risk" if affected else "healthy"
    if not affected and any(item.artifact_family == "section_draft" for item in stale_artifacts):
        status = "attention_required"
    blocked_actions = []
    if status == "chimera_risk":
        blocked_actions = [
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
            "seam_chapter",
        ]
    return OutlineLineageAudit(
        book_id=book_id,
        selector=_selector(book_id, resolved_branch_id),
        node=current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=True),
        status=status,
        declared_source_run_id=context["declared_source_run_id"],
        latest_outline_run_id=context["latest_outline_run_id"],
        generated_at=_now_iso(),
        section_matrix=matrix,
        stale_artifacts=stale_artifacts,
        repair_candidates=repair_candidates,
        first_technical_divergence=first_technical,
        first_visible_story_divergence=first_visible,
        character_cohort_conflicts=conflicts,
        blocked_actions=blocked_actions,
    )
