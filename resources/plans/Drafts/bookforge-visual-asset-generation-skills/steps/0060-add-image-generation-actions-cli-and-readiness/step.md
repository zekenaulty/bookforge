# 0060 - Add Image Generation Actions CLI And Readiness

Status: draft
Depends On: 0040

## Goal
Expose visual generation as BookForge actions and CLI commands.

## Detailed Work
- Add readiness query for visual actions.
- Add execution actions:
  - `plan_visual_asset`
  - `generate_background_layer`
  - `generate_character_reference`
  - `generate_scene_illustration`
  - `refine_visual_asset`
- Add CLI commands:
  - `bookforge visual providers`
  - `bookforge visual readiness`
  - `bookforge visual plan`
  - `bookforge visual generate`
  - `bookforge visual refine`
- Emit receipts and organized output folders.

## Likely Files Touched
- `src/bookforge/query/visual_readiness.py`
- `src/bookforge/execution/visual_actions.py`
- `src/bookforge/cli.py`
- `tests/test_visual_actions.py`
- `tests/test_cli_visual.py`

## Definition Of Done
- Visual actions can be discovered and readiness-checked.
- CLI can produce JSON readiness and descriptor output.
- Mocked generation produces a file-backed receipt.
- Receipts include artifact status.

## Tests
- Readiness tests.
- CLI JSON tests.
- Mocked action execution tests.

