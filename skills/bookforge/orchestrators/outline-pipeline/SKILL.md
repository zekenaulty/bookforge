---
name: outline-pipeline
description: Route outline generation, rerun, resume, backup, and restore work through the outline graph.
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
- Map an outline request to the legal outline phase range, prerequisites, and source artifacts.

Output
- a phase-scoped outline execution plan
