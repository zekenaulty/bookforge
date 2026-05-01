# Nanda API/UI Crosswalk For BookForge Surfaces

Date: 2026-04-27
Source workspace: `C:\Users\Zythis\source\repos\nanda`

## Purpose
This crosswalk maps what Nanda currently exposes to users and agents to the BookForge surfaces that must exist for those affordances to be truthful.

The important distinction:
- Nanda can display fallback information today.
- BookForge must provide canonical/queryable surfaces before Nanda treats that information as execution truth or mutation input.

## FastAPI Route Crosswalk

| Nanda Route | Current Data Source | Current Trust Level | BookForge Surface Needed | Why It Matters |
| --- | --- | --- | --- | --- |
| `GET /api/workspace` | `nanda.knowledge.workspace_state` over BookForge query/filesystem | Mostly queryable, with fallback risk | Continue expanding `bookforge.query.workspace`, `workflow`, `lineage`, `integrity` | Workspace summary is the root truth strip for author chat and book cards. |
| `GET /api/integrity` | Nanda observer over workspace snapshot | Queryable summary | Richer BookForge issue tickets and localized integrity evidence | Nanda can classify global risk but needs affected scopes and evidence refs to guide actions. |
| `GET /api/triage` | Nanda observer triage | Nanda-owned | BookForge issue/action readiness evidence | Triage should recommend from real legal/readiness surfaces, not broad heuristics. |
| `GET /api/signatures` | Nanda filesystem bridge to BookForge thoughts/signatures | Diagnostic | BookForge thought-context projection and signature/probe index | Signatures are context-management aids, not execution truth; projection must label them diagnostic. |
| `GET /api/authors` | Nanda filesystem bridge to author files | Display/query fallback | `list_authors`, `get_author_profile`, author version metadata | Author UI can list authors, but creation/refinement must be BookForge-owned. |
| `GET /api/books` | Nanda now prefers BookForge `list_book_cards(...)` | Queryable | Keep book-card query projected; future book intent/synopsis remains separate | Book cards now have BookForge-owned integrity/current-node/reader availability without filesystem archaeology. |
| `GET /api/book-reader` | Nanda now prefers BookForge reader query with filesystem diagnostic fallback | Queryable | Keep `get_book_reader_index`, `get_book_reader_chapter`, `get_book_reader_scene`, and `get_book_reader_anchor` projected | Reader can show artifact status and branch scope before prose guides mutation. Reader anchors add source hashes, span offsets, and mutation-target safety for selected passages. Successor work can deepen quality gates and compile/export. |
| `POST /api/ops/create_rerun_branch` | Direct BookForge branch import/call | Wired but narrow | Capability descriptor, branch inventory/detail/artifact-index query, branch-local receipt projection | Nanda can create a branch and inspect branch state/next actions/artifacts; the workbench still needs UI wiring for branch detail. |
| `POST /api/ops/refresh_character_appearance_projection` | Direct BookForge projection action | Wired but narrow | Capability descriptor, readiness, receipt expectations | Useful first-class projection action; should appear as branch/main-safe diagnostic/provisional capability. |
| `POST /api/ops/draft_scene_setting_projection` | Direct BookForge projection action | Wired but narrow | Capability descriptor, readiness, artifact status | Setting/background work matters for future author context and scene planning. |
| `POST /api/ops/extract_scene_setting_from_prose` | Direct BookForge projection action | Wired but narrow | Capability descriptor, source-artifact refs, staleness labeling | Prose-derived setting must remain derived, not canonical setting truth. |
| `POST /api/author/chat` | Nanda author bus + query runner + Gemini | Nanda-owned control plane | BookForge capability projection, readiness, receipts, reader/query surfaces | Author voice must be grounded by BookForge truth and Nanda planning receipts. |
| `POST /api/author/conversations` | Nanda SQLite store | Nanda-owned | None directly; optional BookForge author/book validation queries | Conversation scope can be author-only/book/narrative/branch. BookForge should not own chat storage. |
| `GET /api/author/conversations` | Nanda SQLite store | Nanda-owned | None directly | BookForge does not need to expose conversation trace. |
| `GET /api/author/conversations/{id}/planning-artifacts` | Nanda SQLite store | Nanda-owned | BookForge receipts referenced by artifacts | Planning artifacts need stable BookForge receipt refs to remain meaningful. |

## UI Screen Crosswalk

