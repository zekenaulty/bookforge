from bookforge.contracts import (
    ARTIFACT_CLASS_LABELS,
    EXECUTION_RESULT_STATUSES,
    MAIN_BRANCH_ID,
    MERGE_OPERATIONS,
    PRODUCED_ARTIFACT_STATUSES,
    WORKFLOW_FAMILIES,
    SourceArtifactClass,
    canonical_change_status_for_branch_lifecycle,
    classify_source_artifact,
    execution_result_for_branch_lifecycle,
)


def test_runtime_vocabulary_is_frozen() -> None:
    assert WORKFLOW_FAMILIES == (
        "thin_outline",
        "deep_outline",
        "section_local_outline",
        "section_write",
        "recovery_import",
    )
    assert EXECUTION_RESULT_STATUSES == (
        "success",
        "no_op",
        "retryable_pause",
        "hard_fail",
        "integrity_degraded",
        "promotion_required",
    )
    assert MERGE_OPERATIONS == ("promotion", "assembly", "discard")
    assert MAIN_BRANCH_ID == "main"
    assert ARTIFACT_CLASS_LABELS == (
        "immutable_lineage_anchor",
        "frozen_projection",
        "mutable_compatibility_view",
        "diagnostic_only",
    )
    assert PRODUCED_ARTIFACT_STATUSES == (
        "authoritative",
        "provisional",
        "derived",
        "diagnostic",
    )
    assert execution_result_for_branch_lifecycle("promote_ready") == "promotion_required"
    assert execution_result_for_branch_lifecycle("discard") == "hard_fail"
    assert execution_result_for_branch_lifecycle("assembled_pending_promotion") == "promotion_required"
    assert canonical_change_status_for_branch_lifecycle("active") == "none"
    assert canonical_change_status_for_branch_lifecycle("promoted") == "canonical"


def test_classify_source_artifact_for_lineage_anchor() -> None:
    result = classify_source_artifact(
        "workspace/books/demo/outline/pipeline_runs/20260419_050005/outline_final_v1_1.json"
    )
    assert result is SourceArtifactClass.IMMUTABLE_LINEAGE_ANCHOR


def test_classify_source_artifact_for_frozen_projection() -> None:
    result = classify_source_artifact("workspace/books/demo/outline/outline.thin.json")
    assert result is SourceArtifactClass.FROZEN_PROJECTION


def test_classify_source_artifact_for_boundary_projection() -> None:
    result = classify_source_artifact(
        "workspace/books/demo/outline/boundaries/ch_001_sec_002_boundary.json"
    )
    assert result is SourceArtifactClass.FROZEN_PROJECTION


def test_classify_source_artifact_for_mutable_compatibility_view() -> None:
    result = classify_source_artifact("workspace/books/demo/outline/outline.json")
    assert result is SourceArtifactClass.MUTABLE_COMPATIBILITY_VIEW


def test_classify_source_artifact_for_pipeline_report() -> None:
    result = classify_source_artifact(
        "workspace/books/demo/outline/pipeline_runs/20260419_050005/outline_pipeline_report.json"
    )
    assert result is SourceArtifactClass.DIAGNOSTIC_ONLY


def test_classify_source_artifact_for_backup_snapshot() -> None:
    result = classify_source_artifact(
        "workspace/backups/outline_completed/demo/20260419_050005_20260420_000001/outline_snapshot/outline.json"
    )
    assert result is SourceArtifactClass.FROZEN_PROJECTION
