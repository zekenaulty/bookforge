# End-To-End Agentic Authoring Command Graph

Date: 2026-04-30
Scope: BookForge command/capability graph as consumed by Nanda author chat

This artifact is a reference graph for taking a book from author-only ideation to completed manuscript state through Nanda's agentic chat. It is also a command-surface gap check. It should be read as a graph of legal moves, not as one hidden macro.

## Sources Checked

- BookForge static capability projection: `bookforge.query.capabilities:get_capability_projection`
- BookForge selected-scope legal actions: `bookforge.query.actions:list_execution_options`
- BookForge writing surfaces: `get_writing_bootstrap_status`, `get_next_writing_target`, `get_writing_gate_status`, `get_author_loop_envelopes`
- BookForge scene continuation: `bookforge.execution.scene_sequence:continue_scene`
- Nanda bridge status: `nanda.bridge.bookforge.action_registry`
- Nanda route/scope capability projection: `nanda.author.scope_capabilities`
- Nanda agentic turn contracts: `ActionGrammar`, `ProposedActionPlan`, validation, job receipts
- Nanda AuthorWorkLoop: `nanda.jobs.author_work_loop:run_author_work_loop`
- Nanda capability xref: `resources/plans/Drafts/nanda-author-start-authoring/artifacts/capability-xref.md`

Current projection summary:

- Total BookForge projected capabilities: 96
- Actions: 29
- Promotions: 3
- Macros: 4
- Queries: 42
- Readiness surfaces: 6
- Explicit designed gaps: 4
- Implemented BookForge actions stuck in Nanda `needs_bridge`: none found
- Intentionally withheld in Nanda: `apply_scene_commit`, `resume_paused_section`

## Legend

- `[Q]` query/readiness only
- `[I]` implemented command/action
- `[G]` approval-gated command/action
- `[B]` branch-only or non-main branch required
- `[M]` broad macro; not a default adaptive authoring move
- `[W]` withheld from direct Nanda author execution
- `[Gap]` missing or not productized as a reliable command surface
- `-> refresh` means Nanda must re-query BookForge truth before selecting the next action

## Turn-Level Execution Contract

Every agentic chat turn should use this envelope:

```text
User message
  -> Nanda loads context:
       [Q] capability projection
       [Q] selected scope capability projection
       [Q] legal actions / readiness / branch detail / reader anchors as needed
       [Q] active jobs and prior receipts
  -> Nanda builds ActionGrammar from current scoped truth
  -> Author LLM proposes at most one ProposedActionPlan, or null
  -> Nanda validates:
       mode policy
       selected scope
       bridge status
       legal/readiness evidence
       approval class
       freshness / stale branch / expected node
       idempotency / duplicate protection
  -> If approval needed:
       emit approval card / ApprovalRecord candidate
       do not execute unless approved by policy or user
  -> Nanda queues job or calls bridge
  -> BookForge executes or refuses
  -> BookForge emits receipt/artifacts
  -> Nanda emits outcome capsule
  -> refresh before any output-dependent next step
```

Hard invariant:

```text
model proposes -> Nanda validates -> BookForge executes/refuses -> receipts define truth
```

No author-facing prose is execution. No capability projection is readiness. No branch-local receipt is canonical promotion.

## Full Book Authoring Graph

