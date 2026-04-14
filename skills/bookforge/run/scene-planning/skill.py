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
  "skill_id": "bookforge.run.scene-planning",
  "folder": "run/scene-planning",
  "display_name": "Run Phase - Scene Planning",
  "llm_description": "Plans the next scene card from outline, state, and recent lint context.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.plan",
  "phase_id": "plan",
  "logical_phase": "plan",
  "prompt_contract": "Generate the scene card and preserve the BookForge scene-card contract.",
  "output_hint": "JSON matching the scene-card contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "state_snapshot"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md",
    "src/bookforge/phases/plan.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Plan the next scene card.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "chapter": 1,
      "scene": 1
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
