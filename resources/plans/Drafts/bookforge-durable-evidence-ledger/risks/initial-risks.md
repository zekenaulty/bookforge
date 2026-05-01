# Initial Risks

## Ledger/File Drift
Dual-write can split truth if JSONL files update but SQLite does not, or vice versa.

Mitigation:
- Wrap ledger writes in a small writer API.
- Add tests that compare JSONL emission to ledger rows.
- Surface ledger-write failure in `ExecutionResult.details` or a diagnostic ticket instead of silently ignoring it.

## Unstable Backfill IDs
If backfill IDs depend on current timestamps or traversal order, Nanda cannot cite them reliably.

Mitigation:
- Derive backfill IDs from stable fields: book, branch, node, action, request/result IDs, path, content hash, and JSONL line identity where needed.
- Run idempotent backfill tests twice and compare row counts and IDs.

## Diagnostic Fallback Becomes Mutation Source
Reader fallback or stale file artifacts could become selectable mutation anchors.

Mitigation:
- Store artifact status and freshness separately.
- Require `source_status=canonical_current` or `branch_current` for mutation-safe anchors.
- Query surfaces must explicitly report refusal reasons.

## Schema Bloat
Trying to model vectors, memory, recovery, approvals, and all state projections at once could stall implementation.

Mitigation:
- Implement relational identity and evidence refs first.
- Keep payload JSON for flexible details.
- Defer vector chunks and rich document retrieval until artifact IDs and spans are stable.

## Hidden Source Of Truth
SQLite could accidentally become a competing canonical store for outline/prose/state.

Mitigation:
- Ledger records evidence and provenance; canonical content remains existing BookForge artifacts until a later storage migration plan says otherwise.
- Queries must report the payload path/hash behind any artifact row.
