# Slice Note: Continue Scene Loop Contract Hardening

Date: 2026-04-29

Repo: BookForge / `ai-book`

Owner: BookForge engine workstream

## Slice

Harden and document the BookForge side of the `continue_scene` loop contract so Nanda can safely build route/scope projection and `AuthorWorkLoop` behavior without inferring stop reasons or receipt fields.

## Changed

- Added focused tests for loop stop-reason mapping:
  - `provider_failed`
  - `branch_stale`
  - `tool_unavailable`
  - `completed_scope`
- Added a Nanda-facing contract artifact for:
  - wrapper result fields
  - nested `author_loop_step_receipt_v1`
  - readiness refs
  - stop reason mapping
  - canonical-change semantics
  - Nanda gating recommendation

## Files Touched

- `tests/test_scene_action_execution.py`
- `resources/plans/InProgress/bookforge-action-skill-projection-for-nanda/artifacts/2026-04-29-continue-scene-loop-contract.md`
- `resources/plans/InProgress/bookforge-action-skill-projection-for-nanda/plan.md`

## Contract Notes

Confirmed:

- `continue_scene` executes exactly one child action.
- It uses only `ScenePhaseReadiness.recommended_next_action`.
- It emits nested `author_loop_step_receipt_v1`.
- Nanda should prefer the nested receipt over reconstructing from loose wrapper fields.
- Parent-loop states such as `user_cancel_requested`, `budget_exhausted`, `canonical_approval_required`, and `book_complete` remain Nanda policy states unless a future BookForge engine condition maps to them.

## Validation

Focused:

```powershell
python -m pytest `
  tests/test_scene_action_execution.py::test_continue_scene_executes_one_recommended_child_and_records_wrapper `
  tests/test_scene_action_execution.py::test_continue_scene_no_ready_child_reports_no_legal_action_stop_reason `
  tests/test_scene_action_execution.py::test_continue_scene_maps_child_outcome_to_loop_stop_reason `
  -q
```

Result:

```text
7 passed in 2.90s
```

Broader related:

```powershell
python -m pytest `
  tests/test_scene_action_execution.py::test_continue_scene_executes_one_recommended_child_and_records_wrapper `
  tests/test_scene_action_execution.py::test_continue_scene_no_ready_child_reports_no_legal_action_stop_reason `
  tests/test_scene_action_execution.py::test_continue_scene_maps_child_outcome_to_loop_stop_reason `
  tests/test_writing_target.py `
  tests/test_capability_projection.py `
  -q
```

Result:

```text
21 passed in 4.75s
```

Note:

- A first attempt ran two pytest commands in parallel and collided on shared `.pytest_tmp` cleanup on Windows. The suites were rerun sequentially and passed.

## Nanda Reaction Needed

Use `author_loop_step_receipt_v1` as the stable child-step receipt for `AuthorWorkLoop`.

Nanda should:

- map BookForge stop reasons directly:
  - `no_legal_action`
  - `provider_failed`
  - `branch_stale`
  - `tool_unavailable`
  - `completed_scope`
- keep user/budget/canonical approval stops as parent-loop policy states
- re-query branch detail/readiness/legal actions between loop steps
- treat `canonical_changed=true` as invalid for branch-live loops

