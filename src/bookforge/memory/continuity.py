from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import json
import shutil


@dataclass(frozen=True)
class ContinuityPack:
    scene_end_anchor: str
    constraints: List[str]
    open_threads: List[str]
    cast_present: List[str]
    location: str
    next_action: str
    summary: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContinuityPack":
        required = ["scene_end_anchor", "constraints", "open_threads", "cast_present", "location", "next_action"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Continuity pack missing fields: {', '.join(missing)}")
        summary = data.get("summary")
        if not isinstance(summary, dict):
            summary = {}
        return cls(
            scene_end_anchor=str(data.get("scene_end_anchor", "")),
            constraints=[str(item) for item in data.get("constraints", [])],
            open_threads=[str(item) for item in data.get("open_threads", [])],
            cast_present=[str(item) for item in data.get("cast_present", [])],
            location=str(data.get("location", "")),
            next_action=str(data.get("next_action", "")),
            summary=summary,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_end_anchor": self.scene_end_anchor,
            "constraints": list(self.constraints),
            "open_threads": list(self.open_threads),
            "cast_present": list(self.cast_present),
            "location": self.location,
            "next_action": self.next_action,
            "summary": self.summary,
        }


def parse_continuity_pack(text: str) -> ContinuityPack:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Continuity pack JSON must be an object")
    return ContinuityPack.from_dict(data)


def load_continuity_pack(path: Path) -> ContinuityPack:
    return parse_continuity_pack(path.read_text(encoding="utf-8"))


def save_continuity_pack(path: Path, pack: ContinuityPack) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        archive_dir = path.parent / "continuity_history"
        archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"continuity_pack_{timestamp}.json"
        shutil.copyfile(path, archive_path)
    path.write_text(json.dumps(pack.to_dict(), ensure_ascii=True, indent=2), encoding="utf-8")


def continuity_pack_path(book_root: Path) -> Path:
    return book_root / "draft" / "context" / "continuity_pack.json"


def style_anchor_path(book_root: Path) -> Path:
    return book_root / "prompts" / "style_anchor.md"


def load_style_anchor(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def save_style_anchor(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
