# bookforge-visual-asset-generation-skills

## Compiled Plan Metadata

- Plan Scope: `InProgress/bookforge-visual-asset-generation-skills`
- Compiled At (UTC): `2026-04-28T15:22:25Z`
- Source Document Count: `17`
- Projection File: `bookforge-visual-asset-generation-skills.md`

## Contents

1. `plan.md`
2. `decisions/initial-decisions.md`
3. `risks/initial-risks.md`
4. `validation/acceptance.md`
5. `steps/index.md`
6. `steps/0010-audit-legacy-image-system-and-current-provider-options/step.md`
7. `steps/0020-define-visual-asset-contracts-and-provider-capabilities/step.md`
8. `steps/0030-add-style-and-layer-prompt-planner/step.md`
9. `steps/0040-add-openai-image-provider-adapter/step.md`
10. `steps/0050-add-google-and-xai-provider-descriptors-and-adapters/step.md`
11. `steps/0060-add-image-generation-actions-cli-and-readiness/step.md`
12. `steps/0070-add-reference-image-layer-composition-and-refinement-workflows/step.md`
13. `steps/0080-add-nanda-skill-projection-and-fixtures/step.md`
14. `notes/2026-04-28-first-implementation-slice.md`
15. `artifacts/legacy-image-system-audit.md`
16. `artifacts/provider-price-quality-report.md`
17. `promotion.md`

---

## Source 1: `plan.md`

# BookForge Visual Asset Generation Skills

Status: In Progress
Stage: InProgress
Owner: BookForge engine workstream
Last Updated: 2026-04-28

## Current Delta (2026-04-28)
- First implementation slice landed.
- Nano Banana is the default visual model route through the `nano-banana` alias mapped to `google:gemini-2.5-flash-image`.
- OpenAI `gpt-image-2` is exposed as an explicit `image-2` / `gpt-image-2` option.
- Added typed visual contracts, provider descriptors, visual readiness, prompt-plan execution, CLI commands, and capability projection entries.
- Added guarded live Nano Banana generation through the Gemini generateContent REST API.
- Added guarded live OpenAI `gpt-image-2` generation through the OpenAI Image API.
- Added Nanda-facing visual legal-action discovery and visual artifact query surfaces.
- Added queryable visual prompt-plan/detail and generated-asset/detail surfaces so Nanda can display receipts and generated images without file archaeology.
- Full regression passed: `338 passed`.
- `visual generate` requires explicit spend approval through `--allow-spend`.

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
- Visual asset contracts under `src/bookforge/contracts/`.
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
- Nanda fixture output:
  - `artifacts/nanda-visual-skill-fixture.json`
- Tests for descriptors, readiness, prompt planning, provider request construction, receipt emission, and refusal semantics.

## Plan-Level Definition Of Done
- A caller can ask BookForge which image providers/models are configured and what they can do.
- A caller can ask whether a specific visual action is ready for a book/author/scope; generation actions truthfully refuse until adapters exist.
- A generated image produces a receipt with provider/model, prompt plan, output path, dimensions, hash, artifact status, and cost estimate when possible.
- The Nano Banana adapter can generate one file-backed image artifact from a visual prompt plan when credentials and spend approval exist; tests use a fake provider.
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

---

## Source 2: `decisions/initial-decisions.md`

# Initial Decisions

## 2026-04-28: Start As A Draft Successor Plan
- The durable data-layer plan remains pinned for later.
- Visual asset generation is valuable enough to plan now as its own successor plan.
- This work should not be added to `bookforge-supervisable-engine`; that umbrella has already delivered the supervision substrate.

## 2026-04-28: Provider Capability Descriptors First
- Provider/model capabilities must be explicit data.
- BookForge should not assume transparent backgrounds, reference support, price, or output sizes from provider name alone.

## 2026-04-28: OpenAI First, Google/xAI Descriptor-Gated
- OpenAI is the first implementation target because legacy code already exists and official docs are clear.
- Google and xAI should appear through descriptors first, then adapters when tested.

## 2026-04-28: DALL-E Is Legacy Scenic Ideation
- DALL-E may be useful for beautiful backdrops and style experiments.
- It should not be the primary layer/ref/edit/character-consistency engine.

---

## Source 3: `risks/initial-risks.md`

# Initial Risks

## Provider Drift
Model names, prices, and capabilities change quickly. Descriptors must include verification dates and source URLs.

## Transparency Assumption
The user expects transparent layers to be possible. Current OpenAI docs say `gpt-image-2` does not support transparent backgrounds. This must be a readiness/refusal condition.

