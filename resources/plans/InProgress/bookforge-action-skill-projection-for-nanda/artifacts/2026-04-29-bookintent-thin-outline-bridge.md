# 2026-04-29 Slice Note: BookIntent To Thin Outline Bridge

## Closed Gap

BookForge now exposes a narrow bridge between canonical book creation and workflow initialization:

- `create_book_from_intent` creates the book shell and copied `book_intent.json`.
- `draft_starter_outline_from_intent` calls the configured outline provider once to author a starter/thin outline from that created BookIntent.
- The action writes immutable outline run artifacts and latest pointers.
- `initialize_section_workflow` can then consume that run id.

This is not a deterministic scaffold and not the full multi-phase `deep_outline` pipeline.

## Boundary

`draft_starter_outline_from_intent` does:

- use the outline provider/LLM
- produce `outline/pipeline_runs/<run_id>/outline_final_v1_1.json`
- slice the authored outline into `outline_spine_v1.json` and `outline_sections_v1.json`
- write `outline_pipeline_report.json`, `pipeline_latest.json`, and related pointers
- emit receipt details with `provider_used=true`, `workflow_family=thin_outline`, and `deep_outline_pipeline=false`

It does not:

- run `bookforge outline generate`
- run the full phase 01-06 deep outline pipeline
- initialize workflow state
- freeze a section
- create a branch
- write prose

## Nanda Sequence

The intended new-book smoke chain is now:

1. author-only seed conversation
2. `draft_book_intent`
3. `approve_book_intent`
4. `create_book_from_intent`
5. `draft_starter_outline_from_intent`
6. `initialize_section_workflow`
7. `freeze_section_from_phase03_artifact`
8. `create_branch`
9. branch-local `continue_scene` / `author_work_loop`

Nanda should still use dynamic legal/readiness surfaces between each step.

## Future Follow-On

The starter/thin outline is the bootstrap. Adaptive scene/section traversal should later be able to request narrower missing outline fragments instead of forcing another broad outline pass. That should be a scene/section-scoped authoring action, not this book-level starter action.

## Validation

- `python -m pytest --basetemp .pytest_tmp_starter_outline tests/test_outline_start_actions.py -q`
- Result: `2 passed`
