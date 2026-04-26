# Outline Pipeline Orchestrator

Skill id: `bookforge.orchestrators.outline-pipeline`
Kind: `orchestrator`
Graph node: `outline_pipeline`
Phase id: `outline_pipeline`
Logical phase: `outline_pipeline`

## Purpose
- Route outline generation, rerun, resume, backup, and restore work through the outline graph.

## Prompt Contract
- Map an outline request to the legal outline phase range, prerequisites, and source artifacts.

## References
- `src/bookforge/outline.py`
- `src/bookforge/phases/outline/context.py`
