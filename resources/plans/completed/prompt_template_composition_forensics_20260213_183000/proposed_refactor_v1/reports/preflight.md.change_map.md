# Change Map: preflight.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/preflight.md`
- SHA256: `D05581CDE8C564447EF93F71E92DE73918480B50B859B3AF7A2461E48F7EECF2`

## Composition Entries (Order)
1. phase  -> `fragments/phase/preflight/seg_01.md`
2. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
3. phase  -> `fragments/phase/preflight/seg_02.md`
4. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
5. phase  -> `fragments/phase/preflight/seg_03.md`
6. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)
7. phase  -> `fragments/phase/preflight/seg_04.md`

## Reuse Summary
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.
