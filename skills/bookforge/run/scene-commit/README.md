# Run Phase - Scene Commit

Skill id: `bookforge.run.scene-commit`
Kind: `phase`
Graph node: `run.commit`
Phase id: `commit`
Logical phase: `commit`

## Purpose
- Commits validated prose, state, and metadata artifacts to the BookForge workspace.

## Prompt Contract
- Package the final commit step, including artifact writes and durable state advancement, without skipping validations.

## References
- `src/bookforge/runner.py`
- `src/bookforge/pipeline/state_apply.py`
- `docs/help/run.md`
