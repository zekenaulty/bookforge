# 2026-04-26 0075 Setting Projection Actions

## Completed
- Added `draft_scene_setting_projection`.
- Added `extract_scene_setting_from_prose`.
- Added `get_scene_context_projection`.
- Exported both request builders and execution actions from `bookforge.execution`.
- Added both actions to legal-action discovery for scene scope.
- Added setting action tests.

## Contract Notes
- `draft_scene_setting_projection` writes `author_drafted.setting.json` with artifact status `provisional`.
- `extract_scene_setting_from_prose` writes `prose_extracted.setting.json` with artifact status `derived`.
- Both actions are non-canonical and non-mutating.
- `extract_scene_setting_from_prose` refuses when no scene prose exists.
- The current implementation records structured setting supplied by the caller/author worker; it does not perform an internal LLM extraction turn yet.
- If no structured extraction is supplied, the prose-extraction action keeps a source excerpt and reports conservative structured availability.
- `get_scene_context_projection` aggregates appearance, setting, and T1 thought-context availability without creating a second truth model.

## Validation
- `tests/test_scene_setting_actions.py`
- `tests/test_scene_setting_query.py`
- `tests/test_scene_context_query.py`
- `tests/test_action_discovery.py`
- Focused result: 34 passed for action discovery plus setting actions.

## Remaining 0075 Work
- Record appearance, setting, and thought-context artifact usage in downstream prompt/execution receipts.
- Decide whether to add an internal author-LLM setting draft turn or leave Nanda as the author-worker caller that supplies the structured setting payload.
- Consider an aggregate scene-context readiness surface after projection usage receipts land.
