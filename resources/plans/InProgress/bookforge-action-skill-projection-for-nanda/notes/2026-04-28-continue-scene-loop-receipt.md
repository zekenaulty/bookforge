# 2026-04-28 Continue Scene Loop Receipt

BookForge tightened `continue_scene` for Nanda `AuthorWorkLoop`.

Behavior remains unchanged:

- `continue_scene` executes exactly one child action.
- It uses `ScenePhaseReadiness.recommended_next_action`.
- It does not loop internally.
- It does not choose a different child action.

Receipt additions:

- `pre_readiness_ref`
- `post_readiness_ref`
- `recommended_next_action`
- `stop_reason`
- `produced_artifact_refs`
- explicit `canonical_changed`

Stop reason semantics:

- `null`: the parent loop may schedule another step if its own envelope allows it.
- `no_legal_action`: no ready recommended child action exists.
- `provider_failed`: the child action paused or failed due to provider exhaustion.
- `branch_stale`: the child action reports stale branch/write context.
- `tool_unavailable`: the child action hard-failed or degraded integrity.
- `completed_scope`: no next scene-phase action remains after the child action.

Why this matters:

- Nanda can run a parent `AuthorWorkLoop` without parsing prose or raw logs.
- A cancelled/interrupted loop can preserve branch artifacts and resume from a
  fresh readiness query.
- The author response can say exactly what happened in the last step and why the
  loop stopped or can continue.

Validation:

- Focused tests cover:
  - successful one-child execution with pre/post readiness refs
  - produced artifact refs copied into the wrapper receipt
  - `stop_reason: null` when another step is ready
  - `stop_reason: no_legal_action` when no ready child exists
