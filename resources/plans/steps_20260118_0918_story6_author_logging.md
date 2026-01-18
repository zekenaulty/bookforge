# Step Notes: Author Logging and Token Caps

Goal
- Capture raw LLM responses for author generation and standardize logging helpers.
- Increase the default author max tokens to avoid truncation errors.

Context
- Gemini returned valid JSON but hit MAX_TOKENS, truncating output and breaking parsing.
- We want consistent logging for LLM steps to debug failures quickly.

Commands
- None.

Files
- src/bookforge/llm/logging.py
- src/bookforge/llm/__init__.py
- src/bookforge/author.py
- docs/help/author_generate.md

Tests
- None.

Issues
- MAX_TOKENS truncated JSON responses from Gemini.

Decision
- Centralize LLM response logging in bookforge.llm.logging.
- Default BOOKFORGE_AUTHOR_MAX_TOKENS to 6096 with env override.

Completion
- Author generation logs raw responses on failure or when BOOKFORGE_LOG_LLM=1.
- Default author token cap raised and help docs updated.

Next Actions
- Use the shared logging helper in all future LLM steps.
- Consider adding a CLI flag for per-command max tokens later.
