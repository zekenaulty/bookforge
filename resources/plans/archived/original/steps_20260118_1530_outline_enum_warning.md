# Step Notes: Outline Enum Warnings

Goal
- Warn when outline uses non-standard chapter roles, tempos, or scene types without rejecting output.

Context
- Gemini sometimes invents enum values (e.g., scene type "alliance"). We now accept them but want visibility.

Files
- src/bookforge/outline.py

Decision
- Keep schema permissive, but log warnings for non-standard enum values with context.

Completion
- Added preferred vocab sets and a warning pass before outline schema validation.

Next Actions
- Re-run outline generation to see warnings in output when non-standard values appear.
