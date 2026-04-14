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
  "skill_id": "bookforge.run.scene-repair",
  "folder": "run/scene-repair",
  "display_name": "Run Phase - Scene Repair",
  "llm_description": "Repairs scene prose and patch output after lint or deterministic invariant failures.",
  "kind": "phase",
  "category": "run",
  "graph_node": "run.repair",
  "phase_id": "repair",
  "logical_phase": "repair",
  "prompt_contract": "Repair the scene output while preserving required state and continuity invariants.",
  "output_hint": "repaired scene prose plus JSON patch aligned with the repair contract",
  "required_params": [
    "request",
    "book_id",
    "input_payload"
  ],
  "optional_params": [
    "chapter",
    "scene",
    "lint_report"
  ],
  "source_refs": [
    "resources/prompt_blocks/phase/repair/",
    "src/bookforge/phases/repair_phase.py",
    "docs/help/run.md"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "routes": [],
  "example_params": {
    "request": "Repair the failing scene output using the lint report.",
    "book_id": "criticulous_b1",
    "input_payload": {
      "scene_card": {},
      "lint_report": {}
    }
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
