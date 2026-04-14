---
name: book-workflow
description: Routes setup, outline, run, recovery, and export requests across the BookForge skill tree.
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
- Choose the correct BookForge workflow, preserve graph boundaries, and hand work to the best matching child skill.

Output
- a routed action plan or a direct next-step response
