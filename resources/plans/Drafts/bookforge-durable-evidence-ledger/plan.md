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
