from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from bookforge.branching import promote_branch_to_main
from bookforge.branching_store import _evolve_manifest, _load_manifest, _write_manifest
from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ScopeSelector
from bookforge.query import current_main_node, get_integrity_verdict, get_outline_lineage_audit
from bookforge.query.recovery import get_recovery_branch_health, get_recovery_manifest, promotion_removals_path
from bookforge.supervision import paths as supervision_paths
from bookforge.supervision import RuntimeIssue, capture_surface_snapshot

from .recovery_common import (
    advance_recovery_node,
    book_root,
    emit_result,
    now_token,
    read_json,
    request_id,
    write_receipt,
    write_recovery_manifest,
)


_CHARACTER_REF_KEYS = {
    "character",
    "characters",
    "character_id",
    "character_ids",
    "cast",
    "cast_present",
    "custodian",
    "owner",
    "pov_character",
    "speaker",
}


_DEFERRED_SEMANTIC_VALIDATION_FAMILIES = [
    "semantic_continuity",
    "inventory_meaning",
    "setting_meaning",
    "chapter_summary_meaning",
    "appearance_meaning",
    "prose_quality",
]


def _semantic_validation_boundary() -> dict[str, Any]:
    return {
        "status": "deferred",
        "families": list(_DEFERRED_SEMANTIC_VALIDATION_FAMILIES),
        "note": (
            "Recovery validation currently proves structural timeline health only. "
            "Semantic continuity, story quality, and meaning-level inventory/setting/appearance checks remain author/Nanda review gates."
        ),
    }


def _outline_character_ids(outline: dict) -> set[str]:
    character_ids: set[str] = set()
    for item in outline.get("characters") or []:
        if isinstance(item, dict):
            character_id = str(item.get("character_id") or "").strip()
            if character_id:
                character_ids.add(character_id)
    for chapter in outline.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        for section in chapter.get("sections") or []:
            if not isinstance(section, dict):
                continue
            for scene in section.get("scenes") or []:
                if not isinstance(scene, dict):
                    continue
                for character_id in scene.get("characters") or []:
                    cleaned = str(character_id or "").strip()
                    if cleaned:
                        character_ids.add(cleaned)
    return character_ids


def _looks_like_reference_id(text: str) -> bool:
    cleaned = str(text or "").strip()
    if not cleaned:
        return False
    if re.search(r"^(char|character|rhea|vance|unit)_", cleaned, flags=re.IGNORECASE):
        return True
    return bool(re.search(r"^[a-z][a-z0-9]+(?:_[a-z0-9]+)+$", cleaned))


def _outline_thread_ids(outline: dict) -> set[str]:
    thread_ids: set[str] = set()
    for item in outline.get("threads") or []:
        if isinstance(item, dict):
            thread_id = str(item.get("thread_id") or item.get("id") or "").strip()
        else:
            thread_id = str(item or "").strip()
        if thread_id:
            thread_ids.add(thread_id)
    for chapter in outline.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        for section in chapter.get("sections") or []:
            if not isinstance(section, dict):
                continue
            for scene in section.get("scenes") or []:
                if not isinstance(scene, dict):
                    continue
                for thread_id in scene.get("threads") or []:
                    cleaned = str(thread_id or "").strip()
                    if cleaned:
                        thread_ids.add(cleaned)
    return thread_ids


def _iter_recovery_scopes(manifest_payload: dict) -> list[dict]:
    scope = manifest_payload.get("scope") if isinstance(manifest_payload.get("scope"), dict) else {}
    rows = []
    for key in ("affected_scopes", "downstream_scopes"):
        values = scope.get(key) if isinstance(scope.get(key), list) else []
        for item in values:
            if isinstance(item, dict):
                rows.append(dict(item))
    return rows


def _scope_key(chapter_id: int, section_id: int | None) -> str:
    if section_id is None:
        return f"ch_{int(chapter_id):03d}"
    return f"ch_{int(chapter_id):03d}_sec_{int(section_id):03d}"


