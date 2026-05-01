# BookForge Action Skill Projection For Nanda

Status: In Progress
Stage: InProgress
Owner: BookForge engine workstream
Last Updated: 2026-04-29

## Objective
- Expose a generated, machine-readable BookForge capability projection from real query, action, readiness, branch, recovery, and receipt surfaces.
- Let Nanda build its author capability registry from BookForge engine truth instead of manual allowlists, persona claims, or prompt-maintained assumptions.
- Preserve adaptive authoring: BookForge reports available moves and readiness; Nanda chooses a path, may stop after any receipt, and may replan rather than being forced through a fixed pipeline.

## Why Now
- `bookforge-supervisable-engine` established the execution kernel: legal actions, readiness, scene-phase execution, branch-scoped writing, lineage audit, recovery primitives, projection layers, diagnostics, and receipts.
- Nanda now needs a live capability source so its author pane can say what it can actually do, what is only queryable, what requires approval, and what is not wired.
- The next failure mode is capability drift: BookForge supports an action but Nanda does not know it, or Nanda claims an action that BookForge cannot execute at the selected scope.
- The author workflow is moving from fixed end-to-end batches toward graph traversal: write a scene, inspect the receipt, align a scene pair, insert a bridge scene if needed, lint, repair, branch, or move forward.
- This requires a capability projection that honors true units of work, not just exposed code functions.

