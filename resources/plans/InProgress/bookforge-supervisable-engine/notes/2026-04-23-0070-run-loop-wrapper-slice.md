# 2026-04-23 0070 Run-Loop Wrapper Slice

## Summary
- Routed `run_loop` scene execution through the extracted scene-phase action surface instead of keeping a second monolithic per-scene implementation in `runner.py`.
- Kept the existing outer writer behavior intact:
  - outline gate
  - character/style-anchor bootstrap
  - progress heartbeat
  - pause marker / pause contract
  - section-level wrappers at the time of this slice still called `run_loop`
- Added a small scene-sequence adapter so the runner can execute:
  - `plan_scene`
  - `preflight_scene_state`
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `apply_scene_commit`

## Why
- `0070` is no longer just about exposing narrow scene-phase actions individually.
- The batch writer path also needed to stop being a separate source of truth.
- If `run_loop` kept its own internal choreography, Nanda would still be supervising one graph while production writing used another.

## Key Changes
- Added `src/bookforge/execution/scene_sequence.py`.
  - builds live scene-phase requests against the current main-branch node
  - allows the runner to pass durable-slice expansion hints into extracted actions
- Updated `src/bookforge/execution/scene_actions.py`.
  - scene-phase request builders now resolve the live node with `prefer_emitted=False`
  - extracted phase actions now accept `durable_expand_ids` through request details and pass them to the underlying phase implementations
- Updated `src/bookforge/runner.py`.
  - added a runner-local scene-sequence driver
  - translated scene-phase `retryable_pause` results back into `draft/context/run_paused.json`
  - preserved the existing strict-mode lint failure / durable-slice pause behavior
  - kept appearance refresh after scene-card resolution before prose generation

## Validation
- `python -m pytest tests/test_runner_targeting.py tests/test_scene_action_execution.py tests/test_scene_phase_readiness.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_runner_wrap`
- `python -m pytest tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_0070_runner_wrap_scoped`
- `python -m pytest tests/test_scope_contracts.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_query_workspace.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_runner_wrap_regression`
- `python -m pytest tests/test_runner_targeting.py tests/test_runner_outline_gate.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_execution_actions.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_runner_wrap_full`

## Remaining Edge
- At the time this slice landed, `run_loop` delegated per-scene work truthfully, but the section-level wrappers still depended on `run_loop` as the macro entry point rather than owning their own scene traversal.
- That gap was closed later the same day in `2026-04-23-0070-section-wrapper-tightening.md` by introducing `run_section_range(...)` for section-scoped traversal.