```text
ROOT: Start or continue a book through Nanda author chat
|
+-- 0. Choose or create author identity
|   |
|   +-- [Q] list/get author profile
|   +-- [G][I] create_author
|   |       writes versioned author library artifacts
|   |       canonical author-library mutation
|   |       -> refresh author library
|   |
|   +-- [G][I] refine_author
|   |       creates new author version
|   |       -> refresh author profile/version list
|   |
|   +-- [Gap] select_author_version_for_book / rollback / compare
|           BookForge has create/refine surfaces, but version selection/rollback
|           for a book is still a follow-on author-assets surface.
|
+-- 1. Author-only ideation and BookIntent
|   |
|   +-- [I] draft_book_intent
|   |       from Nanda book seed / author-only chat
|   |       creates provisional BookIntent, not a book workspace
|   |       -> refresh BookIntent list/detail
|   |
|   +-- [G][I] approve_book_intent
|   |       approves seed/title/author/genre/intent as source for book creation
|   |       canonical BookIntent approval
|   |       -> refresh BookIntent detail
|   |
|   +-- [G][I] create_book_from_intent
|           creates canonical BookForge book workspace
|           writes book.json, book_intent.json, context, system prompt
|           -> refresh book library and book detail
|
+-- 2. Create starter outline shape
|   |
|   +-- [G][I] draft_starter_outline_from_intent
|   |       provider-backed, exactly one outline-provider call per request
|   |       creates thin/starter outline run artifacts
|   |       writes immutable outline run + pipeline_latest pointer
|   |       does NOT initialize workflow
|   |       does NOT freeze a section
|   |       does NOT create a branch
|   |       does NOT write prose
|   |       next recommended: initialize_section_workflow
|   |       -> refresh outline lineage / writing bootstrap
|   |
|   +-- [Gap] full deep-outline pipeline as agentic chat skill
|           reserved or successor surface; do not fake it from starter outline.
|
+-- 3. Materialize first writable section
|   |
|   +-- [G][I] initialize_section_workflow
|   |       canonical setup from immutable outline run
|   |       no provider call
|   |       no prose write
|   |       no branch creation
|   |       next recommended: freeze_section_from_phase03_artifact
|   |       -> refresh legal actions / writing bootstrap
|   |
|   +-- [G][I] freeze_section_from_phase03_artifact
|   |       freezes exactly one chapter/section from phase03 artifact
|   |       no provider call
|   |       no prose write
|   |       no branch creation
|   |       next recommended: create_branch
|   |       -> refresh legal actions / writing bootstrap
|   |
|   +-- [Q] get_writing_bootstrap_status
|           reports current missing stage and recommended action:
|           create_book_from_intent
|           draft_starter_outline_from_intent
|           initialize_section_workflow
|           freeze_section_from_phase03_artifact
|           create_branch
|           continue_scene
|
+-- 4. Create isolated writing branch
|   |
|   +-- [I] create_branch / Nanda create_rerun_branch alias
|   |       derived branch from current main scope
|   |       no canonical mutation
|   |       -> refresh branch inventory/detail
|   |
|   +-- [Q] branch_inventory / branch_detail / branch_artifact_index / branch_diff_summary
|   +-- [Q] get_next_writing_target
|   +-- [Q] get_writing_gate_status
|   +-- [Q] get_author_loop_envelopes
|
+-- 5. Branch-local scene writing loop
|   |
|   +-- LOOP: while branch has a legal next writing target
|       |
|       +-- [Q] branch_detail legal actions
|       +-- [Q] scene_phase_readiness
|       +-- [Q] next_writing_target
|       +-- [Q] writing_gate_status
|       |
|       +-- if one scene step is ready:
|       |   |
|       |   +-- [B][I] continue_scene
|       |       executes exactly one recommended child action
|       |       returns author_loop_step_receipt_v1
|       |       canonical_changed must be false on derived branches
|       |       -> refresh
|       |
|       +-- continue_scene child graph:
|           |
|           +-- [B][I] plan_scene
|           |       scene plan artifact
|           |
|           +-- [B][I] preflight_scene_state
|           |       scene input/state preflight
|           |
|           +-- [Q/I] generate_continuity_pack
|           |       diagnostic/derived continuity context
|           |
|           +-- [B][I] write_scene_prose
|           |       provisional scene prose
|           |
|           +-- [B][I] state_repair_scene_patch
|           |       branch-local/provisional state patch
|           |
|           +-- [Q/I] lint_scene_prose
|           |       diagnostic lint result
|           |
|           +-- [B][I] repair_scene_prose
|           |       only when lint/readiness says repair is next
|           |
|           +-- [W] apply_scene_commit
|                   direct Nanda exposure is withheld
|                   allowed only as internal BookForge child of continue_scene
|                   commits scene artifacts to the branch, not canonical main
|                   continue_scene reports completed_scope and parent loop refreshes
|
+-- 6. Parent author loop convenience
|   |
|   +-- [B][I] Nanda author_work_loop
|       parent orchestration, not a BookForge engine action
|       repeats bounded continue_scene calls
|       default/current safe primitive: one child at a time
|       stops on:
|         user_cancel_requested
|         time_budget_reached
|         max_steps_reached
|         no_legal_action
|         child_action_refused
|         child_action_failed
|         completed_scope
|         book_complete
|         canonical_changed_detected
|       refreshes between output-dependent steps
|
+-- 7. Section/chapter shaping moves on branch
|   |
|   +-- [B][I] align_scene_pair_seam
|   |       branch-local adjacent scene seam refinement
|   |       no canonical mutation
|   |       -> refresh seam detail / branch diff
|   |
|   +-- [B][I] plan_bridge_scene_insertion
|   |       proposal only
|   |       does not modify outline/prose
|   |       follow-up: apply_bridge_scene_insertion
|   |       -> refresh branch artifacts
|   |
|   +-- [B][I] apply_bridge_scene_insertion
|   |       same-section first slice only
|   |       branch-local outline/snapshot shift
|   |       does NOT write bridge prose
|   |       recommended next: plan_scene / continue_scene for inserted scene
|   |       -> refresh branch detail/artifacts/diff/writing target
|   |
|   +-- [B][I] lock_section_from_written_state
|   |       branch-local when branch_id is derived
|   |       canonical only on main; Nanda should use branch-local path
|   |       requires completed scene artifacts
|   |       -> refresh writing gates
|   |
|   +-- [B][I] finalize_chapter_from_locked_sections
|           branch-local when branch_id is derived
|           internal pairwise seam repair/chapter seam audit
|           -> refresh chapter/branch state
|
+-- 8. Broad section macro escape hatch
|   |
|   +-- [G][M][I] write_frozen_section
|       broad section_write macro around run_section_range
|       may plan/write/repair/lint/commit every missing scene in selected section
|       must not be the default single-scene action
|       use only when the author/operator explicitly asks for section-level macro work
|       Nanda refuses main branch and force outline-gate bypass
|
+-- 9. Branch review and promotion
|   |
|   +-- [Q] branch diff / reader / artifacts / integrity / semantic review as needed
|   |
|   +-- [G][I] promote_branch_to_main
|       requires derived branch and promotion-ready lifecycle
|       canonical mutation
|       should require explicit approval and validation evidence
|       -> refresh canonical reader, branch inventory, integrity
|
+-- 10. Repeat over sections and chapters
|   |
|   +-- [Q] get_next_writing_target
|   +-- [Q] get_writing_gate_status
|   +-- [I/G] freeze next section as needed
|   +-- [I] create branch for next scoped work
|   +-- [B][I] continue_scene / author_work_loop
|   +-- [B][I] lock section
|   +-- [B][I] finalize chapter
|   +-- [G][I] promote validated branch
|
+-- 11. Complete book and output
    |
    +-- [Q] get_writing_gate_status can report book-complete style states
    +-- [Q] canonical reader surfaces can show book/chapter/section/scene prose
    +-- [Gap] compile/export/reader quality gate surface
            projected gap: gap.compile_export_quality
            no agent should claim final export/publish readiness yet
```

