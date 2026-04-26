# Run Scene Commit

Skill id: `bookforge.run.scene-commit`
Kind: `run_phase`
Graph node: `run.apply_commit`
Phase id: `apply_commit`
Logical phase: `scene_commit`

## Purpose
- Commit a validated scene artifact into the draft state.

## Prompt Contract
- Summarize deterministic commit prerequisites and expected artifact promotions.

## References
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/runner.py`
