# 0030 Generate Projection From Existing Surfaces

Status: completed
Depends On: 0020

## Goal
Generate or assemble the first capability projection from real BookForge action, query, readiness, diagnostic, recovery, and receipt surfaces.

## Detailed Work
- Add a query module, likely:
  - `src/bookforge/query/capabilities.py`
- Build projection from existing descriptors where available.
- Use explicit adapters only where no registry exists yet, and cover those adapters with stale-surface tests.
- Include at minimum:
  - action discovery / legal next actions
  - scene-phase readiness
  - scene-phase primitive actions
  - branch-local scene write actions
  - recovery diagnostics and readiness
  - lineage and integrity query surfaces
  - branch creation / promotion / discard / assembly surfaces where currently wired
  - semantic/downstream recovery diagnostic surfaces
- Include current Nanda-needed query/action families where implemented:
  - appearance projection and refresh
  - setting/background projection and extraction
  - thought-context projection
  - outline lineage audit/matrix/inventory/candidates
  - recovery branch health/blast radius/semantic/downstream review
  - canonical reader index/chapter/scene query
  - book library/card query
  - branch/fork inventory, branch detail, and branch artifact index query
  - branch diff summary query
  - recovery anchor candidate and recovery plan preview query
  - author-loop envelope query
  - chapter seam queue query
  - scene-pair seam detail query
  - pairwise scene seam alignment action
  - bridge-scene insertion planning action
  - bridge-scene insertion apply action
- Include explicit documented gaps for Nanda-needed BookForge surfaces that are not implemented yet:
  - author create/refine/select/rollback assets API
  - book intent/synopsis query
  - cross-section bridge-scene insertion and downstream ref-map validation
  - deep state/inventory projection layers
  - manuscript export and quality gates
- Exclude internal helpers.
- Add documented exclusions for surfaces that are real but intentionally not projected yet.
- Record capability evidence sources using module/function/test/doc references where feasible.

## Projection Requirements
- Every executable public action discovered through existing action discovery must be projected or explicitly excluded.
- Projection must expose capability support, not dynamic readiness state.
- Readiness source should be a reference to the query function or command that can answer scope-specific readiness.
- Macro workflow capabilities should list child action IDs when the child relationship is known.
- Missing Nanda-needed surfaces should be represented as explicit gap entries or documented exclusions, not silently omitted when the UI already implies them.
- Gap entries must not be executable and must not appear as wired actions.

## Likely Files Touched
- `src/bookforge/query/capabilities.py`
- `src/bookforge/query/__init__.py`
- `tests/test_capability_projection.py`

## Tests
- Projection returns stable schema version.
- Projection includes known public action IDs.
- Projection excludes documented internal helpers.
- Projection fails if a projected action has no evidence source.
- Projection fails if an action descriptor points to a missing action key.
- Projection fails if capability descriptor says "ready" or "blocked" as a static property.

## Definition Of Done
- Python query returns a `CapabilityProjection`.
- Projection is sourced from real BookForge surfaces, not a free-floating manual list.
- Stale or missing public action projection is test-detectable.
- Nanda can distinguish read-only, diagnostic, branch-local mutation, promotion, and macro capabilities from the projection alone.
- Nanda can also distinguish implemented BookForge surfaces from successor-plan gaps without relying on local hardcoded tables.
