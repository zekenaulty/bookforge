# Gap Closure Refinement Plan

Date: 2026-04-29

## Purpose

This refinement turns the snapshot xref punch list into a dependency-ordered closure plan.

The working conclusion is:

> The kernel is strong enough for controlled branch-local authoring. The next danger is split truth between BookForge, Nanda backend, Nanda UI, and author chat.

Do not add more general capability surface before the P0 control path is closed. The near-term product milestone is one trustworthy path:

```
selected scope
  -> BookForge capability descriptor
  -> BookForge legal/readiness evidence
  -> Nanda bridge/mode/approval overlay
  -> UI action card / author action grammar
  -> execution
  -> receipt/artifacts
  -> refreshed state
```

## Source Authority

The April 29 BookForge xref is the current working punch list where it differs from the April 28 Nanda report. It is not a blind independent audit because it consumed the Nanda-side xref artifact, but it is the sharper reconciliation artifact.

Current interpretation:

- April 28 Nanda report: good initial snapshot xref.
- April 29 BookForge report: second-pass reconciliation, more current for BookForge code/plan reality.
- Both agree on the same P0 shape.
- Neither report claims full autonomous book completion is ready.

## Closure Track A: Split-Truth And Capability Drift

Priority: `P0`

Goal:

Nanda should have exactly one backend truth surface for "what can the user/author do at this selected route/scope right now?"

This track closes the highest-risk class of bug: UI or author chat claiming an action is executable because one local list says so while BookForge readiness, bridge availability, approval state, or scope policy says otherwise.

### A1. Reconcile `apply_bridge_scene_insertion`

Owner:

- BookForge: confirm and document upstream semantics.
- Nanda: either wire or explicitly withhold.

Current state:

- BookForge implements same-section branch-local `apply_bridge_scene_insertion_action(...)`.
- BookForge projects `action.apply_bridge_scene_insertion`.
- Nanda still has code/comments/plans treating apply as a BookForge gap.

Closure decision:

1. If same-section branch-local apply is enough:
   - Nanda wires it as a branch-live action.
   - It remains unavailable for `main`, cross-section pairs, and missing bridge proposals.
2. If not enough:
   - Nanda marks it `implemented_upstream_withheld_in_nanda`.
   - The UI shows the real reason: missing Nanda bridge, missing validation, or missing cross-section semantics.

BookForge checks before handoff:

- `apply_bridge_scene_insertion` refuses `main`.
- Requires an existing bridge proposal.
- Requires adjacent same-section pair.
- Validates live node/expected node.
- Mutates only derived branch artifacts.
- Emits `canonical_changed=false`.
- Emits inserted scene id, shifted artifacts, outline/registry refs, and recommended next actions.
- Capability projection includes branch policy, mutation class, expected receipt, and refusal semantics.

Likely BookForge files:

- `src/bookforge/execution/adaptive_authoring.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/capabilities.py`
- `tests/test_adaptive_authoring_actions.py`
- `docs/help/workflow.md`
- `docs/help/capabilities.md`

Likely Nanda files:

- `src/nanda/bridge/bookforge/bookforge_ops.py`
- `src/nanda/jobs/bookforge_actions.py`
- `src/nanda/api/routes/ops.py`
- `src/nanda/api/routes/author.py`
- Branch Workbench UI components
- Author action grammar/commit gate tests

Definition of done:

- Nanda no longer says BookForge lacks the action.
- The action is either enabled only when all gates pass or explicitly shown as withheld.
- A same-section apply success shows a receipt/artifact card.
- `main` refusal, missing proposal refusal, and stale-node refusal are tested.

### A2. Build Backend Route/Scope Capability Projection

Owner: Nanda, with BookForge descriptor/readiness support.

Goal:

Replace scattered UI affordances with a backend-computed action-card projection.

Input selectors:

- `route`
- `mode_policy`
- `book_id`
- `author_ref`
- `conversation_id`
- `branch_id`
- `chapter`
- `section`
- `scene`
- optional reader anchor
- approval state

Projection output per action:

