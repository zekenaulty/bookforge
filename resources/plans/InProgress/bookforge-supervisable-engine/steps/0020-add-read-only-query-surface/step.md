# 0020 Add Read-Only Query Surface

Status: draft

## Goal
- Expose stable, small, testable read APIs over current BookForge workflow state, lineage anchors, integrity evidence, and current execution coordinates.

## Problem
- Current diagnostics require direct file inspection across many workspace artifacts.
- That forces Nanda to scrape raw files and makes BookForge runtime truth harder to reuse inside its own tests and command paths.

## Detailed Work
- Add `src/bookforge/query/workspace.py` for:
  - active book/cursor
  - current main-branch node
  - branch manifests or branch-local current-node pointers
  - section status
  - active section
  - current pause marker or progress heartbeat
  - active fork groups
- Add `src/bookforge/query/workflow.py` for:
  - workflow family
  - run mode
  - branch id
  - fork-group status
  - last explicit workflow action
  - source artifact class
- Add `src/bookforge/query/lineage.py` for:
  - immutable source run lookup
  - frozen chapter projection lookup
  - section draft lineage
  - materialization source classification
  - `ScopeSelector -> TimelineNodeRef` resolution
  - parent-node and fork-group ancestry lookup
- Ensure `ScopeSelector` resolution supports explicit branch and fork-group addressing instead of assuming `main`.
- Add `src/bookforge/query/integrity.py` for:
  - outline vs prose vs state disagreement summaries
  - mutable-source usage detection
  - chimera-risk indicators
  - branch contamination warnings
- Add `src/bookforge/query/characters.py` and `src/bookforge/query/continuity.py` for read access to current supporting state.
- Keep all query modules read-only and typed.
- Split helpers and translators instead of creating a single kitchen-sink query module.

## Files Likely Touched
- `src/bookforge/query/__init__.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/characters.py`
- `src/bookforge/query/continuity.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/memory/continuity.py`
- `src/bookforge/characters.py`

## Tests
- `python -m pytest tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_section_workflow.py tests/test_workspace_init.py`
- Add fixture coverage that exercises both healthy and mixed-lineage workspaces
- Add fixture coverage for main-branch and derived-branch lookup paths if branch state exists in the fixture set

## Definition Of Done
- A caller can ask BookForge for workflow family, source run, active section, current node, and integrity verdict without hand-reading JSON files.
- A caller can resolve a `ScopeSelector` to the current `TimelineNodeRef` for the selected book, branch, or fork-group scope.
- Query modules return structured Python objects, not raw strings.
- Query modules do not mutate workspace files.
- The `veiled_ledger_b1` chimera class can be surfaced through query helpers rather than ad hoc scripts.

## Notes
- This is the step that lets Nanda stop depending on raw workspace scraping as its only observation seam.
