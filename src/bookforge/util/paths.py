from __future__ import annotations

from pathlib import Path
from typing import Optional


def repo_root(start: Optional[Path] = None) -> Path:
    current = start or Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists():
            return parent
    for parent in [current] + list(current.parents):
        if parent.name == 'src':
            return parent.parent
    return current.parent
