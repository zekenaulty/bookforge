# Acceptance

## Required For Draft Promotion
- The plan explicitly separates static capability projection from dynamic readiness.
- The plan includes the unit boundary doctrine and prevents internal helpers from becoming projected skills.
- The plan explains how adaptive author graph traversal works without mandatory rails.
- The plan includes a Nanda surface/API gap audit grounded in current Nanda plans, FastAPI routes, bridge modules, and UI files.
- The plan includes a route/screen crosswalk showing how current Nanda UI/API affordances depend on BookForge surfaces.
- The plan includes a major surface backlog with priorities, likely APIs, commands/skills, and definitions of done.
- The plan includes concrete unit examples so future command/skill extraction preserves true micro/macro boundaries.
- The plan includes concrete contract fields for capability descriptors.
- The plan includes tests that catch stale projected actions and omitted public actions.
- The plan includes Nanda consumption fixture requirements.
- The plan covers future MCP-style mapping without requiring MCP implementation.
- The plan routes missing BookForge-owned APIs to either this projection plan or named successor plans.

## Required For Implementation Completion
- `CapabilityProjection` and descriptor contracts exist.
- Python query surface returns projection.
- CLI JSON surface returns projection.
- Projection includes action/query/readiness evidence sources.
- Projection distinguishes read-only, diagnostic-only, branch-local mutation, canonical mutation, promotion, and assembly.
- Projection includes expected receipt types and artifact status outputs.
- Macro workflows expose child actions.
- Tests fail on stale projected action keys.
- Tests fail on unprojected public actions unless explicitly excluded.
- Nanda can consume fixture output without hardcoding BookForge actions.
- The projection output can represent BookForge-owned surfaces that are missing or successor-plan-scoped without making them executable.
- Nanda filesystem fallbacks are labeled diagnostic when BookForge-owned query surfaces exist.
- The fixture includes implemented Nanda-facing query/action surfaces such as reader, book cards, branch detail, branch artifact index, branch diff summary, recovery anchor candidates, recovery plan preview, author-loop envelopes, chapter seam queue, scene-pair seam detail, scene-pair seam alignment, bridge-scene planning, and bridge-scene apply/materialization, plus at least one current gap such as deep inventory, manuscript export, or cross-section bridge insertion validation.
