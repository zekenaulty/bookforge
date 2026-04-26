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
  "display_name": "Run Scene Commit",
  "llm_description": "Commit a validated scene artifact into the draft state.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/scene-commit",
  "graph_node": "run.apply_commit",
  "phase_id": "apply_commit",
  "logical_phase": "scene_commit",
  "prompt_contract": "Summarize deterministic commit prerequisites and expected artifact promotions.",
  "output_hint": "a commit readiness summary with canonical artifact targets",
  "required_params": [
    "workspace",
    "book_id",
    "chapter",
    "scene",
    "request"
  ],
  "optional_params": [
    "branch_id",
    "artifact_paths",
    "notes"
  ],
  "source_refs": [
    "src/bookforge/execution/scene_actions.py",
    "src/bookforge/runner.py"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "example_params": {
    "workspace": "workspace",
    "book_id": "demo_book",
    "chapter": 1,
    "scene": 1,
    "request": "Check commit readiness."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
