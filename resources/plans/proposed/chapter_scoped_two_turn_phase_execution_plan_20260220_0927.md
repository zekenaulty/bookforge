# Chapter-Scoped Two-Turn Phase Execution Plan (20260220_0927)

## Purpose
Define a production-safe two-turn execution model for chapter-scoped phases that need heavy reasoning and strict artifact emission, without merging phases.

Initial target (revised, priority order):
1. Phase 03 (scene draft) — chapter-scoped two-turn to stop thinking overflow
2. Phase 04A (transition seam analysis)
3. Phase 04B (transition execution)

Planned reuse pattern:
1. Writing
2. Linting
3. Repair

This plan is process and architecture only. No code behavior is changed by this document itself.

## Doctrine Anchor
This plan inherits:
1. `resources/plans/proposed/outline_pipeline_doctrine_manifesto_20260216_0205.md`

Locked doctrine:
1. LLM authors semantic content and semantic lint judgments.
2. Orchestrator never authors semantic prose/anchors and never discards semantic content silently.
3. Orchestrator enforces deterministic invariants, routing, retries, checkpointing, and reporting visibility.

## Core Thesis
Use a two-turn pair for selected chapter-scoped steps:
1. Turn 1: plan internally, emit minimal confirmation
2. Turn 2: execute from plan, emit strict chapter artifact

Preferred continuity mechanism:
1. Thought-signature continuation (if available and immediate)

Reliability mechanism:
1. Explicit compact planning artifact persisted between turns
2. Thought-signature ledger persisted per request with phase/turn scope

Operational rule:
1. Thought signature is optimization, not sole source of truth.

Execution framing:
1. Treat each chapter+phase pair as a short-lived micro-conversation (`T1 -> T2`) with immediate continuity use only.
2. Do not assume thought continuity survives long pauses; explicit plan artifacts are the durable bridge.

## Thinking Budget Policy (Critical for Phase 03)
Phase 03 is currently failing due to thought token overflow. We will introduce a thinking budget cap and per-turn thinking control to guarantee output headroom.

### Policy
1. `thinking_budget` is an optional hard cap for reasoning tokens.
2. If `thinking_budget` is set, **do not send `thinking_level`** in the same request (Gemini rejects mixed usage).
3. If `thinking_budget` is not set, fall back to `thinking_level`.
4. Per-turn defaults:
   1. `T1` uses step/phase-level `thinking_level` (or `thinking_budget` if set).
   2. `T2` defaults to `low` (or `minimal`) unless explicitly overridden.

### Env cascade (per step/phase)
1. `OUTLINE_PHASE_03_THINKING_BUDGET` (or phase/step-specific)
2. `OUTLINE_THINKING_BUDGET`
3. `GEMINI_THINKING_BUDGET`

If no budget is set, use the existing thinking level cascade:
1. `OUTLINE_PHASE_03_THINKING_LEVEL`
2. `OUTLINE_THINKING_LEVEL`
3. `GEMINI_THINKING_LEVEL`

## Doc-Backed Ground Truth (Gemini 3 Flash + Thought Signatures)
This section is the protocol anchor for this plan.

### Thinking controls
1. Gemini 3 Flash supports `thinking_level` (`minimal|low|medium|high`).
2. `minimal` is Flash-only and is "as close as possible" to no-thinking, not a hard disable.
3. Even at `minimal`, thought signatures still matter for continuity behavior.

### Thought signature semantics
1. Thought signatures are opaque/encrypted continuity artifacts and must be treated as non-interpretable payload.
2. When function calling is used:
   1. Signature is required on the first `functionCall` part in the step.
   2. Parallel calls: first `functionCall` part carries it.
   3. Sequential calls: each step's first `functionCall` carries one.
3. Without function calls, model may still return signature-bearing part (often final part).

### Strict validation boundary
1. Function-calling signature validation is strict within the provider-defined current turn.
2. Current turn is determined by scanning back to most recent user message that is not a `functionResponse`.
3. Missing required signature for first `functionCall` in any current-turn step yields provider `400`.

