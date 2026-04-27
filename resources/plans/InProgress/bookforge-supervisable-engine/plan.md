# BookForge Supervisable Engine

Status: In Progress
Stage: InProgress
Owner: BookForge engine workstream
Last Updated: 2026-04-26

## Objective
- Make BookForge truthful and supervisable by Nanda without moving prose generation or canonical state mutation out of BookForge.
- Convert the current section workflow, write loop, lint/repair loop, recovery paths, and future fan-out/fan-in work into explicit engine-owned contracts that can be queried, verified, resumed, and isolated safely.
- Evolve the current command-shaped workflow wrappers toward a smaller engine execution surface that Nanda can compose as author-directed paths without forcing orchestration logic to live in CLI-only flows.

## Why Now
- The section workflow is now real, but the runtime still blurs thin outline, deep outline, section-local work, and recovery import in ways that allow scope drift.
- `veiled_ledger_b1` exposed the exact failure class this plan needs to prevent: a valid engine continuing against mixed lineage and overscoped recovery artifacts.
- Nanda planning has stabilized enough that the shared boundary is now clear: BookForge must emit truthful scope, lineage, pause, and result surfaces instead of forcing the operator layer to infer them from raw files.
- The next architectural pressure is not just safer reruns. It is safe concurrency. If the contract model cannot distinguish canonical state, isolated rerun branches, and future parallel section branches, the same chimera class will return under a different name.
- The next pressure after truthful supervision is controllable composition. Nanda will eventually need to steer outlining, writing, linting, and repair as smaller author moves instead of only invoking large fixed command chains.
- The next pressure after the first execution-surface extraction is segmented write control. Nanda will need truthful scene-phase actions such as "prepare", "write prose", "lint", and "repair" instead of only section-level macros and hidden `run_loop` choreography.
- The next pressure on the Nanda side is author-surface honesty. The author pane can keep voice, but it cannot claim tools or live state it does not actually receive through BookForge query and execution contracts.
- The next projection-layer pressure is appearance and setting truth. Character appearance, scene background/setting, and prior-stage planning context must become queryable surfaces instead of hidden prompt side effects.
- The next execution-root pressure after `0070` is isolated authoring. The engine needs real branch-scoped write roots so old-scene rewrites and recon work can happen off `main`.
- The next lifecycle pressure after branch-scoped writing is parent-target merge discipline. Scene, section, and chapter branches must be able to promote upward, rebase against newer parent snapshots, and eventually support truthful parallel sibling write work.
- The next safety pressure after branch-scoped authoring is localized lineage diagnosis. `chimera_risk` is not operational enough by itself; Nanda needs section-level evidence, artifact-family disagreement, and safe recovery candidates before it can supervise contaminated books without relying on the human operator as the safety catch.
- The next recovery pressure after lineage diagnosis is author-operable mutation. BookForge should provide timeline-safe primitives, while Nanda produces impact reports, strategy, sequencing, and approval flow. The engine should not need a bespoke `fix_veiled_ledger_chimera` command, but it must expose enough scoped tools to quarantine bad artifacts, normalize a chosen timeline, invalidate impacted outputs, rebuild state, redraft affected prose, validate, and promote with removals.
- The current repo already has the right raw materials:
  - section workflow lifecycle
  - immutable outline run artifacts
  - frozen chapter projections
  - writer-side progress files
  - thought signatures
  - chapter seam audit/finalization work
- What is missing is contract discipline, not more hidden execution.

