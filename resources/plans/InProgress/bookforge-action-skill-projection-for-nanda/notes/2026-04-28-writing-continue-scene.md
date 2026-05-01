# 2026-04-28 Writing Continue Scene Surface

`continue_scene` was added as the first adaptive writing macro for Nanda.

Key behavior:
- It is projected as `action.continue_scene`.
- It is a macro capability, but it executes exactly one child action per call.
- It reads `ScenePhaseReadiness.recommended_next_action`.
- It runs only that recommended scene-phase action.
- It returns a wrapper `ExecutionResult` with child action/status/result id plus before/after readiness context.
- It can target `main` or a derived branch, using the same execution root as the child action.

Design intent:
- This gives Nanda a "continue this scene one step" skill without turning scene writing back into a hidden batch rail.
- The author agent can still inspect legal actions and choose a different primitive when needed.
- The receipt makes the actual child action visible, so author voice can explain what really happened instead of claiming generic progress.

Validation:
- Focused tests cover legal-action exposure, capability projection, and wrapper receipt emission.
