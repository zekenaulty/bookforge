# 0060 - Add Image Generation Actions CLI And Readiness

Status: in_progress
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
  - `bookforge visual artifacts`
  - `bookforge visual asset`
  - `bookforge visual prompt-plan`
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

## Execution Note - 2026-04-28
- Added `bookforge visual providers`, `bookforge visual readiness`, and `bookforge visual plan`.
- Added `bookforge visual generate`.
- Added visual readiness query.
- Added prompt-plan execution receipt.
- Generation requires explicit `--allow-spend`.
- Added visual artifact index/detail and prompt-plan detail query commands for Nanda/UI inspection.
- Nano Banana and OpenAI `gpt-image-2` generation are adapter-ready; xAI generation readiness reports `provider_adapter_missing` until an adapter lands.
- Remaining work: refine/compose actions and xAI live adapter decision.
