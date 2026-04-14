---
name: scene-planning
description: Plans the next scene card from outline, state, and recent lint context.
metadata:
  skill_id: bookforge.run.scene-planning
  display_name: Run Phase - Scene Planning
  kind: phase
  graph_node: run.plan
  phase_id: plan
  logical_phase: plan
---

# Run Phase - Scene Planning

Use this skill when the task belongs to `run.plan` in the BookForge skill tree.

Prompt contract
- Generate the scene card and preserve the BookForge scene-card contract.

Output
- JSON matching the scene-card contract
