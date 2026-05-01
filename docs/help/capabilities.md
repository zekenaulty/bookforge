# bookforge capabilities

Purpose
- Emit BookForge engine capability truth for Nanda, agents, and tool consumers.
- This command is static capability projection, not dynamic readiness.
- Use it to discover what BookForge knows how to do, which selector shape an action expects, what mutation class it has, what receipt type it returns, and whether the surface is implemented or only a designed gap.

Usage
- `bookforge capabilities`
- `bookforge capabilities --json`
- `bookforge capabilities --book <id>`
- `bookforge capabilities --book <id> --json`

Static vs dynamic
- `bookforge capabilities --json` says a capability exists and describes its contract.
- `bookforge workflow legal-actions --book <id> ...` says which actions are legal or blocked for one selected scope.
- `bookforge workflow scene-readiness --book <id> --chapter <n> --scene <s>` says whether a specific scene-phase action is ready and why.
- `bookforge workflow next-writing-target --book <id> [--branch-id <id>]` says where the author loop should look next, whether the book is complete, and what gate blocks continuation.
- `bookforge workflow writing-bootstrap --book <id> [--branch-id <id>]` says which setup-to-writing stage is next after BookIntent creation without running providers or mutations.
- `bookforge workflow writing-gates --book <id> [--branch-id <id>]` says which scene/section/chapter/book/export gates are ready or blocked.
- `bookforge visual readiness --book <id> --model <provider> --purpose <purpose> --json` says whether one visual provider/purpose is currently runnable.
- Do not treat capability projection as permission to execute at a specific scope.

Capability descriptor fields
- `capability_id`: stable identifier such as `action.write_scene_prose`.
- `unit_type`: `query`, `readiness`, `primitive_action`, `validation_gate`, `macro_workflow`, `promotion_action`, or `projection_skill`.
- `capability_type`: broad grouping for UI and planner classification.
- `implementation_status`: `implemented`, `designed_gap`, or `documented_exclusion`.
- `action_key` or `query_key`: BookForge key when executable/queryable.
- `supported_scope_kinds`: supported conceptual scope types.
- `required_selector_shape`: selector fields the caller must provide.
- `branch_policy`: `main_only`, `derived_only`, or `any`.
- `mutation_class`: `read_only`, `diagnostic_only`, `provisional_branch_mutation`, `branch_mutation`, `canonical_mutation`, `promotion`, or `assembly`.
- `approval_required`: whether the action should require explicit operator/agent approval.
- `readiness_source`: the query surface that answers current-scope readiness.
- `expected_receipt_type`: expected result shape, usually `execution_result_v1`, `query_result`, or `readiness_result`.
- `process_area`: broad BookForge process area such as `outline`, `writing`, `branching`, `recovery`, `projection_layers`, `reader_output`, `author_assets`, or `book_intent`.
- `produced_artifact_statuses`: expected artifact truth statuses such as `authoritative`, `provisional`, `derived`, or `diagnostic`.
- `child_actions`: macro child actions when known. Macros are optional recipes, not rails.
- `refusal_semantics`: common refusal modes and reason codes.
- `evidence_sources`: module, CLI, or plan references backing the descriptor.

Nanda consumption rule
- BookForge emits engine truth.
- Nanda maps engine truth to UI/agent buckets such as `wired`, `queryable`, `designed`, or `theater`.
- Nanda owns planning, belief state, candidate action comparison, approvals, and author explanation.
- Persona text and thought context are not proof that a capability exists or is ready.
- Nanda can group engine capabilities by `supported_scope_kinds` and `process_area`, then map them to its own UI buckets.

Visual capability bridge
- Visual capabilities use the same split:
  - static descriptor: `action.plan_visual_asset`, `action.generate_visual_asset`, `query.visual_*`, `readiness.visual_action_readiness`
  - dynamic legal action: `list_execution_options(... workflow_family="visual_assets")`
  - dynamic provider readiness: `get_visual_action_readiness(...)`
  - artifact inspection: `get_visual_asset_index(...)`, `get_visual_prompt_plan_detail(...)`, `get_visual_asset_detail(...)`
- `generate_visual_asset` is implemented but approval-gated because it can spend provider credits.
- Generated image artifacts are provisional; manifests and prompt plans are queryable evidence.

Book intent/create-book bridge
- Book creation uses the same capability/readiness split:
  - static descriptors: `action.draft_book_intent`, `action.approve_book_intent`, `action.create_book_from_intent`, `action.draft_starter_outline_from_intent`, `query.book_intents`, `query.book_intent`
  - dynamic legal action: `bookforge workflow legal-actions --book __book_intents__ --workflow-family book_intent --json`
  - execution: `bookforge book intent draft|approve|create`
