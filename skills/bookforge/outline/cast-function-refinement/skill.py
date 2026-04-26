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
  "skill_id": "bookforge.outline.cast-function-refinement",
  "display_name": "Outline Cast Function Refinement",
  "llm_description": "Refine cast function and character job clarity for one chapter.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/cast-function-refinement",
  "graph_node": "outline.phase_05_cast_function_refinement",
  "phase_id": "phase_05_cast_function_refinement",
  "logical_phase": "phase_05_cast_function_refinement",
  "prompt_contract": "Return one chapter payload plus cast_report without changing locked chronology.",
  "output_hint": "valid phase_05 cast refinement JSON",
  "required_params": [
    "chapter_target_id",
    "chapter_input_outline",
    "request"
  ],
  "optional_params": [
    "character_registry",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_05_cast_function_refinement.md"
  ],
  "help_refs": [
    "skills/bookforge/outline/cast-function-refinement/HELP.md"
  ],
  "example_params": {
    "chapter_target_id": 1,
    "chapter_input_outline": {
      "chapters": []
    },
    "request": "Refine cast function."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
