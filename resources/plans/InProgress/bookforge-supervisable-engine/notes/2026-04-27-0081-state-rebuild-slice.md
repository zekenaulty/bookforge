# 2026-04-27 0081 State Rebuild Slice

## Implemented
- Added `get_state_rebuild_preview(workspace, book_id, *, branch_id)`.
  - Reports branch-local state/projection candidates that `rebuild_state_scope` will quarantine.
  - Includes affected scopes, downstream scopes, affected chapters, affected scene ids, rebuild mode, candidate paths, and rebuilt output paths.
- Added `rebuild_state_scope`.
  - Derived recovery branch only.
  - Quarantines branch-local state/projection artifacts.
  - Records promotion removals so invalid main artifacts are removed during promotion.
  - Rewrites branch `state.json` to a clean outline-derived baseline.
  - Rebuilds branch character index/state files from normalized outline characters.
  - Reinitializes durable context files and resets bible/last excerpt.
- Added `rebuild_state_scope` to:
  - execution exports
  - action discovery/legal-action ordering
  - CLI workflow commands
  - recovery health gating
  - recovery validation requirements
- Hardened quarantine moves with a hashed fallback destination for long Windows paths while preserving source paths in receipts.

## Current Behavior
- The current state rebuild is intentionally conservative:
  - it performs a full branch-local context reset rather than a partial state rollback.
  - this is truthful because current state artifacts are not event-sourced enough to safely subtract only selected scenes or sections.
- `validate_recovery_branch` now refuses until the branch has receipts for:
  - `quarantine_artifacts`
  - `normalize_outline_scope`
  - `invalidate_scope_outputs`
  - `rebuild_state_scope`

## Validation
- Focused suite passed:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_state_focus`
  - Result: `35 passed`
- Full suite passed:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_state_full`
  - Result: `308 passed`

## Follow-Up
- Add `redraft_scope` as the next mutation primitive.
- Add richer state/projection validation after redraft, especially for downstream continuity and series memory.
- Eventually replace full context reset with event-sourced state rollback once state families carry reliable provenance.
