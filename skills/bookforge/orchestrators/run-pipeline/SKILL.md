---
name: run-pipeline
description: Route scene writing, lint, repair, state repair, and commit work through the run graph.
metadata:
  skill_id: bookforge.orchestrators.run-pipeline
  display_name: Run Pipeline Orchestrator
  kind: orchestrator
  graph_node: run_pipeline
  phase_id: run_pipeline
  logical_phase: run_pipeline
---

# Run Pipeline Orchestrator

Use this skill when the task belongs to `run_pipeline` in the BookForge skill tree.

Prompt contract
- Map a drafting request to legal scene-phase actions and readiness prerequisites.

Output
- a scene-phase routing plan with legal next actions
