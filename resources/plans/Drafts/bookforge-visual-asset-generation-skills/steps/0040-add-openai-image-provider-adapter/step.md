# 0040 - Add OpenAI Image Provider Adapter

Status: draft
Depends On: 0020, 0030

## Goal
Implement the first real provider path using OpenAI GPT Image and optional legacy DALL-E descriptor support.

## Detailed Work
- Add OpenAI provider adapter for generation and edits where supported.
- Support provider descriptors for:
  - `gpt-image-2`
  - `gpt-image-1.5`
  - `gpt-image-1-mini`
  - `dall-e-3`
  - `dall-e-2`
- Ensure `gpt-image-2` transparent-background requests refuse or route explicitly because docs say it does not support transparent backgrounds.
- Record:
  - request payload
  - provider/model
  - output bytes/path
  - hash
  - dimensions
  - prompt plan id
  - fallback/refusal reason

## Likely Files Touched
- `src/bookforge/visual/providers/openai.py`
- `src/bookforge/query/visual_providers.py`
- `tests/test_visual_openai_provider.py`

## Definition Of Done
- OpenAI descriptor query works without credentials.
- Adapter builds valid request payloads under tests.
- Mocked generation writes a visual artifact and receipt.
- Unsupported transparency is refused for `gpt-image-2`.

## Tests
- Provider descriptor tests.
- Mocked HTTP/request construction tests.
- Receipt emission tests.
- Refusal tests.

