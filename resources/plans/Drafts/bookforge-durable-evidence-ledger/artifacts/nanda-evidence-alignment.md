# Nanda Evidence Alignment

Status: Initial alignment from Nanda draft plans and current implementation notes

## Nanda Inputs Reviewed
- `nanda-author-start-authoring/plan.md`
- `nanda-author-start-authoring/steps/0030-response-budget-tiers-and-response-capsules/step.md`
- `nanda-author-start-authoring/steps/0045-closing-command-set-and-post-response-runner/step.md`
- `nanda-author-start-authoring/steps/0090-capability-projection-registry-bridge/step.md`
- `nanda-author-start-authoring/artifacts/bookforge-durable-evidence-substrate-ask.md`
- `nanda-author-start-authoring/artifacts/closing-command-set-review.md`
- `nanda-author-start-authoring/steps/0080-author-creation-and-refinement-bridge/step.md`
- `nanda-author-start-authoring/validation/acceptance.md`
- `nanda-author-start-authoring/artifacts/2026-04-27-chatgpt-review-delta.md`
- `src/nanda/store/conversations.py`
- Current Nanda author route receipt/capsule handling in `src/nanda/api/routes/author.py`

## Nanda Needs
### Response Capsules
Nanda wants final author prose to receive compact facts, not full planning state. BookForge must provide stable receipt and artifact refs that can be placed inside those capsules.

### Post-Response Proposed Actions
Nanda is moving toward `AuthorDraftEnvelope` plus `ProposedActionPlan`. The runner will validate a proposed action against capability projection, legal/readiness receipts, commit gates, approval, freshness, idempotency, and expected receipt type. BookForge evidence needs stable operation and receipt IDs for those checks.

### Branch-Scope Transition
After a recovery or rerun branch is created, Nanda needs a branch transition receipt before chat can honestly claim it is working in that branch. BookForge should make the source action receipt and branch evidence easy to query.

### Action Cards
Nanda action cards need expected receipts, previous receipts, artifact availability, approval requirements, refusal reasons, and branch/canonical mutation status. BookForge capability projection gives static truth; evidence ledger gives historical proof and current artifact refs.

### Reader Anchors
Reader selections must carry provenance and freshness. The user will highlight prose and ask for change; Nanda needs to know whether the selected span is canonical, branch-local, diagnostic fallback, stale, or non-mutation-safe.

### Recovery Workbench
Nanda needs to show recovery branch creation, anchor selection, quarantine, normalization, invalidation, state rebuild, redraft, validation, and promotion as receipt-backed steps. The ledger should let the workbench show what happened and what remains without scanning files.

### Author Assets
Nanda now has a specific author creation/refinement bridge step. It expects BookForge-owned author asset operations to return structured receipts with created/refined author refs, previous refs, versions, artifact refs, hashes, profile summaries, diff summaries, warnings/refusals, and next suggested actions.

This requires workspace-level evidence because author creation can happen before a book exists. Selecting an author version for a book remains a separate book-scoped action and should record a transition receipt when implemented.

### Product State Labels
Nanda is standardizing visible states such as `answered`, `inspected`, `ready`, `blocked`, `pending_approval`, `executing`, `executed_branch_local`, `executed_canonical`, `failed`, and `paused`. BookForge evidence should provide enough receipt and operation status to support these labels without Nanda inferring them from prose.

## Nanda SQLite Pattern
Nanda already uses SQLite for conversations, turns, planning artifacts, and work artifacts. That store is useful as a pattern for local durability, WAL mode, and JSON payloads. BookForge's ledger needs stronger operation/receipt/artifact relationships and content hashes because it owns execution truth.

## Alignment Rule
Nanda can reason and present strategy. BookForge must provide mutation-safe evidence, stable IDs, and queryable relationships. The author voice may translate receipts into style, but receipts remain the proof.
