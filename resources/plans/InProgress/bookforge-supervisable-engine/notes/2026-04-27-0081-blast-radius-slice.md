# 2026-04-27 0081 Recovery Blast Radius Slice

## Summary
- Added `get_recovery_blast_radius(...)` as an impact-report-friendly recovery query surface.
- Added CLI support via `bookforge workflow recovery-blast-radius`.
- The surface combines existing branch-local invalidation previews into categorized artifact families:
  - prose
  - state
  - continuity
  - projection
  - series

## Contract Notes
- The surface is read-only and intended to run before destructive recovery actions.
- Prose impacts map to `invalidate_scope_outputs`.
- State, continuity, and projection impacts map to `rebuild_state_scope`.
- Series impacts are diagnostic-only in this slice because series canon is outside the current recovery branch mutation set.
- Every impact row declares:
  - artifact family
  - path
  - artifact status
  - whether the artifact exists
  - whether it is safe as canonical
  - recommended action
  - whether BookForge currently supports mutation for that family

## Files Touched
- `src/bookforge/query/recovery.py`
- `src/bookforge/query/__init__.py`
- `src/bookforge/cli.py`
- `tests/test_recovery_actions.py`
- `docs/help/index.md`
- `docs/help/workflow.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_blast_radius_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_blast_radius_full`
  - Result: `308 passed`

## Next
- Add downstream dependency tracing after redraft.
- Add promotion-result canonical integrity deltas.
- Expand validation from outline lineage into state/projection family health.
