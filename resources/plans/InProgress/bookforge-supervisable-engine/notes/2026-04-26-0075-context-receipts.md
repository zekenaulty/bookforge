# 2026-04-26 0075 Scene Context Receipt Slice

## Completed
- Added `scene_context_projection` snapshots to scene-phase execution receipts.
- Covered:
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `apply_scene_commit`
- The receipt snapshot aggregates:
  - appearance projection status and source artifacts
  - scene setting status, source mode, and source artifacts
  - selected prior T1 thought signatures and limitations

## Truth Boundary
- `scene_context_projection.used_as_prompt_input` is currently `false`.
- The receipt is an observation surface, not proof that the author prompt consumed the projection payload.
- A future prompt-injection slice must only flip this field when the projection payload is actually assembled into the model request.
- Thought signatures remain context aids; execution receipts remain the truth of what happened.

## Validation
- Focused test:
  - `tests/test_scene_action_execution.py::test_write_scene_prose_generates_provisional_receipts`
- 0075 focused regression:
  - `tests/test_scene_action_execution.py`
  - `tests/test_scene_context_query.py`
  - `tests/test_scene_setting_actions.py`
  - `tests/test_appearance_projection_action.py`
  - `tests/test_appearance_query.py`
  - `tests/test_scene_setting_query.py`
  - `tests/test_thought_context_query.py`
- Result: `35 passed`.

## Remaining 0075 Work
- Decide whether prompt assembly should consume scene context projections directly in BookForge or whether Nanda should choose and pass them as explicit action inputs.
- Audit legacy character appearance mutation/refresh paths against the projection contract.
