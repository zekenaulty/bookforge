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
  "skill_id": "bookforge.run.state-repair",
  "display_name": "Run State Repair",
  "llm_description": "Repair state deltas after a scene write or prose repair.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/state-repair",
  "graph_node": "run.state_repair",
  "phase_id": "state_repair",
  "logical_phase": "state_repair",
  "prompt_contract": "Return state updates consistent with prose and durable registry rules.",
  "output_hint": "valid state repair JSON",
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
    "resources/prompt_templates/state_repair.md",
    "src/bookforge/pipeline/state_apply.py"
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
    "request": "Repair state."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
