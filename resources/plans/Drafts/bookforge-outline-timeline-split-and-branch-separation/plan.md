# BookForge Outline Timeline Split And Branch Separation

Status: Draft
Stage: Drafts
Owner: BookForge engine workstream
Last Updated: 2026-04-29

## Objective

Build a deterministic outline-fragment graph and split system that can separate improperly merged outline timelines into isolated branches, each with a precise scope of work and its related artifacts.

This is designed for the Veiled Ledger failure class, but it must not be a bespoke `fix_veiled_ledger` command. The result should be a general BookForge capability that lets Nanda or an author agent inspect timeline fragments, choose or auto-select valid anchors, create separated branches, and then use existing recovery/redraft tools against a cleanly scoped branch.

## Why Now

The existing lineage audit can detect global chimera risk and section-level mismatches. The existing recovery primitives can create branches, quarantine stale artifacts, normalize outline scope, invalidate outputs, rebuild state, redraft, validate, and promote.

The missing layer is between those two:

```text
contaminated workspace
  -> deterministic graph of outline fragments and related data
  -> fragment scope-of-work objects
  -> separated timeline branches
  -> normal recovery / redraft / validation flow
```

If every outline fragment has a proper scope of work, the split itself should be mostly deterministic. The LLM does not need to decide which files belong together. It should only inspect the report, choose between candidate timelines when needed, and later rewrite prose or explain the decision.

## Grounding

Existing surfaces to build on:

- `bookforge.query.outline_lineage.get_outline_lineage_audit`
- `bookforge.query.outline_lineage.get_section_lineage_matrix`
- `bookforge.query.outline_lineage.get_stale_outline_artifact_inventory`
- `bookforge.query.outline_lineage.get_outline_repair_candidates`
- `bookforge.execution.recovery_create.create_recovery_branch`
- `bookforge.execution.recovery_artifacts.quarantine_artifacts`
- `bookforge.execution.recovery_outline.normalize_outline_scope`
- `bookforge.execution.recovery_artifacts.invalidate_scope_outputs`
- `bookforge.execution.recovery_state.rebuild_state_scope`
- `bookforge.execution.recovery_redraft.redraft_scope`
- `bookforge.execution.recovery_validation.validate_recovery_branch`
- `bookforge.execution.recovery_validation.promote_recovery_branch`
- `bookforge.query.branches.get_branch_artifact_index`
- `bookforge.query.branches.get_branch_diff_summary`

Current problem example:

- `workspace/books/veiled_ledger_b1/outline/section_drafts`
- `workspace/books/veiled_ledger_b1/outline/chapters`
- `workspace/books/veiled_ledger_b1/outline/outline.json`
- ghost character/state/prose data from multiple outline passes

## Core Model

### Outline Fragment

An `OutlineFragment` is any artifact that carries outline structure for a bounded scope:

- immutable run output
- frozen chapter projection
- frozen section projection
- mutable compatibility outline
- section draft / phase03 output
- chapter projection generated from a section-local workflow
- snapshot registry entries

Each fragment must report:

- fragment id
- artifact path
- artifact class
- artifact status
- source run id, if known
- workflow family, if known
- chapter/section/scene scope
- mtime
- file hash
- normalized scope hash
- normalized scene list hash
- character ids referenced
- thread ids referenced
- upstream/downstream refs, where present
- confidence that the scope was parsed correctly

### Fragment Work Unit

An `OutlineFragmentWorkUnit` is the smallest operational planning unit.

It answers:

> What does this one outline-bearing fragment claim, what does it touch, and what must happen to it during separation?

Fields:

- fragment id
- parsed scope selector
- claimed lineage
- claimed workflow family
- claimed source artifact class
- candidate assignment
- assignment confidence
- competing candidate ids
- direct outline claims
- direct entity claims
- direct scene-list claims
- artifact dependencies
- downstream artifacts produced from this fragment
- required operation:
  - `include`
  - `copy_as_reference`
  - `materialize_projection`
  - `normalize_into_branch`
  - `quarantine`
  - `salvage_reference`
  - `invalidate`
  - `ignore_as_duplicate`
- operation reason
- blockers
- evidence refs

This object makes the graph separable. If every fragment has one work unit, candidate branches can be assembled by grouping work units rather than making a global judgment over a messy folder.

### Fragment Scope Of Work

An `OutlineFragmentScopeOfWork` is the central contract.

It answers:

> If this fragment becomes part of a separated timeline branch, what exact work must be done to make that branch coherent?

Despite the name, this is the candidate-level aggregate. It is built from many `OutlineFragmentWorkUnit` records and tells BookForge/Nanda what work is needed for one candidate timeline branch.

Fields:

- scope id
- fragment ids included
- fragment work unit ids
- branch candidate id
- chapter/section/scene range
- source lineage anchor
- expected outline files to materialize
- prose artifacts to keep
- prose artifacts to invalidate
- state/projection artifacts to keep
- state/projection artifacts to quarantine
- ambiguous/salvage artifacts
- missing required artifacts
- required redraft scopes
- required validation gates
- confidence
- confidence summary
- refusal/blocker codes
- recommended next action

This object is not an LLM plan. It is a deterministic work package.

### Timeline Graph

The timeline graph is a bipartite-ish graph:

```text
fragment nodes
artifact nodes
scope nodes
entity nodes
```

Edges include:

- `declares_scope`
- `derived_from_run`
- `materializes_chapter`
- `materializes_section`
- `references_character`
- `references_thread`
- `writes_prose`
- `updates_state`
- `supersedes`
- `conflicts_with`
- `ambiguous_with`

