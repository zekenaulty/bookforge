# 2026-04-27 0082 Semantic Readiness Slice

Implemented the first `0082` slice as query-only surfaces:

- `get_recovery_semantic_review_readiness(workspace, book_id, *, branch_id)`
- `get_recovery_semantic_review(workspace, book_id, *, branch_id)`

The readiness surface stays diagnostic-only. It requires a derived recovery branch, a recovery manifest, successful recovery receipts through `validate_recovery_branch`, and healthy structural branch state before reporting `ready`.

The read surface returns a truthful `not_started` semantic review object when no review artifact exists. This gives Nanda an honest capability boundary: structural recovery may be healthy while author-level semantic review remains unperformed.

Validation:

- `python -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0082_semantic_readiness_focus`
- Result: `6 passed`

Remaining `0082` work:

- Add diagnostic `review_recovery_semantics` execution action.
- Add downstream dependency review query/action surfaces.
- Expose semantic review action readiness through `legal_next_actions`.
- Add Nanda-visible review artifacts with findings and confidence.
