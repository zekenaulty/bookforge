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
  "skill_id": "bookforge.run.preflight-state",
  "folder": "run/preflight-state",
  "display_name": "Run Phase - Preflight State",
  "llm_description": "Applies scene-local preflight state reasoning before prose generation.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.preflight",
  "phase_id": "preflight",
  "logical_phase": "preflight",
  "prompt_contract": "Emit the authoritative preflight patch for scene-local state updates.",
  "output_hint": "JSON matching the preflight patch contract",
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
    "resources/prompt_blocks/phase/preflight/",
    "src/bookforge/phases/preflight_phase.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Generate the preflight state patch for the current scene.",
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
