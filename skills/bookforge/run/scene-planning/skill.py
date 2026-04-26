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
  "display_name": "Run Scene Planning",
  "llm_description": "Plan a single scene card for a scoped drafting target.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/scene-planning",
  "graph_node": "run.plan_scene",
  "phase_id": "plan_scene",
  "logical_phase": "scene_planning",
  "prompt_contract": "Return a scene card that satisfies the planning schema and current outline target.",
  "output_hint": "valid scene card JSON",
  "required_params": [
    "workspace",
    "book_id",
    "chapter",
    "scene",
    "request"
  ],
  "optional_params": [
    "section",
    "branch_id",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/plan.md",
    "src/bookforge/execution/scene_actions.py"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "example_params": {
    "workspace": "workspace",
    "book_id": "demo_book",
    "chapter": 1,
    "scene": 1,
    "request": "Plan scene 1."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
