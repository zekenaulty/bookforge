# 0010 - Audit Legacy Image System And Current Provider Options

Status: draft
Depends On: none

## Goal
Capture what should be lifted from the old image system and ground provider choices in current docs and pricing.

## Detailed Work
- Inspect old `ai.console` and `cognition` image code.
- Document useful legacy concepts:
  - prompt rewriting
  - style profiles
  - provider adapter
  - image asset hash and metadata
  - query/read surfaces
- Document what should not be ported directly.
- Verify current provider pricing and capability docs for:
  - OpenAI GPT Image
  - OpenAI DALL-E
  - Google Gemini / Nano Banana
  - xAI Grok / Imagine

## Files Touched
- `resources/plans/Drafts/bookforge-visual-asset-generation-skills/artifacts/legacy-image-system-audit.md`
- `resources/plans/Drafts/bookforge-visual-asset-generation-skills/artifacts/provider-price-quality-report.md`

## Definition Of Done
- Legacy audit exists.
- Provider report exists with sources and verification date.
- Plan identifies the first recommended implementation route.

## Tests
- Planning step only. No runtime tests.

