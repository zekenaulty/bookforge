# Nanda Surface API Gap Audit

Date: 2026-04-27
Source workspace: `C:\Users\Zythis\source\repos\nanda`

## Summary
Nanda has enough UI and API shape to expose BookForge capability drift quickly. The missing BookForge work is not one API; it is a set of self-describing surfaces that let Nanda classify capability, inspect readiness, dispatch one safe action, show receipts/artifacts, and refuse unsafe or unwired paths.

This audit maps current Nanda plans, FastAPI routes, bridges, and UI panels to BookForge-owned surfaces.

## Nanda Surfaces Inspected
- Plans:
  - `nanda-author-start-authoring`
  - `nanda-author-reasoning-loop`
  - `nanda-governed-authoring-runtime`
  - `bookforge-reader-query-api-spec.md`
- FastAPI:
  - `/api/workspace`
  - `/api/integrity`
  - `/api/triage`
  - `/api/signatures`
  - `/api/authors`
  - `/api/books`
  - `/api/book-reader`
  - `/api/ops/create_rerun_branch`
  - `/api/ops/refresh_character_appearance_projection`
  - `/api/ops/draft_scene_setting_projection`
  - `/api/ops/extract_scene_setting_from_prose`
  - `/api/author/chat`
  - `/api/author/conversations`
  - `/api/author/conversations/{id}/planning-artifacts`
- UI:
  - workspace shell
  - Authors
  - Books / Library
  - Book Detail
  - Reader
  - Observe / Integrity
  - Author Chat Workbench
  - Actions pane
  - Scope Capability panel
  - Conversations

## Coverage Matrix

