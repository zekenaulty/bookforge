# Change Map: repair.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/repair.md`
- SHA256: `6171B0A6AF67580D96BF4FD6DCAD349A01A909E073FD9EC37D013E9346C5FB55`

## Composition Entries (Order)
1. phase  -> `fragments/phase/repair/seg_01.md`
2. shared -> `B002.must_stay_true_reconciliation_block` (`fragments/shared/B002.must_stay_true_reconciliation_block.md`)
3. shared -> `B003.must_stay_true_remove_block` (`fragments/shared/B003.must_stay_true_remove_block.md`)
4. phase  -> `fragments/phase/repair/seg_02.md`
5. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
6. phase  -> `fragments/phase/repair/seg_03.md`
7. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
8. phase  -> `fragments/phase/repair/seg_04.md`
9. shared -> `B008a.appearance_updates_object_under_character_updates` (`fragments/shared/B008a.appearance_updates_object_under_character_updates.md`)
10. phase  -> `fragments/phase/repair/seg_05.md`
11. shared -> `B007.transfer_registry_conflict_rule` (`fragments/shared/B007.transfer_registry_conflict_rule.md`)
12. phase  -> `fragments/phase/repair/seg_06.md`
13. shared -> `B008b.appearance_updates_not_array` (`fragments/shared/B008b.appearance_updates_not_array.md`)
14. phase  -> `fragments/phase/repair/seg_07.md`
15. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)

## Reuse Summary
- Uses shared block `B002.must_stay_true_reconciliation_block`
- Uses shared block `B003.must_stay_true_remove_block`
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B008a.appearance_updates_object_under_character_updates`
- Uses shared block `B007.transfer_registry_conflict_rule`
- Uses shared block `B008b.appearance_updates_not_array`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: dedupe repeated reconciliation blocks + block extraction.
- Removed duplicate lines:
  - `resources/prompt_templates/repair.md:55` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:56` -> 
  - `resources/prompt_templates/repair.md:57` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:58` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:60` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:61` -> 
  - `resources/prompt_templates/repair.md:62` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:63` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:65` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:66` -> 
  - `resources/prompt_templates/repair.md:67` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:68` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:82` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:83` -> 
  - `resources/prompt_templates/repair.md:84` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:85` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:87` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:88` -> 
  - `resources/prompt_templates/repair.md:89` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:90` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:108` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:109` -> 
  - `resources/prompt_templates/repair.md:110` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:111` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:134` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:135` -> 
  - `resources/prompt_templates/repair.md:136` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:137` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:189` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:190` -> 
  - `resources/prompt_templates/repair.md:191` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:192` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:194` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:195` -> 
  - `resources/prompt_templates/repair.md:196` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:197` ->   - Remove conflicting old invariants rather than preserving them.
- Policy delta: none (wording preserved; duplicates removed only).

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.