def _scene_ids_for_scope(manifest_payload: dict, scope: dict) -> list[int]:
    try:
        chapter_id = int(scope.get("chapter_id") or scope.get("chapter"))
    except (TypeError, ValueError):
        return []
    section_id_raw = scope.get("section_id", scope.get("section"))
    try:
        section_id = int(section_id_raw) if section_id_raw is not None else None
    except (TypeError, ValueError):
        section_id = None
    ranges = manifest_payload.get("scope_output_ranges") if isinstance(manifest_payload.get("scope_output_ranges"), dict) else {}
    row = ranges.get(_scope_key(chapter_id, section_id)) if isinstance(ranges, dict) else None
    if not isinstance(row, dict):
        return []
    scene_ids: list[int] = []
    for value in row.get("scene_ids") or []:
        try:
            scene_id = int(value)
        except (TypeError, ValueError):
            continue
        if scene_id >= 1:
            scene_ids.append(scene_id)
    return sorted(set(scene_ids))


def _scoped_projection_paths(branch_root: Path, manifest_payload: dict) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for scope in _iter_recovery_scopes(manifest_payload):
        try:
            chapter_id = int(scope.get("chapter_id") or scope.get("chapter"))
        except (TypeError, ValueError):
            continue
        summary_path = branch_root / "draft" / "context" / "chapter_summaries" / f"ch_{chapter_id:03d}.json"
        if summary_path.exists() and summary_path not in seen:
            seen.add(summary_path)
            paths.append(("chapter summary", summary_path))
        for scene_id in _scene_ids_for_scope(manifest_payload, scope):
            for family, rel_dir in (
                ("setting projection", f"draft/context/settings/ch_{chapter_id:03d}/scene_{scene_id:03d}"),
                ("appearance projection", f"draft/context/appearance/ch_{chapter_id:03d}/scene_{scene_id:03d}"),
            ):
                base = branch_root / rel_dir
                if not base.exists():
                    continue
                for path in sorted(base.rglob("*.json")):
                    if path.is_file() and path not in seen:
                        seen.add(path)
                        paths.append((family, path))
    return paths


def _affected_chapter_ids(manifest_payload: dict) -> list[int]:
    chapter_ids: list[int] = []
    for scope in _iter_recovery_scopes(manifest_payload):
        try:
            chapter_id = int(scope.get("chapter_id") or scope.get("chapter"))
        except (TypeError, ValueError):
            continue
        if chapter_id >= 1:
            chapter_ids.append(chapter_id)
    return sorted(set(chapter_ids))


def _character_reference_blockers(
    payload: Any,
    allowed_character_ids: set[str],
    *,
    rel_path: str,
    artifact_label: str,
    context_key: str | None = None,
) -> list[str]:
    blockers: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            cleaned_key = str(key or "").strip().lower()
            blockers.extend(
                _character_reference_blockers(
                    value,
                    allowed_character_ids,
                    rel_path=rel_path,
                    artifact_label=artifact_label,
                    context_key=cleaned_key,
                )
            )
        return blockers
    if isinstance(payload, list):
        for item in payload:
            blockers.extend(
                _character_reference_blockers(
                    item,
                    allowed_character_ids,
                    rel_path=rel_path,
                    artifact_label=artifact_label,
                    context_key=context_key,
                )
            )
        return blockers
    if not isinstance(payload, str):
        return blockers
    text = payload.strip()
    if not text:
        return blockers
    candidates: set[str] = set()
    if context_key in _CHARACTER_REF_KEYS and _looks_like_reference_id(text):
        candidates.add(text)
    candidates.update(match.group(0) for match in re.finditer(r"\bchar_[a-zA-Z0-9_]+\b", text, flags=re.IGNORECASE))
    for character_id in sorted(candidates):
        if character_id and character_id not in allowed_character_ids:
            blockers.append(f"{artifact_label} references non-outline character: {character_id} at {rel_path}")
    return blockers


