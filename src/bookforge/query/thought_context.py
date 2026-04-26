from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, ScopeSelector, TimelineNodeRef
from bookforge.llm.signatures import load_signature_ledger

from .workspace import current_execution_node


def _matches_int(record: Dict[str, Any], keys: tuple[str, ...], expected: Optional[int]) -> bool:
    if expected is None:
        return True
    raw_values = [record.get(key) for key in keys]
    present_values = [value for value in raw_values if value not in (None, "")]
    if not present_values:
        return True
    for value in present_values:
        try:
            if int(value) == int(expected):
                return True
        except (TypeError, ValueError):
            continue
    return False


def _matches_text(record: Dict[str, Any], key: str, expected: Optional[str]) -> bool:
    if expected is None:
        return True
    actual = str(record.get(key) or "").strip()
    if not actual:
        return True
    return actual == str(expected).strip()


def _candidate_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    keep = {
        "signature_id": record.get("signature_id"),
        "created_at": record.get("created_at"),
        "label": record.get("label"),
        "provider": record.get("provider"),
        "model": record.get("model"),
        "book_id": record.get("book_id"),
        "workflow_family": record.get("workflow_family"),
        "phase_id": record.get("phase_id"),
        "turn_id": record.get("turn_id"),
        "chapter_id": record.get("chapter_id"),
        "scene_id": record.get("scene_id"),
        "scope": record.get("scope"),
        "assistant_parts_path": record.get("assistant_parts_path"),
        "log_path": record.get("log_path"),
    }
    return {key: value for key, value in keep.items() if value not in (None, "")}


@dataclass(frozen=True, slots=True)
class ThoughtContextProjectionView:
    book_id: str
    selector: ScopeSelector
    candidate_signatures: List[Dict[str, Any]]
    selected_signatures: List[Dict[str, Any]]
    phase_id: Optional[str]
    turn_id: str
    context_role: str
    artifact_status: str
    limitations: List[str]
    node: Optional[TimelineNodeRef] = None
    schema_version: str = "thought_context_projection_view_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "selector": self.selector.to_dict(),
            "node": self.node.to_dict() if self.node else None,
            "candidate_signatures": [dict(item) for item in self.candidate_signatures],
            "selected_signatures": [dict(item) for item in self.selected_signatures],
            "phase_id": self.phase_id,
            "turn_id": self.turn_id,
            "context_role": self.context_role,
            "artifact_status": self.artifact_status,
            "limitations": list(self.limitations),
        }


def get_thought_context_projection(
    workspace,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    workflow_family: Optional[str] = None,
    phase_id: Optional[str] = None,
    limit: int = 8,
    prefer_emitted: bool = True,
) -> ThoughtContextProjectionView:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    node = current_execution_node(workspace, book_id, branch_id=resolved_branch_id, prefer_emitted=prefer_emitted)
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=resolved_branch_id,
        workflow_family=workflow_family or "section_write",
        chapter=chapter_id,
        section=section_id,
        scene=scene_id,
        phase_id=phase_id,
        turn_id="T1",
    )

    candidates: List[Dict[str, Any]] = []
    for record in load_signature_ledger(workspace, limit=None):
        if str(record.get("book_id") or "").strip() != str(book_id).strip():
            continue
        if str(record.get("turn_id") or "").strip().upper() != "T1":
            continue
        if not _matches_text(record, "workflow_family", workflow_family):
            continue
        if not _matches_text(record, "phase_id", phase_id):
            continue
        if not _matches_int(record, ("chapter_id", "chapter"), chapter_id):
            continue
        if not _matches_int(record, ("scene_id", "scene"), scene_id):
            continue
        candidates.append(_candidate_from_record(record))

    if limit > 0:
        selected = candidates[-limit:]
    else:
        selected = list(candidates)

    return ThoughtContextProjectionView(
        book_id=book_id,
        selector=selector,
        node=node,
        candidate_signatures=candidates,
        selected_signatures=selected,
        phase_id=phase_id,
        turn_id="T1",
        context_role="planning_reuse",
        artifact_status="diagnostic",
        limitations=[
            "thought signatures are context aids only",
            "execution receipts remain the truth of what happened",
        ],
    )
