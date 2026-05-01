# 0050 Add Nanda Consumption Fixture

Status: completed
Depends On: 0040

## Goal
Provide representative projection fixture output that Nanda can consume in tests without manually duplicating BookForge's capability graph.

## Detailed Work
- Add a fixture artifact under the plan or test fixture area.
- Include examples for:
  - read-only query
  - readiness query
  - primitive scene action
  - diagnostic validation gate
  - branch-local mutation
  - promotion-gated mutation
  - macro workflow with child actions
  - blocked/refusal semantics
  - recovery diagnostic
- Include Nanda UI/API gap examples:
  - canonical reader query is implemented and filesystem fallback is diagnostic only
  - author profile read/list is implemented, while creation/refinement/select/rollback remains designed until the BookForge-owned mutation API stabilizes
  - branch inventory/detail is implemented and supports branch workbench inspection
  - pairwise seam alignment is designed, not wired
  - bridge-scene insertion is designed, not wired
- Include at least one projected future-shaped omission or documented exclusion so Nanda can classify unsupported/theater capability claims safely.
- Coordinate with Nanda's capability-registry ingestion plan:
  - Nanda decides `wired`, `queryable`, `designed`, or `theater`.
  - BookForge only reports engine truth.

## Likely Files Touched
- `tests/fixtures/capability_projection_v1.json` or plan-local artifact fixture
- `tests/test_capability_projection.py`
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/artifacts/nanda-consumption-fixture-notes.md`

## Tests
- Fixture validates against `CapabilityProjection`.
- Fixture includes required representative categories.
- Fixture does not include dynamic readiness verdicts as static fields.
- Fixture can be regenerated or compared to current projection without silent drift.

## Definition Of Done
- Nanda has a stable example payload for registry ingestion.
- Fixture demonstrates mutation class, branch policy, artifact status, approval, and refusal semantics.
- Fixture supports author-pane honesty: it can explain capability, readiness source, and mutation risk without persona inference.
- Fixture covers current Nanda screens: Reader, Actions, Scope Capability panel, Book Detail, and Author assets.
