# Forensic Plan: preflight.md

## Snapshot
- Source: `resources/prompt_templates/preflight.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/preflight.md.snapshot.md`
- SHA256: `1275EE1E33A36D57D417B26DBDB413DB6CA691B5EE58F6C55F8E088C2AD9C2FE`
- Line count: `224`
- Byte length: `13545`

## Code Touchpoints
- `src/bookforge/workspace.py:44`
- `src/bookforge/phases/preflight_phase.py:32`
- Runtime coupling:
  - `src/bookforge/phases/preflight_phase.py:36-71`
  - `src/bookforge/runner.py:604-639`
  - `src/bookforge/pipeline/state_patch.py:_sanitize_preflight_patch`

## Intent Summary
`preflight.md` performs initial state alignment and durable mutation gating before write. Composition changes must preserve conservative mutation behavior and scope override logic.

## Detailed Change Plan (Span-Cited)

### Operation PF01 - Preserve preflight role and hard rules section
- Current span: `resources/prompt_templates/preflight.md:1-22`
- Action: keep verbatim (phase-local).

### Operation PF02 - Preserve scope override rule
- Current span: `resources/prompt_templates/preflight.md:23-26`
- Action: extract to `B004.scope_override_nonreal_rule`.

### Operation PF03 - Preserve transition gate logic
- Current span: `resources/prompt_templates/preflight.md:27-42`
- Action: keep phase-local and verbatim.

### Operation PF04 - Preserve world/inventory alignment policy
- Current span: `resources/prompt_templates/preflight.md:43-79`
- Action: keep phase-local and verbatim.

### Operation PF05 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/preflight.md:99-101`
- Action: extract to `B006.global_continuity_array_guardrail`.

### Operation PF06 - Preserve transfer-vs-registry conflict block
- Current span: `resources/prompt_templates/preflight.md:115-118`
- Action: extract to `B007.transfer_registry_conflict_rule`.
- Caution:
  - `resources/prompt_templates/preflight.md:118` includes concatenated suffix (`- Safety check...`).
  - Preserve exact text first pass; normalization is a separate approved pass.

### Operation PF07 - Preserve JSON Contract Block
- Current span: `resources/prompt_templates/preflight.md:135-153`
- Action: extract to `B005.json_contract_block`.

### Operation PF08 - Preserve example output block
- Current span: `resources/prompt_templates/preflight.md:179-217`
- Action: keep phase-local and verbatim.

## Proposed Composed Template Layout (Draft)
1. `preflight/header_and_hard_rules_v1`
2. `shared/scope_override_nonreal_rule`
3. `preflight/transition_gate_v1`
4. `preflight/inventory_and_constraints_v1`
5. `shared/global_continuity_array_guardrail`
6. `shared/transfer_registry_conflict_rule`
7. `shared/json_contract_block`
8. `preflight/input_placeholders_and_examples_v1`

## Risk & Validation Notes
- Preflight mutations flow directly into runner state apply (`src/bookforge/runner.py:626-633`).
- Wording drift can alter LLM mutation aggressiveness and produce pauses.
- Preserve the exact conservative/continuation heuristics in lines `27-42`.

## Reviewer Checklist
- Verify no change in scope gating language.
- Verify durable mutation block definition remains unchanged.
- Verify example JSON remains schema-consistent.
