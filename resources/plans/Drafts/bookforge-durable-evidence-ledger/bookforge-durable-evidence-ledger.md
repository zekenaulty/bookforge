# bookforge-durable-evidence-ledger

## Compiled Plan Metadata

- Plan Scope: `Drafts/bookforge-durable-evidence-ledger`
- Compiled At (UTC): `2026-04-28T03:54:06Z`
- Source Document Count: `15`
- Projection File: `bookforge-durable-evidence-ledger.md`

## Contents

1. `plan.md`
2. `decisions/initial-decisions.md`
3. `risks/initial-risks.md`
4. `validation/acceptance.md`
5. `steps/index.md`
6. `steps/0010-audit-current-file-backed-evidence/step.md`
7. `steps/0020-define-sqlite-schema-and-evidence-contract/step.md`
8. `steps/0030-implement-ledger-store-and-idempotent-backfill/step.md`
9. `steps/0040-dual-write-execution-recovery-author-and-artifact-evidence/step.md`
10. `steps/0050-add-evidence-query-surfaces-and-cli/step.md`
11. `steps/0060-add-reader-anchor-and-citation-evidence/step.md`
12. `steps/0070-add-nanda-consumption-fixtures-and-contract-docs/step.md`
13. `steps/0080-reserve-vector-and-external-store-adapters/step.md`
14. `artifacts/current-evidence-storage-audit.md`
15. `artifacts/nanda-evidence-alignment.md`

---

## Source 1: `plan.md`

# BookForge Durable Evidence Ledger

Status: Draft  
Stage: Drafts  
Owner: BookForge engine workstream  
Created: 2026-04-27

## Objective
- Add SQLite-backed evidence ledgers that index BookForge operations, receipts, artifacts, branches, scopes, citations, approvals, dependencies, issue tickets, and author asset operations.
- Keep existing workspace files as payload/object storage while making evidence queryable without filesystem archaeology.
- Give Nanda stable IDs and relationships for response capsules, action cards, reader anchors, recovery workbench, branch-local authoring, and later citation-aware memory.

## Why Now
- BookForge now exposes legal actions, readiness, scene-phase actions, recovery primitives, capability projection, reader views, branch views, and receipts.
- Nanda is moving toward post-response proposed actions, action receipts, response capsules, branch-scope transitions, and recovery workbench flows.
- Current BookForge evidence is real but fragmented:
  - `runtime/supervision/**/execution_results.jsonl`
  - `state_surface_history.jsonl`
  - `issues_history.jsonl`
  - branch manifests and snapshots
  - recovery manifests and `recovery_receipts.jsonl`
  - produced artifact receipts embedded in execution results
- Those files prove work happened, but they do not yet provide stable cross-cutting queries like "what receipts prove this answer?", "what artifact version backs this selection?", "which branch produced this prose?", or "what downstream scopes are stale because of this recovery branch?"

## Core Decision
SQLite is the first durable evidence substrate.

This is not a full database-platform migration. BookForge should continue writing the current file artifacts for compatibility. The ledger becomes the indexed evidence layer over those artifacts.

## Storage Model
### Per-Book Ledger
Default location:

```text
workspace/books/<book_id>/runtime/evidence/bookforge_evidence.sqlite
```

This ledger owns book-scoped execution, receipts, artifacts, branches, scopes, issues, reader anchors, dependencies, approvals, and citations.

### Workspace Ledger
Location:

```text
workspace/runtime/evidence/workspace_evidence.sqlite
```

This is for workspace-level assets such as author profiles, author versions, global capability snapshots, and cross-book references.

Author asset create/refine is now a real first pressure point from Nanda. The first schema should therefore support workspace-level operation, receipt, and artifact evidence even if book-scoped ledgers remain the primary implementation target.

### File Payloads Remain
Large JSON, Markdown, prompt packages, prose, reports, and snapshots remain as files. The ledger stores IDs, hashes, status, scope, branch, provenance, and storage URIs/paths.

