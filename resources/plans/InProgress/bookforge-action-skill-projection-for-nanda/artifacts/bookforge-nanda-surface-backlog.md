# BookForge Surface Backlog For Nanda

Date: 2026-04-27

## Purpose
This backlog turns Nanda's current and planned UI/API needs into large BookForge-owned coverage slices. It is intentionally broader than the first projection implementation, so successor plans can be carved cleanly without losing context.

Priority meanings:
- `P0`: needed for truthful capability registry and first branch-local author action.
- `P1`: needed for usable author workbench, recovery planning, and safe branch navigation.
- `P2`: important for book completion/polish, but not required before first live author action.
- `P3`: longer-term series or protocol maturity.

## Slice 1: Capability Projection And Gap Truth
Priority: `P0`

Purpose:
- Let Nanda build a registry from BookForge engine truth.
- Stop manual allowlists and local UI derivation from becoming stale.

BookForge surfaces:
- `get_capability_projection(workspace=None, book_id=None)`
- CLI JSON command, likely `bookforge capabilities --json`.
- Capability descriptor contract.
- Descriptor evidence sources.
- Designed-gap entries for missing Nanda-required surfaces.

Commands/skills:
- `query_capabilities`
- `query_capability_by_scope`
- Future MCP-style `bookforge.capabilities.list`

Definition of done:
- Projection includes public queries, readiness, actions, diagnostics, macros, and promotion actions.
- Projection separates static support from dynamic readiness.
- Projection has branch policy, mutation class, approval requirement, artifact statuses, receipt expectations, and refusal semantics.
- Tests fail when a public action is not projected or explicitly excluded.

## Slice 2: Canonical Reader And Book Library
Priority: `P0/P1`
Status: implemented baseline; successor work should focus on quality gates, compile/export, and richer comparison/selection.

Purpose:
- Replace Nanda's direct filesystem reader fallback.
- Give the author pane safe prose visibility with artifact status and source node refs.

BookForge surfaces:
- `list_book_cards(workspace)`
- `get_book_card(workspace, book_id)`
- `get_book_reader_index(workspace, book_id, branch_id="main")`
- `get_book_reader_chapter(workspace, book_id, chapter_id, branch_id="main", include_text=True, max_text_chars=...)`
- `get_book_reader_scene(workspace, book_id, chapter_id, scene_id, branch_id="main", include_text=True, max_text_chars=...)`
- `get_book_reader_anchor(workspace, book_id, chapter_id, scene_id=None, branch_id="main", start_offset=None, end_offset=None, max_text_chars=...)`

Required fields:
- `book_id`
- `branch_id`
- `chapter_id`
- `section_id`
- `scene_id`
- title/summary where available
- `artifact_status`
- `source_artifact_ref`
- `source_node_ref`
- source hash and selected hash for anchors
- selected span offsets for anchors
- mutation-target safety status for anchors
- `integrity_flags`
- `staleness_reason`
- `truncated`
- word/character count

Commands/skills:
- `read_book_index`
- `read_chapter`
- `read_scene`
- `read_selected_excerpt`
- `anchor_selected_excerpt`

Definition of done:
- Nanda can remove fallback warning for canonical reader queries.
- Reader output marks contaminated/stale/quarantined/missing text explicitly.
- Branch-local prose can be read without presenting it as canonical main.
- Selected prose can be anchored before Nanda turns it into a rewrite/repair target.
- Tests cover missing scene, stale lineage, branch-local scene, and truncated output.

## Slice 3: Branch, Fork, And Timeline Explorer
Priority: `P1`
Status: inventory/detail/artifact-index/diff-summary baseline implemented; UI inspector and richer fork-group views remain.

Purpose:
- Let Nanda inspect branches after creating them.
- Support branch-live mode, recovery workbench, and future parallel writing.

BookForge surfaces:
- `get_branch_inventory(workspace, book_id)`
- `get_branch_detail(workspace, book_id, branch_id, chapter_id=None, section_id=None, scene_id=None)`
- `get_branch_artifact_index(workspace, book_id, branch_id, limit=...)`
- `get_branch_diff_summary(workspace, book_id, branch_id, against="main", limit=...)`
- future `get_fork_group_status(workspace, book_id, fork_group_id)`

Required fields:
- lifecycle state
- parent node
- current node
- merge operation
- fork group
- dirty/validation state
- promotion readiness
- stale parent/rebase requirement
- branch-local artifact refs
- issue tickets by branch

