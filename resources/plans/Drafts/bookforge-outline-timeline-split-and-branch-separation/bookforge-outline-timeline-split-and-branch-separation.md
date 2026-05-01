# bookforge-outline-timeline-split-and-branch-separation

## Compiled Plan Metadata

- Plan Scope: `Drafts/bookforge-outline-timeline-split-and-branch-separation`
- Compiled At (UTC): `2026-04-29T05:31:23Z`
- Source Document Count: `13`
- Projection File: `bookforge-outline-timeline-split-and-branch-separation.md`

## Contents

1. `plan.md`
2. `steps/index.md`
3. `steps/0010-define-outline-fragment-graph-and-scope-of-work/step.md`
4. `steps/0020-add-read-only-timeline-split-preview/step.md`
5. `steps/0030-add-deterministic-artifact-partitioning/step.md`
6. `steps/0040-create-separated-outline-timeline-branches/step.md`
7. `steps/0050-add-validation-and-recovery-handoff/step.md`
8. `steps/0060-project-capabilities-and-nanda-fixtures/step.md`
9. `artifacts/fragment-assignment-rules.md`
10. `artifacts/nanda-author-agent-handoff.md`
11. `artifacts/scope-of-work-contract.md`
12. `artifacts/timeline-split-algorithm.md`
13. `artifacts/veiled-ledger-split-model.md`

---

## Source 1: `plan.md`

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

---

## Source 2: `steps/index.md`

# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-define-outline-fragment-graph-and-scope-of-work | draft | - | Freeze the graph vocabulary and `OutlineFragmentScopeOfWork` contract. |
| 0020-add-read-only-timeline-split-preview | draft | 0010 | Produce deterministic timeline candidates and scope-of-work previews without mutation. |
| 0030-add-deterministic-artifact-partitioning | draft | 0020 | Assign prose/state/projection artifacts to candidate timelines or quarantine with confidence. |
| 0040-create-separated-outline-timeline-branches | draft | 0030 | Materialize selected candidates as isolated branches with manifests and receipts. |
| 0050-add-validation-and-recovery-handoff | draft | 0040 | Validate split branches and convert them into existing recovery/redraft workflows. |
| 0060-project-capabilities-and-nanda-fixtures | draft | 0050 | Expose query/action capabilities and Nanda fixtures for author-agent operation. |

---

## Source 3: `steps/0010-define-outline-fragment-graph-and-scope-of-work/step.md`

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

---

## Source 4: `steps/0020-add-read-only-timeline-split-preview/step.md`

# 0020 - Add Read-Only Timeline Split Preview

Status: draft
Depends On: 0010

## Objective

Add the first read-only graph query that turns scattered outline artifacts into timeline candidates and scope-of-work previews.

No mutation happens in this step.

## Detailed Work

- Add `bookforge.query.outline_timeline_split`.
- Implement:
  - `get_outline_fragment_graph(workspace, book_id)`
  - `get_outline_timeline_split_preview(workspace, book_id)`
  - `get_outline_fragment_scope_of_work(workspace, book_id, candidate_id=None)`
- Reuse existing lineage extraction where possible:
  - section matrix rows
  - stale artifact inventory
  - outline repair candidates
  - normalized section hashes
  - scene list hashes
- Generate candidate timelines from:
  - source run lineage
  - frozen projection lineage
  - section draft lineage
  - mutable compatibility view lineage
- Emit candidate-level summaries:
  - affected scopes
  - likely source run
  - included fragments
  - conflicting fragments
  - missing fragments
  - scope of work
  - confidence
  - recommended action

## Files Likely Touched

- `src/bookforge/query/outline_timeline_split.py`
- `src/bookforge/query/__init__.py`
- `src/bookforge/cli.py`
- `tests/test_outline_timeline_split_query.py`

## Tests

- Healthy single-lineage book returns `single_healthy_timeline`.
- Two-outline fixture returns at least two candidates.
- Candidate scopes cover all conflicting sections.
- Preview is deterministic across repeated runs.
- No files are written.

## Definition Of Done

- Nanda can ask "what timelines exist here?" without raw file archaeology.
- The query clearly distinguishes no-op healthy state from split-worthy contamination.
- Each candidate includes a concrete `OutlineFragmentScopeOfWork`.
- Ambiguous artifacts remain visible and unassigned.

---

## Source 5: `steps/0030-add-deterministic-artifact-partitioning/step.md`

# 0030 - Add Deterministic Artifact Partitioning

Status: draft
Depends On: 0020

## Objective

Assign non-outline artifacts to timeline candidates, or explicitly quarantine them, using deterministic evidence.

