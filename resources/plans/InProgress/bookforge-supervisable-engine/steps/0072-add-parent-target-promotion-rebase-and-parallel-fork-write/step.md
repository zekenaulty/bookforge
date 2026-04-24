# 0072 Add Parent-Target Promotion, Rebase, And Parallel Fork Write

Status: pending

## Goal
- Extend the branch model so write-capable branches can merge upward into their parent branch or `main`, support explicit rebase against newer parent snapshots, and enable truthful sibling parallel write execution through fork groups and validation-gated assembly.

## Problem
- `0071` gives us isolated branch-local writer execution roots.
- That is not enough for real authoring workflows.
- The user expectations here are stronger:
  - chapter branches should be able to contain section sub-branches
  - section branches should be able to contain scene branches
  - a scene rewrite branch should be able to promote back into its section parent, not only `main`
  - branches will eventually need incoming changes from their parent
  - some writing work will run in parallel
- The current branch lifecycle is still too narrow:
  - promotion targets `main`
  - branch creation copies from canonical `main`
  - fork-group assembly exists conceptually, but not yet for writer-side branch content
  - rebase does not exist as an explicit supervised capability
- If we do not add parent-target promotion and explicit rebase, nested author branches become dead ends.
- If we allow parallel write branches without a real fork-group assembly/validation discipline, we will recreate hidden race conditions and semantic merge drift.

## Detailed Work
- Generalize branch creation so a branch may derive from a parent branch snapshot, not only canonical `main`.
  - Parent lineage must remain explicit in `BranchManifest`.
  - Branch creation must refuse stale parent snapshots truthfully.
- Add parent-target promotion.
  - Promotion target must be explicit:
    - branch -> parent branch
    - branch -> `main`
  - Promotion should copy validated branch-local state into the target execution root, not assume `main` as the only destination.
  - Receipts must make the target branch explicit.
- Add explicit rebase.
  - Rebase should be an explicit supervised operation, not a silent background mutation.
  - First safe version:
    - detect stale parent snapshot
    - create a refreshed child branch from the newer parent snapshot
    - replay or transplant the scoped branch-local work in a controlled way
    - mark the old branch stale or discarded
  - Do not start with hidden in-place semantic merge.
- Add nested branch hierarchy semantics without hardcoding one topology.
  - Chapter, section, and scene branches are good default roles.
  - The contract should still allow other scoped branch shapes.
  - Parent-child lineage must stay the real source of truth.
- Add write-capable fork-group siblings.
  - Sibling write branches must:
    - share the same parent snapshot revision
    - remain isolated from each other during execution
    - not read sibling outputs mid-run
  - This is the truthful basis for parallel scene or section writing.
- Add writer-side assembly.
  - Sibling branch results must be assembled off-parent, not directly on `main` or the parent branch.
  - Assembly should happen on an assembly branch derived from the shared parent snapshot.
  - Validation must run there before upward promotion.
- Add merge validation for write branches.
  - The first validation pass should focus on merge-level risks such as:
    - stale parent mismatch
    - sibling lineage mismatch
    - branch/fork contamination
    - seam or continuity validation required before promotion
  - Keep semantic prose merge narrow and explicit. Do not promise automatic perfect prose reconciliation.

## Surface Refinements
### Parent-Target Promotion
- Promotion must carry:
  - `source_branch_id`
  - `target_branch_id`
  - `merge_operation`
  - parent snapshot revision
  - validation status at time of promotion
- The execution result must make it clear whether canonical `main` changed or only an intermediate parent branch changed.

### Rebase
- Rebase must be a first-class supervised lifecycle action.
- The first safe contract should answer:
  - what parent revision the branch was created from
  - what parent revision is now current
  - whether the branch is stale
  - whether a refreshed child branch was created
  - what happened to the previous branch
- Rebase must not silently overwrite the old branch's recorded history.

### Parallel Fork Write
- Fork groups must support writer branches, not only outline/materialization branches.
- Required invariants:
  - siblings share one parent snapshot
  - siblings do not read each other during execution
  - assembly happens off-parent
  - upward promotion requires explicit validation status

## Nanda Impact
- This step is what makes multi-level author work practical.
- Nanda should eventually be able to:
  - create a chapter branch
  - create a section branch under it
  - create a scene rewrite branch under that
  - promote upward one layer at a time
  - detect stale parent state and request rebase
  - launch sibling branches for parallel write work
  - inspect assembly and promotion status without reading raw files
- This is also the step that makes future MCP-style execution skills coherent, because the agent can treat branch creation, branch write, rebase, assembly, and promotion as explicit capabilities rather than hidden recovery rituals.

## Files Likely Touched
- `src/bookforge/contracts/branch_manifest.py`
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/scope_selector.py`
- `src/bookforge/branching_store.py`
- `src/bookforge/branching_fork.py`
- `src/bookforge/branching_lifecycle.py`
- `src/bookforge/branching_execution.py`
- `src/bookforge/execution/branch_actions.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/query/actions.py`
- `docs/help/workflow.md`
- `docs/help/index.md`

## Tests
- Add nested-branch and rebase tests, for example:
  - `tests/test_branch_parent_target_promotion.py`
  - `tests/test_branch_rebase.py`
  - `tests/test_parallel_fork_write.py`
- Required behavior coverage:
  - create a chapter branch from `main`, then section branch from chapter branch, then scene branch from section branch
  - promote a scene branch into its section parent without mutating `main`
  - promote a section branch into its chapter parent without mutating `main`
  - detect stale parent revision when a parent branch advances
  - perform explicit rebase or refreshed-child creation
  - create sibling writer branches in one fork group and refuse sibling reads during execution
  - assemble sibling results on an assembly branch before promotion
  - refuse promotion when validation has not passed

## Definition Of Done
- A branch may be created from a parent branch snapshot, not only from canonical `main`.
- A branch may promote into its parent branch or into `main`, with truthful receipts for the actual target.
- Stale parent snapshots are detected and surfaced as a real lifecycle/integrity condition.
- An explicit rebase capability exists and does not silently overwrite existing branch history.
- Sibling writer branches can execute in parallel under one fork group without shared-state mutation.
- Assembly and promotion remain validation-gated and off-parent until approved.

## Notes
- This step is where branch hierarchy becomes operational, not just conceptual.
- The first implementation should stay conservative:
  - explicit actions
  - explicit validation
  - no hidden semantic prose merge promises
- Automatic prose-level reconciliation may exist later, but this step should first make the isolation, lineage, and merge surfaces truthful.
