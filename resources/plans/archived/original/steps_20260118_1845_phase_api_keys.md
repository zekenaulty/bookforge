# Step Notes: Phase API Key Overrides

Goal
- Add per-phase API key overrides for planner, writer, and linter with fallback to the default provider key.

Context
- User wants to split usage across multiple API keys and track spend per phase.

Commands
- None.

Files
- src/bookforge/config/env.py
- src/bookforge/llm/client.py
- src/bookforge/llm/factory.py
- src/bookforge/llm/openai_client.py
- src/bookforge/llm/gemini_client.py
- src/bookforge/llm/ollama_client.py
- src/bookforge/runner.py
- src/bookforge/outline.py
- src/bookforge/phases/plan.py
- src/bookforge/author.py
- .env.example
- README.md

Tests
- Not run (config and wiring change).

Issues
- None.

Decision
- New env vars: PLANNER_API_KEY, WRITER_API_KEY, LINTER_API_KEY override the default provider key per phase.
- LLM logs include key_slot metadata when available.

Completion
- Planner/writer/linter use dedicated keys when configured; fallback to default key otherwise.
- Quota errors are logged with prompt context and key_slot metadata.

Next Actions
- Run tests.
