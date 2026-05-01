# Controlled Heartbeat Smoke

Date: 2026-04-29
Source: BookForge agent

## Purpose

Validate the first branch-local authoring heartbeat on a disposable healthy target instead of using contaminated `veiled_ledger_b1`.

This smoke verifies the narrow operating loop:

```text
healthy book
  -> derived branch
  -> scene scope
  -> continue_scene
  -> one child action
  -> branch-local artifact mutation
  -> canonical main unchanged
  -> receipt-backed stop/resume state
```

## Smoke Target

- Book: `heartbeat_smoke_b1`
- Branch: `heartbeat-ch1-sc1-stop`
- Scope: chapter 1, section 1, scene 1
- Action: `continue_scene`
- Child action executed: `apply_scene_commit`

The branch was seeded with a complete passing provisional scene baseline so the smoke did not require a provider call.

## Result

Observed result:

```json
{
  "result_status": "success",
  "child_action": "apply_scene_commit",
  "canonical_changed": false,
  "stop_reason": "completed_scope",
  "receipt_stop_reason": "completed_scope",
  "receipt_next_recommended_action": null,
  "after_status": "committed",
  "main_scene_exists": false,
  "branch_scene_exists": true,
  "next_target_status": "blocked",
  "next_target_recommended_action": "lock_section_from_written_state"
}
```

Produced branch-local artifacts included:

- `state`
- `scene_prose`
- `scene_meta`
- `last_excerpt`
- `chapter_summary`
- `chapter_markdown`

## Bug Found And Fixed

The first smoke revealed a loop-contract bug:

- branch-committed scenes are intentionally replaceable on a derived branch
- scene-phase readiness therefore still reported an available follow-up action after commit
- `continue_scene` originally interpreted that as `stop_reason: null`
- this could cause a parent `AuthorWorkLoop` to keep scheduling `continue_scene` against a completed scene instead of re-querying the next writing target

Fix:

- `continue_scene` now reports `stop_reason="completed_scope"` whenever the child action is a successful `apply_scene_commit`
- the author-loop step receipt clears `next_recommended_action` when a stop reason exists
- parent loops should then re-query `get_next_writing_target(...)`

Regression added:

```text
tests/test_scene_action_execution.py::test_continue_scene_branch_local_commit_reports_completed_scope
```

Validation:

```text
python -m pytest tests/test_scene_action_execution.py::test_continue_scene_branch_local_commit_reports_completed_scope tests/test_scene_action_execution.py::test_continue_scene_branch_local_heartbeat_preserves_main_and_exposes_artifacts -q
2 passed
```

## Nanda Guidance

For the parent `AuthorWorkLoop`:

- treat `completed_scope` as a hard stop for the current child loop step
- preserve branch artifacts
- re-query branch detail, reader/artifacts/diff, legal actions, and `get_next_writing_target(...)`
- offer the next higher-level action, such as `lock_section_from_written_state`, only if legal/readiness evidence allows it

Do not infer loop continuation from scene-phase readiness alone after a commit. Use the writing-target/gate surfaces after each completed scope.
