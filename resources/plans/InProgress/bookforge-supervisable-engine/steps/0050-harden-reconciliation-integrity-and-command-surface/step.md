# 0050 Harden Reconciliation, Integrity, And Command Surface

Status: draft

## Goal
- Make the supervised paths safe enough for repeated use and difficult to misuse through misleading docs, stale artifacts, partial reconciliation, or incorrect branch merge behavior.

## Problem
- The first five stories can expose truthful surfaces and execution paths, but callers still need strong guarantees that:
  - state was reconciled before control returned
  - no-op or stale writes are visible
  - degraded integrity is surfaced instead of swallowed
  - help text does not overclaim runtime scope

## Detailed Work
- Add mandatory post-execution reconciliation before returning control on `main`.
- Add mandatory post-promotion reconciliation before merged content becomes canonical.
- Add mandatory post-assembly-branch reconciliation before assembled content is eligible for promotion.
- Add pre/post revision diff helpers for state-surface comparison.
- Strengthen integrity helpers so they can flag:
  - mixed workflow-family contamination
  - mutable-source materialization
  - outline/prose/state disagreement
  - overscoped recovery
- Surface merge-specific failures explicitly, including:
  - promotion without validation
  - assembly promotion without validation
  - unvalidated assembly work touching `main`
  - branch lineage drift
- Add one explicit mapping table between:
  - branch lifecycle state
  - public execution result
  - canonical-change status
- Surface no-op, stale-write, downgraded-integrity, promotion-required, and recovery-required outcomes explicitly.
- Align help docs and CLI language with the actual execution surface.
- Keep new helpers small and split by concern.

## Files Likely Touched
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/cli.py`
- `docs/help/workflow.md`
- `docs/help/outline_generate.md`
- `docs/help/run.md`
- `docs/help/index.md`

## Tests
- `python -m pytest tests/test_query_integrity.py tests/test_workspace_init.py tests/test_section_workflow.py tests/test_runner_targeting.py`
- Add targeted reconciliation/no-op coverage if needed, for example `tests/test_reconciliation.py`
- Add merge-path reconciliation coverage if branch promotion or assembly helpers are introduced, for example `tests/test_branch_reconciliation.py`

## Definition Of Done
- Every supported execution result can be classified as `success`, `no_op`, `retryable_pause`, `hard_fail`, `integrity_degraded`, or `promotion_required`.
- Integrity regressions introduced during repair are surfaced, not swallowed.
- Promotion and assembly cannot quietly bypass reconciliation.
- Callers can map branch state, public result, and canonical-change status without reverse-engineering the merge path.
- Help docs do not imply a broader runtime scope than the code actually executes.
- Callers can tell whether a request changed canonical state, changed branch state only, or failed before canonical promotion.
- Callers can tell whether integrity improved or worsened.

## Notes
- This story is where the command/help surface finally becomes trustworthy enough for external orchestration.
