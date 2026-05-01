# 0030 Implement Ledger Store And Idempotent Backfill

Status: designed  
Depends On: 0020

## Goal
Add the SQLite store and backfill existing BookForge supervision/recovery evidence into ledger rows.

## Detailed Work
- Add a store wrapper that:
  - opens per-book evidence DB
  - enables WAL
  - applies migrations
  - writes rows transactionally
  - exposes focused insert/upsert/query primitives
- Add backfill for:
  - `runtime/supervision/main/execution_results.jsonl`
  - `runtime/supervision/branches/*/execution_results.jsonl`
  - `state_surface_history.jsonl`
  - `issues_history.jsonl`
  - branch manifests and current nodes
  - recovery manifests and `recovery_receipts.jsonl`
  - produced artifacts embedded in execution results
- Register artifact hashes for existing artifact paths when files exist.
- Mark missing files as stale or missing without failing the whole backfill.
- Write a backfill summary receipt or report.

## Likely Files Touched
- `src/bookforge/evidence/store.py`
- `src/bookforge/evidence/backfill.py`
- `src/bookforge/evidence/paths.py`
- `src/bookforge/query/evidence.py` for minimal smoke query.
- `tests/test_evidence_backfill.py`

## Tests
- Backfill existing fixture histories into operation, receipt, artifact, branch, issue, and scope rows.
- Running backfill twice does not duplicate rows.
- Missing artifact files produce stale/missing artifact evidence rather than crashing.
- Branch-local evidence remains branch-local.
- Recovery receipts preserve quarantined and removed path details.

## Definition Of Done
- `bookforge` can create a per-book evidence database.
- Existing JSONL/file histories are represented in ledger tables.
- Backfill is idempotent.
- Backfill produces a summary useful to Nanda/operator inspection.