## Optional Side Lanes

### Visual Assets

```text
[Q] visual_provider_descriptors
[Q] visual_action_readiness
[I] plan_visual_asset
    creates provisional prompt plan
    default provider model: nano-banana
    options include gpt-image-2, dall-e-3, grok-imagine-image
    -> refresh visual_asset_index
[G][I] generate_visual_asset
    spend/credential/provider gated
    creates provisional visual asset and diagnostic receipt
    -> refresh visual_asset_index/detail
[Gap] reference-image workflows
[Gap] compose visual layers
```

### Character Appearance, Setting, And Context Projections

```text
[I] refresh_character_appearance_projection
[I] draft_scene_setting_projection
[I] extract_scene_setting_from_prose
[Q] appearance_projection_views
[Q] scene_setting_projection
[Q] scene_context_projection
[Q] thought_context_projection
[Gap] deep_state.inventory
```

These are projection layers over the same book/branch/scope coordinate system. They should feed author context and diagnostics, not become separate truth systems.

### Recovery / Veiled Ledger-Style Repair

```text
[Q] integrity_summary
[Q] outline_lineage_audit
[Q] section_lineage_matrix
[Q] stale_outline_artifact_inventory
[Q] outline_repair_candidates
[Q] recovery_anchor_candidates
[Q] recovery_plan_preview
|
+-- [G][I] create_recovery_branch
|       creates isolated recovery branch and records anchor
|       does NOT itself clean polluted data
|       -> refresh recovery branch health
|
+-- branch-local recovery actions:
|   +-- [B][I] quarantine_artifacts
|   +-- [B][I] normalize_outline_scope
|   +-- [B][I] invalidate_scope_outputs
|   +-- [B][I] rebuild_state_scope
|   +-- [B][I] redraft_scope
|   +-- [Q/I] review_recovery_semantics
|   +-- [Q/I] review_downstream_dependencies
|   +-- [B][I] validate_recovery_branch
|
+-- [G][I] promote_recovery_branch
        canonical mutation after validation
        must include recorded removals/quarantine effects
```

Recovery gap to keep visible:

```text
[Gap] outline-delta fragment splitter
      analyze mixed outline fragments
      partition each fragment lineage into N clean branch candidates
      materialize one branch per outline fragment/timeline
      attach related prose/state/character artifacts to each candidate branch
```

The existing recovery primitives can repair a chosen branch path. They do not yet expose a fully automated "split all blended outline timelines into separate branches" graphing tool.

## Parallel / Fork-Group Future Path

```text
[I] create_branch / fork siblings from shared parent
[Q] branch inventory / fork group state
|
+-- sibling branch A: continue_scene / lock / validate
+-- sibling branch B: continue_scene / lock / validate
+-- sibling branch C: continue_scene / lock / validate
|
+-- [G][I] create_assembly_branch
+-- [I] record_assembly_validation
+-- [G][I] promote_branch_to_main
```

