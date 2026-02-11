from __future__ import annotations

from bookforge.config.env import read_env_value, read_int_env

DEFAULT_WRITE_MAX_TOKENS = 147456
DEFAULT_LINT_MAX_TOKENS = 294912
DEFAULT_REPAIR_MAX_TOKENS = 294912
DEFAULT_STATE_REPAIR_MAX_TOKENS = 294912
DEFAULT_CONTINUITY_MAX_TOKENS = 294912
DEFAULT_PREFLIGHT_MAX_TOKENS = 294912
DEFAULT_STYLE_ANCHOR_MAX_TOKENS = 65536
DEFAULT_APPEARANCE_MAX_TOKENS = 16384
DEFAULT_DURABLE_SLICE_MAX_EXPANSIONS = 2


def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _write_max_tokens() -> int:
    return _int_env("BOOKFORGE_WRITE_MAX_TOKENS", DEFAULT_WRITE_MAX_TOKENS)


def _lint_max_tokens() -> int:
    return _int_env("BOOKFORGE_LINT_MAX_TOKENS", DEFAULT_LINT_MAX_TOKENS)


def _repair_max_tokens() -> int:
    return _int_env("BOOKFORGE_REPAIR_MAX_TOKENS", DEFAULT_REPAIR_MAX_TOKENS)


def _state_repair_max_tokens() -> int:
    return _int_env("BOOKFORGE_STATE_REPAIR_MAX_TOKENS", DEFAULT_STATE_REPAIR_MAX_TOKENS)


def _continuity_max_tokens() -> int:
    return _int_env("BOOKFORGE_CONTINUITY_MAX_TOKENS", DEFAULT_CONTINUITY_MAX_TOKENS)


def _preflight_max_tokens() -> int:
    return _int_env("BOOKFORGE_PREFLIGHT_MAX_TOKENS", DEFAULT_PREFLIGHT_MAX_TOKENS)


def _style_anchor_max_tokens() -> int:
    return _int_env("BOOKFORGE_STYLE_ANCHOR_MAX_TOKENS", DEFAULT_STYLE_ANCHOR_MAX_TOKENS)


def _appearance_max_tokens() -> int:
    return max(512, _int_env("BOOKFORGE_APPEARANCE_MAX_TOKENS", DEFAULT_APPEARANCE_MAX_TOKENS))

def _durable_slice_max_expansions() -> int:
    return max(0, _int_env("BOOKFORGE_DURABLE_SLICE_MAX_EXPANSIONS", DEFAULT_DURABLE_SLICE_MAX_EXPANSIONS))


def _lint_mode() -> str:
    raw = read_env_value("BOOKFORGE_LINT_MODE")
    if raw is None:
        raw = "warn"
    raw = str(raw).strip().lower()
    if raw in {"strict", "warn", "off"}:
        return raw
    return "warn"