- `draft_book_intent` formalizes an author-only seed into a provisional `BookIntent`.
- `approve_book_intent` promotes that intent to an authoritative creation source.
- `create_book_from_intent` creates the canonical BookForge book workspace, writes `book.json`, copies `book_intent.json`, writes `draft/context/book_intent.md`, and rebuilds prompts.
- `draft_starter_outline_from_intent` is the next book-scoped action after creation: it calls the outline provider once to author starter/thin outline run artifacts from the created intent, without running the full deep-outline pipeline or writing prose.
- A drafted intent is not a book. A created book requires an execution receipt from `create_book_from_intent`.
- A created book is not yet workflow-ready until a source outline run exists. After `draft_starter_outline_from_intent`, Nanda should call `initialize_section_workflow`, then `freeze_section_from_phase03_artifact`, then branch-local writing actions.
- `query.writing_bootstrap_status` is the read-only bridge after book creation. It reports whether the next setup/writing step is `draft_starter_outline_from_intent`, `initialize_section_workflow`, `freeze_section_from_phase03_artifact`, `create_branch`, or `continue_scene`.

Adaptive authoring
- The capability graph should support choose-your-own-adventure authoring.
- A macro like `write_frozen_section` can expose a default recipe, but the author agent may instead run `write_scene_prose`, inspect the receipt, run lint, branch, repair, insert, or replan.
- `query.book_reader_anchor` is the mutation-safe selected-prose evidence surface. It is read-only, but it proves branch/canonical scope, source hash, span offsets, selected hash, and whether the selected passage is safe to target.
- Scene anchors can feed branch-local authoring tools. Chapter anchors are inspect-only until narrowed to a scene.
- `continue_scene` is the first adaptive writing macro: it executes only the current `ScenePhaseReadiness.recommended_next_action`, returns a wrapper receipt naming the child action, includes a nested `author_loop_step_receipt`, and exposes the updated readiness state for the next decision.
- `query.next_writing_target` is the first loop-friendly writing cursor query: it is read-only and reports current scene, next scene/section/chapter, `book_complete`, `can_continue`, recommended action, and blocked reason.
- `query.writing_bootstrap_status` sits one level earlier than `next_writing_target`: it answers what must be created before a branch-local author loop can start.
- `readiness.writing_gate_status` is the first loop-friendly gate readiness surface: it reports scene, section, chapter, book, and export gates with action/refusal metadata.
- `query.author_loop_envelopes` is the query-only higher-level loop surface. It lets Nanda ask which envelopes such as `continue_one_step`, `continue_scene`, `continue_section`, or `continue_chapter` are currently supportable without starting a long autonomous run.
- `query.chapter_seam_queue` is the read-only chapter-level selector for adjacent scene-pair seam work. It reports ready, blocked, and already aligned pairs so Nanda can choose `align_scene_pair_seam` deliberately instead of inferring from file order.
- `query.scene_pair_seam_detail` is the read-only focused inspector for one adjacent scene-pair seam. It reports pair readiness, report status, issue counts, repair counts, scene artifact refs, and can include the full pair seam report payload.
- `align_scene_pair_seam` is a derived-branch action for adjacent written scenes. It uses the existing LLM seam repair contract to re-author the boundary and emits branch-local reports/artifacts with `canonical_changed: false`.
- `plan_bridge_scene_insertion` is a derived-branch proposal action. It writes provisional bridge-scene planning evidence, but it does not mutate outline order, renumber scenes, or write bridge prose.
- `apply_bridge_scene_insertion` is a derived-branch action that consumes a bridge proposal, inserts a provisional bridge scene into the branch outline sequence, shifts following branch-local integer scene artifacts, and returns control to the normal scene-phase graph for prose.
- `lock_section_from_written_state` is branch-capable: on `main` it is canonical, and on a derived branch it is branch-authoritative with `canonical_changed: false`.
- `finalize_chapter_from_locked_sections` is branch-capable with the same rule: canonical on `main`, branch-authoritative on derived branches.
- `recommended_next_action` is guidance. Legal/readiness surfaces define options, not rails.

Future MCP-style mapping
- `CapabilityDescriptor` can become MCP-style tool metadata.
- Readiness queries can become resource/query surfaces.
- Execution receipts can become tool result schemas.
- Artifact refs and statuses can become resource references.
- BookForge is not implementing an MCP server in this step; the projection is the protocol-neutral source of truth.
