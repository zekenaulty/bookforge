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
  "folder": "outline/chapter-spine",
  "display_name": "Outline Phase 01 - Chapter Spine",
  "llm_description": "Builds the chapter spine from prompt intent and outline seed context.",
  "kind": "phase",
  "category": "outline",
  "graph_node": "outline.phase_01_chapter_spine",
  "phase_id": "phase_01_chapter_spine",
  "logical_phase": "phase_01_chapter_spine",
  "prompt_contract": "Generate the spine_v1 chapter topology and preserve strict chapter-level structure.",
  "output_hint": "JSON matching the spine_v1 output contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "prompt_file",
    "constraints"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/outline_pipeline/phase_01_chapter_spine_prompt_contract.md",
    "src/bookforge/phases/outline/phase_01_chapter_spine.py",
    "docs/help/outline_generate.md"
  ],
  "help_refs": [
    "docs/help/outline_generate.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Draft the opening chapter spine for a progression fantasy.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "premise": "A failed scholar becomes a dungeon archivist.",
      "target_chapter_count": 8
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
