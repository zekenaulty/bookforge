Goal
- Lock Story 15.R decisions for observability and prompt hashing.

Context
- User confirmed log fields, log location, prompt hashes, and budget reporting.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0113_story15r_observability.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- JSONL log fields include step_type, timestamps, prompt_hashes, model/provider, token_estimates, budgets, status, error.
- Logs live under workspace/books/<id>/logs/run_<timestamp>.jsonl.
- Prompt hashes include stable prefix, dynamic payload, and assembled prompt.
- Budget reporting includes word/page targets and actual counts.

Completion
- Story 15.R accepted and locked.

Next Actions
- Proceed to Story 16.R refinement (tests and documentation).
