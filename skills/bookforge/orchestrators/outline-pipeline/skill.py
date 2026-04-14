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
  "skill_id": "bookforge.orchestrators.outline-pipeline",
  "folder": "orchestrators/outline-pipeline",
  "display_name": "Outline Pipeline Orchestrator",
  "llm_description": "Routes outline generation, rerun, resume, and phase-window requests across the outline graph.",
  "kind": "orchestrator",
  "category": "orchestrators",
  "graph_node": "outline_pipeline",
  "phase_id": "outline_pipeline",
  "logical_phase": "outline_pipeline",
  "prompt_contract": "Route outline tasks to the correct outline phase skill and preserve the existing phase order from BookForge.",
  "output_hint": "a routed outline action plan or a direct next-step response",
  "required_params": [
    "request",
    "book_id"
  ],
  "optional_params": [
    "from_phase",
    "to_phase",
    "transition_hints",
    "working_outline"
  ],
  "source_refs": [
    "docs/help/outline_generate.md",
    "src/bookforge/outline.py",
    "src/bookforge/phases/outline/context.py"
  ],
  "help_refs": [
    "docs/help/outline_generate.md",
    "docs/help/outline_backup.md",
    "docs/help/outline_restore.md"
  ],
  "routes": [
    "bookforge.outline.chapter-spine",
    "bookforge.outline.section-architecture",
    "bookforge.outline.scene-draft",
    "bookforge.outline.transition-seam-analysis",
    "bookforge.outline.transition-execution",
    "bookforge.outline.metadata-relink",
    "bookforge.outline.intro-sync",
    "bookforge.outline.handoff-normalize",
    "bookforge.outline.seam-hygiene",
    "bookforge.outline.cast-function-refinement",
    "bookforge.outline.thread-payoff-refinement"
  ],
  "example_params": {
    "request": "Resume outline work from transition execution through seam hygiene.",
    "book_id": "criticulous_b1",
    "from_phase": "phase_04b_transition_execution",
    "to_phase": "phase_04d_seam_hygiene"
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
