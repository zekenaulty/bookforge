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
  "folder": "outline/scene-draft",
  "display_name": "Outline Phase 03 - Scene Draft",
  "llm_description": "Builds a full scene-level draft outline with transition-ready fields.",
  "kind": "phase",
  "category": "outline",
  "graph_node": "outline.phase_03_scene_draft",
  "phase_id": "phase_03_scene_draft",
  "logical_phase": "phase_03_scene_draft",
  "prompt_contract": "Produce the scene-draft outline with sections, scenes, and transition-ready structure.",
  "output_hint": "JSON matching the outline scene-draft contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "working_sections",
    "transition_hints"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md",
    "src/bookforge/phases/outline/phase_03_scene_draft.py",
    "docs/help/outline_generate.md"
  ],
  "help_refs": [
    "docs/help/outline_generate.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Draft the scene outline for chapter one.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "schema_version": "sections_v1",
      "chapters": [
        {
          "chapter_id": 1,
          "sections": []
        }
      ]
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
