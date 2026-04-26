---
name: continuity-pack
description: Build or verify the continuity pack used for scene writing.
metadata:
  skill_id: bookforge.run.continuity-pack
  display_name: Run Continuity Pack
  kind: run_phase
  graph_node: run.continuity_pack
  phase_id: continuity_pack
  logical_phase: continuity_pack
---

# Run Continuity Pack

Use this skill when the task belongs to `run.continuity_pack` in the BookForge skill tree.

Prompt contract
- Return compact continuity context grounded in existing state and scene target.

Output
- valid continuity pack JSON
