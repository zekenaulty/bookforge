from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from bookforge.memory.continuity import continuity_pack_path, style_anchor_path

from . import _common


@dataclass(frozen=True, slots=True)
class ContinuityView:
    continuity_pack: Optional[Dict[str, Any]]
    style_anchor_path: str
    style_anchor_present: bool
    pause_marker: Optional[Dict[str, Any]]


def get_continuity_view(workspace, book_id: str) -> ContinuityView:
    book_root = _common.book_root(workspace, book_id)
    continuity_path = continuity_pack_path(book_root)
    style_path = style_anchor_path(book_root)
    return ContinuityView(
        continuity_pack=_common.read_json(continuity_path),
        style_anchor_path=style_path.as_posix(),
        style_anchor_present=style_path.exists(),
        pause_marker=_common.state_pause_marker(book_root),
    )
