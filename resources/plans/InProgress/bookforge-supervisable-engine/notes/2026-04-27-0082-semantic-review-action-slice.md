# 2026-04-27 0082 Semantic Review Action Slice

Implemented the first diagnostic semantic recovery action:

- `review_recovery_semantics`

The action is branch-scoped and diagnostic-only. It requires the semantic recovery readiness surface to report ready, then emits `recovery_semantic_review.json` under the branch recovery artifact directory.

The emitted review artifact includes:

- `artifact_status: diagnostic`
- branch `TimelineNodeRef`
- affected and downstream review scopes
- reviewed artifact references from recovery blast radius
- findings
- blocked semantic auto-approval actions
- recommended next action
- confidence and review limitations

The action deliberately assembles evidence rather than pretending to prove story quality. Structural recovery can be healthy while semantic review reports `reviewed_attention_required`.

Validation:

- `python -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0082_semantic_action_focus`
- Result: `6 passed`
- `python -m pytest -o addopts='' tests/test_action_discovery.py tests/test_execution_actions.py tests/test_recovery_actions.py --basetemp=.pytest_tmp_0082_semantic_action_actions`
- Result: `48 passed`

Remaining `0082` work:

- Add downstream dependency review surfaces.
- Decide whether to add an LLM-backed semantic reviewer or keep this as evidence assembly consumed by Nanda.
- Add broader fixtures where downstream scopes are present and semantic findings are richer.
