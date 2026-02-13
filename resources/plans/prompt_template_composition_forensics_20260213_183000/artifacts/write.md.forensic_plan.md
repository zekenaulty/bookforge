# Forensic Plan: write.md

## Snapshot
- Source: `resources/prompt_templates/write.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/write.md.snapshot.md`
- SHA256: `898B8FCFA1997DE8C7BCDF0636E462EA52064D627E2257C3DF644725443888F4`
- Line count: `237`
- Byte length: `18254`

## Code Touchpoints
- `src/bookforge/workspace.py:45`
- `src/bookforge/phases/write_phase.py:35`
- Parser/contract sensitivity:
  - `src/bookforge/pipeline/parse.py:70-88`
  - `src/bookforge/phases/write_phase.py:73-125`
  - `src/bookforge/pipeline/state_patch.py:407`

## Intent Summary
`write.md` is the highest-risk phase template for composition migration because it drives:
- Prose + patch dual-output formatting
- State patch schema compliance downstream
- Durable mutation rules later enforced by lint/state apply

Any wording drift here can create direct runtime failures.

## Detailed Change Plan (Span-Cited)

### Operation W01 - Keep Core Header and Phase Contract Verbatim
- Current span: `resources/prompt_templates/write.md:1-10`
- Action: move verbatim into phase block `resources/prompt_blocks/phase/write/header_v1.md`
- Replacement in composed output: exact same text.
- New language: `NO TEXT CHANGE`.

### Operation W02 - Dedupe repeated must_stay_true end-truth line
- Canonical source line retained: `resources/prompt_templates/write.md:11`
- Duplicate spans to remove:
  - `resources/prompt_templates/write.md:24`
  - `resources/prompt_templates/write.md:65`
  - `resources/prompt_templates/write.md:68`
  - `resources/prompt_templates/write.md:71`
  - `resources/prompt_templates/write.md:81`
  - `resources/prompt_templates/write.md:105`
  - `resources/prompt_templates/write.md:155`
  - `resources/prompt_templates/write.md:158`
  - `resources/prompt_templates/write.md:194`
  - `resources/prompt_templates/write.md:197`
- Replacement strategy:
  - Keep canonical block `B001.must_stay_true_end_truth_line` once in primary policy section.
  - Delete duplicate occurrences with no replacement text.
- Replacement text (canonical):
```text
- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
```
- Semantic intent: unchanged; redundancy removed.

### Operation W03 - Preserve must_stay_true removal block as shared block
- Current span: `resources/prompt_templates/write.md:12-15`
- Action: extract into shared block `B003.must_stay_true_remove_block`
- Replacement in composed output: exact same text.

### Operation W04 - Preserve inventory posture reconciliation block
- Current span: `resources/prompt_templates/write.md:18-23`
- Action: extract into shared block `resources/prompt_blocks/shared/inventory_posture_reconciliation_v1.md`
- Replacement in composed output: exact same text.

### Operation W05 - Preserve scope override rule as shared block
- Current span: `resources/prompt_templates/write.md:59-62`
- Action: extract into `B004.scope_override_nonreal_rule`
- Replacement in composed output: exact same text.

### Operation W06 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/write.md:91-93`
- Action: extract into `B006.global_continuity_array_guardrail`
- Replacement in composed output: exact same text.

### Operation W07 - Preserve transfer-vs-registry rule (known formatting caution)
- Current span: `resources/prompt_templates/write.md:127-135`
- Action: extract into `B007.transfer_registry_conflict_rule`
- Replacement in composed output: exact same text in first migration pass.
- Caution:
  - `resources/prompt_templates/write.md:130` contains a wrapped/concatenated clause.
  - Do not normalize this line in first pass; normalization requires explicit semantic review.

### Operation W08 - Preserve appearance updates object guardrails
- Current spans:
  - `resources/prompt_templates/write.md:107-109`
  - `resources/prompt_templates/write.md:140-142`
- Action: extract to `B008.appearance_updates_object_guardrail`
- Replacement in composed output: exact same text.

### Operation W09 - Preserve JSON Contract Block as shared block
- Current span: `resources/prompt_templates/write.md:215-233`
- Action: extract to `B005.json_contract_block`
- Replacement in composed output: exact same text.

### Operation W10 - Preserve phase-local output shape and placeholders
- Current spans:
  - `resources/prompt_templates/write.md:168-213`
- Action: keep phase-local block (not shared) due strong coupling to write output structure.
- Coupling rationale:
  - Write parser expects prose + `STATE_PATCH` structure (`src/bookforge/pipeline/parse.py:70-88`).

## Proposed Composed Template Layout (Draft)
1. `write/header_v1`
2. `shared/must_stay_true_end_truth_line`
3. `shared/must_stay_true_remove_block`
4. `shared/inventory_posture_reconciliation_v1`
5. `write/durable_ephemeral_and_ui_v1`
6. `write/appearance_and_naming_v1`
7. `shared/scope_override_nonreal_rule`
8. `write/state_patch_rules_core_v1`
9. `shared/global_continuity_array_guardrail`
10. `shared/transfer_registry_conflict_rule`
11. `shared/appearance_updates_object_guardrail`
12. `write/output_blocks_v1`
13. `shared/json_contract_block`

## Risk & Validation Notes
- Must pass unchanged parsing and schema flow in:
  - `src/bookforge/phases/write_phase.py:73-125`
- Must not alter wording that state repair/lint depend on for behavior cues.
- First migration rule: semantic no-op except duplicate line removal.

## Reviewer Checklist
- Confirm all deleted duplicate spans are semantically redundant.
- Confirm no non-duplicate policy sentence was dropped.
- Confirm composed output is byte-equivalent except approved dedupe removals.
