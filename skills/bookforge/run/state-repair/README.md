# Run State Repair

Skill id: `bookforge.run.state-repair`
Kind: `run_phase`
Graph node: `run.state_repair`
Phase id: `state_repair`
Logical phase: `state_repair`

## Purpose
- Repair state deltas after a scene write or prose repair.

## Prompt Contract
- Return state updates consistent with prose and durable registry rules.

## References
- `resources/prompt_templates/state_repair.md`
- `src/bookforge/pipeline/state_apply.py`
