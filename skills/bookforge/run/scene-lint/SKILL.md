---
name: scene-lint
description: Lint one scene for prose, continuity, and state-contract issues.
metadata:
  skill_id: bookforge.run.scene-lint
  display_name: Run Scene Lint
  kind: run_phase
  graph_node: run.lint_scene
  phase_id: lint_scene
  logical_phase: scene_lint
---

# Run Scene Lint

Use this skill when the task belongs to `run.lint_scene` in the BookForge skill tree.

Prompt contract
- Return lint findings and pass/fail status without mutating scene prose.

Output
- valid lint report JSON