## Capability Theater
Nanda may show designed visual skills as if they are wired. Capability projection must distinguish available, inspectable, planned, unavailable, and needs-bridge states.

## Workspace Size
Image assets can quickly bloat workspaces. Storage paths, hashes, and dedupe checks need to exist in the first implementation slice.

## Reference Contamination
Reference images can silently become truth. Every reference must carry role, source, scope, and hash.

## Over-Generic Image Command
A single `image generate` command would recreate the old problem. Public skills must match visual purpose and operator decision points.

---

## Source 4: `validation/acceptance.md`

# Acceptance

## Plan Acceptance
- Provider report includes current price/capability findings and source URLs.
- Legacy audit identifies what to lift and what not to port.
- Step plan separates contracts, prompt planning, provider adapters, actions/CLI, composition, and Nanda projection.

## Implementation Acceptance
- Provider descriptors can be queried without credentials.
- Readiness refuses unsupported transparent-background requests for selected models.
- OpenAI generation can produce a file-backed artifact through a mocked or live-configured provider path.
- Every generated visual artifact has a receipt with provider/model, prompt plan, hash, dimensions, output path, artifact status, and source refs.
- Capability projection reports visual skills with accurate readiness source, mutation class, expected receipt, and planned/unavailable provider status.
- Tests cover:
  - provider descriptor parsing
  - readiness/refusal
  - prompt plan output
  - provider request payload construction
  - receipt emission
  - capability projection entries

---

## Source 5: `steps/index.md`

# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-audit-legacy-image-system-and-current-provider-options | completed | - | Capture old image-system lessons and current provider price/capability evidence. |
| 0020-define-visual-asset-contracts-and-provider-capabilities | completed | 0010 | Freeze visual asset, prompt plan, provider descriptor, reference image, layer manifest, and receipt contracts. |
| 0030-add-style-and-layer-prompt-planner | in_progress | 0020 | Add T1 visual prompt planning for backgrounds, characters, scene images, transparent layers, and compositions. |
| 0040-add-openai-image-provider-adapter | in_progress | 0020, 0030 | Implement the first real provider adapter, readiness, receipts, and refusal semantics for OpenAI GPT Image/DALL-E. GPT Image generation is wired; edits/reference and legacy DALL-E live paths remain. |
| 0050-add-google-and-xai-provider-descriptors-and-adapters | in_progress | 0020, 0030 | Add Gemini/Nano Banana and xAI/Grok descriptors, then adapters only when configured and verified. Nano Banana adapter is now wired; xAI remains descriptor-only. |
| 0060-add-image-generation-actions-cli-and-readiness | in_progress | 0040 | Expose visual actions, readiness, and CLI surfaces for provider list, prompt plan, generate, refine, and compose. Prompt-plan and guarded generate are wired. |
| 0070-add-reference-image-layer-composition-and-refinement-workflows | draft | 0060 | Add reference-image workflows, layer manifests, composition outputs, and refinement actions. |
| 0080-add-nanda-skill-projection-and-fixtures | in_progress | 0060, 0070 | Publish visual skills through capability projection, legal-action discovery, artifact queries, and Nanda fixtures with theater-safe statuses. |

---

## Source 6: `steps/0010-audit-legacy-image-system-and-current-provider-options/step.md`

# 0010 - Audit Legacy Image System And Current Provider Options

Status: completed
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

## Execution Note - 2026-04-28
- Legacy and provider reports were created.
- Provider docs were captured in `artifacts/provider-price-quality-report.md`.

---

## Source 7: `steps/0020-define-visual-asset-contracts-and-provider-capabilities/step.md`

# 0020 - Define Visual Asset Contracts And Provider Capabilities

Status: completed
Depends On: 0010

## Goal
Freeze the contract vocabulary before implementation.

## Detailed Work
- Add or plan contract classes for:
  - `VisualAssetRequest`
  - `VisualPromptPlan`
  - `VisualAssetReceipt`
  - `VisualStyleProfile`
  - `ProviderCapabilityDescriptor`
  - `ReferenceImageRef`
  - `LayerIntent`
  - `LayerCompositionManifest`
- Define visual purpose enum:
  - `background_layer`
  - `character_reference`
  - `character_in_scene`
  - `transparent_foreground_layer`
  - `scene_illustration`
  - `style_transfer`
  - `composition`
- Define provider support flags and refusal codes.

## Likely Files Touched
- `src/bookforge/contracts/visual_asset.py`
- `src/bookforge/contracts/visual_provider.py`
- `src/bookforge/contracts/visual_prompt.py`
- `tests/test_visual_contracts.py`

