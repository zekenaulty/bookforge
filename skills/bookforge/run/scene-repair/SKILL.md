---
name: scene-repair
description: Repairs scene prose and patch output after lint or deterministic invariant failures.
metadata:
  skill_id: bookforge.run.scene-repair
  display_name: Run Phase - Scene Repair
  kind: phase
  graph_node: run.repair
  phase_id: repair
  logical_phase: repair
---

# Run Phase - Scene Repair

Use this skill when the task belongs to `run.repair` in the BookForge skill tree.

Prompt contract
- Repair the scene output while preserving required state and continuity invariants.

Output
- repaired scene prose plus JSON patch aligned with the repair contract
