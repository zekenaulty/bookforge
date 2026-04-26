# 2026-04-26 0072 Writer Assembly Staging

## Summary
- Extended `create_assembly_branch(...)` so it does more than create an empty off-parent branch.
- It now stages scoped draft scene outputs from fork-group sibling writer branches into the assembly branch snapshot.
- Added `validate_assembly_branch(...)` and `workflow validate-assembly-branch` to deterministically verify staged sibling writer outputs before promotion.

## Rules
- Sibling branches must still share the same parent node and parent snapshot revision.
- Parent staleness is checked against the actual parent branch:
  - `main` parent checks current `main`
  - derived parent checks the parent branch current node
- Assembly reads sibling outputs only after sibling execution, not during sibling execution.
- The assembly branch remains off-parent until validation and explicit promotion.
- Validation only checks staged output presence. It does not perform semantic seam or continuity review.

## Validation
- Added coverage that two sibling writer branches stage separate scene files into one assembly branch while leaving canonical `main` untouched.
- Added coverage that deterministic assembly validation marks a staged assembly branch as `assembled_pending_promotion`.
- Added coverage that a validated assembly branch can promote staged writer outputs to `main`.
- Focused non-outline regression set passed with `99` tests.
