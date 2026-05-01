# BookForge Visual Asset Generation Skills

Status: Draft
Stage: Drafts
Owner: BookForge engine workstream
Last Updated: 2026-04-28

## Objective
- Lift the useful parts of the old image generator into BookForge as truthful, provider-aware visual asset skills.
- Support book and author workflows that need backgrounds, character references, scene illustrations, transparent or composable layers, and visual style experiments.
- Give Nanda a machine-readable action surface for visual generation without making the author agent pretend it knows provider capabilities, pricing, or artifact safety.

## Why Now
- The data-layer work is pinned, but the authoring product needs visible value and richer creative surfaces.
- The old `cognition` and `ai.console` image work already proved a useful pattern: prompt distillation first, provider call second, asset record last.
- The old implementation was too command-shaped and provider-assumptive. The new version must be skill-shaped, receipt-backed, and explicit about provider capabilities.
- Image generation is not one capability. Background art, character references, character-in-scene rendering, style transfer, transparent foreground layers, and layer composition have different provider strengths and different failure modes.
- The author agent should be able to choose among legal visual moves the same way it chooses writing moves: inspect readiness, pick a scoped action, receive a receipt, then continue or refine.

## Grounding
- Legacy code:
  - `C:\Users\Zythis\source\repos\__draft_old\ai.console\Program.cs`
  - `C:\Users\Zythis\source\repos\__draft_old\cognition\src\Cognition.Clients\Images\OpenAIImageClient.cs`
  - `C:\Users\Zythis\source\repos\__draft_old\cognition\src\Cognition.Clients\Images\ImageService.cs`
  - `C:\Users\Zythis\source\repos\__draft_old\cognition\src\Cognition.Api\Controllers\ImagesController.cs`
  - `C:\Users\Zythis\source\repos\__draft_old\cognition\src\Cognition.Data.Relational\Modules\Images\ImageAsset.cs`
  - `C:\Users\Zythis\source\repos\__draft_old\cognition\src\Cognition.Data.Relational\Modules\Images\ImageStyle.cs`
- Current BookForge plans:
  - `resources/plans/InProgress/bookforge-action-skill-projection-for-nanda/plan.md`
  - `resources/plans/InProgress/bookforge-supervisable-engine/plan.md`
  - `resources/plans/Drafts/bookforge-durable-evidence-ledger/plan.md`
- Current provider docs reviewed:
  - OpenAI API pricing and image generation docs
  - Google Gemini image generation and pricing docs
  - xAI image generation and models/pricing docs

## Core Model
### Provider Capabilities Are Data
- Provider support must be represented as descriptors, not hardcoded assumptions.
- Each provider model descriptor should report:
  - generation support
  - edit/reference support
  - maximum reference image count, when known
  - transparency/background support
  - supported sizes/aspect ratios/resolutions
  - output formats
  - batch or variation support
  - expected price model
  - known limitations
  - verification date and source URL
- Nanda may ask "can I generate a transparent foreground layer here?" BookForge must answer from descriptors and readiness, not from persona text.

### Visual Assets Are Book Artifacts
- Generated images are not loose files.
- Each image or composition should carry:
  - asset id
  - book/author scope, if applicable
  - branch id, if applicable
  - visual purpose
  - provider/model
  - prompt package id
  - source/reference image refs
  - output file path
  - dimensions and mime type
  - content hash
  - artifact status
  - receipt id
- Initial storage can remain file-backed. The contract must be ready to move into the future evidence ledger without semantic rewrites.

### Visual Purpose Drives Prompting
- A background layer prompt is not a character prompt.
- A character reference prompt is not a scene illustration prompt.
- A transparent foreground or composited layer has stricter constraints than a mood-board image.
- BookForge should treat these as distinct skills:
  - `generate_background_layer`
  - `generate_character_reference`
  - `generate_character_in_scene`
  - `generate_transparent_foreground_layer`
  - `generate_scene_illustration`
  - `refine_visual_asset`
  - `compose_visual_layers`

### Prompt Distillation Is A First-Class Planning Turn
- The old `/image` command asked the language model to rewrite the user request into a provider-appropriate image prompt.
- Keep that pattern, but formalize it:
  - T1 visual planning produces `VisualPromptPlan`.
  - T2 provider execution uses the `VisualPromptPlan`.
  - The execution receipt records the prompt plan id and provider request.
- Distillation should include:
  - visual purpose
  - style profile
  - subject constraints
  - composition constraints
  - negative constraints
  - reference image roles
  - layer/background requirements
  - provider-specific notes

### Layered Image Workflow
- The system should support layered production without assuming every provider supports alpha transparency directly.
- Backgrounds can be generated as opaque images.
- Foreground/character layers should be generated with transparent background only when the selected provider/model supports it.
- If direct transparency is unavailable, the skill should refuse, route to a different provider, or produce a diagnostic candidate requiring external/background removal, not silently pretend the layer is clean.
- Compositions should be manifest-driven:
  - background asset
  - foreground assets
  - layer ordering
  - transform/crop/scale metadata
  - source hashes
  - composed output hash

### Style Profiles
- Styles are reusable author/book assets, not hidden prompt snippets.
- Each `VisualStyleProfile` should include:
  - name
  - description
  - prompt prefix
  - negative prompt or avoid list
  - default provider preferences
  - aspect-ratio defaults
  - known failure modes
  - example outputs, eventually
- The old `ImageStyle` table shape maps well to this, but BookForge should store style profiles in file-backed workspace assets for v1.

