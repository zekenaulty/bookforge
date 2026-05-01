from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bookforge.contracts import MAIN_BRANCH_ID, TimelineNodeRef
from bookforge.pipeline.chapter_seam import scene_pair_seam_report_path

from . import _common
from .workspace import current_execution_node


def _relative_to(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


@dataclass(frozen=True, slots=True)
class ScenePairSeamQueueItem:
    chapter_id: int
    scene_a_id: int
    scene_b_id: int
    section_a_id: Optional[int]
    section_b_id: Optional[int]
    scene_a_path: str
    scene_b_path: str
    scene_a_exists: bool
    scene_b_exists: bool
    status: str
    action: Optional[str] = None
    blocked_reason: Optional[str] = None
    report_path: Optional[str] = None
    report_status: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "scene_pair_seam_queue_item_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "chapter_id": self.chapter_id,
            "scene_a_id": self.scene_a_id,
            "scene_b_id": self.scene_b_id,
            "section_a_id": self.section_a_id,
            "section_b_id": self.section_b_id,
            "scene_a_path": self.scene_a_path,
            "scene_b_path": self.scene_b_path,
            "scene_a_exists": bool(self.scene_a_exists),
            "scene_b_exists": bool(self.scene_b_exists),
            "status": self.status,
            "action": self.action,
            "blocked_reason": self.blocked_reason,
            "report_path": self.report_path,
            "report_status": self.report_status,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class ChapterSeamQueue:
    book_id: str
    branch_id: str
    chapter_id: int
    status: str
    items: List[ScenePairSeamQueueItem]
    node: Optional[TimelineNodeRef] = None
    recommended_pair: Optional[Dict[str, Any]] = None
    ready_count: int = 0
    blocked_count: int = 0
    aligned_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "chapter_seam_queue_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "chapter_id": self.chapter_id,
            "node": self.node.to_dict() if self.node else None,
            "status": self.status,
            "ready_count": int(self.ready_count),
            "blocked_count": int(self.blocked_count),
            "aligned_count": int(self.aligned_count),
            "recommended_pair": dict(self.recommended_pair) if self.recommended_pair else None,
            "items": [item.to_dict() for item in self.items],
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class ScenePairSeamDetail:
    book_id: str
    branch_id: str
    chapter_id: int
    scene_a_id: int
    scene_b_id: int
    status: str
    pair: Optional[ScenePairSeamQueueItem] = None
    node: Optional[TimelineNodeRef] = None
    report_found: bool = False
    report_path: Optional[str] = None
    report_status: Optional[str] = None
    issue_counts_before: Dict[str, Any] = field(default_factory=dict)
    issue_counts_after: Dict[str, Any] = field(default_factory=dict)
    repair_action_count: Optional[int] = None
    scene_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    report: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    blocked_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "scene_pair_seam_detail_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "chapter_id": self.chapter_id,
            "scene_a_id": self.scene_a_id,
            "scene_b_id": self.scene_b_id,
            "node": self.node.to_dict() if self.node else None,
            "status": self.status,
            "pair": self.pair.to_dict() if self.pair else None,
            "report_found": bool(self.report_found),
            "report_path": self.report_path,
            "report_status": self.report_status,
            "issue_counts_before": dict(self.issue_counts_before),
            "issue_counts_after": dict(self.issue_counts_after),
            "repair_action_count": self.repair_action_count,
            "scene_artifacts": [dict(item) for item in self.scene_artifacts],
            "report": dict(self.report) if isinstance(self.report, dict) else None,
            "action": self.action,
            "blocked_reason": self.blocked_reason,
            "details": dict(self.details),
        }


