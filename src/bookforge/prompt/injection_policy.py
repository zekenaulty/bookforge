from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class InjectionPolicy:
    max_canon_items: Optional[int]
    max_canon_chars: Optional[int]


def build_injection_policy(policies: Dict[str, Any] | None = None) -> InjectionPolicy:
    policies = policies or {}
    canon = policies.get("canon_injection", {})

    max_items = canon.get("max_items")
    max_chars = canon.get("max_chars")

    if not isinstance(max_items, int) or max_items <= 0:
        max_items = None
    if not isinstance(max_chars, int) or max_chars <= 0:
        max_chars = None

    return InjectionPolicy(max_canon_items=max_items, max_canon_chars=max_chars)
