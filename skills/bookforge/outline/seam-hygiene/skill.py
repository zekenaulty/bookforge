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
  "skill_id": "bookforge.outline.seam-hygiene",
  "display_name": "Outline Seam Hygiene",
  "llm_description": "Repair seam hygiene in constrained outline windows after relinking.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/seam-hygiene",
  "graph_node": "outline.phase_04d_seam_hygiene",
  "phase_id": "phase_04d_seam_hygiene",
  "logical_phase": "phase_04_transition_causality_refinement",
  "prompt_contract": "Return only allowed seam fields for the active hygiene window.",
  "output_hint": "valid phase_04d seam hygiene JSON",
  "required_params": [
    "chapter_target_id",
    "chapter_input_outline",
    "request"
  ],
  "optional_params": [
    "phase04d_current_window",
    "phase04d_allowed_fields"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_04d_seam_hygiene.md"
  ],
  "help_refs": [
    "skills/bookforge/outline/seam-hygiene/HELP.md"
  ],
  "example_params": {
    "chapter_target_id": 1,
    "chapter_input_outline": {
      "chapters": []
    },
    "request": "Repair seam hygiene."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
