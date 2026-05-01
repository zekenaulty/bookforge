# 0020 Define Unit Boundary And Capability Contract

Status: completed
Depends On: 0010

## Goal
Freeze the first BookForge-owned capability projection contract and the rules for what counts as a public command or skill.

## Detailed Work
- Add a typed contract for capability projection, likely:
  - `src/bookforge/contracts/capability_projection.py`
- Define:
  - `CapabilityProjection`
  - `CapabilityDescriptor`
  - `CapabilityEvidenceSource`
  - `CapabilityRefusalSemantics`
- Freeze unit types:
  - `query`
  - `readiness`
  - `primitive_action`
  - `validation_gate`
  - `macro_workflow`
  - `promotion_action`
  - `projection_skill`
- Freeze mutation classes:
  - `read_only`
  - `diagnostic_only`
  - `provisional_branch_mutation`
  - `branch_mutation`
  - `canonical_mutation`
  - `promotion`
  - `assembly`
- Freeze branch policy vocabulary by aligning with existing execution option contracts where possible.
- Freeze artifact status expectations using existing produced-artifact vocabulary.
- Define descriptor fields:
  - `schema_version`
  - `capability_id`
  - `human_label`
  - `unit_type`
  - `capability_type`
  - `action_key`
  - `query_key`
  - `supported_scope_kinds`
  - `required_selector_shape`
  - `branch_policy`
  - `mutation_class`
  - `approval_required`
  - `readiness_source`
  - `expected_receipt_type`
  - `produced_artifact_statuses`
  - `legal_next_action_relationships`
  - `refusal_semantics`
  - `child_actions`
  - `evidence_sources`
- Encode the rule that capability projection is static while readiness remains scope-specific and dynamic.

## Adaptive Authoring Rules
- `recommended_next_action` is not a rail.
- Macro workflows must expose child actions.
- Capability projection may include future-shaped placeholders only if marked as not implemented or omitted from executable projection.
- The first executable projection must not claim scene insertion, pairwise seam alignment, or branch comparison is wired unless those actions are present in BookForge.

## Likely Files Touched
- `src/bookforge/contracts/capability_projection.py`
- `src/bookforge/contracts/__init__.py`
- `tests/test_capability_projection_contract.py`

## Tests
- Contract round-trip serialization.
- Required-field validation.
- Invalid unit type and mutation class rejection.
- Macro workflow descriptor can list child actions without implying mandatory execution.
- Static capability descriptor cannot claim dynamic readiness status.

## Definition Of Done
- Capability projection contract exists and is exported.
- Unit boundary doctrine is reflected in contract naming and tests.
- Artifact status, branch policy, mutation class, approval, readiness source, and refusal semantics are first-class fields.
- Tests prove static capability and dynamic readiness are not collapsed.
