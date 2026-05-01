# Slice Note: Author Loop Refresh Contract

Date: 2026-04-29

Repo: BookForge / `ai-book`

Owner: BookForge engine workstream

## Slice

Make the BookForge author-loop envelope query explicit about refresh and stop-reason ownership so Nanda can harden `AuthorWorkLoop` without inventing local policy.

## Change

`get_author_loop_envelopes(...)` now includes top-level and per-envelope refresh metadata:

- `refresh_required_between_steps=true`
- `refresh_query_order`
- `cancellation_policy`
- `stop_reason_ownership`
- `child_action_count_per_step=1`

Static capability projection for `query.author_loop_envelopes` now also includes:

- `refresh_required_between_steps=true`
- `refresh_query_order`
- `cancellation_policy`

## Refresh Query Order

BookForge recommends this post-step and resume-before-step order:

1. `branch_detail`
2. `branch_artifact_index`
3. `branch_diff_summary`
4. `book_reader_scene`
5. `next_writing_target`
6. `writing_gate_status`
7. `scene_phase_readiness`
8. `legal_actions`

Nanda can skip expensive display queries when it does not need them, but it should not schedule another mutation from stale readiness.

## Stop Reason Ownership

BookForge child-step stop reasons:

- `no_legal_action`
- `provider_failed`
- `branch_stale`
- `tool_unavailable`
- `completed_scope`

Nanda parent-loop stop reasons:

- `user_cancel_requested`
- `needs_user_choice`
- `budget_exhausted`
- `canonical_approval_required`
- `book_complete`

This keeps `continue_scene` as a one-child-step executor while Nanda owns parent-loop budgets, cancellation, user choices, and canonical approval policy.

## Validation

Focused command:

```powershell
python -m pytest tests/test_adaptive_authoring_actions.py::test_author_loop_envelopes_expose_section_and_chapter_shapes tests/test_capability_projection.py::test_projection_exports_static_action_query_readiness_and_gap_surfaces -q
```

Result:

```text
2 passed
```

## Nanda Consumption Note

The first `AuthorWorkLoop` should use this as the policy source:

- do not rely on chat memory to resume
- do not loop on stale scene readiness
- do not map BookForge `no_legal_action` blindly to failure
- if cancellation is requested, stop scheduling new child actions after the current child yields
- preserve completed branch-local artifacts and receipts
