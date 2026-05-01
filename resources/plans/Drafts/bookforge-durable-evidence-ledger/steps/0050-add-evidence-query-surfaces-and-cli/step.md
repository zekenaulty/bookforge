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