## Grounding
- `resources/plans/proposed/outline_section_chunked_pipeline_plan_20260413_1120.md`
- `docs/help/workflow.md`
- `docs/help/outline_generate.md`
- `docs/help/run.md`
- `docs/help/index.md`
- `src/bookforge/cli.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/runner.py`
- `src/bookforge/workspace.py`
- `src/bookforge/pipeline/phase_history.py`
- `src/bookforge/pipeline/run_logging.py`
- `src/bookforge/pipeline/chapter_seam.py`
- `src/bookforge/llm/logging.py`
- `src/bookforge/llm/thoughts.py`
- `tests/test_section_workflow.py`
- `tests/test_runner_targeting.py`
- `tests/test_runner_outline_gate.py`
- `tests/test_workspace_init.py`
- Cross-plan input:
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\bookforge-supervisable-engine\bookforge-supervisable-engine.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\plans\Drafts\nanda-pre-bookforge-foundation\nanda-pre-bookforge-foundation.md`
  - `C:\Users\Zythis\source\repos\nanda\resources\ai-reports\nanda-design-report-v2-shareable.md`

## Core Model
### Book-Rooted Contracts
- `StateSurface` and `IssueTicket` are book-rooted contracts.
- The public mental model is one tree per book, projected downward through narrowing selectors such as chapter, section, scene, branch, and workflow family.
- `state_surface(book)` returns the full observable picture for the book.
- `state_surface(book, chapter=3, section=2)` returns a projection through a lens over the same rooted truth model.
- The public contract is not "many tiny section surfaces aggregated upward." Storage may normalize internally, but the caller-visible contract stays book-rooted.

### Artifact Status And Projection Layers
- Every execution-produced artifact must declare one artifact status:
  - `authoritative`
  - `provisional`
  - `derived`
  - `diagnostic`
- Meanings:
  - `authoritative`: canonical truth that downstream execution may safely consume without additional promotion
  - `provisional`: produced by execution but not yet validated or promoted; may be resumable or replaceable
  - `derived`: computed projection from other truth-bearing artifacts; useful, but not independently canonical
  - `diagnostic`: observability or debugging material only; never an execution prerequisite by itself
- Query surfaces must report artifact status so callers do not have to infer whether a file is safe to build on.
- Future state families such as:
  - scene/workflow state
  - character appearance state
  - deep inventory or durable state
  - continuity and seam state
  - thought-signature and prompt-package state
  - character appearance projection state
  - scene background and setting projection state
  are projection layers over the same book-rooted coordinate system, not separate truth systems.
- All projection layers must stay addressable by the same `TimelineNodeRef` and `ScopeSelector` vocabulary.

### Lineage Audit Surfaces
- Integrity verdicts must be actionable, not only global.
- When BookForge detects mixed lineage, overscoped recovery, stale section drafts, or mutable-source materialization, it must expose enough structured evidence for Nanda to answer:
  - which chapter/section scopes are affected
  - which artifact families disagree
  - where the first technical divergence starts
  - where the first reader-visible story splice appears if detectable from structured artifacts
  - which candidate source lineages are coherent enough to inspect
  - which repair actions are blocked until a human chooses a recovery anchor
- The first lineage-audit surface is read-only.
- Repair mutation must remain a later explicit action with branch isolation, receipts, backup/quarantine semantics, and validation gates.
- Until a lineage matrix exists for a contaminated book, Nanda may report the global risk and missing evidence, but it must not claim exact repair scope.

### Author-Operable Timeline Recovery And Story Weaving
- BookForge provides timeline-safe primitives.
- Nanda provides author-level diagnosis, strategy, sequencing, approval flow, and user-facing explanation.
- The missing Nanda object is `book_timeline_impact_report_v1`.
- `book_timeline_impact_report_v1` is Nanda-owned, but BookForge must expose enough query and mutation surfaces for Nanda to populate and execute it truthfully.
- The impact report should include:
  - `cause_hypothesis`
  - `affected_scopes`
  - `downstream_scopes`
  - `artifact_impacts`
  - `canonical_conflicts`
  - `salvage_candidates`
  - `repair_strategy_options`
  - `recommended_plan`
  - `human_decisions_required`
  - `validation_gates`
- BookForge mutation primitives should be reusable for both disaster recovery and normal authoring work:
  - contaminated outline recovery
  - upstream scene or chapter retcon
  - downstream continuity reweaving
  - alternate branch comparison
  - scoped redrafting
  - prose salvage as non-canonical reference
- In this plan, "repair" means restoring a coherent book timeline, not merely patching prose.
- A completed timeline repair means:
  - only the selected correct outline lineage remains active in canonical outline artifacts
  - invalid outline artifacts are removed from active discovery paths or quarantined with receipts
  - invalid series, continuity, character, inventory, setting, summary, index, and projection data no longer appear in canonical book datasets
  - impacted prose is invalidated and redrafted from the selected timeline
  - final promotion to `main` includes additions, replacements, removals, and quarantine receipts
  - BookForge no longer reports `chimera_risk`
  - previously blocked actions become available again through legal-action and readiness surfaces
- Salvage is separate from canonical truth.
  - Contaminated prose may be referenced as inspiration only when explicitly selected.
  - Salvage material must not silently feed continuity, state, outline, or downstream prose as authoritative input.
- Healthy timeline and good story are separate gates.
  - Integrity validation can pass while seam repair, style polish, or author revision still remain.

### TimelineNodeRef
- Every execution point gets a coordinate.
- A coordinate is the thing that answers:
  - where am I
  - what produced this
  - what scope is active
  - what branch am I on
- Every `StateSurface`, `IssueTicket`, `ExecutionRequest`, and `ExecutionResult` carries a `TimelineNodeRef`.
- `revision_id` is monotonic on node transitions within a branch. It is not a counter for arbitrary surface emission.

```python
@dataclass
class TimelineNodeRef:
    book_id: str
    workflow_family: str
    source_run_id: str
    branch_id: str
    fork_group_id: str | None
    chapter: int | None
    section: int | None
    scene: int | None
    phase_id: str | None
    turn_id: str | None
    revision_id: str
