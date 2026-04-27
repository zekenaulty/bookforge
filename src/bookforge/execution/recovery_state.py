from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from bookforge.characters import create_character_state_path
from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID
from bookforge.memory.durable_state import ensure_durable_state_files
from bookforge.query.recovery import get_recovery_manifest, get_state_rebuild_preview, recovery_dir
from bookforge.supervision import capture_surface_snapshot
from bookforge.util.schema import SCHEMA_VERSION, validate_json
from bookforge.workspace import DEFAULT_BUDGETS

from .recovery_artifacts import _move_to_quarantine
from .recovery_common import (
    advance_recovery_node,
    book_root,
    emit_result,
    execution_root,
    load_recovery_scope,
    read_json,
    record_promotion_removals,
    relative,
    write_json,
    write_receipt,
)


def _outline_character_entries(outline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    entries: Dict[str, Dict[str, Any]] = {}
    characters = outline.get("characters") if isinstance(outline.get("characters"), list) else []
    for entry in characters:
        if not isinstance(entry, dict):
            continue
        char_id = str(entry.get("character_id") or entry.get("id") or "").strip()
        if not char_id:
            continue
        entries[char_id] = dict(entry)

    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_chars = scene.get("characters") if isinstance(scene.get("characters"), list) else []
                for raw in scene_chars:
                    if isinstance(raw, dict):
                        char_id = str(raw.get("character_id") or raw.get("id") or raw.get("name") or "").strip()
                        if char_id:
                            entries.setdefault(char_id, dict(raw))
                    else:
                        char_id = str(raw or "").strip()
                        if char_id:
                            entries.setdefault(char_id, {"character_id": char_id, "name": char_id.replace("_", " ").title()})
    return entries


def _clean_state_from_outline(outline: Dict[str, Any], existing_state: Dict[str, Any]) -> Dict[str, Any]:
    existing_budgets = existing_state.get("budgets") if isinstance(existing_state.get("budgets"), dict) else {}
    budgets = dict(DEFAULT_BUDGETS)
    for key, value in existing_budgets.items():
        budgets[key] = value
    status = "OUTLINED" if outline else str(existing_state.get("status") or "OUTLINED")
    state = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "cursor": {"chapter": 0, "scene": 0},
        "world": {
            "time": {},
            "location": "",
            "cast_present": [],
            "open_threads": [],
            "recent_facts": [],
        },
        "summary": {
            "last_scene": [],
            "chapter_so_far": [],
            "story_so_far": [],
            "key_facts_ring": [],
            "must_stay_true": [],
            "pending_story_rollups": [],
        },
        "budgets": budgets,
        "duplication_warnings_in_row": 0,
    }
    validate_json(state, "state")
    return state


def _minimal_character_state(character_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
    state = {
        "schema_version": "1.0",
        "character_id": character_id,
        "name": str(entry.get("name") or character_id.replace("_", " ").title()).strip(),
        "inventory": [],
        "containers": [],
        "invariants": [],
        "history": [],
        "artifact_status": "authoritative",
        "rebuild_source": "normalized_outline",
    }
    role = str(entry.get("role") or "").strip()
    if role:
        state["role"] = role
    intro = entry.get("intro")
    if isinstance(intro, dict):
        state["intro"] = dict(intro)
    appearance_base = entry.get("appearance_base")
    if isinstance(appearance_base, dict):
        state["appearance_base"] = dict(appearance_base)
    return state


def _write_character_baseline(branch_root: Path, outline: Dict[str, Any]) -> List[str]:
    entries = _outline_character_entries(outline)
    written: List[str] = []
    for char_id, entry in sorted(entries.items()):
        state_path = create_character_state_path(branch_root, char_id)
        payload = _minimal_character_state(char_id, entry)
        write_json(state_path, payload)
        written.append(relative(branch_root, state_path))
    return written


def _reset_context_baseline(branch_root: Path) -> List[str]:
    context = branch_root / "draft" / "context"
    context.mkdir(parents=True, exist_ok=True)
    (context / "bible.md").write_text("", encoding="utf-8")
    (context / "last_excerpt.md").write_text("", encoding="utf-8")
    ensure_durable_state_files(branch_root)
    return [
        "draft/context/bible.md",
        "draft/context/last_excerpt.md",
        "draft/context/item_registry.json",
        "draft/context/plot_devices.json",
        "draft/context/durable_commits.json",
        "draft/context/items/index.json",
        "draft/context/plot_devices/index.json",
    ]


def _paths_to_quarantine(preview: Dict[str, Any]) -> List[str]:
    return [str(item).strip() for item in preview.get("candidate_paths", []) if str(item).strip()]


def rebuild_state_scope(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "rebuild_state_scope":
        raise ValueError("Unsupported execution action.")
    branch_id = str(request.branch_id or request.selector.branch_id or "").strip()
    if not branch_id or branch_id == MAIN_BRANCH_ID:
        raise ValueError("rebuild_state_scope requires a derived recovery branch.")
    book_id = request.selector.book_id
    root = book_root(workspace, book_id)
    branch_root = execution_root(root, branch_id)
    manifest = get_recovery_manifest(workspace, book_id, branch_id=branch_id)
    load_recovery_scope(manifest)
    before_snapshot = capture_surface_snapshot(workspace, book_id, branch_id=branch_id)

    existing_state = read_json(branch_root / "state.json")
    preview = get_state_rebuild_preview(workspace, book_id, branch_id=branch_id)
    moved = _move_to_quarantine(root, branch_id, _paths_to_quarantine(preview), action="rebuild_state_scope")
    removed = [item["source"] for item in moved]

    outline = read_json(branch_root / "outline" / "outline.json")
    state_path = write_json(branch_root / "state.json", _clean_state_from_outline(outline, existing_state))
    rebuilt_context = _reset_context_baseline(branch_root)
    rebuilt_characters = _write_character_baseline(branch_root, outline)

    removals_path = record_promotion_removals(root, branch_id, removed)
    advance_recovery_node(workspace, book_id, branch_id, "rebuild_state_scope")
    receipt = write_receipt(
        workspace,
        book_id,
        branch_id,
        action="rebuild_state_scope",
        status="success",
        message=f"Rebuilt branch-local state baseline and quarantined {len(moved)} state/projection artifacts.",
        artifact_paths={
            "state": relative(branch_root, state_path),
            "promotion_removals": relative(root, removals_path),
        },
        removed_active_paths=removed,
        quarantined_paths=moved,
        details={
            "rebuild_mode": "full_book_context_reset_from_normalized_outline",
            "candidate_count": len(preview.get("candidate_paths", []) or []),
            "rebuilt_context_artifacts": rebuilt_context,
            "rebuilt_character_states": rebuilt_characters,
            "unsupported_state_families": [],
        },
    )
    return emit_result(
        workspace,
        book_id,
        request,
        status="success",
        message=f"Rebuilt branch-local state baseline and quarantined {len(moved)} state/projection artifacts.",
        receipt=receipt,
        artifact_paths={"state": relative(branch_root, state_path), "promotion_removals": relative(root, removals_path)},
        before_snapshot=before_snapshot,
    )
