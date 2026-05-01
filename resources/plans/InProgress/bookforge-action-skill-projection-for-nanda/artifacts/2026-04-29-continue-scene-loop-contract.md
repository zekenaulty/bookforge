# Continue Scene Loop Contract Confirmation

Date: 2026-04-29

Slice: `continue_scene` / `AuthorWorkLoop` contract support

Owner: BookForge engine workstream

## Contract Status

BookForge considers `continue_scene` stable enough for Nanda's first supervised `AuthorWorkLoop`.

The action is intentionally narrow:

- executes exactly one child scene-phase action
- chooses only `ScenePhaseReadiness.recommended_next_action`
- does not loop internally
- does not pick an alternate action
- returns a wrapper `ExecutionResult`
- includes nested `author_loop_step_receipt_v1`
- can run on `main` or a derived branch, but Nanda should use it branch-local for live authoring

## Public Keys

- Static capability id: `action.continue_scene`
- Legal/action key: `continue_scene`
- Request builder: `bookforge.execution.build_continue_scene_request(...)`
- Executor: `bookforge.execution.continue_scene(...)`
- CLI: `bookforge workflow continue-scene`
- Readiness input: `bookforge.query.get_scene_phase_readiness(...)`
- Writing cursor query: `bookforge.query.get_next_writing_target(...)`
- Writing gate query: `bookforge.query.get_writing_gate_status(...)`
- Loop envelope query: `bookforge.query.get_author_loop_envelopes(...)`

## Request Selector

Required:

- `book_id`
- `chapter`
- `scene`

Optional:

- `section`
- `branch_id`

Rules:

- A current execution node must exist for the selected branch.
- The selected scene must have a ready `recommended_next_action` unless the caller wants a `no_op` wrapper with `stop_reason=no_legal_action`.

## Wrapper Result Fields

`continue_scene` returns `ExecutionResult` with:

- `action=continue_scene`
- `status=<child status or no_op>`
- `artifact_paths=<child artifact paths>`
- `produced_artifacts=<child produced artifacts>`
- `details.macro_kind=single_recommended_scene_phase_step`
- `details.child_action`
- `details.child_status`
- `details.pre_readiness_ref`
- `details.post_readiness_ref`
- `details.before_scene_status`
- `details.before_recommended_next_action`
- `details.after_scene_status`
- `details.after_recommended_next_action`
- `details.recommended_next_action`
- `details.stop_reason`
- `details.branch_id`
- `details.child_mutation_scope`
- `details.canonical_changed`
- `details.child_result_id`
- `details.child_request_id`
- `details.produced_artifact_refs`
- `details.author_loop_step_receipt`

## Nested `author_loop_step_receipt_v1`

Shape:

- `schema_version=author_loop_step_receipt_v1`
- `step_index=1`
- `pre_readiness_ref`
- `post_readiness_ref`
- `action_run`
- `child_result_ref`
- `child_request_ref`
- `child_status`
- `produced_artifact_refs`
- `canonical_changed`
- `next_recommended_action`
- `stop_reason`

Nanda should prefer this nested receipt over reconstructing the loop step from loose wrapper fields.

## Readiness Ref Shape

`pre_readiness_ref` and `post_readiness_ref` include:

- `schema_version=scene_phase_readiness_ref_v1`
- `scene_status`
- `recommended_next_action`
- `ready_actions`
- `node_revision_id`
- `node_branch_id`
- `updated_at`

These are compact references for loop orchestration. They are not full readiness payloads. If Nanda needs full readiness, it should re-query `get_scene_phase_readiness(...)`.

## Stop Reason Mapping

`details.stop_reason` and `author_loop_step_receipt.stop_reason` are:

- `null`
  - child action succeeded or no terminal block exists and another recommended action is ready
- `no_legal_action`
  - no ready recommended child action existed before execution
- `provider_failed`
  - child action returned `status=retryable_pause`
- `branch_stale`
  - child action reports `failure_code=stale_write`, `stale_parent`, or `branch_stale`
- `tool_unavailable`
  - child action returned `status=hard_fail` or `integrity_degraded`
- `completed_scope`
  - child action returned and post-readiness has no next recommended scene-phase action

Nanda-owned loop stop reasons such as `user_cancel_requested`, `budget_exhausted`, `canonical_approval_required`, and `book_complete` remain parent-loop policy states. BookForge does not emit those from one `continue_scene` call unless/until a concrete engine condition maps to them.

## Canonical Change Semantics

`details.canonical_changed` is explicit.

For Nanda branch-live authoring:

- require `branch_id != main`
- expect `canonical_changed=false`
- treat any `canonical_changed=true` as a hard policy violation for branch-live mode

For main-branch execution:

- `canonical_changed` can be true only when the child action reports canonical change semantics.
- Nanda should avoid live authoring on `main` unless a future canonical-gated path explicitly approves it.

## Nanda Gating Recommendation

Nanda should expose `continue_scene` / `AuthorWorkLoop` only when:

1. selected scope includes book, non-main branch, chapter, and scene
2. branch detail/legal actions show `continue_scene.allowed=true`
3. scene readiness recommends a ready child action
4. route/scope projection is branch-live
5. loop envelope limits are present
6. mode policy refuses canonical mutation

Parent loop should re-query before each child step:

- branch detail
- legal actions
- scene readiness
- next writing target or writing gates as needed

## Validation

Focused BookForge validation:

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

Covered:

- one-child execution wrapper
- nested `author_loop_step_receipt_v1`
- produced artifact refs
- `stop_reason=null`
- `stop_reason=no_legal_action`
- `stop_reason=provider_failed`
- `stop_reason=branch_stale`
- `stop_reason=tool_unavailable`
- `stop_reason=completed_scope`

Broader related validation:

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
