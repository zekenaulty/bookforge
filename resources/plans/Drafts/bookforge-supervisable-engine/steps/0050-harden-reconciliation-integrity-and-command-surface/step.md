# 0050 Harden Reconciliation, Integrity, And Command Surface

Status: draft

## Goal
- Make the first supervised path safe enough for repeated use and difficult to misuse through misleading docs, stale artifacts, or partial reconciliation.

## Problem
- The first four stories can expose truthful surfaces, but callers still need strong guarantees that:
  - state was reconciled before control returned
  - no-op or stale writes are visible
  - degraded integrity is surfaced instead of swallowed
  - help text does not overclaim runtime scope

## Detailed Work
- Add mandatory post-execution reconciliation before returning control.
- Add pre/post revision diff helpers for state-surface comparison.
- Strengthen integrity helpers so they can flag:
  - mixed workflow-family contamination
  - mutable-source materialization
  - outline/prose/state disagreement
  - overscoped recovery
- Surface no-op, stale-write, downgraded-integrity, and recovery-required outcomes explicitly.
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

## Definition Of Done
- Every supported execution result can be classified as success, no-op, pause, hard-fail, or integrity-degraded.
- Integrity regressions introduced during repair are surfaced, not swallowed.
- Help docs do not imply a broader runtime scope than the code actually executes.
- Callers can tell whether a request changed canonical state and whether integrity improved or worsened.

## Notes
- This story is where the command/help surface finally becomes trustworthy enough for external orchestration.