def _chapter_dir(book_root: Path, chapter_id: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{int(chapter_id):03d}"


def _scene_path(book_root: Path, chapter_id: int, scene_id: int) -> Path:
    return _chapter_dir(book_root, chapter_id) / f"scene_{int(scene_id):03d}.md"


def _scene_id(scene: Dict[str, Any], fallback: int) -> Optional[int]:
    for key in ("scene_id", "beat_id", "id"):
        resolved = _common.coerce_int(scene.get(key))
        if resolved is not None:
            return resolved
    return fallback if fallback >= 1 else None


def _chapter_outline(outline: Dict[str, Any], chapter_id: int) -> Optional[Dict[str, Any]]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for chapter in chapters:
        if isinstance(chapter, dict) and _common.coerce_int(chapter.get("chapter_id")) == int(chapter_id):
            return chapter
    return None


def _chapter_scene_rows(outline: Dict[str, Any], chapter_id: int) -> List[Dict[str, Any]]:
    chapter = _chapter_outline(outline, chapter_id)
    if not isinstance(chapter, dict):
        return []
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    if not sections:
        sectionless_scenes = chapter.get("scenes") if isinstance(chapter.get("scenes"), list) else []
        sections = [{"section_id": None, "title": None, "scenes": sectionless_scenes}]
    rows: List[Dict[str, Any]] = []
    for section_index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            continue
        section_id = _common.coerce_int(section.get("section_id"))
        scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        for scene_index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                continue
            scene_id = _scene_id(scene, scene_index)
            if scene_id is None:
                continue
            rows.append(
                {
                    "chapter_id": int(chapter_id),
                    "section_id": int(section_id) if section_id is not None else None,
                    "scene_id": int(scene_id),
                    "summary": str(scene.get("summary") or scene.get("title") or "").strip() or None,
                    "section_index": section_index,
                    "scene_index": scene_index,
                }
            )
    rows.sort(key=lambda item: int(item["scene_id"]))
    return rows


def _report_status(report_path: Path) -> Optional[str]:
    payload = _common.read_json(report_path)
    if not isinstance(payload, dict):
        return None
    status = str(payload.get("status") or "").strip()
    return status or None


def _issue_counts(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    section = payload.get(key) if isinstance(payload.get(key), dict) else {}
    counts = section.get("issue_counts") if isinstance(section.get("issue_counts"), dict) else {}
    return dict(counts)


def _scene_artifacts(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    artifacts = payload.get("scene_artifacts") if isinstance(payload.get("scene_artifacts"), list) else []
    return [dict(item) for item in artifacts if isinstance(item, dict)]


def _item_status(
    *,
    branch_id: str,
    scene_a_exists: bool,
    scene_b_exists: bool,
    report_status: Optional[str],
) -> Tuple[str, Optional[str], Optional[str]]:
    if report_status == "aligned":
        return "aligned", None, None
    if branch_id == MAIN_BRANCH_ID:
        return "blocked", None, "Scene-pair seam alignment is branch-only; create or select a derived branch first."
    if not scene_a_exists or not scene_b_exists:
        missing = []
        if not scene_a_exists:
            missing.append("scene A prose")
        if not scene_b_exists:
            missing.append("scene B prose")
        return "blocked", None, f"Missing {', '.join(missing)}."
    return "ready", "align_scene_pair_seam", None


def get_chapter_seam_queue(
    workspace,
    book_id: str,
    *,
    chapter_id: int,
    branch_id: str = MAIN_BRANCH_ID,
    prefer_emitted: bool = True,
) -> ChapterSeamQueue:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    root = _common.book_root(Path(workspace), book_id)
    execution_root = _common.execution_book_root(root, resolved_branch_id)
    outline = _common.load_outline(execution_root)
    node = current_execution_node(
        Path(workspace),
        book_id,
        branch_id=resolved_branch_id,
        prefer_emitted=prefer_emitted,
    )
    chapter = _chapter_outline(outline, int(chapter_id))
    if not isinstance(chapter, dict):
        return ChapterSeamQueue(
            book_id=book_id,
            branch_id=resolved_branch_id,
            chapter_id=int(chapter_id),
            node=node,
            status="blocked",
            items=[],
            details={"blocked_reason": f"Chapter {int(chapter_id)} does not exist in the selected outline."},
        )

    rows = _chapter_scene_rows(outline, int(chapter_id))
    items: List[ScenePairSeamQueueItem] = []
    for index in range(1, len(rows)):
        left = rows[index - 1]
        right = rows[index]
        scene_a_id = int(left["scene_id"])
        scene_b_id = int(right["scene_id"])
        scene_a_path = _scene_path(execution_root, int(chapter_id), scene_a_id)
        scene_b_path = _scene_path(execution_root, int(chapter_id), scene_b_id)
        report_path = scene_pair_seam_report_path(execution_root, int(chapter_id), scene_a_id, scene_b_id)
        report_status = _report_status(report_path)
        scene_a_exists = scene_a_path.exists()
        scene_b_exists = scene_b_path.exists()
        status, action, blocked_reason = _item_status(
            branch_id=resolved_branch_id,
            scene_a_exists=scene_a_exists,
            scene_b_exists=scene_b_exists,
            report_status=report_status,
        )
        items.append(
            ScenePairSeamQueueItem(
                chapter_id=int(chapter_id),
                section_a_id=left.get("section_id"),
                section_b_id=right.get("section_id"),
                scene_a_id=scene_a_id,
                scene_b_id=scene_b_id,
                scene_a_path=_relative_to(execution_root, scene_a_path),
                scene_b_path=_relative_to(execution_root, scene_b_path),
                scene_a_exists=scene_a_exists,
                scene_b_exists=scene_b_exists,
                report_path=_relative_to(execution_root, report_path) if report_path.exists() else None,
                report_status=report_status,
                status=status,
                action=action,
                blocked_reason=blocked_reason,
                details={
                    "canonical_changed": False,
                    "scene_a_summary": left.get("summary"),
                    "scene_b_summary": right.get("summary"),
                    "cross_section": left.get("section_id") != right.get("section_id"),
                },
            )
        )

    ready_count = sum(1 for item in items if item.status == "ready")
    aligned_count = sum(1 for item in items if item.status == "aligned")
    blocked_count = sum(1 for item in items if item.status == "blocked")
    recommended = next((item for item in items if item.status == "ready"), None)
    if not items:
        status = "empty"
    elif ready_count:
        status = "ready"
    elif blocked_count:
        status = "blocked"
    else:
        status = "aligned"
    return ChapterSeamQueue(
        book_id=book_id,
        branch_id=resolved_branch_id,
        chapter_id=int(chapter_id),
        node=node,
        status=status,
        ready_count=ready_count,
        blocked_count=blocked_count,
        aligned_count=aligned_count,
        recommended_pair=recommended.to_dict() if recommended else None,
        items=items,
        details={
            "pair_count": len(items),
            "branch_only_action": "align_scene_pair_seam",
            "queue_policy": "Adjacent outline scene pairs are queued in chapter order.",
        },
    )


def get_scene_pair_seam_detail(
    workspace,
    book_id: str,
    *,
    chapter_id: int,
    scene_a_id: int,
    scene_b_id: int,
    branch_id: str = MAIN_BRANCH_ID,
    include_report: bool = True,
    prefer_emitted: bool = True,
) -> ScenePairSeamDetail:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    root = _common.book_root(Path(workspace), book_id)
    execution_root = _common.execution_book_root(root, resolved_branch_id)
    queue = get_chapter_seam_queue(
        Path(workspace),
        book_id,
        branch_id=resolved_branch_id,
        chapter_id=int(chapter_id),
        prefer_emitted=prefer_emitted,
    )
    pair = next(
        (
            item
            for item in queue.items
            if int(item.scene_a_id) == int(scene_a_id) and int(item.scene_b_id) == int(scene_b_id)
        ),
        None,
    )
    if pair is None:
        return ScenePairSeamDetail(
            book_id=book_id,
            branch_id=resolved_branch_id,
            chapter_id=int(chapter_id),
            scene_a_id=int(scene_a_id),
            scene_b_id=int(scene_b_id),
            node=queue.node,
            status="blocked",
            blocked_reason=f"Scene pair ch{int(chapter_id):03d} sc{int(scene_a_id):03d}->sc{int(scene_b_id):03d} is not adjacent in the selected outline.",
            details={"chapter_queue_status": queue.status, "pair_count": len(queue.items)},
        )

    report_path = scene_pair_seam_report_path(execution_root, int(chapter_id), int(scene_a_id), int(scene_b_id))
    report_payload = _common.read_json(report_path)
    report = report_payload if isinstance(report_payload, dict) else None
    report_status = str(report.get("status") or "").strip() if report else None
    report_status = report_status or pair.report_status
    status = pair.status
    if report_status and report_status not in {"aligned", "pass"} and pair.status == "ready":
        status = "attention_required"
    return ScenePairSeamDetail(
        book_id=book_id,
        branch_id=resolved_branch_id,
        chapter_id=int(chapter_id),
        scene_a_id=int(scene_a_id),
        scene_b_id=int(scene_b_id),
        node=queue.node,
        status=status,
        pair=pair,
        report_found=report is not None,
        report_path=_relative_to(execution_root, report_path) if report_path.exists() else None,
        report_status=report_status,
        issue_counts_before=_issue_counts(report, "before") if report else {},
        issue_counts_after=_issue_counts(report, "after") if report else {},
        repair_action_count=report.get("repair_action_count") if report else None,
        scene_artifacts=_scene_artifacts(report) if report else [],
        report=dict(report) if report and include_report else None,
        action=pair.action,
        blocked_reason=pair.blocked_reason,
        details={
            "canonical_changed": False,
            "chapter_queue_status": queue.status,
            "include_report": bool(include_report),
        },
    )
