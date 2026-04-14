---
name: run-pipeline
description: Routes scene-planning, drafting, repair, lint, and commit requests across the run graph.
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
- Route run-loop tasks to the right scene-phase skill without collapsing distinct validation and repair steps together.

Output
- a routed run action plan or a direct next-step response
