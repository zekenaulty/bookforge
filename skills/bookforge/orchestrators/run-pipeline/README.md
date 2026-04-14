# Run Pipeline Orchestrator

Skill id: `bookforge.orchestrators.run-pipeline`
Kind: `orchestrator`
Graph node: `run_pipeline`
Phase id: `run_pipeline`
Logical phase: `run_pipeline`

## Purpose
- Routes scene-planning, drafting, repair, lint, and commit requests across the run graph.

## Prompt Contract
- Route run-loop tasks to the right scene-phase skill without collapsing distinct validation and repair steps together.

## References
- `docs/help/run.md`
- `src/bookforge/runner.py`
