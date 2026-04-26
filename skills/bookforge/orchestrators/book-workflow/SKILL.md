---
name: book-workflow
description: Route setup, end-to-end book workflow, and export-like BookForge requests to narrower outline or run skills.
metadata:
  skill_id: bookforge.orchestrators.book-workflow
  display_name: Book Workflow Orchestrator
  kind: orchestrator
  graph_node: book_workflow
  phase_id: book_workflow
  logical_phase: book_workflow
---

# Book Workflow Orchestrator

Use this skill when the task belongs to `book_workflow` in the BookForge skill tree.

Prompt contract
- Identify the requested book workflow path, required prerequisites, and the next narrow BookForge skill or command to run.

Output
- a concise routing plan with required inputs and refusal reasons if prerequisites are missing
