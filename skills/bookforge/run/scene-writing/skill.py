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
  "skill_id": "bookforge.run.scene-writing",
  "display_name": "Run Scene Writing",
  "llm_description": "Write prose for a single scene without automatically linting or repairing it.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/scene-writing",
  "graph_node": "run.write_scene",
  "phase_id": "write_scene",
  "logical_phase": "scene_writing",
  "prompt_contract": "Return scene prose that follows the scene card, continuity pack, and author voice.",
  "output_hint": "scene prose text or a structured refusal with missing prerequisites",
  "required_params": [
    "workspace",
    "book_id",
    "chapter",
    "scene",
    "scene_card",
    "request"
  ],
  "optional_params": [
    "continuity_pack",
    "branch_id",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/write.md",
    "src/bookforge/execution/scene_actions.py"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "example_params": {
    "workspace": "workspace",
    "book_id": "demo_book",
    "chapter": 1,
    "scene": 1,
    "scene_card": {},
    "request": "Write scene prose."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