## Evidence Model
### Required Tables
- `schema_metadata`: ledger schema version, created/updated timestamps, migration history.
- `scopes`: normalized `ScopeSelector` payloads with stable scope IDs.
- `timeline_nodes`: normalized `TimelineNodeRef` payloads with branch/fork/workflow identity.
- `branches`: branch and fork-group identity, parent node, lifecycle, promotion state, current head.
- `operation_runs`: one row per query/action/macro/recovery execution.
- `receipts`: one row per query result, readiness check, precondition, action result, validation, refusal, postcondition, or branch transition.
- `artifacts`: one row per produced or read artifact with status, freshness, scope, branch, hash, and storage URI/path.
- `artifact_versions`: versioned content refs and parent/source refs.
- `issue_tickets`: categorized integrity/safety findings linked to operation/receipt/scope/node.
- `approvals`: approval requests and decisions for gated actions.
- `dependencies`: downstream dependency edges, invalidation reasons, stale/affected flags.
- `artifact_spans`: selected prose/outline/state anchors with source hash and offsets.
- `citations`: source artifact/receipt spans cited by answers, reports, artifacts, or receipts.
- `asset_refs`: workspace-owned asset refs such as authors and author versions when the evidence is not naturally book-scoped.

### Deferred Tables
- `embedding_chunks`: vector index metadata. Do not implement until stable artifact IDs, hashes, branch IDs, and citation spans exist.

## Evidence Identity Rules
- Every operation gets an `operation_id`.
- Every receipt gets a `receipt_id`.
- Every artifact gets an `artifact_id`.
- Every normalized scope gets a `scope_id`.
- Every reader selection or prose anchor gets an `artifact_span_id`.
- IDs must be stable under idempotent backfill.
- A rerun that genuinely produces new evidence gets new operation/receipt IDs, not silent overwrite.

## Artifact Truth Rules
- Artifact status remains one of:
  - `authoritative`
  - `provisional`
  - `derived`
  - `diagnostic`
- Freshness is separate from artifact status.
- Branch/canonical target is separate from artifact status.
- Diagnostic filesystem fallback can be indexed, but must not become a mutation-safe anchor.
- Thought signatures can be indexed as context evidence, but not as proof of execution state or canonical truth.

## Query Expectations
BookForge should expose read-only evidence queries before broad mutation uses them:

- `get_evidence_operation(...)`
- `list_evidence_operations(...)`
- `list_evidence_receipts(...)`
- `list_evidence_artifacts(...)`
- `get_artifact_evidence(...)`
- `get_scope_evidence_summary(...)`
- `get_reader_anchor_evidence(...)`
- `list_scope_dependencies(...)`
- `list_approval_requests(...)`

These queries should support narrowing by `book_id`, `branch_id`, `fork_group_id`, `scope`, `capability_id`, `action`, `receipt_type`, artifact status, freshness, and time bounds.

## Nanda Alignment
This plan directly supports Nanda needs from `nanda-author-start-authoring`:

- Response capsules cite receipt refs and artifact refs instead of carrying raw planning state.
- Post-response proposed action execution can validate idempotency and expected receipts.
- Branch-scope transition receipts can reference the exact source action receipt.
- Action cards can show previous receipts, expected receipts, and artifact availability.
- Reader selections can become mutation-safe anchors only when backed by stable artifact/span evidence.
- Recovery workbench can show branch-local changes, validation blockers, blast radius, approvals, and promotion readiness without raw file archaeology.
- Author creation/refinement can return versioned author asset receipts with artifact refs and hashes.
- Later recall and vector retrieval can cite exact artifact versions and spans.

## Scope
In scope:
- Design and implement a SQLite ledger store.
- Support per-book and minimal workspace-level ledgers.
- Backfill existing BookForge file evidence into ledger rows.
- Dual-write new execution/recovery evidence into files and ledger.
- Dual-write author asset create/refine evidence into workspace evidence rows.
- Add evidence query surfaces and CLI output.
- Add stable reader/prose anchor evidence.
- Add tests proving idempotent backfill, write-through, branch scoping, and artifact hash/freshness behavior.
- Document Nanda consumption expectations.

Out of scope:
- Replacing workspace files as payload storage.
- Full Postgres/Mongo migration.
- Vector retrieval implementation.
- Nanda UI work.
- Broad recovery orchestration changes beyond evidence emitted by existing actions.
- Storing raw provider hidden reasoning.

## Deliverables
- `src/bookforge/evidence/schema.py`
- `src/bookforge/evidence/store.py`
- `src/bookforge/evidence/backfill.py`
- `src/bookforge/evidence/hash.py`
- `src/bookforge/evidence/writer.py`
- `src/bookforge/query/evidence.py`
- `src/bookforge/query/workspace_evidence.py` or a shared evidence query that handles workspace scope.
- CLI commands under `bookforge evidence ...`
- Backfill command for existing workspaces.
- Tests for schema, store, backfill, write-through, and query surfaces.
- Nanda-facing fixture with operations, receipts, artifacts, spans, branches, and approval-gated examples.

