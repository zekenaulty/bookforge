# Reader Prose Anchors

Status: implemented

## Why

Nanda needs to turn a user-selected passage into a truthful action target without guessing from raw reader text. The reader already exposes canonical and branch-scoped prose, but it did not prove the exact source artifact, selected span, hash, freshness, or mutation-safety status.

## Implemented Surface

- Added `bookforge.query.get_book_reader_anchor(...)`.
- Added CLI command `bookforge book reader-anchor`.
- Added capability descriptor `query.book_reader_anchor`.
- Added focused tests for:
  - canonical scene span anchors
  - branch-scoped scene anchors
  - chapter-level inspect-only anchors
  - invalid span handling
  - CLI parse coverage
  - capability fixture coverage

## Contract Shape

The anchor is read-only and reports:

- selected scope and `TimelineNodeRef`
- `branch_id`
- canonical-relative and execution-root-relative source paths
- full source hash
- selected span offsets
- selected text hash
- `reader_status` such as `canonical_current`, `branch_current`, `missing`, or `invalid_span`
- `artifact_status`
- `freshness_status`
- `valid_as_mutation_target`
- `invalid_reason`
- allowed mutation scopes

Scene anchors are valid mutation targets. Chapter anchors are inspect-only until narrowed to a scene. Branch anchors are explicitly branch-scoped so Nanda can prevent branch-local text from being treated as canonical.

## Nanda Use

Before converting "fix this passage" into a mutation request, Nanda should request a reader anchor for the selected span and require:

- `valid_as_mutation_target == true`
- expected `branch_id`
- expected `source_hash`
- acceptable `reader_status`

The anchor proves the source and span. It does not execute a rewrite and it does not imply dynamic readiness for a rewrite action.
