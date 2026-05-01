# 0080 - Add Nanda Skill Projection And Fixtures

Status: in_progress
Depends On: 0060, 0070

## Goal
Expose visual asset generation to Nanda through capability projection without capability theater.

## Detailed Work
- Add visual capabilities to BookForge projection.
- Include capability metadata:
  - unit type
  - supported scope kinds
  - provider descriptor source
  - readiness source
  - mutation class
  - artifact statuses
  - approval/refusal semantics
- Add fixture data for Nanda:
  - available OpenAI background generation
  - inspectable Gemini provider descriptor
  - unavailable xAI due unknown price or missing credentials
  - refused transparent layer for unsupported model
  - planned layer composition skill

## Likely Files Touched
- `src/bookforge/query/capabilities.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/visual.py`
- `resources/plans/InProgress/bookforge-visual-asset-generation-skills/artifacts/nanda-visual-skill-fixture.json`
- `tests/test_capability_projection_visual.py`

## Definition Of Done
- Nanda can list visual skills without hardcoding them.
- Designed/planned providers are not rendered as ready actions.
- Readiness and capability remain separate.
- Refusal examples are present in fixtures.

## Tests
- Capability projection tests.
- Fixture shape tests.

## Execution Note - 2026-04-28
- Added visual provider descriptor, visual readiness, and prompt-plan capability projection entries.
- Added implemented projection entries for `plan_visual_asset`, `generate_visual_asset`, visual readiness, provider descriptors, visual asset index/detail, and visual prompt-plan detail.
- Added visual legal-action discovery through `list_execution_options(...)` for `workflow_family="visual_assets"`.
- Added queryable visual artifact surfaces so Nanda can inspect prompt plans, generated image manifests, and generated asset provenance after execution.
- Added `nanda-visual-skill-fixture.json` with expected Nanda bridge behavior, approval/spend semantics, and refusal examples.
- Removed the background-generation designed gap now that generic visual planning/generation is implemented; remaining visual gaps are reference-image workflows and layer composition.
- Remaining work: Nanda bridge/API routes and UI rendering for visual plan/generate/artifact inspection.