| Nanda Screen | Current Surface | User Expectation | BookForge Gap | Projection Requirement |
| --- | --- | --- | --- | --- |
| Home / Launcher | Workspace/books/authors routes | Choose a book or author without knowing IDs | Book/card/author library surfaces | Project `book_library`, `author_library` query capabilities and label fallback status. |
| Authors | `/api/authors` filesystem bridge | Browse, create, refine, version authors | Author assets API | Project author read now; mark create/refine/select/rollback as designed until wired. |
| Author Detail | `/api/authors`, `/api/books` | Inspect profile, associated books, start author-only chat | Author profile/version/association surfaces | Project author profile/version and active-author selection gaps. |
| Books / Library | `/api/books` | See book health and open relevant work | Book intent/synopsis still missing | Book-card query is now BookForge-owned; successor work should add intent/synopsis rather than re-solving library cards. |
| Book Detail | `/api/books`, local capability derivation | Status board, current node, warnings, actions | Book intent/synopsis, branch detail UI wiring | Project static capabilities plus dynamic readiness sources for this book. |
| Reader | `/api/book-reader` | Read canonical/provisional prose safely and select mutation-safe passages | Reader quality gates and compile/export, not basic reader query | Canonical reader and reader-anchor queries are now BookForge-owned; Nanda fallback should remain diagnostic only. |
| Observe / Integrity | workspace/integrity/triage/signatures/actions | Inspect state and risks | Localized issue surfaces and branch health | Project integrity, lineage, recovery diagnostics, branch status. |
| Author Chat Workbench | author route + planning artifacts | Ask author to reason, query, maybe act | Capability projection, action receipts, reader selection context | Project legal actions/readiness and produce fixture for Nanda registry. |
| Actions Pane | direct `create_rerun_branch`, placeholders | Execute safe scoped tools | Branch-local actions, promotion gates, assembly status | Project branch/create/discard/promote/assembly capabilities with approval metadata. |
| Scope Capability Panel | `ui/src/scope.ts` local derivation | Show what is actually available for this scope | Backend capability projection and Nanda overlay | Project engine truth; Nanda overlays `wired/queryable/designed/theater`. |
| Conversations | Nanda store placeholder | Search/resume chats/work contexts | None directly | Nanda-owned. BookForge receipts need stable refs for trace usefulness. |
| Future Branch Explorer | not present yet | Inspect branches/forks/timeline nodes | UI/API wiring for branch detail/diff view | BookForge now exposes branch inventory, branch detail, branch artifact index, and branch diff summary; Nanda still needs inspector flow. |
| Future Recovery Workbench | observer/recovery query receipts | Diagnose and execute repairs safely | Recovery action descriptors, impact reports, branch health, promotion readiness | Project recovery diagnostics/primitives, but keep mutation approval-gated. |
| Future Diff/Compare | not present yet | Compare branch-local prose/artifacts | Reader + artifact diff/read surfaces | Reader/artifact successor should provide comparison anchors. |
| Future Approval Queue | not present yet | Approve anchors, promotion, cleanup, broad recovery | Approval-required metadata and receipt refs | Projection needs approval reasons and refusal semantics. |

## Planner/Test Pressure From Nanda
Nanda tests already encode several BookForge expectations:

- Chapter questions must target prompt scope, not engine current node.
- Chimera risk prompts must query outline lineage audit, section matrix, and repair candidates.
- Recovery prompts must include legal next actions and recovery readiness.
- Downstream impact prompts must query branch health, blast radius, semantic review readiness, semantic review, and downstream dependency review.
- Candidate action comparison treats unwired `create_recovery_branch` as queryable/shadow, not executable.
- Reader route now prefers BookForge canonical reader and keeps filesystem as diagnostic fallback.
- Selected prose should be converted through BookForge reader anchors before Nanda treats the span as a mutation target.
- Author-only conversations exist; BookForge should support author assets but should not own conversation storage.

## Immediate Projection Consequences
The first capability projection should include these categories:

- `implemented_query`: workspace, workflow, lineage, integrity, characters, continuity, outline lineage, recovery diagnostics, scene context, book cards, reader views, reader prose anchors, branch inventory, branch detail, branch artifact index, branch diff summary, recovery anchor candidates, recovery plan preview.
- `implemented_readiness`: scene phase readiness, recovery plan/readiness, semantic review readiness.
- `implemented_action`: scene actions, projection actions, branch/recovery actions currently exported and discoverable.
- `implemented_macro`: section write/finalize flows where represented as macro recipes.
- `implemented_diagnostic`: thought context, semantic recovery review, downstream dependency review.
- `designed_gap`: author assets, book intent/synopsis, pairwise seam alignment, bridge-scene insertion, inventory/deep state, export/quality gates.
- `nanda_owned`: conversations, planning artifacts, UI routes, author voice, approval queue, capability buckets.

## High-Risk Mismatches To Prevent
- Filesystem fallback displayed as canonical reader truth after BookForge reader query is available.
- Static capability displayed as dynamic readiness.
- Branch-local action displayed as canonical mutation.
- Recovery diagnostic displayed as completed repair.
- Projection action displayed as canonical character/location truth.
- Thought signature context displayed as evidence that an action executed.
- Local UI capability derivation continuing after BookForge projection exists.
- Macro workflow displayed as the only valid path through the graph.

## What Nanda Needs From BookForge First
1. Capability projection for existing surfaces and explicit gaps.
2. Branch detail/workbench UI consumption, because branch-live mode needs more than a branch list.
3. Branch-local write/action descriptor hardening, because first live author action depends on it.
4. Recovery action projection, anchor candidates, plan preview, and readiness metadata, because Nanda is already planning shadow recovery.
5. Successor plans for author assets, book intent/synopsis, reader quality gates/export, seam alignment, and deep inventory/state.
