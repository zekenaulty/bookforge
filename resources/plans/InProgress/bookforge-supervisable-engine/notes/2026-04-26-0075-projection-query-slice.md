# 2026-04-26 0075 Projection Query Slice

## Completed
- Added `bookforge.query.appearance` with branch-aware appearance projection views.
- Added `bookforge.query.setting` with scene setting projection lookup.
- Added `bookforge.query.thought_context` with prior T1 thought-signature context discovery.
- Exported all three query surfaces from `bookforge.query`.
- Added `refresh_character_appearance_projection` as a non-mutating execution action.
- Added action discovery for `refresh_character_appearance_projection`.

## Contract Notes
- Existing character `appearance_current` is not silently treated as authoritative.
- Appearance query defaults to `derived` for readable state, `provisional` when projection is pending, and `diagnostic` when missing.
- Scene setting distinguishes `author_drafted` (`provisional`), `prose_extracted` (`derived`), `outline_derived` (`derived`), and `missing` (`diagnostic`).
- Thought signatures are exposed as `diagnostic` planning-reuse context only; execution receipts remain the source of truth for what happened.
- The appearance projection action writes `draft/context/appearance/ch_###/scene_###/appearance_projection.json` and records a `ProducedArtifactReceipt`.

## Validation
- `tests/test_appearance_query.py`
- `tests/test_scene_setting_query.py`
- `tests/test_thought_context_query.py`
- `tests/test_appearance_projection_action.py`
- Focused result: 11 passed.

## Remaining 0075 Work
- Add setting/background extraction and author-drafted setting actions.
- Record appearance, setting, and thought-context artifact usage in downstream scene-phase prompt receipts.
- Consider a compact aggregate scene-context readiness/query surface once the individual projections settle.
