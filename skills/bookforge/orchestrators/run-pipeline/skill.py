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
  "skill_id": "bookforge.orchestrators.run-pipeline",
  "folder": "orchestrators/run-pipeline",
  "display_name": "Run Pipeline Orchestrator",
  "llm_description": "Routes scene-planning, drafting, repair, lint, and commit requests across the run graph.",
  "kind": "orchestrator",
  "category": "orchestrators",
  "graph_node": "run_pipeline",
  "phase_id": "run_pipeline",
  "logical_phase": "run_pipeline",
  "prompt_contract": "Route run-loop tasks to the right scene-phase skill without collapsing distinct validation and repair steps together.",
  "output_hint": "a routed run action plan or a direct next-step response",
  "required_params": [
    "request",
    "book_id"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "state_snapshot",
    "scene_card"
  ],
  "source_refs": [
    "docs/help/run.md",
    "src/bookforge/runner.py"
  ],
  "help_refs": [
    "docs/help/run.md",
    "docs/help/llm.md"
  ],
  "routes": [
    "bookforge.run.scene-planning",
    "bookforge.run.preflight-state",
    "bookforge.run.continuity-pack",
    "bookforge.run.scene-writing",
    "bookforge.run.scene-repair",
    "bookforge.run.state-repair",
    "bookforge.run.scene-lint",
    "bookforge.run.scene-commit"
  ],
  "example_params": {
    "request": "Prepare the next scene-writing loop and tell me the next concrete phase.",
    "book_id": "criticulous_b1",
    "chapter": 1,
    "scene": 1
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
