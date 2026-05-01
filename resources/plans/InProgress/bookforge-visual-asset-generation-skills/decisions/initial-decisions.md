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

