from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .vocabulary import is_valid_workflow_family


def _clean_required(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be omitted or a non-empty string.")
    return cleaned


def _positive_optional_int(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    try:
        resolved = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer when provided.") from exc
    if resolved < 1:
        raise ValueError(f"{field_name} must be >= 1 when provided.")
    return resolved


@dataclass(frozen=True, slots=True)
class ScopeSelector:
    book_id: str
    branch_id: Optional[str] = None
    fork_group_id: Optional[str] = None
    workflow_family: Optional[str] = None
    chapter: Optional[int] = None
    section: Optional[int] = None
    scene: Optional[int] = None
    phase_id: Optional[str] = None
    turn_id: Optional[str] = None

    def __post_init__(self) -> None:
        book_id = _clean_required(self.book_id, "book_id")
        branch_id = _clean_optional(self.branch_id, "branch_id")
        fork_group_id = _clean_optional(self.fork_group_id, "fork_group_id")
        workflow_family = _clean_optional(self.workflow_family, "workflow_family")
        phase_id = _clean_optional(self.phase_id, "phase_id")
        turn_id = _clean_optional(self.turn_id, "turn_id")
        chapter = _positive_optional_int(self.chapter, "chapter")
        section = _positive_optional_int(self.section, "section")
        scene = _positive_optional_int(self.scene, "scene")

        if workflow_family is not None and not is_valid_workflow_family(workflow_family):
            raise ValueError(f"Unknown workflow_family: {workflow_family}")
        if section is not None and chapter is None:
            raise ValueError("section requires chapter.")
        if scene is not None and chapter is None:
            raise ValueError("scene requires chapter.")

        object.__setattr__(self, "book_id", book_id)
        object.__setattr__(self, "branch_id", branch_id)
        object.__setattr__(self, "fork_group_id", fork_group_id)
        object.__setattr__(self, "workflow_family", workflow_family)
        object.__setattr__(self, "chapter", chapter)
        object.__setattr__(self, "section", section)
        object.__setattr__(self, "scene", scene)
        object.__setattr__(self, "phase_id", phase_id)
        object.__setattr__(self, "turn_id", turn_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "fork_group_id": self.fork_group_id,
            "workflow_family": self.workflow_family,
            "chapter": self.chapter,
            "section": self.section,
            "scene": self.scene,
            "phase_id": self.phase_id,
            "turn_id": self.turn_id,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ScopeSelector":
        if not isinstance(payload, dict):
            raise ValueError("ScopeSelector payload must be a dictionary.")
        return cls(
            book_id=payload.get("book_id"),
            branch_id=payload.get("branch_id"),
            fork_group_id=payload.get("fork_group_id"),
            workflow_family=payload.get("workflow_family"),
            chapter=payload.get("chapter"),
            section=payload.get("section"),
            scene=payload.get("scene"),
            phase_id=payload.get("phase_id"),
            turn_id=payload.get("turn_id"),
        )

    def is_book_root(self) -> bool:
        return (
            self.branch_id is None
            and self.fork_group_id is None
            and self.workflow_family is None
            and self.chapter is None
            and self.section is None
            and self.scene is None
            and self.phase_id is None
            and self.turn_id is None
        )
