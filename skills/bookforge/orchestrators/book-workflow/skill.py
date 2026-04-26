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
  "skill_id": "bookforge.orchestrators.book-workflow",
  "display_name": "Book Workflow Orchestrator",
  "llm_description": "Route setup, end-to-end book workflow, and export-like BookForge requests to narrower outline or run skills.",
  "kind": "orchestrator",
  "category": "orchestrators",
  "folder": "orchestrators/book-workflow",
  "graph_node": "book_workflow",
  "phase_id": "book_workflow",
  "logical_phase": "book_workflow",
  "prompt_contract": "Identify the requested book workflow path, required prerequisites, and the next narrow BookForge skill or command to run.",
  "output_hint": "a concise routing plan with required inputs and refusal reasons if prerequisites are missing",
  "required_params": [
    "workspace",
    "book_id",
    "request"
  ],
  "optional_params": [
    "chapter",
    "section",
    "scene",
    "notes"
  ],
  "source_refs": [
    "docs/help/workflow.md",
    "src/bookforge/cli.py"
  ],
  "help_refs": [
    "skills/bookforge/orchestrators/book-workflow/HELP.md"
  ],
  "routes": [
    "bookforge.orchestrators.outline-pipeline",
    "bookforge.orchestrators.run-pipeline"
  ],
  "example_params": {
    "workspace": "workspace",
    "book_id": "demo_book",
    "request": "Plan the next safe workflow step."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
