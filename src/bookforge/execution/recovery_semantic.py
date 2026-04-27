from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ProducedArtifactReceipt
from bookforge.query.recovery import (
    get_recovery_blast_radius,
    get_recovery_branch_health,
    get_recovery_manifest,
    get_recovery_semantic_review_readiness,
    recovery_semantic_review_path,
)
from bookforge.supervision import capture_surface_snapshot

from .recovery_common import (
    advance_recovery_node,
    book_root,
    emit_result,
    now_token,
    relative,
    write_json,
    write_receipt,
    write_recovery_manifest,
)


def _review_scope(manifest: Dict[str, Any]) -> Dict[str, Any]:
    scope = manifest.get("scope") if isinstance(manifest.get("scope"), dict) else {}
    return {
        "affected_scopes": [dict(item) for item in scope.get("affected_scopes", []) if isinstance(item, dict)],
        "downstream_scopes": [dict(item) for item in scope.get("downstream_scopes", []) if isinstance(item, dict)],
    }


def _reviewed_artifacts(blast_radius: Dict[str, Any]) -> List[Dict[str, Any]]:
    reviewed: List[Dict[str, Any]] = []
    for impact in blast_radius.get("artifact_impacts") or []:
        if not isinstance(impact, dict):
            continue
        path = str(impact.get("path") or "").strip()
        if not path:
            continue
        reviewed.append(
            {
                "path": path,
                "family": str(impact.get("family") or "unknown"),
                "artifact_status": str(impact.get("artifact_status") or "diagnostic"),
                "exists": bool(impact.get("exists")),
                "safe_as_canonical": bool(impact.get("safe_as_canonical")),
            }
        )
    return reviewed


def _semantic_findings(readiness: Dict[str, Any], blast_radius: Dict[str, Any], manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    semantic_status = readiness.get("semantic_validation_status")
    if semantic_status in {None, "deferred"}:
        findings.append(
            {
                "category": "semantic_continuity_risk",
                "severity": "medium",
                "message": (
                    "Structural recovery validation passed, but semantic continuity and story-quality review are still author-level gates."
                ),
                "evidence": ["recovery_branch_health.semantic_validation"],
            }
        )
    downstream = _review_scope(manifest)["downstream_scopes"]
    if downstream:
        findings.append(
            {
                "category": "downstream_dependency_risk",
                "severity": "medium",
                "message": "Recovery manifest declares downstream scopes that require author review after redraft.",
                "scopes": downstream,
                "evidence": ["recovery_manifest.scope.downstream_scopes"],
            }
        )
    unsupported = [str(item) for item in blast_radius.get("unsupported_families") or [] if str(item).strip()]
    if unsupported:
        findings.append(
            {
                "category": "human_decision_required",
                "severity": "medium",
                "message": "Some impacted artifact families are outside the current recovery mutation set.",
                "families": unsupported,
                "evidence": ["recovery_blast_radius.unsupported_families"],
            }
        )
    if not blast_radius.get("artifact_impacts"):
        findings.append(
            {
                "category": "missing_evidence",
                "severity": "low",
                "message": "No blast-radius artifact impacts were available for semantic review.",
                "evidence": ["recovery_blast_radius.artifact_impacts"],
            }
        )
    return findings


def review_recovery_semantics(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "review_recovery_semantics":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("review_recovery_semantics requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    readiness = get_recovery_semantic_review_readiness(workspace, book_id, branch_id=branch_id)
    if not readiness.get("ready"):
        raise ValueError(f"review_recovery_semantics is not ready: {readiness.get('blockers') or []}")

    manifest = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    health = get_recovery_branch_health(workspace, book_id, branch_id=branch_id)
    blast_radius = get_recovery_blast_radius(workspace, book_id, branch_id=branch_id)
    node = advance_recovery_node(workspace, book_id, branch_id, "review_recovery_semantics")
    review_path = recovery_semantic_review_path(root, branch_id)
    rel_review_path = relative(root, review_path)
    findings = _semantic_findings(readiness, blast_radius, manifest)
    status = "reviewed_attention_required" if findings else "reviewed_clean"
    semantic_validation = {
        "status": status,
        "reviewed_at": now_token(),
        "artifact_path": rel_review_path,
        "finding_count": len(findings),
        "note": "Diagnostic semantic review emitted. Findings are author/Nanda-facing evidence, not automatic mutation authority.",
    }
    payload = {
        "schema_version": "recovery_semantic_review_v1",
        "book_id": book_id,
        "branch_id": branch_id,
        "node": node.to_dict(),
        "artifact_status": "diagnostic",
        "status": status,
        "review_scope": _review_scope(manifest),
        "structural_health_status": health.status,
        "reviewed_artifacts": _reviewed_artifacts(blast_radius),
        "findings": findings,
        "blocked_actions": ["semantic_auto_approval"] if findings else [],
        "recommended_next_action": "author_review_recovery_findings" if findings else "promote_recovery_branch",
        "confidence": "medium" if findings else "low",
        "review_limitations": [
            "This diagnostic action assembles evidence from recovery artifacts; it does not rewrite prose or prove story quality.",
            "Author/Nanda review remains responsible for deciding whether findings require downstream mutation.",
        ],
        "readiness": readiness,
    }
    write_json(review_path, payload)

    manifest_payload = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    validation = manifest_payload.get("validation") if isinstance(manifest_payload.get("validation"), dict) else {}
    validation["semantic_validation"] = semantic_validation
    manifest_payload["validation"] = validation
    manifest_payload["updated_at"] = now_token()
    write_recovery_manifest(root, branch_id, manifest_payload)

    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="review_recovery_semantics",
        status="success",
        message="Recovery semantic review diagnostic emitted.",
        artifact_paths={"semantic_review": rel_review_path},
        details={
            "semantic_validation": semantic_validation,
            "finding_count": len(findings),
            "review_status": status,
            "recommended_next_action": payload["recommended_next_action"],
        },
    )
    artifact = ProducedArtifactReceipt(
        artifact_key="recovery_semantic_review",
        label="Recovery semantic review",
        artifact_status="diagnostic",
        path=rel_review_path,
        format="json",
        consumable=True,
        replaceable=True,
        details={"status": status, "finding_count": len(findings)},
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status="success",
        message="Recovery semantic review diagnostic emitted.",
        receipt=receipt,
        artifact_paths={"semantic_review": rel_review_path},
        produced_artifacts=[artifact],
        details={"semantic_review": payload},
        before_snapshot=before_snapshot,
    )
