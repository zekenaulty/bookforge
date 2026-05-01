# 2026-04-29 Slice Note: Writing Bootstrap Status

## Context

Nanda can now move a user from author-only ideation into a created BookForge book, but the path from that book to branch-local writing has several distinct BookForge-owned setup steps:

1. `draft_starter_outline_from_intent`
2. `initialize_section_workflow`
3. `freeze_section_from_phase03_artifact`
4. `create_branch`
5. `continue_scene`

The author agent needs a single read-only way to ask "what is the next real BookForge move before I can write?" without conflating status inspection with provider calls or mutations.

## Added Surface

BookForge now exposes `query.writing_bootstrap_status` through:

- Python: `bookforge.query.get_writing_bootstrap_status(...)`
- CLI: `bookforge workflow writing-bootstrap --book <id> [--branch-id <id>] [--chapter <n>] [--section <n>] [--scene <n>] --json`
- Capability projection: `query.writing_bootstrap_status`

The query returns `writing_bootstrap_status_v1`, including:

- overall status
- `can_start_writing`
- recommended next action
- required approval class
- target selector and target branch
- per-stage status rows
- artifact refs/statuses for BookIntent, outline, and workflow registry artifacts
- warnings and blocked reasons

## Boundary

This query is read-only. It does not:

- create a starter outline
- call an LLM/provider
- initialize workflow state
- freeze sections
- create branches
- write prose

It uses `legal-actions` evidence before recommending setup actions. If outline lineage reports `chimera_risk`, bootstrap blocks and points callers toward lineage/recovery diagnostics.

## Nanda Use

Nanda can call this after `create_book_from_intent` to decide whether to show:

- "Draft starter outline" when the created BookIntent has no outline run
- "Initialize workflow" after starter outline artifacts exist
- "Freeze first section" after workflow init
- "Create branch" after a section is frozen
- "Continue scene" when a branch-local scene can be written

This is the missing status bridge between Smoke A (book creation) and Smoke B (branch-local writing heartbeat).

## Validation

- `tests/test_writing_bootstrap.py`
- `tests/test_capability_projection.py`
- `tests/fixtures/capability_projection_v1.json` regenerated from the live BookForge projection
