from __future__ import annotations

from typing import Optional

from bookforge.config.env import read_env_value


_VALID_LEVELS = {"minimal", "low", "medium", "high"}


def _normalize_level(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip().lower()
    if raw in _VALID_LEVELS:
        return raw
    return None


def resolve_turn_thinking_level(
    phase_id: str,
    turn_id: str,
    *,
    default_t1: str = "high",
    default_t2: str = "low",
) -> str:
    phase_key = str(phase_id).strip().upper()
    turn_key = str(turn_id).strip().upper()
    default = default_t1 if turn_key == "T1" else default_t2

    for key in (
        f"BOOKFORGE_{phase_key}_{turn_key}_THINKING_LEVEL",
        f"BOOKFORGE_{phase_key}_THINKING_LEVEL",
        f"BOOKFORGE_{turn_key}_THINKING_LEVEL",
    ):
        resolved = _normalize_level(read_env_value(key))
        if resolved:
            return resolved

    return default
