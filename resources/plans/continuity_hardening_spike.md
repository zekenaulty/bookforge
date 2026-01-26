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
- Multi-turn thought-signature caching or explicit caching integration.
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
- Add a **Timeline Lock** directive at system level:
  - “Only write events assigned to the current scene. Do not resolve future-scene outcomes.”
- Add a **State Primacy** directive:
  - “State invariants and summary facts are binding; do not contradict them.”
- Add a **Milestone Uniqueness** directive:
  - “Do not repeat milestone events (e.g., binding the shard) if already marked in state.”
- Add a **Spatial/Inventory Consistency** directive:
  - “Injuries, inventory, and ownership must remain consistent unless explicitly changed in the scene card.”

### 2) Writer/Repair Prompt Hardening
- Echo the same timeline lock and state-primacy rules at prompt level.
- Include a compact list of **must-stay-true invariants** (e.g., shard bound, maps not yet acquired, oath filament arm).
- Add a direct instruction: “If a required event is not in the current scene card, do not perform it.”
- Clarify output contract: prose is required; state_patch must include invariant reinforcement.

### 3) Timeline Enforcement Checks (Non-LLM)
- Add a deterministic validation step:
  - If prose mentions outcomes tagged for later scenes, flag or reject.
- Implement a minimal regex-based “future-event” check using the outline window.

### 4) State Importance Enhancements
- Extend state summaries with explicit **milestones** and **inventory** flags (design only).
- Ensure “must_stay_true” includes timeline-critical facts.
- Promote those facts in continuity pack and writer prompts.

### 5) Optional: Second-Phase Continuity Refinement (Design Only)
- Add a “state refinement” pass after write/repair:
  - Compare scene output to invariants and outline current scene.
  - Repair or annotate drift (e.g., event duplication, inventory swaps).
- Keep this optional until prompt hardening is validated.

## Definition of Done
- System/base prompts include timeline lock + state primacy + milestone uniqueness.
- Writer/repair prompts include explicit enforcement lines + invariant emphasis.
- A clear decision is documented on whether to implement the second-phase refinement step.
- A short checklist exists for validating drift reduction on a single chapter rerun.

## Open Questions
- Should “timeline lock” be enforced strictly (hard fail) or warn-first?
- Do we want a strict schema field for inventory/injury location, or keep it in must_stay_true?
- Should outline be injected into system prompt for writer by default (already optional/added)?

## Suggested Test
- Reset book to post-outline state, re-run Chapter 1, and audit:
  - No early map acquisition.
  - Single shard-binding event.
  - Consistent Oath filament arm.
  - Shadow-form ordering matches outline.