Commands/skills:
- `inspect_branch`
- `inspect_fork_group`
- `compare_branch_to_main`
- `query_branch_next_actions`

Definition of done:
- Nanda branch screen can show active/ready/blocked/stale/promoted/discarded from BookForge query output.
- Branch-local author action can refresh status after one execution through `get_branch_detail(...)`.
- Nanda can list branch-local artifact classes and branch/main relationships through `get_branch_artifact_index(...)`.
- Nanda can summarize branch-local changes through `get_branch_diff_summary(...)`.
- Tests cover stale parent, terminal branch refusal, and fork-group sibling status.

## Slice 4: First Branch-Local Authoring Execution
Priority: `P0/P1`

Purpose:
- Let Nanda run one safe authoring action without canonical mutation.
- Prove the author pane can plan, gate, execute, display receipt/artifact, and explain non-canonical status.

Candidate first action:
- `write_scene_prose` on a derived branch.

BookForge surfaces:
- action descriptor in capability projection
- readiness query for target scene/branch
- request builder schema
- execution action
- receipt schema
- reader/artifact query for produced output
- next-actions refresh after execution

Required receipt fields:
- `execution_outcome`
- `branch_id`
- `canonical_change_status: none`
- `mutation_class`
- `produced_artifacts[]`
- artifact statuses
- expected next legal actions/readiness refs
- refusal reason if blocked

Commands/skills:
- `write_scene_prose`
- later `plan_scene`, `preflight_scene_state`, `generate_continuity_pack`, `lint_scene_prose`, `repair_scene_prose`, `apply_scene_commit`

Definition of done:
- Main remains unchanged.
- Branch-local artifact is readable and labeled provisional.
- Re-running either resumes/idempotently refuses or creates a clearly separate revision.
- Nanda can show receipt and artifact in the author workbench.
- `continue_scene` emits a nested `author_loop_step_receipt_v1` so Nanda loop jobs do not need to reconstruct step receipts from loose execution-result detail fields.

## Slice 5: Recovery And Story-Weaving Primitives
Priority: `P1`

Purpose:
- Give Nanda enough primitives to reason, plan, and execute recovery/story-weaving without BookForge defining one-off `fix_book_x` commands.

BookForge surfaces:
- `create_recovery_branch`
- `quarantine_artifacts`
- `normalize_outline_scope`
- `invalidate_scope_outputs`
- `rebuild_state_scope`
- `redraft_scope`
- `validate_recovery_branch`
- `review_recovery_semantics`
- `review_downstream_dependencies`
- `promote_recovery_branch`
- `get_recovery_plan_readiness`
- `get_recovery_anchor_candidates`
- `get_recovery_plan_preview`
- `get_recovery_manifest`
- `get_recovery_branch_health`
- `get_recovery_blast_radius`
- `get_outline_repair_candidates`

Required contract details:
- destructive or quarantine actions require approval metadata
- anchor candidates expose `recommended_candidate_id`, `auto_selected_candidate_id`, and human-decision requirements
- plan preview emits ordered recovery steps before mutation
- broad-radius actions include blast-radius summary
- promotion receipts include removals/quarantines and integrity delta
- semantic reviews are diagnostic, not proof of story quality
- salvage references are non-canonical unless explicitly imported

Commands/skills:
- `create_recovery_branch`
- `query_recovery_anchor_candidates`
- `preview_recovery_plan`
- `quarantine_recovery_artifacts`
- `normalize_recovery_outline`
- `invalidate_recovery_outputs`
- `rebuild_recovery_state`
- `redraft_recovery_scope`
- `validate_recovery_branch`
- `review_recovery_semantics`
- `review_downstream_dependencies`
- `promote_recovery_branch`

Definition of done:
- Nanda can produce an impact report and task plan from query evidence.
- If exactly one coherent non-shelf timeline anchor exists, Nanda can auto-select it from BookForge evidence.
- If multiple conflicting anchors exist, Nanda can ask the user which timeline to inhabit before mutation.
- Every mutation is branch-first.
- Promotion removes invalid files, not only overwrites valid ones.
- Chimera risk clears only after validation and promotion.

## Slice 6: Pairwise Seam Alignment And Repair Routing
Priority: `P1/P2`
Status: `scene-pair seam alignment, chapter seam queue, and scene-pair seam detail implemented for derived branches; repair-route classification remains successor work`

