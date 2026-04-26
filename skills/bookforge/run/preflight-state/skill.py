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
  "display_name": "Run Preflight State",
  "llm_description": "Align state and durable registries before scene prose is written.",
  "kind": "run_phase",
  "category": "run",
  "folder": "run/preflight-state",
  "graph_node": "run.preflight",
  "phase_id": "preflight",
  "logical_phase": "preflight_state",
  "prompt_contract": "Return state alignment updates or explicit refusal issues for the target scene.",
  "output_hint": "valid preflight state JSON",
  "required_params": [
    "workspace",
    "book_id",
    "chapter",
    "scene",
    "scene_card",
    "request"
  ],
  "optional_params": [
    "branch_id",
    "notes"
  ],
  "source_refs": [
    "resources/prompt_templates/preflight.md",
    "src/bookforge/runner.py"
  ],
  "help_refs": [
    "docs/help/run.md"
  ],
  "example_params": {
    "workspace": "workspace",
    "book_id": "demo_book",
    "chapter": 1,
    "scene": 1,
    "scene_card": {},
    "request": "Run preflight state alignment."
  }
})


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
