---
name: state-repair
description: Repairs the authoritative patch after prose generation without rewriting the full scene again.
metadata:
  skill_id: bookforge.run.state-repair
  display_name: Run Phase - State Repair
  kind: phase
  graph_node: run.state_repair
  phase_id: state_repair
  logical_phase: state_repair
---

# Run Phase - State Repair

Use this skill when the task belongs to `run.state_repair` in the BookForge skill tree.

Prompt contract
- Emit the authoritative state-repair patch while preserving the already-written prose.

Output
- JSON matching the state-repair contract