## Plan-Level Definition Of Done
- A book can initialize an evidence ledger without changing existing workspace file behavior.
- Existing supervision/recovery histories can be backfilled idempotently.
- New execution results write both current JSONL files and ledger rows.
- Produced artifacts are registered with stable IDs, hashes, statuses, branch/canonical target, and storage paths.
- Author create/refine actions register versioned author asset artifacts with stable IDs and hashes.
- Evidence queries answer "what proves this action/result/artifact/scope?" without scanning the full file tree.
- Reader selections can report whether they are mutation-safe anchors.
- Nanda can consume a fixture that includes operation refs, receipt refs, artifact refs, branch refs, and anchor refs.
- Existing tests continue to pass during the compatibility phase.

## Risks
- Ledger/file drift if dual-write is inconsistent.
- Overwide schema that tries to solve vector memory before stable evidence exists.
- Backfill producing unstable IDs from timestamps or path-specific noise.
- Treating diagnostic fallback artifacts as safe mutation anchors.
- Making SQLite a hidden second source of truth instead of an evidence index over file payloads.

## First Implementation Bias
- Start with schema, idempotent backfill, and queryability.
- Keep JSON payload columns for flexible contract payloads, but index the fields Nanda needs.
- Use transactions for each operation emission.
- Make write-through best effort only if failure semantics are explicit; for mutation actions, ledger write failure should become visible, not silent.
- Do not build vector retrieval until artifact spans and citations are stable.

---

## Source 2: `decisions/initial-decisions.md`

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

---

## Source 3: `risks/initial-risks.md`

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

---

## Source 4: `validation/acceptance.md`

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

---

## Source 5: `steps/index.md`

# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-audit-current-file-backed-evidence | designed | - | Produce a concrete inventory of current evidence files, contracts, emitters, and Nanda evidence needs. |
| 0020-define-sqlite-schema-and-evidence-contract | designed | 0010 | Freeze the first book/workspace ledger schema, ID rules, freshness/status rules, and Python contract boundaries. |
| 0030-implement-ledger-store-and-idempotent-backfill | designed | 0020 | Add SQLite store plus backfill from current supervision/recovery histories. |
| 0040-dual-write-execution-recovery-author-and-artifact-evidence | designed | 0030 | Wire current emitters to write file artifacts and ledger rows consistently, including author asset actions. |
| 0050-add-evidence-query-surfaces-and-cli | designed | 0040 | Expose operation/receipt/artifact/scope/branch evidence through Python query and CLI JSON. |
| 0060-add-reader-anchor-and-citation-evidence | designed | 0050 | Make prose/reader selections provenance-backed and mutation-safety aware. |
| 0070-add-nanda-consumption-fixtures-and-contract-docs | designed | 0060 | Provide fixture data and docs for Nanda response capsules, action cards, branch transitions, and recovery workbench. |
| 0080-reserve-vector-and-external-store-adapters | designed | 0070 | Document deferred vector/external DB adapter boundaries without implementing them prematurely. |

---

## Source 6: `steps/0010-audit-current-file-backed-evidence/step.md`

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

---

## Source 7: `steps/0020-define-sqlite-schema-and-evidence-contract/step.md`

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

---

## Source 8: `steps/0030-implement-ledger-store-and-idempotent-backfill/step.md`

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

---

## Source 9: `steps/0040-dual-write-execution-recovery-author-and-artifact-evidence/step.md`

# 0040 Dual-Write Execution Recovery Author And Artifact Evidence

Status: designed  
Depends On: 0030

## Goal
Wire current BookForge emitters so new work writes both legacy file artifacts and ledger evidence, including author asset operations.

## Detailed Work
- Add a central evidence writer that can ingest:
  - `ExecutionResult`
  - `ProducedArtifactReceipt`
  - `IssueTicket`
  - `StateSurface`
  - `RecoveryReceipt`
  - branch manifest/current node snapshots
  - author asset create/refine execution results and produced artifacts
- Integrate with:
  - `src/bookforge/supervision/emit.py`
  - `src/bookforge/execution/scene_actions.py`
  - `src/bookforge/execution/projection_actions.py`
  - `src/bookforge/execution/recovery_common.py`
  - `src/bookforge/execution/branch_actions.py`
  - `src/bookforge/execution/author_assets.py` using workspace-level evidence.
