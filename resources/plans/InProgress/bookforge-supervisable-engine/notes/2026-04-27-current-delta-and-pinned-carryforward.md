# 2026-04-27 Current Delta And `_Pinned` Carry-Forward

## Current State
- `bookforge-supervisable-engine` is complete through `0082`.
- Full regression is green: `310 passed`.
- BookForge now has the engine substrate originally missing during the Veiled Ledger failure:
  - explicit `TimelineNodeRef` / `ScopeSelector`
  - book-rooted state and issue surfaces
  - branch-local current-node state
  - isolated rerun branches and fork groups
  - action discovery through `legal_next_actions`
  - scene-phase write actions
  - branch-scoped writing
  - appearance, setting, and thought-context projection surfaces
  - outline lineage audit and section-level lineage matrix
  - recovery branch primitives
  - recovery blast radius and invalidation previews
  - semantic recovery and downstream dependency diagnostic surfaces

## What This Means
- The system can now explain and contain lineage contamination mechanically.
- BookForge has timeline-safe primitives that Nanda can compose.
- The operator should no longer be the only safety catch for mixed-outline/chimera states.
- The current gap is no longer "can BookForge know what happened?"
- The next gap is "can Nanda reason over these surfaces, select an approved plan, and drive the right primitives without manual command choreography?"

## What We Still Need To Get To
- Nanda-side:
  - `book_timeline_impact_report_v1`
  - action comparison and shadow-mode planning
  - approval gates for destructive cleanup, anchor selection, and promotion
  - author-pane capability grounding from BookForge readiness/action surfaces
- BookForge-side follow-up:
  - manuscript compile/export
  - output-quality gates before commit/promotion
  - prose-only lint/repair routing
  - series continuity rollups
  - deeper outline contract hardening
  - generated action/skill/MCP capability projection

## Valuable `_Pinned` Carry-Forward
### `bookforge_plan_v3_draft.md`
Still valuable:
- compile/export
- opening preview gate
- banned phrase and similarity checks
- word/page count enforcement
- prompt registry/logging completeness
- thought-signature replay/perspective surfaces

Current delta:
- durable state, appearance, branch isolation, action discovery, recovery, and semantic diagnostics have moved beyond this draft.
- compile/export and output-quality gates remain the highest-value unimplemented parts.

### `lint_repair_split_routing_plan_20260213_183000.md`
Still valuable:
- deterministic issue classification
- prose-only fast repair lane
- lane-specific metrics
- conservative escalation back to full repair

Current delta:
- lint/repair pass depth is already raised to `8`.
- the right implementation point is now the scene/action surface and receipts, not hidden `runner.py` logic alone.

### `series_continuity_plan.md`
Still valuable:
- `series_summary.json`
- series continuity pack
- book-end rollups
- cross-book character state rollups
- series-aware linting/validation

Current delta:
- workspace and character canon scaffolding exist, but phases 4-7 remain a real future milestone.

### `outline_dynamic_lint_repair_loop_plan_20260412_1505.md`
Still valuable:
- P0 deterministic outline lint checks
- repair-family grouping: Structural / Identity / Seam
- window overlap and convergence rules
- issue fingerprinting

Current delta:
- section chunking, lineage audit, and recovery branches reduce the blast radius.
- a full outline lint/repair loop is still useful, but should be implemented as a scoped action/readiness path, not as more hidden phase jungle.

### `downstream_contract_alignment_gap_plan_20260216_0233.md`
Still valuable:
- planner propagation of transition/location fields
- location ID ownership unification
- `end_condition` prompt/schema alignment
- lint strictness wiring
- unknown-key preserve-and-route doctrine

Current delta:
- some downstream safety is now handled through lineage/recovery surfaces.
- the schema/prompt/runtime contract details remain relevant for a follow-up hardening plan.

### `bookforge_agent_skilltree_plan_20260412.md`
Still valuable:
- skill capabilities should map to real graph/action nodes
- generated capability docs should be derived from a manifest/catalog
- orchestrators should route without duplicating execution logic

Current delta:
- the source of truth should now be `legal_next_actions`, readiness queries, `ExecutionRequest`, `ExecutionResult`, and produced-artifact receipts.
- any MCP skill layer should be generated from those surfaces, not from a separate hand-maintained pipeline model.

### Thought Signature Probe Reports
Still valuable:
- isolated lens probes
- compression/critic/conflict/failure-simulation batteries
- cross-probe stability as diagnostic signal

Current delta:
- thought signatures are context and recovery aids.
- receipts, artifacts, and `TimelineNodeRef` remain execution truth.

### Durable Appearance / Inventory / Continuity Completed Plans
Still valuable:
- durable-state doctrine
- appearance/inventory/plot-device validation rules
- authoritative-surface boundaries

Current delta:
- `0075` and `0081` brought some of this into query/recovery validation.
- deeper series-level and author-facing projection work remains useful.

## Mostly Superseded `_Pinned` Material
- v1/v2 scaffolding plans
- early runner-lift plans
- older outline refinement plans marked failed
- proposed section-chunking details already absorbed by `0070-0082`
- stale deterministic seam-repair framing where it conflicts with the doctrine that LLM authors semantic seam repairs

## Recommended Next Plan Order
1. `bookforge-manuscript-output-and-quality-gates`
2. `bookforge-lint-repair-routing`
3. `bookforge-series-continuity-rollups`
4. `bookforge-outline-contract-hardening`
5. `bookforge-author-skill-capability-projection`