### Retention boundary
1. Explicit server-retention guarantees are documented for Interactions API only.
2. Interactions retention windows: paid and free tiers differ.
3. `store=false` disables `previous_interaction_id` continuation semantics.
4. For this plan's reliability model, do not assume server-stored retention; rely on local artifacts.

## Why This Is Needed
Observed and expected issues in single-turn chapter calls:
1. Model spends output budget on internal planning and leaves incomplete artifacts.
2. Phase 03 scene drafting has repeatedly failed due to thought-token overflow (MAX_TOKENS) even when chapter-scoped.
3. Seam insertion can pass structure but leave transition chain misalignment.
4. Long payload context increases token pressure and drift.
5. Resume after quota/rate pause may not preserve hidden thought continuity.

Two-turn chapter execution addresses this by:
1. Separating planning from rendering.
2. Making plan state explicit and inspectable.
3. Reducing per-turn payload and preserving chapter-locality.
4. Allowing deterministic resume behavior without semantic code synthesis.

## Non-Goals
1. Do not merge phases.
2. Do not convert deterministic validators into semantic prose judges.
3. Do not add code-authored fallback transition text.
4. Do not require full-book payloads for 04A/04B calls.

## Terminology
1. Turn pair: `T1` planning + `T2` execution for one chapter in one phase.
2. Chapter-local artifact: output authored for only target chapter.
3. Merged artifact: orchestrator-applied global state used for resume continuity.
4. Compact plan artifact: minimal explicit plan data persisted from T1.

## High-Level Architecture
Five subsystems:

### 1) Chapter Context Builder
Builds minimal input bundle for one chapter:
1. Target chapter in full
2. Compact neighbor handoff summaries:
   1. Previous chapter tail handoff summary (if exists)
   2. Next chapter head arrival summary (if exists)
3. Chapter-relevant registry slices only

Must not inject:
1. Full-book outline payload
2. Full prior phase payload where chapter-local subset is sufficient

### 2) Phase Prompt Compiler
Compiles phase and turn contract with chapter-only placeholders.

Compiler constraints:
1. Reject templates that do not contain chapter-scoped required tokens.
2. Reject templates that include forbidden full-book payload tokens for targeted steps.
3. Emit deterministic prompt-hash metadata.

### 3) Two-Turn Phase Runner
Runs `T1` then `T2` per chapter.

Turn pair behavior:
1. `T1` may use high reasoning and returns minimal visible output.
2. `T2` must emit strict schema-conformant chapter artifact.
3. On `T2` fail, retry `T2` with targeted fix list if plan artifact is still valid.
4. Preserve prior assistant content object exactly between `T1` and `T2` when continuity is attempted.
5. Never repack, trim, reorder, or reinterpret assistant parts during immediate `T1 -> T2` handoff.

### 4) Deterministic Gate
Checks:
1. Schema
2. Ref integrity
3. Chain invariants
4. Required report evidence blocks
5. Chapter scope invariants

Never does:
1. Semantic prose generation
2. Semantic fallback patching

### 5) Artifact Ledger
Stores both:
1. Raw chapter patch (exact model-authored chapter output)
2. Merged phase/chapter state (orchestrator assembled global outline)

This removes ambiguity between:
1. "what model wrote"
2. "what pipeline merged"

## Phase 04A Two-Turn Workflow

### 04A-T1 (Planning)
Goal:
1. Audit every adjacent scene edge in target chapter.
2. Classify alignment/misalignment and recommended seam handling.
3. Build candidate seam intent internally.

Output:
1. Minimal confirmation object only (ready/not-ready + counts + optional digest).
2. No full chapter rewrite output.

Persist:
1. Thought signature if returned by provider.
2. `04A_plan_compact.json` containing inspectable chapter-local planning summary.
3. Raw assistant `parts` block for exact replay into `T2` when immediate continuity is used.

### 04A-T2 (Execution)
Goal:
1. Emit chapter-local 04A artifact from planned intent.

