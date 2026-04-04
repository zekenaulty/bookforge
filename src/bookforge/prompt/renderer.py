from __future__ import annotations

from pathlib import Path
from typing import Dict
import json
import os

from bookforge.util.paths import repo_root

from .serialization import dumps_json


def load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render_template(template_text: str, values: Dict[str, object]) -> str:
    perspective_block = _load_perspective_block()
    if perspective_block and "perspective_block" not in values:
        values = dict(values)
        values["perspective_block"] = perspective_block
    rendered = template_text
    for key in sorted(values.keys()):
        token = "{{" + key + "}}"
        value = values[key]
        if not isinstance(value, str):
            value = dumps_json(value)
        rendered = rendered.replace(token, value)
    if perspective_block and "{{perspective_block}}" not in template_text:
        mode = str(os.environ.get("BOOKFORGE_PERSPECTIVE_MODE") or "prefix").strip().lower()
        if mode == "prefix":
            rendered = f"Perspective Replay (optional):\n{perspective_block}\n\n{rendered}"
    return rendered


def _load_perspective_block() -> str:
    raw_text = os.environ.get("BOOKFORGE_PERSPECTIVE_TEXT")
    if raw_text:
        return str(raw_text).strip()
    path_raw = os.environ.get("BOOKFORGE_PERSPECTIVE_PATH")
    if not path_raw:
        return ""
    path = Path(path_raw)
    if not path.is_absolute():
        path = repo_root(Path(__file__).resolve()) / path
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    stripped = content.strip()
    if not stripped:
        return ""
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped
    if isinstance(payload, dict):
        for key in ("perspective", "summary", "response_text", "content", "text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(payload, ensure_ascii=True, indent=2)
    if isinstance(payload, list):
        return json.dumps(payload, ensure_ascii=True, indent=2)
    return stripped


def render_template_file(path: Path, values: Dict[str, object]) -> str:
    return render_template(load_template(path), values)
