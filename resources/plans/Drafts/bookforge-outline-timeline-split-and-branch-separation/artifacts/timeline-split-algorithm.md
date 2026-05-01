# Timeline Split Algorithm

Date: 2026-04-29

## Purpose

This is the deterministic algorithm BookForge should implement before any LLM-assisted repair happens.

The LLM may call the tool, explain the preview, choose between candidate timelines when policy allows, and later redraft prose. It should not assign artifacts to timelines by intuition.

## Phase 1 - Collect Fragments

Collect all outline-bearing and outline-derived artifacts:

- immutable outline pipeline run outputs
- frozen chapter projections
- frozen section projections
- mutable `outline.json`
- section drafts
- phase03 section-local outline artifacts
- snapshot registry entries
- scene metadata that declares outline source
- state/projection files that reference outline scene ids

Each discovered artifact receives an `OutlineFragment` record or a related artifact record.

## Phase 2 - Normalize Scope Claims

For each fragment:

- parse book/chapter/section/scene scope
- parse source run id when present
- parse workflow family when present
- compute file hash
- compute normalized section hash
- compute normalized scene list hash
- extract character ids
- extract location ids where available
- extract thread/plot ids where available
- record mtime and path evidence

Unparseable fragments are still represented. They become blocked or salvage work units, not hidden skips.

## Phase 3 - Build Graph

Create graph nodes:

- fragment
- artifact
- scope
- source run
- workflow family
- character/entity
- prose output
- state/projection output

Create edges:

- `declares_scope`
- `derived_from_run`
- `belongs_to_workflow_family`
- `materializes_chapter`
- `materializes_section`
- `references_character`
- `references_thread`
- `writes_prose`
- `updates_state`
- `supersedes`
- `conflicts_with`
- `ambiguous_with`

## Phase 4 - Create Fragment Work Units

Every fragment becomes one `OutlineFragmentWorkUnit`.

The work unit records:

- likely candidate assignment
- confidence
- competing candidates
- direct claims
- dependent outputs
- required operation
- evidence refs
- blockers

This is where the system distinguishes:

- active branch material
- reference-only material
- salvage material
- quarantine material
- invalidated outputs

## Phase 5 - Partition Candidate Timelines

Group high-confidence work units into candidates by:

- source run id
- workflow family
- normalized section hash
- normalized scene list hash
- chapter/section scope
- compatible character/entity ids
- supersession relationships

Medium-confidence work units may attach to a candidate only if they do not conflict with another candidate and the plan allows medium-confidence inclusion.

Low-confidence work units do not attach to active branch state by default.

Ambiguous/conflict units are quarantined or salvage-only.

## Phase 6 - Build Scope Of Work

For each candidate timeline, build an `OutlineFragmentScopeOfWork`:

- included work units
- excluded/quarantined/salvage work units
- missing required fragments
- outline materialization work
- snapshot rebuild work
- prose invalidation work
- state/projection rebuild work
- character cleanup work
- required redraft scopes
- validation gates
- confidence summary
- recommended next action

The scope of work is the thing Nanda and the operator can reason about.

## Phase 7 - Preview And Refuse Unsafe Mutations

The read-only preview should classify the split:

- `no_split_needed`
- `single_valid_candidate`
- `multiple_valid_candidates`
- `manual_anchor_choice_required`
- `insufficient_evidence`
- `unsafe_to_split`

Mutation is refused when:

- no candidate can produce complete required outline scope
- a candidate has mixed source runs in active work units
- required chapters/sections are missing
- active work units include unresolved conflicts
- branch target already exists without explicit overwrite/replace policy

## Phase 8 - Create Branches From Scope Of Work

For each selected candidate:

- create derived branch from current main or selected parent node
- materialize normalized outline outputs from included work units
- materialize branch-local snapshot registry
- copy reference artifacts into evidence/reference area
- quarantine unsafe artifacts outside active state
- mark invalidated prose/state outputs
- write split manifest
- emit branch creation receipt

The branch is `materialized_not_validated`, not clean.

## Phase 9 - Validate And Handoff

Run structural validation:

- no mixed outline lineage in active outline scope
- no active section draft from another candidate
- no ghost character ids in active state
- no active prose artifact generated from excluded timeline
- snapshot registry matches selected candidate
- branch manifest accounts for every considered artifact

If structural validation passes, hand off to recovery/redraft:

- normalize outline scope
- invalidate impacted prose/state
- rebuild state/projections
- redraft impacted scopes
- run semantic review
- promote only after explicit validation and approval

## Key Constraint

This system separates data. It does not decide which separated branch is the right story unless only one candidate is structurally valid by policy.
