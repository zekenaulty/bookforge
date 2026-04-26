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
  "display_name": "Outline Pipeline Orchestrator",
  "llm_description": "Route outline generation, rerun, resume, backup, and restore work through the outline graph.",
  "kind": "orchestrator",
  "category": "orchestrators",
  "folder": "orchestrators/outline-pipeline",
  "graph_node": "outline_pipeline",
  "phase_id": "outline_pipeline",
  "logical_phase": "outline_pipeline",
  "prompt_contract": "Map an outline request to the legal outline phase range, prerequisites, and source artifacts.",
  "output_hint": "a phase-scoped outline execution plan",
  "required_params": [
    "workspace",
    "book_id",
    "request"
  ],
  "optional_params": [
    "from_phase",
    "to_phase",
    "chapter",
    "section",
    "notes"
  ],
  "source_refs": [
    "src/bookforge/outline.py",
    "src/bookforge/phases/outline/context.py"
  ],
  "help_refs": [
    "docs/help/workflow.md"
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
    "workspace": "workspace",
    "book_id": "demo_book",
    "request": "Resume the outline pipeline."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