## Definition Of Done
- Contracts are typed and serializable.
- Provider descriptors include source URL and verification date.
- Refusal codes include unsupported transparency, unsupported references, unsupported size, missing credentials, and unknown price.

## Tests
- Contract serialization tests.
- Descriptor validation tests.

## Execution Note - 2026-04-28
- Added `src/bookforge/contracts/visual.py`.
- Added `visual_assets` workflow family.
- Added provider descriptors with Nano Banana as default and `gpt-image-2` as an option.
- Validation: `python -m pytest -q` -> `332 passed`.

---

## Source 8: `steps/0030-add-style-and-layer-prompt-planner/step.md`

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

---

## Source 9: `steps/0040-add-openai-image-provider-adapter/step.md`

# 0040 - Add OpenAI Image Provider Adapter

Status: in_progress
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

## Execution Note - 2026-04-28
- Wired `gpt-image-2` text-to-image generation through the OpenAI `/v1/images/generations` endpoint.
- `gpt-image-2` now reports `adapter_ready` for non-transparent generation and still refuses transparent foreground requests.
- The live adapter is spend-guarded by the existing `visual generate --allow-spend` flow and requires `OPENAI_API_KEY` or `OPENAI_KEY`.
- Added mocked HTTP tests for request construction and `b64_json` extraction; no real provider call is made in tests.
- Remaining in this step: edits/reference-image support where applicable and any legacy DALL-E live adapter decision.

---

## Source 10: `steps/0050-add-google-and-xai-provider-descriptors-and-adapters/step.md`

# 0050 - Add Google And xAI Provider Descriptors And Adapters

Status: in_progress
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

## Execution Note - 2026-04-28
- Added Google Nano Banana and xAI Grok descriptor coverage.
- Added live Nano Banana REST adapter for `google:gemini-2.5-flash-image`.
- Remaining work: account-level xAI price verification and xAI adapter.

---

## Source 11: `steps/0060-add-image-generation-actions-cli-and-readiness/step.md`

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

---

## Source 12: `steps/0070-add-reference-image-layer-composition-and-refinement-workflows/step.md`

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

---

## Source 13: `steps/0080-add-nanda-skill-projection-and-fixtures/step.md`

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

---

## Source 14: `notes/2026-04-28-first-implementation-slice.md`

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

---

## Source 15: `artifacts/legacy-image-system-audit.md`

# Legacy Image System Audit

Verified: 2026-04-28

## What Exists In The Old Code
### `ai.console` `/image`
- Builds an image prompt from the recent conversation plus an explicit style block.
- Asks the language model to rewrite the request into a DALL-E-3-friendly image prompt.
- Chooses aspect-ratio-specific generation helpers:
  - wide / landscape
  - portrait
  - square
- Saves outputs under an agent/user image folder.

Useful lesson: keep the two-turn shape. The language model should plan the visual prompt before the image provider runs.

### `Cognition.Clients.Images.OpenAIImageClient`
- Wraps OpenAI image generation.
- Supports per-call model override.
- Uses `/v1/images/generations`.
- Requests base64 output.
- Has retry behavior for transient failures.
- Falls back from `gpt-image-1` to `dall-e-3` when organization verification blocks the GPT Image call.

Useful lesson: provider adapters need clear fallback/refusal semantics. Silent fallback should become receipt-backed fallback.

### `ImageService`
- Calls the image client.
- Computes SHA-256 for generated bytes.
- Persists provider, model, dimensions, prompt, negative prompt, guidance, seed, and hash.

Useful lesson: hash every generated image and record provider/model/prompt metadata from the start.

### `ImagesController`
- Exposes generate, get by id, list by conversation, and list by persona.
- Supports style lookup by style id or name.
- Returns generated content as image bytes.

Useful lesson: the new BookForge surface should expose both generation and query/list/read surfaces.

### Cognition Console Image UI
- `ImageLabPage` separated generation, styles, gallery, and viewer into distinct UI surfaces.
- `useImageGenerator` inserted a pending placeholder, synthesized an image prompt from recent chat, then replaced the placeholder with an image asset id after generation.
- `ImageViewer` rendered stored image content and optionally showed the prompt.

Useful lesson: Nanda should not need a giant visual cockpit immediately, but BookForge should provide enough receipts and list/read surfaces for a future visual gallery, prompt inspector, and refinement loop.

### `ImageAsset`
- Stores:
  - conversation id
  - persona id
  - provider/model
  - mime type
  - width/height
  - bytes
  - sha256
  - prompt
  - negative prompt
  - style id
  - steps/guidance/seed
  - metadata

