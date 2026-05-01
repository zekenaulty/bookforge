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
