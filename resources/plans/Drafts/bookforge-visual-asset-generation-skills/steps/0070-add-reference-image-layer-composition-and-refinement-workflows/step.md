# 0070 - Add Reference Image Layer Composition And Refinement Workflows

Status: draft
Depends On: 0060

## Goal
Support the actual creative workflow: references, layers, refinements, and composed outputs.

## Detailed Work
- Add `ReferenceImageRef` query and validation.
- Add `generate_character_in_scene`.
- Add `generate_transparent_foreground_layer` with strict provider capability checks.
- Add `compose_visual_layers` using a composition manifest.
- Add `refine_visual_asset` paths for prompt-only and reference-assisted refinements.
- Keep original assets immutable; refinements produce new derived/provisional assets.

## Likely Files Touched
- `src/bookforge/visual/references.py`
- `src/bookforge/visual/composition.py`
- `src/bookforge/execution/visual_actions.py`
- `tests/test_visual_references.py`
- `tests/test_visual_composition.py`

## Definition Of Done
- Reference image roles and hashes are recorded.
- Layer composition creates a manifest and output artifact.
- Unsupported transparency refuses.
- Refinement creates a new asset, not an in-place mutation.

## Tests
- Reference validation tests.
- Composition manifest tests.
- Refinement receipt tests.
- Transparent-layer refusal tests.