def _read_validation_payload(path: Path) -> Any:
    if path.suffix.lower() == ".json":
        return read_json(path)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _thread_reference_blockers(
    payload: Any,
    allowed_thread_ids: set[str],
    *,
    rel_path: str,
    artifact_label: str,
) -> list[str]:
    if not allowed_thread_ids:
        return []
    blockers: list[str] = []
    if isinstance(payload, dict):
        for value in payload.values():
            blockers.extend(_thread_reference_blockers(value, allowed_thread_ids, rel_path=rel_path, artifact_label=artifact_label))
        return blockers
    if isinstance(payload, list):
        for item in payload:
            blockers.extend(_thread_reference_blockers(item, allowed_thread_ids, rel_path=rel_path, artifact_label=artifact_label))
        return blockers
    if not isinstance(payload, str):
        return blockers
    for thread_id in sorted({match.group(0) for match in re.finditer(r"\bTHREAD_[a-zA-Z0-9_]+\b", payload)}):
        if thread_id not in allowed_thread_ids:
            blockers.append(f"{artifact_label} references non-outline thread: {thread_id} at {rel_path}")
    return blockers


def _continuity_artifact_paths(branch_root: Path, manifest_payload: dict) -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    context = branch_root / "draft" / "context"
    for label, path in (
        ("continuity pack", context / "continuity_pack.json"),
        ("world bible", context / "bible.md"),
        ("last excerpt", context / "last_excerpt.md"),
    ):
        if path.exists():
            candidates.append((label, path))
    history_root = context / "continuity_history"
    if history_root.exists():
        candidates.extend(("continuity history", path) for path in sorted(history_root.rglob("*.json")) if path.is_file())
    for chapter_id in _affected_chapter_ids(manifest_payload):
        chapter_seam_root = context / "chapter_seams" / f"ch_{chapter_id:03d}"
        if chapter_seam_root.exists():
            candidates.extend(("chapter seam artifact", path) for path in sorted(chapter_seam_root.rglob("*.json")) if path.is_file())
    return candidates


def _projection_lineage_blockers(payload: dict, *, branch_id: str, rel_path: str, artifact_label: str) -> list[str]:
    blockers: list[str] = []
    for key in ("node", "selector"):
        value = payload.get(key)
        if not isinstance(value, dict):
            continue
        embedded_branch = str(value.get("branch_id") or "").strip()
        if embedded_branch and embedded_branch != branch_id:
            blockers.append(f"{artifact_label} has stale {key} branch {embedded_branch} at {rel_path}")
    return blockers


def _durable_artifact_paths(branch_root: Path) -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    context = branch_root / "draft" / "context"
    for label, path in (
        ("item registry", context / "item_registry.json"),
        ("item index", context / "items" / "index.json"),
        ("plot device registry", context / "plot_devices.json"),
        ("plot device index", context / "plot_devices" / "index.json"),
        ("durable commits", context / "durable_commits.json"),
    ):
        if path.exists():
            candidates.append((label, path))
    for label, rel_dir in (
        ("item history", "items/history"),
        ("plot device history", "plot_devices/history"),
    ):
        base = context / rel_dir
        if not base.exists():
            continue
        candidates.extend((label, path) for path in sorted(base.rglob("*.json")) if path.is_file())
    return candidates


def _durable_index_blockers(branch_root: Path) -> list[str]:
    blockers: list[str] = []
    context = branch_root / "draft" / "context"
    item_registry = read_json(context / "item_registry.json")
    item_index = read_json(context / "items" / "index.json")
    registered_items = {
        str(item.get("item_id") or "").strip()
        for item in item_registry.get("items") or []
        if isinstance(item, dict) and str(item.get("item_id") or "").strip()
    }
    for item_id in item_index.get("item_ids") or []:
        cleaned = str(item_id or "").strip()
        if cleaned and cleaned not in registered_items:
            blockers.append(f"item index references missing registry item: {cleaned} at draft/context/items/index.json")
    plot_registry = read_json(context / "plot_devices.json")
    plot_index = read_json(context / "plot_devices" / "index.json")
    registered_devices = {
        str(item.get("device_id") or "").strip()
        for item in plot_registry.get("devices") or []
        if isinstance(item, dict) and str(item.get("device_id") or "").strip()
    }
    for device_id in plot_index.get("device_ids") or []:
        cleaned = str(device_id or "").strip()
        if cleaned and cleaned not in registered_devices:
            blockers.append(f"plot device index references missing registry device: {cleaned} at draft/context/plot_devices/index.json")
    return blockers


