# Run Scene Lint

Skill id: `bookforge.run.scene-lint`
Kind: `run_phase`
Graph node: `run.lint_scene`
Phase id: `lint_scene`
Logical phase: `scene_lint`

## Purpose
- Lint one scene for prose, continuity, and state-contract issues.

## Prompt Contract
- Return lint findings and pass/fail status without mutating scene prose.

## References
- `resources/prompt_templates/lint.md`
- `src/bookforge/lint.py`