Required output content:
1. `phase_report.edge_audit[]` for every adjacent edge in chapter.
2. `phase_report.candidate_seams[]` derived from audited edges.

Required edge audit fields:
1. `from_scene_ref`
2. `to_scene_ref`
3. `alignment_verdict` (`aligned|misaligned|uncertain`)
4. `mismatch_codes[]`
5. `recommended_resolution` (`inline_bridge|micro_scene|full_scene`)
6. `reason`

Mismatch code taxonomy (initial set):
1. `location_jump_unrealized`
2. `time_skip_unrealized`
3. `handoff_state_drop`
4. `objective_snap_unbridged`
5. `continuity_dependency_missing`
6. `anchor_flow_mismatch`
7. `post_insertion_chain_unreconciled`

Execution discipline:
1. `T2` is emit-focused, not context expansion.
2. `T2` input must remain chapter-local and must not add full-book payloads.
3. If continuity replay fails validation or provider rejects it, rerun `T1` and continue with explicit plan artifact path.

## Phase 04B Two-Turn Workflow

### 04B-T1 (Planning)
Input:
1. Target chapter full detail
2. Chapter-local selected seam candidates
3. Relevant chapter-local 04A edge audit
4. Compact neighbor context as needed

Goal:
1. Plan insertions and reconciliation touchpoints.
2. Produce touched scene-ref chain.

Output:
1. Minimal confirmation object only (ready/not-ready + touched refs summary).

Persist:
1. Thought signature if returned.
2. `04B_plan_compact.json` with touched refs and reconciliation checklist.
3. Raw assistant `parts` block for exact replay into `T2` when immediate continuity is used.

### 04B-T2 (Execution)
Goal:
1. Author required inserted scenes for selected insertion candidates.
2. Reconcile transition chain semantics around each insertion.

Insertion reconciliation requirement (A -> B with inserted X):
1. Rewrite `A.transition_out_text` and `A.transition_out_anchors`.
2. Author `X.transition_in_text` and `X.transition_in_anchors`.
3. Author `X.transition_out_text` and `X.transition_out_anchors`.
4. Rewrite downstream `B.transition_in_text` and `B.transition_in_anchors` to consume X.
5. Ensure chain refs are consistent after renumbering.

Required evidence block:
1. `phase_report.transition_reconciliations[]` listing:
   1. touched `scene_ref`
   2. updated field names
   3. reason for change

Execution discipline:
1. `T2` must execute declared touch-set and reconciliation checklist from `T1` artifact.
2. If execution touches refs outside declared scope, flag as drift and route targeted retry.
3. If continuity replay fails, rerun `T1` first; do not execute blind `T2`.

## Deterministic Validation Scope
Deterministic checks must remain structural.

### 04A validation
1. All adjacent edges audited for target chapter.
2. Edge refs are chapter-local and valid format.
3. Candidate seams map to audited edges.
4. Resolution enums and numeric bounds valid.

### 04B validation
1. All selected insertion candidates resolved or explicit terminal error.
2. Chain invariants valid after insertion:
   1. predecessor `hands_off_to`
   2. inserted `consumes_outcome_from` and `hands_off_to`
   3. successor `consumes_outcome_from`
3. Reconciliation evidence present for affected refs.
4. Required transition fields are present/non-empty on touched scenes.

Deterministic validator does not:
1. Decide whether prose is "good"
2. Author replacement transition text

## Thought Signature Policy
Thought signature is supported but treated as ephemeral.

### Reliability assumption
1. Continuity is most reliable for immediate next-turn continuation.
2. Continuity after pause/resume is not trusted as sole mechanism.
3. Long-pause signature reuse is explicitly non-authoritative for this workflow.

### Operational usage
1. Use thought signature in immediate `T1 -> T2` flow when available.
2. Always persist compact explicit plan artifact as fallback.
3. Preserve assistant parts losslessly when replaying continuity.
4. If thought signature missing/invalid or replay rejected:
   1. rerun `T1` for that chapter-phase pair, then run `T2`
   2. or drive `T2` from explicit plan artifact if sufficient by contract
