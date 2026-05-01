# 0015 Map Nanda Surface API Needs

Status: completed
Depends On: 0010

## Goal
Cross-reference Nanda's plans, FastAPI routes, bridge modules, and UI screens against the BookForge-owned surfaces they need, then decide which gaps belong in this capability projection plan and which need successor plans.

## Nanda Inputs To Inspect
- Plans:
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-author-start-authoring\plan.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-author-reasoning-loop\plan.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-governed-authoring-runtime\plan.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\bookforge-reader-query-api-spec.md`
- FastAPI:
  - `src/nanda/api/app.py`
  - `src/nanda/api/routes/author.py`
  - `src/nanda/api/routes/books.py`
  - `src/nanda/api/routes/reader.py`
  - `src/nanda/api/routes/ops.py`
  - `src/nanda/api/routes/authors.py`
  - `src/nanda/api/routes/integrity.py`
- BookForge bridge:
  - `src/nanda/bridge/bookforge/author_context.py`
  - `src/nanda/bridge/bookforge/bookforge_ops.py`
  - `src/nanda/bridge/bookforge/books.py`
  - `src/nanda/bridge/bookforge/reader.py`
  - `src/nanda/bridge/bookforge/scene_context.py`
- UI:
  - `ui/src/scope.ts`
  - `ui/src/api/types.ts`
  - `ui/src/api/client.ts`
  - `ui/src/features/scope/ScopeCapabilityPanel.tsx`
  - `ui/src/features/actions/ActionsPane.tsx`
  - `ui/src/features/books/BookDetailScreen.tsx`
  - `ui/src/features/books/ReaderScreen.tsx`

## Work
- Produce a matrix of Nanda-visible screens/routes/bridges and their required BookForge surfaces.
- Produce an API/UI crosswalk that ties concrete Nanda routes/screens to BookForge-owned surfaces and fallback risks.
- Produce a surface backlog that groups missing BookForge work into large successor-ready slices.
- Produce concrete examples of public capability units vs internal helpers.
- Classify each required BookForge surface as:
  - already implemented and should be projected now
  - implemented but missing stable descriptor/receipt coverage
  - Nanda filesystem fallback that should move into BookForge
  - planned successor surface outside this projection plan
  - Nanda-owned only, no BookForge delta required
- Identify the minimum surfaces needed for Nanda's first live branch-local authoring action.
- Identify surfaces needed by the Books/Reader/Scope/Actions screens so UI affordances can stop using local derivation.
- Identify surfaces needed for future recovery/story-weaving plans without turning them into one-off `fix_this_book` commands.

## Likely Files Touched
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/artifacts/nanda-surface-api-gap-audit.md`
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/artifacts/nanda-api-ui-crosswalk.md`
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/artifacts/bookforge-nanda-surface-backlog.md`
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/artifacts/capability-unit-examples.md`
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/plan.md`
- `resources/plans/Drafts/bookforge-action-skill-projection-for-nanda/validation/acceptance.md`

## Tests
- Planning-only step.
- Compile the plan after updates.

## Definition Of Done
- Gap audit names all BookForge-owned surfaces Nanda currently needs.
- API/UI crosswalk maps current Nanda route and screen behavior to BookForge surface requirements.
- Surface backlog gives large coherent successor slices, not scattered endpoint requests.
- Capability examples clarify which micro/macro units should become skills and which helpers stay internal.
- Gap audit distinguishes BookForge-owned work from Nanda-owned work.
- Each missing surface is routed to this plan or an explicit successor plan.
- The capability projection plan's acceptance criteria cover Nanda's real API/UI consumption path.
