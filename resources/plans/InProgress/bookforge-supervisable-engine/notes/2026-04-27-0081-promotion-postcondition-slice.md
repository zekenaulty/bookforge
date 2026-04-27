# 2026-04-27 0081 Recovery Promotion Postcondition

## Summary
- Added canonical postcondition details to `promote_recovery_branch`.
- The promotion result now reports:
  - pre/post outline-lineage status
  - pre/post integrity status
  - planned promotion removals
  - applied promotion removals
  - whether main cleared chimera risk
  - whether main outline lineage and integrity are healthy after promotion

## Why
- Nanda needs to verify that a recovery plan actually changed canonical timeline health.
- A successful branch promotion is not enough by itself; the author layer needs to know whether `main` is now trusted and which invalid files were removed.

## Files Touched
- `src/bookforge/execution/recovery_validation.py`
- `tests/test_recovery_actions.py`
- `docs/help/index.md`
- `docs/help/workflow.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_promotion_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_promotion_full`
  - Result: `308 passed`

## Next
- Add downstream dependency tracing after redraft.
- Expand validation from outline lineage into state/projection family health.
