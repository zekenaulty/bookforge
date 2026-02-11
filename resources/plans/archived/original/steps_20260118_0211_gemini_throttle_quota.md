Goal
- Add Gemini throttling and quota-aware error handling for free-tier limits.

Context
- User requires 15 requests/minute throttling and logging of quota details with retry delays.

Commands
- None.

Files
- src/bookforge/llm/errors.py
- src/bookforge/llm/rate_limiter.py
- src/bookforge/llm/utils.py
- src/bookforge/llm/client.py
- src/bookforge/llm/openai_client.py
- src/bookforge/llm/gemini_client.py
- src/bookforge/llm/ollama_client.py
- src/bookforge/llm/factory.py
- src/bookforge/llm/__init__.py
- src/bookforge/config/env.py
- .env.example
- .env
- resources/plans/steps_20260118_0211_gemini_throttle_quota.md

Tests
- .\.venv\Scripts\python -m pytest -q

Issues
- None.

Decision
- Add rate limiter with GEMINI_REQUESTS_PER_MINUTE (15 default in .env example).
- Parse RetryInfo and QuotaFailure details from Gemini errors and log them.
- Retry transient HTTP errors up to 3 times with backoff or server-provided retry delay.

Completion
- Throttling and quota error handling added.
