from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ExcerptPolicy:
    include_style_anchor: bool
    include_continuity_pack: bool
    max_banned_phrases: int


def build_excerpt_policy(policies: Dict[str, Any] | None = None) -> ExcerptPolicy:
    policies = policies or {}
    style_anchor = policies.get("style_anchor", {})
    continuity = policies.get("continuity_pack", {})
    banned = policies.get("banned_phrases", {})

    include_style_anchor = bool(style_anchor.get("enabled", True))
    include_continuity_pack = bool(continuity.get("enabled", True))
    max_banned = banned.get("max_items", 60)
    if not isinstance(max_banned, int) or max_banned < 0:
        max_banned = 60

    return ExcerptPolicy(
        include_style_anchor=include_style_anchor,
        include_continuity_pack=include_continuity_pack,
        max_banned_phrases=max_banned,
    )
