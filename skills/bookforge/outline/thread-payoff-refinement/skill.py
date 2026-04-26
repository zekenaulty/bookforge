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
  "skill_id": "bookforge.outline.thread-payoff-refinement",
  "display_name": "Outline Thread Payoff Refinement",
  "llm_description": "Refine thread setup and payoff clarity for one chapter.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/thread-payoff-refinement",
  "graph_node": "outline.phase_06_thread_payoff_refinement",
  "phase_id": "phase_06_thread_payoff_refinement",
  "logical_phase": "phase_06_thread_payoff_refinement",
  "prompt_contract": "Return one chapter payload with thread payoff refinements that preserve scene chronology.",
  "output_hint": "valid phase_06 thread payoff JSON",
  "required_params": [
    "chapter_target_id",
    "chapter_input_outline",
    "request"
  ],
  "optional_params": [
    "thread_registry",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_06_thread_payoff_refinement.md"
  ],
  "help_refs": [
    "skills/bookforge/outline/thread-payoff-refinement/HELP.md"
  ],
  "example_params": {
    "chapter_target_id": 1,
    "chapter_input_outline": {
      "chapters": []
    },
    "request": "Refine thread payoffs."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