- stable capability id
- user-facing label
- raw action/query key
- action group
- capability bucket: available, inspectable, planned, unavailable, needs bridge
- bridge status
- UI exposure status
- legal status and evidence ref
- readiness status and evidence ref
- mode policy: shadow, branch-live, canonical-gated
- branch policy
- mutation class
- approval requirement
- stale/fresh status
- expected receipt type
- expected produced artifact statuses
- blocked/refusal reason
- next action relationship where available
- source evidence refs

BookForge support:

- Keep `get_capability_projection(...)` stable.
- Keep action descriptors current.
- Keep readiness/query outputs typed and serializable.
- Avoid adding descriptors that imply dynamic readiness.

Nanda closure work:

- Add backend route/scope capability service.
- Expose an API route.
- Have Branch Workbench, Recovery Workbench, Visual Workbench, Author Assets, BookIntent, and Author Chat consume it.
- Treat React local lists as degraded display only, never mutation authority.

Definition of done:

- Every enabled action card has backend evidence.
- Any blocked action has a reason the author can repeat safely.
- Static BookForge capability alone never enables a mutation.
- Tests prove disabled backend state cannot become enabled in UI or chat action grammar.

### A3. Replace `NANDA_WIRED_ACTIONS`

Owner: Nanda.

Goal:

Remove the stale hardcoded allowlist as an author capability authority.

Replacement:

`BridgeStatusRegistry`

Generated from:

- BookForge static capability projection.
- Nanda job/action registry.
- direct bridge modules.
- mode/approval policies.
- route/scope capability projection.

Rules:

- If BookForge supports an action but Nanda has no bridge, status is `needs_bridge`.
- If Nanda has a bridge but selected scope fails readiness, status is `blocked`.
- If Nanda intentionally withholds an upstream action, status is `withheld` with reason.
- If an action is Nanda-only orchestration, it declares its BookForge child actions or says it is UI/job-only.

Definition of done:

- `NANDA_WIRED_ACTIONS` is gone or renamed to a non-authoritative compatibility shim.
- Author capability claims use the registry.
- All job actions have bridge-status entries.
- All bridge-status entries map to a BookForge capability, a Nanda-only orchestration action, or an explicit gap.

## Closure Track B: Controlled Heartbeat Validation

Priority: `P0`

Goal:

Prove the first real authoring loop end-to-end before judging broader UX or adding more actions.

Scope:

- branch-local only
- non-main only
- one selected scene
- one `continue_scene` step
- then bounded `AuthorWorkLoop`
- no canonical mutation

Test path:

1. Open/select a known book.
2. Create or select a non-main branch.
3. Select chapter/section/scene.
4. Query branch detail, legal actions, readiness, reader/artifact state.
5. Run `Continue one step`.
6. Verify child receipt, produced artifact refs, stop reason, recommended next action, and `canonical_changed=false`.
7. Run `AuthorWorkLoop` with low max steps.
8. Cancel mid-loop.
9. Verify no next child action starts after cancel.
10. Refresh branch detail, reader, artifact index, diff, seam queue.
11. Resume only after fresh queries.

BookForge responsibilities:

- `continue_scene` remains exactly one child action.
- Nested `author_loop_step_receipt_v1` stays stable.
- Stop codes remain structured.
- `canonical_changed` remains explicit.
- Produced artifacts have refs/status.

Nanda responsibilities:

- Job graph shows each query/action/receipt/stop.
- Final author answer cites what actually ran.
- Cancel preserves completed branch artifacts.
- Resume never uses chat memory as truth.

Definition of done:

- Branch-local artifacts are visible after stop/cancel.
- Canonical `main` remains unchanged.
- The author cannot claim completion without a receipt.
- The UI cannot enable the same action on `main`.

## Closure Track C: AuthorWorkLoop Hardening

Priority: `P1`

Goal:

Move from "first loop can run" to "loop is safe enough for longer supervised sessions."

Work items:

1. Refresh branch detail/readiness/legal actions between child steps.
2. Add explicit resume button that performs fresh queries before scheduling.
3. Add max duration/time-budget UI.
4. Add spend envelope before spend-bearing actions can enter the loop.
5. Add stop-code tests:
   - `no_legal_action`
   - `provider_failed`
   - `branch_stale`
   - `tool_unavailable`
   - `completed_scope`
   - `book_complete`
