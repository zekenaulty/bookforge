# Step Notes: Request Timeout Increase

Goal
- Increase LLM request timeouts to avoid premature failures on long outputs.

Context
- Outline generation timed out during the HTTP read step.

Commands
- None.

Files
- src/bookforge/config/env.py
- src/bookforge/llm/openai_client.py
- src/bookforge/llm/gemini_client.py
- src/bookforge/llm/ollama_client.py
- src/bookforge/llm/factory.py
- docs/help/outline_generate.md
- .env.example

Tests
- Not run (config change).

Issues
- None.

Decision
- Add BOOKFORGE_REQUEST_TIMEOUT_SECONDS (default: 600) and pass it to all LLM clients.

Completion
- LLM requests use a longer timeout with env override.

Next Actions
- Re-run outline generation to confirm timeouts are resolved.
