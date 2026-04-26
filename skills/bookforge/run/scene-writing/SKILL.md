---
name: scene-writing
description: Write prose for a single scene without automatically linting or repairing it.
metadata:
  skill_id: bookforge.run.scene-writing
  display_name: Run Scene Writing
  kind: run_phase
  graph_node: run.write_scene
  phase_id: write_scene
  logical_phase: scene_writing
---

# Run Scene Writing

Use this skill when the task belongs to `run.write_scene` in the BookForge skill tree.

Prompt contract
- Return scene prose that follows the scene card, continuity pack, and author voice.

Output
- scene prose text or a structured refusal with missing prerequisites
