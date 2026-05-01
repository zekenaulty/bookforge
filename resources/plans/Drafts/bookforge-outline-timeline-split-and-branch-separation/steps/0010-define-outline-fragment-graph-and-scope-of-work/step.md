# 0010 - Define Outline Fragment Graph And Scope Of Work

Status: draft
Depends On: -

## Objective

Define the contracts and vocabulary that make deterministic timeline separation possible.

The load-bearing object is `OutlineFragmentScopeOfWork`. If this object is weak, the split system becomes another global chimera warning. If it is strong, branch creation is mostly mechanical.

## Detailed Work

- Add contracts for:
  - `OutlineFragment`
  - `OutlineFragmentWorkUnit`
  - `OutlineGraphEdge`
  - `OutlineTimelineCandidate`
  - `OutlineFragmentScopeOfWork`
  - `OutlineTimelineSplitPreview`
  - `OutlineTimelineSplitBranchPlan`
- Define scope selectors for:
  - book
  - chapter
  - section
  - scene
  - source run
  - workflow family
  - fragment id
- Define artifact assignment statuses:
  - `included`
  - `excluded`
  - `quarantined`
  - `salvage_reference`
  - `ambiguous`
  - `conflict`
  - `missing`
- Define confidence statuses:
  - `high`
  - `medium`
  - `low`
  - `ambiguous`
  - `conflict`
- Define blocker/refusal codes:
  - `no_outline_fragments`
  - `single_healthy_timeline`
  - `unparseable_fragment_scope`
  - `candidate_has_mixed_source_runs`
  - `candidate_missing_required_chapter`
  - `candidate_missing_required_section`
  - `ambiguous_artifact_assignment`
  - `conflicting_character_identity`
  - `manual_anchor_choice_required`
  - `fragment_requires_salvage_review`
  - `fragment_operation_unsafe`
- Define fragment operations:
  - `include`
  - `copy_as_reference`
  - `materialize_projection`
  - `normalize_into_branch`
  - `quarantine`
  - `salvage_reference`
  - `invalidate`
  - `ignore_as_duplicate`
- Define the aggregation rule:
  - every considered outline-bearing artifact produces one `OutlineFragmentWorkUnit`
  - each candidate timeline references the work units assigned to it
  - each `OutlineFragmentScopeOfWork` is built from candidate work units plus required missing-work records
  - ambiguous/conflict work units are never auto-included in a branch

## Files Likely Touched

- `src/bookforge/contracts/outline_timeline_split.py`
- `src/bookforge/contracts/__init__.py`
- `src/bookforge/contracts/vocabulary.py`
- `tests/test_outline_timeline_split_contracts.py`
- `resources/plans/Drafts/bookforge-outline-timeline-split-and-branch-separation/`

## Tests

- Contract round-trip tests.
- Required-field validation.
- One fragment produces exactly one work unit.
- Candidate scope-of-work aggregates work units without losing assignment evidence.
- Produced artifact status and confidence enum validation.
- Refusal code list stability.

## Definition Of Done

- `OutlineFragmentScopeOfWork` can represent a complete deterministic work package for one candidate timeline.
- `OutlineFragmentWorkUnit` can represent the operation required for one fragment without relying on prose explanation.
- Ambiguous work units cannot be included in a candidate without an explicit selected assignment.
- Contracts can serialize to JSON for Nanda.
- No contract requires LLM-written explanations to be operational.
- Invalid confidence/status values fail fast.
