# 0080 - Add Nanda Skill Projection And Fixtures

Status: draft
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
- `resources/plans/Drafts/bookforge-visual-asset-generation-skills/artifacts/nanda-visual-skill-fixture.json`
- `tests/test_capability_projection_visual.py`

## Definition Of Done
- Nanda can list visual skills without hardcoding them.
- Designed/planned providers are not rendered as ready actions.
- Readiness and capability remain separate.
- Refusal examples are present in fixtures.

## Tests
- Capability projection tests.
- Fixture shape tests.

