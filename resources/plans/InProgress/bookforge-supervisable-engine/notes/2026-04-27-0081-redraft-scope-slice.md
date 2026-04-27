# 2026-04-27 0081 Redraft Scope Slice

## Implemented
- Added `redraft_scope`.
  - Derived recovery branch only.
  - Reads affected scopes from the recovery manifest.
  - Prepares normalized affected sections as branch-local frozen sections with scene ranges from the normalized outline.
  - Delegates writing to the existing scoped section writer instead of creating a second prose pipeline.
  - Emits a recovery receipt with redrafted scopes and child write result ids.
- Added `redraft_scope` to:
  - execution exports
  - legal-action ordering
  - CLI workflow commands
  - recovery health gating
  - recovery validation requirements
- Validation now requires `redraft_scope` after `rebuild_state_scope`.

## Current Behavior
- `redraft_scope` may call the LLM-backed section writer in real workspaces.
- Tests mock the writer boundary and verify orchestration without model calls.
- The action does not yet support explicit salvage-reference injection.

## Validation
- Focused suite passed:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_redraft_focus`
  - Result: `35 passed`
- Full suite passed:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_redraft_full`
  - Result: `308 passed`

## Follow-Up
- Add explicit salvage-reference injection for redraft.
- Add richer postcondition receipts with next legal actions and integrity deltas.
- Add downstream/story-weaving validation after redraft.
