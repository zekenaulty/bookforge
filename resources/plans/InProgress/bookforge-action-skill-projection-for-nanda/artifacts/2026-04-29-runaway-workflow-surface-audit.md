# Runaway Workflow Surface Audit

Date: 2026-04-29

## Purpose

Audit BookForge command/capability surfaces for accidental broad execution, especially cases where Nanda or an author agent asks for a narrow operation such as:

- draft a thin starter outline
- outline or continue one scene
- write only prose
- inspect the next legal action

The safety invariant is: a small-scope action must not silently trigger a full outline pipeline, full section write, lint/repair chain, commit, or book-level workflow unless the action is explicitly a macro and the caller has approved that macro boundary.

## Findings

### Starter Outline

`draft_starter_outline_from_intent` is provider-backed and intentionally non-deterministic. It calls the outline provider once and writes immutable thin-outline run artifacts:

- `outline_spine_v1.json`
- `outline_sections_v1.json`
- `outline_final_v1_1.json`
- `outline_pipeline_report.json`
- `pipeline_latest.json`

It does not initialize workflow state, freeze a section, create a branch, or write prose.

Tightening applied:

- Capability descriptor now declares `provider_call_count_per_request=1`.
- Capability descriptor now declares that it does not initialize workflow, freeze a section, create a branch, or write prose.
- Execution result now reports `next_recommended_action="initialize_section_workflow"` and keeps the later chain under `follow_on_sequence`.
- `follow_on_sequence_policy` says callers must re-query legal actions/readiness after every receipt.

### Workflow Initialization And Freeze

`initialize_section_workflow` and `freeze_section_from_phase03_artifact` are canonical materialization actions, not provider or writing actions.

Tightening applied:

- Both are now marked `approval_required=True` in the BookForge capability projection.
- Both declare `does_not_call_provider=True` and `does_not_write_prose=True`.
- `freeze_section_from_phase03_artifact` declares `freezes_one_section_only=True`.

### Scene Continuation

`continue_scene` remains the preferred adaptive authoring primitive.

It executes exactly one readiness-recommended scene-phase child action per call and returns an `author_loop_step_receipt_v1`. It does not loop internally. Multi-step author loops are owned by Nanda, bounded by max steps/time/cancel, and must refresh branch/readiness/legal-action truth between child calls.

### Section Macro

`write_frozen_section` is intentionally broad. It wraps `runner.run_section_range(...)` and can plan, write, repair, lint, and commit every missing scene in the selected frozen section.

Tightening applied:

- Capability descriptor now requires approval.
- Capability descriptor marks it as `broad_macro=True`.
- Capability descriptor declares `approval_class="section_macro"`.
- Capability descriptor declares `not_for_single_scene_requests=True`.
- Capability descriptor declares `preferred_single_scene_action="continue_scene"`.
- Capability descriptor declares `step_count_per_call="all missing scenes in the selected frozen section"`.
- Dynamic legal-action details now include the same broad-macro warning plus `scene_start`, `scene_end`, and `scene_count`.

## Remaining Boundary

BookForge still exposes direct CLI commands for legacy/operator use, including broad macro commands. Those commands are explicit names (`write-section`, `advance-section`, `run_loop`) rather than hidden side effects of narrow skills. `bookforge run` defaults to one scene when no `--steps` or `--until` is supplied, but it remains an operator macro because `--until` can intentionally broaden it.

For Nanda/agentic authoring, the safe default remains:

1. Query capability projection.
2. Query selected-scope legal actions/readiness.
3. Prefer `continue_scene` for scene-scoped writing.
4. Treat `write_frozen_section` as an approval-gated section macro.
5. Execute one approved step.
6. Refresh state before any next step.

## Validation

Focused regression:

```text
python -m pytest tests/test_outline_start_actions.py tests/test_capability_projection.py tests/test_action_discovery.py -q
44 passed
```
