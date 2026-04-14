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
  "skill_id": "bookforge.outline.handoff-normalize",
  "folder": "outline/handoff-normalize",
  "display_name": "Outline Phase 04C-Handoff - Handoff Normalize",
  "llm_description": "Normalizes terminal handoff and location-jump metadata for targeted scenes only.",
  "kind": "phase",
  "category": "outline",
  "graph_node": "outline.phase_04c_handoff_normalize",
  "phase_id": "phase_04c_handoff_normalize",
  "logical_phase": "phase_04_transition_causality_refinement",
  "prompt_contract": "Normalize the allowed handoff fields for the targeted refs without changing scene order or scene identity.",
  "output_hint": "JSON matching the outline_handoff_normalize_v1 contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "handoff_targets",
    "allowed_jump_modes"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/outline_pipeline/phase_04c_handoff_normalize_prompt_contract.md",
    "src/bookforge/phases/outline/phase_04c_handoff_normalize.py",
    "docs/help/outline_generate.md"
  ],
  "help_refs": [
    "docs/help/outline_generate.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Normalize handoff metadata for the last scene in chapter one.",
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
