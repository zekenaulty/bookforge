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
  "display_name": "Run Pipeline Orchestrator",
  "llm_description": "Route scene writing, lint, repair, state repair, and commit work through the run graph.",
  "kind": "orchestrator",
  "category": "orchestrators",
  "folder": "orchestrators/run-pipeline",
  "graph_node": "run_pipeline",
  "phase_id": "run_pipeline",
  "logical_phase": "run_pipeline",
  "prompt_contract": "Map a drafting request to legal scene-phase actions and readiness prerequisites.",
  "output_hint": "a scene-phase routing plan with legal next actions",
  "required_params": [
    "workspace",
    "book_id",
    "request"
  ],
  "optional_params": [
    "chapter",
    "section",
    "scene",
    "branch_id",
    "notes"
  ],
  "source_refs": [
    "src/bookforge/runner.py",
    "src/bookforge/execution/scene_actions.py"
  ],
  "help_refs": [
    "docs/help/run.md"
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
    "workspace": "workspace",
    "book_id": "demo_book",
    "chapter": 1,
    "scene": 1,
    "request": "Choose the next scene action."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
