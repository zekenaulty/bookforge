---
name: scene-planning
description: Plan a single scene card for a scoped drafting target.
metadata:
  skill_id: bookforge.run.scene-planning
  display_name: Run Scene Planning
  kind: run_phase
  graph_node: run.plan_scene
  phase_id: plan_scene
  logical_phase: scene_planning
---

# Run Scene Planning

Use this skill when the task belongs to `run.plan_scene` in the BookForge skill tree.

Prompt contract
- Return a scene card that satisfies the planning schema and current outline target.

Output
- valid scene card JSON
