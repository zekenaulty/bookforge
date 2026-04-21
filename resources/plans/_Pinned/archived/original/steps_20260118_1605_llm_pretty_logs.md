# Step Notes: Pretty LLM Text Logs

Goal
- Write a human-readable text file alongside each LLM response log for quick inspection.

Context
- Raw LLM logs are JSON and hard to scan for output shape during debugging.

Files
- src/bookforge/llm/logging.py

Decision
- Add a pretty text log that extracts the response text and pretty-prints JSON when possible.
- Keep the original JSON log as the canonical record.

Completion
- Added pretty text log writer that emits `<label>_<timestamp>.txt` next to the JSON log.
- Attempts JSON pretty-print; falls back to raw text when parsing fails.

Next Actions
- Re-run a generation step and open the .txt log for quick inspection.