## Grounding
- `resources/plans/InProgress/bookforge-supervisable-engine/plan.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/notes/2026-04-27-current-delta-and-pinned-carryforward.md`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/scene_phase.py`
- `src/bookforge/query/recovery.py`
- `src/bookforge/execution/actions.py`
- `src/bookforge/execution/recovery_actions.py`
- `src/bookforge/contracts/execution_option.py`
- `src/bookforge/contracts/scene_phase.py`
- `src/bookforge/contracts/produced_artifact.py`
- `src/bookforge/contracts/execution_result.py`
- `src/bookforge/cli.py`
- Nanda counterpart plans:
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-author-reasoning-loop\plan.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-governed-authoring-runtime\plan.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-author-chat-bus\plan.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-author-start-authoring\plan.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\bookforge-reader-query-api-spec.md`
- Nanda current API/UI evidence:
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\api\app.py`
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\api\routes\author.py`
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\api\routes\books.py`
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\api\routes\reader.py`
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\api\routes\ops.py`
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\bridge\bookforge\author_context.py`
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\bridge\bookforge\bookforge_ops.py`
  - `C:\Users\Zythis\source\repos\nanda\src\nanda\bridge\bookforge\reader.py`
  - `C:\Users\Zythis\source\repos\nanda\ui\src\scope.ts`
  - `C:\Users\Zythis\source\repos\nanda\ui\src\features\scope\ScopeCapabilityPanel.tsx`
  - `C:\Users\Zythis\source\repos\nanda\ui\src\features\actions\ActionsPane.tsx`
  - `C:\Users\Zythis\source\repos\nanda\ui\src\features\books\ReaderScreen.tsx`

## Core Model
### Static Capability vs Dynamic Readiness
- A capability descriptor says what BookForge knows how to do in general.
- A readiness result says whether that move is currently legal and ready for one specific `ScopeSelector` and `TimelineNodeRef`.
- These must stay separate.
- Example:
  - Static capability: `write_scene_prose` exists for scene scope and can run branch-local.
  - Dynamic readiness: chapter 3, section 2, scene 1 is not ready because the scene card is missing.

### Adaptive Graph Traversal
- BookForge exposes legal actions and readiness as a graph of available moves.
- Nanda and the author agent choose a path through that graph.
- `recommended_next_action` is guidance, not a rail.
- Macro workflows may provide a default recipe, but the caller may stop, branch, inspect, repair, insert, rewrite, or replan after any receipt.
- The system should support organic authoring patterns such as:
  - write scene 2
  - align scene 1 and scene 2 based on the desired transition shape
  - move to scene 3
  - insert a bridge scene if the transition cannot be made honest locally
  - fork a branch to rewrite an old scene without touching canonical main
  - compare candidate branches before promotion

### Unit Boundary Doctrine
- Public commands and skills should represent meaningful operator or agent decision points.
- Do not expose internal helper functions as capabilities just because they exist in code.
- A public capability is justified when it has its own:
  - scope selector
  - readiness or legal-action semantics
  - mutation class
  - branch policy
  - receipt shape
  - artifact status outputs
  - refusal semantics
  - approval requirement, when applicable
- If an operation only renders a prompt, parses JSON, formats output, applies retry plumbing, or calls a provider as part of a larger phase, it should stay internal.
- If an operation changes what the author or supervisor can choose next, it is probably a real capability.

### Capability Unit Types
- `query`: read-only information surface, such as lineage audit or reader view.
- `readiness`: read-only current-state assessment for a specific action and scope.
- `primitive_action`: one meaningful action with its own receipt, such as `write_scene_prose`.
- `validation_gate`: a diagnostic or validation action that can block promotion or downstream use.
- `macro_workflow`: an optional recipe composed of child actions, such as section advance or chapter finalize.
- `promotion_action`: canonicalization, merge, or branch promotion with explicit approval and validation.
- `projection_skill`: generated descriptor or metadata surface used by tools such as Nanda.

### Capability Descriptor Shape
Each projected capability should include:
- `schema_version`
- `capability_id`
- `human_label`
- `unit_type`
- `capability_type`
- `action_key` or `query_key`
- `supported_scope_kinds`
- `required_selector_shape`
- `branch_policy`
- `mutation_class`
- `approval_required`
- `readiness_source`
- `expected_receipt_type`
- `produced_artifact_statuses`
- `legal_next_action_relationships`
- `refusal_semantics`
- `child_actions` for macro workflows
- `evidence_sources`

### Mutation Classes
- `read_only`
- `diagnostic_only`
- `provisional_branch_mutation`
- `branch_mutation`
- `canonical_mutation`
- `promotion`
- `assembly`

### Artifact Status
- Capabilities that produce artifacts must declare expected statuses:
  - `authoritative`
  - `provisional`
  - `derived`
  - `diagnostic`
- Receipts remain the execution truth. Thought signatures, persona context, and prompt commentary are not proof that a capability exists or executed.

### Macro Workflows Are Recipes
- Existing end-to-end workflows should remain available as convenience commands when useful.
- A macro workflow must expose its child actions and boundaries rather than hiding the graph.
- A macro should not imply that the child sequence is mandatory for author agents.
- The author agent should be able to call the primitive action directly when it has enough context and readiness says the action is legal.

### Recovery Branch Truth
- `create_recovery_branch` means isolate the recovery work and record the selected anchor.
- It does not mean the branch is clean.
- A recovery branch initially snapshots current branch state and materializes outline evidence needed for diagnosis, including stale artifacts when those artifacts exist.
- The branch becomes clean only after cleanup, normalization, output invalidation, state rebuild, redraft, validation, and promotion receipts prove that result.
- Nanda author voice must describe this as an isolated recovery workspace, not a sterile copy or a clean timeline.

### MCP-Style Future Compatibility
- This plan does not build an MCP server.
- It should produce capability descriptors that are close enough to MCP-style skill metadata that a later protocol adapter can map each truthful BookForge capability into an MCP tool or resource without reinterpreting engine semantics.
- If future workflow nodes become MCP skills, the projected capability is the source of truth, not a separate hand-maintained tool list.

### Nanda Surface Coverage
- Nanda's current UI and FastAPI already expose screens that imply BookForge capabilities:
  - Books / Library
  - Book Detail
  - Reader
  - Scope Capability panel
  - Actions pane
  - Author Chat workbench
  - Recovery/integrity views
- BookForge must help Nanda avoid prompt/UI theater by projecting both what exists and what is intentionally absent.
- Missing surfaces should be visible as unsupported, designed, or successor-plan gaps. They should not be inferred from filesystem fallbacks.
- Canonical reader, book-card, branch inventory/detail/artifact-index/diff-summary, and recovery anchor/plan preview baselines are now part of this projection-plan implementation because Nanda needed them to stop relying on filesystem fallback truth.
- Reader/prose anchors are part of the reader surface: they turn selected prose spans into read-only, branch-aware evidence with source paths, hashes, offsets, freshness, and mutation-target safety.
- Author asset create/refine is now pulled into this plan as the first mutation slice for Nanda's author-only chat; author version selection/rollback, book intent, lint/repair routing, deep inventory/state layers, reader quality gates, and export remain successor-plan needs.
- This plan owns the capability descriptor layer and gap visibility. Follow-on successor plans own the missing domain APIs.

## Scope
- Audit current BookForge query, action, readiness, branch, recovery, projection, and receipt surfaces.
- Audit Nanda's plans, FastAPI routes, bridge modules, and UI screens for BookForge-owned missing surfaces/APIs.
- Define the first `CapabilityProjection` contract and capability descriptor vocabulary.
- Generate or assemble capability projection from real BookForge surfaces.
- Expose projection through Python and CLI JSON.
- Add a Nanda consumption fixture that covers read-only queries, readiness, branch-local mutation, promotion-gated mutation, recovery diagnostics, and refusal/blocking examples.
- Document the mapping to Nanda and future MCP-style skill layers.

## Non-Goals
- No full MCP server.
- No Nanda UI work.
- No new author persona style doctrine beyond wrapping existing BookForge author generation/refinement in truthful action/receipt surfaces.
- No new scene-writing or recovery mutation primitive unless needed only as a fixture adapter.
- No static hand-maintained list that can drift from real BookForge actions.
- No claim that a capability is dynamically ready without a scope-specific readiness call.
- No conversion of internal helpers into public skills.
- Author create/refine mutation APIs are in scope as versioned author-library actions because Nanda's author-only chat needs a real BookForge tool surface; select/rollback mutation APIs, export, lint/repair routing, and book intent APIs remain out of scope unless represented as projection descriptors or explicit gap entries.
- Canonical reader/book-card/branch-detail/artifact-index/diff-summary and recovery anchor/plan preview baselines are in scope only as read-only query surfaces required to make Nanda's capability, branch workbench, and recovery planning truth non-theatrical.
- No claim that Nanda filesystem fallbacks are canonical BookForge surfaces.

## Deliverables
- Capability projection contract under `src/bookforge/contracts/`.
- Capability query module under `src/bookforge/query/`.
- Projection registry or generator that references existing action/readiness/query surfaces.
- CLI command for JSON projection output.
- Tests that compare projected action IDs against real action discovery where possible.
- Fixture output for Nanda to consume in tests.
- Reader/prose anchor query and CLI surface for mutation-safe selected passage targeting.
- `artifacts/nanda-surface-api-gap-audit.md`
- `artifacts/nanda-api-ui-crosswalk.md`
- `artifacts/bookforge-nanda-surface-backlog.md`
- `artifacts/capability-unit-examples.md`
- `artifacts/2026-04-29-bookforge-nanda-snapshot-xref-punch-list.md`
- `artifacts/2026-04-29-gap-closure-refinement-plan.md`
- `artifacts/2026-04-29-message-to-nanda-agent.md`
- `artifacts/2026-04-29-apply-bridge-scene-insertion-contract.md`
- `artifacts/2026-04-29-slice-note-apply-bridge-scene-insertion.md`
- `artifacts/2026-04-29-continue-scene-loop-contract.md`
- `artifacts/2026-04-29-slice-note-continue-scene-loop-contract.md`
- `artifacts/2026-04-29-slice-note-capability-fixture-sync.md`
- `artifacts/2026-04-29-message-to-nanda-scope-capabilities.md`
- `artifacts/2026-04-29-slice-note-branch-writing-target-advance.md`
- `artifacts/2026-04-29-slice-note-bridge-insertion-refresh-surfaces.md`
- `artifacts/2026-04-29-slice-note-branch-local-heartbeat-proof.md`
- `artifacts/2026-04-29-slice-note-author-loop-refresh-contract.md`
- Documentation that distinguishes:
  - static capability
  - dynamic readiness
  - primitive action
  - macro workflow
  - promotion action
  - future MCP-style mapping

## Plan-Level Definition Of Done
- Nanda can build a capability registry from BookForge output without hardcoding BookForge actions.
- Nanda's current API/UI needs are mapped to BookForge-owned surfaces, successor plans, or Nanda-owned work.
- Nanda's current FastAPI routes and UI screens are crosswalked to BookForge surfaces so reader/actions/scope capability gaps are visible.
- Major missing BookForge surface families are grouped into successor-ready slices with priority, likely APIs, commands/skills, and definitions of done.
- Every projected capability maps to a real BookForge query, readiness, action, diagnostic, promotion, or macro source.
- Projection distinguishes static engine support from scope-specific readiness.
- Projection identifies scope requirements, branch policy, mutation class, approval requirement, expected receipt, artifact status, and refusal semantics.
- Macro workflows expose child actions instead of hiding pipeline rails.
- Tests fail if a projected capability points at a missing or stale surface.
- Tests fail if a real public action is omitted from projection without an explicit documented exclusion.
- Reader/prose anchors let callers distinguish canonical current text, branch current text, missing artifacts, invalid spans, and inspect-only chapter selections before creating mutation requests.
- The projection can represent future adaptive authoring moves, such as scene insertion and pairwise seam alignment, without claiming they are wired before implementation exists.
- The projection can carry explicit gap/designed metadata for BookForge successor-plan surfaces such as author selection/rollback, book intent/synopsis, lint/repair routing, deep state/inventory projections, reader quality gates, and export.

## Risks
- Manual duplication could recreate capability drift between BookForge, Nanda, and UI code.
- Combining capability and readiness would let Nanda confuse "engine supports this" with "this scope is ready now."
- Over-projecting helper functions would create noisy tools that do not match author intent.
- Under-projecting macro child actions would leave Nanda trapped behind rails.
- Promotion, branch-local mutation, and diagnostic-only actions must not share vague mutation labels.
- Capability descriptors that omit artifact status would recreate file-safety ambiguity.

## Initial Implementation Bias
- Start by inventorying what exists.
- Start from Nanda's actual UI/API needs, not only BookForge's internal module list.
- Prefer large coherent surface slices over one-off endpoints. If a missing API is part of reader, branch explorer, author assets, seam repair, or export, plan the whole slice instead of patching only the current UI hole.
- Name the first contract before writing generator code.
- Generate from existing descriptors where possible.
- Where no registry exists yet, use a small explicit adapter with tests that compare it against real discovery surfaces.
- Keep the first implementation thin: enough for Nanda to ingest and classify, not a full skill marketplace.
