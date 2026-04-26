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
  "skill_id": "bookforge.run.continuity-pack",
  "display_name": "Run Continuity Pack",
  "llm_description": "Build or verify the continuity pack used for scene writing.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/continuity-pack",
  "graph_node": "run.continuity_pack",
  "phase_id": "continuity_pack",
  "logical_phase": "continuity_pack",
  "prompt_contract": "Return compact continuity context grounded in existing state and scene target.",
  "output_hint": "valid continuity pack JSON",
  "required_params": [
    "workspace",
    "book_id",
    "chapter",
    "scene",
    "request"
  ],
  "optional_params": [
    "scene_card",
    "branch_id",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/continuity_pack.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "example_params": {
    "workspace": "workspace",
    "book_id": "demo_book",
    "chapter": 1,
    "scene": 1,
    "request": "Build continuity pack."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
