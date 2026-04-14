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
  "skill_id": "bookforge.run.scene-commit",
  "folder": "run/scene-commit",
  "display_name": "Run Phase - Scene Commit",
  "llm_description": "Commits validated prose, state, and metadata artifacts to the BookForge workspace.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.commit",
  "phase_id": "commit",
  "logical_phase": "commit",
  "prompt_contract": "Package the final commit step, including artifact writes and durable state advancement, without skipping validations.",
  "output_hint": "a deterministic commit checklist or commit-ready response",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "lint_report"
  ],
  "source_refs": [
    "src/bookforge/runner.py",
    "src/bookforge/pipeline/state_apply.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Commit the validated scene outputs.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "scene_card": {},
      "patch": {},
      "lint_report": {
        "status": "pass"
      }
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
