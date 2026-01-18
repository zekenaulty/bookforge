# Step Notes: Story 9 Writing Loop Implementation

Goal
- Implement the run loop that plans, writes, lints, repairs, commits, and advances scenes.

Context
- Story 9 requires the end-to-end scene loop and state updates with resumable behavior.

Commands
- None.

Files
- src/bookforge/runner.py
- src/bookforge/cli.py
- src/bookforge/llm/logging.py
- src/bookforge/phases/plan.py
- docs/help/run.md
- resources/prompt_templates/write.md
- workspace/books/sagefall_p1_v1/prompts/templates/write.md

Tests
- Not run (implementation change).

Issues
- None.

Decision
- Default run executes 1 scene step if neither --steps nor --until is provided.
- Quota errors are logged via log_llm_error (when BOOKFORGE_LOG_LLM=1).
- Continuity pack is generated per step from the current state; style anchor is generated once per book.
- Write prompt includes the style anchor block for consistent voice.

Completion
- bookforge run executes plan -> write -> lint -> repair -> commit -> advance and updates state cursor.
- Scene prose and scene meta files are written with state patches and lint reports.

Next Actions
- Run tests.
