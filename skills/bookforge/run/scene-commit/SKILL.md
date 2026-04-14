---
name: scene-commit
description: Commits validated prose, state, and metadata artifacts to the BookForge workspace.
metadata:
  skill_id: bookforge.run.scene-commit
  display_name: Run Phase - Scene Commit
  kind: phase
  graph_node: run.commit
  phase_id: commit
  logical_phase: commit
---

# Run Phase - Scene Commit

Use this skill when the task belongs to `run.commit` in the BookForge skill tree.

Prompt contract
- Package the final commit step, including artifact writes and durable state advancement, without skipping validations.

Output
- a deterministic commit checklist or commit-ready response
