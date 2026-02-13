# Forensic Plan: state_repair.md

## Snapshot
- Source: `resources/prompt_templates/state_repair.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/state_repair.md.snapshot.md`
- SHA256: `8E8A1B56E9DEB467F32D3DDBA28C6DD827E27E50392580F75D7F76166181A010`
- Line count: `189`
- Byte length: `13505`

## Code Touchpoints
- `src/bookforge/workspace.py:48`
- `src/bookforge/phases/state_repair_phase.py:37`
- Parser/contract sensitivity:
  - `src/bookforge/phases/state_repair_phase.py:67-115`
  - `src/bookforge/pipeline/parse.py:_extract_json`
  - `src/bookforge/pipeline/state_patch.py:407`

## Intent Summary
`state_repair.md` is schema-critical. It is the last patch-shape checkpoint before lint and final apply.

## Detailed Change Plan (Span-Cited)

### Operation SR01 - Preserve top-level goal and must_stay_true rules
- Current span: `resources/prompt_templates/state_repair.md:1-18`
- Action: keep verbatim (phase-local).

### Operation SR02 - Preserve durable/ephemeral and UI gate region
- Current span: `resources/prompt_templates/state_repair.md:27-42`
- Action: keep verbatim; do not alter punctuation/keyword casing.

### Operation SR03 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/state_repair.md:68-70`
- Action: extract to `B006.global_continuity_array_guardrail`.

### Operation SR04 - Preserve appearance updates object guardrail
- Current span: `resources/prompt_templates/state_repair.md:83-85`
- Action: extract to `B008.appearance_updates_object_guardrail`.

### Operation SR05 - Preserve transfer-vs-registry conflict block
- Current span: `resources/prompt_templates/state_repair.md:103-111`
- Action: extract to `B007.transfer_registry_conflict_rule`.
- Caution:
  - `resources/prompt_templates/state_repair.md:106` contains concatenated text due formatting artifact; preserve text in first migration pass.

### Operation SR06 - Preserve scope override block
- Current span: `resources/prompt_templates/state_repair.md:119-122`
- Action: extract to `B004.scope_override_nonreal_rule`.

### Operation SR07 - Preserve JSON Contract Block
- Current span: `resources/prompt_templates/state_repair.md:163-181`
- Action: extract to `B005.json_contract_block`.

### Operation SR08 - Preserve all input placeholder sections
- Current span: `resources/prompt_templates/state_repair.md:123-161`
- Action: keep phase-local and verbatim.

## Proposed Composed Template Layout (Draft)
1. `state_repair/header_and_goal_v1`
2. `state_repair/rules_core_v1`
3. `shared/global_continuity_array_guardrail`
4. `shared/appearance_updates_object_guardrail`
5. `shared/transfer_registry_conflict_rule`
6. `shared/scope_override_nonreal_rule`
7. `state_repair/input_placeholders_v1`
8. `shared/json_contract_block`

## Risk & Validation Notes
- Must remain JSON-only output semantics (`src/bookforge/phases/state_repair_phase.py:67-90`).
- Any drift in guardrail examples can reintroduce schema retry churn.
- Keep canonical examples identical on first pass.

## Reviewer Checklist
- Confirm no rule-line loss in ranges `1-122`.
- Confirm all schema examples remain exactly present.
- Confirm composed output still enforces JSON-only output contract.