5. Never parse/decode thought signature fields; treat as opaque bytes.

## Thought Signature Tracking and Replay
Thought signatures are required for continuity and must be tracked as first-class artifacts.

### Tracking requirements
1. Every model response must be inspected for thought signatures in assistant `parts`.
2. Each signature is stored with mandatory metadata:
   1. `request_id`
   2. `phase_id`
   3. `turn_id` (`T1` or `T2`)
   4. `chapter_id` (if chapter-scoped)
   5. `model`
   6. `thinking_level`
   7. `prompt_hash`
   8. `timestamp`
3. If multiple signatures appear in a single response:
   1. preserve their ordering and part association
   2. store each with `part_index` + `step_index` where applicable
4. Signature storage must be lossless; do not reformat or truncate.

### Signature ledger
Maintain a single append-only ledger per run:
1. `thought_signature_ledger.jsonl` (one record per signature)
2. `thought_signature_index.json` (latest-by-scope lookup)

Index requirements:
1. lookup by `phase_id + turn_id + chapter_id`
2. lookup by `request_id`
3. lookup for "global author signature" (see below)

### Global author signature (most recent action)
We will store the most recent author-phase signature as a global continuity handle:
1. record `scope = "global_author"`
2. update on each author action
3. optional usage as continuity seed in downstream prompts when explicitly enabled
4. never required for correctness; always best-effort

### Signature selection and replay
Provide a selectable replay mechanism:
1. CLI should list signatures by scope (phase/turn/chapter, or global author).
2. CLI should allow choosing a specific signature for a targeted replay attempt.
3. Replay always includes the original assistant parts, not just the signature.
4. Replay is immediate continuity only; long-pause reuse is opt-in and logged.

## "Tell Me Your Current Thoughts" Console Command
We need a console command that asks the model to reconstruct its active context without leaking chain-of-thought.

### Command behavior
1. Uses system + user prompt pairing.
2. Uses the most recent signature (or selected signature) as continuity input when possible.
3. Output is a structured "context summary," not hidden reasoning.

### Output schema (suggested)
1. `current_objectives[]`
2. `active_constraints[]`
3. `recent_decisions[]`
4. `assumptions[]`
5. `open_questions[]`
6. `recommended_next_steps[]`

### Safety rule
1. Do not request chain-of-thought or hidden reasoning.
2. Require concise, inspectable summary only.

## Resume and Checkpoint Contract
Turn pair is the checkpoint unit.

### Durable completion boundary
1. Mark chapter-phase as durable only after `T2` pass.

### Incomplete pair behavior
If paused/error after `T1` and before successful `T2`:
1. Pair is incomplete.
2. Resume starts at `T1` for that chapter-phase by default.
3. No assumption that hidden thought state survived pause.
4. Immediate-continuity replay path is only attempted in same operational window; otherwise force `T1` regeneration.

### Quota-aware scheduling
Before starting a new pair:
1. Verify estimated budget for `T1 + T2 + retry buffer`.
2. If insufficient, do not start pair.

## Artifact Model
For each chapter-phase pair:
1. `chapter_context_bundle.json`
2. `phase_04a_t1_plan_compact.json` or `phase_04b_t1_plan_compact.json`
3. `phase_04a_t1_assistant_parts.json` or `phase_04b_t1_assistant_parts.json` (lossless replay object when present)
4. `phase_04a_t2_chapter_patch.json` or `phase_04b_t2_chapter_patch.json`
5. chapter validation artifact
6. merged phase snapshot artifact
7. `thought_signature_ledger.jsonl`
8. `thought_signature_index.json`
9. `thought_signature_latest.json` (optional convenience pointer)

Reporting clarity requirement:
1. Keep chapter patch artifact and merged artifact side-by-side.
2. Surface both in phase report pointers.
3. Record continuity mode used for each pair:
   1. `signature_replay`
   2. `explicit_plan_fallback`
   3. `t1_regenerated`

