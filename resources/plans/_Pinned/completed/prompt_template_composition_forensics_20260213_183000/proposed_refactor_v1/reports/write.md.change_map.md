# Change Map: write.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/write.md`
- SHA256: `0AECFF344DF887C79DFFF4FC1B6967817CADE8BB5569D32BAFE2FACD1B850D52`

## Composition Entries (Order)
1. phase  -> `fragments/phase/write/seg_01.md`
2. shared -> `B001.must_stay_true_end_truth_line` (`fragments/shared/B001.must_stay_true_end_truth_line.md`)
3. shared -> `B003.must_stay_true_remove_block` (`fragments/shared/B003.must_stay_true_remove_block.md`)
4. phase  -> `fragments/phase/write/seg_02.md`
5. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
6. phase  -> `fragments/phase/write/seg_03.md`
7. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
8. phase  -> `fragments/phase/write/seg_04.md`
9. shared -> `B008a.appearance_updates_object_under_character_updates` (`fragments/shared/B008a.appearance_updates_object_under_character_updates.md`)
10. phase  -> `fragments/phase/write/seg_05.md`
11. shared -> `B007.transfer_registry_conflict_rule` (`fragments/shared/B007.transfer_registry_conflict_rule.md`)
12. phase  -> `fragments/phase/write/seg_06.md`
13. shared -> `B008b.appearance_updates_not_array` (`fragments/shared/B008b.appearance_updates_not_array.md`)
14. phase  -> `fragments/phase/write/seg_07.md`
15. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)

## Reuse Summary
- Uses shared block `B001.must_stay_true_end_truth_line`
- Uses shared block `B003.must_stay_true_remove_block`
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B008a.appearance_updates_object_under_character_updates`
- Uses shared block `B007.transfer_registry_conflict_rule`
- Uses shared block `B008b.appearance_updates_not_array`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: dedupe exact duplicate lines + block extraction.
- Removed duplicate lines:
  - `resources/prompt_templates/write.md:24` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:65` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:68` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:71` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:81` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:105` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:155` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:158` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:194` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:197` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
- Policy delta: none (wording preserved; duplicates removed only).

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.
