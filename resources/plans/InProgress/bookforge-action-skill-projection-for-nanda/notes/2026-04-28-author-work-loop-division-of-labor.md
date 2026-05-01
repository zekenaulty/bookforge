# 2026-04-28 Author Work Loop Division Of Labor

This note coordinates the next parallel slice between BookForge and Nanda after
`continue_scene` became the first adaptive writing macro.

## Shared Objective

Move from one-off supervised scene actions toward an interruptible author work
loop:

1. Nanda observes the selected book, branch, and scope.
2. Nanda asks BookForge for legal actions and readiness.
3. Nanda runs one safe `continue_scene` step.
4. BookForge emits child and wrapper receipts.
5. Nanda refreshes state from receipts and query surfaces.
6. Nanda either stops, asks the user, or schedules the next step.

This is not autonomous book completion yet. It is supervised, resumable graph
traversal where every completed mutation is preserved on the target branch and
every next move is based on fresh BookForge evidence.

## BookForge Track

BookForge owns engine truth, mutation safety, receipts, and queryable state.

Immediate BookForge gaps:

- Add a next-writing-target query.
  - It should answer current scene, next scene, next section, next chapter,
    blocked reason, branch target, and book-complete status.
  - It should not run writing or mutate state.
  - It should be exposed through Python query APIs, CLI JSON, and capability
    projection.
- Add section, chapter, and book readiness gates.
  - Required questions: can this scene advance, can this section lock, can this
    chapter finalize, can this book continue, can this manuscript export.
  - Gates should report missing prerequisites, blocking tickets, stale branch or
    lineage issues, and recommended next action.
- Audit and harden branch-local commit/finalize semantics.
  - `apply_scene_commit` must be visibly branch-local when run on a derived
    branch.
  - Receipts must say whether canonical state changed. For branch-local work,
    that value must be false.
  - Nanda should not expose commit/finalize as live until this receipt contract
    is clear enough to render safely.
- Keep `continue_scene` receipts loop-friendly.
  - Wrapper receipts should include child action, child result id, before and
    after readiness, produced artifacts, mutation scope, branch id,
    canonical-changed flag, recommended next action, and stop reason when
    applicable.
- Add cooperative macro boundaries where possible.
  - BookForge does not need to cancel an in-flight provider call in the first
    slice.
  - It must avoid hidden long loops in adaptive macros. One macro call should
    finish one child action and return control.
- Plan later adaptive authoring primitives.
  - Scene insertion for pacing and missing connective tissue.
  - Pairwise seam alignment for scene A to scene B transitions.
  - Stable selected-prose anchors before "fix this passage" becomes a mutation
    target.

Suggested BookForge implementation order:

1. `get_next_writing_target(...)`
2. `get_writing_gate_status(...)` or equivalent section/chapter/book gate query
3. capability projection entries for those queries/readiness surfaces
4. branch-local `apply_scene_commit` receipt audit and tests
5. follow-on scene insertion and seam alignment planning

## Nanda Track

Nanda owns intent interpretation, loop policy, UI status, user interruption,
approval flow, and author response.

Pinned Nanda contracts:

- `AuthorWorkLoopEnvelope`
  - `book_id`
  - `branch_id`
  - target `chapter`, `section`, `scene`
  - objective
  - mode policy
  - max steps
  - max duration
  - max spend
  - allowed actions
  - stop conditions
  - user turn id
- `AuthorLoopStepReceipt`
  - step index
  - pre-readiness ref
  - action run
  - child receipt ref
  - produced artifact refs
  - post-readiness ref
  - canonical changed flag
  - next recommended action
  - stop reason
- `AuthorLoopStopReceipt`
  - status
  - reason
  - branch preserved flag
  - last completed action
  - last receipt id
  - canonical changed flag
  - resume strategy
- Stop reason enum:
  - `completed_scope`
  - `user_cancel_requested`
  - `needs_user_choice`
  - `no_legal_action`
  - `budget_exhausted`
  - `provider_failed`
  - `branch_stale`
  - `canonical_approval_required`
  - `book_complete`
  - `tool_unavailable`
- Resume contract:
  - Resume always starts with fresh branch detail, readiness, legal-action,
    reader, and receipt queries.
  - User comments during pause must be interpreted before resume. They may
    change the next action.

Immediate Nanda gaps:

