Goal
- Lock Story 9.R decisions for writing loop, state patches, and word/page targets.

Context
- User confirmed state patch schema, resume rules, stop conditions, and writer compliance checklist.
- User added requirement for word/page count thresholds with configurable words-per-page rules.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0100_story9r_writing_loop.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- State patch includes world_updates, thread_updates, canon_updates, cursor_advance, duplication_warnings_in_row_delta.
- Resume mid-chapter using existing scene files and state.json cursor.
- Stop conditions: outline complete, max steps, consecutive failure threshold.
- Writer output includes compliance checklist (scene_target_completed, end_condition_met, new_entities_count, new_threads_count).
- Word/page count targets are enforced per scene with configurable words_per_page/chars_per_page and threshold bands.

Completion
- Story 9.R accepted and locked.

Next Actions
- Proceed to Story 10.R refinement (pre-generation duplication prevention).
