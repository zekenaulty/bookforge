from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, ScopeSelector, TimelineNodeRef

from .appearance import AppearanceProjectionView, list_appearance_projection_views
from .setting import SceneSettingProjectionView, get_scene_setting_projection
from .thought_context import ThoughtContextProjectionView, get_thought_context_projection
from .workspace import current_execution_node


@dataclass(frozen=True, slots=True)
class SceneContextProjectionView:
    book_id: str
    selector: ScopeSelector
    appearance: List[AppearanceProjectionView]
    setting: SceneSettingProjectionView
    thought_context: ThoughtContextProjectionView
    availability: Dict[str, Any]
    node: Optional[TimelineNodeRef] = None
    schema_version: str = "scene_context_projection_view_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "availability": dict(self.availability),
            "appearance": [item.to_dict() for item in self.appearance],
            "setting": self.setting.to_dict(),
            "thought_context": self.thought_context.to_dict(),
        }


def get_scene_context_projection(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    workflow_family: str = "section_write",
    phase_id: Optional[str] = None,
    prefer_emitted: bool = True,
) -> SceneContextProjectionView:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family=workflow_family,
        chapter=chapter_id,
        section=section_id,
        scene=scene_id,
        phase_id=phase_id,
    )
    appearance = list_appearance_projection_views(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        prefer_emitted=prefer_emitted,
    )
    setting = get_scene_setting_projection(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        prefer_emitted=prefer_emitted,
    )
    thought_context = get_thought_context_projection(
        workspace,
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        workflow_family=workflow_family,
        phase_id=phase_id,
        prefer_emitted=prefer_emitted,
    )
    availability = {
        "appearance_available": any(item.appearance_status == "current" for item in appearance),
        "appearance_missing_count": sum(1 for item in appearance if item.appearance_status == "missing"),
        "appearance_stale_count": sum(1 for item in appearance if item.appearance_status == "stale"),
        "setting_available": setting.setting_status == "available",
        "setting_source_mode": setting.source_mode,
        "setting_artifact_status": setting.artifact_status,
        "thought_context_available": bool(thought_context.selected_signatures),
        "thought_context_count": len(thought_context.selected_signatures),
    }
    return SceneContextProjectionView(
        book_id=book_id,
        selector=selector,
        node=node,
        appearance=appearance,
        setting=setting,
        thought_context=thought_context,
        availability=availability,
    )
