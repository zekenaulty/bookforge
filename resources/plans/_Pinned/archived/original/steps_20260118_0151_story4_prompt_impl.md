Goal
- Implement Story 4 prompt templates, registry, deterministic serialization, and hashing.

Context
- Story 4 from bookforge_plan_v2.md.

Commands
- None.

Files
- src/bookforge/prompt/registry.py
- src/bookforge/prompt/renderer.py
- src/bookforge/prompt/serialization.py
- src/bookforge/prompt/hashing.py
- src/bookforge/prompt/system.py
- src/bookforge/prompt/__init__.py
- resources/prompt_templates/plan.md
- resources/prompt_templates/write.md
- resources/prompt_templates/lint.md
- resources/prompt_templates/repair.md
- resources/prompt_templates/system_base.md
- resources/prompt_templates/output_contract.md
- resources/prompt_registry.json
- tests/test_prompt_render.py
- tests/test_prompt_hashing.py
- tests/test_prompt_registry.py
- resources/plans/steps_20260118_0151_story4_prompt_impl.md

Tests
- Not run (tests added).

Issues
- None.

Decision
- Use deterministic JSON serialization with sorted keys and 2-space indent.
- Hash stable prefix, dynamic payload, and assembled prompt with SHA-256.

Completion
- Story 4 completed.

Next Actions
- Proceed to Story 5 implementation (budgeter and continuity pack).
