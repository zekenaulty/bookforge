# Run Phase - State Repair

Skill id: `bookforge.run.state-repair`
Kind: `phase`
Graph node: `run.state_repair`
Phase id: `state_repair`
Logical phase: `state_repair`

## Purpose
- Repairs the authoritative patch after prose generation without rewriting the full scene again.

## Prompt Contract
- Emit the authoritative state-repair patch while preserving the already-written prose.

## References
- `resources/prompt_blocks/phase/state_repair/`
- `src/bookforge/phases/state_repair_phase.py`
- `docs/help/run.md`
