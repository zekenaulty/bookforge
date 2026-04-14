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
  "skill_id": "bookforge.run.state-repair",
  "folder": "run/state-repair",
  "display_name": "Run Phase - State Repair",
  "llm_description": "Repairs the authoritative patch after prose generation without rewriting the full scene again.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.state_repair",
  "phase_id": "state_repair",
  "logical_phase": "state_repair",
  "prompt_contract": "Emit the authoritative state-repair patch while preserving the already-written prose.",
  "output_hint": "JSON matching the state-repair contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "prose"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/state_repair/",
    "src/bookforge/phases/state_repair_phase.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Repair the state patch after prose generation.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "scene_card": {},
      "prose": "Sample prose"
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
