from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, ScopeSelector, TimelineNodeRef
from bookforge.contracts.vocabulary import is_valid_produced_artifact_status

from . import _common
from .workspace import current_execution_node


def _artifact_relpath(book_root: Path, path: Path) -> str:
    try:
        return path.relative_to(book_root).as_posix()
    except ValueError:
        return path.as_posix()


def _character_index(book_root: Path) -> Dict[str, str]:
    payload = _common.read_json(book_root / "draft" / "context" / "characters" / "index.json") or {}
    entries = payload.get("characters") if isinstance(payload.get("characters"), list) else []
    indexed: Dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        character_id = str(entry.get("character_id") or "").strip()
        state_path = str(entry.get("state_path") or "").strip()
        if character_id and state_path:
            indexed[character_id] = state_path
    return indexed


def _outline_characters(book_root: Path) -> Dict[str, Dict[str, Any]]:
    outline = _common.load_outline(book_root)
    characters = outline.get("characters") if isinstance(outline.get("characters"), list) else []
    by_id: Dict[str, Dict[str, Any]] = {}
    for entry in characters:
        if not isinstance(entry, dict):
            continue
        character_id = str(entry.get("character_id") or "").strip()
        if character_id:
            by_id[character_id] = entry
    return by_id


def _state_artifact_status(state: Dict[str, Any], has_appearance: bool) -> str:
    raw = str(
        state.get("appearance_artifact_status")
        or state.get("artifact_status")
        or ""
    ).strip()
    if raw and is_valid_produced_artifact_status(raw):
        return raw
    if not has_appearance:
        return "diagnostic"
    if bool(state.get("appearance_projection_pending")):
        return "provisional"
    return "derived"


def _last_touched_position(state: Dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
    raw = state.get("last_touched") if isinstance(state.get("last_touched"), dict) else {}
    chapter = _common.coerce_int(raw.get("chapter") or raw.get("chapter_id"))
    scene = _common.coerce_int(raw.get("scene") or raw.get("scene_id"))
    return chapter, scene


def _staleness_reason(state: Dict[str, Any], *, chapter: Optional[int], scene: Optional[int]) -> Optional[str]:
    if bool(state.get("appearance_projection_pending")):
        return "appearance_projection_pending"
    last_chapter, last_scene = _last_touched_position(state)
    if chapter is None:
        return None
    if last_chapter is None:
        return None
    if last_chapter < chapter:
        return "last_touched_before_requested_scene"
    if scene is not None and last_chapter == chapter and last_scene is not None and last_scene < scene:
        return "last_touched_before_requested_scene"
    return None


def _visible_scene_details(appearance_current: Any) -> Dict[str, Any]:
    if not isinstance(appearance_current, dict):
        return {}
    visible: Dict[str, Any] = {}
    for key in ("summary", "atoms", "marks", "attire", "appearance_art", "alias_map"):
        value = appearance_current.get(key)
        if isinstance(value, (dict, list, str, int, float, bool)):
            visible[key] = value
    return visible


@dataclass(frozen=True, slots=True)
class AppearanceProjectionView:
    book_id: str
    selector: ScopeSelector
    character_id: str
    character_name: Optional[str]
    appearance_status: str
    artifact_status: str
    source_artifacts: List[str]
    staleness_reason: Optional[str]
    visible_scene_details: Dict[str, Any]
    last_refreshed_node: Optional[Dict[str, Any]]
    state_path: Optional[str]
    node: Optional[TimelineNodeRef] = None
    schema_version: str = "appearance_projection_view_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "character_id": self.character_id,
            "character_name": self.character_name,
            "appearance_status": self.appearance_status,
            "artifact_status": self.artifact_status,
            "source_artifacts": list(self.source_artifacts),
            "staleness_reason": self.staleness_reason,
            "visible_scene_details": dict(self.visible_scene_details),
            "last_refreshed_node": dict(self.last_refreshed_node) if isinstance(self.last_refreshed_node, dict) else None,
            "state_path": self.state_path,
        }


def list_appearance_projection_views(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    character_id: Optional[str] = None,
    prefer_emitted: bool = True,
) -> List[AppearanceProjectionView]:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    canonical_root = _common.book_root(workspace, book_id)
    book_root = _common.execution_book_root(canonical_root, resolved_branch_id)
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=section_id,
        scene=scene_id,
    )

    indexed = _character_index(book_root)
    outline_chars = _outline_characters(book_root)
    target_id = str(character_id or "").strip() or None
    character_ids = sorted(set(indexed) | set(outline_chars))
    if target_id:
        character_ids = [target_id]

    views: List[AppearanceProjectionView] = []
    for char_id in character_ids:
        outline_entry = outline_chars.get(char_id, {})
        rel_state_path = indexed.get(char_id)
        state_path = book_root / rel_state_path if rel_state_path else None
        source_artifacts: List[str] = []
        state: Dict[str, Any] = {}
        if state_path is not None and state_path.exists():
            source_artifacts.append(_artifact_relpath(book_root, state_path))
            state = _common.read_json(state_path) or {}

        appearance_current = state.get("appearance_current") if isinstance(state, dict) else None
        has_appearance = isinstance(appearance_current, dict) and any(
            key in appearance_current for key in ("summary", "atoms", "marks", "attire", "appearance_art")
        )
        reason = _staleness_reason(state, chapter=chapter_id, scene=scene_id) if state else None
        if not state:
            appearance_status = "missing"
        elif not has_appearance:
            appearance_status = "missing"
        elif reason:
            appearance_status = "stale"
        else:
            appearance_status = "current"

        views.append(
            AppearanceProjectionView(
                book_id=book_id,
                selector=selector,
                node=node,
                character_id=char_id,
                character_name=str(state.get("name") or outline_entry.get("name") or "").strip() or None,
                appearance_status=appearance_status,
                artifact_status=_state_artifact_status(state, has_appearance),
                source_artifacts=source_artifacts,
                staleness_reason=reason,
                visible_scene_details=_visible_scene_details(appearance_current),
                last_refreshed_node=state.get("appearance_last_refreshed_node") if isinstance(state.get("appearance_last_refreshed_node"), dict) else None,
                state_path=rel_state_path,
            )
        )

    return views
