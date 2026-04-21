# Change Map: state_repair.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/state_repair.md`
- SHA256: `BDA655A758FDBC0559FE0980FC92FEBA80FE2EE1792F660DE65D774297D582C2`

## Composition Entries (Order)
1. phase  -> `fragments/phase/state_repair/seg_01.md`
2. shared -> `B003.must_stay_true_remove_block` (`fragments/shared/B003.must_stay_true_remove_block.md`)
3. phase  -> `fragments/phase/state_repair/seg_02.md`
4. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
5. phase  -> `fragments/phase/state_repair/seg_03.md`
6. shared -> `B007.transfer_registry_conflict_rule` (`fragments/shared/B007.transfer_registry_conflict_rule.md`)
7. phase  -> `fragments/phase/state_repair/seg_04.md`
8. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
9. phase  -> `fragments/phase/state_repair/seg_05.md`
10. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)

## Reuse Summary
- Uses shared block `B003.must_stay_true_remove_block`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B007.transfer_registry_conflict_rule`
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.