| Nanda Need | Current Nanda Evidence | BookForge Surface Needed | Current BookForge State | Planning Home |
| --- | --- | --- | --- | --- |
| Machine-readable engine capabilities | `nanda-author-start-authoring` step `0090`, `ui/src/scope.ts`, `ScopeCapabilityPanel` | `get_capability_projection(...)` plus CLI JSON | Implemented | This plan |
| Route/scope capability truth | `ui/src/scope.ts` derives local `UiCapability` | Capability projection filtered by `ScopeSelector` plus Nanda bridge/UI status overlay | Implemented projection; Nanda maps UI availability | This plan plus Nanda registry bridge |
| Legal next actions | `AuthorContextPackage.execution_options`, `legal_next_actions` query receipts | Project `ExecutionOption` surfaces with unit type, branch policy, mutation class, receipt expectations | Implemented query, missing full projection metadata | This plan |
| Scene-phase readiness | `scene_phase_readiness` query registry, AuthorContextPackage scene phase | Project readiness source and descriptor; keep dynamic readiness separate | Implemented | This plan |
| First branch-local author action | `nanda-author-start-authoring` step `0040` blocked | Stable branch-local scene/section action descriptor, request schema, receipt schema, artifact statuses, next-actions snapshot | BookForge scene actions exist; Nanda needs projection and stable bridge target | This plan for descriptor; Nanda bridge after |
| Generic action dispatch | Nanda currently has per-action `bookforge_ops.py` wrappers | Optional stable `execute_capability_action`/`execute_action` contract or explicit action-specific builders with descriptors | Not generalized | Future BookForge/Nanda execution bridge; do not block projection |
| Branch inventory/status | UI needs Branch Explorer; capability xref marks branch status designed | `get_branch_inventory`, `get_branch_detail`, `get_branch_artifact_index`, `get_branch_diff_summary`, branch current-node and lifecycle projection | Implemented read-only query surfaces; Nanda still needs inspector flow | This plan |
| Create rerun branch | `/api/ops/create_rerun_branch` wired through BookForge branch functions | Capability descriptor for `create_branch`/rerun materialization, receipt expectations, branch policy | Implemented action, projection missing | This plan |
| Branch rebase/discard/promote | Nanda modes mention branch-live/canonical-gated; ActionsPane has placeholders | Capability descriptors, readiness, approval metadata, receipts | BookForge actions exist in execution exports/legal actions; Nanda not wired | This plan for truth; Nanda remains gated |
| Fork group / assembly | Governed runtime and ActionsPane name assembly | Capability descriptors for fork group and assembly branches; branch/fork status queries | Implemented inventory/detail/artifact-index basics; diff still future | This plan plus future branch explorer depth |
| Canonical reader | `/api/book-reader` uses BookForge reader when available | `get_book_reader_index`, `get_book_reader_chapter`, `get_book_reader_scene` with artifact status/source node/integrity flags | Implemented canonical query surface | This plan; quality gates/export successor remains |
| Books library cards | `/api/books`, `books.py` uses BookForge when available | `list_book_cards`, `get_book_card` with title, author, integrity, current node, branch count, modified time | Implemented consolidated BookForge query | This plan |
| Book detail synopsis/intent | Book Detail UI has no synopsis/intent source | `get_book_intent`, `get_book_synopsis`, optional approve/set surfaces | Missing | Successor `bookforge-book-intent-and-synopsis-surface` |
| Author list/read | `/api/authors`, author context profile loading, Authors detail UI | `list_author_profiles`, `get_author_profile`, version metadata, rich voice/style surface | Implemented query surface and projected capabilities; Nanda now renders exact selected-book author version | This plan |
| Author creation/refinement | Nanda step `0080`, UI marks designed | `create_author`, `refine_author`, `preview_author`, `select_author_version`, `rollback_author_version` receipts | `create_author` and `refine_author` implemented as versioned `author_assets` actions with execution receipts; preview/select/rollback still missing | This plan for create/refine; successor for preview/select/rollback |
| Character appearance projection | Nanda wired op wrapper and scene context query | Capability descriptors for appearance query and projection refresh action | Implemented in BookForge 0075-era modules | This plan projects; future appearance plan can deepen |
| Scene setting/background projection | Nanda wired op wrapper and setting query | Capability descriptors for setting query, author-drafted setting, prose-extracted setting | Implemented in projection actions/query | This plan projects |
| Deep state / inventory layers | Governed runtime mentions state manager; user called out future inventory layers | Query/action descriptors for inventory/state projections and mutation-safe refresh/extract actions | Not clearly present as stable public surface | Future projection-layer successor; projection should allow layer categories |
| Thought context/signature projection | Query registry has `thought_context_projection`; signatures route exists | Descriptor should mark thought context as diagnostic/context reuse, not execution truth | Implemented query/fallback mix | This plan projects with diagnostic artifact status |
| Outline lineage diagnosis | Query registry includes lineage audit/matrix/inventory/candidates | Project outline lineage queries as read-only diagnostics | Implemented | This plan |
| Recovery impact planning | Nanda reasoning loop needs impact reports and candidate comparisons | Query surfaces for impact inputs, blast radius, candidate repair actions, anchor candidates, plan preview, downstream dependency review | Implemented baseline recovery planning queries | This plan projects current surfaces; future recovery story-weaving plan for deeper mutation |
| Recovery primitives | Nanda wants quarantine, normalize, invalidate, rebuild, redraft, validate, promote | Stable descriptors, readiness, request schemas, receipt schemas, approval metadata, removal/quarantine refs | Implemented action family exists; Nanda not wired | This plan projects; future action bridge/approval work in Nanda |
| Semantic/downstream recovery review | Nanda query runner lists semantic/downstream reviews | Descriptors for diagnostic actions and read surfaces | Implemented 0082 | This plan projects |
| Quality gates/export | Nanda wants reader/artifact panels and eventual publish/export | Compile/export, word count, banned phrases, repetition/similarity, quality gate receipts | Missing or partial legacy stubs | Successor `bookforge-manuscript-output-and-reader-quality-gates` |
| Lint/repair routing | Nanda will steer repairs and avoid overbroad work | Route descriptor and receipts for prose-only, state, seam, full repair lanes | Not split enough yet | Successor `bookforge-lint-repair-routing` |
| Pairwise seam alignment | User expects scene A/B LLM seam rewrite as authorial process | `align_scene_pair` readiness/action, boundary window contract, original/fixed prose artifacts, receipt | Not present as stable public capability | Successor seam/repair routing plan; projection may include as designed exclusion only |
| Insert bridge scene | Adaptive author traversal may need inserted scenes organically | `insert_scene`/`insert_bridge_scene` branch-local action, outline/prose/state impacts, renumber or stable ref rules | Not present | Future authoring primitive plan; projection should not claim wired |
| Conversation trace access | Nanda step `0070` | No BookForge surface required | Nanda-owned | No BookForge delta |
| Live bus / streaming events | Nanda step `0010` | Optional long-running BookForge progress receipt/event surfaces later | Mostly Nanda-owned for chat; BookForge command progress can remain receipts for now | Future only |

