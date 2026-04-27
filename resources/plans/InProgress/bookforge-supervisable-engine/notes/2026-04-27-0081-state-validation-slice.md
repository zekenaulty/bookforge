# 2026-04-27 0081 Recovery State Validation Slice

## Summary
- Added branch-local character state/projection validation to `validate_recovery_branch`.
- Validation now blocks promotion if the recovery branch contains character index entries or character state files whose `character_id` is absent from the normalized outline.

## Why
- This directly targets the Veiled Ledger ghost-character failure mode.
- Outline lineage can be healthy while stale state/projection data still contains invalid timeline entities.
- The branch must not promote if characters like `char_artie` or `char_vex` survive in state after outline normalization and state rebuild.

## Current Scope
- Implemented:
  - `draft/context/characters/index.json`
  - `draft/context/characters/*.state.json`
- Deferred:
  - continuity prose/fact extraction
  - settings/location projections
  - inventory/deep state
  - chapter summaries
  - appearance/setting projection semantic validation

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_state_validation_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_state_validation_full`
  - Result: `308 passed`

## Next
- Add validation for continuity, settings, inventory/deep state, chapter summaries, and appearance/setting projections.
