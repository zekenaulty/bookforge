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
  "folder": "outline/transition-seam-analysis",
  "display_name": "Outline Phase 04A - Transition Seam Analysis",
  "llm_description": "Finds transition seam candidates and proposes required transition resolutions.",
  "kind": "phase",
  "category": "outline",
  "graph_node": "outline.phase_04a_transition_seam_analysis",
  "phase_id": "phase_04a_transition_seam_analysis",
  "logical_phase": "phase_04_transition_causality_refinement",
  "prompt_contract": "Analyze the scene draft for seam failures and emit candidate transition fixes with routing-ready metadata.",
  "output_hint": "JSON matching the transition_refine_v1 seam-analysis contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "transition_hints",
    "policy_context"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md",
    "src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py",
    "docs/help/outline_generate.md"
  ],
  "help_refs": [
    "docs/help/outline_generate.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Identify transition seam problems for chapter one.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "chapter_id": 1,
      "outline": {}
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