## Minimum BookForge Coverage Needed For Nanda's First Live Branch-Local Authoring
1. Capability projection includes `write_scene_prose` or the selected first branch-local action with:
   - required selector shape
   - branch policy
   - mutation class
   - readiness source
   - request builder evidence
   - expected receipt type
   - produced artifact statuses
   - refusal semantics
2. Dynamic readiness remains queryable for the target scene/scope.
3. The action can run on a derived branch and produce a receipt that states:
   - `branch_id`
   - `canonical_change_status: none`
   - produced prose/artifact refs
   - artifact status
   - next legal actions or refresh hint
4. Nanda can display the produced artifact without using it as canonical main state.

## Surfaces This Plan Must Cover Directly
- Capability projection contract.
- Descriptor coverage for existing BookForge legal actions.
- Descriptor coverage for existing query/readiness/diagnostic surfaces.
- Descriptor metadata for Nanda bucket mapping:
  - branch policy
  - mutation class
  - approval required
  - expected receipt
  - artifact statuses
  - evidence source
  - refusal semantics
- Fixture examples for:
  - reader query
  - branch detail query
  - branch artifact index query
  - branch diff summary query
  - recovery anchor candidates query
  - recovery plan preview query
  - branch-local write
  - recovery diagnostics
  - promotion-gated action
  - designed but unwired seam alignment / bridge-scene insertion

## Surfaces To Route To Successor Plans
- Reader quality gates, manuscript compile, and export:
  - `bookforge-manuscript-output-and-reader-quality-gates`
- Author asset creation/refinement:
  - `bookforge-author-assets-api`
  - Author list/read/profile and create/refine actions are now implemented; this successor should focus on preview, version selection, rollback, assigning an author version to a book, and deeper receipt/readiness UX.
- Book intent/synopsis:
  - `bookforge-book-intent-and-synopsis-surface`
- Lint/repair routing and pairwise seam alignment:
  - `bookforge-lint-repair-routing`
- Series/continuity rollups:
  - `bookforge-series-continuity-rollups`
- Deep state/inventory projections:
  - likely successor under projection-layer hardening after appearance/setting stabilizes

## BookForge-Owned vs Nanda-Owned
- BookForge owns:
  - engine capability truth
  - legal actions
  - readiness
  - mutation
  - receipts
  - artifact status
  - canonical reader truth
  - author asset persistence
  - branch/recovery state
- Nanda owns:
  - route-level UI buckets
  - bridge/UI exposure status
  - planner decisions
  - belief/candidate/commit-gate artifacts
  - conversation trace
  - author voice
  - shadow vs live mode policy
  - human approval workflow

## Open Planning Implication
The capability projection should not try to implement every missing surface. It should make missing surfaces visible and classifiable. Nanda can then display `queryable`, `designed`, or `theater` honestly while BookForge successor plans add the actual APIs.
