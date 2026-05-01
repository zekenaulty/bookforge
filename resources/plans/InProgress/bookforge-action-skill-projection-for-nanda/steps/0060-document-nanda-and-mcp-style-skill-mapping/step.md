# 0060 Document Nanda And MCP-Style Skill Mapping

Status: completed
Depends On: 0050

## Goal
Document how BookForge capability projection maps to Nanda's author surface and to a future MCP-style skill/tool layer without committing to a protocol implementation now.

## Detailed Work
- Document the ownership split:
  - BookForge emits engine capability truth.
  - Nanda maps engine truth to UI/agent buckets.
  - Nanda owns planner strategy, belief state, candidate action comparison, approval flow, and author explanation.
- Document Nanda classification examples:
  - `wired`
  - `queryable`
  - `designed`
  - `theater`
- Document static/dynamic split:
  - projection says the capability exists
  - readiness says whether the current scope can use it now
  - execution receipt says what actually happened
- Document macro vs primitive mapping:
  - macros are recipes
  - primitives are direct choices
  - validation gates can be inserted adaptively
  - promotion requires explicit validation/approval
- Document future MCP-style mapping:
  - capability descriptor -> MCP tool metadata candidate
  - readiness source -> MCP resource/query candidate
  - receipt schema -> tool result schema
  - artifact refs/statuses -> resource references
- Document adaptive author examples:
  - write one scene only
  - align a scene pair
  - insert a bridge scene if needed
  - rewrite an old scene in a branch
  - compare branch candidates before promotion

## Likely Files Touched
- `docs/help/workflow.md` or new `docs/help/capabilities.md`
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/artifacts/nanda-mcp-style-mapping.md`

## Tests
- Documentation-only step.
- Run full capability tests after doc changes if examples include generated snippets.

## Definition Of Done
- Docs explain how Nanda should consume BookForge capability truth without duplicating it.
- Docs explain why macro workflows are optional recipes, not rails.
- Docs explain how future MCP-style skills can map from the projection without hand-maintained parallel lists.
