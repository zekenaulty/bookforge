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
  "skill_id": "bookforge.outline.transition-seam-analysis",
  "display_name": "Outline Transition Seam Analysis",
  "llm_description": "Analyze transition seams and select required repair or insertion candidates.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/transition-seam-analysis",
  "graph_node": "outline.phase_04a_transition_seam_analysis",
  "phase_id": "phase_04a_transition_seam_analysis",
  "logical_phase": "phase_04_transition_causality_refinement",
  "prompt_contract": "Return one chapter payload plus a phase_report with candidate_seams.",
  "output_hint": "valid phase_04a transition analysis JSON",
  "required_params": [
    "chapter_target_id",
    "chapter_input_outline",
    "request"
  ],
  "optional_params": [
    "chapter_prev_outline",
    "chapter_next_outline",
    "transition_hints"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md"
  ],
  "help_refs": [
    "skills/bookforge/outline/transition-seam-analysis/HELP.md"
  ],
  "example_params": {
    "chapter_target_id": 1,
    "chapter_input_outline": {
      "chapters": []
    },
    "request": "Analyze transition seams."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
