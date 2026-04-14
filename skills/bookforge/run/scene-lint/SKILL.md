---
name: scene-lint
description: Evaluates the scene and patch for continuity, invariant, and anti-duplication failures.
metadata:
  skill_id: bookforge.run.scene-lint
  display_name: Run Phase - Scene Lint
  kind: phase
  graph_node: run.lint
  phase_id: lint
  logical_phase: lint
---

# Run Phase - Scene Lint

Use this skill when the task belongs to `run.lint` in the BookForge skill tree.

Prompt contract
- Produce a lint report that surfaces failure reasons instead of silently forgiving them.

Output
- JSON matching the lint report contract
