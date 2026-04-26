---
name: scene-commit
description: Commit a validated scene artifact into the draft state.
metadata:
  skill_id: bookforge.run.scene-commit
  display_name: Run Scene Commit
  kind: run_phase
  graph_node: run.apply_commit
  phase_id: apply_commit
  logical_phase: scene_commit
---

# Run Scene Commit

Use this skill when the task belongs to `run.apply_commit` in the BookForge skill tree.

Prompt contract
- Summarize deterministic commit prerequisites and expected artifact promotions.

Output
- a commit readiness summary with canonical artifact targets
