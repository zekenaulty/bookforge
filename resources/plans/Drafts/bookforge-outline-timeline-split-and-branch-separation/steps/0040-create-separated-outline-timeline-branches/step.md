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