- Preserve current JSONL and file output paths.
- Define failure behavior:
  - read-only queries can report ledger write warnings.
  - mutation actions should surface ledger write failure as a diagnostic issue or failed postcondition rather than silently losing evidence.
- Add operation-run lifecycle rows for starts, completions, refusals, pauses, and failures where feasible.

## Likely Files Touched
- `src/bookforge/evidence/writer.py`
- `src/bookforge/supervision/emit.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/execution/recovery_common.py`
- `src/bookforge/execution/branch_actions.py`
- `src/bookforge/execution/projection_actions.py`
- `tests/test_evidence_write_through.py`

## Tests
- A scene action writes legacy `execution_results.jsonl` and ledger rows.
- A recovery action writes `recovery_receipts.jsonl` and ledger rows.
- An author create/refine action writes workspace evidence rows and artifact refs.
- Produced artifacts are registered with status, hash, branch/canonical target, and path.
- Ledger row operation/receipt IDs are surfaced in result details or queryable by request ID.
- Failure path emits visible diagnostic evidence.

## Definition Of Done
- New execution evidence is dual-written.
- Existing compatibility files remain unchanged for current consumers.
- Ledger contains enough rows for Nanda to cite action execution and produced artifacts.
- Nanda can cite author asset creation/refinement receipts without treating them as book mutations.

---

## Source 10: `steps/0050-add-evidence-query-surfaces-and-cli/step.md`

# 0050 Add Evidence Query Surfaces And CLI

Status: designed  
Depends On: 0040

## Goal
Expose stable read-only evidence queries for Nanda, operators, and tests.

## Detailed Work
- Add `src/bookforge/query/evidence.py` with functions such as:
  - `get_evidence_operation(...)`
  - `list_evidence_operations(...)`
  - `list_evidence_receipts(...)`
  - `list_evidence_artifacts(...)`
  - `get_artifact_evidence(...)`
  - `get_scope_evidence_summary(...)`
  - `list_scope_dependencies(...)`
  - `list_approval_requests(...)`
- Add CLI commands:
  - `bookforge evidence init --book ...`
  - `bookforge evidence backfill --book ...`
  - `bookforge evidence operations --book ...`
  - `bookforge evidence receipts --book ...`
  - `bookforge evidence artifacts --book ...`
  - `bookforge evidence scope --book ...`
- Ensure JSON output is compact and Nanda-friendly.
- Add filters for branch, action, receipt type, artifact status, freshness, chapter/section/scene, and time bounds.
- Add capability projection evidence refs where appropriate without merging static capability and dynamic evidence.

## Likely Files Touched
- `src/bookforge/query/evidence.py`
- `src/bookforge/cli.py`
- `docs/help/evidence.md`
- `docs/help/index.md`
- `tests/test_evidence_query_cli.py`

## Tests
- Query functions return stable IDs and normalized payloads.
- CLI outputs valid JSON.
- Filtering by branch/scope/action/status works.
- Missing ledger produces a clear unavailable/needs-backfill response.

## Definition Of Done
- Nanda can query BookForge evidence without reading JSONL files directly.
- Operators can inspect recent operations, receipts, artifacts, and scope summaries from CLI.
- Evidence queries distinguish missing ledger from healthy empty result.

---

## Source 11: `steps/0060-add-reader-anchor-and-citation-evidence/step.md`

# 0060 Add Reader Anchor And Citation Evidence

Status: designed  
Depends On: 0050

## Goal
Make reader/prose selections provenance-backed so Nanda can safely convert user-highlighted text into scoped action targets.

## Detailed Work
- Register reader artifacts with:
  - `artifact_id`
  - artifact type
  - scope selector
  - branch/canonical target
  - artifact status
  - freshness status
  - content hash
  - path/storage URI
- Add artifact span records with:
  - `artifact_span_id`
  - artifact ID
  - source hash
  - start/end offsets
  - excerpt policy
  - mutation safety status
  - refusal reason when not safe
- Add citation rows linking:
  - reader spans to response capsules
  - action receipts to produced artifacts
  - recovery reports to source artifacts
- Update reader query payloads to include artifact/span evidence where available.

