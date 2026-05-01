# 0030 - Add Style And Layer Prompt Planner

Status: in_progress
Depends On: 0020

## Goal
Formalize the T1 visual planning turn that turns author/user intent into provider-ready prompt plans.

## Detailed Work
- Add a visual prompt planner that takes:
  - user intent
  - book/author context
  - selected visual purpose
  - style profile
  - reference image roles
  - provider descriptor
- Emit `VisualPromptPlan`.
- Keep provider-specific hints in the prompt plan, not scattered through command code.
- Add planner templates for:
  - scenic background
  - character reference
  - character in scene
  - transparent foreground
  - scene illustration
  - style transfer

## Likely Files Touched
- `src/bookforge/visual/prompt_planner.py`
- `src/bookforge/prompts/visual/`
- `tests/test_visual_prompt_planner.py`

## Definition Of Done
- Prompt planner emits structured plans.
- Plans distinguish user intent from provider prompt text.
- Plans include negative constraints and layer/reference requirements.

## Tests
- Unit tests with fixed provider descriptors.
- Snapshot-style tests for prompt-plan shape.

## Execution Note - 2026-04-28
- Added first deterministic `VisualPromptPlan` action via `plan_visual_asset`.
- Remaining work: replace/augment deterministic prompt packaging with the intended T1 LLM visual planning turn.
