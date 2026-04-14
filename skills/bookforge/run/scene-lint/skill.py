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
  "folder": "run/scene-lint",
  "display_name": "Run Phase - Scene Lint",
  "llm_description": "Evaluates the scene and patch for continuity, invariant, and anti-duplication failures.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.lint",
  "phase_id": "lint",
  "logical_phase": "lint",
  "prompt_contract": "Produce a lint report that surfaces failure reasons instead of silently forgiving them.",
  "output_hint": "JSON matching the lint report contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "pre_state",
    "post_state"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/lint/lint_policy_rules_and_inputs.md",
    "src/bookforge/phases/lint_phase.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Lint the current scene output.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "scene_card": {},
      "prose": "Sample prose",
      "patch": {}
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
