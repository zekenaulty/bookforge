# 2026-04-29 Nanda Consumption: Workflow Materialization Bridge

Status: Nanda consumption implemented and validated

## Summary

Nanda now consumes BookForge's existing canonical materialization actions after
the provider-backed starter outline:

- `initialize_section_workflow`
- `freeze_section_from_phase03_artifact`

These remain separate actions in the graph. The starter outline action writes
authored outline run artifacts only. Workflow initialization and section
freezing are explicit canonical-gated materialization steps. Branch creation and
prose writing remain later steps.

## Nanda Surfaces Added

- Bridge functions:
  - `initialize_section_workflow(...)`
  - `freeze_section_from_phase03_artifact(...)`
- Ops routes:
  - `POST /api/ops/initialize_section_workflow`
  - `POST /api/ops/freeze_section_from_phase03_artifact`
- BookForge job actions for both.
- Bridge-status registration for `/api/scope-capabilities`.
- Author seed/BookIntent panel controls for:
  - draft starter outline
  - initialize workflow
  - freeze first section
  - create first-section branch through the existing `create_rerun_branch`
    action

## Safety Contract

- Both materialization actions require `allow_canonical=true` from Nanda.
- Neither materialization action calls the provider.
- Neither materialization action creates a branch.
- Neither materialization action writes prose.
- The visible new-book path remains graph traversal:
  `BookIntent -> create book -> starter outline -> initialize workflow -> freeze
  section -> create branch -> continue_scene`.

## Validation

Nanda validation:

- `python -m pytest tests\test_ops.py tests\test_jobs.py tests\test_api.py::CapabilitiesRouteTests -q`
- `python -m compileall -q src tests`
- `npm run build`

## Remaining Joint Gap

The branch receipt from first-section branch creation still needs a cleaner UI
handoff into the selected book/branch workbench. Today the branch can be
created as a job, but the user still needs a refresh/selection step before
running `continue_scene` or `AuthorWorkLoop`.
