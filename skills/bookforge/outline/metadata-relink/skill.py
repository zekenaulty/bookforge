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
  "skill_id": "bookforge.outline.metadata-relink",
  "display_name": "Outline Metadata Relink",
  "llm_description": "Relink metadata in constrained scene windows after transition insertions.",
  "kind": "outline_phase",
  "category": "outline",
  "folder": "outline/metadata-relink",
  "graph_node": "outline.phase_04c_metadata_relink",
  "phase_id": "phase_04c_metadata_relink",
  "logical_phase": "phase_04_transition_causality_refinement",
  "prompt_contract": "Return only allowed metadata field changes for the active relink window.",
  "output_hint": "valid phase_04c metadata relink JSON",
  "required_params": [
    "chapter_target_id",
    "chapter_input_outline",
    "request"
  ],
  "optional_params": [
    "phase04c_current_window",
    "phase04c_allowed_fields"
  ],
  "source_refs": [
    "resources/prompt_templates/outline_phase_04c_metadata_relink.md"
  ],
  "help_refs": [
    "skills/bookforge/outline/metadata-relink/HELP.md"
  ],
  "example_params": {
    "chapter_target_id": 1,
    "chapter_input_outline": {
      "chapters": []
    },
    "request": "Relink metadata."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
