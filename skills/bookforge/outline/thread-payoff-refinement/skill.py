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
  "folder": "outline/thread-payoff-refinement",
  "display_name": "Outline Phase 06 - Thread Payoff Refinement",
  "llm_description": "Tightens thread progression and payoff distribution across the final outline.",
  "kind": "phase",
  "category": "outline",
  "graph_node": "outline.phase_06_thread_payoff_refinement",
  "phase_id": "phase_06_thread_payoff_refinement",
  "logical_phase": "phase_06_thread_payoff_refinement",
  "prompt_contract": "Refine thread/payoff structure while preserving validated cast and transition work.",
  "output_hint": "JSON matching the final outline output contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "working_outline"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md",
    "src/bookforge/phases/outline/phase_06_thread_payoff_refinement.py",
    "docs/help/outline_generate.md"
  ],
  "help_refs": [
    "docs/help/outline_generate.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Refine thread payoff continuity in the final outline.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "outline": {}
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
