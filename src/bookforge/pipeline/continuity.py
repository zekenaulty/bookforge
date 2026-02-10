from __future__ import annotations

from typing import Any, Dict


def _global_continuity_stats(state: Dict[str, Any]) -> Dict[str, Any]:
    stats = state.get("continuity_system", {}).get("global", {}) if isinstance(state, dict) else {}
    if not isinstance(stats, dict):
        return {}
    return stats
