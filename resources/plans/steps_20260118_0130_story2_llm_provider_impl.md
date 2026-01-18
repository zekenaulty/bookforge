Goal
- Implement Story 2 LLM provider layer.

Context
- Story 2 from bookforge_plan_v2.md.

Commands
- None.

Files
- src/bookforge/config/env.py
- src/bookforge/config/__init__.py
- src/bookforge/llm/client.py
- src/bookforge/llm/types.py
- src/bookforge/llm/utils.py
- src/bookforge/llm/openai_client.py
- src/bookforge/llm/gemini_client.py
- src/bookforge/llm/ollama_client.py
- src/bookforge/llm/factory.py
- src/bookforge/llm/__init__.py
- tests/test_config.py
- tests/test_llm_factory.py
- .env.example
- resources/plans/steps_20260118_0130_story2_llm_provider_impl.md

Tests
- Not run (unit tests added).

Issues
- None.

Decision
- Use stdlib HTTP client to avoid external dependencies.
- Add optional API URL and default model fields to .env.example.

Completion
- Story 2 completed.

Next Actions
- Proceed to Story 3 implementation (schema versioning and validation).
