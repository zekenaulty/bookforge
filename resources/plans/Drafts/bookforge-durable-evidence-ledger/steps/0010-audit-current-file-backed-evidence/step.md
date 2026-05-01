# 0010 Audit Current File-Backed Evidence

Status: designed  
Depends On: -

## Goal
Create a precise map of the current BookForge evidence surfaces and how Nanda is already trying to consume them.

## Detailed Work
- Inspect current contract objects:
  - `src/bookforge/contracts/execution_result.py`
  - `src/bookforge/contracts/produced_artifact.py`
  - `src/bookforge/contracts/recovery.py`
  - `src/bookforge/contracts/state_surface.py`
  - `src/bookforge/contracts/issue_ticket.py`
- Inspect emitters:
  - `src/bookforge/supervision/emit.py`
  - `src/bookforge/supervision/paths.py`
  - `src/bookforge/execution/scene_actions.py`
  - `src/bookforge/execution/recovery_common.py`
  - `src/bookforge/execution/projection_actions.py`
  - `src/bookforge/execution/author_assets.py`
- Inspect current query surfaces:
  - branch inventory/detail/artifact/diff
  - reader views
  - capability projection
  - recovery health/impact/anchor/plan views
  - outline lineage audit and matrix
- Inspect Nanda evidence needs:
  - response capsules
  - post-response proposed actions
  - branch-scope transition receipts
  - recovery workbench
  - reader anchors
  - action cards
- Produce a mapping from current files/contracts to target ledger tables.

## Likely Files Touched
- `resources/plans/Drafts/bookforge-durable-evidence-ledger/artifacts/current-evidence-storage-audit.md`
- `resources/plans/Drafts/bookforge-durable-evidence-ledger/artifacts/nanda-evidence-alignment.md`

## Tests
- Planning-only step.
- Manual validation: audit names every current append path and history file used by runtime supervision/recovery.

## Definition Of Done
- Current evidence files and emitters are listed.
- Existing evidence contracts are mapped to proposed ledger rows.
- Nanda evidence asks are mapped to ledger fields.
- Gaps are classified as schema, backfill, write-through, query, reader-anchor, or future-vector work.
