# 2026-04-27 0081 Two-Chapter Recovery Fixture

## Summary
- Added an end-to-end two-chapter recovery regression fixture.
- The fixture creates:
  - a clean two-chapter outline anchor
  - polluted mutable outline state with ghost `char_artie`
  - section-draft contamination for both chapters
  - polluted prose outputs for both chapters
  - polluted character state/index data
  - polluted chapter summaries and setting projections
- The test runs:
  - `create_recovery_branch`
  - `quarantine_artifacts`
  - `normalize_outline_scope`
  - `invalidate_scope_outputs`
  - `rebuild_state_scope`
  - `redraft_scope`
  - `validate_recovery_branch`
  - `promote_recovery_branch`

## Assertions
- Normalization restores both affected sections from the clean source run.
- Invalidation removes stale extra scenes in both chapters from the branch.
- State rebuild removes ghost character state and restores only outline-valid characters.
- Redraft regenerates both affected chapter sections in branch scope.
- Promotion removes stale section drafts and extra polluted scenes from `main`.
- Main outline lineage returns to `healthy`.

## Boundary
- This is a real multi-chapter artifact fixture, but still intentionally small.
- It is not a full Veiled Ledger reproduction with large chapter count, real prose volume, or provider-generated artifacts.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0081_multichapter_fixture_focus`
  - Result: `6 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_multichapter_fixture_full`
  - Result: `310 passed`
