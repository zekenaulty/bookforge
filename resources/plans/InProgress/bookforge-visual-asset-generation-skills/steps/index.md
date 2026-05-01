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