- Add an `AuthorWorkLoop` job around `continue_scene`.
  - The loop runs one `continue_scene`, records its receipt, refreshes state,
    checks stop conditions, then decides whether to schedule another step.
  - It should support envelopes such as continue one step, continue this scene,
    continue this section, with max step, time, spend, and stop-condition limits.
- Add interruption semantics.
  - `cancel_requested` stops scheduling new actions.
  - The currently running BookForge action may finish; no next action starts.
  - Completed branch artifacts and receipts are preserved.
  - The loop emits its own receipt with last completed action, last receipt id,
    canonical-changed flag, stop reason, and resume strategy.
- Add resume semantics.
  - Resume must re-query branch detail, scene readiness, legal actions, reader
    state, and prior receipts.
  - Resume must not trust chat memory as execution truth.
- Make `continue_scene` primary in the branch workbench.
  - It should be the obvious "continue one recommended step" button.
  - Primitive scene-phase actions remain available for explicit author choice.
- Render loop status cards.
  - Current scope, branch id, running action, last completed action, next legal
    action, canonical-changed flag, stop reason, and receipt refs.
- Add loop tests.
  - One-step happy path through the job runner.
  - Cancel before first action.
  - Cancel while an action is running.
  - Resume after interruption from fresh queries.
  - Stop on no legal next action, user-choice-required, budget exhausted,
    provider failure, stale branch, and book complete.

Nanda definition of done:

- A user can start "continue one step" on a non-main branch.
- A user can start "continue this scene" with max steps and duration limits.
- The loop emits visible job events for each query, action, receipt, and stop.
- Cancel prevents any new step from being scheduled.
- If a child action is already running, it may finish, then the loop stops.
- Completed branch artifacts are preserved.
- Resume re-queries BookForge before acting.
- UI shows branch, target, running action, last receipt, stop reason,
  `canonical_changed=false`, and next action.
- Tests cover happy path, cancel before start, cancel mid-action, resume, no
  legal action, budget stop, provider failure, stale branch, and book complete.

Nanda implementation constraints:

- `write_frozen_section` must not become the v1 loop primitive. It is too broad.
  Use `continue_scene`.
- Avoid parent jobs that hold broad branch locks while child jobs need the same
  locks. Either the parent executes each `continue_scene` step under one lock, or
  children own locks and the parent remains lock-light.
- The loop needs `interrupted` or `paused` state. Plain `cancelled` implies the
  work was discarded, which is false for preserved branch artifacts.

## Shared Invariants

- Cancel the loop, not the branch.
- Do not roll back completed branch work by default.
- A branch is the durable work surface; a loop is resumable orchestration state.
- No hidden canonical mutation is allowed in branch-local writing.
- Nanda must re-query BookForge evidence before resume.
- The author voice may say "done" only when an execution receipt proves the
  action completed.
- Static capability, dynamic readiness, execution receipt, and user-facing UI
  state must stay separate.
- Book completion must come from a BookForge gate, not cursor inference.
- `apply_scene_commit` remains hidden or caution-gated until BookForge proves
  branch-local/canonical semantics in receipts.

## BookForge Definition Of Done

- `continue_scene` receipt includes child action, before/after readiness,
  produced artifacts, branch id, canonical-changed flag, recommended next action,
  and stop reason when applicable.
- `get_next_writing_target(...)` exists and is query-only.
- A writing gate query exists for scene, section, chapter, and book
  continuation.
- Capability projection exposes the next-writing-target and writing-gate query
  surfaces.
- `apply_scene_commit` branch-local semantics are audited before Nanda exposes
  it as a live commit action.
- Tests prove branch-local writing never mutates canonical main.

## Parallelization Boundary

Nanda can begin `AuthorWorkLoop` now using the existing `continue_scene` action.
BookForge does not need to block that first loop, because `continue_scene`
already returns control after one child action.

BookForge should build the next-writing-target and writing-gate queries in
parallel. Those surfaces make Nanda's loop smarter, but the first supervised
loop can use existing legal actions and scene readiness until the richer gates
land.

## Open Risks

- Branch-local commit/finalize must not be presented as canonical promotion.
- Provider calls may still run long; first-slice cancellation is cooperative at
  action boundaries, not inside a provider request.
- Book-complete status needs a clear gate so loops stop cleanly instead of
  cycling on missing next targets.
- Scene insertion and seam alignment are real future needs, but should not block
  the first `AuthorWorkLoop`.