6. Keep section lock/chapter finalize explicit until user approves a broader envelope.
7. Later: allow envelope-approved traversal into section lock/chapter finalize using writing gates.

BookForge support:

- Keep `get_next_writing_target(...)` and `get_writing_gate_status(...)` stable.
- Add fixture coverage for stop codes as they become stable.
- Keep `lock_section_from_written_state` and `finalize_chapter_from_locked_sections` branch-local where branch id is non-main.

Definition of done:

- The loop never schedules from stale readiness.
- Resume always starts with fresh truth queries.
- Stop reason is always explicit.
- Branch artifacts are preserved across interruption.
- Canonical mutation requires separate approval path.

## Closure Track D: Action Cards, Direct Jobs, And Chat Actions

Priority: `P1`

Goal:

Make every visible action follow the same validation/execution/receipt model whether it starts from a button, form, or chat.

Work items:

1. Action cards consume backend route/scope projection.
2. Direct UI forms create prefilled action plans instead of bypassing the runner.
3. Author chat proposed actions use the same validator.
4. Job/result cards and final responses consume the same outcome capsule.

Actions in scope:

- `continue_scene`
- `author_work_loop`
- section lock
- chapter finalize
- seam alignment
- bridge insertion plan/apply
- recovery actions
- BookIntent draft/approve/create
- author create/refine
- visual prompt plan/generate

Definition of done:

- A button and a chat request for the same action hit the same validation/runner path.
- Approval-required actions cannot execute from either path without approval.
- Receipt cards and final responses agree.
- Internal command names are secondary labels, not the primary UX.

## Closure Track E: Selected-Prose Handoff

Priority: `P1`

Goal:

Let users select text and ask the author to act on it without turning stale/diagnostic text into mutation authority.

Current state:

- BookForge/Nanda reader anchors exist.
- Selected prose can be inspected.
- Mutation-safe handoff is incomplete.

Work items:

1. Create structured selection cards from reader anchors.
2. Include artifact ref, branch id, scope, source hash, selected hash, offsets, artifact status, freshness, and mutation-target status.
3. Pass selection cards into author chat context.
4. Require `valid_as_mutation_target=true` before rewrite/repair/seam actions can use a selection.
5. Allow diagnostic/fallback selections only for discussion, not mutation.

Definition of done:

- The author can say "I can discuss this selection, but I cannot mutate it because it is diagnostic fallback/stale."
- A valid branch-local selection can become a scoped action target.
- Tests cover canonical current, branch current, stale, diagnostic fallback, preview, and no receipt-backed source.

## Closure Track F: Recovery Workbench And Veiled Ledger Repair

Priority: `P1`

Goal:

Make the Veiled Ledger-style repair possible through author reasoning plus BookForge primitives, not a bespoke `fix_veiled_ledger` command.

Correct recovery concept:

- Choose a valid anchor lineage.
- Create recovery branch.
- Quarantine bad artifacts.
- Normalize outline scope.
- Invalidate contaminated prose/state/series/projections.
- Rebuild state/projections from valid lineage.
- Redraft impacted scopes.
- Validate branch health and downstream continuity.
- Promote only after explicit validation/approval.
- Remove/quarantine invalid files so main is clean after promotion.

Nanda should produce:

- `book_timeline_impact_report_v1`
- candidate repair strategies
- recommended execution plan
- human decisions required
- validation gates

BookForge should provide:

- read-only lineage/impact/semantic/downstream query surfaces
- branch-first mutation primitives
- receipts for quarantine/delete/invalidate/rebuild/redraft/validate/promote
- branch diff and artifact indexes
- validation before canonical promotion

Remaining work:

- Recovery branch receipt timeline.
- Idempotency/replay protection for recovery primitives.
- Promotion confirmation with validation-first gate.
- Reader/diff refresh after each step.
- Deletion/removal/quarantine receipts visible in final promotion plan.

Definition of done:

- Nanda can explain the recovery choice and ask for the anchor decision.
- Every mutation runs on a branch first.
- The operator can inspect exactly what changed and what was removed/quarantined.
- Promotion requires validation and approval.
- BookForge no longer reports chimera risk after promotion.

