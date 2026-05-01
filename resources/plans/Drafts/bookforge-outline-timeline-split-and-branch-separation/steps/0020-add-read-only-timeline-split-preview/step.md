# 0020 - Add Read-Only Timeline Split Preview

Status: draft
Depends On: 0010

## Objective

Add the first read-only graph query that turns scattered outline artifacts into timeline candidates and scope-of-work previews.

No mutation happens in this step.

## Detailed Work

- Add `bookforge.query.outline_timeline_split`.
- Implement:
  - `get_outline_fragment_graph(workspace, book_id)`
  - `get_outline_timeline_split_preview(workspace, book_id)`
  - `get_outline_fragment_scope_of_work(workspace, book_id, candidate_id=None)`
- Reuse existing lineage extraction where possible:
  - section matrix rows
  - stale artifact inventory
  - outline repair candidates
  - normalized section hashes
  - scene list hashes
- Generate candidate timelines from:
  - source run lineage
  - frozen projection lineage
  - section draft lineage
  - mutable compatibility view lineage
- Emit candidate-level summaries:
  - affected scopes
  - likely source run
  - included fragments
  - conflicting fragments
  - missing fragments
  - scope of work
  - confidence
  - recommended action

## Files Likely Touched

- `src/bookforge/query/outline_timeline_split.py`
- `src/bookforge/query/__init__.py`
- `src/bookforge/cli.py`
- `tests/test_outline_timeline_split_query.py`

## Tests

- Healthy single-lineage book returns `single_healthy_timeline`.
- Two-outline fixture returns at least two candidates.
- Candidate scopes cover all conflicting sections.
- Preview is deterministic across repeated runs.
- No files are written.

## Definition Of Done

- Nanda can ask "what timelines exist here?" without raw file archaeology.
- The query clearly distinguishes no-op healthy state from split-worthy contamination.
- Each candidate includes a concrete `OutlineFragmentScopeOfWork`.
- Ambiguous artifacts remain visible and unassigned.
