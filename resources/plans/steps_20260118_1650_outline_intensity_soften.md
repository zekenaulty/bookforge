# Step Notes: Outline Intensity Softening

Goal
- Allow outline pacing intensity values outside 1-5 without failing validation.

Context
- Gemini output used intensity=6, which failed schema validation.

Files
- schemas/outline.schema.json
- src/bookforge/outline.py

Decision
- Remove min/max constraints from intensity in the schema.
- Warn when intensity is outside the preferred 1-5 range.

Completion
- intensity is now a number with a preferred range note.
- Outline warning pass logs out-of-range intensity values with chapter context.

Next Actions
- Re-run outline generation to confirm intensity >5 no longer fails.
