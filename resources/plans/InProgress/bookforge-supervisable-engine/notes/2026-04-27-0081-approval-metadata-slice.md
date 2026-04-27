# 2026-04-27 0081 Approval Metadata Slice

## Summary
- Tightened recovery action discovery so each recovery primitive reports a specific approval reason.
- Nanda can now distinguish:
  - `recovery anchor selection`
  - `destructive cleanup/quarantine`
  - `scope output invalidation`
  - `state/projection rebuild`
  - `scope redraft`
  - `promotion to main`
  - `broad recovery radius`

## Boundary
- This updates query/action-discovery metadata.
- It does not add a new approval enforcement layer.
- Enforcement remains branch-first execution, validation, and promotion safety; Nanda owns approval flow and decision policy.

## Why
- Generic approval text is not enough for an author agent planning multi-step recovery.
- The author decision layer needs to know whether an action is selecting a timeline anchor, invalidating outputs, rebuilding state, redrafting, or promoting canonical changes.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_approval_focus`
  - Result: `35 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_approval_full`
  - Result: `308 passed`