## Likely Files Touched
- `src/bookforge/query/reader.py`
- `src/bookforge/query/evidence.py`
- `src/bookforge/evidence/writer.py`
- `tests/test_reader_anchor_evidence.py`

## Tests
- Canonical reader scene returns artifact evidence and hash.
- Branch-local reader scene returns branch-local artifact evidence.
- Diagnostic fallback reader output is marked not mutation-safe.
- Span creation refuses stale or hash-mismatched content.
- Citation records can be queried by receipt/answer/artifact ref.

## Definition Of Done
- Reader selections can be represented as stable evidence refs.
- Nanda can tell whether a highlighted passage is safe to use as a mutation anchor.
- Diagnostic and stale selections are not silently promoted into action targets.

---

## Source 12: `steps/0070-add-nanda-consumption-fixtures-and-contract-docs/step.md`

# 0070 Add Nanda Consumption Fixtures And Contract Docs

Status: designed  
Depends On: 0060

## Goal
Give Nanda stable fixture data and docs for response capsules, action cards, branch transitions, reader anchors, and recovery workbench integration.

## Detailed Work
- Add a fixture book or generated fixture payload with:
  - query operation
  - branch-local action operation
  - refused operation
  - recovery branch creation receipt
  - produced artifacts with statuses
  - branch-local reader anchor
  - diagnostic fallback reader anchor
  - approval-required promotion placeholder
  - issue ticket and dependency examples
- Document how Nanda should consume:
  - operation IDs
  - receipt IDs
  - artifact IDs
  - artifact span IDs
  - branch refs
  - approval refs
  - dependency/staleness refs
- Document what Nanda must not infer:
  - no canonical mutation without canonical receipt
  - no clean branch claim without cleanup/validation receipts
  - no execution claim from capability projection alone
  - no mutation target from diagnostic reader fallback

## Likely Files Touched
- `tests/fixtures/evidence/`
- `docs/help/evidence.md`
- `resources/plans/Drafts/bookforge-durable-evidence-ledger/artifacts/nanda-consumption-contract.md`
- `tests/test_evidence_nanda_fixture.py`

## Tests
- Fixture validates against evidence query contract.
- Fixture contains at least one example of each major Nanda use case.
- Fixture IDs are stable across regeneration.

## Definition Of Done
- Nanda can build test coverage against BookForge evidence without a live messy workspace.
- The fixture includes enough data to prove response capsules and action cards can cite stable evidence refs.

---

## Source 13: `steps/0080-reserve-vector-and-external-store-adapters/step.md`

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

---

## Source 14: `artifacts/current-evidence-storage-audit.md`

# Current Evidence Storage Audit

Status: Initial audit from 2026-04-27

## Current Strengths
BookForge already emits real evidence contracts. This plan should build on them, not replace them casually.

Existing surfaces include:

- `ExecutionResult` with `result_id`, `request_id`, `action`, `status`, `TimelineNodeRef`, `ScopeSelector`, issue IDs, artifact paths, produced artifacts, and details.
- `ProducedArtifactReceipt` with artifact key, label, artifact status, path, format, and consumable/resumable/replaceable flags.
- `IssueTicket` histories emitted under supervision.
- `StateSurface` histories emitted under supervision.
- `RecoveryReceipt` with recovery action, branch, node, removed paths, quarantined paths, and details.
- Branch manifests, branch current nodes, branch snapshots, and branch artifact/diff queries.
- Reader and capability projection surfaces that now expose status and available actions.

## Current File Layout
Supervision root:

```text
workspace/books/<book_id>/runtime/supervision/
  main/
    current_node.json
    state_surface_latest.json
    state_surface_history.jsonl
    issues_latest.json
    issues_history.jsonl
    execution_results.jsonl
  branches/<branch_id>/
    branch_manifest.json
    current_node.json
    state_surface_latest.json
    state_surface_history.jsonl
    issues_latest.json
    issues_history.jsonl
    execution_results.jsonl
    snapshot/
```

Recovery surfaces add branch-local recovery manifests and `recovery_receipts.jsonl` through `src/bookforge/query/recovery.py` and `src/bookforge/execution/recovery_common.py`.

Scene actions append execution results through `src/bookforge/execution/scene_actions.py`.

Projection and recovery actions also append execution results or recovery receipts through their local helper paths.