### Capability Projection
- Visual generation skills must appear in BookForge capability projection.
- Static capability says the engine supports a visual skill.
- Dynamic readiness says a selected scope has enough prompt/context/reference/style data to run that skill now.
- Visual skills should expose mutation class as `provisional_branch_mutation` or `diagnostic_only` unless and until canonical book-art promotion is defined.

## Provider Conclusions From Current Research
### OpenAI GPT Image
- `gpt-image-2` is the current OpenAI GPT Image model family member to plan around.
- OpenAI's Image API supports generation and edits; the Responses API supports conversational image flows and image inputs.
- The current docs explicitly say `gpt-image-2` does not support transparent backgrounds, so transparency must be capability-gated instead of assumed.
- GPT Image is the best first production adapter for instruction-following, edits, references, and predictable receipts.

### OpenAI DALL-E
- DALL-E 3 and DALL-E 2 model pages still exist with per-image pricing, but DALL-E is previous-generation/deprecated territory.
- Treat DALL-E as an optional legacy backdrop generator, not the primary production layer engine.
- DALL-E can still be valuable for painterly or scenic background ideation, especially where exact text, continuity, alpha, and reference fidelity do not matter.

### Google Nano Banana / Gemini Image
- Nano Banana now refers to Gemini native image generation models, including Gemini 2.5 Flash Image, Gemini 3.1 Flash Image Preview, and Gemini 3 Pro Image Preview.
- Gemini is especially interesting for reference-heavy workflows: Gemini 3 image models document support for up to 14 reference images, with explicit object and character reference roles.
- Gemini 2.5 Flash Image is cost-effective for fast high-volume experimentation.
- Gemini 3.1 Flash Image and Gemini 3 Pro Image add higher-resolution and stronger production potential at higher price points.

### xAI Grok / Imagine
- xAI exposes an image generation/editing API with `grok-imagine-image`, including aspect ratios, 1k/2k resolution, base64 output, style transfer, batches, and OpenAI-compatible client usage.
- The public xAI docs currently show an Imagine API section, but the visible pricing table does not publish a concrete image price in the documentation captured for this plan.
- Treat xAI as experimental until account-level pricing and quality tests are verified.

## Scope
- Draft the provider-aware visual asset skill model.
- Add contracts for visual requests, prompt plans, provider descriptors, reference image refs, layer manifests, and receipts.
- Add provider capability descriptors for OpenAI, Google Gemini, and xAI.
- Implement OpenAI first because existing legacy code already maps to it and current docs are strongest.
- Add Google/xAI descriptors before adapters so Nanda can see the intended capabilities without claiming unsupported readiness.
- Add CLI/query/action surfaces that support planning, generation, refinement, and composition.
- Add Nanda fixture output so visual skills appear as queryable/planned/actionable capabilities.

## Non-Goals
- No full image UI in BookForge.
- No full database-backed image ledger in this plan.
- No automatic canonical cover-art promotion.
- No claim that one provider can do all visual tasks.
- No silent fallback from one provider to another without recording it in a receipt.
- No use of generated images as canonical story truth unless a later plan defines that promotion path.
- No promise of perfect character consistency. The system should improve consistency through references, style profiles, and manifests, but receipts must record limitations.

## Deliverables
- `artifacts/provider-price-quality-report.md`
- `artifacts/legacy-image-system-audit.md`
- Visual asset contracts under `src/bookforge/contracts/` or successor package.
- Provider descriptor query surface under `src/bookforge/query/`.
- Visual readiness query surface.
- Visual action adapters under `src/bookforge/execution/` or a visual provider module.
- CLI commands for:
  - visual provider list
  - visual readiness
  - visual prompt plan
  - visual generate
  - visual refine
  - visual compose
- Capability projection additions for Nanda.
- Tests for descriptors, readiness, prompt planning, provider request construction, receipt emission, and refusal semantics.

## Plan-Level Definition Of Done
- A caller can ask BookForge which image providers/models are configured and what they can do.
- A caller can ask whether a specific visual action is ready for a book/author/scope.
- A generated image produces a receipt with provider/model, prompt plan, output path, dimensions, hash, artifact status, and cost estimate when possible.
- The OpenAI adapter can generate at least one file-backed image artifact in a test mode or mocked provider test.
- Visual skills appear in capability projection with accurate mutation class and readiness source.
- DALL-E, Gemini, and xAI are not advertised as ready unless credentials and adapter support exist.
- Provider pricing and capability metadata include source URLs and verification dates.
- The system refuses transparent-layer requests when the selected model does not support transparent backgrounds.

## Risks
- Provider pricing and model names change quickly; descriptors must carry verification dates.
- The author agent may overstate visual capability if Nanda renders designed skills as available.
- Reference images can become a hidden source of truth unless every input image is recorded as a ref with role and hash.
- DALL-E nostalgia can tempt us to use a legacy model for jobs that require reference fidelity or layer precision.
- Google and xAI APIs may change preview behavior before stable release.
- Generated art assets can grow workspace size quickly; this plan should keep storage paths organized from the beginning.

## Initial Implementation Bias
- Build OpenAI first.
- Represent Google/xAI as descriptors before adapters.
- Keep old Cognition lessons, but do not port the old relational schema wholesale.
- Prefer provider descriptors and receipts over ad hoc command flags.
- Start with background generation and character reference generation before full layered composition.
- Keep Nanda-facing skill descriptors honest: available, inspectable, planned, or unavailable.

