# Book Workflow Orchestrator

Skill id: `bookforge.orchestrators.book-workflow`
Kind: `orchestrator`
Graph node: `book_workflow`
Phase id: `book_workflow`
Logical phase: `book_workflow`

## Purpose
- Route setup, end-to-end book workflow, and export-like BookForge requests to narrower outline or run skills.

## Prompt Contract
- Identify the requested book workflow path, required prerequisites, and the next narrow BookForge skill or command to run.

## References
- `docs/help/workflow.md`
- `src/bookforge/cli.py`
