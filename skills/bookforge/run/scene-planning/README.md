# Run Phase - Scene Planning

Skill id: `bookforge.run.scene-planning`
Kind: `phase`
Graph node: `run.plan`
Phase id: `plan`
Logical phase: `plan`

## Purpose
- Plans the next scene card from outline, state, and recent lint context.

## Prompt Contract
- Generate the scene card and preserve the BookForge scene-card contract.

## References
- `resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md`
- `src/bookforge/phases/plan.py`
- `docs/help/run.md`
