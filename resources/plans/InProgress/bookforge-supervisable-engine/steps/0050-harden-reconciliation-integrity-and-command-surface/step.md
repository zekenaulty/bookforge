# 0050 Harden Reconciliation, Integrity, And Command Surface

Status: completed

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
- `src/bookforge/supervision/reconcile.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/execution/scoped.py`
- `src/bookforge/branching.py`
- `src/bookforge/branching_fork.py`
- `src/bookforge/branching_execution.py`
- `src/bookforge/branching_lifecycle.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/runner.py`
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
- Current executed validation:
  - `python -m pytest --basetemp .pytest_tmp_integrity_slice tests/test_query_integrity.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scope_contracts.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050c tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0050_branch_receipts tests/test_branch_execution.py tests/test_fork_group_assembly.py tests/test_branch_promotion.py tests/test_supervision_emit.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050d tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0050_integrity_plus tests/test_query_integrity.py tests/test_supervision_emit.py tests/test_scoped_execution.py tests/test_query_workspace.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050f tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`

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
- Current implemented slice:
  - main-branch reconciliation snapshots and before/after diff details
  - branch-local reconciliation snapshots and before/after diff details for off-main mutation paths
  - promotion now emits a reconciled main-branch result instead of only a derived-branch result
  - ambiguous reconciliation field renamed to `pre_reconciliation_status`
  - revision-only expected-node drift is classified as `stale_write`
  - structural integrity now detects `workflow_family_contamination`, `stale_parent`, and `overscoped_recovery`
  - branch-control logic has been split into smaller files before further 0050 growth
  - branch receipts now emit `branch_change_status` without claiming canonical mutation
  - branch revision tokens now use microsecond precision to avoid same-second node collisions during rapid branch activity
  - workflow and run help now describe the public reconciliation fields
- Follow-on work:
  - future integrity detectors beyond the current chimera/mutable-source/workflow-family/stale-parent/overscoped slice can land as later stories without blocking 0050 completion
  - additional command/help alignment for newly extracted execution actions now belongs to `0060`
