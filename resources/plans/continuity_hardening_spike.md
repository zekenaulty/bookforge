# BookForge Continuity Hardening Spike Plan (Draft)

## Purpose
- Capture the drift/continuity issues observed in `workspace/books/starwrought_b1_v1/draft/chapters/ch_001.md` and define a focused hardening spike.
- Prioritize system-level prompt hardening and timeline/state enforcement, since system-level rules have proven more influential.
- Use this spike to decide whether to add a secondary continuity refinement phase.

## Scope (In)
- System instruction hardening (base/system prompts).
- Writer/repair prompt hardening (explicit timeline and state priority).
- Timeline enforcement rules and checks.
- State importance and invariant emphasis.
- Plan for a second-phase continuity refinement pass (design only, no implementation unless explicitly approved).

## Scope (Out)
- Major redesign of the generation pipeline.
- Thought-signature caching or explicit caching integration.
- Full prose post-editing or stylistic polish.

## Observed Issues (Chapter 1 Audit)
- Timeline contradictions (maps acquired before retrieval).
- Scene order drift vs outline (shadow-forms event order).
- Duplicate milestone events (shard binding happens twice).
- Arm-side swap for Oath filament/scarring.
- Inventory continuity gaps (longsword vs short-blade).
- Directional intent flip without transition (flee south vs return to Spire).
- Encoding/mojibake artifacts (non-ASCII degradation).

## Goals
- Enforce scene boundaries so a scene does not resolve events assigned to later scenes.
- Elevate state/invariants as hard constraints during writing and repair.
- Reduce event duplication (single-occurrence milestone enforcement).
- Improve consistency of injury/inventory/ownership details.

## Plan of Record (Prompt + System Hardening First)

### 1) System Instruction Hardening (Highest Priority)
- Add explicit Timeline Lock definition:
  - "Timeline Lock: You may only depict events explicitly listed in the current Scene Card. You must not depict, imply, or resolve any later-scene milestone outcomes (including acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone."
- Add State Primacy directive:
  - "State invariants and summary facts are binding; do not contradict them."
- Add Milestone Uniqueness directive:
  - "If a milestone is marked DONE in state/must_stay_true, you must not depict it happening again. If marked NOT_YET, you must not depict it happening now."
- Add Spatial/Inventory Consistency directive:
  - "Injuries, inventory, and ownership must remain consistent unless explicitly changed in the scene card."

### 2) Writer/Repair Prompt Hardening
- Echo the same timeline lock and state-primacy rules at prompt level.
- Include a compact milestone ledger in must_stay_true with standard phrasing:
  - "milestone: shard_bind = DONE/NOT_YET"
  - "milestone: maps_acquired = DONE/NOT_YET"
  - "milestone: shadow_form_first = DONE/NOT_YET"
- Include a compact list of must-stay-true invariants (arm-side, inventory weapon type, ownership flags).
- Add a direct instruction: "If a required event is not in the current scene card, do not perform it."
- Require a short preflight compliance block before prose (not hidden reasoning):
  - Scene ID
  - Allowed events (from scene card)
  - Forbidden milestones (from must_stay_true)
  - Current arm-side / inventory facts
- Clarify output contract: prose is required; state_patch must include invariant reinforcement.

### 3) Timeline Enforcement Checks (Non-LLM)
- Add deterministic tripwires tied to known failures (warn-first):
  - Duplicate milestone check (DONE -> reject if prose re-binds/re-acquires).
  - NOT_YET acquisition check (maps/shard acquisition keywords).
  - Arm-side invariant check (left/right + filament/scar/oath).
  - Weapon/inventory check (longsword vs short-blade mismatch).
- Mojibake/encoding check (reject if contains U+FFFD or common mojibake byte sequences, e.g., U+00C3 U+00A2 U+0080 U+0094 for em dash, U+00C3 U+00A2 U+0080 U+0099 for right quote).
- Implement a minimal regex-based "future-event" check using the outline window.

