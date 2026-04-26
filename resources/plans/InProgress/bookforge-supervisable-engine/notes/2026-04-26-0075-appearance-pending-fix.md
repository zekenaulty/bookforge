# 2026-04-26 0075 Appearance Pending Fix

## Finding
- `_apply_character_updates(...)` could mutate `appearance_current` without marking the appearance projection as pending.
- If the legacy LLM appearance refresh stalled or failed after that mutation, query surfaces could treat the changed appearance as current instead of stale.

## Change
- `src/bookforge/pipeline/state_apply.py` now sets `appearance_projection_pending: true` whenever `appearance_updates` change `appearance_current`.
- `list_appearance_projection_views(...)` already classifies that state as:
  - `appearance_status: stale`
  - `artifact_status: provisional`
  - `staleness_reason: appearance_projection_pending`

## Validation
- Added coverage in `tests/test_character_invariants_remove.py`.
- Targeted run:
  - `tests/test_character_invariants_remove.py`
  - `tests/test_appearance_query.py`
- Result: `6 passed`.

## Remaining Follow-Up
- Legacy `_load_character_states(...)` can still derive missing `appearance_current` from base state as a read-side compatibility behavior.
- That path correctly marks `appearance_projection_pending: true`, but should be revisited later if we fully separate read-only projection preparation from canonical character-state mutation.
