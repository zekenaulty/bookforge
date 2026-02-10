from __future__ import annotations

from pathlib import Path

from bookforge.config.env import read_env_value
from bookforge.prompt.system import load_system_prompt
from bookforge.util.paths import repo_root


def _bool_env(name: str, default: bool) -> bool:
    raw = read_env_value(name)
    if raw is None:
        return default
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _phase_include_outline(phase: str, default: bool) -> bool:
    name = f"BOOKFORGE_{str(phase).strip().upper()}_INCLUDE_OUTLINE"
    return _bool_env(name, default)


def _system_prompt_for_phase(system_path: Path, outline_path: Path, phase: str) -> str:
    defaults = {
        "preflight": True,
        "write": True,
        "state_repair": True,
        "repair": True,
        "continuity_pack": False,
        "lint": False,
    }
    include = _phase_include_outline(phase, defaults.get(phase, False))
    return load_system_prompt(system_path, outline_path, include_outline=include)


def _resolve_template(book_root: Path, name: str) -> Path:
    book_template = book_root / "prompts" / "templates" / name
    if book_template.exists():
        return book_template
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / name
