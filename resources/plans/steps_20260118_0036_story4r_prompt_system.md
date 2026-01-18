Goal
- Lock Story 4.R decisions for prompt system and caching rules.

Context
- User confirmed stable prefix contents, registry name, deterministic JSON formatting, and hashing requirements.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0036_story4r_prompt_system.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Stable prefix includes base rules, book constitution, author fragment, output contract.
- Prompt registry file is prompts/registry.json.
- Deterministic JSON serialization uses sorted keys and 2-space indent; no timestamps in stable prefix.
- Hash stable prefix, dynamic payload, and final assembled prompt.

Completion
- Story 4.R accepted and locked.

Next Actions
- Proceed to Story 5.R refinement (prompt budgeter and continuity pack).
