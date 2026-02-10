# Step Notes: Outline Enum Softening

Goal
- Allow outline generation to succeed even when Gemini invents new scene types or other enum values.

Context
- Outline generation failed because the scene `type` value "alliance" was outside the enum.
- We want to be forgiving of extra data while still steering the model toward preferred vocab.

Files
- schemas/outline.schema.json
- resources/prompt_templates/outline.md
- workspace/books/sagefall_p1_v1/prompts/templates/outline.md

Decision
- Relax enum validation for chapter_role, tempo, and scene type to accept any string.
- Keep preferred vocab in the prompt so the model aims for standard values.

Completion
- Outline schema now treats chapter_role/tempo/scene type as strings with preferred values in descriptions.
- Outline prompt now says “prefer” vocab and allows concise custom values as a fallback.

Next Actions
- Re-run outline generation to confirm validation no longer fails on custom scene types.
