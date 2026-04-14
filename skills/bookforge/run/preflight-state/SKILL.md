---
name: preflight-state
description: Applies scene-local preflight state reasoning before prose generation.
metadata:
  skill_id: bookforge.run.preflight-state
  display_name: Run Phase - Preflight State
  kind: phase
  graph_node: run.preflight
  phase_id: preflight
  logical_phase: preflight
---

# Run Phase - Preflight State

Use this skill when the task belongs to `run.preflight` in the BookForge skill tree.

Prompt contract
- Emit the authoritative preflight patch for scene-local state updates.

Output
- JSON matching the preflight patch contract
