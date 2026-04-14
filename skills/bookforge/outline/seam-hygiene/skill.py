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
  "skill_id": "bookforge.outline.seam-hygiene",
  "folder": "outline/seam-hygiene",
  "display_name": "Outline Phase 04D - Seam Hygiene",
  "llm_description": "Performs final local seam cleanup after transition insertion and relink steps.",
  "kind": "phase",
  "category": "outline",
  "graph_node": "outline.phase_04d_seam_hygiene",
  "phase_id": "phase_04d_seam_hygiene",
  "logical_phase": "phase_04_transition_causality_refinement",
  "prompt_contract": "Clean seam-local hygiene issues inside the active window without altering scene identity or order.",
  "output_hint": "JSON matching the outline_seam_hygiene_v1 contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "window",
    "allowed_fields"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/outline_pipeline/phase_04d_seam_hygiene_prompt_contract.md",
    "src/bookforge/phases/outline/phase_04d_seam_hygiene.py",
    "docs/help/outline_generate.md"
  ],
  "help_refs": [
    "docs/help/outline_generate.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Perform seam hygiene on the active transition window.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "chapter_id": 1,
      "outline": {}
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
