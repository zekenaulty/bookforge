# Outline Pipeline Orchestrator

Skill id: `bookforge.orchestrators.outline-pipeline`
Kind: `orchestrator`
Graph node: `outline_pipeline`
Phase id: `outline_pipeline`
Logical phase: `outline_pipeline`

## Purpose
- Routes outline generation, rerun, resume, and phase-window requests across the outline graph.

## Prompt Contract
- Route outline tasks to the correct outline phase skill and preserve the existing phase order from BookForge.

## References
- `docs/help/outline_generate.md`
- `src/bookforge/outline.py`
- `src/bookforge/phases/outline/context.py`