Useful lesson: the model is close to the future evidence-ledger shape, but BookForge should start file-backed and contract-driven rather than porting the database table directly.

### `ImageStyle`
- Stores:
  - name
  - description
  - prompt prefix
  - negative prompt
  - defaults
  - active flag

Useful lesson: this maps cleanly to `VisualStyleProfile`.

## What Not To Port Directly
- Do not hardcode one provider as "the image command."
- Do not rely on one style prompt for every book or author.
- Do not let fallback choose a different model without recording that in the receipt.
- Do not store images only by conversation/persona; BookForge needs book, author, branch, and visual-purpose scope.
- Do not assume DALL-E size defaults or behavior are still current.

## Lifted Design
- `VisualPromptPlan` replaces ad hoc prompt rewriting.
- `ProviderCapabilityDescriptor` replaces hidden provider assumptions.
- `VisualAssetReceipt` replaces loose save behavior.
- `VisualStyleProfile` replaces old `ImageStyle`.
- `ReferenceImageRef` and `LayerCompositionManifest` add missing support for character refs and layered production.

---

## Source 16: `artifacts/provider-price-quality-report.md`

# Provider Price And Quality Report

Verified: 2026-04-28

## Summary
The best first production path is OpenAI GPT Image for reliable instruction following, edits, receipts, and reference workflows. Google Gemini/Nano Banana is important for cost-effective and reference-rich experiments, especially because Gemini 3 image models document up to 14 reference images. DALL-E remains useful as a legacy scenic/background ideation path, but should not be treated as the precision layer engine. xAI/Grok Imagine has a public API surface, but the official docs visible during this review did not publish a concrete public image price; treat it as experimental until account-level pricing is verified.

## Current Pricing Snapshot
| Provider / Model | Public price signal | Notes |
| --- | --- | --- |
| OpenAI `gpt-image-2` | Image input $8.00 / 1M tokens, cached image input $2.00 / 1M, image output $30.00 / 1M; text input $5.00 / 1M. Calculator examples list 1024x1024 low around $0.006, medium $0.053, high $0.211. | Current OpenAI image model to plan around. Transparent backgrounds are not supported by `gpt-image-2` per docs. |
| OpenAI `gpt-image-1.5` | Image input $8.00 / 1M, cached $2.00 / 1M, image output $32.00 / 1M, text input $5.00 / 1M, text output $10.00 / 1M. Calculator examples: 1024x1024 low $0.009, medium $0.034, high $0.133. | Good fallback candidate, but capabilities must be descriptor-gated. |
| OpenAI `gpt-image-1-mini` | Image input $2.50 / 1M, cached $0.25 / 1M, image output $8.00 / 1M, text input $2.00 / 1M. Calculator examples: 1024x1024 low $0.005, medium $0.011, high $0.036. | Best low-cost GPT Image draft lane. |
| OpenAI DALL-E 3 | Standard: $0.04 square, $0.08 non-square. HD: $0.08 square, $0.12 non-square. | Previous-generation/deprecated territory. Keep only as optional backdrop/ideation lane. |
| OpenAI DALL-E 2 | $0.016, $0.018, $0.02 by listed sizes. | Model page labels it deprecated. Do not build new production flow on it. |
| Google Gemini 2.5 Flash Image / Nano Banana | Standard output $0.039 per image up to 1024x1024; batch/flex $0.0195. Input $0.30 / 1M text/image standard. | Strong low-cost ideation and high-volume lane. |
| Google Gemini 3.1 Flash Image Preview / Nano Banana 2 | Standard output examples: $0.045 at 0.5K, $0.067 at 1K, $0.101 at 2K, $0.151 at 4K. Batch examples are lower. | Interesting for interactive high-throughput reference-heavy work. Preview behavior may change. |
| Google Gemini 3 Pro Image Preview / Nano Banana Pro | Standard output examples: $0.134 per 1K/2K image, $0.24 per 4K image. Batch/flex roughly half in the cited table. | Higher-cost production lane; docs position it for professional asset production and high fidelity. |
| xAI `grok-imagine-image` | Official docs reviewed show Imagine API but visible model/pricing page displayed `Image- / image` without a concrete public number. | API exists; price should be verified from account console or billing docs before cost routing. |

