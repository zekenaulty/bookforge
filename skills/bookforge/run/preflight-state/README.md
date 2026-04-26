# Run Preflight State

Skill id: `bookforge.run.preflight-state`
Kind: `run_phase`
Graph node: `run.preflight`
Phase id: `preflight`
Logical phase: `preflight_state`

## Purpose
- Align state and durable registries before scene prose is written.

## Prompt Contract
- Return state alignment updates or explicit refusal issues for the target scene.

## References
- `resources/prompt_templates/preflight.md`
- `src/bookforge/runner.py`
