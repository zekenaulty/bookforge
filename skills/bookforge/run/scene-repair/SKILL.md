---
name: scene-repair
description: Repair prose for a single scene based on lint findings and bounded constraints.
metadata:
  skill_id: bookforge.run.scene-repair
  display_name: Run Scene Repair
  kind: run_phase
  graph_node: run.repair_scene
  phase_id: repair_scene
  logical_phase: scene_repair
---

# Run Scene Repair

Use this skill when the task belongs to `run.repair_scene` in the BookForge skill tree.

Prompt contract
- Return repaired prose while preserving scene facts and requested repair scope.

Output
- repaired scene prose text or structured refusal
