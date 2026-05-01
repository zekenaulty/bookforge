# 0060 - Project Capabilities And Nanda Fixtures

Status: draft
Depends On: 0050

## Objective

Expose the split system through capability projection, legal actions, readiness, CLI, and Nanda fixtures so the author agent can operate it through conversation without theater.

## Detailed Work

- Add capability descriptors for:
  - `query.outline_fragment_graph`
  - `query.outline_timeline_split_preview`
  - `query.outline_fragment_scope_of_work`
  - `query.outline_split_branch_plan`
  - `action.create_outline_timeline_split_branches`
  - `action.validate_outline_timeline_split_branch`
  - `action.convert_split_branch_to_recovery_plan`
- Add legal-action rows for mutation steps.
- Add readiness/refusal metadata:
  - no split needed
  - single candidate auto-selectable
  - multiple candidates require user/author choice
  - selected candidate blocked
  - ambiguous artifacts require quarantine
- Add CLI help docs.
- Add Nanda fixture outputs:
  - healthy book
  - two-candidate split
  - ambiguous artifact
  - blocked candidate
  - auto-selected single valid candidate

## Files Likely Touched

- `src/bookforge/query/capabilities.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/cli.py`
- `docs/help/workflow.md`
- `docs/help/capabilities.md`
- `tests/test_capability_projection.py`
- `tests/fixtures/capability_projection_v1.json`
- `resources/plans/Drafts/bookforge-outline-timeline-split-and-branch-separation/artifacts/nanda-author-agent-handoff.md`

## Tests

- Capability projection includes all query/action surfaces.
- Real legal-action strings are covered by projection.
- Fixture projection matches live projection.
- CLI parser accepts split commands.
- Nanda fixture examples serialize cleanly.

## Definition Of Done

- Nanda can discover split capabilities from BookForge projection.
- Nanda can tell the difference between preview-only, auto-selectable, user-choice-required, and mutation-ready states.
- User-facing author responses can say what was proven and what remains uncertain.
- The author agent can call split preview and branch creation tools without needing a hardcoded Veiled Ledger fix.
