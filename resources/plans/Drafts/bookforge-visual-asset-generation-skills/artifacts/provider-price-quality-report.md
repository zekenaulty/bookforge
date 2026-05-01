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

