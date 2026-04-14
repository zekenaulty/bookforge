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
  "skill_id": "bookforge.run.continuity-pack",
  "folder": "run/continuity-pack",
  "display_name": "Run Phase - Continuity Pack",
  "llm_description": "Builds the continuity pack used to ground scene writing without replaying raw prose.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.continuity_pack",
  "phase_id": "continuity_pack",
  "logical_phase": "continuity_pack",
  "prompt_contract": "Produce the continuity pack and preserve factual continuity anchors.",
  "output_hint": "JSON matching the continuity-pack contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "state_snapshot"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/continuity_pack/prompt_contract_and_constraints.md",
    "src/bookforge/phases/continuity_phase.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Build the continuity pack for the next scene.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "scene_card": {},
      "state": {}
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
