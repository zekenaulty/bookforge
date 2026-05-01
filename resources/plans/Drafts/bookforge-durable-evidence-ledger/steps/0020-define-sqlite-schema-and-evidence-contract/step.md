# 0020 Define SQLite Schema And Evidence Contract

Status: designed  
Depends On: 0010

## Goal
Freeze the first SQLite schema and Python contract boundaries for BookForge evidence.

## Detailed Work
- Add schema design for:
  - `schema_metadata`
  - `ledger_scope` or an equivalent distinction between book and workspace ledgers
  - `scopes`
  - `timeline_nodes`
  - `branches`
  - `operation_runs`
  - `receipts`
  - `artifacts`
  - `artifact_versions`
  - `issue_tickets`
  - `approvals`
  - `dependencies`
  - `artifact_spans`
  - `citations`
  - `asset_refs` for workspace-level author assets and future cross-book assets
- Define ID derivation rules for:
  - backfilled operations
  - live operations
  - receipts
  - artifacts
  - artifact versions
  - spans
  - citations
- Define evidence row payload strategy:
  - normalized indexed fields for BookForge/Nanda queries
  - JSON payload column for contract-specific details
- Define artifact hash and freshness rules.
- Define mutation-safe anchor rules.
- Define how recovery receipts map into general receipt rows without losing recovery-specific fields.
- Define how author asset create/refine results map into operation, receipt, artifact, and asset rows without requiring a fake book ID.

## Likely Files Touched
- `src/bookforge/evidence/schema.py`
- `src/bookforge/evidence/ids.py`
- `src/bookforge/evidence/hash.py`
- `src/bookforge/evidence/contracts.py` if a separate contract module is needed.
- `tests/test_evidence_schema.py`

## Tests
- Schema initializes in a temporary book root.
- Required tables and indexes exist.
- Schema metadata is written.
- Invalid artifact status or missing scope fields fail at contract boundary.
- ID derivation is deterministic for the same source payload.

## Definition Of Done
- SQLite schema is explicit in code.
- Schema version metadata exists.
- Artifact status, freshness, branch/canonical target, and scope identity are first-class fields.
- Workspace-level author asset evidence is represented without pretending it belongs to a normal book branch.
- Backfill/live ID rules are documented and tested.
- Deferred vector table is documented but not implemented unless needed as an empty reserved migration.
