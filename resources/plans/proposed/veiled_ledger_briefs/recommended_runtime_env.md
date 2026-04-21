# Recommended Runtime Environment For The Veiled Ledger Test Round

This is a reference snippet, not a command to override models ad hoc during a run.

## Core Runtime Policy
- Keep the configured Gemini 3.1 Pro stack authoritative.
- Do not downgrade models at runtime to chase throughput.
- Use long request timeouts and long shell command timeouts instead.
- Keep turn-aware thinking explicit:
  - T1 / planning = `high`
  - T2 / execution = `low`

## Recommended `.env` Settings

```dotenv
LLM_PROVIDER=gemini
BOOKFORGE_REQUEST_TIMEOUT_SECONDS=43200

# Keep the configured model stack authoritative.
# These should remain pointed at the intended Gemini 3.1 Pro family for the test round.
# OUTLINE_MODEL=...
# PLANNER_MODEL=...
# PREFLIGHT_MODEL=...
# WRITER_MODEL=...
# REPAIR_MODEL=...
# STATE_REPAIR_MODEL=...
# LINTER_MODEL=...
# CONTINUITY_MODEL=...
# CHARACTERS_MODEL=...

BOOKFORGE_T1_THINKING_LEVEL=high
BOOKFORGE_T2_THINKING_LEVEL=low

# Optional explicit phase overrides if you want no ambiguity:
BOOKFORGE_PLAN_T1_THINKING_LEVEL=high
BOOKFORGE_PLAN_T2_THINKING_LEVEL=low
BOOKFORGE_WRITE_T1_THINKING_LEVEL=high
BOOKFORGE_WRITE_T2_THINKING_LEVEL=low
BOOKFORGE_PREFLIGHT_T1_THINKING_LEVEL=high
BOOKFORGE_PREFLIGHT_T2_THINKING_LEVEL=low
BOOKFORGE_REPAIR_T1_THINKING_LEVEL=high
BOOKFORGE_REPAIR_T2_THINKING_LEVEL=low
BOOKFORGE_STATE_REPAIR_T1_THINKING_LEVEL=high
BOOKFORGE_STATE_REPAIR_T2_THINKING_LEVEL=low
BOOKFORGE_LINT_T1_THINKING_LEVEL=high
BOOKFORGE_LINT_T2_THINKING_LEVEL=low
```

## Command-Scope Timeout Guidance
When launching long book-generation commands from an external shell/tooling layer:
- use a command timeout on the order of 12 hours
- do not treat one-hour interruptions as normal behavior
- monitor `workspace/books/<book>/logs/runs/<run_id>.progress.json` for live phase progress during long runs

## Current Code Reality
- Writer-side phases already resolve turn-aware thinking through `resolve_turn_thinking_level(...)`.
- Default behavior is already `T1=high`, `T2=low`.
- The value of this file is making the expectation explicit for this test round.
