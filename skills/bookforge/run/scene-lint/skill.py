from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bookforge.skill_runtime import build_skill_definition, execute_skill, skill_main


SKILL = build_skill_definition({
  "skill_id": "bookforge.run.scene-lint",
  "display_name": "Run Scene Lint",
  "llm_description": "Lint one scene for prose, continuity, and state-contract issues.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/scene-lint",
  "graph_node": "run.lint_scene",
  "phase_id": "lint_scene",
  "logical_phase": "scene_lint",
  "prompt_contract": "Return lint findings and pass/fail status without mutating scene prose.",
  "output_hint": "valid lint report JSON",
  "required_params": [
    "workspace",
    "book_id",
    "chapter",
    "scene",
    "scene_prose",
    "request"
  ],
  "optional_params": [
    "scene_card",
    "branch_id",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/lint.md",
    "src/bookforge/lint.py"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "example_params": {
    "workspace": "workspace",
    "book_id": "demo_book",
    "chapter": 1,
    "scene": 1,
    "scene_prose": "",
    "request": "Lint scene prose."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
