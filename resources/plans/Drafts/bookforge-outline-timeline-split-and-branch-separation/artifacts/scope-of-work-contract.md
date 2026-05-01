# Scope Of Work Contract

Date: 2026-04-29

## Purpose

The timeline split system only becomes reliable if every outline fragment produces a concrete work unit.

The split model has two levels:

- `OutlineFragmentWorkUnit`: one operational record for one outline-bearing fragment.
- `OutlineFragmentScopeOfWork`: the aggregate work package for one candidate timeline branch.

This prevents the split preview from becoming another broad warning. The author agent should see exactly which fragments are usable, which are unsafe, and which downstream work must happen before a separated branch can be trusted.

## OutlineFragmentWorkUnit

Required fields:

- `work_unit_id`
- `fragment_id`
- `artifact_path`
- `parsed_scope`
- `claimed_source_run_id`
- `claimed_workflow_family`
- `claimed_artifact_class`
- `candidate_assignment`
- `assignment_confidence`
- `competing_candidate_ids`
- `direct_outline_claims`
- `direct_entity_claims`
- `direct_scene_list_claims`
- `artifact_dependencies`
- `downstream_artifacts`
- `required_operation`
- `operation_reason`
- `evidence_refs`
- `blocker_codes`

`required_operation` values:

- `include`: copy or materialize into active branch state.
- `copy_as_reference`: keep readable in branch evidence but do not feed execution.
- `materialize_projection`: rebuild a branch-local projection from this fragment.
- `normalize_into_branch`: transform compatible data into branch-local layout.
- `quarantine`: preserve outside active state.
- `salvage_reference`: preserve as inspiration/reference only.
- `invalidate`: mark dependent outputs as invalid for this candidate.
- `ignore_as_duplicate`: drop from active planning because a stronger fragment supersedes it.

## OutlineFragmentScopeOfWork

Required fields:

- `scope_of_work_id`
- `branch_candidate_id`
- `candidate_label`
- `candidate_lineage_anchor`
- `chapter_range`
- `section_range`
- `scene_range`
- `included_work_unit_ids`
- `reference_work_unit_ids`
- `quarantined_work_unit_ids`
- `salvage_work_unit_ids`
- `invalidated_work_unit_ids`
- `missing_required_fragments`
- `expected_outline_outputs`
- `expected_snapshot_outputs`
- `prose_artifacts_to_keep`
- `prose_artifacts_to_invalidate`
- `state_artifacts_to_keep`
- `state_artifacts_to_quarantine`
- `character_records_to_keep`
- `character_records_to_quarantine`
- `required_redraft_scopes`
- `required_rebuild_scopes`
- `required_validation_gates`
- `confidence_summary`
- `blocker_codes`
- `recommended_next_action`

## Key Rule

The aggregate scope of work cannot hide fragment uncertainty.

If any fragment is ambiguous, conflicting, or assigned only by weak evidence, the aggregate must expose that fact in:

- `confidence_summary`
- `blocker_codes`
- `salvage_work_unit_ids`
- `quarantined_work_unit_ids`
- `recommended_next_action`

## Branch Creation Contract

Branch creation consumes `OutlineFragmentScopeOfWork`, not raw folders.

That means the mutating action should not scan `outline/section_drafts` and decide in place. It should receive or resolve a selected candidate, read its work units, and perform exactly the operations listed by the scope of work.

## Nanda Contract

Nanda should render the scope of work as an action plan:

- what timeline this branch represents
- what data will be included
- what data will be quarantined
- what data is salvage-only
- what prose/state must be redrafted or rebuilt
- what validation gates must pass before promotion
- whether the choice can be auto-selected

Nanda may explain and ask for approval. BookForge owns the assignment evidence and mutation.
