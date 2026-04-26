# Run Scene Writing

Skill id: `bookforge.run.scene-writing`
Kind: `run_phase`
Graph node: `run.write_scene`
Phase id: `write_scene`
Logical phase: `scene_writing`

## Purpose
- Write prose for a single scene without automatically linting or repairing it.

## Prompt Contract
- Return scene prose that follows the scene card, continuity pack, and author voice.

## References
- `resources/prompt_templates/write.md`
- `src/bookforge/execution/scene_actions.py`