Purpose:
- Implement the author's intended seam process: LLM-author rewrites the end of scene A and beginning of scene B together under bounded scope.
- Avoid deterministic prose mangling.

BookForge surfaces:
- `align_scene_pair_seam_action(workspace, request)` (implemented)
- `bookforge workflow align-scene-pair-seam` (implemented)
- `scene_pair_seam_report_path(...)` (implemented report location helper)
- `get_chapter_seam_queue(workspace, book_id, chapter_id, branch_id)` (implemented)
- `bookforge workflow chapter-seam-queue` (implemented)
- `get_scene_pair_seam_detail(workspace, book_id, chapter_id, scene_a, scene_b, branch_id)` (implemented)
- `bookforge workflow scene-pair-seam-detail` (implemented)
- future `get_scene_pair_seam_readiness(workspace, book_id, chapter_id, scene_a, scene_b, branch_id)`
- future `get_scene_pair_seam_report(...)`
- `get_chapter_seam_queue(...)`
- `repair_route_classification(...)`

Required fields:
- scene A ending window source
- scene B opening window source
- original segment refs
- rewritten segment refs
- preserved event constraints
- overlap/duplication/tense/continuity findings
- artifact status for original/fixed scene versions
- allowed edit window
- refusal for missing canonical/branch-local source

Commands/skills:
- `inspect_scene_pair_seam`
- `align_scene_pair`
- `align_chapter_seams`
- `classify_repair_lane`

Definition of done:
- Original scene prose is preserved. (implemented for branch-local pair alignment)
- Fixed scene prose is emitted with explicit branch-local artifact status. (implemented baseline)
- LLM is author; system supplies scope, constraints, and receipts. (implemented through existing seam repair prompt contract)
- Tests cover branch-local execution and projection/legal-action exposure. (implemented baseline)
- Nanda can query a chapter-level seam work queue before deciding which pair to align. (implemented baseline)
- Nanda can inspect one seam pair's existing report, issue counts, repair count, and artifact refs without reading raw branch files. (implemented baseline)
- Future tests should cover duplicated UI prompt overlap, repeated regrounding, tense blending, and no-op clean seam with real prompt fixtures.

## Slice 7: Scene Insertion And Organic Outline Growth
Priority: `P2`
Status: `same-section branch-local proposal and apply/materialization implemented; cross-section insertion and downstream ref-map validation remain successor work`

Purpose:
- Support adaptive authoring where a bridge scene or extra beat is inserted when needed, instead of treating scene count as a fixed pipeline output.

BookForge surfaces:
- `plan_bridge_scene_insertion_action(workspace, request)` (implemented proposal-only)
- `bookforge workflow plan-bridge-scene-insertion` (implemented proposal-only)
- `apply_bridge_scene_insertion_action(workspace, request)` (implemented same-section branch-local materialization)
- `bookforge workflow apply-bridge-scene-insertion` (implemented same-section branch-local materialization)
- `insert_bridge_scene_readiness`
- `insert_bridge_scene`
- `insert_scene_card`
- `renumber_or_refmap_section`
- `update_section_scene_sequence`
- `get_scene_sequence_diff`

Design constraints:
- Branch-local first.
- Stable scene refs or explicit ref-map required.
- Downstream continuity impact report required before promotion.
- Section/chapter macros may recommend insertion, but the author agent chooses.

Definition of done:
- Author can plan/propose a bridge scene in a branch without rerunning the full book. (implemented baseline)
- Author can insert a same-section bridge scene in a branch without rerunning the full book. (implemented baseline)
- Reader and outline projections show inserted scene as provisional.
- Promotion validates sequence, handoffs, and downstream refs. (future broader validation hardening)

## Slice 8: Author Assets API
Priority: `P1/P2`

Purpose:
- Let Nanda create/refine/select authors through BookForge-owned assets.

BookForge surfaces:
- `list_authors`
- `get_author_profile`
- `create_author`
- `refine_author`
- `preview_author_profile`
- `list_author_versions`
- `select_author_version`
- `rollback_author_version`
- `set_active_author_for_book`

Required fields:
- author slug
- display name
- version
- status
- source prompt/context refs
- produced artifact refs
- approval requirement for overwrites/rollback

Definition of done:
- Nanda stops writing or inferring author files directly.
- Author-only chat can use BookForge author truth.
- Refinement is unavailable with receipt until wired.

