---
name: transition-execution
description: Execute selected transition repairs and insertion decisions within one chapter.
metadata:
  skill_id: bookforge.outline.transition-execution
  display_name: Outline Transition Execution
  kind: outline_phase
  graph_node: outline.phase_04b_transition_execution
  phase_id: phase_04b_transition_execution
  logical_phase: phase_04_transition_causality_refinement
---

# Outline Transition Execution

Use this skill when the task belongs to `outline.phase_04b_transition_execution` in the BookForge skill tree.

Prompt contract
- Return one chapter payload and a phase_report resolving selected transition candidates without downgrading required insertions.

Output
- valid phase_04b transition execution JSON
