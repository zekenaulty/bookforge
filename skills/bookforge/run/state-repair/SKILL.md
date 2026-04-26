---
name: state-repair
description: Repair state deltas after a scene write or prose repair.
metadata:
  skill_id: bookforge.run.state-repair
  display_name: Run State Repair
  kind: run_phase
  graph_node: run.state_repair
  phase_id: state_repair
  logical_phase: state_repair
---

# Run State Repair

Use this skill when the task belongs to `run.state_repair` in the BookForge skill tree.

Prompt contract
- Return state updates consistent with prose and durable registry rules.

Output
- valid state repair JSON
