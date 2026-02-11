# Prompt Schema Hardening Plan

Purpose
Create a disciplined, over-specified prompt contract that prevents repeat JSON/schema failures across phases (preflight/write/repair/state_repair/lint). This is a meta‑repair: we are hardening the phase that repairs state by making its own schema usage explicit and self‑checked.

Principles (Non‑Negotiable)
- Over‑specify, do not under‑specify: every JSON shape used by a phase must be spelled out in the prompt with VALID/INVALID examples.
- Shared contract: the same JSON rules must appear in every phase that can emit those fields.
- Deterministic behavior: any “decision” language must map to a concrete, required action (e.g., set scope_override when the story requires it).
- Schema alignment first, style second: prose quality is secondary to producing a valid patch and consistent canon.

Meta‑Note (the irony)
We are repairing the state management logic of a phase meant to repair state. That means prompts must be treated like code: explicit contracts, versioned, and cross‑checked against validators.

Scope
In scope:
- Prompt contracts for: `preflight`, `write`, `repair`, `state_repair`, `lint`, and `system_base`.
- JSON shapes for: `character_updates`, `character_continuity_system_updates`, `global_continuity_system_updates`, `inventory_alignment_updates`, `item_registry_updates`, `plot_device_updates`, `transfer_updates`, `appearance_updates`.
- Enforcement guidance for scope overrides, expected_before, custody rules, and transfer semantics.

Out of scope (for this plan)
- Engine refactors.
- Schema or code changes (except as follow‑up tasks in later plans).

Definition of Done
- All phases include a consistent “JSON Contract Block” with VALID/INVALID examples for every JSON structure they can emit.
- All phases explicitly describe action triggers that map to validator requirements (e.g., when to set scope_override).
- The known recurring failures are explicitly addressed in prompts (array vs object; transfer vs registry conflicts; expected_before mismatch).
- Lint instructions include pipeline‑incoherence guardrails and require evidence for any failure.
- A prompt delta checklist exists to prevent drift across phases (copy/paste‑safe canonical block).

Story Track
S1. Canonical JSON Contract Block (shared snippet)
S2. Preflight: scope override and transfer/registry conflict rule
S3. Write: end‑state ledger + durable update obligation
S4. Repair/State Repair: end‑of‑scope reasoning + patch consistency
S5. Lint: temporal scope, pipeline‑incoherent guard, evidence requirements
S6. Phase Drift Prevention: update checklist + prompt auditing steps

Status Tracker
- S1: completed (JSON contract block added to global + criticulous_b1 overrides) — define shared JSON contract block and examples
- S2: completed (preflight conflict + scope override rule added) — add preflight conflict avoidance rules (registry vs transfer)
- S3: completed (write durable change ledger + conflict rule + contract block) — require durable change ledger and end‑state canonicalization
- S4: completed (repair/state_repair updated with conflict rule + contract block) — enforce repair alignment with “last occurrence wins” and schema rules
- S5: completed (lint guardrail + canonical target clarification) — add pipeline_state_incoherent guard and evidence‑cited errors
- S6: pending (override template sync + drift checklist) — add prompt drift checklist and local override verification

Plan Detail

S1. Canonical JSON Contract Block
Goal: One block to paste into all phases.
Content must include:
- Explicit “arrays only” rules for *_updates.
- INVALID vs VALID example pairs for:
  - item_registry_updates
  - plot_device_updates
  - transfer_updates
  - inventory_alignment_updates
  - appearance_updates (object, not array)
- Required fields for each block.
- Non‑null custodian rule.

S2. Preflight Hard Rules
Add a “Transfer vs Registry Conflict” rule:
- If you create a new item in item_registry_updates with a final custodian, do NOT emit transfer_updates for that item.
- If you emit transfer_updates, the registry entry must be created with custodian=world and then transferred.
- expected_before must match the registry entry at the time of transfer.

Add a “Scope Override Decision” rule:
- If the scene is non‑present or non‑real but items must persist into the next real scene, then you MUST set scope_override=true (or allow_non_present_mutation=true) on each affected update.

S3. Write: Durable End‑State Ledger
Add a small compliance sub‑block:
- “Durable changes committed:” list of final values that must appear in continuity updates.
- End‑state is canonical: if UI shows multiple values, last occurrence wins.

S4. Repair/State Repair: Non‑Ambiguous Canon
Add:
- “Do not leave durable change only in prose.”
- “If patch contains transfer_updates and registry_updates, enforce the transfer/registry conflict rule.”
- “Appearance updates must be an object (not array) and must only touch atoms/marks.”

S5. Lint: Pipeline Incoherence Guard
Add explicit guard:
- If post‑state candidate contradicts must_stay_true or other post‑invariants, emit a single pipeline_state_incoherent error and stop.
- Any continuity failure must cite both the conflicting claim and the end‑of‑scene canonical claim.

S6. Prompt Drift Prevention
Create a short checklist:
- Confirm JSON Contract Block matches current schema.
- Confirm override templates updated (book prompts in workspace) after global changes.
- Confirm per‑phase local overrides are in sync.

Risks & Edge Cases
- New JSON shapes will keep appearing; without a shared contract block, drift will recur.
- Scene card scope ambiguity (non‑real but canon‑real) will continue causing drop/override issues if not explicitly handled in preflight.
- Transfer preconditions will continue failing unless conflict rule is explicit.

Validation Plan (No code changes here)
- Run 1 full chapter with strict prompt JSON contracts.
- Inspect preflight JSON for items created + transfer semantics.
- Verify no schema failures for array vs object.

Notes (Integration Discipline)
- Keep logic in phase‑specific modules; do not expand runner.py after lift‑and‑shift.
- Any new JSON shape requires immediate prompt update across all phases that can emit it.


Edge Cases Observed (capture; do not halt work)
- Transfer vs registry conflict: creating a new item with final custodian AND emitting transfer_updates causes expected_before mismatch. Prompt now forces either registry-only or world->transfer flow.
- Existing item custodian change: if an item already exists and custody changes, use transfer_updates (not registry-only) to avoid silent ownership drift.
- Non-real but story-real transitions (e.g., System Void): preflight must explicitly set scope_override on physical updates when story continuity requires it.
- New item + transfer: registry custodian must be "world" prior to transfer; otherwise omit transfer_updates.
