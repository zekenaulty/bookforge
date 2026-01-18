Goal
- Lock Story 2.R decisions for the LLM provider abstraction.

Context
- User approved provider set, env keys, per-phase models, retry/backoff, and JSON handling.
- Note future requirement for per-task provider/model overrides.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_${ts}_story2r_llm_provider.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Providers: openai, gemini, ollama.
- Env keys: LLM_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY, OLLAMA_URL, PLANNER_MODEL, WRITER_MODEL, LINTER_MODEL.
- Model selection uses per-phase models with a default fallback.
- Retry/backoff: 3 retries with exponential backoff starting at 1s.
- Planning/lint outputs require strict JSON-only responses.
- Reserve config fields for per-task provider/model overrides (future).

Completion
- Story 2.R accepted and locked.

Next Actions
- Proceed to Story 3.R refinement (schema governance and validation).