def _state_projection_blockers(workspace: Path, book_id: str, branch_id: str) -> list[str]:
    root = book_root(workspace, book_id)
    branch_root = supervision_paths.branch_snapshot_root(root, branch_id)
    outline = read_json(branch_root / "outline" / "outline.json")
    allowed_character_ids = _outline_character_ids(outline)
    allowed_thread_ids = _outline_thread_ids(outline)
    if not allowed_character_ids:
        return []
    blockers: list[str] = []
    characters_root = branch_root / "draft" / "context" / "characters"
    index_payload = read_json(characters_root / "index.json")
    for item in index_payload.get("characters") or []:
        if not isinstance(item, dict):
            continue
        character_id = str(item.get("character_id") or "").strip()
        if character_id and character_id not in allowed_character_ids:
            blockers.append(f"character index contains non-outline character: {character_id}")
    if characters_root.exists():
        for path in sorted(characters_root.glob("*.state.json")):
            payload = read_json(path)
            character_id = str(payload.get("character_id") or "").strip()
            if character_id and character_id not in allowed_character_ids:
                rel_path = path.relative_to(branch_root).as_posix()
                blockers.append(f"character state contains non-outline character: {character_id} at {rel_path}")
    manifest_payload = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    for artifact_label, path in _scoped_projection_paths(branch_root, manifest_payload):
        payload = read_json(path)
        rel_path = path.relative_to(branch_root).as_posix()
        blockers.extend(
            _character_reference_blockers(
                payload,
                allowed_character_ids,
                rel_path=rel_path,
                artifact_label=artifact_label,
            )
        )
        blockers.extend(_projection_lineage_blockers(payload, branch_id=branch_id, rel_path=rel_path, artifact_label=artifact_label))
    for artifact_label, path in _continuity_artifact_paths(branch_root, manifest_payload):
        payload = _read_validation_payload(path)
        rel_path = path.relative_to(branch_root).as_posix()
        blockers.extend(
            _character_reference_blockers(
                payload,
                allowed_character_ids,
                rel_path=rel_path,
                artifact_label=artifact_label,
            )
        )
        blockers.extend(_thread_reference_blockers(payload, allowed_thread_ids, rel_path=rel_path, artifact_label=artifact_label))
        if isinstance(payload, dict):
            blockers.extend(_projection_lineage_blockers(payload, branch_id=branch_id, rel_path=rel_path, artifact_label=artifact_label))
    for artifact_label, path in _durable_artifact_paths(branch_root):
        payload = read_json(path)
        rel_path = path.relative_to(branch_root).as_posix()
        blockers.extend(
            _character_reference_blockers(
                payload,
                allowed_character_ids,
                rel_path=rel_path,
                artifact_label=artifact_label,
            )
        )
        blockers.extend(_thread_reference_blockers(payload, allowed_thread_ids, rel_path=rel_path, artifact_label=artifact_label))
        blockers.extend(_projection_lineage_blockers(payload, branch_id=branch_id, rel_path=rel_path, artifact_label=artifact_label))
    blockers.extend(_durable_index_blockers(branch_root))
    return blockers


