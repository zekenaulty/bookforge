from __future__ import annotations

from typing import Final, FrozenSet, Literal


WorkflowFamily = Literal[
    "thin_outline",
    "deep_outline",
    "section_local_outline",
    "section_write",
    "recovery_import",
    "author_assets",
    "book_intent",
    "visual_assets",
]

ExecutionResultStatus = Literal[
    "success",
    "no_op",
    "retryable_pause",
    "hard_fail",
    "integrity_degraded",
    "promotion_required",
]

ArtifactClassLabel = Literal[
    "immutable_lineage_anchor",
    "frozen_projection",
    "mutable_compatibility_view",
    "diagnostic_only",
]

ProducedArtifactStatus = Literal[
    "authoritative",
    "provisional",
    "derived",
    "diagnostic",
]


WORKFLOW_FAMILIES: Final[tuple[str, ...]] = (
    "thin_outline",
    "deep_outline",
    "section_local_outline",
    "section_write",
    "recovery_import",
    "author_assets",
    "book_intent",
    "visual_assets",
)

WORKFLOW_FAMILY_DESCRIPTIONS: Final[dict[str, str]] = {
    "thin_outline": "Provider-authored starter/thin outline family rooted in immutable run artifacts, including BookIntent-derived starter outlines that are not full deep-outline pipeline runs.",
    "deep_outline": "Full batch outline pipeline rooted in immutable run artifacts under outline/pipeline_runs/<run_id>/.",
    "section_local_outline": "Section-scoped outline materialization and freeze work driven by workflow commands.",
    "section_write": "Scene planning, write, repair, state-repair, and lint execution for prose generation.",
    "recovery_import": "Explicit recovery/import work that may rebuild state from prior artifacts without pretending to be a same-family resume.",
    "author_assets": "Versioned author persona creation and refinement under workspace/authors/.",
    "book_intent": "Book intent, synopsis, seed approval, and canonical book workspace creation.",
    "visual_assets": "Visual asset prompt planning, provider descriptor, and generated image artifact work.",
}

EXECUTION_RESULT_STATUSES: Final[tuple[str, ...]] = (
    "success",
    "no_op",
    "retryable_pause",
    "hard_fail",
    "integrity_degraded",
    "promotion_required",
)

BRANCH_LIFECYCLE_STATES: Final[tuple[str, ...]] = (
    "active",
    "promote_ready",
    "needs_review",
    "discard",
    "promoted",
    "assembled_pending_promotion",
)

MERGE_OPERATIONS: Final[tuple[str, ...]] = (
    "promotion",
    "assembly",
    "discard",
)

ARTIFACT_CLASS_LABELS: Final[tuple[str, ...]] = (
    "immutable_lineage_anchor",
    "frozen_projection",
    "mutable_compatibility_view",
    "diagnostic_only",
)

PRODUCED_ARTIFACT_STATUSES: Final[tuple[str, ...]] = (
    "authoritative",
    "provisional",
    "derived",
    "diagnostic",
)

MAIN_BRANCH_ID: Final[str] = "main"
ASSEMBLY_BRANCH_PREFIX: Final[str] = "assembly"
CURRENT_NODE_FILENAME: Final[str] = "current_node.json"
BRANCH_MANIFEST_FILENAME: Final[str] = "branch_manifest.json"

_WORKFLOW_FAMILY_SET: Final[FrozenSet[str]] = frozenset(WORKFLOW_FAMILIES)
_EXECUTION_RESULT_STATUS_SET: Final[FrozenSet[str]] = frozenset(EXECUTION_RESULT_STATUSES)
_ARTIFACT_CLASS_SET: Final[FrozenSet[str]] = frozenset(ARTIFACT_CLASS_LABELS)
_PRODUCED_ARTIFACT_STATUS_SET: Final[FrozenSet[str]] = frozenset(PRODUCED_ARTIFACT_STATUSES)


def is_valid_workflow_family(value: str) -> bool:
    return str(value or "").strip() in _WORKFLOW_FAMILY_SET


def is_valid_execution_result_status(value: str) -> bool:
    return str(value or "").strip() in _EXECUTION_RESULT_STATUS_SET


def is_valid_artifact_class(value: str) -> bool:
    return str(value or "").strip() in _ARTIFACT_CLASS_SET


def is_valid_produced_artifact_status(value: str) -> bool:
    return str(value or "").strip() in _PRODUCED_ARTIFACT_STATUS_SET


def is_main_branch(branch_id: str) -> bool:
    return str(branch_id or "").strip() == MAIN_BRANCH_ID


def execution_result_for_branch_lifecycle(lifecycle_state: str) -> str:
    normalized = str(lifecycle_state or "").strip()
    mapping: Final[dict[str, str]] = {
        "active": "retryable_pause",
        "promote_ready": "promotion_required",
        "needs_review": "integrity_degraded",
        "discard": "hard_fail",
        "promoted": "success",
        "assembled_pending_promotion": "promotion_required",
    }
    if normalized not in mapping:
        raise ValueError(f"Unknown lifecycle_state: {lifecycle_state}")
    return mapping[normalized]


def canonical_change_status_for_branch_lifecycle(lifecycle_state: str) -> str:
    normalized = str(lifecycle_state or "").strip()
    mapping: Final[dict[str, str]] = {
        "active": "none",
        "promote_ready": "none",
        "needs_review": "none",
        "discard": "none",
        "promoted": "canonical",
        "assembled_pending_promotion": "none",
    }
    if normalized not in mapping:
        raise ValueError(f"Unknown lifecycle_state: {lifecycle_state}")
    return mapping[normalized]
