# 2026-04-27 0081 Multi-Scope Coverage

## Summary
- Added regression coverage for explicit broad-scope recovery branch creation.
- The test now covers:
  - caller-provided `affected_scopes` with multiple scopes
  - manifest persistence of each affected scope
  - empty scene-range handling for a declared scope with no registry range
  - broad-radius approval metadata on recovery actions
  - blast-radius `scope_groups` output for broad affected scopes

## Boundary
- This is broad-scope contract coverage, not a full Veiled Ledger fixture.
- It does not yet create multiple real chapters with full outline/prose/state/projection contamination.

## Why
- Nanda will need to request broad recovery scopes when a timeline impact report identifies multiple affected chapters or sections.
- BookForge should preserve those scopes and expose broad-radius approval metadata even when some declared scopes have incomplete branch-local material.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0081_multi_scope_focus`
  - Result: `5 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_multi_scope_full`
  - Result: `309 passed`