This is the step that turns "two outlines exist" into "these exact files belong to candidate A, these belong to candidate B, and these are ambiguous."

## Detailed Work

- Add artifact collectors for:
  - prose scene files
  - scene metadata
  - phase history
  - chapter markdown
  - character indexes
  - character state
  - continuity summaries
  - context projections
  - appearance and setting projections
  - recovery/supervision receipts where useful
- Add assignment rules:
  - direct source-run/scope link is high confidence
  - exact normalized section/scene hash match is high confidence
  - character/thread set plus scene structure match is medium confidence
  - mtime adjacency alone is low confidence
  - mismatch against two candidates is conflict
  - no reliable evidence is ambiguous
- Emit partition records:
  - path
  - artifact class
  - assignment status
  - candidate id
  - confidence
  - evidence refs
  - reason codes
- Keep destructive decisions out of this step.

## Files Likely Touched

- `src/bookforge/query/outline_timeline_split.py`
- `src/bookforge/query/branches.py` if artifact classes need refinement
- `tests/test_outline_timeline_split_partition.py`

## Tests

- Prose matching one candidate is assigned high confidence.
- Ghost character state goes to the candidate that declares the character id.
- Duplicate protagonist/ghost character conflicts are flagged.
- Artifacts with only mtime evidence are not assigned active state.
- Ambiguous artifacts are not silently included.

## Definition Of Done

- Every collected artifact has an assignment record.
- Every assignment has evidence and confidence.
- Only high and selected medium-confidence artifacts are eligible for active branch materialization.
- Ambiguous and conflict artifacts are visible to Nanda as salvage/quarantine candidates.

---

## Source 6: `steps/0040-create-separated-outline-timeline-branches/step.md`

# 0040 - Create Separated Outline Timeline Branches

Status: draft
Depends On: 0030

## Objective

Materialize selected timeline candidates into isolated branches, with active branch state containing only artifacts assigned to that candidate and all ambiguous data preserved as quarantine/salvage.

## Detailed Work

- Add request builder and action:
  - `build_create_outline_timeline_split_branches_request(...)`
  - `create_outline_timeline_split_branches(...)`
- Require explicit selected candidate ids unless the preview reports exactly one valid candidate.
- For each selected candidate:
  - create a branch with role `outline_timeline_split`
  - write split manifest
  - materialize normalized outline
  - materialize snapshot registry
  - materialize frozen projections
  - copy included artifacts into active branch paths
  - move excluded/ambiguous/conflict artifacts under split quarantine/salvage paths
  - write branch creation receipt
- Preserve original workspace state.
- Do not promote to main.
- Do not redraft prose in this action.

## Files Likely Touched

- `src/bookforge/execution/outline_timeline_split.py`
- `src/bookforge/execution/__init__.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/capabilities.py`
- `src/bookforge/cli.py`
- `tests/test_outline_timeline_split_actions.py`
- `tests/fixtures/capability_projection_v1.json`

## Tests

- Creates two branches from a two-timeline fixture.
- Branch active outline contains only selected candidate outline data.
- Ambiguous artifacts are quarantined/salvage-only.
- Main is unchanged.
- Receipts list included, excluded, quarantined, and missing artifacts.
- Action refuses when selected candidate has unresolved blockers.

## Definition Of Done

- BookForge can create isolated branches for candidate timelines without LLM judgment.
- Every branch has a split manifest and receipt.
- The branch is described as `materialized_not_validated`, not clean.
- Nanda can inspect branch artifacts and explain what was included or quarantined.

---

## Source 7: `steps/0050-add-validation-and-recovery-handoff/step.md`

# 0050 - Add Validation And Recovery Handoff

Status: draft
Depends On: 0040

## Objective

Validate split branches and hand them into the existing recovery/redraft pipeline.

Timeline split is isolation. Recovery remains the process that turns an isolated candidate into a promotable book state.

## Detailed Work

- Add `validate_outline_timeline_split_branch(...)`.
- Validate:
  - no mixed source runs in active outline
  - no section draft artifacts active outside selected candidate
  - snapshot registry agrees with outline
  - character ids in state/projections exist in selected outline
  - projection `node`/`selector` branch ids match split branch
  - ambiguous/conflict artifacts remain in quarantine/salvage
- Add `convert_split_branch_to_recovery_plan(...)`.
- Map split scope-of-work into existing recovery scope:
  - affected scopes
  - downstream scopes
  - artifacts to quarantine
  - outputs to invalidate
  - state/projections to rebuild
  - scopes to redraft
- Keep semantic review separate from structural validation.

## Files Likely Touched

