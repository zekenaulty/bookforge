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
  "skill_id": "bookforge.outline.scene-draft",
  "display_name": "Outline Scene Draft",
  "llm_description": "Draft scene cards for one chapter inside the chapter-scoped outline flow.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/scene-draft",
  "graph_node": "outline.phase_03_scene_draft",
  "phase_id": "phase_03_scene_draft",
  "logical_phase": "phase_03_scene_draft",
  "prompt_contract": "Return exactly one chapter payload with scene cards that satisfy the outline schema.",
  "output_hint": "valid phase_03 chapter-scoped scene draft JSON",
  "required_params": [
    "chapter_target_id",
    "chapter_input_outline",
    "request"
  ],
  "optional_params": [
    "chapter_prev_outline",
    "chapter_next_outline",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_03_scene_draft.md",
    "src/bookforge/outline.py"
  ],
  "help_refs": [
    "skills/bookforge/outline/scene-draft/HELP.md"
  ],
  "example_params": {
    "chapter_target_id": 1,
    "chapter_input_outline": {
      "chapters": []
    },
    "request": "Draft scenes for chapter 1."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
