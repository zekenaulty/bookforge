# 0080 Reserve Vector And External Store Adapters

Status: designed  
Depends On: 0070

## Goal
Document the deferred path from SQLite evidence to richer document, vector, and external database layers without implementing them prematurely.

## Detailed Work
- Define the adapter boundary for later stores:
  - SQLite local store
  - future Postgres or service-backed relational store
  - future object/document store
  - future vector index
- Define what vector chunks must cite:
  - artifact ID
  - artifact version ID
  - scope ID
  - branch/canonical target
  - source hash
  - span offsets
  - embedding model
  - freshness status
- Define migration constraints:
  - no uncited memory retrieval
  - no branch-agnostic retrieval
  - no vector source without artifact hash
  - no hidden write path that bypasses operation/receipt evidence
- Add a future-plan handoff note.

## Likely Files Touched
- `resources/plans/Drafts/bookforge-durable-evidence-ledger/artifacts/future-vector-and-external-store-boundary.md`
- `docs/help/evidence.md`

## Tests
- Documentation-only step.

## Definition Of Done
- Future vector/store work has a clear boundary.
- Current SQLite work remains focused on stable evidence identity, not semantic retrieval.