- `src/bookforge/execution/outline_timeline_split.py`
- `src/bookforge/query/recovery.py`
- `src/bookforge/execution/recovery_common.py`
- `tests/test_outline_timeline_split_validation.py`
- `tests/test_recovery_actions.py`

## Tests

- Valid split branch passes structural validation.
- Branch with ghost character state fails validation.
- Branch with active ambiguous artifact fails validation.
- Recovery plan preview can be produced from split branch manifest.
- Existing recovery primitives can consume the handoff scope.

## Definition Of Done

- Split branch validation tells Nanda whether the branch is structurally usable.
- Split branch handoff can drive the existing recovery sequence.
- The branch can reach `needs_redraft` or `promotion_ready` only through receipts.
- Semantic/prose quality remains a separate author-review gate.

---

## Source 8: `steps/0060-project-capabilities-and-nanda-fixtures/step.md`

# 0060 - Project Capabilities And Nanda Fixtures

Status: draft
Depends On: 0050

## Objective

Expose the split system through capability projection, legal actions, readiness, CLI, and Nanda fixtures so the author agent can operate it through conversation without theater.

## Detailed Work

- Add capability descriptors for:
  - `query.outline_fragment_graph`
  - `query.outline_timeline_split_preview`
  - `query.outline_fragment_scope_of_work`
  - `query.outline_split_branch_plan`
  - `action.create_outline_timeline_split_branches`
  - `action.validate_outline_timeline_split_branch`
  - `action.convert_split_branch_to_recovery_plan`
- Add legal-action rows for mutation steps.
- Add readiness/refusal metadata:
  - no split needed
  - single candidate auto-selectable
  - multiple candidates require user/author choice
  - selected candidate blocked
  - ambiguous artifacts require quarantine
- Add CLI help docs.
- Add Nanda fixture outputs:
  - healthy book
  - two-candidate split
  - ambiguous artifact
  - blocked candidate
  - auto-selected single valid candidate

## Files Likely Touched

- `src/bookforge/query/capabilities.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/cli.py`
- `docs/help/workflow.md`
- `docs/help/capabilities.md`
- `tests/test_capability_projection.py`
- `tests/fixtures/capability_projection_v1.json`
- `resources/plans/Drafts/bookforge-outline-timeline-split-and-branch-separation/artifacts/nanda-author-agent-handoff.md`

## Tests

- Capability projection includes all query/action surfaces.
- Real legal-action strings are covered by projection.
- Fixture projection matches live projection.
- CLI parser accepts split commands.
- Nanda fixture examples serialize cleanly.

## Definition Of Done

- Nanda can discover split capabilities from BookForge projection.
- Nanda can tell the difference between preview-only, auto-selectable, user-choice-required, and mutation-ready states.
- User-facing author responses can say what was proven and what remains uncertain.
- The author agent can call split preview and branch creation tools without needing a hardcoded Veiled Ledger fix.

---

## Source 9: `artifacts/fragment-assignment-rules.md`

# Fragment Assignment Rules

Date: 2026-04-29

## Purpose

This note captures the deterministic assignment model for outline timeline splitting.

The rule is conservative:

> Do not assign an artifact to active branch state unless there is structural evidence. If evidence is weak, preserve it as salvage or quarantine.

## Evidence Strength

### High Confidence

Use for active inclusion by default.

- artifact path directly belongs to a selected immutable source run
- artifact path directly belongs to a selected frozen projection
- fragment declares matching `source_run_id`
- normalized section hash matches the candidate exactly
- normalized scene list hash matches the candidate exactly
- scene ids and section/chapter refs match exactly and no competing candidate matches

### Medium Confidence

Eligible only when the split plan allows medium-confidence inclusion.

- character/thread set matches candidate and conflicts with other candidates
- prose metadata summary matches candidate scene summary/outcome
- phase history refs match candidate scene ids after renumbering
- mtime falls inside the candidate wave and structure matches

### Low Confidence

Do not include in active branch state by default.

- mtime adjacency only
- filename scope only
- partial character-name match without stable id
- prose text appears thematically related but lacks metadata

### Ambiguous

Quarantine or salvage.

- artifact plausibly belongs to more than one candidate
- source run absent and hashes do not match
- state file references characters from multiple candidate timelines

### Conflict

Quarantine and block validation until resolved.

- artifact declares a different source run than candidate
- artifact has branch/node coordinates from another branch
- artifact includes entity ids absent from selected timeline
- artifact matches multiple incompatible candidates at high confidence

## Assignment Outputs

Every considered artifact receives one assignment record:

