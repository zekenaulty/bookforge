# 2026-04-26 0081 Implementation Slice

## Implemented
- Added recovery contract objects:
  - `RecoveryAnchor`
  - `RecoveryScope`
  - `RecoveryReceipt`
  - `RecoveryBranchHealth`
- Added read/query recovery surfaces:
  - recovery manifest lookup
  - recovery plan readiness
  - scope invalidation preview
  - salvage candidates
  - recovery branch health
- Added branch-first recovery execution primitives:
  - `create_recovery_branch`
  - `quarantine_artifacts`
  - `normalize_outline_scope`
  - `invalidate_scope_outputs`
  - `validate_recovery_branch`
  - `promote_recovery_branch`
- Added action discovery entries for recovery branches so Nanda can ask what is legal next.
- Added CLI wrappers for recovery query/action primitives.
- Updated promotion lifecycle so recovery branches can carry explicit removal receipts into promotion.
- Recovery branches now copy outline lineage evidence directories into the isolated branch snapshot before mutation:
  - `outline/pipeline_runs`
  - `outline/section_drafts`
- Scope invalidation records pre-normalization scene ranges so polluted extra scene files can be removed even after the branch outline is normalized.
- Added initial Nanda decision-layer metadata:
  - approval-required flags for recovery branch creation, destructive cleanup, invalidation, and promotion
  - recommended next recovery action in readiness/health surfaces
  - explicit shadow/full-execution boundary in the 0081 step doc

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_outline_lineage_audit.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_focus`
  - Result: `41 passed`
- Full regression:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_nanda_delta_full`
  - Result: `308 passed`
- Post-review module split:
  - `recovery_common.py`: 257 lines
  - `recovery_create.py`: 190 lines
  - `recovery_artifacts.py`: 126 lines
  - `recovery_outline.py`: 180 lines
  - `recovery_validation.py`: 109 lines
  - `recovery_actions.py`: 18-line facade

## Remaining Work
- Add `rebuild_state_scope`.
- Add `redraft_scope` as a scope-level orchestration primitive.
- Add postcondition receipts with integrity deltas and next legal action snapshots.
- Add impact-report-friendly blast-radius queries for prose/state/series/continuity/projection invalidation.
- Expand approval-required metadata across broad-scope state rebuild and redraft primitives when they land.
- Expand recovery validation across state/projection families instead of outline lineage only.
- Add larger multi-chapter contamination fixture coverage.
