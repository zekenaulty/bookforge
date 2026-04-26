# Run Scene Repair

Skill id: `bookforge.run.scene-repair`
Kind: `run_phase`
Graph node: `run.repair_scene`
Phase id: `repair_scene`
Logical phase: `scene_repair`

## Purpose
- Repair prose for a single scene based on lint findings and bounded constraints.

## Prompt Contract
- Return repaired prose while preserving scene facts and requested repair scope.

## References
- `resources/prompt_templates/repair.md`
- `src/bookforge/runner.py`
