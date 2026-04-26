from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, ScopeSelector, TimelineNodeRef

from . import _common
from .workspace import current_execution_node


def _artifact_relpath(book_root: Path, path: Path) -> str:
    try:
        return path.relative_to(book_root).as_posix()
    except ValueError:
        return path.as_posix()


def _scene_setting_dir(book_root: Path, chapter: int, scene: int) -> Path:
    return book_root / "draft" / "context" / "settings" / f"ch_{chapter:03d}" / f"scene_{scene:03d}"


def _read_projection(path: Path) -> Dict[str, Any]:
    return _common.read_json(path) or {}


def _outline_scene(book_root: Path, chapter_id: int, scene_id: int) -> Optional[Dict[str, Any]]:
    outline = _common.load_outline(book_root)
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict) or _common.coerce_int(chapter.get("chapter_id")) != chapter_id:
            continue
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
            for scene in scenes:
                if isinstance(scene, dict) and _common.coerce_int(scene.get("scene_id")) == scene_id:
                    return scene
    return None


def _first_string(payload: Dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _list_field(payload: Dict[str, Any], keys: tuple[str, ...]) -> List[Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return list(value)
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    return []


@dataclass(frozen=True, slots=True)
class SceneSettingProjectionView:
    book_id: str
    selector: ScopeSelector
    setting_status: str
    artifact_status: str
    source_mode: str
    source_artifacts: List[str]
    location_id: Optional[str]
    location_label: Optional[str]
    background_details: List[Any]
    sensory_anchors: List[Any]
    continuity_constraints: List[Any]
    node: Optional[TimelineNodeRef] = None
    schema_version: str = "scene_setting_projection_view_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "setting_status": self.setting_status,
            "artifact_status": self.artifact_status,
            "source_mode": self.source_mode,
            "source_artifacts": list(self.source_artifacts),
            "location_id": self.location_id,
            "location_label": self.location_label,
            "background_details": list(self.background_details),
            "sensory_anchors": list(self.sensory_anchors),
            "continuity_constraints": list(self.continuity_constraints),
        }


def get_scene_setting_projection(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    prefer_emitted: bool = True,
) -> SceneSettingProjectionView:
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

    setting_dir = _scene_setting_dir(book_root, int(chapter_id), int(scene_id))
    author_path = setting_dir / "author_drafted.setting.json"
    prose_path = setting_dir / "prose_extracted.setting.json"
    source_artifacts: List[str] = []

    payload: Dict[str, Any] = {}
    source_mode = "missing"
    artifact_status = "diagnostic"
    if author_path.exists():
        payload = _read_projection(author_path)
        source_artifacts.append(_artifact_relpath(book_root, author_path))
        source_mode = "author_drafted"
        artifact_status = "provisional"
    elif prose_path.exists():
        payload = _read_projection(prose_path)
        source_artifacts.append(_artifact_relpath(book_root, prose_path))
        source_mode = "prose_extracted"
        artifact_status = "derived"
    else:
        outline_scene = _outline_scene(book_root, int(chapter_id), int(scene_id)) or {}
        if outline_scene:
            payload = outline_scene
            source_artifacts.append("outline/outline.json")
            source_mode = "outline_derived"
            artifact_status = "derived"

    location_id = _first_string(payload, ("location_id", "location_start_id", "location_end_id"))
    location_label = _first_string(payload, ("location_label", "location", "location_start", "location_end", "setting_label"))
    background_details = _list_field(payload, ("background_details", "visual_background", "setting_details", "details"))
    sensory_anchors = _list_field(payload, ("sensory_anchors", "transition_in_anchors", "transition_out_anchors", "anchors"))
    continuity_constraints = _list_field(payload, ("continuity_constraints", "constraints", "handoff_constraints"))

    has_setting = bool(location_id or location_label or background_details or sensory_anchors or continuity_constraints)
    return SceneSettingProjectionView(
        book_id=book_id,
        selector=selector,
        node=node,
        setting_status="available" if has_setting else "missing",
        artifact_status=artifact_status,
        source_mode=source_mode,
        source_artifacts=source_artifacts,
        location_id=location_id,
        location_label=location_label,
        background_details=background_details,
        sensory_anchors=sensory_anchors,
        continuity_constraints=continuity_constraints,
    )
