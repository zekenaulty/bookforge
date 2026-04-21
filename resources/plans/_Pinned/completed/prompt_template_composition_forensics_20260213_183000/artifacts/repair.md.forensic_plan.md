# Forensic Plan: repair.md

## Snapshot
- Source: `resources/prompt_templates/repair.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/repair.md.snapshot.md`
- SHA256: `D5F4DF4FEF7A604A8BD6EF36A4CC0D8DDCF95AA26AD3DBE3A0B8DBA65083DECC`
- Line count: `257`
- Byte length: `18703`

## Code Touchpoints
- `src/bookforge/workspace.py:47`
- `src/bookforge/phases/repair_phase.py:35`
- Parser/contract sensitivity:
  - `src/bookforge/pipeline/parse.py:70-88`
  - `src/bookforge/phases/repair_phase.py:66-125`
  - `src/bookforge/pipeline/state_patch.py:407`

## Intent Summary
`repair.md` is high risk because it can rewrite prose and patch under lint pressure. It must stay tightly aligned with schema constraints and state ownership rules.

## Detailed Change Plan (Span-Cited)

### Operation R01 - Preserve header and primary policy band
- Current span: `resources/prompt_templates/repair.md:1-54`
- Action: retain verbatim as phase-local block.
- New language: `NO TEXT CHANGE`.

### Operation R02 - Dedupe repeated must_stay_true reconciliation blocks
- Canonical source retained: `resources/prompt_templates/repair.md:8-10`
- Duplicate spans to remove:
  - `resources/prompt_templates/repair.md:55-58`
  - `resources/prompt_templates/repair.md:60-63`
  - `resources/prompt_templates/repair.md:65-68`
  - `resources/prompt_templates/repair.md:82-85`
  - `resources/prompt_templates/repair.md:87-90`
  - `resources/prompt_templates/repair.md:108-111`
  - `resources/prompt_templates/repair.md:134-137`
  - `resources/prompt_templates/repair.md:189-192`
  - `resources/prompt_templates/repair.md:194-197`
- Replacement strategy:
  - Keep canonical `B002.must_stay_true_reconciliation_block` once.
  - Remove duplicate copies.
- Canonical replacement text:
```text
- must_stay_true reconciliation (mandatory):
  - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - Remove conflicting old invariants rather than preserving them.
```

### Operation R03 - Preserve must_stay_true removal block
- Current span: `resources/prompt_templates/repair.md:11-14`
- Action: extract to `B003.must_stay_true_remove_block`.
- Replacement in composed output: exact same text.

### Operation R04 - Preserve scope override rule
- Current span: `resources/prompt_templates/repair.md:71-74`
- Action: extract to `B004.scope_override_nonreal_rule`.
- Replacement in composed output: exact same text.

### Operation R05 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/repair.md:120-122`
- Action: extract to `B006.global_continuity_array_guardrail`.

### Operation R06 - Preserve appearance updates object guardrails
- Current spans:
  - `resources/prompt_templates/repair.md:138-140`
  - `resources/prompt_templates/repair.md:174-176`
- Action: extract to `B008.appearance_updates_object_guardrail`.

### Operation R07 - Preserve transfer-vs-registry conflict block
- Current span: `resources/prompt_templates/repair.md:158-166`
- Action: extract to `B007.transfer_registry_conflict_rule`.
- Caution:
  - `resources/prompt_templates/repair.md:161` contains concatenated text due line wrap artifact.
  - Do not normalize wording in first migration pass.

### Operation R08 - Preserve JSON Contract Block
- Current span: `resources/prompt_templates/repair.md:233-251`
- Action: extract to `B005.json_contract_block`.

### Operation R09 - Preserve phase output contract region
- Current spans:
  - `resources/prompt_templates/repair.md:77-99`
  - `resources/prompt_templates/repair.md:101-232`
- Action: keep as phase-local composition blocks with no semantic edits.

## Proposed Composed Template Layout (Draft)
1. `repair/header_and_rules_v1`
2. `shared/must_stay_true_reconciliation_block`
3. `shared/must_stay_true_remove_block`
4. `repair/inventory_and_mechanics_v1`
5. `shared/scope_override_nonreal_rule`
6. `repair/output_contract_v1`
7. `repair/state_patch_rules_v1`
8. `shared/global_continuity_array_guardrail`
9. `shared/appearance_updates_object_guardrail`
10. `shared/transfer_registry_conflict_rule`
11. `shared/json_contract_block`

## Risk & Validation Notes
- Repair parse path must remain valid (`src/bookforge/phases/repair_phase.py:66-125`).
- Do not weaken JSON examples that currently prevent schema retries.
- Deduplication must not remove the only occurrence of any hard rule.

## Reviewer Checklist
- Verify every removed repeated reconciliation block is a duplicate of lines 8-10.
- Verify no unique contextual rule is accidentally removed near deduped spans.
- Confirm composed output remains parse-compatible with `PROSE:` + `STATE_PATCH:` extraction path.
