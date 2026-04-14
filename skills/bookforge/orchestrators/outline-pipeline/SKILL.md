---
name: outline-pipeline
description: Routes outline generation, rerun, resume, and phase-window requests across the outline graph.
metadata:
  skill_id: bookforge.orchestrators.outline-pipeline
  display_name: Outline Pipeline Orchestrator
  kind: orchestrator
  graph_node: outline_pipeline
  phase_id: outline_pipeline
  logical_phase: outline_pipeline
---

# Outline Pipeline Orchestrator

Use this skill when the task belongs to `outline_pipeline` in the BookForge skill tree.

Prompt contract
- Route outline tasks to the correct outline phase skill and preserve the existing phase order from BookForge.

Output
- a routed outline action plan or a direct next-step response
