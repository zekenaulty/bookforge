# Run Scene Planning

Skill id: `bookforge.run.scene-planning`
Kind: `run_phase`
Graph node: `run.plan_scene`
Phase id: `plan_scene`
Logical phase: `scene_planning`

## Purpose
- Plan a single scene card for a scoped drafting target.

## Prompt Contract
- Return a scene card that satisfies the planning schema and current outline target.

## References
- `resources/prompt_templates/plan.md`
- `src/bookforge/execution/scene_actions.py`
