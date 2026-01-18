from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import json


@dataclass(frozen=True)
class PromptRegistry:
    version: str
    templates: Dict[str, str]
    budgets: Dict[str, Any]
    policies: Dict[str, Any]


def load_registry(path: Path) -> PromptRegistry:
    if not path.exists():
        raise FileNotFoundError(f"Prompt registry not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    version = str(data.get("version") or data.get("prompt_version") or "").strip()
    if not version:
        raise ValueError("Prompt registry missing version")
    templates = data.get("templates") or {}
    if not isinstance(templates, dict) or not templates:
        raise ValueError("Prompt registry missing templates")
    budgets = data.get("budgets") or {}
    policies = data.get("policies") or {}
    if not isinstance(budgets, dict) or not isinstance(policies, dict):
        raise ValueError("Prompt registry budgets/policies must be objects")
    return PromptRegistry(
        version=version,
        templates=templates,
        budgets=budgets,
        policies=policies,
    )
