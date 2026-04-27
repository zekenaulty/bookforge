# 2026-04-27 0081 Recovery Receipt Postconditions

## Summary
- Added status-aware postcondition snapshots to every branch-local recovery receipt.
- The postcondition surface lets Nanda inspect an action result and see:
  - branch health after the action
  - outline lineage status after the action
  - completed and remaining successful recovery receipts
  - blockers and warnings after the action
  - recommended next recovery action
  - approval-required metadata
  - branch-local mutation scope and canonical-change status

## Important Behavior
- Receipt prerequisites are status-aware.
- A failed `validate_recovery_branch` receipt no longer satisfies the validation prerequisite.
- This matters because recovery branches may be validated multiple times while still missing rebuild/redraft work.
- The next-action snapshot should guide the author layer back to the next missing successful step instead of treating the first failed attempt as completion.
- While validating this slice, the full suite exposed that explicit chapter finalization after lock needed to remain a truthful `no_op` when the chapter was already finalized by section lock. That behavior is now handled at the chapter workflow level without weakening recovery branch mutation status.

## Files Touched
- `src/bookforge/execution/recovery_common.py`
- `tests/test_recovery_actions.py`
- `docs/help/index.md`
- `docs/help/workflow.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`
- `src/bookforge/section_workflow.py`

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_postconditions_focus`
  - Result: `35 passed`
- Regression focus after chapter-finalize no-op correction:
  - `python -m pytest -o addopts='' tests/test_execution_actions.py::test_finalize_chapter_action_returns_main_scoped_emitted_result tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_postconditions_focus`
  - Result: `36 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_postconditions_full`
  - Result: `308 passed`

## Next
- Run the full suite.
- Add blast-radius query surfaces for prose, state, series, continuity, and projection invalidation candidates.
- Extend promotion results with canonical post-promotion integrity deltas.
