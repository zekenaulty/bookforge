# 2026-04-23 0070 Section Wrapper Tightening

## Summary
- Tightened the section-level macro surface so `write_frozen_section`, `resume_paused_section`, and `advance_section_workflow` no longer depend on `run_loop(...)` as their macro entry point.
- Added a dedicated runner surface, `run_section_range(...)`, for section-scoped traversal over the extracted scene-phase sequence.
- Kept `run_loop(...)` as the batch/operator macro over the same lower-level write path instead of letting section wrappers parameterize the batch surface directly.

## Why
- `run_loop(...)` is the right batch/operator entry point, but it was still acting as the only macro-level path for section work.
- That kept section wrappers one level too indirect for truthful supervision and future skill extraction.
- The section wrappers needed a dedicated section-scoped macro so Nanda and later MCP-style capability extraction can treat section execution as a real skill boundary instead of “call the batch thing with the right arguments.”

## Changes
- `src/bookforge/runner.py`
  - split the old public runner body into `_run_write_scope(...)`
  - added `_set_cursor_for_scene_range(...)`
  - added `run_section_range(...)` for section-scoped traversal
  - kept `run_loop(...)` as a thin public wrapper over `_run_write_scope(...)`
- `src/bookforge/execution/scoped.py`
  - `write_frozen_section(...)` now calls `run_section_range(...)`
  - `resume_paused_section(...)` now calls `run_section_range(...)`
- `src/bookforge/section_workflow.py`
  - `advance_section_workflow(...)` now calls `run_section_range(...)`
  - removed the local cursor-reset helper that duplicated runner logic
- `tests/test_execution_actions.py`
  - updated the write-section adapter test to patch `run_section_range(...)`
- `tests/test_scoped_execution.py`
  - updated paused-resume tests to patch `run_section_range(...)`

## Validation
- `python -m pytest tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_targeting.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_section_range`
  - `20 passed`
- `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_targeting.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_section_range_full`
  - `78 passed`
- `python -m pytest tests/test_scope_contracts.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_query_workspace.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_section_range_regression`
  - `28 passed`

## Result
- Section-scoped commands now have their own truthful macro executor.
- Batch `run` and section-scoped execution still share the same lower-level extracted scene-phase path.
- The dependency direction is cleaner:
  - scene actions are the atomic truth
  - section-range execution is the section macro
  - `run_loop(...)` is the batch/operator macro
