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