## Slice 9: Book Intent, Synopsis, And Creation Seed
Priority: `P2`
Status: `initial BookIntent/create-book bridge implemented`

Purpose:
- Give Nanda a canonical way to ask "what is this book supposed to be?" before reading all outline/prose.

BookForge surfaces:
- `list_book_intents`
- `get_book_intent`
- `get_book_synopsis`
- `draft_book_intent` (implemented)
- `approve_book_intent` (implemented)
- `update_book_constraints`
- `create_book_from_intent` (implemented)

Fields:
- short synopsis
- long synopsis
- genre/tone promise
- reader promise
- central conflict
- themes/motifs
- must-have constraints
- must-not constraints
- status: user-approved / author-drafted / generated-from-state / provisional
- source/revision

Definition of done:
- Nanda Book Detail can show intent/synopsis with status.
- Generated intent is context only until approved.
- Approved intent can influence outline/write planning.

## Slice 10: Deep State, Inventory, Appearance, And Setting Layers
Priority: `P1/P2`

Purpose:
- Expand projection layers without creating separate truth systems.

BookForge surfaces:
- `get_scene_context_projection`
- `list_appearance_projection_views`
- `get_scene_setting_projection`
- `get_inventory_projection`
- `get_deep_state_projection`
- `refresh_character_appearance_projection`
- `draft_scene_setting_projection`
- `extract_scene_setting_from_prose`
- future `extract_inventory_from_prose`
- future `refresh_deep_state_projection`

Rules:
- All layers share `ScopeSelector` and `TimelineNodeRef`.
- Derived/extracted surfaces are not authoritative state unless promoted by a specific action.
- Thought signatures can refine context selection but never replace receipts.

Definition of done:
- Nanda can query scene context without scanning prose.
- Appearance/setting bugs are visible as staleness or missing projection, not hidden prompt drift.
- Inventory/state layers can be added without changing the capability model.

## Slice 11: Manuscript Output, Quality Gates, And Export
Priority: `P2`

Purpose:
- Turn written books into readable, reviewable outputs with quality gates before export.

BookForge surfaces:
- `compile_manuscript_preview`
- `get_chapter_completeness`
- `get_word_count_report`
- `run_repetition_similarity_gate`
- `run_banned_phrase_gate`
- `run_preview_gate`
- `export_manuscript`

Definition of done:
- Nanda can show readable book/chapter status.
- Export is blocked by explicit quality gates, not missing files.
- Quality gate receipts are diagnostic or blocking with clear remediation actions.

## Slice 12: Series Continuity Rollups
Priority: `P3`

Purpose:
- Make multi-book workflows real after single-book completion is stable.

BookForge surfaces:
- `get_series_summary`
- `rollup_book_end_state`
- `merge_cross_book_state`
- `get_series_continuity_pack`
- `validate_series_transition`

Definition of done:
- Book-end facts become series-level inputs.
- Cross-book state is explicit and queryable.
- Nanda can discuss series continuity without reading every prior book.

## Slice 13: Prompt/Thought Context Observability
Priority: `P2`

Purpose:
- Preserve the useful thought-signature lens/probe work while keeping it separate from execution truth.

BookForge surfaces:
- `get_thought_context_projection`
- `list_thought_signatures`
- `run_thought_probe_suite`
- `compare_thought_probe_outputs`

Rules:
- Probe outputs are diagnostic/contextual.
- Execution receipts remain authoritative for what happened.
- T1 thought signatures may be used as refinement context for T2 only when the request/receipt records the source signature.

Definition of done:
- Nanda can show thought-signature context as "context reuse" not "proof."
- Probe reports can be attached to author planning without contaminating action receipts.

## Recommended Successor Order
1. `bookforge-action-skill-projection-for-nanda`
2. `bookforge-manuscript-output-and-reader-quality-gates`
3. `bookforge-branch-timeline-explorer`
4. `bookforge-branch-local-authoring-actions`
5. `bookforge-lint-repair-routing-and-seam-alignment`
6. `bookforge-author-assets-api`
7. `bookforge-book-intent-and-synopsis-surface`
8. `bookforge-deep-state-inventory-projections`
9. `bookforge-series-continuity-rollups`

This order keeps Nanda honest first, then makes the reader and branch surfaces usable, then expands authoring and repair power.
