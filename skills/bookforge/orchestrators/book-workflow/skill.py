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
  "folder": "orchestrators/book-workflow",
  "display_name": "Book Workflow Orchestrator",
  "llm_description": "Routes setup, outline, run, recovery, and export requests across the BookForge skill tree.",
  "kind": "orchestrator",
  "category": "orchestrators",
  "graph_node": "book_workflow",
  "phase_id": "book_workflow",
  "logical_phase": "book_workflow",
  "prompt_contract": "Choose the correct BookForge workflow, preserve graph boundaries, and hand work to the best matching child skill.",
  "output_hint": "a routed action plan or a direct next-step response",
  "required_params": [
    "request"
  ],
  "optional_params": [
    "book_id",
    "workspace",
    "phase_selector",
    "input_payload"
  ],
  "source_refs": [
    "docs/help/index.md",
    "src/bookforge/cli.py",
    "README.md"
  ],
  "help_refs": [
    "docs/help/index.md"
  ],
  "routes": [
    "bookforge.orchestrators.outline-pipeline",
    "bookforge.orchestrators.run-pipeline"
  ],
  "example_params": {
    "request": "Create or resume the next useful BookForge action for criticulous_b1.",
    "book_id": "criticulous_b1",
    "workspace": "workspace"
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
