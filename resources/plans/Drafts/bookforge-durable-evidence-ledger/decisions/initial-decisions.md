# Initial Decisions

## SQLite First
SQLite is the first durable evidence backend. It is sufficient for local authoring, branch/recovery inspection, and Nanda bridge queries. Postgres or a service DB can be introduced later through a store adapter after contracts stabilize.

## Files Remain Payload Storage
Markdown, JSON, reports, prompt packages, prose, and snapshots remain on disk. The ledger stores identity, status, hashes, provenance, branch/scope coordinates, and storage paths.

## Per-Book Before Global
The first ledger is per book under `workspace/books/<book_id>/runtime/evidence/`. Workspace-level author asset evidence is a follow-on unless author asset flows become the first implementation pressure.

## Append-First Semantics
Operation runs, receipts, artifact versions, issue tickets, approvals, dependencies, spans, and citations are append-first records. Latest views may be derived, but the ledger should preserve history.

## Backfill Is Required
Existing file-backed evidence is too valuable to ignore. The first implementation must backfill current supervision and recovery histories before relying on write-through for new actions.

## Capability Projection Is Not The Ledger
Capability projection describes what BookForge can do. The evidence ledger records what was queried, attempted, refused, produced, validated, or promoted. Nanda needs both.
