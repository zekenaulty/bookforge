# 2026-04-28 First Implementation Slice

## Landed
- `src/bookforge/contracts/visual.py`
- `src/bookforge/query/visual.py`
- `src/bookforge/execution/visual_actions.py`
- Visual CLI commands:
  - `bookforge visual providers`
  - `bookforge visual readiness`
  - `bookforge visual plan`
  - `bookforge visual generate`
- Capability projection entries for:
  - `action.plan_visual_asset`
  - `query.visual_provider_descriptors`
  - `readiness.visual_action_readiness`
  - visual generation/composition designed gaps
- Nano Banana default route:
  - alias: `nano-banana`
  - provider/model: `google:gemini-2.5-flash-image`
- OpenAI option:
  - aliases: `image-2`, `gpt-image-2`, `openai-image-2`
  - provider/model: `openai:gpt-image-2`
- Live OpenAI generation adapter:
  - endpoint: `/v1/images/generations`
  - output: `data[0].b64_json`
  - credentials: `OPENAI_API_KEY` or `OPENAI_KEY`
  - transparent background requests still refuse for `gpt-image-2`

## Validation
- `python -m compileall -q src tests`
- `python -m pytest -q`
- Result: `338 passed`
- Focused post-OpenAI-adapter validation:
  - `.venv\Scripts\python.exe -m pytest tests/test_visual_assets.py -q`
  - Result: `11 passed`

## Remaining
- Live Google Nano Banana adapter is wired through Gemini REST.
- OpenAI edits/reference-image adapter decisions.
- Legacy DALL-E live adapter decision.
- Real T1 LLM visual prompt planner.
- Richer asset byte generation, hashes, and image receipts for reference/layer workflows.
- Nanda visual fixture refresh.
