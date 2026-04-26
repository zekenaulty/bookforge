# 2026-04-26 0072 Nested Branch Primitives

## Summary
- Started 0072.
- Landed the conservative branch hierarchy primitives needed before parallel writer assembly:
  - create branch from parent branch snapshot
  - promote a branch into an explicit parent branch
  - rebase by creating a refreshed child branch from the current parent snapshot and discarding the old branch without erasing history

## Current Boundaries
- These primitives now have workflow CLI wrappers as of the 0072 lifecycle CLI slice.
- The rebase path is intentionally safe and non-semantic: it refreshes the branch from the parent snapshot but does not attempt hidden prose/state transplant.
- Writer fork-group assembly remains planned, not implemented.

## Tests
- Covered by `tests/test_branch_execution.py`:
  - nested scene branch promotes into chapter parent without touching `main`
  - rebase creates a refreshed child from the updated parent and marks the old branch discarded
