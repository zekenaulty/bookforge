# 2026-04-28 Branch-Local Commit Receipt Audit

BookForge audited `apply_scene_commit` for Nanda author-loop exposure.

Result:

- `apply_scene_commit` is branch-aware.
- On `main`, it emits canonical reconciliation details including
  `canonical_change_status`.
- On a derived branch, it writes only inside that branch snapshot and emits
  branch-local reconciliation details.
- Branch-local execution results intentionally do not emit
  `canonical_change_status`.
- Reconciled results now include an explicit `canonical_changed` boolean:
  - `true` when a main-branch action produces a canonical state change
  - `false` for branch-local actions

Why this matters:

- Nanda can display branch-local work without implying canonical mutation.
- `AuthorWorkLoop` can preserve completed branch artifacts after interruption.
- The Branch Workbench can distinguish "branch changed" from "book canonical
  state changed" using receipts instead of file inference.

Validation:

- Focused tests prove:
  - branch-local `apply_scene_commit` writes scene prose only to the branch
    snapshot
  - the canonical main scene file remains absent
  - branch-local execution results include `branch_change_status`
  - branch-local execution results include `canonical_changed: false`
  - branch-local execution results still omit `canonical_change_status`
  - main-branch `apply_scene_commit` includes `canonical_change_status:
    canonical` and `canonical_changed: true`

Nanda contract guidance:

- `apply_scene_commit` can be shown for derived branches as a branch-local
  commit/finalize operation.
- It should not be described as changing canonical book state unless the receipt
  says `canonical_changed: true`.
- Promotion remains a separate canonical operation with its own approval and
  reconciliation path.
