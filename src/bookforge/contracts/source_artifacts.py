from __future__ import annotations

from enum import Enum
from pathlib import PurePath
import re

from .vocabulary import ARTIFACT_CLASS_LABELS


class SourceArtifactClass(str, Enum):
    IMMUTABLE_LINEAGE_ANCHOR = "immutable_lineage_anchor"
    FROZEN_PROJECTION = "frozen_projection"
    MUTABLE_COMPATIBILITY_VIEW = "mutable_compatibility_view"
    DIAGNOSTIC_ONLY = "diagnostic_only"


_PIPELINE_SEMANTIC_OUTPUT_NAMES = {
    "outline_spine_v1.json",
    "outline_sections_v1.json",
    "outline_draft_v1_1.json",
    "phase_04a_output.json",
    "outline_transitions_refined_v1_1.json",
    "outline_transitions_relinked_v1_1.json",
    "outline_intro_synced_v1_1.json",
    "outline_handoff_normalized_v1_1.json",
    "outline_seams_hygiened_v1_1.json",
    "outline_cast_refined_v1_1.json",
    "outline_final_v1_1.json",
}

_PIPELINE_DIAGNOSTIC_NAMES = {
    "outline_pipeline_report.json",
    "outline_pipeline_report_latest.json",
    "phase_history.json",
    "pipeline_latest.json",
    "outline_pipeline_latest.json",
    "outline_backup_latest.json",
    "outline_backups_index.json",
    "backup_manifest.json",
}

_FROZEN_PROJECTION_NAMES = {
    "snapshot_registry.json",
    "outline.thin.json",
    "outline.toc.json",
    "outline.index.json",
    "outline.appendix.json",
}

_MUTABLE_COMPATIBILITY_NAMES = {
    "outline.json",
    "characters.json",
}

_PIPELINE_RUN_PATTERN = re.compile(r"/outline/pipeline_runs/[^/]+/")
_BACKUP_PIPELINE_PATTERN = re.compile(r"/backups/outline_completed/[^/]+/[^/]+/pipeline_run/")
_BACKUP_SNAPSHOT_PATTERN = re.compile(r"/backups/outline_completed/[^/]+/[^/]+/outline_snapshot/")


def _normalize_path(value: str | PurePath) -> str:
    raw = value.as_posix() if isinstance(value, PurePath) else str(value)
    return raw.replace("\\", "/").strip().lower()


def _filename(path_text: str) -> str:
    return path_text.rsplit("/", 1)[-1]


def _is_pipeline_semantic_output(filename: str) -> bool:
    if filename in _PIPELINE_SEMANTIC_OUTPUT_NAMES:
        return True
    return filename.endswith("_output.json")


def _is_pipeline_diagnostic(filename: str) -> bool:
    if filename in _PIPELINE_DIAGNOSTIC_NAMES:
        return True
    return (
        filename.endswith("_validation.json")
        or filename.endswith("_checkpoint.json")
        or "_attempt_raw_" in filename
        or filename.endswith("_input.json")
    )


def classify_source_artifact(path: str | PurePath) -> SourceArtifactClass:
    normalized = _normalize_path(path)
    filename = _filename(normalized)

    if _PIPELINE_RUN_PATTERN.search(normalized) or _BACKUP_PIPELINE_PATTERN.search(normalized):
        if _is_pipeline_semantic_output(filename):
            return SourceArtifactClass.IMMUTABLE_LINEAGE_ANCHOR
        return SourceArtifactClass.DIAGNOSTIC_ONLY

    if _BACKUP_SNAPSHOT_PATTERN.search(normalized):
        return SourceArtifactClass.FROZEN_PROJECTION

    if "/outline/boundaries/" in normalized:
        return SourceArtifactClass.FROZEN_PROJECTION

    if "/outline/chapters/" in normalized and filename.endswith(".json"):
        return SourceArtifactClass.FROZEN_PROJECTION

    if filename in _FROZEN_PROJECTION_NAMES:
        return SourceArtifactClass.FROZEN_PROJECTION

    if filename in _MUTABLE_COMPATIBILITY_NAMES:
        return SourceArtifactClass.MUTABLE_COMPATIBILITY_VIEW

    if filename in _PIPELINE_DIAGNOSTIC_NAMES:
        return SourceArtifactClass.DIAGNOSTIC_ONLY

    if "/outline/section_drafts/" in normalized:
        return SourceArtifactClass.DIAGNOSTIC_ONLY

    if normalized.endswith("/draft/context/run_paused.json"):
        return SourceArtifactClass.DIAGNOSTIC_ONLY

    if "/logs/" in normalized:
        return SourceArtifactClass.DIAGNOSTIC_ONLY

    if filename in ARTIFACT_CLASS_LABELS:
        return SourceArtifactClass(filename)

    return SourceArtifactClass.DIAGNOSTIC_ONLY