### 4) State Importance Enhancements
- Extend state summaries with explicit milestones and inventory/injury flags (design only).
- Ensure must_stay_true includes timeline-critical facts with standard phrasing for regex gating.
- Promote those facts in continuity pack and writer prompts.

### 5) Optional: Second-Phase Continuity Refinement (Design Only)
- Add a state refinement pass after write/repair:
  - Compare scene output to invariants and outline current scene.
  - Repair or annotate drift (event duplication, inventory swaps).
- Keep this optional until prompt hardening is validated.

## Definition of Done
- System/base prompts include timeline lock + state primacy + milestone uniqueness (with explicit milestone syntax).
- Writer/repair prompts include enforcement lines, milestone ledger, and preflight compliance block.
- Deterministic tripwire list is documented with warn-first policy and a path to hard-fail for critical items.
- A clear decision is documented on whether to implement the second-phase refinement step.
- A short checklist exists for validating drift reduction on a single chapter rerun.

## Open Questions
- Should timeline lock be enforced strictly (hard fail) or warn-first?
- Do we want a strict schema field for inventory/injury location, or keep it in must_stay_true?
- Should outline be injected into system prompt for writer by default (already optional/added)?

## Suggested Test
- Reset book to post-outline state, re-run Chapter 1, and audit:
  - maps acquired early: no
  - shard-binding duplicated: no
  - oath filament arm swapped: no
  - weapon swapped: no
  - shadow-form order drift: no
  - mojibake artifacts: no

## Stories

### Story CHS-1: System Instruction Hardening
Goal
- Make timeline lock and state primacy unambiguous at system level.

Scope
- Add explicit timeline lock definition (allowed vs disallowed).
- Add milestone uniqueness rules with DONE/NOT_YET semantics.
- Add state primacy + spatial/inventory consistency rules.

Definition of Done
- System/base prompt includes the exact timeline lock and milestone rules.
- System rules are phrased as hard constraints (non-negotiable).
- No pipeline logic changes are required for this story.

### Story CHS-2: Writer/Repair Prompt Hardening
Goal
- Force writer/repair to bind to scene scope and invariants before prose.

Scope
- Add milestone ledger format guidance in must_stay_true.
- Add preflight compliance block requirement.
- Reiterate: do not depict non-scene milestones.

Definition of Done
- Writer and repair prompts include preflight block requirements.
- Writer and repair prompts include milestone ledger guidance.
- Example prompt snippet shows required ordering: preflight -> prose -> state_patch.

### Story CHS-3: Deterministic Tripwire Checks (Warn-First)
Goal
- Catch the highest-signal drift errors without NLP complexity.

Scope
- Define regex tripwires for milestone duplication, NOT_YET acquisition, arm-side mismatch, weapon mismatch, mojibake.
- Specify warn-first behavior and escalation to hard fail for critical items.

Definition of Done
- Tripwire list is documented with exact keyword sets per invariant.
- Each tripwire has a pass/fail rule and escalation rule.
- Test checklist maps 1:1 to tripwires.

### Story CHS-4: State Importance Enhancements (Design Only)
Goal
- Specify how milestones/inventory/injury facts live in state for this spike.

Scope
- Standard phrasing for milestone/inventory/injury entries in must_stay_true.
- Define how these are promoted into continuity pack and prompts.

Definition of Done
- Standard phrasing examples documented (ASCII-safe).
- Decision recorded: keep in must_stay_true for this spike.

### Story CHS-5: Optional Second-Phase Refinement Decision
Goal
- Decide whether a second-phase refinement is needed after prompt hardening.

Scope
- Evaluate one rerun with hardened prompts + tripwires.
- If drift persists, define the minimal refinement pass scope.

Definition of Done
- Written decision: adopt or defer second-phase refinement.
- If adopted, a minimal design outline is added (no implementation).
