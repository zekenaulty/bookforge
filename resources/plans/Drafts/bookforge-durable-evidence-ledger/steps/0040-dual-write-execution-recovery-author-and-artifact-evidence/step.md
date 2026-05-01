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
