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
  "skill_id": "bookforge.run.scene-writing",
  "folder": "run/scene-writing",
  "display_name": "Run Phase - Scene Writing",
  "llm_description": "Writes the full scene prose and primary patch from the approved scene card and continuity pack.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.write",
  "phase_id": "write",
  "logical_phase": "write",
  "prompt_contract": "Write the scene prose and emit the corresponding patch without violating continuity rules.",
  "output_hint": "scene prose plus JSON patch aligned with the write contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "continuity_pack"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/write/",
    "src/bookforge/phases/write_phase.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Write the scene prose for the approved scene card.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "scene_card": {},
      "continuity_pack": {}
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
