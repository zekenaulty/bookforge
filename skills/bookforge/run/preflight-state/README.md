# Run Phase - Preflight State

Skill id: `bookforge.run.preflight-state`
Kind: `phase`
Graph node: `run.preflight`
Phase id: `preflight`
Logical phase: `preflight`

## Purpose
- Applies scene-local preflight state reasoning before prose generation.

## Prompt Contract
- Emit the authoritative preflight patch for scene-local state updates.

## References
- `resources/prompt_blocks/phase/preflight/`
- `src/bookforge/phases/preflight_phase.py`
- `docs/help/run.md`