## Closure Track G: Book Start, Author Assets, And Visual First Slice

Priority: `P1/P2`

Goal:

Finish the first product loops that are already partially wired.

### G1. BookIntent / Create Book

Current state:

- BookForge has create-book from approved intent.
- Nanda has job paths.

Remaining:

- Full author-only `ProposedActionPlan` support.
- Smooth transition from author-only ideation to book-scoped conversation.
- Action cards for draft/approve/create.
- Receipt cards showing canonical workspace created and selected.

Definition of done:

- A non-programmer can chat a book seed, approve intent, create a BookForge book, and continue in book scope without manual filesystem operations.

### G2. Author Assets

Current state:

- BookForge has create/refine.
- Nanda has direct paths.

Remaining:

- Author asset scoped chat.
- Richer author profile/voice output.
- Preview/compare.
- Select author version for book.
- Rollback/select prior version.

Definition of done:

- User can create/refine/select an author through Nanda while BookForge owns the author assets and receipts.

### G3. Visual Assets

Current state:

- BookForge has visual descriptors/readiness/prompt-plan/generate.
- OpenAI and Nano Banana are wired.
- Nanda has visual routes/bridges.

Remaining:

- Plan docs should be updated where they still say Nanda routes are missing.
- Automatic workbench refresh after visual jobs.
- Reference image workflow.
- Layer composition/refinement.
- xAI remains descriptor-only until pricing/API verified.

Definition of done:

- User can plan and generate a spend-approved visual asset, inspect the prompt plan and result, and understand it is provisional visual material, not story canon.

## Closure Track H: Successor Plans After Control Path

Priority: `P2`

Do not expand the completed supervisable-engine umbrella. Start or refine successors:

1. `bookforge-manuscript-output-and-reader-quality-gates`
   - compile preview
   - export readiness
   - word count/completeness
   - manuscript quality gates
2. `bookforge-lint-repair-routing`
   - prose-only lane
   - state/continuity lane
   - seam lane
   - full repair fallback
3. `bookforge-outline-contract-hardening`
   - planner propagation
   - location ownership
   - `end_condition`
   - unknown-key routing
   - outline lint P0 checks
4. `bookforge-author-assets-api-v2`
   - preview/compare/select/rollback
   - richer author voice profiles
   - book-level author selection receipts
5. `bookforge-durable-evidence-ledger`
   - pinned for now
   - operation runs, receipts, artifacts, scopes, branches, approvals, citations

## Implementation Order

### Phase 1: Truth Path Closure

1. Reconcile `apply_bridge_scene_insertion`.
2. Build backend route/scope capability projection.
3. Replace `NANDA_WIRED_ACTIONS`.
4. Make action cards consume backend projection.

Exit gate:

- UI/chat cannot enable an action without backend evidence.

### Phase 2: Heartbeat Proof

5. Run controlled branch-local heartbeat smoke test.
6. Fix failures in receipt display, canonical-change status, cancellation, and branch artifact refresh.

Exit gate:

- One branch-local loop can run, stop, cancel, and resume from fresh truth.

### Phase 3: Loop And Workbench Hardening

7. Add loop refresh/resume/stop-code tests.
8. Add explicit resume.
9. Add action-card unification for direct UI/chat.
10. Add selected-prose handoff.
11. Harden recovery stepper and promotion confirmation.

Exit gate:

- The system can safely do supervised multi-step authoring and supervised recovery planning without hidden state assumptions.

### Phase 4: Product Surface Completion

12. Polish BookIntent/create-book transition.
13. Polish author create/refine/select.
14. Close visual first-slice refresh.
15. Start manuscript output and lint/repair routing successor plans.

Exit gate:

- A user can start a book, select/refine an author, branch-write scenes, inspect prose, and see receipts without understanding the internal pipeline.

## Non-Goals For This Refinement

- Full autonomous book completion.
- Unapproved canonical promotion.
- Full MCP server implementation.
- DB migration before heartbeat validation.
- Vector/citation memory before receipt/operation IDs are durable.
- Cross-section bridge insertion before same-section path is validated.