## Context Minimization Rules
For targeted two-turn chapter phases:
1. Pass one target chapter in full.
2. Pass only compact neighbor context.
3. Pass only chapter-relevant registry slices.
4. Never pass full-book prior phase outputs.

Special 04B rule:
1. Do not pass full 04A global output; pass chapter-local selected candidates and relevant edge audit subset only.

## Retry Routing
1. Retry scope is chapter-local.
2. Retry payload includes only failing edges/fields.
3. Retry reason codes must be explicit in artifacts and console summary.
4. No silent downgrade or hidden fallback.

Pair-level retry rule:
1. Prefer `T2` retry only when `T1` plan artifact is still valid and drift-free.
2. If `T2` drift indicates stale or invalid planning intent, restart pair at `T1`.

## Extension Strategy for Other Phases
This same two-turn pattern can be applied where "reasoning" and "artifact emission" conflict.

Candidate phases:
1. Writing
2. Linting
3. Repair

Adoption gate:
1. Phase has high planning complexity and structured output risk.
2. Deterministic fallback artifact can be defined.
3. Added turn cost is acceptable.
4. Phase is compatible with signature tracking and replay without revealing hidden reasoning.

Extension template:
1. `P-T1`: plan-only minimal response + compact plan artifact.
2. `P-T2`: execute-only strict output from plan.
3. deterministic validation + targeted retry.

## Risks and Mitigations
1. Risk: turn cost increase.
   1. Mitigation: apply only to selected phases/chapters; keep payload small.
2. Risk: thought signature unavailable or rejected.
   1. Mitigation: explicit compact plan artifact fallback.
3. Risk: report inflation/duplicate entries on retries.
   1. Mitigation: chapter-keyed replacement semantics; rebuild aggregates from map.
4. Risk: semantic drift after insertion.
   1. Mitigation: mandatory reconciliation evidence and chain invariant checks.
5. Risk: T1 output bloat cancels two-turn value.
   1. Mitigation: enforce minimal T1 schema and reject oversized plan responses.
6. Risk: T2 replans due to oversized or irrelevant context.
   1. Mitigation: strict chapter-only context builder and payload caps.
7. Risk: continuity break due to assistant-part normalization.
   1. Mitigation: lossless assistant-part replay contract and artifacted raw parts.
8. Risk: model swap between T1 and T2 causes unstable continuity behavior.
   1. Mitigation: lock model and provider settings for entire pair.

## Acceptance Criteria
1. 04A/04B targeted calls are chapter-scoped in both prompt context and raw model output.
2. 04A emits edge audit for every adjacent edge and candidate seams derived from that audit.
3. 04B selected insertion candidates result in authored inserted scenes or explicit terminal error.
4. 04B insertion outputs include reconciliation evidence for all affected scene refs.
5. Resume logic treats incomplete turn pairs as non-durable and restarts safely from T1 unless equivalent explicit plan artifact path is valid.
6. No deterministic semantic autofill is introduced.
7. Immediate `T1 -> T2` continuity attempts preserve assistant parts losslessly.
8. When continuity is unavailable, explicit-plan fallback path produces equivalent contract-compliant output.
9. No long-pause dependency on hidden thought state is required for correctness.

## Rollout Sequence
1. Add thinking budget support + mutual-exclusion policy (budget vs level).
2. Implement Phase 03 two-turn runner (T1 plan + T2 emit) with per-turn thinking control.
3. Finalize contract docs for 04A-T1, 04A-T2, 04B-T1, 04B-T2.
4. Add artifact schema definitions for compact plan artifacts and reconciliation evidence.
5. Implement chapter context minimization and prompt payload restrictions.
6. Implement two-turn runner path for 04A/04B with checkpoint semantics.
7. Add deterministic validations and targeted retry routing.
8. Run chapter-level pilot on one book and compare:
   1. seam resolution quality
   2. orphan beat incidence
   3. retry rate
   4. token and turn consumption
9. If stable, evaluate adoption for writing/linting/repair using the same template.
