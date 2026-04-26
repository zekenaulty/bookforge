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
  "skill_id": "bookforge.outline.chapter-spine",
  "display_name": "Outline Chapter Spine",
  "llm_description": "Create or refine the book-level chapter spine.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/chapter-spine",
  "graph_node": "outline.phase_01_chapter_spine",
  "phase_id": "phase_01_chapter_spine",
  "logical_phase": "phase_01_chapter_spine",
  "prompt_contract": "Return the chapter-spine JSON contract for the requested book scope.",
  "output_hint": "valid phase_01 chapter spine JSON",
  "required_params": [
    "book",
    "targets",
    "request"
  ],
  "optional_params": [
    "notes",
    "transition_hints"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_01_chapter_spine.md",
    "src/bookforge/phases/outline/context.py"
  ],
  "help_refs": [
    "skills/bookforge/outline/chapter-spine/HELP.md"
  ],
  "example_params": {
    "book": {
      "book_id": "demo_book",
      "title": "Demo Book"
    },
    "targets": {
      "chapters": 3
    },
    "request": "Draft the chapter spine."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
