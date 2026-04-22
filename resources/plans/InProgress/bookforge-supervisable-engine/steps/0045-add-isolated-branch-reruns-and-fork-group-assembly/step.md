# 0045 Add Isolated Branch Reruns And Fork Group Assembly

Status: completed

## Goal
- Add explicit branch isolation and merge semantics so reruns and future parallel section work can execute safely without contaminating canonical state.

## Problem
- The chapter 3 chimera class happened because recovery and continuation logic ran against live state without isolation.
- A single-branch rerun and a multi-branch fan-out/fan-in assembly are not the same thing, but they need to share the same branch primitives.
- If we build rerun branches without accounting for fork groups, later parallel writing work will inherit branch semantics that are too narrow.

## Detailed Work
- Add branch creation from a parent `TimelineNodeRef` with:
  - unique `branch_id`
  - inherited immutable source lineage
  - declared parent node
- Support isolated rerun branches for scoped phase re-execution:
  - branch-local writes only
  - branch-scoped `StateSurface` and `IssueTicket` output
  - no direct mutation of canonical state
- Add `fork_group_id` for sibling branches that share:
  - the same parent node
  - the same pre-fork canonical ancestry
- Freeze the fork-group parent snapshot for the lifetime of the group unless an explicit rebase or recreation step is performed.
- Enforce the fan-out rule:
  - sibling branches may read from the parent node and pre-fork canonical state
  - sibling branches may not read one another during execution
- Refuse assembly when canonical preconditions required by the frozen parent snapshot are no longer satisfied.
- Distinguish merge types explicitly:
  - `promotion` for single-branch replacement or adoption into `main`
  - `assembly` for combining multiple sibling branches into an assembly branch that is still non-canonical
- Create an explicit assembly branch for fork-group merge work.
- Run seam audit and any seam-local repair on the assembly branch, not on `main`.
- Require explicit reconciliation and integrity validation before either promotion or validated assembly promotion returns content to `main`.
- Reuse chapter seam audit or equivalent join validation as the assembly-branch integrity gate for sibling outputs.
- Classify branch outcomes explicitly:
  - `promote_ready`
  - `needs_review`
  - `discard`
- Map those branch outcomes to public execution-result states and canonical-change status explicitly in the shared contract docs.
- Preserve lineage traceability from main -> parent node -> branch nodes -> promotion or assembly result.

## Files Touched
- `src/bookforge/branching.py`
- `src/bookforge/contracts/__init__.py`
- `src/bookforge/contracts/branch_manifest.py`
- `src/bookforge/contracts/vocabulary.py`
- `src/bookforge/query/_common.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/supervision/__init__.py`
- `src/bookforge/supervision/emit.py`
- `src/bookforge/supervision/paths.py`
- `tests/test_branch_execution.py`
- `tests/test_branch_promotion.py`
- `tests/test_fork_group_assembly.py`
- `tests/test_scope_contracts.py`

## Tests
- `python -m pytest --basetemp .pytest_tmp_0045 tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scope_contracts.py`
- `python -m pytest --basetemp .pytest_tmp_0045_regression tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py`
- Add coverage for:
  - branch creation from a declared parent node
  - branch scope preservation in manifest and current-node projection
  - refusal on silent source switching
  - discard leaving canonical state untouched
  - sibling branches sharing a `fork_group_id`
  - no-cross-read enforcement for sibling branches
  - refusal when a fork-group parent snapshot is stale against required canonical preconditions
  - assembly branch blocked from promotion by failed seam validation

## Definition Of Done
- A derived branch can rerun a scoped phase without mutating canonical state directly.
- Every branch records its parent `TimelineNodeRef`.
- Sibling branches in a fork group share the same parent node and `fork_group_id`.
- Promotion and assembly are distinct code paths with distinct validation gates.
- A failed or discarded branch leaves canonical state untouched.
- Assembly can surface seam issues as an explicit validation result on the assembly branch before promotion to `main`.
- Fork groups cannot silently merge against incompatible canonical advancement; they must rebase, recreate, or refuse.

## Notes
- This story defines the branching primitives broadly enough for sequential reruns and future parallel writing, even if the full fan-out scheduler lands later.
- Assembly remains off `main`. The current implementation provides an explicit assembly branch plus validation-state recording and promotion gating; automatic seam-audit execution can plug into that branch seam later without changing the contract model.
