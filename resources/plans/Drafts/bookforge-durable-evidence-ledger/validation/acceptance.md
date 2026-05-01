# Acceptance Criteria

## Schema And Store
- SQLite schema initializes under a book evidence directory.
- Schema version metadata is persisted and queryable.
- Store uses WAL mode and transactional writes.
- Store can serialize and deserialize normalized scopes, timeline nodes, operation runs, receipts, artifacts, branches, issues, dependencies, approvals, spans, and citations.

## Backfill
- Backfill ingests current `runtime/supervision/**/execution_results.jsonl`.
- Backfill ingests state surface and issue histories where present.
- Backfill ingests recovery receipts and recovery manifests where present.
- Backfill registers produced artifact paths with content hashes when files exist.
- Running backfill twice does not duplicate operation, receipt, artifact, branch, or span rows.

## Write-Through
- A new execution result still writes existing JSONL output.
- The same execution result creates or updates ledger rows.
- Produced artifacts from `ExecutionResult.produced_artifacts` are registered with status, scope, branch, hash, and storage path.
- Recovery receipts are represented in the ledger without losing recovery-specific fields such as quarantined and removed paths.

## Query Surface
- Evidence queries can narrow by book, branch, scope, action, receipt type, artifact status, and freshness.
- Evidence queries can answer which receipts and artifacts belong to one operation.
- Evidence queries can answer which artifacts are safe, stale, diagnostic-only, or branch-local for a selected scope.
- Evidence queries expose stable IDs suitable for Nanda response capsules and action cards.

## Reader Anchors
- Reader artifact/span records include artifact ID, source hash, branch/canonical target, artifact status, freshness, offsets, and scope.
- Diagnostic fallback selections are reported as not mutation-safe.
- Branch-local selections are distinguishable from canonical selections.

## Compatibility
- Existing tests for supervision, branch, recovery, scene actions, capability projection, reader, and author assets continue to pass.
- Existing file locations remain readable by older code during migration.
- CLI can output JSON suitable for Nanda fixtures.
