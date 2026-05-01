# 0050 - Add Validation And Recovery Handoff

Status: draft
Depends On: 0040

## Objective

Validate split branches and hand them into the existing recovery/redraft pipeline.

Timeline split is isolation. Recovery remains the process that turns an isolated candidate into a promotable book state.

## Detailed Work

- Add `validate_outline_timeline_split_branch(...)`.
- Validate:
  - no mixed source runs in active outline
  - no section draft artifacts active outside selected candidate
  - snapshot registry agrees with outline
  - character ids in state/projections exist in selected outline
  - projection `node`/`selector` branch ids match split branch
  - ambiguous/conflict artifacts remain in quarantine/salvage
- Add `convert_split_branch_to_recovery_plan(...)`.
- Map split scope-of-work into existing recovery scope:
  - affected scopes
  - downstream scopes
  - artifacts to quarantine
  - outputs to invalidate
  - state/projections to rebuild
  - scopes to redraft
- Keep semantic review separate from structural validation.

## Files Likely Touched

- `src/bookforge/execution/outline_timeline_split.py`
- `src/bookforge/query/recovery.py`
- `src/bookforge/execution/recovery_common.py`
- `tests/test_outline_timeline_split_validation.py`
- `tests/test_recovery_actions.py`

## Tests

- Valid split branch passes structural validation.
- Branch with ghost character state fails validation.
- Branch with active ambiguous artifact fails validation.
- Recovery plan preview can be produced from split branch manifest.
- Existing recovery primitives can consume the handoff scope.

## Definition Of Done

- Split branch validation tells Nanda whether the branch is structurally usable.
- Split branch handoff can drive the existing recovery sequence.
- The branch can reach `needs_redraft` or `promotion_ready` only through receipts.
- Semantic/prose quality remains a separate author-review gate.