- `included`
- `excluded`
- `quarantined`
- `salvage_reference`
- `ambiguous`
- `conflict`
- `missing`

No hidden skip is allowed. If the system sees a relevant file, it must explain what happened to it.

## Veiled Ledger Implication

For Veiled Ledger, this means the system should be able to say:

- which sections belong to the declared source-run timeline
- which sections belong to the section-draft wave
- which prose/state/character artifacts cannot be trusted
- which artifacts can be reused only as salvage/reference
- which branch needs redraft before it can be semantically valid

The author agent can then choose or auto-select a timeline, but it should not invent the artifact assignment.

---

## Source 10: `artifacts/nanda-author-agent-handoff.md`

# Nanda Author Agent Handoff

Date: 2026-04-29

## Purpose

This plan gives Nanda a tool shape for reasoning about outline bleed without relying on user observation or LLM guessing.

Nanda should reason and communicate. BookForge should graph, split, mutate, validate, and receipt.

## Expected Nanda Flow

1. User asks about chimera/outline bleed/timeline repair.
2. Nanda calls `outline_timeline_split_preview`.
3. Nanda explains candidate timelines and confidence.
4. If one valid candidate exists, Nanda can auto-select.
5. If multiple candidates imply different books, Nanda asks the user to choose.
6. Nanda calls `create_outline_timeline_split_branches`.
7. Nanda inspects branch manifests, diff, artifact index, and validation.
8. Nanda creates or recommends a recovery/redraft work plan from the selected branch.

## Author Response Rules

Acceptable:

```text
BookForge found two deterministic outline timelines. Candidate A is anchored to the declared source run. Candidate B is anchored to a later section-draft wave. Five artifacts are ambiguous and will be preserved as salvage, not active state.
```

Not acceptable:

```text
I fixed the timeline.
```

unless execution receipts prove branch creation, validation, recovery, redraft, and promotion.

## Tool Truth

The author agent should not claim:

- a branch is clean because it was created
- ambiguous data was removed unless a receipt says so
- a timeline is the correct story unless the user/author policy selected it
- prose is repaired because outline artifacts were split

The author agent can claim:

- candidates found
- evidence and confidence
- selected or auto-selected anchor
- branch creation result
- validation state
- remaining required work

## UI/Action Card Needs

Nanda action cards should show:

- preview-only vs mutation
- selected candidate id
- confidence
- branch names to create
- ambiguous artifact count
- conflict count
- approval requirement
- expected receipts
- next recovery action

---

## Source 11: `artifacts/scope-of-work-contract.md`

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

---

## Source 12: `artifacts/timeline-split-algorithm.md`

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

---

## Source 13: `artifacts/veiled-ledger-split-model.md`

# Veiled Ledger Split Model

Date: 2026-04-29

## Working Hypothesis

Veiled Ledger appears to contain at least two outline timelines:

1. the declared/frozen outline lineage
2. the section-draft or recovery wave that bled into later materialization

There may also be ambiguous prose/state artifacts that are useful as inspiration but unsafe as active branch state.

## Desired Operator Experience

The author agent should be able to say:

```text
I found two outline timelines.

Candidate A is anchored to source run <id> and covers scopes <...>.
Candidate B is anchored to section-draft wave <id/timestamp> and covers scopes <...>.

These artifacts are cleanly assigned.
These artifacts are ambiguous and will be preserved as salvage only.
These state/character files conflict.

Recommended action: create separated branches, validate each branch, then choose the timeline to redraft/promote.
```

If only one valid candidate remains after validation, the author agent can auto-select it. If two candidates are structurally coherent but imply different books, it must ask the user which timeline is correct.

## Branches Produced

Example names:

- `split/veiled-ledger/declared-source-run`
- `split/veiled-ledger/section-draft-wave`
- `split/veiled-ledger/salvage`

The salvage branch/bucket is not a canonical candidate. It exists to preserve useful prose or ideas that should not contaminate active state.

## Scope Of Work Shape

For each candidate:

- active outline to materialize
- active frozen projections
- section scope coverage
- prose to keep
- prose to invalidate
- state/projections to keep
- state/projections to quarantine
- redraft scopes
- validation gates
- downstream scopes to review

## Repair Flow After Split

The split system stops at isolated branches.

Then existing recovery/story-weaving tools take over:

1. validate split branch
2. convert split branch to recovery plan
3. quarantine/invalidate/rebuild as needed
4. redraft impacted chapters/sections
5. semantic/downstream review
6. promotion approval

## Key Safety Rule

Creating a split branch does not mean the branch is clean.

It means the branch is isolated and explainable. Cleanliness requires validation receipts.
