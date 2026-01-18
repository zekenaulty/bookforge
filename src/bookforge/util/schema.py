from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("jsonschema is required; install with pip install jsonschema") from exc

SCHEMA_VERSION = "1.0"

_SCHEMA_MAP = {
    "book": "book.schema.json",
    "state": "state.schema.json",
    "outline": "outline.schema.json",
    "scene_card": "scene_card.schema.json",
    "state_patch": "state_patch.schema.json",
    "lint_report": "lint_report.schema.json",
}

@dataclass
class SchemaValidationError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message

def _root_dir() -> Path:
    return Path(__file__).resolve().parents[3]

def load_schema(schema_name: str) -> dict:
    if schema_name not in _SCHEMA_MAP:
        raise SchemaValidationError(f"Unknown schema: {schema_name}")
    path = _root_dir() / "schemas" / _SCHEMA_MAP[schema_name]
    if not path.exists():
        raise SchemaValidationError(f"Schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def validate_json(data: Any, schema_name: str) -> None:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join([str(p) for p in first.path])
        message = f"{schema_name} validation failed at {path or '<root>'}: {first.message}"
        raise SchemaValidationError(message)
