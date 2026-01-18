from __future__ import annotations

from pathlib import Path
from typing import Dict

from .serialization import dumps_json


def load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render_template(template_text: str, values: Dict[str, object]) -> str:
    rendered = template_text
    for key in sorted(values.keys()):
        token = "{{" + key + "}}"
        value = values[key]
        if not isinstance(value, str):
            value = dumps_json(value)
        rendered = rendered.replace(token, value)
    return rendered


def render_template_file(path: Path, values: Dict[str, object]) -> str:
    return render_template(load_template(path), values)
