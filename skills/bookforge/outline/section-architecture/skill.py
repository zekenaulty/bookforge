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
  "skill_id": "bookforge.outline.section-architecture",
  "display_name": "Outline Section Architecture",
  "llm_description": "Create section architecture from an approved chapter spine.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/section-architecture",
  "graph_node": "outline.phase_02_section_architecture",
  "phase_id": "phase_02_section_architecture",
  "logical_phase": "phase_02_section_architecture",
  "prompt_contract": "Return section architecture JSON that preserves chapter ids and target pacing.",
  "output_hint": "valid phase_02 section architecture JSON",
  "required_params": [
    "chapter_spine",
    "request"
  ],
  "optional_params": [
    "book",
    "targets",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_02_section_architecture.md"
  ],
  "help_refs": [
    "skills/bookforge/outline/section-architecture/HELP.md"
  ],
  "example_params": {
    "chapter_spine": {
      "chapters": []
    },
    "request": "Draft section architecture."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
