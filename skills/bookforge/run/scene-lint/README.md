# Run Phase - Scene Lint

Skill id: `bookforge.run.scene-lint`
Kind: `phase`
Graph node: `run.lint`
Phase id: `lint`
Logical phase: `lint`

## Purpose
- Evaluates the scene and patch for continuity, invariant, and anti-duplication failures.

## Prompt Contract
- Produce a lint report that surfaces failure reasons instead of silently forgiving them.

## References
- `resources/prompt_blocks/phase/lint/lint_policy_rules_and_inputs.md`
- `src/bookforge/phases/lint_phase.py`
- `docs/help/run.md`
