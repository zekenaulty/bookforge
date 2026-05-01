# 2026-04-28 Author Asset Actions

## Summary
- Added BookForge-owned author-library mutation actions:
  - `create_author`
  - `refine_author`
- Added workflow family:
  - `author_assets`
- Added virtual selector scope for author library actions:
  - `book_id="__author_library__"`
- Added execution exports:
  - `build_create_author_request(...)`
  - `create_author_action(workspace, request)`
  - `build_refine_author_request(...)`
  - `refine_author_action(workspace, request)`
- Added CLI receipt surfaces:
  - `bookforge author create ... [--json]`
  - `bookforge author refine <author_ref> ... [--json]`

## Contract Notes
- Author profiles remain global workspace assets under `workspace/authors`.
- Create/refine actions emit `execution_result_v1`.
- Produced artifacts are marked `authoritative` because the versioned author library is the source of truth after the write succeeds.
- Refinement creates a successor version and does not overwrite prior author versions.
- Book author selection remains a separate future action because it mutates book metadata, not the author library.

## Capability Projection Delta
- Promoted from designed gap to implemented action descriptors:
  - `action.create_author`
  - `action.refine_author`
- Removed:
  - `gap.author_assets.create_refine`
- Kept future gaps for author selection/rollback/preview in successor planning rather than overloading the first mutation slice.

## Validation
- Focused tests:
  - `python -m pytest tests/test_author_asset_actions.py tests/test_capability_projection.py tests/test_scope_contracts.py -q`
  - Result: 16 passed.
- Compile check:
  - `python -m compileall -q src tests`

