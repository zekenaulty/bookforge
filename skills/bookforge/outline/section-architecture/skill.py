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
  "folder": "outline/section-architecture",
  "display_name": "Outline Phase 02 - Section Architecture",
  "llm_description": "Expands the chapter spine into chapter sections with intentional section roles and structure.",
  "kind": "phase",
  "category": "outline",
  "graph_node": "outline.phase_02_section_architecture",
  "phase_id": "phase_02_section_architecture",
  "logical_phase": "phase_02_section_architecture",
  "prompt_contract": "Transform the spine into sections_v1 while preserving chapter identity and order.",
  "output_hint": "JSON matching the sections_v1 output contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "working_spine",
    "constraints"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/outline_pipeline/phase_02_section_architecture_prompt_contract.md",
    "src/bookforge/phases/outline/phase_02_section_architecture.py",
    "docs/help/outline_generate.md"
  ],
  "help_refs": [
    "docs/help/outline_generate.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Expand the spine into a sectioned chapter plan.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "schema_version": "spine_v1",
      "chapters": [
        {
          "chapter_id": 1,
          "title": "The Archive Below"
        }
      ]
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
