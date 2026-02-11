# BookForge Implementation Plan v3 (Draft)

Objective
- Preserve the thin‑engine philosophy while hardening durability, continuity, and schema‑correct prompting.
- Align the plan with the current system state: phases, durable registries, scope policy, and appearance system.
- Restore missing pipeline targets from v2 (preview gate, duplication checks, compile/export, logging) without regressions.


Testing Constraints
- Daily scene budget: ~10 scenes/day due to 20‑turn cap and per‑phase consumption.
- Use long CLI timeouts (45–60 minutes) to avoid killing slow phases (repair/state_repair can exceed 10 minutes).
- Record start/end timestamps and total runtime per scene.

Execution and Testing Artifacts (required)
- All work on this plan must be logged under a dedicated folder:
  - resources/plans/bookforge_plan_v3/
    - steps/steps_YYYYMMDD_HHMM_<slug>.md
    - testing/test_YYYYMMDD_HHMM_<slug>.md
- Each test run must include:
  - Command executed (full CLI invocation)
  - Start/end timestamps
  - Scene range attempted
  - Outcome summary (pass/fail + error)
  - Linked log files (workspace/logs/llm/*)
  - Follow‑up actions taken
- Scene‑by‑scene test loops are required for Story 0 and any story that modifies prompt shapes.

Definition of Done (v3)
- CLI supports: init, author generate, outline generate, characters generate, run, compile, export synopsis, book set/show/clear/reset/update-templates.
- LLM provider selection via .env with per‑phase models and API keys.
- Workspace layout matches resources/initial_concept.md and includes series‑level canon scaffolding.
- Prompt system uses stable system prompt + per‑phase templates, with deterministic payload ordering and budget reporting.
- Prompt schema hardening is implemented across preflight/write/repair/state_repair/lint/system_base with a shared JSON Contract Block.
- Continuity pack is generated per scene and is facts‑only (no prose), with consistent scope handling.
- Preflight alignment exists and enforces scope policy (timeline/ontology), durable constraints, and posture alignment.
- Durable registries (item_registry, plot_devices) with transfer semantics, expected_before preconditions, commit ledger, and snapshots.
- Durable Character Appearance System (DCAS) is live: appearance_base in canon, appearance_current/history in runtime, APPEARANCE_CHECK authoritative surface, and projection refresh.
- Lint/repair loop runs end‑to‑end with pipeline coherence guardrails and timeline reasoning.
- Opening preview gate + similarity/duplication checks exist and are enforced before commit.
- Compile/export implementations produce manuscript and synopsis from stored artifacts.
- Logging and prompt hash traceability exist per phase; prompt registry snapshots are stored per run.
- Tests cover schema validation, budgeter, continuity, durable registries, appearance, lint/repair, and compilation ordering.

Scope
In scope:
- CLI orchestration and workspace semantics.
- Provider abstraction and per‑phase model config.
- Prompt templates, registry, stable prefix caching, and budget reporting.
- Author library and versioned author artifacts.
- Outline generation, scene planning, run loop with preflight/write/repair/state_repair/lint.
- Durable inventory and plot device registries + transfers.
- DCAS appearance system.
- Compile/export commands.
- Logging, metrics, and test coverage.

Out of scope
- Web UI or external DB/vector store.
- Cross‑book continuity engine (future).
- Full plagiarism detection beyond self‑dup checks.

Design Principles
- State is authoritative; continuity pack is derived.
- Durable state changes must be explicit in patches; no prose inference.
- Prompt contracts are treated like code: over‑specified JSON shapes, shared across phases.
- Scope policy is explicit: non‑real/non‑present requires override for physical mutations.
- Lint favors precision: must prove durable violation or emit pipeline_state_incoherent.

Architecture Snapshot (current)
- Phases: plan, preflight, continuity_pack, write, repair, state_repair, lint.
- Pipeline modules: prompts, parse, durable, state_apply, lint helpers.
- Durable registries: item_registry.json, plot_devices.json + snapshots and ledger.
- DCAS: appearance_current/history, APPEARANCE_CHECK, projection refresh.

Key Additions vs v2
- Preflight alignment phase with scope gating.
- Durable registries + transfer semantics + preconditions.
- Prompt schema hardening (JSON Contract Block across phases).
- DCAS appearance system.
- Pipeline coherence guard in lint.

Missing vs v2 (to implement in v3)
- Opening preview gate + banned phrases + similarity checks.
- Compile/export implementations (CLI stubs exist).
- Prompt registry snapshots + logging completeness.
- Word/page count enforcement.

Story Map (v3)

Story 0: Prompt Schema Hardening
- Enforce JSON Contract Block across all phases (global + book overrides).
- Transfer vs registry conflict rules.
- Scope override decision clarity.
- Lint pipeline_state_incoherent guard + timeline reasoning.

Story 1: Preflight Alignment v2
- Full scope‑aware posture alignment and durable constraint enforcement.
- Required override rules for non‑real transitions.
- Expected_before guidance for transfers.

Story 2: Durable Registries + Transfers
- item_registry + plot_devices fully enforce required fields.
- Transfer updates with expected_before and commit ledger.
- Snapshot history for durable registries.

Story 3: DCAS Appearance System
- appearance_base in canon character.json.
- appearance_current/history in runtime character state.
- APPEARANCE_CHECK authoritative surface.
- Projection refresh after accepted scenes.

Story 4: Write/Lint/Repair Loop Improvements
- Durable change ledger in write compliance.
- Lint timeline reasoning + last occurrence canonicalization.
- Repair/state_repair forced to reconcile durable changes explicitly.

Story 5: Opening Preview + Duplication Gates
- Implement preview gate (tagged block, stripped on commit).
- Banned phrase extraction and injection.
- Similarity checks for openers and n‑grams.

Story 6: Compile + Export
- Compile manuscript ordering.
- Export synopsis generation.

Story 7: Logging + Prompt Registry Snapshot
- Prompt hash logs per phase.
- Prompt registry snapshots per run.

Story 8: Tests + Docs
- Coverage for durable registry updates, preflight, DCAS, and lint coherence.
- Update docs/help to reflect durable systems + schema contracts.


Story Details (v3)

Story 0: Prompt Schema Hardening
Purpose
- Make every phase prompt explicitly conform to the schema rules enforced by validators.
- Eliminate repeat JSON shape failures (array vs object, missing required keys, invalid custodian).

Scope and Constraints
- Applies to: system_base, preflight, write, repair, state_repair, lint templates.
- No code changes; prompt text only. Must remain stable across global and per‑book overrides.

Implementation Tasks
- Create a shared JSON Contract Block and paste into each phase prompt.
- Explicitly document transfer vs registry conflict rules (new item custody vs transfer).
- Clarify scope override decision logic in preflight (non‑present/non‑real).
- Add durable change ledger requirement in write compliance.
- Add pipeline_state_incoherent guardrails + canonical target declarations in lint.

Inputs
- state_patch schema + validator rules.
- Known failure logs (array/object mismatches, precondition conflicts).

Outputs
- Phase prompts with explicit VALID/INVALID examples.
- Drift checklist for global vs local overrides.

Edge Cases to Address
- New items + transfer_updates in same patch.
- Non‑real scenes that are story‑real (System Void).
- Appearance updates accidentally emitted as array.

Acceptance Criteria
- Repeated JSON shape failures disappear in preflight/write/repair/state_repair.
- Transfer/registry conflicts no longer trigger expected_before mismatch.

Story 1: Preflight Alignment v2
Purpose
- Ensure preflight alignment produces valid, scope‑aware patches that set up the next scene without mutating canon incorrectly.

Scope and Constraints
- Must respect scene_card scope (timeline/ontology) and durable constraints.
- Preflight is not a writing step; must avoid inventing prose‑driven state.

Implementation Tasks
- Codify decision gates: continuation vs discontinuous transitions.
- Enforce durable constraints in preflight with deterministic posture alignment.
- Require scope_override on physical updates when scope is non‑present/non‑real but continuity demands physical state.
- Add expected_before guidance for all custody or container changes.

Inputs
- scene_card (scope, constraints), state, character_states, registries.

Outputs
- State_patch‑compatible JSON with valid inventory/registry updates.

Edge Cases to Address
- Transition into realm that is “non‑real” but canon‑real.
- Items required_in_custody but currently not in visible containers.
- Custody change implied without transfer_updates.

Acceptance Criteria
- Preflight never fails schema validation.
- Scope policy only blocks updates when no override is justified.

Story 2: Durable Registries + Transfers
Purpose
- Make item_registry and plot_devices the authoritative durable objects with explicit custody transfer semantics.

Scope and Constraints
- Registry updates must be explicit and validated; transfers must honor expected_before.

Implementation Tasks
- Ensure registry update required fields are always present.
- Enforce transfer update consistency with registry entries.
- Maintain durable commit ledger + snapshots.

Inputs
- item_registry.json, plot_devices.json, transfer_updates.

Outputs
- Durable registry updates and ledger entries per scene.

Edge Cases to Address
- New item with final custodian plus transfer conflict.
- Tombstone/retirement updates and re‑introduction.
- Transfer chain ordering in same patch.

Acceptance Criteria
- No precondition mismatch when transfer rules are followed.
- Durable registries stay consistent across reruns.

Story 3: DCAS Appearance System
Purpose
- Maintain durable, canonical appearance state per character, without brittle prose enforcement.

Scope and Constraints
- Appearance_current atoms/marks are canonical; summary/projection is derived.

Implementation Tasks
- Ensure appearance_base exists in canon character.json.
- Seed appearance_current/history in runtime state on first use.
- Add APPEARANCE_CHECK authoritative surface in write/lint.
- Add projection refresh after accepted scenes (no atom/mark mutation from projection).

Inputs
- Canon character definitions, character states.

Outputs
- Stable appearance_current + history; validated APPEARANCE_CHECK.

Edge Cases to Address
- Temporary dirt/lighting should not mutate atoms/marks.
- Durable changes (scar, haircut) must be explicit and go through appearance_updates.

Acceptance Criteria
- Lint flags only authoritative appearance contradictions, not metaphor.
- Appearance consistency holds across scenes.

Story 4: Write/Lint/Repair Loop Improvements
Purpose
- Make the loop resilient: durable changes are explicit, lint uses timeline reasoning, repair can reconcile without drift.

Scope and Constraints
- Lint must use post‑state candidate as canonical, with pipeline incoherence guard.
- Repair/state_repair must not “freeze” real changes due to pre‑state primacy.

Implementation Tasks
- Add durable change ledger in write compliance.
- Enforce last‑occurrence‑wins for in‑scene UI values.
- Require evidence for lint failures and avoid early‑stop errors.

Inputs
- Prose, pre/post state, continuity pack, patch.

Outputs
- Validated scenes that match durable state.

Edge Cases to Address
- Transitional UI snapshots that self‑correct.
- Incoherent pre/post state causing false lints.

Acceptance Criteria
- Lint fails only when durable violations persist to end of scene.
- Repair/state_repair emits schema‑valid patches.

Story 5: Opening Preview + Duplication Gates
Purpose
- Prevent repetitive openings and content duplication before committing scenes.

Scope and Constraints
- Preview must be tag‑wrapped and stripped from final scene.

Implementation Tasks
- Implement preview gate; evaluate for novelty and cadence.
- Extract banned phrases and inject into write prompt.
- Similarity checks across openers and n‑grams.

Inputs
- Prior scenes, preview text, current scene draft.

Outputs
- Approved openings; rejected drafts are rerun.

Edge Cases to Address
- False positives on stylistic phrases.
- Very short scenes where preview and body overlap.

Acceptance Criteria
- Openers do not repeat; similarity thresholds enforced before commit.

Story 6: Compile + Export
Purpose
- Produce manuscript and synopsis outputs from stored artifacts.

Scope and Constraints
- Order is canonical; no missing scenes.

Implementation Tasks
- Implement compile command using chapter/scene ordering.
- Implement export synopsis using outline + scene meta.

Inputs
- Draft chapters/scenes, outline.json, scene_meta.

Outputs
- manuscript.md, synopsis.md.

Acceptance Criteria
- Compile/export commands run end‑to‑end and produce correct ordering.

Story 7: Logging + Prompt Registry Snapshot
Purpose
- Ensure traceability of prompts, budgets, and schema evolution.

Scope and Constraints
- Snapshot prompt registry per run; log hashes per phase.

Implementation Tasks
- Log prompt hashes, budgets, and model metadata.
- Snapshot registry.json in run logs.

Edge Cases to Address
- Local overrides diverge from global without being logged.

Acceptance Criteria
- Every run has prompt hash and registry snapshot artifacts.

Story 8: Tests + Docs
Purpose
- Ensure durability and correctness across schema and pipeline changes.

Scope and Constraints
- Tests must reflect new durable registries and DCAS.

Implementation Tasks
- Add tests for registry updates, preflight alignment, DCAS, lint coherence.
- Update docs/help with durable systems and schema contract rules.

Acceptance Criteria
- Tests pass; docs reflect actual CLI behavior.
Definition of Done by Story (condensed)
- Story 0: Shared JSON Contract Block exists in all phase prompts + book overrides.
- Story 1: Preflight emits valid patches and passes scope policy in non‑real scenes.
- Story 2: Durable updates validated, logged, and reproducible.
- Story 3: Appearance consistency enforced without prose brittleness.
- Story 4: Lint failures only on durable violations or pipeline incoherence.
- Story 5: Preview gate and similarity checks prevent duplication.
- Story 6: Compile/export commands produce artifacts from scene files.
- Story 7: Logs include prompt hashes, budgets, registry snapshots.
- Story 8: Tests pass and docs match actual CLI behavior.

Rerun and Override Semantics
- Each phase declares mutation behavior (immutable, append‑only, rewrite‑with‑archive).
- Reset clears draft outputs but preserves canon/series data.
- Book template updates are explicit via book update‑templates.

Observability and Metrics
- Log prompt hashes, model info, token estimates, registry snapshots, and budget outcomes.
- Record lint/repair failure counts and reasons.

Dependencies / External Plans
- series_continuity_plan.md (still outstanding; should be integrated after v3 stabilization).
- proposed/chatgpt_suggested_wins.md (integrate where it aligns with v3 stories).




