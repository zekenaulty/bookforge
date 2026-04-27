# 2026-04-27 0081 Blast-Radius Scope Groups

## Summary
- Extended `get_recovery_blast_radius(...)` with an explicit `scope_groups` block.
- The surface now separates:
  - `affected`
  - `downstream`
  - `prose_invalidation_scope`
  - `state_rebuild_scope`
  - `downstream_trace_status`
  - `downstream_trace_note`

## Boundary
- Downstream grouping is currently manifest-declared only.
- This does not perform semantic dependency tracing after redraft.
- The status field deliberately reports `manifest_declared_only` when downstream scopes are present so Nanda does not treat the grouping as proof of full dependency analysis.

## Why
- Nanda needs to plan recovery actions against different scopes:
  - prose invalidation/redraft normally targets directly affected scopes
  - state rebuild must consider directly affected and declared downstream scopes
  - downstream author review may remain necessary even when mutation support is narrow

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0081_blast_radius_scope_focus`
  - Result: `4 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_blast_radius_scope_full`
  - Result: `308 passed`
