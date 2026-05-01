# 0050 - Add Google And xAI Provider Descriptors And Adapters

Status: draft
Depends On: 0020, 0030

## Goal
Represent Gemini/Nano Banana and xAI/Grok as truthful provider capabilities, then add adapters only when configuration and tests exist.

## Detailed Work
- Add provider descriptors for:
  - `gemini-2.5-flash-image`
  - `gemini-3.1-flash-image-preview`
  - `gemini-3-pro-image-preview`
  - `grok-imagine-image`
- Mark preview models and unknown-price models explicitly.
- Add Google adapter after descriptor tests.
- Add xAI adapter after account-level pricing and API behavior are verified.
- Preserve OpenAI-compatible client usage for xAI only as an adapter implementation detail.

## Likely Files Touched
- `src/bookforge/visual/providers/google.py`
- `src/bookforge/visual/providers/xai.py`
- `tests/test_visual_google_provider.py`
- `tests/test_visual_xai_provider.py`

## Definition Of Done
- Google/xAI descriptors are visible in provider query.
- Unknown xAI pricing does not allow cost-based auto-routing.
- Gemini reference-image limits are represented in descriptors.
- Adapters are not marked ready unless credentials/config exist.

## Tests
- Descriptor tests for preview, reference count, sizes, and price metadata.
- Readiness tests for missing credentials.

