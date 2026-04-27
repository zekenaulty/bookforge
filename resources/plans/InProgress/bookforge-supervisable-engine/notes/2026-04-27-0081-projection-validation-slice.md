# 2026-04-27 0081 Projection Validation Slice

## Summary
- Extended `validate_recovery_branch` beyond character state files.
- Validation now inspects affected branch-local:
  - chapter summaries
  - setting projections
  - appearance projections
- The branch is blocked when these artifacts reference non-outline character IDs or carry embedded `node`/`selector` branch coordinates from outside the recovery branch.

## Why
- A recovery branch can normalize outline data and rebuild character state while stale side projections still point at the polluted timeline.
- The Nanda author agent needs BookForge to reject that state before promotion instead of relying on the user to notice ghost facts in side data.

## Current Scope
- Implemented deterministic checks:
  - `char_*` references in affected summary/projection payloads must exist in the normalized outline character set.
  - Character-reference fields such as `character_id`, `characters`, `cast`, and `pov_character` must not name non-outline characters.
  - Projection artifacts with embedded `node.branch_id` or `selector.branch_id` must match the recovery branch.
- Deferred semantic checks:
  - continuity contradictions in prose-like summaries
  - location/setting semantic drift beyond stale branch coordinates and ghost character refs
  - inventory/deep-state validation

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_projection_validation_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_projection_validation_full`
  - Result: `308 passed`

## Next
- Add inventory/deep-state validation and downstream dependency tracing.
