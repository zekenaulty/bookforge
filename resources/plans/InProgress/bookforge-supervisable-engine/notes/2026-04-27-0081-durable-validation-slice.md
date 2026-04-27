# 2026-04-27 0081 Durable Validation Slice

## Summary
- Added recovery-branch validation for durable inventory and plot-device state before promotion.
- `validate_recovery_branch` now scans branch-local durable artifacts under `draft/context`:
  - `item_registry.json`
  - `items/index.json`
  - `plot_devices.json`
  - `plot_devices/index.json`
  - `durable_commits.json`
  - item and plot-device history JSON files
- The validator blocks promotion when these artifacts retain:
  - character references that are absent from the normalized branch outline
  - stale embedded `node.branch_id` or `selector.branch_id` values
  - item/device index entries missing from their registries
  - stale `THREAD_*` references when the normalized outline exposes a thread ID set

## Boundary
- This is deterministic structural validation, not semantic inventory reasoning.
- It catches obvious stale timeline data such as ghost custodians, stale branch coordinates, and broken registry/index agreement.
- It does not yet infer whether an item, device, or inventory fact is narratively correct after a redraft.

## Why
- Timeline recovery cannot clear `chimera_risk` safely if branch-local durable state still contains ghost timeline entities.
- Nanda needs BookForge to surface these blockers as receipts and validation details, not require raw filesystem archaeology.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_durable_validation_focus2`
  - Result: `35 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_durable_validation_full`
  - Result: `308 passed`
