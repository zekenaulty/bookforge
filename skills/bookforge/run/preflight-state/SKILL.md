---
name: preflight-state
description: Align state and durable registries before scene prose is written.
metadata:
  skill_id: bookforge.run.preflight-state
  display_name: Run Preflight State
  kind: run_phase
  graph_node: run.preflight
  phase_id: preflight
  logical_phase: preflight_state
---

# Run Preflight State

Use this skill when the task belongs to `run.preflight` in the BookForge skill tree.

Prompt contract
- Return state alignment updates or explicit refusal issues for the target scene.

Output
- valid preflight state JSON
