# Step Notes: Prompt Logging

Goal
- Log the full prompt sent to the LLM alongside the response logs.

Context
- Need system + user prompt visibility to debug outline failures and prompt drift.

Files
- src/bookforge/llm/logging.py
- src/bookforge/author.py
- src/bookforge/outline.py
- src/bookforge/phases/plan.py
- docs/help/outline_generate.md

Decision
- Store system + non-system messages in the JSON log payload.
- Emit a separate `.prompt.txt` file with role-labeled prompt content.

Completion
- Added prompt extraction/formatting helpers.
- log_llm_response now accepts messages and writes `.prompt.txt` logs.
- Existing call sites pass the messages used for the request.

Next Actions
- Re-run a command with BOOKFORGE_LOG_LLM=1 and check `.prompt.txt` output.
