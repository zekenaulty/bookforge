# Run Phase - Scene Repair

Skill id: `bookforge.run.scene-repair`
Kind: `phase`
Graph node: `run.repair`
Phase id: `repair`
Logical phase: `repair`

## Purpose
- Repairs scene prose and patch output after lint or deterministic invariant failures.

## Prompt Contract
- Repair the scene output while preserving required state and continuity invariants.

## References
- `resources/prompt_blocks/phase/repair/`
- `src/bookforge/phases/repair_phase.py`
- `docs/help/run.md`
