Goal
- Lock Story 11.R decisions for lint, repair, and similarity checks.

Context
- User confirmed similarity checks, lint scope, retry limits, and halt-on-failure behavior.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0107_story11r_lint_similarity.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Similarity checks: n-gram overlap + opening similarity; block commit on threshold breach.
- Lint includes continuity/invariant checks, no-recap rule, and word/page thresholds.
- Repair retries: 2 retries after initial failure (3 attempts total).
- If lint or similarity still fails, halt the run and log the failure.

Completion
- Story 11.R accepted and locked.

Next Actions
- Proceed to Story 12.R refinement (canon store and retrieval rules).
