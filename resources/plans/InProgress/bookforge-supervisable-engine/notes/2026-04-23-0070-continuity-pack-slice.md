# 0070 Continuity-Pack Slice Execution Note

Date
- 2026-04-23

Scope
- Continue story `0070-segment-section-write-into-scoped-scene-actions`.
- Extract `generate_continuity_pack` as a truthful scene-phase action between `preflight_scene_state` and `write_scene_prose`.
- Correct the next extraction order after tracing `run_loop`: existing pipeline truth is `write -> state_repair -> lint -> repair`, so `state_repair_scene_patch` lands before `lint_scene_prose`.

Changes
- Added the continuity-pack execution action surface:
  - `build_generate_continuity_pack_request(...)`
  - `generate_continuity_pack(...)`
- Exposed the action through:
  - `bookforge.execution`
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - `bookforge workflow generate-continuity-pack`
- Kept the action narrow:
  - requires active cursor scene on `main`
  - requires existing `scene_card` and `preflight_patch`
  - produces only a `derived` continuity-pack receipt
  - does not generate prose
  - does not lint
  - does not repair
  - does not commit
  - does not mutate canonical `state.json`
- Added a materialization guard:
  - safe preflight summary changes are applied only to an in-memory working state
  - provisional character, continuity-system, or durable mutations are refused until a truthful materialization surface exists
- Updated operator docs:
  - `docs/help/workflow.md`
  - `docs/help/index.md`
  - `docs/help/run.md`
- Updated plan traceability for the landed continuity-pack guardrails.
- Added the state-repair execution action surface:
  - `build_state_repair_scene_patch_request(...)`
  - `state_repair_scene_patch(...)`
- Exposed the state-repair action through:
  - `bookforge.execution`
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - `bookforge workflow state-repair-scene-patch`
- Kept the state-repair action narrow:
  - requires active cursor scene on `main`
  - requires existing `scene_card`, `preflight_patch`, `continuity_pack`, `write_prose`, and `write_patch`
  - produces only a `provisional` corrected state patch
  - does not apply the corrected patch to canonical state
  - does not lint
  - does not repair prose
  - does not commit
- Added the lint execution action surface:
  - `build_lint_scene_prose_request(...)`
  - `lint_scene_prose(...)`
- Exposed the lint action through:
  - `bookforge.execution`
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - `bookforge workflow lint-scene-prose`
- Kept the lint action narrow:
  - requires active cursor scene on `main`
  - requires existing `scene_card`, `preflight_patch`, `continuity_pack`, `write_prose`, and `state_repair_patch`
  - produces only a `provisional` lint report
  - does not repair prose
  - does not rerun state repair
  - does not commit

Validation
- Ran:
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py tests/test_scoped_execution.py -q`
  - `python -m pytest tests/test_execution_actions.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q`
  - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py tests/test_scoped_execution.py -q`
  - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py tests/test_scoped_execution.py -q`
  - `python -m pytest tests/test_execution_actions.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q`
  - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
- Result:
  - `31 passed`
  - `38 passed`
  - `28 passed`
  - `41 passed`
  - `39 passed`
  - `43 passed`
  - `46 passed`
  - `44 passed`
  - `48 passed`
  - `28 passed`
  - `51 passed`

Notes
- The scene-phase traversal path now has six extracted actions:
  - `plan_scene`
  - `preflight_scene_state`
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
- The next 0070 slice should continue the post-write path:
  - `repair_scene_prose`
  - then apply/commit once lint/repair receipts are stable
- Appearance and setting extraction remain intentionally deferred to `0075`.
