# BookForge/Nanda Snapshot Xref Punch List

Date: 2026-04-29

## Inputs

- External review text supplied in chat for `bookforge.20260428_222530.md` and `nanda.20260428_222546.md`.
- Current BookForge plan indexes:
  - `resources/plans/InProgress/bookforge-supervisable-engine/steps/index.md`
  - `resources/plans/InProgress/bookforge-action-skill-projection-for-nanda/steps/index.md`
  - `resources/plans/InProgress/bookforge-visual-asset-generation-skills/steps/index.md`
- Current BookForge code under `src/bookforge`, `tests`, and `docs/help`.
- Current Nanda plan/code spot-checks under `C:\Users\Zythis\source\repos\nanda`.
- Nanda-side xref artifact:
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-author-start-authoring\artifacts\2026-04-28-snapshot-xref-punch-list.md`

The two named snapshot files were not present in this repo during this pass, so this report treats the pasted review text and the Nanda-side xref artifact as the external-review source of truth.

## Executive Read

The narrow branch-local authoring heartbeat is ready to test deliberately:

- Select or create a non-main branch.
- Target a chapter/section/scene.
- Ask BookForge for legal actions/readiness.
- Run one `continue_scene` step or a bounded Nanda `AuthorWorkLoop`.
- Preserve branch-local artifacts and receipts.
- Prove canonical `main` did not change.
- Stop/cancel gracefully and resume only after fresh queries.

The broader product is not done. The remaining work is no longer "make BookForge supervisable." That substrate is effectively in place. The current closure problem is capability-truth consolidation, Nanda action-card routing, branch-local loop hardening, recovery workbench maturity, selected-prose handoff, visual/author/book-intent polish, and a later durable evidence ledger.

## Plan-State vs Code-Reality Xref

| Area | Plan State | Code Reality | Finding |
| --- | --- | --- | --- |
| BookForge supervisable engine | `0010-0082` all `completed` | Query/action/readiness/recovery/branch/scene surfaces exist; latest full regression previously reported `372 passed` | Treat as kernel substrate, not active blocker. Remaining work should move to successor/product plans. |
| BookForge capability projection | `0010-0060` all `completed` | `get_capability_projection`, CLI fixture, descriptors, action/query/readiness entries exist | Static capability truth is real. It still must not be treated as selected-scope readiness. |
| Nanda route/scope capability projection | Nanda step `0090` partially implemented | Nanda still has local/hardcoded capability truth, including `NANDA_WIRED_ACTIONS` | Highest-priority Nanda consolidation item. UI and author claims need one backend route/scope projection. |
| `continue_scene` | Implemented in BookForge and wired in Nanda | BookForge emits nested `author_loop_step_receipt_v1`; Nanda preserves it with fallback | Good convergence. This is the correct first loop primitive. |
| `get_next_writing_target` and writing gates | Implemented BookForge-side | `bookforge.query.writing:get_next_writing_target` and `get_writing_gate_status` exist and are projected | Nanda can use these to expand beyond a single-scene loop, but should still require envelope approval. |
| Seam queue/detail | Implemented BookForge-side and Nanda-side | `chapter_seam_queue` and `scene_pair_seam_detail` exist in BookForge; Nanda has routes/query runner references | Ready for branch-local seam selection and inspection without artifact archaeology. |
| `apply_bridge_scene_insertion` | External review/Nanda plan still call it unavailable | BookForge now implements same-section branch-local apply/materialization and projects it | Active drift. Nanda must either wire it with gates/tests or mark it intentionally withheld despite upstream implementation. |
| BookIntent/create book | Earlier notes called this missing | BookForge has `draft/approve/create_book_from_intent`; Nanda has job paths | The "cannot create canonical BookForge book" assessment is stale. Product polish remains, but the surface exists. |
| Author create/refine | Earlier notes called this missing or partial | BookForge has `create_author` and `refine_author`; Nanda has direct paths | Create/refine exists. Preview/select/rollback/version-to-book selection remain follow-up. |
| Visual generation | Plan is still `in_progress` | OpenAI and Nano Banana generation are wired; visual queries/actions/readiness exist; Nanda routes exist | First visual slice is usable but plan docs are behind Nanda code in places. Reference/layer/refinement workflows remain unfinished. |
| Recovery planning and primitives | Implemented through 0082 | Lineage audit, recovery branch, quarantine/normalize/invalidate/rebuild/redraft/validate/promote-style primitives exist | Usable for branch-local recovery planning and steps. Needs stronger workbench receipts, idempotency, validation-first promotion, and reader/diff refresh. |
| Reader anchors | Implemented BookForge/Nanda query surface | Reader anchors expose artifact/source/mutation-target evidence | Selection-to-action handoff is still incomplete. Talking about selected prose is easier than safely mutating it. |
| Durable data/evidence layer | Draft/pinned | File-backed artifacts plus Nanda SQLite conversations/jobs | Important but intentionally pinned for now. Do not block heartbeat work on DB migration. |

## Confirmed Stale Or Conflicting Claims

1. `apply_bridge_scene_insertion` is no longer a pure BookForge gap.
   - BookForge has `build_apply_bridge_scene_insertion_request(...)`.
   - BookForge has `apply_bridge_scene_insertion_action(...)`.
   - BookForge projects `action.apply_bridge_scene_insertion`.
   - Nanda still has code/commentary saying BookForge exposes this as a gap.

2. BookIntent/create-book is no longer only a designed gap.
   - BookForge exposes `create_book_from_intent`.
   - BookForge docs mention `bookforge.execution.create_book_from_intent_action(...)`.
   - Nanda has job/route surfaces for BookIntent flow.

3. Author creation/refinement is no longer only a designed gap.
   - BookForge exposes `create_author` and `refine_author`.
   - Nanda has direct create/refine paths.
   - The missing product layer is chat/persona/preview/select/rollback, not the base mutation primitive.

4. Visual Nanda routes are ahead of the BookForge visual plan note.
   - BookForge visual step `0080` still says Nanda bridge/API routes and UI rendering remain.
   - Nanda has `src/nanda/api/routes/visual.py` and `src/nanda/bridge/bookforge/visual.py`.
   - Remaining visual work is refresh, reference/layers/refinement, and richer UI flow.

5. The old test-count snapshots are stale.
   - The current local plan/code footprint includes many more tests and surfaces than the review's lower counts.
   - Test counts alone do not prove product readiness; use them only as regression confidence.

## P0 Punch List

### 1. Consolidate Nanda Route/Scope Capability Truth

Owner: Nanda, with BookForge projection/readiness as inputs.

Problem:

Nanda still has multiple capability truth sources: BookForge static projection, local bridge functions, job registry, route logic, React-derived affordances, and `NANDA_WIRED_ACTIONS`.

Required shape:

- Backend endpoint or service such as `/api/scope-capabilities`.
- Inputs: route/scope, `book_id`, `author_ref`, `conversation_id`, `branch_id`, `chapter`, `section`, `scene`, selected reader anchor, mode policy, approval state.
- Outputs: action cards with capability id, label, bridge status, UI exposure, legal status, readiness status, mutation class, branch policy, approval requirement, expected receipt, expected artifacts, stale/fresh status, blocked/refusal reason, and evidence refs.

Definition of done:

- UI never enables an action from local React logic when the backend projection says blocked, stale, unavailable, approval-gated, or not bridged.
- Author chat action grammar consumes the same backend projection.
- Designed/query-only/theater capabilities cannot render as executable.
- Tests prove backend projection blocks both UI action cards and chat `ProposedActionPlan` execution.

BookForge support needed:

- Keep static descriptors stable.
- Ensure every action/query/readiness descriptor includes mutation class, branch policy, approval requirement, expected receipt/artifact status, refusal semantics, and evidence refs.
- Add descriptor entries for newly implemented surfaces as they land.

### 2. Reconcile `apply_bridge_scene_insertion` Across Repos

Owner: BookForge and Nanda.

Problem:

BookForge has implemented same-section branch-local bridge insertion apply, while Nanda still treats it as unavailable.

Decision:

- If the BookForge same-section semantics are sufficient, wire it through Nanda.
- If the semantics are not yet product-safe, explicitly classify it as `implemented_upstream_withheld_in_nanda` with missing validation reasons.

BookForge already provides:

- Branch-only refusal.
- Existing bridge proposal requirement.
- Live-node mismatch handling.
- Same-section branch-local outline/registry/projection mutation.
- Shifted artifact handling for following scene ids.
- `canonical_changed=false` branch-local receipt semantics.
- Recommended next actions: `plan_scene`, `continue_scene`.

Nanda work if wiring:

- Add bridge wrapper in `bookforge_ops.py`.
- Add job/action registry entry.
- Add route if needed.
- Add branch-live `ProposedActionPlan` validation.
- Add Branch Workbench action card gated by non-main branch, same-section pair, existing proposal, legal action row, and expected receipt.
- Add receipt card showing inserted scene id, moved artifacts, branch-only mutation, canonical unchanged, and next actions.

Tests:

- Main branch refusal.
- Missing proposal refusal.
- Stale node refusal.
- Same-section success.
- Canonical unchanged.
- Nanda route/scope projection marks available only when proposal/legal/readiness evidence exists.

### 3. Replace `NANDA_WIRED_ACTIONS`

Owner: Nanda.

Problem:

`src/nanda/bridge/bookforge/author_context.py` still hardcodes a stale action list. It omits newer job/actions like `continue_scene`, `author_work_loop`, BookIntent, visual, author assets, seam queue/detail, and bridge insertion.

Definition of done:

- Replace `NANDA_WIRED_ACTIONS` with a bridge-status overlay generated from:
  - BookForge static capability projection.
  - Nanda job/action registry.
  - Direct bridge modules.
  - UI exposure registration.
  - Mode/approval policy.
- If a local overlay remains, it names Nanda bridge availability only, not engine capability truth.
- Tests verify every job action maps to bridge status and every bridge status maps to a BookForge capability or explicit Nanda-only action.

### 4. Run The Branch-Local Heartbeat Smoke Test

Owner: both.

Scope:

Do not test whole-book autonomy yet. Test the smallest trustworthy loop.

Test script:

1. Select a known book.
2. Create/select a non-main branch.
3. Select a scene scope.
4. Confirm branch detail/legal actions report `continue_scene`.
5. Run `Continue one step`.
6. Verify job events, child receipt refs, produced artifacts, stop reason, recommended next action, and `canonical_changed=false`.
7. Run bounded `AuthorWorkLoop` with a low max-step count.
8. Cancel mid-loop and verify no next child action starts after BookForge yields.
9. Refresh branch reader/artifact/diff/seam queue.
10. Verify author response/status cards do not claim more than receipts prove.

Pass conditions:

- Branch-local artifacts remain inspectable after stop/cancel.
- Canonical main is unchanged.
- Resume strategy requires fresh branch/detail/readiness/legal-action queries.
- No UI action is enabled without legal/readiness/bridge evidence.

## P1 Punch List

### 5. Harden `AuthorWorkLoop`

Owner: Nanda with BookForge stop-code stability.

Remaining:

- Refresh branch detail, legal actions, and readiness between child steps.
- Add explicit resume button that re-queries before scheduling another loop.
- Add max duration/time-budget UI.
- Add spend envelope before any spend-bearing loop action is allowed.
- Add tests for no legal action, provider failure after partial progress, stale branch, tool unavailable, completed scope, and book complete.
- Keep section lock/chapter finalize as explicit next actions until the user approves a broader envelope.

Definition of done:

- Loop never schedules a child action from stale readiness.
- Cancel stops scheduling; completed branch work is preserved.
- Resume does not use chat memory as truth.
- Final loop result always has stop reason, last action, receipt refs, artifact refs, branch id, canonical-changed status, and resume strategy.

### 6. Make Action Cards The Primary UX Contract

Owner: Nanda.

Definition of done:

- Branch Workbench, Recovery Workbench, Visual Workbench, BookIntent, Author Assets, and Author Chat render action availability from the backend route/scope projection.
- Each action card shows target scope, branch/canonical policy, mutation class, legal/readiness status, approval, expected receipt/artifact, blocked reason, and last relevant receipt.
- Internal action keys move to debug/secondary text.

### 7. Unify Direct UI Jobs And Chat-Proposed Actions

Owner: Nanda.

Scope:

- `create_author`
- `refine_author`
- `draft_book_intent`
- `approve_book_intent`
- `create_book_from_intent`
- `plan_visual_asset`
- `generate_visual_asset`
- `continue_scene`
- `author_work_loop`
- recovery and seam actions

Definition of done:

- Direct UI forms and author chat use the same validator/runner envelope.
- A direct form can prefill an action plan, but it does not bypass commit gate, approval, or receipt handling.
- Final responses and status cards use one outcome capsule shape.

### 8. Build Selected-Prose To Action Handoff

Owner: Nanda using BookForge reader anchors.

Definition of done:

- Reader selection creates a structured selection card with book, branch, chapter, section, scene, artifact ref, source hash, span offsets, artifact status, freshness, and `valid_as_mutation_target`.
- Author chat receives the selection as structured context.
- Mutation candidates require a valid BookForge mutation-safe anchor.
- Diagnostic fallback and stale selections can be discussed but not mutated.

### 9. Harden Recovery Workbench

Owner: Nanda and BookForge.

Remaining:

- Recovery branch receipt timeline.
- Idempotency/replay protection for branch-local recovery actions.
- Validation-first promotion confirmation.
- Reader/diff refresh after every recovery step.
- Promotion screen with validation receipts, branch diff, canonical postconditions, approval record, and deletions/quarantines.

Definition of done:

- The operator can see what was diagnosed, what branch was created, what mutated, what was quarantined/deleted, what validation passed, what canonical state did not change, and what remains before promotion.

### 10. Close Visual First-Slice Drift

Owner: BookForge and Nanda.

BookForge plan reality:

- Contracts/descriptors are done.
- Prompt-plan/generate are wired.
- OpenAI and Nano Banana generation are wired.
- Reference/edit/layer/composition/refinement remain incomplete.
- xAI remains descriptor-only pending API/pricing verification.

Nanda reality:

- Visual routes and bridges exist.
- Manual refresh and richer workbench lifecycle remain.

Definition of done:

- Update visual plan notes so they no longer say Nanda routes are missing if they exist.
- Nanda refreshes visual workbench from terminal job events.
- Reference/layer/refinement capabilities remain planned/unavailable until BookForge has descriptors, readiness, and receipts.

## P2 Punch List

### 11. Response Capsules And Budget Tiers

Owner: Nanda.

Definition of done:

- Final author response receives a compact capsule for action-bearing turns.
- Capsule includes user intent, selected scope, accepted evidence, stale/unavailable evidence, executed action/result, branch/canonical status, active jobs, not-done list, and next safe actions.
- Long artifacts route to reader/workbench panes, not huge chat bubbles.

### 12. Live Bus / Near-Streaming Operational Events

Owner: Nanda.

Definition of done:

- SSE or reliable polling for turn/job progress.
- UI sorts by causal/stage order.
- Visible state reflects actual query/action/receipt progress, not generic planner anatomy.

### 13. Chat Title/Rename

Owner: Nanda.

Definition of done:

- Generated titles after early turns.
- Rename route/UI.
- User title override is preserved.
- Conversation list displays book/author/scope/mode/integrity badges.

### 14. Manuscript Output And Quality Gates

Owner: BookForge successor plan.

Definition of done:

- Canonical and branch-local manuscript compile preview.
- Word count/completeness gates.
- Export readiness.
- Reader-quality diagnostics with artifact status.
- Future route for prose quality gates, repetition, style drift, and publishable manuscript snapshots.

### 15. Lint/Repair Routing

Owner: BookForge successor plan.

Definition of done:

- Separate prose-only, state/continuity, seam, and full repair lanes.
- Receipt explains route classification.
- Ambiguous classification refuses or escalates instead of widening silently.

### 16. Durable Evidence Ledger

Owner: BookForge primary, Nanda consumer.

Status:

Pinned, not immediate heartbeat blocker.

Definition of done:

- SQLite or relational ledger for operation runs, receipts, artifacts, scopes, branches, issue tickets, artifact spans, approvals, dependencies, and citations.
- File artifacts remain content/object storage; the ledger becomes the queryable index.
- Nanda conversations/jobs link to BookForge operation and receipt ids.
- Future vector retrieval indexes ledger-backed artifacts only.

## BookForge-Owned Closure Work

These are the BookForge tasks that actually close current Nanda gaps:

1. Keep capability descriptors complete and current for every implemented action/query/readiness surface.
2. Stabilize `continue_scene` receipt fields and stop-code enum as Nanda loop fixtures.
3. Publish/maintain legal-action semantics for `apply_bridge_scene_insertion`.
4. Add or update help docs for:
   - `continue_scene`
   - writing gates
   - seam queue/detail
   - bridge insertion apply
   - BookIntent/create book
   - author create/refine
   - visual prompt/generate
5. Keep fixtures updated so Nanda can test projection ingestion without live BookForge execution.
6. Split successor plans rather than extending the completed supervisable-engine umbrella:
   - manuscript output and reader quality gates
   - lint/repair routing
   - outline contract hardening
   - author asset management v2
   - durable evidence ledger

## Nanda-Owned Closure Work

These are not BookForge bugs, but BookForge should expect Nanda to need them before product readiness:

1. Backend route/scope capability projection.
2. Action-card UI based on backend projection.
3. Replace `NANDA_WIRED_ACTIONS`.
4. Wire or intentionally withhold `apply_bridge_scene_insertion`.
5. Harden `AuthorWorkLoop` refresh/resume/cancel/status behavior.
6. Unify direct UI jobs with chat-proposed action runner.
7. Add selected-prose action handoff.
8. Harden recovery workbench receipts and promotion confirmation.
9. Add response capsules.
10. Add live/near-live bus polish.

## Serious "Done" Criteria

The platform is not "done" when it has many surfaces. It is done for the next milestone when:

- There is one backend source of truth for action availability at a selected route/scope.
- Every enabled UI action has legal/readiness/bridge/approval evidence.
- Every executed action has a receipt and artifact refs.
- Every author claim about execution can cite a receipt/job.
- Branch-local and canonical states are impossible to confuse in UI and prose.
- Cancel stops the loop without deleting completed branch work.
- Resume starts from fresh BookForge queries, not chat memory.
- Designed/planned/theater capabilities cannot become enabled actions by local UI fallback.
- Recovery and bridge insertion can be inspected, run branch-locally, validated, and either promoted or withheld with receipts.

## Immediate Order Of Work

1. Reconcile `apply_bridge_scene_insertion` drift with Nanda.
2. Build Nanda backend route/scope capability projection.
3. Replace `NANDA_WIRED_ACTIONS`.
4. Make action cards consume backend projection.
5. Run controlled branch-local heartbeat smoke test.
6. Harden `AuthorWorkLoop` refresh/resume/stop-code coverage.
7. Unify direct UI jobs and chat-proposed actions.
8. Add selected-prose action handoff.
9. Harden recovery workbench receipts/promotion.
10. Update visual plan/code alignment and refresh behavior.
11. Start successor plans for manuscript output and lint/repair routing.
12. Return to durable evidence ledger once heartbeat/product gaps are tighter.