## Capability Notes
### OpenAI
- The OpenAI Image API supports generation and edits, and edits can use one or more input images as references.
- The Responses API supports conversational, iterative image experiences with image inputs and outputs.
- `gpt-image-2` supports broad size control, including 2K and 4K-style dimensions within documented constraints.
- `gpt-image-2` does not currently support transparent backgrounds. The visual skill layer must not assume transparency.
- Official docs still call out limitations: text rendering, consistency across recurring characters, and precise composition can fail.

### Google Gemini / Nano Banana
- Google docs define Nano Banana as Gemini native image generation, with Nano Banana, Nano Banana 2, and Nano Banana Pro corresponding to Gemini image models.
- Gemini 3 image models document up to 14 reference images, including separate object and character reference categories.
- Gemini 3.1 Flash Image includes Google Search grounding for images, which may be useful for non-person reference context, but it adds cost and source-control considerations.

### xAI / Grok Imagine
- xAI docs show `grok-imagine-image` through xAI SDK and OpenAI-compatible client usage.
- The API supports image generation, image edits/style transfer from an image URL, multiple images per request, aspect ratios, 1k/2k resolution, and base64 output.
- Because official price was not visible in the docs reviewed, BookForge should classify xAI cost metadata as `unknown_verified_price=false` until manually verified.

## Quality / Cost Routing Recommendation
| Task | Recommended first route | Reason |
| --- | --- | --- |
| Painterly background / scenic plate | DALL-E 3 optional legacy, Gemini 2.5 Flash Image, or GPT Image medium | DALL-E can still produce beautiful mood/scenery; Gemini is cheaper for iteration; GPT Image is safer for receipts and editing. |
| Production scene illustration | GPT Image 2 or Gemini 3 Pro Image | Higher instruction following and higher-res options. |
| Character reference sheet | GPT Image 2 edits/references or Gemini 3 image models | Requires reference handling and consistency controls. |
| Character in a new scene | GPT Image 2 or Gemini 3 image models | Needs both character and scene refs; descriptor should enforce reference roles. |
| Transparent foreground layer | Capability-gated provider only; not GPT Image 2 today | Docs say `gpt-image-2` does not support transparent backgrounds. |
| Cheap concept batches | Gemini 2.5 Flash Image, GPT Image 1 Mini, or xAI after pricing verification | Cheap lanes should be explicitly marked draft/provisional. |
| Style transfer experiments | xAI/Grok or GPT Image edits | xAI docs emphasize style transfer; GPT Image edits are better integrated into OpenAI path. |

## Prompting Strategy Differences
### DALL-E
- Use it for mood, composition, color, scenery, and illustrative backdrops.
- Keep prompts descriptive and aesthetic.
- Avoid asking for precise text, exact character continuity, transparent layers, or multi-reference fidelity.
- Output should default to `diagnostic` or `provisional` until selected.

### GPT Image
- Use explicit constraints and reference roles.
- Separate subject identity, pose, composition, style, lighting, background, and exclusions.
- Record reference image ids and roles.
- For edits, specify exactly what must remain unchanged.
- Do not promise perfect consistency; use receipts and visual review.

### Gemini / Nano Banana
- Use concise iterative instructions and explicit image reference roles.
- Exploit reference count for character/object/scene context.
- Use Gemini 2.5 Flash Image for cheap iteration and Gemini 3 Pro Image for higher-fidelity candidates.
- Treat preview models as capability descriptors with verification dates.

### xAI / Grok
- Treat as experimental until pricing and output behavior are measured locally.
- Good candidate for style transfer and quick variations.
- Prefer test batches and diagnostic artifacts before production use.

## Sources
- OpenAI pricing: https://developers.openai.com/api/docs/pricing
- OpenAI image generation docs: https://developers.openai.com/api/docs/guides/image-generation
- OpenAI DALL-E 3 model page: https://developers.openai.com/api/docs/models/dall-e-3
- OpenAI DALL-E 2 model page: https://developers.openai.com/api/docs/models/dall-e-2
- Google Gemini image generation docs: https://ai.google.dev/gemini-api/docs/image-generation
- Google Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- xAI image generation docs: https://docs.x.ai/developers/model-capabilities/images/generation
- xAI models/pricing docs: https://docs.x.ai/developers/models

---

## Source 17: `promotion.md`

# Promotion

Promoted: 2026-04-28

## Source
- `resources/plans/Drafts/bookforge-visual-asset-generation-skills`

## Reason
- User approved implementation with Nano Banana as default and OpenAI `gpt-image-2` as an explicit option.

## Baseline Change
- Draft plan copied to `resources/plans/InProgress/bookforge-visual-asset-generation-skills`.
- InProgress plan updated with first implementation slice and validation evidence.
