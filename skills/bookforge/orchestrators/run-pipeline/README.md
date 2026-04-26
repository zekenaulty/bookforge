# Run Pipeline Orchestrator

Skill id: `bookforge.orchestrators.run-pipeline`
Kind: `orchestrator`
Graph node: `run_pipeline`
Phase id: `run_pipeline`
Logical phase: `run_pipeline`

## Purpose
- Route scene writing, lint, repair, state repair, and commit work through the run graph.

## Prompt Contract
- Map a drafting request to legal scene-phase actions and readiness prerequisites.

## References
- `src/bookforge/runner.py`
- `src/bookforge/execution/scene_actions.py`
