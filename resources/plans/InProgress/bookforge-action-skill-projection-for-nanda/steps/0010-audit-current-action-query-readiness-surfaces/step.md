# 0010 Audit Current Action Query Readiness Surfaces

Status: completed
Depends On: -

## Goal
Create a concrete inventory of BookForge surfaces that can become projected capabilities, and separate them from internal helpers that should not be exposed.

## Detailed Work
- Inspect existing action discovery:
  - `src/bookforge/query/actions.py`
  - `src/bookforge/contracts/execution_option.py`
- Inspect scene-phase readiness and execution:
  - `src/bookforge/query/scene_phase.py`
  - `src/bookforge/execution/actions.py`
- Inspect recovery and diagnostic surfaces:
  - `src/bookforge/query/recovery.py`
  - `src/bookforge/execution/recovery_actions.py`
  - `src/bookforge/execution/recovery_semantic.py`
- Inspect branch and promotion surfaces exposed through legal actions.
- Inspect query-only surfaces:
  - workspace/status
  - lineage
  - integrity
  - characters
  - continuity
  - appearance
  - setting/background
  - thought context/signature views
  - manuscript/prose reader surfaces, if present
- Classify each surface as:
  - public capability candidate
  - readiness source
  - macro workflow
  - diagnostic/projection query
  - internal helper
  - future capability placeholder
- Identify public actions that currently lack:
  - stable action key
  - readiness source
  - receipt contract
  - artifact status declaration
  - branch policy
  - approval requirement
  - refusal semantics

## Unit Boundary Checks
- Confirm `write_scene_prose`, `lint_scene_prose`, `repair_scene_prose`, branch creation, recovery diagnostics, and promotion are treated as public decision points.
- Confirm prompt rendering, provider calls, JSON parsing, retry logic, and file formatting stay internal.
- Confirm macro workflows such as section advance can be represented as recipes with child actions rather than mandatory rails.

## Likely Files Touched
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/artifacts/current-surface-audit.md`
- No production code required in this step unless a missing export blocks the audit.

## Tests
- No new automated tests required.
- Manual validation: audit file lists all real public action IDs returned by current action discovery fixtures.

## Definition Of Done
- Surface audit exists.
- Every current public action/query/readiness surface has an initial unit classification.
- Internal helpers that must not become projected skills are explicitly called out.
- Gaps needed for `0020` contract design are listed.