Partitioning creates timeline candidates by grouping fragment work units that agree on normalized scope hashes, source lineage, section/scene structure, character sets, and workflow family.

### Assignment Confidence

Assignments should be conservative:

- `high`: direct path/source/run/scope match
- `medium`: hash/structure/entity match without direct lineage
- `low`: plausible temporal or scope adjacency only
- `ambiguous`: cannot assign safely
- `conflict`: belongs to multiple incompatible candidates

Only high and selected medium-confidence artifacts may enter active separated branch state.

Low, ambiguous, and conflict artifacts go to salvage/quarantine.

### Split Branch

A split branch is a derived branch created from one timeline candidate.

It must contain:

- normalized outline for that timeline
- snapshot registry matching that timeline
- frozen projections matching that timeline
- valid state/projection subset where assignment is safe
- recovery manifest recording the fragment graph and scope of work
- quarantine/salvage directory for excluded artifacts

It must not silently inherit polluted active outline files.

### Branch Cleanliness

Branch creation does not mean clean. A separated split branch can have states:

- `graph_preview_only`
- `materialized_not_validated`
- `validated_structural`
- `needs_redraft`
- `needs_semantic_review`
- `promotion_ready`
- `discard_recommended`

The split system separates timelines. Existing recovery validation proves whether one timeline branch is safe to promote.

## Proposed Query And Action Surface

Read-only first:

- `get_outline_fragment_graph(workspace, book_id)`
- `get_outline_timeline_split_preview(workspace, book_id)`
- `get_outline_fragment_scope_of_work(workspace, book_id, candidate_id=None)`
- `get_outline_split_branch_plan(workspace, book_id, candidate_id=None)`

Mutation second:

- `create_outline_timeline_split_branches`

Validation/handoff:

- `validate_outline_timeline_split_branch`
- `convert_split_branch_to_recovery_plan`

Possible CLI shape:

```powershell
bookforge workflow outline-fragment-graph --book veiled_ledger_b1 --json
bookforge workflow outline-timeline-split-preview --book veiled_ledger_b1 --json
bookforge workflow outline-fragment-scope-of-work --book veiled_ledger_b1 --candidate declared_source_run --json
bookforge workflow create-outline-timeline-split-branches --book veiled_ledger_b1 --selected-candidates declared_source_run,section_draft_wave --json
```

## Scope

- Add contracts for outline fragments, graph edges, timeline candidates, fragment scope of work, split preview, and branch creation receipts.
- Add fragment-level work units so every outline fragment has an explicit operation and evidence trail.
- Build a deterministic graph from existing outline and recovery query surfaces.
- Partition fragments into candidate timelines.
- Produce per-candidate scope-of-work objects.
- Create isolated branches for selected candidates.
- Keep ambiguous data quarantined/salvage-only.
- Add validation gates proving no mixed outline lineage remains in a split branch.
- Project capabilities for Nanda.

## Non-Goals

- No LLM judgment for artifact assignment in the first implementation.
- No automatic selection when multiple high-confidence timelines imply different books.
- No automatic canonical promotion.
- No semantic/prose quality repair in the split command.
- No cross-book series continuity repair.
- No database migration in this plan.
- No whole-book redraft command hidden inside branch creation.

## Deliverables

- Outline split contracts under `src/bookforge/contracts/`.
- Read-only query module under `src/bookforge/query/`.
- Branch creation action under `src/bookforge/execution/`.
- CLI commands for preview, scope of work, and branch creation.
- Recovery handoff adapter from split branch to existing recovery primitives.
- Tests with:
  - clean single-lineage book
  - two-outline chimera fixture
  - ambiguous artifact fixture
  - ghost character/state fixture
  - branch creation fixture
- Nanda capability projection entries and fixture updates.
- Plan artifacts:
- `artifacts/veiled-ledger-split-model.md`
- `artifacts/fragment-assignment-rules.md`
- `artifacts/scope-of-work-contract.md`
- `artifacts/timeline-split-algorithm.md`
- `artifacts/nanda-author-agent-handoff.md`

## Definition Of Done

- BookForge can preview outline timeline candidates without mutating the workspace.
- Every outline fragment considered by the system has an `OutlineFragmentWorkUnit`.
- Each candidate has a concrete `OutlineFragmentScopeOfWork`.
- Ambiguous data is never silently assigned to active branch state.
- BookForge can create two or more separated split branches from a contaminated workspace.
- Each branch records exactly which fragments and artifacts were included, excluded, or quarantined.
- Split branches can be validated for structural lineage health.
- Nanda can show the author/user the candidate timelines and ask for a choice only when more than one valid choice exists.
- When only one structurally valid timeline exists, Nanda can auto-select it and proceed to recovery branch work.
- The branch handoff can use existing recovery primitives for quarantine, normalization, invalidation, rebuild, redraft, validation, and promotion.

## Risks

- Path and mtime evidence can be misleading after manual copying or git operations.
- Some artifacts may contain useful prose from the wrong timeline; those must remain salvage/reference, not active state.
- A timeline can be structurally coherent but the wrong story.
- Character ids may not be stable across outline passes; name matching should be evidence, not proof.
- Partial state/projection data may reference old branch ids or node coordinates.
- Over-eager branch creation could duplicate polluted data into new branches under a cleaner name.
- Nanda author voice may overstate certainty unless confidence and ambiguity are explicit.

## Implementation Bias

- Start with read-only graph and scope-of-work.
- Prefer explicit confidence and quarantine over clever assignment.
- Reuse existing recovery contracts where possible.
- Keep split branch creation narrow and deterministic.
- Treat branch creation as isolation, not repair completion.
- Make the capability projection honest: preview/query surfaces first, mutation gated later.
