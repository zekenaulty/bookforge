from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from bookforge.contracts import MAIN_BRANCH_ID, RecoveryBranchHealth, RecoveryReceipt, RecoveryScope
from bookforge.supervision import paths as supervision_paths

from . import _common
from .outline_lineage import get_outline_lineage_audit
from .workspace import current_execution_node


RECOVERY_DIRNAME = "recovery"
RECOVERY_MANIFEST_FILENAME = "recovery_manifest.json"
RECOVERY_RECEIPTS_FILENAME = "recovery_receipts.jsonl"
PROMOTION_REMOVALS_FILENAME = "promotion_removals.json"
SEMANTIC_REVIEW_FILENAME = "recovery_semantic_review.json"


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
            **approval,
        },
    )
