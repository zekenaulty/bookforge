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
  "skill_id": "bookforge.run.scene-repair",
  "display_name": "Run Scene Repair",
  "llm_description": "Repair prose for a single scene based on lint findings and bounded constraints.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/scene-repair",
  "graph_node": "run.repair_scene",
  "phase_id": "repair_scene",
  "logical_phase": "scene_repair",
  "prompt_contract": "Return repaired prose while preserving scene facts and requested repair scope.",
  "output_hint": "repaired scene prose text or structured refusal",
  "required_params": [
    "workspace",
    "book_id",
    "chapter",
    "scene",
    "lint_report",
    "request"
  ],
  "optional_params": [
    "scene_prose",
    "branch_id",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/repair.md",
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
    "lint_report": {},
    "request": "Repair scene prose."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