This is structurally possible, but Nanda should still use one approved step -> receipt -> refresh for output-dependent work. Parallel execution is safe only when dependencies are independent and merge/promotion is validated after assembly.

## Current Command Surface Gap Check

### Good / Ready For Agentic Graph Traversal

- Book creation from approved intent is real: `draft_book_intent`, `approve_book_intent`, `create_book_from_intent`.
- Starter outline bridge is real and narrow: `draft_starter_outline_from_intent` is provider-backed, one call, no workflow initialization, no freezing, no branch creation, no prose writing.
- Workflow materialization is split correctly: `initialize_section_workflow` and `freeze_section_from_phase03_artifact` are separate approval-gated canonical setup commands.
- Branch-local heartbeat is real: `continue_scene` executes exactly one child action and returns loop-friendly receipts.
- Nanda AuthorWorkLoop is the right current parent loop: bounded, branch-only, refreshes between child steps, preserves completed branch work.
- Same-section bridge insertion is now executable: proposal and apply are separate, branch-local, and apply does not write bridge prose.
- Nanda bridge drift check is clean: no implemented BookForge action is currently stuck in `needs_bridge`.

### Intentionally Withheld

- `apply_scene_commit` is withheld from direct Nanda execution. It is allowed only as an internal child of `continue_scene` until direct commit semantics are proven safe in receipts.
- `resume_paused_section` is withheld from Nanda. It is a canonical writer macro and needs explicit provider/canonical approval semantics plus refreshed pause-marker handoff.

### Broad Macro Risk

- `write_frozen_section` exists and is bridged, but it is a broad section macro:
  - may execute multiple scene-phase children
  - may write every missing scene in the selected frozen section
  - is approval-gated with `approval_class=section_macro`
  - should not be selected for "write one scene" or "outline one scene"
  - should not be the first AuthorWorkLoop primitive

### Remaining High-Value Gaps

1. `[Gap] compile/export/reader quality gates`
   - BookForge projects this as `gap.compile_export_quality`.
   - Existing reader queries are enough to inspect prose; they are not final manuscript export.

2. `[Gap] whole-book autonomous author loop`
   - Current safe loop is bounded `continue_scene` on a non-main branch.
   - Section/chapter/book envelopes should remain graph traversal over gates, not a hidden mega-run.

3. `[Gap] selected prose -> action handoff`
   - Reader anchors exist.
   - "Fix this passage" still needs structured handoff into ActionGrammar with mutation-safe anchor validation.

4. `[Gap] outline-delta fragment splitter`
   - Needed for fully separating blended outline timelines into N clean branch candidates.
   - Current recovery can normalize a chosen recovery branch but does not automatically partition all timelines.

5. `[Gap] author asset version selection`
   - Create/refine exist.
   - Select active author version for a book, compare, rollback, and assign-to-book remain follow-on surfaces.

6. `[Gap] deep state / inventory`
   - Projected as `gap.deep_state.inventory`.
   - Needed for RPG/system-heavy books and smart downstream weaving.

7. `[Gap] visual reference/layer composition`
   - Basic prompt plan and generation exist.
   - Reference image workflows and layer composition remain designed gaps.

8. `[Risk] Nanda local phrase helper convergence`
   - Nanda has mostly moved to ActionGrammar/ProposedActionPlan.
   - Some branch-scene candidate helpers still map phrases to candidate handles before validation.
   - This is less dangerous than raw execution because route/scope validation gates it, but the final model should keep LLM proposal as the intent source.

9. `[Risk] batch continuation`
   - Whole-batch approve/pause/resume is not fully productized.
   - Output-dependent chains must stay one approved step -> receipt/job state -> refresh -> next author-selected step.

## Agent Reference Rules

1. To start a book, use BookIntent first. Do not create a book workspace from chat prose directly.
2. To create initial outline shape, use `draft_starter_outline_from_intent`. Do not call a full outline pipeline unless that specific capability exists and is selected.
3. To prepare writing, run `initialize_section_workflow`, then `freeze_section_from_phase03_artifact`, then create/select a non-main branch.
4. To write adaptively, prefer `continue_scene` or bounded `author_work_loop`.
5. To do one scene, never choose `write_frozen_section`.
6. To do section macro work, use `write_frozen_section` only with explicit section-macro approval and clear user intent.
7. To add a bridge scene, plan it first, apply the insertion second, then write the inserted scene through `continue_scene`.
8. To finish sections/chapters, lock/finalize on the branch, validate, then promote separately.
9. To repair polluted timeline state, diagnose first, create a recovery branch second, execute recovery primitives third, validate before promotion.
10. To claim completion, cite receipts. To claim canonical change, cite promotion/canonical receipts. To claim final manuscript export, wait for the export/quality-gate surface.

