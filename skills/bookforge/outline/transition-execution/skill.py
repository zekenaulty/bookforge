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
  "skill_id": "bookforge.outline.transition-execution",
  "display_name": "Outline Transition Execution",
  "llm_description": "Execute selected transition repairs and insertion decisions within one chapter.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/transition-execution",
  "graph_node": "outline.phase_04b_transition_execution",
  "phase_id": "phase_04b_transition_execution",
  "logical_phase": "phase_04_transition_causality_refinement",
  "prompt_contract": "Return one chapter payload and a phase_report resolving selected transition candidates without downgrading required insertions.",
  "output_hint": "valid phase_04b transition execution JSON",
  "required_params": [
    "chapter_target_id",
    "chapter_input_outline",
    "phase_04_selected_candidates_json",
    "request"
  ],
  "optional_params": [
    "phase_04_selected_insertions_json",
    "phase_04_blocked_candidates_json"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_04b_transition_execution.md"
  ],
  "help_refs": [
    "skills/bookforge/outline/transition-execution/HELP.md"
  ],
  "example_params": {
    "chapter_target_id": 1,
    "chapter_input_outline": {
      "chapters": []
    },
    "phase_04_selected_candidates_json": [],
    "request": "Resolve selected transitions."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