def validate_recovery_branch(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "validate_recovery_branch":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("validate_recovery_branch requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)
    manifest = _load_manifest(root, branch_id)
    audit = get_outline_lineage_audit(workspace, book_id, branch_id=branch_id)
    blockers = []
    if audit.status == "chimera_risk":
        blockers.append("branch still reports chimera_risk")
    actions = {receipt.action for receipt in get_recovery_branch_health(workspace, book_id, branch_id=branch_id).receipts}
    for required in ("quarantine_artifacts", "normalize_outline_scope", "invalidate_scope_outputs", "rebuild_state_scope", "redraft_scope"):
        if required not in actions:
            blockers.append(f"{required} has not completed")
    state_projection_blockers = _state_projection_blockers(workspace, book_id, branch_id)
    blockers.extend(state_projection_blockers)
    semantic_validation = _semantic_validation_boundary()
    status = "success" if not blockers else "integrity_degraded"
    lifecycle = "promote_ready" if not blockers else "needs_review"
    updated = _evolve_manifest(
        manifest,
        lifecycle_state=lifecycle,
        validation_status="passed" if not blockers else "failed",
        validation_message="Recovery branch passed validation." if not blockers else "; ".join(blockers),
    )
    _write_manifest(root, updated)
    manifest_payload = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    manifest_payload["status"] = "validated" if not blockers else "needs_review"
    manifest_payload["updated_at"] = now_token()
    manifest_payload["validation"] = {
        "status": updated.validation_status,
        "blockers": blockers,
        "outline_lineage_status": audit.status,
        "state_projection_blockers": state_projection_blockers,
        "semantic_validation": semantic_validation,
    }
    write_recovery_manifest(root, branch_id, manifest_payload)
    advance_recovery_node(workspace, book_id, branch_id, "validate_recovery_branch")
    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="validate_recovery_branch",
        status=status,
        message=updated.validation_message or "Recovery validation completed.",
        details={
            "blockers": blockers,
            "outline_lineage_status": audit.status,
            "state_projection_blockers": state_projection_blockers,
            "semantic_validation": semantic_validation,
        },
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status=status,
        message=updated.validation_message or "Recovery validation completed.",
        receipt=receipt,
        before_snapshot=before_snapshot,
        runtime_issue=RuntimeIssue(
            category="chimera_risk",
            code="recovery_validation_failed",
            severity="high",
            message="Recovery branch validation failed.",
            details={"blockers": blockers},
        )
        if blockers
        else None,
    )


def promote_recovery_branch(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "promote_recovery_branch":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("promote_recovery_branch requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    health = get_recovery_branch_health(workspace, book_id, branch_id=branch_id)
    if health.status != "healthy":
        raise ValueError(f"Recovery branch {branch_id} is not healthy: {health.blockers}")
    pre_audit = get_outline_lineage_audit(workspace, book_id)
    pre_integrity = get_integrity_verdict(workspace, book_id, prefer_emitted=False)
    planned_removals_payload = read_json(promotion_removals_path(root, branch_id))
    planned_removed_paths = sorted(
        {str(item).strip().replace("\\", "/") for item in planned_removals_payload.get("remove_paths", []) if str(item).strip()}
    )
    promote_branch_to_main(workspace, book_id, branch_id, request_id=request.request_id)
    node = current_main_node(workspace, book_id, prefer_emitted=False)
    if node is None:
        raise ValueError("Unable to resolve main node after recovery promotion.")
    post_audit = get_outline_lineage_audit(workspace, book_id)
    post_integrity = get_integrity_verdict(workspace, book_id, prefer_emitted=False)
    applied_removed_paths = [rel_path for rel_path in planned_removed_paths if not (root / rel_path).exists()]
    postcondition = {
        "schema_version": "recovery_promotion_postcondition_v1",
        "source_branch_id": branch_id,
        "canonical_change_status": "canonical",
        "pre_outline_lineage_status": pre_audit.status,
        "post_outline_lineage_status": post_audit.status,
        "pre_integrity_status": pre_integrity.status,
        "post_integrity_status": post_integrity.status,
        "planned_removed_paths": planned_removed_paths,
        "applied_removed_paths": applied_removed_paths,
        "planned_removed_path_count": len(planned_removed_paths),
        "applied_removed_path_count": len(applied_removed_paths),
        "main_recovered_from_chimera": pre_audit.status == "chimera_risk" and post_audit.status != "chimera_risk",
        "main_outline_lineage_healthy": post_audit.status == "healthy",
        "main_integrity_healthy": post_integrity.status in {"healthy", "passed"},
    }
    return ExecutionResult(
        result_id=request_id(book_id, request.action, branch_id, "success"),
        action=request.action,
        status="success",
        node=node,
        selector=ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID),
        message=f"Recovery branch {branch_id} promoted to main.",
        details={"source_branch_id": branch_id, "recovery_health": health.to_dict(), "postcondition": postcondition},
        emitted_at=now_token(),
        request_id=request.request_id,
    )