## Current Gaps
- Evidence is branch-directory and file-path indexed rather than relation indexed.
- Operation identity is uneven across action families.
- Produced artifacts have paths and statuses but no stable artifact IDs.
- Reader selections do not yet have stable span IDs with hashes and freshness.
- Recovery receipts and general execution receipts are separate surfaces.
- Nanda must still summarize and stitch receipts from payloads instead of querying a single evidence graph.
- There is no first-class approval record table.
- Dependency/staleness edges exist in diagnostic payloads but not as queryable durable relationships.
- Backfill from existing histories is not formalized.

## Planning Conclusion
The next layer should be an evidence index, not a wholesale storage rewrite. SQLite should index the already-emitted evidence, register artifact hashes and spans, and provide stable query surfaces for Nanda.

---

## Source 15: `artifacts/nanda-evidence-alignment.md`

# Nanda Evidence Alignment

Status: Initial alignment from Nanda draft plans and current implementation notes

## Nanda Inputs Reviewed
- `nanda-author-start-authoring/plan.md`
- `nanda-author-start-authoring/steps/0030-response-budget-tiers-and-response-capsules/step.md`
- `nanda-author-start-authoring/steps/0045-closing-command-set-and-post-response-runner/step.md`
- `nanda-author-start-authoring/steps/0090-capability-projection-registry-bridge/step.md`
- `nanda-author-start-authoring/artifacts/bookforge-durable-evidence-substrate-ask.md`
- `nanda-author-start-authoring/artifacts/closing-command-set-review.md`
- `nanda-author-start-authoring/steps/0080-author-creation-and-refinement-bridge/step.md`
- `nanda-author-start-authoring/validation/acceptance.md`
- `nanda-author-start-authoring/artifacts/2026-04-27-chatgpt-review-delta.md`
- `src/nanda/store/conversations.py`
- Current Nanda author route receipt/capsule handling in `src/nanda/api/routes/author.py`

## Nanda Needs
### Response Capsules
Nanda wants final author prose to receive compact facts, not full planning state. BookForge must provide stable receipt and artifact refs that can be placed inside those capsules.

### Post-Response Proposed Actions
Nanda is moving toward `AuthorDraftEnvelope` plus `ProposedActionPlan`. The runner will validate a proposed action against capability projection, legal/readiness receipts, commit gates, approval, freshness, idempotency, and expected receipt type. BookForge evidence needs stable operation and receipt IDs for those checks.

### Branch-Scope Transition
After a recovery or rerun branch is created, Nanda needs a branch transition receipt before chat can honestly claim it is working in that branch. BookForge should make the source action receipt and branch evidence easy to query.

### Action Cards
Nanda action cards need expected receipts, previous receipts, artifact availability, approval requirements, refusal reasons, and branch/canonical mutation status. BookForge capability projection gives static truth; evidence ledger gives historical proof and current artifact refs.

### Reader Anchors
Reader selections must carry provenance and freshness. The user will highlight prose and ask for change; Nanda needs to know whether the selected span is canonical, branch-local, diagnostic fallback, stale, or non-mutation-safe.

### Recovery Workbench
Nanda needs to show recovery branch creation, anchor selection, quarantine, normalization, invalidation, state rebuild, redraft, validation, and promotion as receipt-backed steps. The ledger should let the workbench show what happened and what remains without scanning files.

### Author Assets
Nanda now has a specific author creation/refinement bridge step. It expects BookForge-owned author asset operations to return structured receipts with created/refined author refs, previous refs, versions, artifact refs, hashes, profile summaries, diff summaries, warnings/refusals, and next suggested actions.

This requires workspace-level evidence because author creation can happen before a book exists. Selecting an author version for a book remains a separate book-scoped action and should record a transition receipt when implemented.

### Product State Labels
Nanda is standardizing visible states such as `answered`, `inspected`, `ready`, `blocked`, `pending_approval`, `executing`, `executed_branch_local`, `executed_canonical`, `failed`, and `paused`. BookForge evidence should provide enough receipt and operation status to support these labels without Nanda inferring them from prose.

## Nanda SQLite Pattern
Nanda already uses SQLite for conversations, turns, planning artifacts, and work artifacts. That store is useful as a pattern for local durability, WAL mode, and JSON payloads. BookForge's ledger needs stronger operation/receipt/artifact relationships and content hashes because it owns execution truth.

## Alignment Rule
Nanda can reason and present strategy. BookForge must provide mutation-safe evidence, stable IDs, and queryable relationships. The author voice may translate receipts into style, but receipts remain the proof.