```

### ScopeSelector
- `ScopeSelector` is the observer-facing selector that narrows the book-rooted contracts and resolves to a current `TimelineNodeRef`.
- A selector may address canonical or derived work explicitly.
- At minimum it must support:
  - `book_id`
  - optional `branch_id`
  - optional `fork_group_id`
  - optional `chapter`
  - optional `section`
  - optional `scene`
  - optional `phase_id`
  - optional `turn_id`

### Branches And Fork Groups
- Canonical book state lives on `branch_id="main"`.
- Any rerun, repair attempt, or scoped re-execution runs on a derived branch unless the supported command explicitly says it is a main-branch action.
- Every branch declares its parent `TimelineNodeRef` at creation.
- Every branch needs its own current-node pointer or branch manifest so pause/resume is unambiguous off `main`.
- No branch mutates canonical state directly.
- Promotion from branch to `main` requires explicit reconciliation and integrity validation.
- Discarded branches leave canonical state untouched.
- Parallel siblings share a `fork_group_id` and the same parent node.
- A fork group keeps a frozen parent snapshot for the life of that group.
- Sibling branches may read from their declared parent and pre-fork canonical state, but not from one another during execution.
- If `main` advances incompatibly while a fork group is alive, assembly must refuse until the group is explicitly rebased, discarded, or recreated from a new parent node.
- Single-branch promotion and multi-branch assembly are distinct merge operations and must remain distinct in both code and docs.
- Assembly does not create provisional canonical state on `main`.
- Assembly happens on a dedicated assembly branch derived from the shared parent or fork group. Seam audit and seam-local repair run there. Only validated promotion writes the assembled result to `main`.

### Observer / Engine Bridge
- Nanda thinks in observer-scope terms such as:
  - resume the paused section in chapter 3
  - investigate continuity risk in chapter 5
- BookForge executes in engine-scope terms such as:
  - workflow family
  - source lineage
  - writable scope
  - phase boundary
- The shared bridge is:
  - `ScopeSelector -> TimelineNodeRef -> ForgeExecutionTarget`
  - `ForgeExecutionResult -> StateSurface + IssueTicket + ObserverView`
- Neither side should internalize the other's private addressing model. They share the coordinate system and the contract objects.
- `ObserverView` is a Nanda-side projection, not a BookForge-owned shared contract object.

### Execution Surface Evolution
- The current CLI commands are transitional workflow wrappers, not the long-term orchestration boundary.
- The long-term stable seam is a smaller engine action surface that exposes:
  - narrowly scoped executable actions
  - branch policy and lineage requirements per action
  - receipts and reconciliation output per action
  - legal next actions from the current node
- That execution surface must also expose readiness and artifact truth, not just executability.
- `legal_next_actions(...)` answers what the engine allows.
- Readiness surfaces answer what is actually possible right now, including:
  - missing prerequisites
  - available inputs
  - already-produced outputs
  - whether the action would mutate canonical or only provisional state
  - the recommended next action from the current node
- Nanda should eventually be able to run BookForge as a choose-your-own-adventure author loop:
  - observe current node and integrity
  - ask BookForge what actions are legal next
  - choose one narrow action
  - inspect the resulting receipt
  - continue without depending on a monolithic command path
- The important boundary rule does not change:
  - BookForge still owns prose generation and canonical state mutation
  - Nanda chooses among legal engine actions and evaluates the outcomes
- For the author-pane path, this means:
  - BookForge must expose truthful capability and readiness surfaces for scene-phase actions
  - Nanda must assemble structured worker prompt packages from those truthful surfaces instead of improvising capability claims in persona text
- This means the medium-term API shape is:
  - query surfaces for truth and legal-next-action discovery
  - query surfaces for readiness and produced-artifact truth
  - execution actions for narrow engine moves
  - macro workflow commands as wrappers over those same actions, not a separate logic layer
  - scene-phase readiness and result surfaces so the write loop can be traversed as a graph instead of only resumed as a batch

### Author Capability Grounding
- The Nanda author pane may keep voice and persona framing, but capability claims must come from actual BookForge query and execution surfaces.
- The author surface may not imply that a tool, diagnostic pass, or mutation path exists unless:
  - the corresponding readiness or legal-action surface says it is available
  - and the corresponding BookForge execution path is actually wired
- Thought signatures and persona prompts may enrich context assembly, but they are not proof of execution capability.
- T1 thought signatures from prior workflow stages may be reused as context-management and planning-refinement inputs, but the prompt package and execution receipt must record that use explicitly.
- Execution receipts and readiness/query surfaces remain the authority for what the author pane can honestly claim.

### Result Mapping
| Branch Lifecycle State | Execution Result / Public Status | Canonical Change |
| --- | --- | --- |
| active | `retryable_pause` or in-progress observation | none |
| promote_ready | `promotion_required` | none until validated promotion |
| needs_review | `integrity_degraded` or blocked review state | none |
| discard | `hard_fail`, explicit discard, or abandoned branch | none |
| promoted | `success` | canonical change applied |
| assembled_pending_promotion | `promotion_required` | none until validated promotion |

## Scope
- Freeze BookForge-owned mode vocabulary and lineage rules:
  - `thin_outline`
  - `deep_outline`
  - `section_local_outline`
  - `section_write`
  - `recovery_import`
  - `retryable_pause`
  - `hard_fail`
- Freeze the shared contract vocabulary for:
  - `TimelineNodeRef`
  - `ScopeSelector`
  - `branch_id`
  - `fork_group_id`
  - `promotion`
  - `assembly`
  - `discard`
- Freeze artifact truth vocabulary for:
  - `authoritative`
  - `provisional`
  - `derived`
  - `diagnostic`
- Add a read-only query surface under `src/bookforge/query/`.
- Emit versioned engine contracts:
  - `TimelineNodeRef`
  - `ScopeSelector`
  - `StateSurface`
  - `IssueTicket`
  - `ExecutionRequest`
  - `ExecutionResult`
- Prepare explicit receipt and readiness surfaces so produced artifacts, prerequisites, and recommended next actions are queryable instead of inferred from files alone.
- Add author-operable recovery and story-weaving mutation primitives that can be composed by Nanda:
  - select a recovery anchor
  - create a recovery branch
  - quarantine scoped artifacts
  - normalize outline scope from a selected source lineage
  - invalidate impacted outputs
  - rebuild book state projections for a scope
  - redraft affected scenes, sections, or chapters
  - validate recovery branch health
  - promote cleaned state back to `main` with removals
- Support one truthful main-branch execution path with bounded pause/resume behavior.
- Support isolated branch reruns and fork-group fan-out/fan-in through the same coordinate system and branch invariants.
- Reconcile and validate lineage before returning control to the caller.
- Align help docs and command labels with actual runtime semantics.
- Prepare the runtime for a later action-catalog extraction so outlining, writing, linting, and repair can be composed from smaller API-facing steps.

## Non-Goals
- No Nanda supervisor logic in this repo.
- No React or operator UI work.
- No generic agent framework.
- No rewrite of the entire outline or write pipeline.
- No attempt to build a full generic scheduler for all future branches in the first slice.
- No long-term commitment to CLI commands as the only orchestration surface.
- No silent fallback between workflow families.
- No use of mutable compatibility views such as `outline.json` as implicit canonical lineage anchors when immutable run artifacts exist.
- No duplicate thought-signature lineage system unless existing carry paths prove insufficient.
- No sibling-branch reads during fork-group execution.

## Deliverables
- `src/bookforge/query/__init__.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/characters.py`
- `src/bookforge/query/continuity.py`
- `src/bookforge/contracts/__init__.py`
- `src/bookforge/contracts/branch_manifest.py`
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/scope_selector.py`
- `src/bookforge/contracts/state_surface.py`
- `src/bookforge/contracts/issue_ticket.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- Future or follow-on contract targets:
  - produced-artifact receipt contract
  - scene-phase readiness contract
- `src/bookforge/branching.py`
- Future extraction target:
  - a smaller execution action catalog under `src/bookforge/execution/` or equivalent
- Query and contract tests
- Branching and fork-group tests
- One narrow execution adapter backed by the existing workflow/write surfaces
- Branch-aware reconciliation and promotion helpers
- Help and command-surface updates that tell the truth about scope and recovery

## Plan-Level Definition Of Done
- A caller can query workflow family, run mode, source run, source artifact class, active section, current node, and integrity verdict through stable Python entry points.
- BookForge emits book-rooted `StateSurface` projections and categorized `IssueTicket` output that both carry `TimelineNodeRef` coordinates.
- A caller can tell whether a produced artifact is `authoritative`, `provisional`, `derived`, or `diagnostic` without reverse-engineering file paths or command history.
- `current_node.json` or an equivalent contract-backed pointer identifies the active main-branch node.
- Derived branches have branch-local current-node pointers or manifests so branch pause/resume and verification stay unambiguous.
- Provider exhaustion resolves to `retryable_pause` or `hard_fail`, not multi-hour hidden retries as the only visible behavior.
- One narrow `ExecutionRequest -> ExecutionResult` path works on `main` without a hidden workflow-family switch.
- An isolated branch rerun can execute without mutating canonical state directly.
- Fork-group siblings can be assembled through an explicit assembly branch that runs seam validation before canonical promotion.
- Fork groups refuse unsafe assembly when their frozen parent snapshot no longer matches required canonical preconditions.
- Section materialization can be traced to immutable source runs or frozen chapter projections instead of mutable merged outline views.
- Reconciliation and lineage validation run before control returns to the caller on `main`, and before promotion/assembly returns content to canonical state.
- Help docs stop implying scope that the runtime does not actually execute.
- The plan preserves a path to replace macro command orchestration with smaller API-facing execution actions without changing the shared truth model.
- The plan preserves a path for Nanda to ground author-surface capability claims in actual readiness and receipt data instead of persona-only prompt behavior.
- A contaminated book can be recovered through composable branch-first primitives without direct main mutation or manual filesystem surgery.
- Promotion of a recovery branch removes or quarantines invalid files as well as writing repaired replacements.
- After recovery promotion, lineage, integrity, legal-action, and readiness surfaces agree that the book is no longer blocked by the original timeline contamination.

## Constraints
- BookForge keeps ownership of prose generation and canonical workspace mutation.
- Query modules stay read-only.
- New modules should target roughly `80-250` lines. Split aggressively at `>300`.
- Prefer small typed data objects at the boundary instead of raw dict blobs passed through unrelated modules.
- Do not normalize legacy accidental behavior as a contract just because live workspaces already contain it.
- Every execution-produced artifact must declare its artifact status.
- Thought signatures, prompt packages, and persona context may inform execution and replay, but they may not become the authoritative record of what happened.
- Every non-main branch must declare its parent `TimelineNodeRef`.
- No silent source switching inside a branch.
- No promotion or assembly without explicit reconciliation and integrity validation.
- Parallel siblings may not read one another during execution.
- Fork-group assembly must use the frozen parent snapshot declared at fork time unless an explicit rebase or recreation step occurs.
- Recovery mutation must be branch-first.
- No direct `main` recovery mutation from a contaminated lineage.
- No recovery action may silently choose a source lineage. Anchor selection must be explicit in the request and receipt.
- No recovery promotion may leave invalid artifacts in active canonical discovery paths.
- Nanda may plan, sequence, and request actions, but BookForge enforces preconditions, scope, receipts, rollback/quarantine, validation, and promotion safety.
- Existing working-tree changes outside this plan scope are not part of this draft and must remain untouched.

## Dependencies
- The section-chunked workflow remains the primary runtime spine.
- Current chapter seam audit/finalization work remains a dependency, not a replacement for these contracts.
- The Nanda operator plan depends on this plan's steps `0010-0045`.
- The future Nanda author-loop work depends on a later extraction step that turns the workflow wrappers into a smaller choose-your-own-adventure execution surface.
- The future Nanda author-pane work depends on BookForge exposing scene-phase capability/readiness receipts so persona responses can stay grounded in actual callable actions.

## Step Outline
- See `steps/index.md` and the numbered step folders for execution-shaped stories.
