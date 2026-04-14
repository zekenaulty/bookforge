# Book Workflow Orchestrator

Skill id: `bookforge.orchestrators.book-workflow`
Kind: `orchestrator`
Graph node: `book_workflow`
Phase id: `book_workflow`
Logical phase: `book_workflow`

## Purpose
- Routes setup, outline, run, recovery, and export requests across the BookForge skill tree.

## Prompt Contract
- Choose the correct BookForge workflow, preserve graph boundaries, and hand work to the best matching child skill.

## References
- `docs/help/index.md`
- `src/bookforge/cli.py`
- `README.md`
