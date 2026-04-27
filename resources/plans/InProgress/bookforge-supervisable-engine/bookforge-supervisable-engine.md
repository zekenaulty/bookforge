# bookforge-supervisable-engine

## Compiled Plan Metadata

- Plan Scope: `InProgress/bookforge-supervisable-engine`
- Compiled At (UTC): `2026-04-27T16:37:20Z`
- Source Document Count: `55`
- Projection File: `bookforge-supervisable-engine.md`

## Contents

1. `plan.md`
2. `decisions/initial-decisions.md`
3. `risks/initial-risks.md`
4. `validation/acceptance.md`
5. `steps/index.md`
6. `steps/0010-freeze-scope-lineage-and-contract-vocabulary/step.md`
7. `steps/0020-add-read-only-query-surface/step.md`
8. `steps/0030-emit-versioned-state-surfaces-and-issue-tickets/step.md`
9. `steps/0040-add-truthful-scoped-execution-and-bounded-resume/step.md`
10. `steps/0045-add-isolated-branch-reruns-and-fork-group-assembly/step.md`
11. `steps/0050-harden-reconciliation-integrity-and-command-surface/step.md`
12. `steps/0060-extract-minimal-engine-execution-surface-for-nanda/step.md`
13. `steps/0070-segment-section-write-into-scoped-scene-actions/step.md`
14. `steps/0071-make-scene-and-section-write-execution-branch-scoped/step.md`
15. `steps/0072-add-parent-target-promotion-rebase-and-parallel-fork-write/step.md`
16. `steps/0075-extract-appearance-setting-and-context-refinement-surfaces/step.md`
17. `steps/0080-add-outline-lineage-audit-and-recovery-briefing/step.md`
18. `steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`
19. `notes/2026-04-21-0010-execution.md`
20. `notes/2026-04-21-0020-execution.md`
21. `notes/2026-04-21-0030-execution.md`
22. `notes/2026-04-21-0040-execution.md`
23. `notes/2026-04-21-0045-execution.md`
24. `notes/2026-04-21-0050-execution.md`
25. `notes/2026-04-22-0050-execution.md`
26. `notes/2026-04-22-0060-execution.md`
27. `notes/2026-04-23-0070-commit-slice.md`
28. `notes/2026-04-23-0070-continuity-pack-slice.md`
29. `notes/2026-04-23-0070-repair-slice.md`
30. `notes/2026-04-23-0070-run-loop-wrapper-slice.md`
31. `notes/2026-04-23-0070-section-wrapper-tightening.md`
32. `notes/2026-04-26-0070-complete.md`
33. `notes/2026-04-26-0071-branch-scoped-writer.md`
34. `notes/2026-04-26-0072-complete.md`
35. `notes/2026-04-26-0072-lifecycle-cli.md`
36. `notes/2026-04-26-0072-nested-branch-primitives.md`
37. `notes/2026-04-26-0072-writer-assembly-staging.md`
38. `notes/2026-04-26-0075-appearance-pending-fix.md`
39. `notes/2026-04-26-0075-complete.md`
40. `notes/2026-04-26-0075-context-receipts.md`
41. `notes/2026-04-26-0075-projection-query-slice.md`
42. `notes/2026-04-26-0075-setting-actions.md`
43. `notes/2026-04-26-0080-complete.md`
44. `notes/2026-04-26-0081-implementation-slice.md`
45. `notes/2026-04-26-0081-planning.md`
46. `notes/2026-04-27-0081-blast-radius-slice.md`
47. `notes/2026-04-27-0081-continuity-validation-slice.md`
48. `notes/2026-04-27-0081-durable-validation-slice.md`
49. `notes/2026-04-27-0081-projection-validation-slice.md`
50. `notes/2026-04-27-0081-promotion-postcondition-slice.md`
51. `notes/2026-04-27-0081-recovery-postconditions-slice.md`
52. `notes/2026-04-27-0081-redraft-scope-slice.md`
53. `notes/2026-04-27-0081-state-rebuild-slice.md`
54. `notes/2026-04-27-0081-state-validation-slice.md`
55. `promotion.md`

---

## Source 1: `plan.md`

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

---

## Source 2: `decisions/initial-decisions.md`

# Initial Decisions

- BookForge remains the only system allowed to generate prose or mutate canonical book state.
- Nanda will consume BookForge truth; it should not have to reverse-engineer hidden runtime mode from raw files forever.
- Thin outline, deep outline, section-local outline, section write, and recovery import are distinct runtime modes and may not silently promote into one another.
- `StateSurface` and `IssueTicket` are book-rooted contracts with narrowing via scope selectors, not scene-level surfaces stitched together after the fact.
- Every emitted contract object carries a `TimelineNodeRef`.
- `revision_id` is node-transition monotonic within a branch, not surface-emission monotonic.
- Immutable outline run artifacts and frozen chapter projections are the preferred lineage anchors.
- Mutable compatibility artifacts such as `outline.json` are never sufficient by themselves to justify scoped materialization.
- Query modules belong under `src/bookforge/query/` and must remain read-only.
- Shared engine contract objects belong under `src/bookforge/contracts/`.
- Canonical state lives on `branch_id="main"`.
- Any rerun or re-execution outside the explicitly supported main-branch path happens on a derived branch with a declared parent node.
- Parallel sibling branches are bound by a shared `fork_group_id`, shared parent lineage, and a hard no-cross-read rule during execution.
- Single-branch promotion and multi-branch assembly are distinct operations and must stay distinct in both code and docs.
- Multi-branch assembly happens on an assembly branch, not on `main`, and only validated promotion writes assembled content back to canonical state.
- Fork groups hold a frozen parent snapshot. If canonical state advances incompatibly, assembly must rebase, recreate, or refuse.
- Derived branches need branch-local current-node pointers or branch manifests; `current_node.json` on `main` is not sufficient once branches exist.
- The first truthful supervised issue class is lineage/integrity conflict, because it is both mechanical and already proven by live failures.
- `ObserverView` belongs to Nanda-side projection work, not to the BookForge-owned shared contract set.
- Existing Gemini `T1 -> T2` carry should be preserved and instrumented lightly; do not build a second thought lineage graph unless evidence demands it.
- Help docs are part of the contract surface. If the docs imply broader scope than the runtime actually executes, that is a defect.
- The current CLI workflows are transitional wrappers. The long-term orchestration seam is a smaller engine action surface that both CLI and Nanda can call.
- Legal next actions should eventually be queryable from current engine truth; Nanda should not have to infer hidden valid transitions from command docs alone.

---

## Source 3: `risks/initial-risks.md`

# Initial Risks

- `src/bookforge/cli.py`, `src/bookforge/section_workflow.py`, and `src/bookforge/runner.py` already carry broad responsibilities and can easily absorb too much more.
- A "scoped" execution adapter may secretly depend on batch assumptions and accidentally normalize a hidden workflow-family switch.
- Query helpers may drift into mutation or implicit repair if the read-only boundary is not enforced.
- Mutable compatibility artifacts may continue to look canonical unless lineage classification is made explicit in both code and docs.
- Provider retry/backoff behavior may remain buried in transport logs if pause state is not elevated into a first-class result surface.
- If `TimelineNodeRef` is under-specified, later branch and assembly features will bolt on incompatible addressing rules and recreate lineage drift in a more formal-looking shape.
- If branch promotion and fork-group assembly are not separated early, future parallel writing work will reuse single-branch promotion logic and silently merge incompatible sibling outputs.
- If sibling branches can read one another during fan-out execution, merge order will become a hidden dependency and parallelism will stop being trustworthy.
- If book-rooted surfaces are implemented as ad hoc aggregation over many tiny artifacts, callers will still be forced to infer canonical truth from storage layout.
- Derived prose features can sprawl into expensive or low-signal machinery if introduced before the state and ticket contracts are stable.
- The repo already contains older and newer planning shapes; without discipline, this plan can become another disconnected artifact instead of the local BookForge source of truth.

---

## Source 4: `validation/acceptance.md`

# Acceptance

This plan is ready for promotion only when the target implementation can satisfy all of the following:

- BookForge exposes workflow, lineage, integrity, and book state through stable read-only query modules.
- BookForge can resolve observer-shaped scope selection into a current `TimelineNodeRef` without hand-reading raw workspace files.
- `ScopeSelector` can explicitly address `main`, a derived branch, or a fork group without relying on inferred scope alone.
- At least one real execution path emits:
  - a book-rooted versioned `StateSurface`
  - categorized `IssueTicket` output
  - a truthful pause/result status
- Every emitted contract object carries a `TimelineNodeRef`.
- One narrow `ExecutionRequest -> ExecutionResult` path can be executed and verified on `main` without hidden scope switching.
- Lineage validation runs before section materialization or resume proceeds.
- Provider exhaustion can be observed as `retryable_pause` or `hard_fail` without reading raw transport logs.
- Branch reruns can execute in isolation without mutating canonical state directly.
- Fork-group assembly and single-branch promotion are explicitly distinct merge operations with validation gates.
- Assembly does not write provisional state to `main` before validation completes.
- Derived branches expose unambiguous current-node state through branch-local pointers or manifests.
- Fork-group assembly refuses when the frozen parent snapshot is no longer valid for safe merge.
- The plan states clearly how branch lifecycle states map to public execution results and canonical-change status.
- Contaminated book recovery is expressed as composable branch-first primitives, not a one-off fixer command.
- Recovery promotion can apply removals/quarantine as well as additions/replacements.
- Nanda can build a `book_timeline_impact_report_v1` from BookForge evidence and then request scoped recovery/story-weaving actions without direct filesystem mutation.
- A recovered book can be verified through query surfaces as no longer blocked by the original lineage or chimera issue.
- Help docs and CLI labels match the actual runtime mode and recovery behavior.
- New code follows the small-file rule and does not normalize `300-600` line modules as acceptable.

---

## Source 5: `steps/index.md`

# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-freeze-scope-lineage-and-contract-vocabulary | completed | - | Freeze runtime vocabulary, coordinate primitives, artifact truth rules, and caller-visible scope semantics. |
| 0020-add-read-only-query-surface | completed | 0010 | Expose workflow, lineage, integrity, character, continuity, and scope-to-node resolution through small query modules. |
| 0030-emit-versioned-state-surfaces-and-issue-tickets | completed | 0010, 0020 | Emit book-rooted state, pause, and issue contracts that carry timeline coordinates. |
| 0040-add-truthful-scoped-execution-and-bounded-resume | completed | 0010, 0020, 0030 | Support one narrow main-branch resume path with expected-node validation and truthful pause reporting. |
| 0045-add-isolated-branch-reruns-and-fork-group-assembly | completed | 0030, 0040 | Add branch isolation, sibling fork groups, promotion vs assembly semantics, and validation-gated merge paths. |
| 0050-harden-reconciliation-integrity-and-command-surface | completed | 0030, 0040, 0045 | Add post-execution and post-promotion reconciliation, stronger integrity helpers, and help-doc coherence. |
| 0060-extract-minimal-engine-execution-surface-for-nanda | completed | 0050 | Replace command-only orchestration with a smaller action catalog and legal-next-action API that Nanda can compose. |
| 0070-segment-section-write-into-scoped-scene-actions | completed | 0060 | Turn the hidden `section_write` batch flow into truthful scene-phase actions and readiness queries that Nanda can traverse as an author skill graph. |
| 0071-make-scene-and-section-write-execution-branch-scoped | completed | 0070 | Move scene and section write execution off `main` into real branch-local execution roots so old-scene rewrites and isolated author work become truthful. |
| 0072-add-parent-target-promotion-rebase-and-parallel-fork-write | completed | 0071 | Let branch work merge upward into parent branches or `main`, add explicit rebase, and support sibling parallel write branches with validation-gated assembly. |
| 0075-extract-appearance-setting-and-context-refinement-surfaces | completed | 0070 | Make character appearance, scene background/setting, and prior-stage T1 thought-signature context explicit queryable projection layers instead of incidental prompt side effects. |
| 0080-add-outline-lineage-audit-and-recovery-briefing | completed | 0020, 0030, 0050, 0060 | Add read-only outline lineage audit, section-level lineage matrix, stale artifact inventory, and recovery candidate briefing so Nanda can localize chimera risks before any repair mutation. |
| 0081-add-author-operable-timeline-recovery-and-story-weaving-primitives | in_progress | 0045, 0070, 0071, 0072, 0075, 0080 | Add branch-first mutation primitives that let Nanda compose timeline recovery, retcon, redraft, and downstream story-weaving plans without BookForge needing bespoke fix commands for every failure class. |

---

## Source 6: `steps/0010-freeze-scope-lineage-and-contract-vocabulary/step.md`

# 0010 Freeze Scope, Lineage, And Contract Vocabulary

Status: completed

## Goal
- Freeze the BookForge-owned runtime vocabulary and coordinate system before more code lands on top of accidental behavior.

## Problem
- Current docs and runtime behavior still permit ambiguous interpretations of:
  - thin outline vs deep outline
  - section-local work vs batch outline
  - same-mode resume vs recovery import
  - immutable lineage anchors vs mutable compatibility views
- The current plan draft also needs explicit names for:
  - `TimelineNodeRef`
  - `ScopeSelector`
  - `branch_id`
  - `fork_group_id`
  - `promotion`
  - `assembly`
  - `discard`
- Without a frozen vocabulary, both BookForge changes and Nanda integration will keep normalizing scope drift.

## Detailed Work
- Define the engine-owned runtime modes and result states in one place.
- Define the coordinate primitives:
  - `TimelineNodeRef`
  - `ScopeSelector`
- Freeze the rule that `ScopeSelector` may explicitly address a derived branch or fork group.
- Freeze the rule that `revision_id` is monotonic on node transitions within a branch.
- Freeze the public contract rule that `StateSurface` and `IssueTicket` are book-rooted and narrowed by selectors instead of stitched together from many tiny surfaces.
- Freeze which existing artifacts count as:
  - immutable lineage anchors
  - frozen projections
  - mutable compatibility views
  - diagnostic-only artifacts
- Freeze the branch model terms:
  - `main`
  - derived branch
  - fork group
  - assembly branch
  - promotion
  - assembly
  - discard
- Freeze the fork-group rule that the parent snapshot stays fixed for the group unless an explicit rebase or recreation step occurs.
- Align help docs with those definitions.
- Add a small central code surface for caller-visible mode labels and source artifact classification.
- Add a small central code surface for the shared coordinate and selector types.
- Add a small central code surface for current-node pointer semantics on `main` and derived branches.
- Freeze the rule that `ObserverView` is Nanda-side only and not part of the BookForge-owned shared contract set.
- Document the specific `veiled_ledger_b1` failure class this contract is meant to prevent.

## Files Likely Touched
- `docs/help/workflow.md`
- `docs/help/outline_generate.md`
- `docs/help/run.md`
- `docs/help/index.md`
- `src/bookforge/cli.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/contracts/__init__.py`
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/scope_selector.py`
- `src/bookforge/contracts/state_surface.py`

## Tests
- `python -m pytest tests/test_section_workflow.py tests/test_workspace_init.py tests/test_runner_outline_gate.py`
- Add a small contract-label test if central enums/labels are introduced, for example `tests/test_scope_contracts.py`
- Add a contract-shape test for `TimelineNodeRef` and `ScopeSelector`, for example `tests/test_timeline_node.py`

## Definition Of Done
- Runtime mode vocabulary is frozen in code and docs.
- The coordinate and selector primitives are frozen in code and docs.
- `revision_id` semantics are frozen clearly enough that later stories do not invent incompatible counters.
- Branch-model terms are defined clearly enough that later stories do not invent competing meanings.
- Fork-group freeze/rebase semantics are defined clearly enough that later stories do not invent unsafe merge behavior.
- Source artifact classes are classified consistently for current workflow artifacts.
- The docs no longer imply that a section-scoped command is a full-batch command.
- The repo has one canonical explanation of what is and is not a lineage anchor.

## Notes
- This step is intentionally contract-heavy and code-light. The output is a boundary that later stories can implement against.
- Completed 2026-04-21 with:
  - `src/bookforge/contracts/` vocabulary, coordinate, selector, and source-artifact classification modules
  - help/CLI wording aligned to `deep_outline`, `section_local_outline`, and `section_write`
  - focused contract tests covering labels, artifact classes, `TimelineNodeRef`, and `ScopeSelector`

---

## Source 7: `steps/0020-add-read-only-query-surface/step.md`

# 0020 Add Read-Only Query Surface

Status: completed

## Goal
- Expose stable, small, testable read APIs over current BookForge workflow state, lineage anchors, integrity evidence, and current execution coordinates.

## Problem
- Current diagnostics require direct file inspection across many workspace artifacts.
- That forces Nanda to scrape raw files and makes BookForge runtime truth harder to reuse inside its own tests and command paths.

## Detailed Work
- Add `src/bookforge/query/workspace.py` for:
  - active book/cursor
  - current main-branch node
  - branch manifests or branch-local current-node pointers
  - section status
  - active section
  - current pause marker or progress heartbeat
  - active fork groups
- Add `src/bookforge/query/workflow.py` for:
  - workflow family
  - run mode
  - branch id
  - fork-group status
  - last explicit workflow action
  - source artifact class
- Add `src/bookforge/query/lineage.py` for:
  - immutable source run lookup
  - frozen chapter projection lookup
  - section draft lineage
  - materialization source classification
  - `ScopeSelector -> TimelineNodeRef` resolution
  - parent-node and fork-group ancestry lookup
- Ensure `ScopeSelector` resolution supports explicit branch and fork-group addressing instead of assuming `main`.
- Add `src/bookforge/query/integrity.py` for:
  - outline vs prose vs state disagreement summaries
  - mutable-source usage detection
  - chimera-risk indicators
  - branch contamination warnings
- Add `src/bookforge/query/characters.py` and `src/bookforge/query/continuity.py` for read access to current supporting state.
- Keep all query modules read-only and typed.
- Split helpers and translators instead of creating a single kitchen-sink query module.

## Files Likely Touched
- `src/bookforge/query/__init__.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/characters.py`
- `src/bookforge/query/continuity.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/memory/continuity.py`
- `src/bookforge/characters.py`

## Tests
- `python -m pytest tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_section_workflow.py tests/test_workspace_init.py`
- Add fixture coverage that exercises both healthy and mixed-lineage workspaces
- Add fixture coverage for main-branch and derived-branch lookup paths if branch state exists in the fixture set

## Definition Of Done
- A caller can ask BookForge for workflow family, source run, active section, current node, and integrity verdict without hand-reading JSON files.
- A caller can resolve a `ScopeSelector` to the current `TimelineNodeRef` for the selected book, branch, or fork-group scope.
- Query modules return structured Python objects, not raw strings.
- Query modules do not mutate workspace files.
- The `veiled_ledger_b1` chimera class can be surfaced through query helpers rather than ad hoc scripts.

## Notes
- This is the step that lets Nanda stop depending on raw workspace scraping as its only observation seam.
- Completed 2026-04-21 with:
  - read-only query modules under `src/bookforge/query/`
  - current-node, workflow snapshot, lineage lookup, continuity, character, and integrity helpers
  - fixture-backed tests for healthy and mixed-lineage workspaces

---

## Source 8: `steps/0030-emit-versioned-state-surfaces-and-issue-tickets/step.md`

# 0030 Emit Versioned State Surfaces And Issue Tickets

Status: completed

## Goal
- Make BookForge emit engine-owned, book-rooted state, issue, and pause contracts after execution so supervision can act on explicit truth instead of inference.

## Problem
- Current execution artifacts are rich but uneven:
  - progress heartbeats
  - run logs
  - phase history
  - outline artifacts
  - scene meta
- They do not yet combine into one stable, versioned contract surface.
- The runtime also lacks a single execution coordinate that every emitted contract can point at.

## Detailed Work
- Implement contract objects under `src/bookforge/contracts/`:
  - `timeline_node.py`
  - `scope_selector.py`
  - `state_surface.py`
  - `issue_ticket.py`
  - `execution_request.py`
  - `execution_result.py`
- Define the public contract rule:
  - `StateSurface` and `IssueTicket` are book-rooted
  - narrowing happens through scope selectors and projections, not by stitching together tiny independent surfaces
- Persist emitted state and ticket contracts under a per-book supervision root even if the underlying storage is normalized by branch, node, or artifact type.
- Define revision behavior for `StateSurface` so pre/post execution comparisons are deterministic within a branch.
- Define `revision_id` as node-transition monotonic within a branch, not surface-emission monotonic.
- Require every emitted surface and ticket to carry a `TimelineNodeRef`.
- Persist `current_node.json` or an equivalent pointer for the active main-branch node.
- Persist branch-local current-node pointers or a branch manifest model for derived branches so off-main pause/resume is unambiguous.
- Make `ScopeSelector` capable of explicitly addressing:
  - `main`
  - a derived `branch_id`
  - a `fork_group_id`
- Persist enough metadata to reconstruct:
  - workflow family
  - chapter/section/scene target
  - source lineage
  - branch id
  - fork group id
  - pre/post revision ids
- Emit categorized `IssueTicket` output from the first supervised issue class:
  - `scope_contract_violation`
  - `lineage_conflict`
  - `chimera_risk`
  - `provider_retry_exhausted`
  - `recovery_mode_required`
- Emit explicit pause state when bounded retry policy is exhausted, checkpointed to the active `TimelineNodeRef`.
- Thread emission into existing section-local execution without building a second state system.
- Support branch-scoped surfaces and tickets as first-class outputs, not as log noise or hidden sidecars.
- Keep ticket concerns distinguishable by scope:
  - branch tickets for execution concerns
  - main-branch tickets for canonical concerns
  - assembly-branch tickets for merge concerns
- When fork-group execution exists, make the main-branch book surface able to show active fork-group progress without pretending sibling branch results are already canonical.

## Files Likely Touched
- `src/bookforge/contracts/__init__.py`
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/scope_selector.py`
- `src/bookforge/contracts/state_surface.py`
- `src/bookforge/contracts/issue_ticket.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- `src/bookforge/runner.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/pipeline/run_logging.py`
- `src/bookforge/pipeline/phase_history.py`
- `src/bookforge/pipeline/io.py`
- `src/bookforge/workspace.py`

## Tests
- `python -m pytest tests/test_timeline_node.py tests/test_state_surface.py tests/test_issue_tickets.py tests/test_pause_marker.py tests/test_section_workflow.py tests/test_runner_targeting.py`
- Add one integration-style assertion that a real scoped run emits a revisioned book-rooted state surface and categorized issue output with node coordinates

## Definition Of Done
- One real execution path emits a versioned book-rooted `StateSurface` that carries a `TimelineNodeRef`.
- One real integrity failure emits categorized `IssueTicket` output that carries a `TimelineNodeRef`.
- One bounded provider stall can be observed as a pause/result state rather than opaque log churn, with the pause checkpointed to the active node.
- Revision ids make pre/post execution comparisons unambiguous within a branch.
- Derived branches have enough emitted pointer or manifest state that pause/resume and verification do not depend on guessing which node is current.
- Main-branch and derived-branch surfaces use the same contract family instead of ad hoc side channels.

## Notes
- This story should stay focused on the first useful contract surface, not every future metric or detector.

---

## Source 9: `steps/0040-add-truthful-scoped-execution-and-bounded-resume/step.md`

# 0040 Add Truthful Scoped Execution And Bounded Resume

Status: completed

## Goal
- Support one narrow `ExecutionRequest -> ExecutionResult` path on `main` without pretending BookForge already has a generic agent runtime.

## Problem
- Current command surfaces can resume real work, but they still expose too much implicit behavior:
  - same-mode resume
  - recovery import
  - outline gate bypass
  - provider stall handling
- That makes it too easy for external callers to request one thing and get another.

## Detailed Work
- Lock the first truthful execution path:
  - `resume_paused_section`
  - same workflow family
  - same source lineage
  - same branch (`main`)
- Define the minimum `ExecutionRequest` fields required for that path:
  - target scope
  - expected `TimelineNodeRef`
  - expected workflow family
  - expected source lineage
  - allowed move class
- Add a small execution adapter that translates the request into existing BookForge operations.
- Refuse overscoped or mismatched requests explicitly instead of silently switching modes.
- Refuse if:
  - the live node does not match the expected node
  - the live branch is not `main`
  - the workflow family differs
  - the source lineage differs
- Bound provider retry behavior so the caller gets either:
  - `success`
  - `retryable_pause`
  - `hard_fail`
- Checkpoint the active `TimelineNodeRef` when a retryable pause is emitted so the resume coordinate is exact.
- Return `ExecutionResult` with:
  - status
  - node before
  - node after
  - artifact refs
  - pre/post revisions
  - new issue tickets
  - whether the run remained in the requested mode
- Do not add branch-rerun or fork-group behavior in this story. This story is main-branch resume only.

## Files Likely Touched
- `src/bookforge/cli.py`
- `src/bookforge/runner.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- `docs/help/workflow.md`
- `docs/help/run.md`

## Tests
- `python -m pytest tests/test_scoped_execution.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_runner_targeting.py tests/test_pause_marker.py`
- Add coverage for refusal paths where expected node, workflow family, source lineage, or branch does not match live workspace truth

## Definition Of Done
- A caller can submit one narrow `resume_paused_section` request without knowing internal phase choreography.
- The request cannot silently switch workflow families or source lineage.
- The request cannot silently cross from `main` into a derived branch or recovery mode.
- Provider exhaustion yields a truthful pause/fail result with an exact node checkpoint.
- The result contains enough information for a delegate/verify loop.

## Notes
- A truthful narrow execution path is better than a fake generic control surface.

---

## Source 10: `steps/0045-add-isolated-branch-reruns-and-fork-group-assembly/step.md`

# 0045 Add Isolated Branch Reruns And Fork Group Assembly

Status: completed

## Goal
- Add explicit branch isolation and merge semantics so reruns and future parallel section work can execute safely without contaminating canonical state.

## Problem
- The chapter 3 chimera class happened because recovery and continuation logic ran against live state without isolation.
- A single-branch rerun and a multi-branch fan-out/fan-in assembly are not the same thing, but they need to share the same branch primitives.
- If we build rerun branches without accounting for fork groups, later parallel writing work will inherit branch semantics that are too narrow.

## Detailed Work
- Add branch creation from a parent `TimelineNodeRef` with:
  - unique `branch_id`
  - inherited immutable source lineage
  - declared parent node
- Support isolated rerun branches for scoped phase re-execution:
  - branch-local writes only
  - branch-scoped `StateSurface` and `IssueTicket` output
  - no direct mutation of canonical state
- Add `fork_group_id` for sibling branches that share:
  - the same parent node
  - the same pre-fork canonical ancestry
- Freeze the fork-group parent snapshot for the lifetime of the group unless an explicit rebase or recreation step is performed.
- Enforce the fan-out rule:
  - sibling branches may read from the parent node and pre-fork canonical state
  - sibling branches may not read one another during execution
- Refuse assembly when canonical preconditions required by the frozen parent snapshot are no longer satisfied.
- Distinguish merge types explicitly:
  - `promotion` for single-branch replacement or adoption into `main`
  - `assembly` for combining multiple sibling branches into an assembly branch that is still non-canonical
- Create an explicit assembly branch for fork-group merge work.
- Run seam audit and any seam-local repair on the assembly branch, not on `main`.
- Require explicit reconciliation and integrity validation before either promotion or validated assembly promotion returns content to `main`.
- Reuse chapter seam audit or equivalent join validation as the assembly-branch integrity gate for sibling outputs.
- Classify branch outcomes explicitly:
  - `promote_ready`
  - `needs_review`
  - `discard`
- Map those branch outcomes to public execution-result states and canonical-change status explicitly in the shared contract docs.
- Preserve lineage traceability from main -> parent node -> branch nodes -> promotion or assembly result.

## Files Touched
- `src/bookforge/branching.py`
- `src/bookforge/contracts/__init__.py`
- `src/bookforge/contracts/branch_manifest.py`
- `src/bookforge/contracts/vocabulary.py`
- `src/bookforge/query/_common.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/supervision/__init__.py`
- `src/bookforge/supervision/emit.py`
- `src/bookforge/supervision/paths.py`
- `tests/test_branch_execution.py`
- `tests/test_branch_promotion.py`
- `tests/test_fork_group_assembly.py`
- `tests/test_scope_contracts.py`

## Tests
- `python -m pytest --basetemp .pytest_tmp_0045 tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scope_contracts.py`
- `python -m pytest --basetemp .pytest_tmp_0045_regression tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py`
- Add coverage for:
  - branch creation from a declared parent node
  - branch scope preservation in manifest and current-node projection
  - refusal on silent source switching
  - discard leaving canonical state untouched
  - sibling branches sharing a `fork_group_id`
  - no-cross-read enforcement for sibling branches
  - refusal when a fork-group parent snapshot is stale against required canonical preconditions
  - assembly branch blocked from promotion by failed seam validation

## Definition Of Done
- A derived branch can rerun a scoped phase without mutating canonical state directly.
- Every branch records its parent `TimelineNodeRef`.
- Sibling branches in a fork group share the same parent node and `fork_group_id`.
- Promotion and assembly are distinct code paths with distinct validation gates.
- A failed or discarded branch leaves canonical state untouched.
- Assembly can surface seam issues as an explicit validation result on the assembly branch before promotion to `main`.
- Fork groups cannot silently merge against incompatible canonical advancement; they must rebase, recreate, or refuse.

## Notes
- This story defines the branching primitives broadly enough for sequential reruns and future parallel writing, even if the full fan-out scheduler lands later.
- Assembly remains off `main`. The current implementation provides an explicit assembly branch plus validation-state recording and promotion gating; automatic seam-audit execution can plug into that branch seam later without changing the contract model.

---

## Source 11: `steps/0050-harden-reconciliation-integrity-and-command-surface/step.md`

# 0050 Harden Reconciliation, Integrity, And Command Surface

Status: completed

## Goal
- Make the supervised paths safe enough for repeated use and difficult to misuse through misleading docs, stale artifacts, partial reconciliation, or incorrect branch merge behavior.

## Problem
- The first five stories can expose truthful surfaces and execution paths, but callers still need strong guarantees that:
  - state was reconciled before control returned
  - no-op or stale writes are visible
  - degraded integrity is surfaced instead of swallowed
  - help text does not overclaim runtime scope

## Detailed Work
- Add mandatory post-execution reconciliation before returning control on `main`.
- Add mandatory post-promotion reconciliation before merged content becomes canonical.
- Add mandatory post-assembly-branch reconciliation before assembled content is eligible for promotion.
- Add pre/post revision diff helpers for state-surface comparison.
- Strengthen integrity helpers so they can flag:
  - mixed workflow-family contamination
  - mutable-source materialization
  - outline/prose/state disagreement
  - overscoped recovery
- Surface merge-specific failures explicitly, including:
  - promotion without validation
  - assembly promotion without validation
  - unvalidated assembly work touching `main`
  - branch lineage drift
- Add one explicit mapping table between:
  - branch lifecycle state
  - public execution result
  - canonical-change status
- Surface no-op, stale-write, downgraded-integrity, promotion-required, and recovery-required outcomes explicitly.
- Align help docs and CLI language with the actual execution surface.
- Keep new helpers small and split by concern.

## Files Likely Touched
- `src/bookforge/supervision/reconcile.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/execution/scoped.py`
- `src/bookforge/branching.py`
- `src/bookforge/branching_fork.py`
- `src/bookforge/branching_execution.py`
- `src/bookforge/branching_lifecycle.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/runner.py`
- `src/bookforge/workspace.py`
- `src/bookforge/cli.py`
- `docs/help/workflow.md`
- `docs/help/outline_generate.md`
- `docs/help/run.md`
- `docs/help/index.md`

## Tests
- `python -m pytest tests/test_query_integrity.py tests/test_workspace_init.py tests/test_section_workflow.py tests/test_runner_targeting.py`
- Add targeted reconciliation/no-op coverage if needed, for example `tests/test_reconciliation.py`
- Add merge-path reconciliation coverage if branch promotion or assembly helpers are introduced, for example `tests/test_branch_reconciliation.py`
- Current executed validation:
  - `python -m pytest --basetemp .pytest_tmp_integrity_slice tests/test_query_integrity.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scope_contracts.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050c tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0050_branch_receipts tests/test_branch_execution.py tests/test_fork_group_assembly.py tests/test_branch_promotion.py tests/test_supervision_emit.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050d tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0050_integrity_plus tests/test_query_integrity.py tests/test_supervision_emit.py tests/test_scoped_execution.py tests/test_query_workspace.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050f tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`

## Definition Of Done
- Every supported execution result can be classified as `success`, `no_op`, `retryable_pause`, `hard_fail`, `integrity_degraded`, or `promotion_required`.
- Integrity regressions introduced during repair are surfaced, not swallowed.
- Promotion and assembly cannot quietly bypass reconciliation.
- Callers can map branch state, public result, and canonical-change status without reverse-engineering the merge path.
- Help docs do not imply a broader runtime scope than the code actually executes.
- Callers can tell whether a request changed canonical state, changed branch state only, or failed before canonical promotion.
- Callers can tell whether integrity improved or worsened.

## Notes
- This story is where the command/help surface finally becomes trustworthy enough for external orchestration.
- Current implemented slice:
  - main-branch reconciliation snapshots and before/after diff details
  - branch-local reconciliation snapshots and before/after diff details for off-main mutation paths
  - promotion now emits a reconciled main-branch result instead of only a derived-branch result
  - ambiguous reconciliation field renamed to `pre_reconciliation_status`
  - revision-only expected-node drift is classified as `stale_write`
  - structural integrity now detects `workflow_family_contamination`, `stale_parent`, and `overscoped_recovery`
  - branch-control logic has been split into smaller files before further 0050 growth
  - branch receipts now emit `branch_change_status` without claiming canonical mutation
  - branch revision tokens now use microsecond precision to avoid same-second node collisions during rapid branch activity
  - workflow and run help now describe the public reconciliation fields
- Follow-on work:
  - future integrity detectors beyond the current chimera/mutable-source/workflow-family/stale-parent/overscoped slice can land as later stories without blocking 0050 completion
  - additional command/help alignment for newly extracted execution actions now belongs to `0060`

---

## Source 12: `steps/0060-extract-minimal-engine-execution-surface-for-nanda/step.md`

# 0060 Extract Minimal Engine Execution Surface For Nanda

Status: completed

## Goal
- Extract a smaller execution surface from the current workflow wrappers so Nanda can compose outlining, writing, linting, and repair as narrow engine actions instead of depending on large fixed command chains.

## Problem
- The current command surface is still too macro-shaped:
  - `workflow init`
  - `workflow freeze-section`
  - `workflow advance-section`
  - `workflow resume-paused-section`
  - `run`
- That is acceptable for transitional operator use, but it is the wrong long-term seam for an author agent.
- Nanda will need to steer execution as a choose-your-own-adventure loop:
  - inspect current truth
  - discover legal next actions
  - choose one narrow action
  - inspect the resulting receipt
  - continue or branch without re-encoding engine behavior outside BookForge
- If the CLI remains the only orchestration surface, two bad things happen:
  - BookForge logic gets trapped in wrapper commands instead of reusable engine actions
  - Nanda is forced to infer valid transitions from docs and historical behavior instead of asking the engine directly

## Detailed Work
- Split oversized workflow-control modules before extending the execution surface further.
  - `src/bookforge/branching.py` should be split by concern before more branch lifecycle and reconciliation logic lands.
  - Natural seams:
    - branch store / manifest / snapshot helpers
    - branch execution isolation helpers
    - branch lifecycle / promotion / assembly gating
- Define a smaller action catalog under `src/bookforge/execution/` or equivalent.
- Separate two layers explicitly:
  - macro workflow wrappers for CLI/operator convenience
  - narrow engine actions for programmatic composition
- Define at least one shared action descriptor contract for queryable action discovery, for example:
  - `ExecutionOption`
  - `AvailableAction`
  - or equivalent
- Each narrow action should declare:
  - supported workflow family
  - supported branch policy
  - required selector shape
  - required lineage preconditions
  - whether it may mutate canonical state
  - emitted receipt/result contract
  - legal next actions on success / pause / failure
- First extraction target should cover at least one path in each family:
  - outline/materialization:
    - initialize workflow
    - freeze section
    - finalize chapter
  - write/lint/repair:
    - resume paused write
    - write frozen section
    - optional narrower scene-step actions later if the runtime split is justified
  - branch lifecycle:
    - create branch
    - discard branch
    - validate assembly
    - promote branch
- Add a query seam that returns legal next actions from the current engine state.
  - Inputs:
    - `ScopeSelector`
    - current `TimelineNodeRef`
    - integrity verdict
    - branch lifecycle state when applicable
  - Output:
    - explicit legal action list
    - refusal reasons for currently illegal actions
- Keep BookForge as the authority on valid transitions.
  - Nanda should choose among legal actions.
  - Nanda should not own the engine transition graph.
- Make the CLI wrappers consume the same action layer instead of duplicating orchestration logic.
- Document the choose-your-own-adventure rule clearly:
  - query truth
  - query legal next actions
  - execute one narrow action
  - inspect receipt
  - repeat

## Files Likely Touched
- `src/bookforge/execution/__init__.py`
- `src/bookforge/execution/scoped.py`
- `src/bookforge/execution/` new action modules
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/contracts/` new action-discovery contract if needed
- `src/bookforge/cli.py`
- `src/bookforge/branching.py` or its split replacements
- `docs/help/workflow.md`
- `docs/help/run.md`
- `docs/help/index.md`

## Tests
- Add execution-surface tests, for example:
  - `tests/test_execution_actions.py`
  - `tests/test_action_discovery.py`
  - `tests/test_branch_action_lifecycle.py`
- Add at least one integration test that proves:
  - query current truth
  - query legal next actions
  - execute a narrow action
  - observe the next legal action set change
- Add at least one real branch flow integration test:
  - create branch
  - run scoped action in branch
  - promote branch
  - verify canonical surface and lineage receipt on `main`
- Current executed validation:
  - `python -m pytest --basetemp .pytest_tmp_0060_branch_action tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060c tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_branch_lifecycle tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060d tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_assembly_action tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060e tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_assembly_create tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060f tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_finalize tests/test_execution_actions.py tests/test_action_discovery.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060g tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_lock tests/test_execution_actions.py tests/test_action_discovery.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060h tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_write tests/test_execution_actions.py tests/test_action_discovery.py tests/test_scoped_execution.py tests/test_section_workflow.py tests/test_chapter_seam.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060i tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`

## Definition Of Done
- BookForge exposes a smaller execution action surface that is distinct from CLI wrappers.
- At least one outline/materialization path and one write/resume path are callable through narrow engine actions.
- The engine can report legal next actions from current truth without requiring Nanda to infer them externally.
- CLI wrappers call the extracted action layer instead of retaining unique orchestration logic.
- Branch lifecycle actions are available through the same execution-surface model.
- The action layer preserves the current truth model:
  - `TimelineNodeRef`
  - `ScopeSelector`
  - reconciliation receipts
  - integrity and lineage enforcement
- No new control-surface work is added by growing `branching.py` further; oversized modules are split first.

## Notes
- This is not a generic agent framework story.
- It is a controlled extraction story: turn the existing engine into a smaller, composable action surface while keeping BookForge in charge of prose generation and canonical mutation.
- Current implemented slice:
  - `ExecutionOption` contract for queryable action discovery
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - narrow `initialize_section_workflow` execution adapter under `bookforge.execution`
  - narrow `freeze_section_from_phase03_artifact` execution adapter under `bookforge.execution`
  - narrow `write_frozen_section` execution adapter under `bookforge.execution`
  - narrow `lock_section_from_written_state` execution adapter under `bookforge.execution`
  - narrow `finalize_chapter_from_locked_sections` execution adapter under `bookforge.execution`
  - narrow `create_assembly_branch` execution adapter under `bookforge.execution`
  - narrow `create_branch` execution adapter under `bookforge.execution`
  - narrow `discard_branch` execution adapter under `bookforge.execution`
  - narrow `promote_branch_to_main` execution adapter under `bookforge.execution`
  - narrow `record_assembly_validation` execution adapter under `bookforge.execution`
  - existing `resume_paused_section` adapter remains the pause-aware write/resume counterpart
  - `bookforge workflow init`, `bookforge workflow freeze-section`, `bookforge workflow write-section`, `bookforge workflow lock-section`, and `bookforge workflow finalize-chapter` now route through the extracted execution adapters
  - `bookforge workflow legal-actions` exposes the same action-discovery seam for operator use
  - `bookforge workflow legal-actions --branch-id <id>` now exposes derived-branch legality for discard/promotion/assembly-validation checks
  - `bookforge workflow legal-actions --fork-group-id <id>` now exposes main-branch fork-group legality for assembly creation
  - `bookforge workflow advance-section` now composes extracted actions instead of calling its own orchestration path
- Follow-on work:
  - extract deeper write/lint/repair sub-actions if the choose-your-own-adventure author loop needs per-scene or per-phase control beyond section-level write and truthful pause/resume
  - add success/pause/failure next-action hints to the action descriptors if the current simpler descriptor stops being sufficient

---

## Source 13: `steps/0070-segment-section-write-into-scoped-scene-actions/step.md`

# 0070 Segment Section-Write Into Scoped Scene Actions

Status: completed

## Goal
- Break the current `section_write` loop into truthful scene-phase execution actions and readiness queries so Nanda can steer write, lint, and repair as a graph of legal skills instead of only invoking section-level or batch wrappers.

## Problem
- `0060` extracted an honest section-level control surface:
  - `freeze_section_from_phase03_artifact`
  - `write_frozen_section`
  - `resume_paused_section`
  - `lock_section_from_written_state`
  - `finalize_chapter_from_locked_sections`
- That is enough for section-level composition, but it still hides the actual write choreography inside `run_loop`.
- Today the engine still behaves like this:
  - decide one section
  - enter `run_loop`
  - implicitly run plan -> preflight -> continuity -> write -> state_repair -> lint -> repair -> apply/commit
  - return only when the whole scene or section segment is done or paused
- That is too coarse for the next Nanda author loop.
- The author system needs to be able to ask narrower questions, for example:
  - can I write prose for this scene right now
  - what prerequisite artifacts are missing before prose can be generated
  - can I lint this scene yet
  - can I repair only the prose without re-running planning
  - what are my legal next actions from the current scene node
- The user-facing author pane also needs a truthful capability basis.
  - The author voice may stay expressive.
  - The capability claims must come from actual BookForge readiness and execution receipts, not persona improvisation.

## Detailed Work
- Freeze the first scene-phase action vocabulary for the `section_write` family.
  - Candidate first slice:
    - `plan_scene`
    - `preflight_scene_state`
    - `generate_continuity_pack`
    - `write_scene_prose`
    - `state_repair_scene_patch`
    - `lint_scene_prose`
    - `repair_scene_prose`
    - `apply_scene_commit`
  - The first pass does not need to expose every micro-helper inside those phases.
  - The boundary should still be phase-shaped, not internal utility-shaped.
- Add a scene-phase readiness/query seam.
  - A caller should be able to ask:
    - what scene-phase actions are legal for the current node
    - what prerequisite artifacts are present
    - what prerequisite artifacts or prior actions are missing
    - what the recommended next action is
  - This can be a new contract or an extension of `ExecutionOption.details`, but it must be explicit and machine-usable.
  - `legal_next_actions(...)` alone is not enough for this slice.
  - The first implementation must also answer readiness questions about prerequisites, available inputs, present outputs, and mutation scope.
- Introduce a truthful scene-phase status object.
  - Minimum information:
    - current scene scope
    - current phase artifact availability
    - whether prose exists
    - whether lint exists
    - whether repair exists
    - whether the scene is committed
    - missing prerequisites for each action
    - current pause marker if any
  - This should be queryable without starting execution.
- Freeze produced-artifact truth semantics for scene-phase work.
  - Every produced artifact in this slice must declare one status:
    - `authoritative`
    - `provisional`
    - `derived`
    - `diagnostic`
  - The first implementation should not rely on implicit file meaning.
  - Query surfaces and execution receipts must report artifact status explicitly.
- Add a produced-artifact receipt surface.
  - The first slice may implement this as a small new contract or as a typed detail structure carried by `ExecutionResult`.
  - Minimum information per artifact:
    - artifact id or stable label
    - path or logical ref
    - artifact status
    - producing node
    - producing action
    - whether it is consumable, resumable, replaceable, or diagnostic-only
- Extract the first pure prose-generation action.
  - `write_scene_prose` must be callable without automatically triggering lint, repair, or final state commit.
  - It should return the generated prose and the raw patch/artifact references the write phase already produces.
  - If prerequisites are missing, it must refuse truthfully and report which prior actions are required.
- Preserve pause/resume truth at the scene-phase level.
  - Scene actions must emit enough node detail that a caller can tell:
    - which scene and phase was active
    - whether the action completed, paused, or failed
    - what artifacts were created
    - what the next legal action is
- Split `runner.py` by concern before adding more action logic there.
  - The current file is still too large and mixes:
    - scene targeting
    - pause handling
    - per-phase execution
    - state application
    - persistence
  - The extraction should move toward smaller modules such as:
    - scene readiness / prerequisite evaluation
    - scene-phase execution adapters
    - scene commit/apply helpers
    - pause + receipt helpers
- Keep `run_loop` as a wrapper, not the only truthful write engine.
  - `run_loop` may continue to exist for batch/operator use.
  - It should progressively become a macro over extracted scene-phase actions instead of the source of truth for phase choreography.
- Keep BookForge as the authority on skill traversal.
  - Nanda should not infer "if prose exists then lint is legal" on its own.
  - BookForge should answer that through legal-next-action and readiness surfaces.

## Surface Refinements
### Artifact Status Vocabulary
- `authoritative`
  - Canonical truth that downstream execution may safely consume.
- `provisional`
  - Produced by an execution action but not yet validated or promoted.
  - May be resumable, replaceable, or discardable depending on the action contract.
- `derived`
  - Computed from other artifacts; useful for navigation or prompt context, but not independently canonical.
- `diagnostic`
  - Observability or debugging material only; never treated as an execution prerequisite by itself.

### ScenePhaseReadiness
- The first scene-phase readiness surface should answer, for each candidate action:
  - whether it is legal now
  - whether it is ready now
  - which prerequisites are missing
  - which inputs are available
  - which outputs already exist
  - whether the action would mutate canonical state, provisional state, or only diagnostics
  - the recommended next action from the current scene node
  - whether a pause marker or stale prerequisite blocks execution
- This surface should be book-rooted and coordinate-addressable through `TimelineNodeRef` and `ScopeSelector`.
- The first slice should prefer one readiness surface with multiple phase rows rather than many disconnected single-purpose booleans.

### Partial Output Rules
- A scene-phase action may produce useful intermediate output without reaching final scene commit.
- The first contract rules are:
  - incomplete but execution-produced scene-phase artifacts are `provisional`
  - provisional outputs may be resumable or replaceable
  - readiness must say whether a downstream action may consume a provisional output
  - diagnostics may reference provisional outputs, but diagnostics do not promote them
  - no downstream action may silently treat a provisional output as authoritative

### Layered Query Rule
- Scene/workflow state, appearance state, durable inventory state, continuity state, and thought-signature context must remain projection layers over the same coordinate system.
- This step should only implement the layers required for the first code slice.
- It should not pre-build future layer surfaces that are not yet needed.

### Author Capability Grounding
- The author pane may stay expressive, but it may only claim capabilities that correspond to actions currently reporting ready or legal status through the BookForge readiness/action surfaces.
- Persona framing may translate capability into voice.
- Persona framing may not invent tools, diagnostics, or mutation paths that BookForge cannot actually execute.

## Nanda Impact
- The Observe pane can already render truthful workspace, integrity, and node state.
- The Author pane needs the next contract layer so it can stay honest while becoming more useful.
- This step is the BookForge-side prerequisite for a Nanda-side author bus shaped like:
  - read current `StateSurface`
  - read scene-phase readiness / legal actions
  - gather relevant thought signatures and artifact refs
  - build a structured worker prompt package
  - execute one narrow worker action
  - translate the receipt back into author voice without claiming capabilities that are not wired
- The author pane should not claim generic tools such as "The Forge" or "The Auditor" unless those map to real query or execution surfaces exposed by BookForge.
- This step should leave Nanda with enough truthful structure to say:
  - "I can write prose for scene 3 now."
  - "I cannot lint yet because prose is missing."
  - "I can inspect continuity state, but I cannot mutate until you choose a legal action."

## Files Likely Touched
- `src/bookforge/runner.py`
- `src/bookforge/execution/scoped.py`
- `src/bookforge/execution/` new scene-action modules
- `src/bookforge/execution/scene_sequence.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/` new readiness module if needed
- `src/bookforge/contracts/execution_option.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- `src/bookforge/contracts/` new scene-readiness and produced-artifact contracts if needed
- `src/bookforge/pipeline/phase_history.py`
- `src/bookforge/pipeline/run_logging.py`
- `src/bookforge/cli.py`
- `docs/help/workflow.md`
- `docs/help/run.md`
- `docs/help/index.md`

## Tests
- Add scene-phase execution tests, for example:
  - `tests/test_scene_action_execution.py`
  - `tests/test_scene_action_readiness.py`
- Add refusal-path tests that prove:
  - `write_scene_prose` refuses when scene planning or continuity prerequisites are missing
  - `lint_scene_prose` refuses until prose exists
  - `repair_scene_prose` refuses until lint or repairable prose exists
- Add readiness tests that prove:
  - the readiness surface reports missing prerequisites instead of only blocked actions
  - artifact statuses are queryable for produced scene-phase outputs
  - provisional outputs are not silently treated as authoritative
- Add one progression test that proves a legal-action graph transition such as:
  - freeze section
  - discover `plan_scene`
  - execute `plan_scene`
  - discover `preflight_scene_state`
  - execute `preflight_scene_state`
  - discover `generate_continuity_pack`
  - execute `generate_continuity_pack`
  - discover `write_scene_prose`
  - execute `write_scene_prose`
  - discover `state_repair_scene_patch`
  - execute `state_repair_scene_patch`
  - discover `lint_scene_prose`
  - execute `lint_scene_prose`
  - observe `repair_scene_prose` or `apply_scene_commit` become the next reported path based on lint result
- Add one pause/resume test that proves a paused scene-phase action keeps a truthful phase-level node and can be resumed without silently widening scope.
- Add one wrapper test that proves `run_loop` or a CLI wrapper can consume the extracted scene-phase actions without changing external behavior.

## Definition Of Done
- BookForge exposes at least one truthful pure prose action that does not automatically trigger lint, repair, or commit.
- BookForge exposes a scene-phase readiness surface that tells a caller more than just allowed/blocked.
- A caller can ask what scene-phase actions are legal next and why blocked actions are blocked.
- A caller can ask what prerequisite artifacts or prior actions are missing before a selected scene-phase action can run.
- A caller can tell whether produced scene-phase artifacts are `authoritative`, `provisional`, `derived`, or `diagnostic`.
- Partial scene-phase outputs have explicit consumable/resumable/replaceable semantics instead of being implied by file presence.
- Scene-phase actions emit receipts with enough node and artifact detail for scoped resume and author-pane reporting.
- `run_loop` is no longer the only truthful owner of scene-phase choreography.
- The extracted scene-phase surface is explicit enough that Nanda can build author responses around actual capabilities instead of persona theater.

## Notes
- This story is not about exposing internal chain-of-thought.
- The Nanda-side "author bus" should be understood as a structured context assembly and worker-routing layer, not a request for raw hidden reasoning.
- The first extracted scene-phase surface should stay narrow and truthful.
  - Better to expose four or five reliable phase actions than a fake "full autonomous author" surface.
- This story should prefer phase-shaped actions over one-off internal utility entry points.
- The first code slice after this refinement should be:
  - `ScenePhaseReadiness`
  - `write_scene_prose`
- Do not turn this refinement into a new doctrine cycle.
  - The point is to give the next code slice a stable contract, not to spawn another planning branch.
- First slice landed 2026-04-22 with:
  - new contract objects:
    - `ProducedArtifactReceipt`
    - `ScenePhaseActionReadiness`
    - `ScenePhaseReadiness`
  - explicit produced-artifact status vocabulary:
    - `authoritative`
    - `provisional`
    - `derived`
    - `diagnostic`
  - `ExecutionResult.produced_artifacts` so scene-phase execution can emit typed artifact receipts instead of hiding them in generic details
  - a new query surface:
    - `bookforge.query.get_scene_phase_readiness(...)`
    - current slice is intentionally limited to the active cursor scene on `main`
    - current action rows:
      - `plan_scene`
      - `preflight_scene_state`
      - `generate_continuity_pack`
      - `write_scene_prose`
  - extracted execution actions:
    - `build_plan_scene_request(...)`
    - `plan_scene_action(...)`
    - `build_preflight_scene_state_request(...)`
    - `preflight_scene_state(...)`
    - `build_generate_continuity_pack_request(...)`
    - `generate_continuity_pack(...)`
    - `build_write_scene_prose_request(...)`
    - `write_scene_prose(...)`
    - `build_state_repair_scene_patch_request(...)`
    - `state_repair_scene_patch(...)`
    - `build_lint_scene_prose_request(...)`
    - `lint_scene_prose(...)`
    - `build_repair_scene_prose_request(...)`
    - `repair_scene_prose(...)`
    - `build_apply_scene_commit_request(...)`
    - `apply_scene_commit(...)`
  - public surface exposure for the first slice:
    - `bookforge workflow scene-readiness`
    - `bookforge workflow plan-scene`
    - `bookforge workflow preflight-scene-state`
    - `bookforge workflow generate-continuity-pack`
    - `bookforge workflow write-scene-prose`
    - `bookforge workflow state-repair-scene-patch`
    - `bookforge workflow lint-scene-prose`
    - `bookforge workflow repair-scene-prose`
    - `bookforge workflow apply-scene-commit`
    - `bookforge workflow legal-actions --scene <s>` now includes extracted scene actions such as `plan_scene`, `preflight_scene_state`, `generate_continuity_pack`, `write_scene_prose`, `state_repair_scene_patch`, `lint_scene_prose`, `repair_scene_prose`, and `apply_scene_commit` when scene scope is selected
  - guardrails on the continuity-pack slice:
    - emits the continuity pack as `derived`
    - applies safe preflight patch materialization only to an in-memory working state
    - does not mutate `state.json`, character files, durable inventory/state, prose, lint, repair, or commit artifacts
    - refuses when preflight artifacts imply provisional character or durable mutations that this slice cannot materialize truthfully yet
  - guardrails on the first write slice:
    - no implicit prerequisite generation
    - no automatic lint, repair, or commit
    - no hidden canonical mutation
    - refusal when preflight artifacts imply provisional character or durable mutations that this slice cannot materialize truthfully yet
  - guardrails on the state-repair slice:
    - emits the corrected state patch as `provisional`
    - applies safe preflight patch materialization only to an in-memory working state
    - consumes write prose and write patch, but does not apply the resulting patch to canonical state
    - does not run lint, prose repair, or commit
    - refusal when preflight artifacts imply provisional character or durable mutations that this slice cannot materialize truthfully yet
  - guardrails on the lint slice:
    - emits the lint report as `provisional` because prose repair consumes it as an execution artifact
    - applies safe preflight and state-repair patches only to in-memory working states
    - consumes the latest current prose baseline, which may be `write_prose` or a newer `repair_prose`
    - requires continuity-pack presence to preserve graph consistency even though lint itself reads prose/state inputs
    - does not repair prose, rerun state repair, or commit
    - refusal when preflight artifacts imply provisional character or durable mutations that this slice cannot materialize truthfully yet
  - guardrails on the repair slice:
    - emits `repair_prose` and `repair_patch` as `provisional`
    - consumes the latest current prose baseline plus the latest current failing lint report
    - does not rerun state repair, lint, or commit implicitly
    - reopens the readiness graph so `state_repair_scene_patch` becomes the next truthful extracted action
  - guardrails on the commit slice:
    - consumes the latest current passing provisional baseline rather than assuming `write_*` is final
    - mutates canonical state through the real scene apply path:
      - state patch apply
      - character/stat updates
      - appearance refresh when requested
      - durable apply
      - scene-file persistence
      - bible update
      - chapter rollup/compile on chapter end
      - cursor advance
    - emits reconciled main-branch execution results so commit receipts carry `state_change_status` and `canonical_change_status`
    - exposes authoritative scene artifacts as produced-artifact receipts instead of forcing callers to infer commit success from filesystem side effects
  - readiness/source-lineage corrections in this slice:
    - current provisional prose is now resolved from artifact lineage instead of assuming `write_*` remains current forever
    - stale provisional `state_repair` and `lint` outputs are surfaced as superseded when a newer repair pass exists
    - passing lint now truthfully recommends `apply_scene_commit`
  - guardrails on the preflight slice:
    - emits the preflight patch as `provisional`
    - does not apply the patch to `state.json`
    - does not apply character, stat, durable inventory, or deep-state mutations
    - leaves continuity generation as a separate future scene-phase action
  - validation completed:
    - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py -q`
    - `python -m pytest tests/test_execution_actions.py tests/test_action_discovery.py tests/test_scoped_execution.py tests/test_query_workspace.py -q`
    - `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_repair`
    - `python -m pytest tests/test_scoped_execution.py tests/test_execution_actions.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q --basetemp .pytest_tmp_0070_repair_regression`
    - `python -m pytest tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q`
    - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py tests/test_scoped_execution.py -q`
    - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
    - `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_commit`
    - `python -m pytest tests/test_scope_contracts.py tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_query_workspace.py -q --basetemp .pytest_tmp_0070_commit_regression`
    - `python -m pytest tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q --basetemp .pytest_tmp_0070_commit_supervision`
    - `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_commit_sceneplus`
    - `python -m pytest tests/test_runner_targeting.py tests/test_scene_action_execution.py tests/test_scene_phase_readiness.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_runner_wrap`
    - `python -m pytest tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_0070_runner_wrap_scoped`
    - `python -m pytest tests/test_scope_contracts.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_query_workspace.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_runner_wrap_regression`
    - `python -m pytest tests/test_runner_targeting.py tests/test_runner_outline_gate.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_execution_actions.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_runner_wrap_full`
    - `python -m pytest tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_targeting.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_section_range`
    - `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_targeting.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_section_range_full`
    - `python -m pytest tests/test_scope_contracts.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_query_workspace.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_section_range_regression`
  - wrapper/macro integration landed in this slice:
    - `run_loop` now drives scene execution through the extracted scene-phase actions instead of owning an independent monolithic per-scene implementation
    - the runner keeps the existing outer write gate, style-anchor bootstrap, progress heartbeat, and pause contract while delegating scene work to the scene-action sequence
    - section-level write wrappers now route through a dedicated `run_section_range(...)` macro instead of parameterizing `run_loop(...)` directly
    - `run_loop(...)` remains available as the batch/operator macro entry point over the same lower-level scene-phase traversal
    - the runner-side sequence preserves the existing repair loop and durable-slice expansion policy while passing the expansion hints into extracted scene-phase actions
    - pause conversion is now explicit:
      - scene-phase `retryable_pause` results are translated back into the legacy `run_paused.json` surface so scoped resume and workspace observation keep working
  - known repo-head drift outside this slice:
    - outline tests currently fail because some dummy test clients do not accept the newer thinking arguments
    - prompt composition checksum expectations are already stale at head
    - skilltree artifact tests expect files that are not present in this repo state

---

## Source 14: `steps/0071-make-scene-and-section-write-execution-branch-scoped/step.md`

# 0071 Make Scene And Section Write Execution Branch-Scoped

Status: completed

## Goal
- Let BookForge run scene-phase and section-range writing inside real derived branches instead of only on `main`, so the author or supervisor can rewrite old scenes, revise prior chapters, and isolate risky authoring work without forcing a full-book rerun.

## Problem
- `0070` gives us truthful scene-phase actions and a truthful section-range macro on `main`.
- That is necessary, but it is still single-root execution:
  - scene readiness is effectively `main` + active cursor only
  - scene actions are still `main_only`
  - section wrappers are still `main`-family commands even though they now use a dedicated section-range macro
- The current branch model is real, but shallow for writing:
  - branch manifests and branch-local current nodes already exist
  - branch snapshot roots already exist
  - rerun-freeze/materialization already exists on branches
  - promotion/assembly lifecycle already exists
- What is missing is branch-local writer truth.
- Today the system cannot truthfully support:
  - rewrite Chapter 1 Scene 2 while `main` is currently writing Chapter 9 Section 3
  - run two isolated scene writes in parallel without racing on canonical `main` state
  - let Nanda treat rewrite/recon work as a branch-scoped author move
- If we loosen `main` instead of making the writer branch-aware, we will recreate the same chimera class under a different name.

## Detailed Work
- Introduce an execution-root abstraction for write work.
  - `main` execution root points at the canonical book root.
  - derived-branch execution root points at the branch snapshot root.
  - scene-phase and section-range code must read/write only through that execution root.
- Make branch snapshots writer-complete.
  - Branch creation currently copies outline/state projections.
  - Expand the branch snapshot so it includes the write-side material a branch-scoped writer actually needs, such as:
    - `draft/chapters`
    - `draft/context`
    - phase-history content required for scene-phase reuse or resume
    - branch-local continuity/style anchor surfaces as needed
  - Keep the copied surface minimal but sufficient for truthful write execution.
- Generalize scene-phase readiness to branch scope.
  - `ScenePhaseReadiness` must resolve against:
    - `main`
    - or a derived branch selected through `ScopeSelector.branch_id`
  - It must stop assuming the active cursor scene on `main` is the only legal scene-phase target.
  - In a derived branch, the active cursor and active section come from the branch snapshot, not canonical `main`.
- Generalize scene-phase execution to branch scope.
  - Scene-phase request builders and executors must support derived branch execution.
  - Expected-node validation must compare against the branch-local current node, not `main`.
  - Produced-artifact receipts must be emitted to the branch-local supervision surface.
  - Scene actions should still refuse stale or mismatched lineage truthfully.
- Generalize section-range execution to branch scope.
  - `run_section_range(...)` should accept an execution root / branch selector.
  - A branch-local section-range run should:
    - use branch-local cursor truth
    - emit branch-local pause markers and execution receipts
    - not mutate canonical `main`
- Preserve strict `main` semantics.
  - `main` remains the canonical single-writer path.
  - Branch-scoped execution is the truthful route for:
    - off-cursor rewrite
    - recon work
    - parallel sibling write work
    - risky repair exploration
- Add branch-scoped write entry points.
  - Candidate first execution surfaces:
    - branch-scoped `scene-readiness`
    - branch-scoped `plan_scene`
    - branch-scoped `write_scene_prose`
    - branch-scoped `repair_scene_prose`
    - branch-scoped `apply_scene_commit`
    - branch-scoped section-range execution
  - Keep the first slice narrow. We do not need to expose every scene action in the first branch-aware pass if write/repair/commit prove the root.
- Keep branch writes isolated.
  - Branch-scoped execution must never mutate canonical state or canonical files directly.
  - All write outputs, receipts, pause markers, and current-node movement must stay branch-local until promotion.

## Surface Refinements
### Execution Root Rule
- Any write-capable action must execute against a resolved execution root.
- The root is determined by:
  - `main` branch => canonical book root
  - derived branch => branch snapshot root
- Query surfaces and execution surfaces must agree on the same root for one action request.

### Branch-Scoped Readiness
- A caller should be able to ask:
  - what is the current scene/section cursor inside branch `X`
  - what scene-phase actions are legal there
  - whether a historical scene is writable inside that branch even when `main` is elsewhere
  - what artifacts already exist inside the branch
  - whether the branch is stale relative to its parent snapshot
- Branch query edge cases are first-class:
  - unknown branch id returns a truthful refusal or empty result, never a fallback to `main`
  - discarded/promoted branches remain queryable for history but are not write-ready
  - branch-local current node is used for readiness and expected-node validation
  - `ScopeSelector(branch_id=...)` lets Nanda query a specific branch without reading branch files directly

### Branch-Scoped Receipts
- Scene-phase and section-range receipts inside a branch must:
  - carry the branch-local `TimelineNodeRef`
  - write to branch-local supervision paths
  - declare artifact status using the shared vocabulary
  - never imply canonical mutation until promotion

## Nanda Impact
- This step is what turns "rewrite an older scene" from a hand-wavy future capability into a truthful engine-owned path.
- Nanda should eventually be able to:
  - inspect `main`
  - choose an old scene or section
  - create an isolated branch for rewrite
  - ask branch-local readiness questions
  - run branch-local scene or section write work
  - compare branch-local results without touching `main`
- This is also the prerequisite for honest author-side parallelism.

## Files Likely Touched
- `src/bookforge/runner.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/execution/scene_sequence.py`
- `src/bookforge/execution/scoped.py`
- `src/bookforge/query/scene_phase.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/branching_store.py`
- `src/bookforge/branching_fork.py`
- `src/bookforge/branching_execution.py`
- `src/bookforge/execution/branch_actions.py`
- `src/bookforge/contracts/`
- `docs/help/workflow.md`
- `docs/help/run.md`
- `docs/help/index.md`

## Tests
- Add branch-scoped writer tests, for example:
  - `tests/test_branch_scene_phase_readiness.py`
  - `tests/test_branch_scene_action_execution.py`
  - `tests/test_branch_section_range_execution.py`
- Required behavior coverage:
  - create a branch from canonical state and run scene readiness against a historical scene while `main` is elsewhere
  - branch-scoped scene execution writes only into the branch snapshot
  - branch-scoped section-range execution can pause and resume without mutating `main`
  - branch-scoped commit produces authoritative artifacts inside the branch snapshot only
  - stale branch parent or stale expected node is detected truthfully
  - `main` remains unchanged after branch-local scene or section execution

## Open Todo
- Fix outline test failures separately from this branch-execution work.
  - Current working tree contains outline-related edits in `src/bookforge/outline.py`, `tests/test_outline_generate.py`, and `tests/test_plan_scene.py`.
  - Do not mix those fixes into `0071` unless they directly block branch-scoped execution tests.

## Definition Of Done
- A derived branch can resolve its own active cursor and scene-phase readiness without consulting canonical `main` cursor truth.
- A derived branch can execute at least one real scene-phase write path and one real section-range write path.
- A historical scene can be rewritten inside a branch even when `main` is currently writing a different chapter/section.
- Branch-local writer execution emits branch-local receipts, pause markers, and produced-artifact records.
- Canonical `main` state remains unchanged until explicit promotion.
- Truthful refusal surfaces exist for stale parent lineage, stale expected node, or invalid branch scope.

## Execution Notes
- Implemented branch-aware workspace/current-node queries and branch-scoped scene-phase readiness.
- Scene-phase request builders and actions now accept `branch_id` and resolve reads/writes through the selected execution root.
- Branch snapshots now include writer-facing material such as `draft`, `prompts`, and context folders needed for branch-local authoring.
- Branch-local `apply_scene_commit` can replace a copied committed scene while preserving `.original` backups; `main` still blocks accidental committed-scene overwrite.
- `write_section` can execute through a branch-local section-range path and passes branch identity down to the section traversal.
- CLI workflow scene-phase commands and `write-section` now accept `--branch-id`.
- Focused non-outline validation passed:
  - `tests/test_branch_execution.py`
  - `tests/test_action_discovery.py`
  - `tests/test_execution_actions.py`
  - `tests/test_scoped_execution.py`
  - `tests/test_scene_phase_readiness.py`
  - `tests/test_scene_action_execution.py`

## Notes
- This step is about isolated authoring roots, not merge semantics.
- It intentionally stops short of:
  - parent-target promotion
  - rebase
  - parallel sibling assembly
- Those belong in the next step because they change merge and lifecycle contracts.

---

## Source 15: `steps/0072-add-parent-target-promotion-rebase-and-parallel-fork-write/step.md`

# 0072 Add Parent-Target Promotion, Rebase, And Parallel Fork Write

Status: completed

## Goal
- Extend the branch model so write-capable branches can merge upward into their parent branch or `main`, support explicit rebase against newer parent snapshots, and enable truthful sibling parallel write execution through fork groups and validation-gated assembly.

## Problem
- `0071` gives us isolated branch-local writer execution roots.
- That is not enough for real authoring workflows.
- The user expectations here are stronger:
  - chapter branches should be able to contain section sub-branches
  - section branches should be able to contain scene branches
  - a scene rewrite branch should be able to promote back into its section parent, not only `main`
  - branches will eventually need incoming changes from their parent
  - some writing work will run in parallel
- The current branch lifecycle is still too narrow:
  - promotion targets `main`
  - branch creation copies from canonical `main`
  - fork-group assembly exists conceptually, but not yet for writer-side branch content
  - rebase does not exist as an explicit supervised capability
- If we do not add parent-target promotion and explicit rebase, nested author branches become dead ends.
- If we allow parallel write branches without a real fork-group assembly/validation discipline, we will recreate hidden race conditions and semantic merge drift.

## Detailed Work
- Generalize branch creation so a branch may derive from a parent branch snapshot, not only canonical `main`.
  - Parent lineage must remain explicit in `BranchManifest`.
  - Branch creation must refuse stale parent snapshots truthfully.
- Add parent-target promotion.
  - Promotion target must be explicit:
    - branch -> parent branch
    - branch -> `main`
  - Promotion should copy validated branch-local state into the target execution root, not assume `main` as the only destination.
  - Receipts must make the target branch explicit.
- Add explicit rebase.
  - Rebase should be an explicit supervised operation, not a silent background mutation.
  - First safe version:
    - detect stale parent snapshot
    - create a refreshed child branch from the newer parent snapshot
    - replay or transplant the scoped branch-local work in a controlled way
    - mark the old branch stale or discarded
  - Do not start with hidden in-place semantic merge.
- Add nested branch hierarchy semantics without hardcoding one topology.
  - Chapter, section, and scene branches are good default roles.
  - The contract should still allow other scoped branch shapes.
  - Parent-child lineage must stay the real source of truth.
- Add write-capable fork-group siblings.
  - Sibling write branches must:
    - share the same parent snapshot revision
    - remain isolated from each other during execution
    - not read sibling outputs mid-run
  - This is the truthful basis for parallel scene or section writing.
- Add writer-side assembly.
  - Sibling branch results must be assembled off-parent, not directly on `main` or the parent branch.
  - Assembly should happen on an assembly branch derived from the shared parent snapshot.
  - Validation must run there before upward promotion.
- Add merge validation for write branches.
  - The first validation pass should focus on merge-level risks such as:
    - stale parent mismatch
    - sibling lineage mismatch
    - branch/fork contamination
    - seam or continuity validation required before promotion
  - Keep semantic prose merge narrow and explicit. Do not promise automatic perfect prose reconciliation.

## Surface Refinements
### Parent-Target Promotion
- Promotion must carry:
  - `source_branch_id`
  - `target_branch_id`
  - `merge_operation`
  - parent snapshot revision
  - validation status at time of promotion
- The execution result must make it clear whether canonical `main` changed or only an intermediate parent branch changed.

### Rebase
- Rebase must be a first-class supervised lifecycle action.
- The first safe contract should answer:
  - what parent revision the branch was created from
  - what parent revision is now current
  - whether the branch is stale
  - whether a refreshed child branch was created
  - what happened to the previous branch
- Rebase must not silently overwrite the old branch's recorded history.

### Parallel Fork Write
- Fork groups must support writer branches, not only outline/materialization branches.
- Required invariants:
  - siblings share one parent snapshot
  - siblings do not read each other during execution
  - assembly happens off-parent
  - upward promotion requires explicit validation status

## Nanda Impact
- This step is what makes multi-level author work practical.
- Nanda should eventually be able to:
  - create a chapter branch
  - create a section branch under it
  - create a scene rewrite branch under that
  - promote upward one layer at a time
  - detect stale parent state and request rebase
  - launch sibling branches for parallel write work
  - inspect assembly and promotion status without reading raw files
- This is also the step that makes future MCP-style execution skills coherent, because the agent can treat branch creation, branch write, rebase, assembly, and promotion as explicit capabilities rather than hidden recovery rituals.

## Files Likely Touched
- `src/bookforge/contracts/branch_manifest.py`
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/scope_selector.py`
- `src/bookforge/branching_store.py`
- `src/bookforge/branching_fork.py`
- `src/bookforge/branching_lifecycle.py`
- `src/bookforge/branching_execution.py`
- `src/bookforge/execution/branch_actions.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/query/actions.py`
- `docs/help/workflow.md`
- `docs/help/index.md`

## Tests
- Add nested-branch and rebase tests, for example:
  - `tests/test_branch_parent_target_promotion.py`
  - `tests/test_branch_rebase.py`
  - `tests/test_parallel_fork_write.py`
- Required behavior coverage:
  - create a chapter branch from `main`, then section branch from chapter branch, then scene branch from section branch
  - promote a scene branch into its section parent without mutating `main`
  - promote a section branch into its chapter parent without mutating `main`
  - detect stale parent revision when a parent branch advances
  - perform explicit rebase or refreshed-child creation
  - create sibling writer branches in one fork group and refuse sibling reads during execution
  - assemble sibling results on an assembly branch before promotion
  - refuse promotion when validation has not passed

## Definition Of Done
- A branch may be created from a parent branch snapshot, not only from canonical `main`.
- A branch may promote into its parent branch or into `main`, with truthful receipts for the actual target.
- Stale parent snapshots are detected and surfaced as a real lifecycle/integrity condition.
- An explicit rebase capability exists and does not silently overwrite existing branch history.
- Sibling writer branches can execute in parallel under one fork group without shared-state mutation.
- Assembly and promotion remain validation-gated and off-parent until approved.

## Progress
- Implemented first conservative nested-branch primitives:
  - branch creation can copy from a parent branch snapshot instead of always copying from `main`
  - scene branches can promote into an explicit parent branch without mutating `main`
  - rebase can create a refreshed child branch from the current parent snapshot and discard the old branch history-preservingly
- Added branch/rebase action builders for the programmatic execution surface.
- Added tests covering nested branch promotion and refreshed-child rebase.
- Exposed the conservative lifecycle primitives through the workflow CLI:
  - `create-branch`
  - `create-assembly-branch`
  - `discard-branch`
  - `promote-branch`
  - `rebase-branch`
  - `validate-assembly-branch`
  - `record-assembly-validation`
- Added first writer-side assembly behavior:
  - assembly branches are created off-parent
  - sibling branches are required to share one parent snapshot
  - parent staleness checks work for `main` and parent branches
  - scoped sibling draft scene files are staged into the assembly branch snapshot for validation
  - deterministic staging validation can mark the assembly branch `assembled_pending_promotion`
- Validated full conservative fork-group path:
  - sibling writer branches stage scoped files into an assembly branch
  - deterministic validation marks the assembly branch promotion-ready
  - validated assembly promotion copies staged outputs into `main`
- Deferred follow-up:
  - richer semantic seam/continuity merge checks before promotion
  - higher-level sibling execution launch helpers for Nanda convenience

## Notes
- This step is where branch hierarchy becomes operational, not just conceptual.
- The first implementation should stay conservative:
  - explicit actions
  - explicit validation
  - no hidden semantic prose merge promises
- Automatic prose-level reconciliation may exist later, but this step should first make the isolation, lineage, and merge surfaces truthful.

---

## Source 16: `steps/0075-extract-appearance-setting-and-context-refinement-surfaces/step.md`

# 0075 Extract Appearance, Setting, And Context Refinement Surfaces

Status: completed

## Goal
- Make character appearance, scene background/setting, and prior-stage context refinement explicit, queryable BookForge projection layers that Nanda can use without inferring truth from prose, prompt logs, or hidden runner side effects.

## Problem
- Character appearance already exists in the runtime, but it is currently too easy for it to behave like an incidental helper inside writer execution.
- The last observed state suggested at least one bug in the appearance flow, likely around stale, missing, or incorrectly refreshed projections.
- Scene setting/background is also under-specified:
  - prose may mention concrete background details that should be tracked
  - the author LLM may also need a distinct turn to deliberately establish or refine the scene's visual/background setting before prose or seam repair
- Thought signatures from earlier workflow stages preserve useful planning context, but they are not currently modeled as a controlled refinement input for later scene-phase actions.
- If these remain implicit, Nanda will eventually have to guess:
  - whether a character's visible appearance is current
  - whether a scene has a usable background/setting projection
  - which prior T1 planning signatures are safe and relevant context for the current author move

## Detailed Work
- First implementation slice:
  - added query modules for appearance, scene setting, and prior T1 thought-context projections
  - added a deterministic `refresh_character_appearance_projection` execution action that writes a derived scene/cast projection artifact and produced-artifact receipt
  - kept projection output non-canonical and non-mutating; existing character state is read, not rewritten
  - added action discovery details so Nanda can see whether appearance projection can run for the selected scene scope
- Second implementation slice:
  - added `draft_scene_setting_projection` to record author-provided setting/background intent as a `provisional` artifact
  - added `extract_scene_setting_from_prose` to record prose-derived setting/background observations as a `derived` artifact
  - kept both actions non-canonical and non-mutating
  - added action discovery for both setting projection actions
  - `extract_scene_setting_from_prose` refuses when no scene prose exists instead of inventing source context
- Third implementation slice:
  - added `get_scene_context_projection(...)` as a compact aggregate query over appearance, setting, and prior T1 thought-context projections
  - the aggregate reports availability counts and statuses without making Nanda stitch projection layers together manually
- Fourth implementation slice:
  - added compact `scene_context_projection` snapshots to downstream scene-phase `ExecutionResult.details`
  - covered `generate_continuity_pack`, `write_scene_prose`, `state_repair_scene_patch`, `lint_scene_prose`, `repair_scene_prose`, and `apply_scene_commit`
  - kept the receipt honest by recording `used_as_prompt_input: false`
  - this means the action receipt exposes what appearance/setting/thought context was observable at execution time, but does not claim the prompt consumed that projection bundle
- Audit the current character appearance path.
  - Likely starting points:
    - `src/bookforge/characters.py`
    - `src/bookforge/pipeline/scene.py`
    - `src/bookforge/runner.py`
    - any helpers named like `refresh_appearance_projections(...)`
    - any helpers named like `_ensure_character_appearance_current(...)`
  - Determine whether current appearance artifacts are:
    - authoritative character truth
    - derived scene projections
    - provisional LLM outputs
    - diagnostic only
  - Current implementation note:
    - committed `appearance_updates` now mark `appearance_projection_pending: true`
    - this prevents a failed/stalled legacy appearance refresh from being misreported as current appearance projection truth
    - `list_appearance_projection_views(...)` reports this state as stale/provisional until refresh clears the pending flag
- Add an appearance projection query surface.
  - Candidate module:
    - `src/bookforge/query/appearance.py`
  - The query should be book-rooted and narrowable by:
    - `book_id`
    - optional `chapter`
    - optional `section`
    - optional `scene`
    - optional `character_id`
    - optional `branch_id`
  - It should return structured data, not raw file paths only.
  - It should report artifact status using the shared vocabulary:
    - `authoritative`
    - `provisional`
    - `derived`
    - `diagnostic`
- Add an extracted appearance scene-phase action.
  - Candidate action:
    - `refresh_character_appearance_projection`
  - The first action should be scene/cast scoped.
  - It should read:
    - scene card cast
    - character state
    - existing appearance data
    - current timeline node
  - It should emit explicit `ProducedArtifactReceipt` records.
  - It should not silently mutate canonical character state unless a later explicit apply/promote path exists.
- Add a scene background/setting projection surface.
  - Candidate query module:
    - `src/bookforge/query/setting.py`
  - Candidate execution actions:
    - `extract_scene_setting_from_prose`
    - `draft_scene_setting_projection`
  - `extract_scene_setting_from_prose` should read already-produced prose and derive setting/background details from what is actually on page.
  - `draft_scene_setting_projection` should be a distinct author-LLM turn that can establish intended scene background before prose generation or seam repair.
  - Both paths must label outputs truthfully:
    - prose-derived extraction is `derived`
    - author-drafted setting projection is `provisional` until accepted by a later commit/apply action
  - Current implementation note:
    - `draft_scene_setting_projection` records structured caller/author-provided setting details; it does not call an LLM internally yet
    - `extract_scene_setting_from_prose` reads existing scene prose and records a derived artifact; structured extraction can be supplied by a caller/author worker, otherwise the artifact remains conservative and may report no structured setting
    - Decision for this step: Nanda/the author worker supplies structured setting payloads; an internal BookForge author-LLM setting draft/extract turn is deferred to a later explicit action
- Add context refinement through prior T1 thought signatures.
  - Treat T1 thought signatures from previous workflow stages as context-management artifacts, not source of truth.
  - Candidate query surface:
    - `src/bookforge/query/thought_context.py`
  - Candidate refinement behavior:
    - select relevant prior T1 signatures by `TimelineNodeRef`, phase, scene, and workflow family
    - expose them as candidate context inputs for the next scene-phase action
    - record which signatures were included in the prompt package or execution receipt
  - Current implementation note:
    - scene-phase receipts now record selected prior T1 signatures in `scene_context_projection.thought_context`
    - receipt snapshots explicitly say the projection was not used as prompt input yet
    - later prompt injection must flip `used_as_prompt_input` only when the projection payload is actually assembled into the model request
  - This is essentially reuse of previous planning work.
  - It must not replace explicit execution receipts, state surfaces, or artifact truth.
- Thread all three surfaces through the same coordinate model.
  - `TimelineNodeRef`
  - `ScopeSelector`
  - branch id
  - fork group id where relevant
  - artifact status
- Add readiness semantics.
  - A caller should be able to ask:
    - is appearance projection available for this scene/cast
    - is it stale relative to current character state or current scene node
    - is setting/background available
    - was the setting extracted from prose or drafted by the author LLM
    - which prior T1 thought signatures are available as refinement context
    - whether any of these are legal inputs for the next scene-phase action
  - Current implementation note:
    - `get_scene_context_projection(...)` provides the first aggregate availability surface for these projection layers
- Keep this as projection-layer work, not canonical mutation work.
  - 0075 should not solve character-state promotion, inventory promotion, or final scene commit.
  - It should make projections visible, typed, and safe to reason about.

## Surface Sketch
### Appearance Projection
- Minimum fields:
  - `book_id`
  - `selector`
  - `node`
  - `character_id`
  - `character_name`
  - `appearance_status`
  - `artifact_status`
  - `source_artifacts`
  - `staleness_reason`
  - `visible_scene_details`
  - `last_refreshed_node`

### Scene Setting Projection
- Minimum fields:
  - `book_id`
  - `selector`
  - `node`
  - `setting_status`
  - `artifact_status`
  - `source_mode`
  - `source_mode` values:
    - `prose_extracted`
    - `author_drafted`
    - `outline_derived`
    - `missing`
  - `location_id`
  - `location_label`
  - `background_details`
  - `sensory_anchors`
  - `continuity_constraints`
  - `source_artifacts`

### Thought Context Refinement
- Minimum fields:
  - `book_id`
  - `selector`
  - `node`
  - `candidate_signatures`
  - `selected_signatures`
  - `phase_id`
  - `turn_id`
  - `context_role`
  - `context_role` values:
    - `planning_reuse`
    - `constraint_reminder`
    - `style_or_voice_reference`
    - `diagnostic_context`
  - `artifact_status`
  - `limitations`
- Required limitation:
  - thought signatures are context aids only
  - execution receipts remain the truth of what happened

## Files Likely Touched
- `src/bookforge/characters.py`
- `src/bookforge/pipeline/scene.py`
- `src/bookforge/runner.py`
- `src/bookforge/query/__init__.py`
- `src/bookforge/query/appearance.py`
- `src/bookforge/query/setting.py`
- `src/bookforge/query/thought_context.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/execution/__init__.py`
- `src/bookforge/contracts/`
- `src/bookforge/llm/storage.py`
- `src/bookforge/llm/signatures.py`
- `docs/help/workflow.md`
- `docs/help/index.md`

## Tests
- Add appearance projection tests, for example:
  - `tests/test_appearance_query.py`
  - `tests/test_appearance_projection_action.py`
- Add setting/background tests, for example:
  - `tests/test_scene_setting_query.py`
  - `tests/test_scene_setting_actions.py`
- Add thought-context selection tests, for example:
  - `tests/test_thought_context_query.py`
- Required behavior coverage:
  - appearance projection reports missing state without crashing
  - appearance projection detects stale state when character state revision or node changes
  - appearance projection emits explicit artifact status
  - scene setting extraction from prose is `derived`
  - author-drafted setting projection is `provisional`
  - thought-signature context selection filters to relevant prior T1 signatures
  - thought signatures are never reported as authoritative execution truth
  - readiness surfaces can report appearance, setting, and thought-context availability without starting execution
  - scene-phase execution receipts record projection availability and truthfully report whether the projection was used as prompt input

## Definition Of Done
- A caller can query character appearance projection status for a book, scene, or character without inspecting raw files.
- A caller can tell whether appearance data is current, stale, missing, derived, provisional, or authoritative.
- A caller can trigger a scene/cast-scoped appearance projection action without accidentally mutating canonical character truth.
- A caller can query scene background/setting status independently from prose generation.
- A caller can distinguish prose-extracted setting details from author-drafted setting projections.
- A caller can discover relevant prior T1 thought signatures as optional refinement context for a scene-phase action.
- Execution receipts record whether appearance, setting, or thought-context artifacts were used as prompt inputs or were only observable as diagnostic projection context.
- Nanda can present these capabilities honestly in the author pane using BookForge query results instead of persona claims.

## Notes
- This step is intentionally separate from 0070.
- 0070 is about segmenting the write loop into phase-shaped actions.
- 0075 is about projection-layer quality and context reuse around those actions.
- Appearance and setting should eventually inform continuity, prose writing, seam repair, and lint/repair, but they should not be hidden inside those phases.
- The scene background/setting work should support both:
  - extraction from prose already written
  - a distinct author LLM turn that drafts intended background/setting before prose or seam repair
- Prior T1 thought signatures should be treated as controlled context reuse.
  - They can reduce repeated planning work.
  - They can preserve author intent between graph nodes.
  - They cannot replace state surfaces, issue tickets, or produced-artifact receipts.

---

## Source 17: `steps/0080-add-outline-lineage-audit-and-recovery-briefing/step.md`

# 0080 Add Outline Lineage Audit And Recovery Briefing

Status: completed

## Goal
- Add read-only BookForge query surfaces that localize outline lineage contamination by chapter and section before any repair or author mutation is attempted.
- Give Nanda enough structured evidence to explain, inspect, and block unsafe author actions without relying on the human operator to notice outline-pass bleed manually.

## Problem
- BookForge can currently classify `veiled_ledger_b1` as `chimera_risk`, but the classification is too global to be operational.
- The current integrity verdict exposes:
  - `stale_section_drafts_present`
  - first `overscoped_recovery`
- That is not enough for an author agent to answer:
  - which sections disagree
  - which artifact families disagree
  - where the first technical divergence starts
  - where the first reader-visible story splice appears
  - which candidate source lineage is coherent
  - which repair paths are safe to propose
- The Veiled Ledger failure class was not caught by the engine early enough.
  - A full deep outline pass and section-local outline drafts coexisted.
  - Recovery continued by consuming a broader or different outline source than the active section-local workflow expected.
  - The mutable compatibility outline became mixed.
  - The author/operator had to infer the failure from prose and artifact archaeology.
- That makes Nanda unsafe as an author supervisor. If the engine only says "chimera risk" without evidence, the author pane can either overclaim or underreact.

## Design Rule
- This step is read-only.
- Do not add repair mutation yet.
- Do not quarantine, overwrite, restore, promote, or rebuild canonical state in this story.
- The output of this story is structured diagnosis and recovery candidate briefing only.
- Mutation belongs in a later explicit recovery story after the audit surface exists and has tests.

## Detailed Work
- Completed implementation:
  - added read-only outline lineage audit surfaces
  - added section-level lineage matrix rows with artifact hashes, field diffs, scene-count deltas, and character-cohort deltas
  - added stale outline artifact inventory
  - added non-mutating repair candidate briefing
  - threaded localized lineage details into integrity issues and emitted issue tickets
  - blocked unsafe main-branch authoring/write/seam actions when lineage chimera is detected
  - added operator-facing CLI projections for audit, matrix, stale artifacts, and repair candidates
- Add an outline lineage audit query module.
  - Candidate module:
    - `src/bookforge/query/outline_lineage.py`
  - Candidate public functions:
    - `get_outline_lineage_audit(workspace, book_id, *, branch_id="main")`
    - `get_section_lineage_matrix(workspace, book_id, *, chapter_id=None, section_id=None, branch_id="main")`
    - `get_stale_outline_artifact_inventory(workspace, book_id, *, branch_id="main")`
    - `get_outline_repair_candidates(workspace, book_id, *, branch_id="main")`
- Build a section-level lineage matrix.
  - Each row should identify one chapter/section scope.
  - Minimum row fields:
    - `chapter_id`
    - `section_id`
    - `section_title`
    - `declared_source_run_id`
    - `latest_outline_run_id`
    - `workflow_family`
    - `materialized_status`
    - `candidate_artifacts`
    - `normalized_section_hashes`
    - `normalized_scene_list_hashes`
    - `differing_fields`
    - `scene_count_delta`
    - `character_cohort_delta`
    - `artifact_mtimes`
    - `suspected_contamination_class`
    - `recommended_safe_next_action`
- Compare these artifact families when present:
  - immutable declared outline run artifacts under `outline/pipeline_runs/<source_run_id>/`
  - latest outline run artifacts under `outline/pipeline_runs/<latest_run_id>/`
  - frozen chapter projections under `outline/chapters/ch_###.json`
  - mutable compatibility outline under `outline/outline.json`
  - section-local draft artifacts under `outline/section_drafts/ch_###_sec_###_phase03.json`
  - workflow registry and snapshot views:
    - `outline/snapshot_registry.json`
    - `outline/outline.thin.json`
    - `outline/outline.index.json`
    - `outline/outline.toc.json`
    - `outline/outline.appendix.json`
- Normalize section comparison before hashing.
  - Include:
    - section id
    - title
    - intent
    - end condition
    - scene ids
    - scene summaries
    - scene outcomes
    - scene character ids
    - scene thread ids
    - handoff refs
    - terminal echo fields
  - Exclude volatile fields unless needed for diagnostics:
    - mtimes
    - file paths
    - generated report timestamps
    - diagnostics-only metadata
- Add character cohort detection.
  - Detect incompatible character id families that occupy the same narrative role or scope.
  - The first implementation should flag:
    - multiple protagonist ids in the same book lineage
    - character cohorts that switch within a chapter
    - scene casts that use ids absent from the chosen candidate source
    - registry characters that are not referenced by the selected coherent lineage
  - For Veiled Ledger, the surface should be able to show:
    - `char_rhea / char_vex / char_artie`
    - `rhea_mercer / vance_harrow / unit_734`
    - chapter 3 as the visible splice zone
- Add artifact inventory diagnostics.
  - Return a structured list of stale or competing outline artifacts with:
    - path
    - artifact family
    - artifact status
    - mtime
    - size
    - inferred chapter/section scope
    - inferred source run if available
    - hash
    - whether it is safe to consume as canonical
- Add repair candidate briefing, still read-only.
  - Candidate recommendations should be explicit and non-mutating:
    - `inspect_only`
    - `choose_recovery_anchor`
    - `create_recovery_branch_from_selected_lineage`
    - `restore_affected_sections_from_declared_source_run`
    - `restore_affected_sections_from_frozen_chapter_projection`
    - `quarantine_stale_section_drafts`
    - `rebuild_snapshot_registry_from_selected_source`
    - `shelf_book`
  - Each candidate must include:
    - required human decision
    - expected writable scope for the later repair story
    - affected section set
    - source artifact family
    - risk level
    - why the action is blocked or allowed
- Integrate the audit result into integrity reporting.
  - `get_integrity_verdict(...)` should stop breaking after the first overscoped section.
  - It should include enough `IntegrityIssue.details` for Nanda to link an issue to a localized matrix row.
  - `IssueTicket.details` should preserve:
    - affected scopes
    - first technical divergence
    - first visible story divergence if detected
    - candidate artifact families
    - recommended safe next action
  - If this requires extending `IntegrityIssue`, do it with backward-compatible defaults.
- Add legal-action gating for contaminated books.
  - Action discovery should treat `chimera_risk` with lineage conflicts as blocking for:
    - direct main `write-section`
    - direct main `advance-section`
    - direct main `seam-chapter`
    - direct main `finalize-chapter`
    - direct main scene rewrite or repair
  - Allowed actions should be read-only diagnostics and branch/recovery preparation only.
  - If a mutation action remains technically available for compatibility, its refusal reason must say why it is unsafe.
- Add a minimal CLI/operator surface if useful for local testing.
  - Candidate commands:
    - `bookforge workflow outline-lineage-audit --book <book>`
    - `bookforge workflow section-lineage-matrix --book <book> [--chapter N] [--section N]`
    - `bookforge workflow outline-repair-candidates --book <book>`
  - CLI output should be a readable projection of the query objects.
  - The query functions are the real contract; CLI commands are convenience wrappers.

## Nanda Contract Notes
- Nanda should call the lineage audit automatically when:
  - integrity status is `chimera_risk`
  - the user mentions chimera, bleed, outline pass, section drafts, wrong chapter, wrong characters, or "what went wrong"
  - the user asks about content in a contaminated book or chapter
- Nanda should not claim exact localization until this audit surface exists.
- Before this step is implemented, acceptable author wording is:
  - "BookForge reports chimera risk and stale section drafts, but it does not yet expose enough evidence to identify every affected section."
- After this step is implemented, acceptable author wording is:
  - "BookForge reports chimera risk. I inspected outline lineage. The affected scopes are ..., the first technical divergence is ..., and the safe next action is ..."
- Nanda should render:
  - global verdict
  - affected section matrix
  - artifact inventory
  - recommended safe next actions
  - blocked mutation actions

## Files Likely Touched
- `src/bookforge/query/outline_lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/__init__.py`
- `src/bookforge/contracts/` if a typed audit contract is introduced
- `src/bookforge/supervision/emit.py`
- `src/bookforge/cli.py`
- `docs/help/workflow.md`
- `docs/help/index.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/index.md`

## Tests
- Add focused lineage audit tests:
  - `tests/test_outline_lineage_audit.py`
  - `tests/test_section_lineage_matrix.py`
- Required fixtures:
  - healthy single-lineage book
  - stale section drafts present but non-canonical
  - mutable outline differs from frozen chapter projection
  - declared source run differs from latest run
  - mixed character cohort within a chapter
  - Veiled Ledger-style section-local draft vs frozen chapter projection conflict
- Required assertions:
  - healthy books return `healthy` and no affected scopes
  - audit returns every affected section, not just the first mismatch
  - matrix rows include hash, differing fields, artifact mtimes, and recommended safe action
  - character cohort switch is detected and localized
  - integrity tickets include localized details
  - legal action discovery blocks unsafe main mutations while allowing inspection/branch setup
  - no test mutates canonical book state

## Definition Of Done
- BookForge exposes a read-only outline lineage audit query surface.
- BookForge exposes a section-level lineage matrix that localizes outline-source disagreement.
- BookForge exposes stale outline artifact inventory.
- BookForge exposes non-mutating repair candidates.
- `get_integrity_verdict(...)` reports localized lineage details instead of stopping at the first overscoped section.
- Nanda can distinguish:
  - global chimera status
  - affected scopes
  - suspected artifact source
  - first technical divergence
  - visible story splice zone
  - blocked unsafe actions
  - safe next diagnostic or recovery-prep action
- Veiled Ledger can be inspected without raw filesystem archaeology.
- No repair mutation is implemented in this step.

## Executed Validation
- Focused lineage/action suite:
  - `python -m pytest -o addopts='' tests/test_outline_lineage_audit.py tests/test_query_integrity.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0080_focus`
- Broader query/action/supervision regression:
  - `python -m pytest -o addopts='' tests/test_outline_lineage_audit.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_supervision_emit.py tests/test_action_discovery.py tests/test_scoped_execution.py --basetemp=.pytest_tmp_0080_regression`
- Full regression:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0080_full`
  - result: `304 passed`
- Veiled Ledger smoke checks:
  - `bookforge workflow outline-lineage-audit --book veiled_ledger_b1`
  - `bookforge workflow section-lineage-matrix --book veiled_ledger_b1 --chapter 3`
  - `bookforge workflow legal-actions --book veiled_ledger_b1 --chapter 3 --section 3`

## Explicit Non-Goals
- Do not repair Veiled Ledger in this story.
- Do not delete or quarantine stale artifacts in this story.
- Do not rebuild `outline.json`.
- Do not rebuild snapshot registry.
- Do not rewrite prose.
- Do not run seam repair.
- Do not promote any recovery branch.
- Do not make Nanda infer lineage from prose when BookForge can expose artifact truth.

## Follow-On Work
- Add an explicit branch-scoped recovery-import action after this read-only audit is stable.
- Add repair candidate execution with backup/quarantine receipts.
- Add snapshot registry rebuild from a selected source lineage.
- Add branch-local validation comparing repaired candidate state against the lineage audit.
- Add Nanda author planner support for automatic audit queries and grounded repair briefing.

---

## Source 18: `steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`

# 0081 Add Author-Operable Timeline Recovery And Story-Weaving Primitives

Status: in_progress

## Goal
- Add branch-first BookForge mutation primitives that let Nanda compose timeline recovery, retcon, redraft, and downstream story-weaving plans without requiring a bespoke BookForge command for every failure class.
- Make "repair" mean full timeline recovery:
  - correct outline lineage active
  - invalid artifacts removed from active discovery paths or quarantined
  - invalid state/projection data removed from canonical datasets
  - impacted prose invalidated and redrafted
  - branch validated
  - promotion to `main` includes replacements and removals
  - `chimera_risk` clears

## Problem
- `0080` made chimera and outline lineage contamination visible, but it is read-only.
- Nanda can now identify affected scopes and candidate recovery anchors, but it cannot yet execute the repair safely.
- The current engine has branch primitives, scene write primitives, outline lineage audit, and promotion primitives, but it lacks composable recovery tools for:
  - selecting a trusted timeline source
  - normalizing outline artifacts inside a branch
  - quarantining stale or polluted artifacts
  - invalidating affected prose/state outputs
  - rebuilding timeline-derived state
  - redrafting impacted scopes
  - validating that the recovered branch is healthy
- A monolithic command like `fix_veiled_ledger_chimera` would solve one incident but not the long-term author workflow.
- The author agent needs reusable tools it can reason over and sequence.

## Boundary With Nanda
- BookForge owns mutation, scope enforcement, receipts, validation, artifact cleanup, and promotion safety.
- Nanda owns author-level reasoning:
  - diagnosis from multiple surfaces
  - impact report creation
  - strategy selection
  - task sequencing
  - human approval flow
  - explanation to the user
- Nanda should produce a first-class `book_timeline_impact_report_v1` before requesting mutation.
- `book_timeline_impact_report_v1` is Nanda-owned, but BookForge must expose enough evidence and tools for it to be truthful.
- Expected impact report fields:
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
- BookForge should accept the chosen recovery anchor and scoped execution requests. It should not need to parse or own the whole impact report.

## Nanda Decision-Layer Alignment
- Nanda can implement read-only and shadow-mode reasoning now using existing surfaces from `0060`, `0070`, `0075`, `0080`, and the partial `0081` recovery slice.
- Full non-shadow timeline recovery requires BookForge to expose stable primitive receipts and readiness metadata so Nanda can compare candidate actions without filesystem inference.
- BookForge must provide:
  - stable action names through `legal_next_actions`
  - stable request/result schemas for recovery/story-weaving primitives
  - readiness queries for recovery/story-weaving work, not only scene-phase work
  - approval-required metadata for:
    - anchor selection
    - destructive cleanup/quarantine
    - broad recovery radius
    - promotion to `main`
  - postcondition receipts that report:
    - affected scopes
    - produced artifacts
    - deleted or quarantined artifacts
    - integrity delta
    - recommended next legal action
  - impact-report-friendly blast-radius query surfaces for:
    - prose invalidation
    - state invalidation
    - series/continuity invalidation
    - projection invalidation
    - downstream redraft candidates
- Until those surfaces exist for a primitive, Nanda must treat that primitive as shadow-mode or human-approved only.
- BookForge should not encode Nanda's decision policy; it should expose enough truthful state for Nanda to run that policy.

## Design Rules
- Recovery mutation is branch-first.
- No recovery action mutates `main` directly when the book is contaminated.
- Every recovery branch declares:
  - parent `TimelineNodeRef`
  - selected source lineage or recovery anchor
  - affected writable scopes
  - expected quarantine/removal policy
  - salvage policy
- Source lineage selection is explicit.
- A recovery action must refuse if:
  - the selected anchor does not match the audit evidence
  - requested scope is wider than approved
  - required backups or quarantine receipts cannot be written
  - branch parent is stale
  - active fork/branch descendants would be invalidated without explicit handling
- Promotion is not just copy-in.
  - It must support additions, replacements, removals, and quarantine receipts.
  - Invalid files must leave active canonical discovery paths.
- Salvage is non-canonical unless explicitly promoted.
  - Contaminated prose can be included as reference for redraft only when requested.
  - Salvage material must never become authoritative continuity/state input by accident.
- Healthy timeline and good story are separate gates.
  - Timeline validation clears structural risk.
  - Seam repair, style polish, or author revision can remain separate follow-up work.

## Proposed Primitive Tool Surface
- Readiness/query primitives:
  - `get_recovery_plan_readiness(workspace, book_id, *, branch_id, impact_report_ref=None)`
  - `get_recovery_branch_health(workspace, book_id, *, branch_id)`
  - `get_recovery_blast_radius(workspace, book_id, *, branch_id)`
  - `get_scope_invalidation_preview(workspace, book_id, *, branch_id, scope)`
  - `get_salvage_candidates(workspace, book_id, *, scope)`
- Execution primitives:
  - `select_recovery_anchor`
  - `create_recovery_branch`
  - `quarantine_artifacts`
  - `normalize_outline_scope`
  - `invalidate_scope_outputs`
  - `rebuild_state_scope`
  - `redraft_scope`
  - `validate_recovery_branch`
  - `promote_recovery_branch`
- CLI wrappers should be convenience only.
  - The Python action/query surface is the contract Nanda should compose.

## Current Implementation Slice
- Implemented recovery contracts:
  - `RecoveryAnchor`
  - `RecoveryScope`
  - `RecoveryReceipt`
  - `RecoveryBranchHealth`
- Implemented read/query surfaces:
  - `get_recovery_plan_readiness`
  - `get_recovery_branch_health`
  - `get_recovery_blast_radius`
  - `get_scope_invalidation_preview`
  - `get_state_rebuild_preview`
  - `get_salvage_candidates`
- Implemented branch-first execution primitives:
  - `create_recovery_branch`
  - `quarantine_artifacts`
  - `normalize_outline_scope`
  - `invalidate_scope_outputs`
  - `rebuild_state_scope`
  - `redraft_scope`
  - `validate_recovery_branch`
  - `promote_recovery_branch`
- Implemented legal-action discovery for the recovery sequence.
- Implemented CLI wrappers for the implemented query/action primitives.
- Implemented initial approval/next-action metadata on recovery discovery and health surfaces.
- Recovery receipts now include status-aware postcondition snapshots with:
  - branch health status after the action
  - outline lineage status after the action
  - completed and remaining required receipts
  - blockers/warnings after the action
  - recommended next recovery action
  - approval-required metadata
  - canonical-change status for branch-local mutation
- Promotion now honors branch recovery removal receipts before copying branch snapshot data into the target.
- Recovery branches materialize outline evidence directories that normal rerun branches intentionally omit:
  - `outline/pipeline_runs`
  - `outline/section_drafts`
  - latest outline pointer/summary files when present
- Scope invalidation preserves the pre-normalization scene range so a normalized one-scene section cannot accidentally leave a stale extra scene file active.
- State rebuild now quarantines branch-local state/projection artifacts and rebuilds a clean outline-derived baseline before validation.
- Redraft now prepares normalized affected sections as branch-local frozen sections and invokes the existing scoped section writer in the recovery branch.
- Validation now requires `rebuild_state_scope` and `redraft_scope` before a recovery branch can become healthy.
- Quarantine now uses hashed fallback quarantine paths when deep Windows paths exceed practical filesystem limits while preserving original source paths in receipts.
- Recovery blast-radius now categorizes impact-report-friendly candidate artifacts into prose, state, continuity, projection, and series families.
- Recovery promotion results now include canonical postconditions with pre/post outline lineage status, pre/post integrity status, planned/applied removals, and whether `main` cleared chimera risk.
- Recovery validation now blocks branch promotion when branch-local character index/state artifacts contain character IDs that are absent from the normalized outline.
- Recovery validation now blocks branch promotion when affected chapter summaries, setting projections, or appearance projections reference non-outline character IDs or carry stale embedded branch coordinates.
- Recovery validation now blocks branch promotion when durable inventory/plot-device registries and indexes retain non-outline character refs, stale embedded branch coordinates, or index entries that no longer exist in their registries.
- Recovery validation now blocks branch promotion when continuity packs, continuity history, bible/last-excerpt text, or affected chapter seam reports retain non-outline character/thread refs or stale embedded branch coordinates.

## Remaining Implementation
- Extend blast-radius surfaces with downstream dependency tracing after redraft.
- Add approval-required metadata to all destructive or broad-scope primitives.
- Expand validation beyond outline lineage to state/projection families:
  - semantic continuity validation beyond ghost-character, thread-reference, and stale-branch checks
  - semantic validation for inventory/deep state beyond ghost-character and index-consistency checks
  - semantic validation for locations/settings beyond stale branch and ghost-character checks
  - semantic validation for chapter summaries beyond ghost-character checks
  - semantic validation for appearance/setting projections beyond stale branch and ghost-character checks
- Add richer downstream invalidation detection after redraft.
- Add Veiled Ledger-size multi-chapter fixture coverage.

## Detailed Work
- Add recovery contracts.
  - Candidate contracts:
    - `RecoveryAnchor`
    - `RecoveryScope`
    - `RecoveryPlanReceipt`
    - `ArtifactQuarantineReceipt`
    - `ScopeInvalidationReceipt`
    - `TimelineNormalizationReceipt`
    - `RecoveryBranchHealth`
  - Every contract must carry `TimelineNodeRef`, branch id, scope, and artifact status.
- Add recovery branch creation.
  - Create a derived branch with workflow family `recovery_import`.
  - Record selected anchor:
    - declared source run
    - frozen chapter projection
    - manual hybrid
    - shelf/no-op
  - Record affected scope set.
  - Record salvage policy:
    - `none`
    - `reference_only`
    - `explicit_reuse_required`
- Add artifact quarantine.
  - Move or mark invalid artifacts out of active branch discovery paths.
  - Preserve enough evidence for audit.
  - Emit quarantine receipts.
  - Initial families:
    - `outline/section_drafts`
    - mutable outline compatibility views
    - stale outline projections
    - affected draft prose
    - affected state/projection files
- Add outline normalization.
  - Rebuild branch-local outline artifacts for selected scopes from the chosen anchor.
  - Ensure branch-local `outline.json`, frozen chapter projections, section views, thin/toc/index/appendix views, and source lineage pointers agree.
  - Do not leave mixed outline data active in the branch.
- Add output invalidation.
  - Mark affected prose/state/summary/projection outputs stale or quarantine them before redraft.
  - Preserve original prose as historical material.
  - Do not let invalidated outputs feed new state or prose as authoritative input.
- Add state rebuild.
  - Rebuild branch-local state from normalized outline and valid prior canonical state.
  - Initial scope should include:
    - characters
    - continuity
    - locations/settings
    - inventory/deep state where represented
    - chapter summaries
    - phase history/projection indexes
    - appearance and setting projections when present
  - If a state family cannot be rebuilt yet, emit a blocking ticket instead of pretending it is clean.
  - Current implementation uses a conservative branch-local full-book context reset because state data is not yet event-sourced enough for safe partial rollback.
  - Current implementation rebuilds:
    - `state.json`
    - character index/state files from normalized outline characters
    - empty bible and last excerpt context
    - durable item/plot-device registries
  - Current implementation quarantines active branch copies of:
    - old `state.json`
    - character state/index files
    - affected chapter summaries
    - affected settings/appearance projections
    - affected scene phase-history artifacts
    - durable-state context files
- Add scoped redraft.
  - Let Nanda request redraft by chapter, section, or scene.
  - Use existing branch-scoped write actions where possible.
  - Preserve original prose under a non-canonical artifact status.
  - Allow explicit salvage reference injection without treating salvage as truth.
  - Current implementation supports branch-local redraft for affected recovery scopes from the recovery manifest.
  - Current implementation prepares each normalized affected section as frozen/writable, then delegates to the existing scoped section writer.
  - Current implementation does not yet support explicit salvage reference injection.
- Add validation.
  - Recovery branch health must prove:
    - no `chimera_risk`
    - no stale active outline artifacts
    - no source run mismatch
    - normalized outline hashes agree across active views
    - state/projection data does not contain invalid timeline entities
    - impacted prose has been regenerated or explicitly marked unwritten
    - legal actions are unblocked for the recovered scope
  - Validation should emit actionable issues rather than a generic failure.
- Add promotion.
  - Promotion applies additions, replacements, removals, and quarantine markers.
  - Promotion refuses if validation is stale or failed.
  - Promotion emits canonical reconciliation and verifies `main` health after merge.

## Edge Cases
- A contaminated section can contain prose worth salvaging, but salvage is reference-only unless explicitly promoted.
- A downstream chapter can be structurally clean but continuity-invalid because upstream facts changed.
- State can be polluted even when outline hashes match.
- A repair can expose new impacts after redraft; validation must be iterative.
- Multiple anchors can be internally coherent but imply different books; Nanda must ask the human which timeline is correct.
- Active branches or fork groups derived from polluted `main` must be blocked, rebased, or discarded.
- Promotion must remove invalid files, not only overwrite valid replacements.
- A branch can be timeline-healthy while the prose still needs seam repair or style revision.
- Rebuilding a scope may require downstream invalidation if continuity dependencies cross the requested boundary.

## Files Likely Touched
- `src/bookforge/contracts/`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/outline_lineage.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/execution/recovery_actions.py` or equivalent
- `src/bookforge/execution/branch_actions.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/branching_lifecycle.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/cli.py`
- `docs/help/workflow.md`
- `docs/help/index.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/index.md`

## Tests
- Add recovery primitive tests:
  - create recovery branch from selected anchor
  - refuse recovery branch without explicit anchor
  - refuse recovery branch with stale parent
  - quarantine stale outline artifacts in branch only
  - normalize outline scope from declared source run
  - normalize outline scope from frozen projection
  - invalidate affected prose and state outputs
  - preserve original prose as non-canonical historical material
  - redraft section in recovery branch without mutating `main`
  - validate recovered branch clears `chimera_risk`
  - refuse promotion with active stale artifacts
  - promote branch with removals and verify `main` no longer detects chimera
- Add Veiled Ledger-style fixture tests:
  - chapters 1-3 affected by mixed outline lineage
  - ghost character cohort removed from canonical state after recovery
  - affected prose redrafted from selected outline
  - stale section drafts no longer appear in active discovery paths
- Add action discovery tests:
  - contaminated `main` exposes diagnostic and recovery-prep actions only
  - recovery branch exposes normalize/invalidate/redraft/validate actions in legal order
  - promotion appears only after validation passes

## Definition Of Done
- BookForge exposes recovery/story-weaving primitives as composable query and execution surfaces.
- Nanda can choose a recovery strategy from an impact report and execute it through BookForge primitives without manual filesystem surgery.
- Recovery mutation runs in a derived branch.
- Recovery actions emit receipts for anchor selection, quarantine, normalization, invalidation, rebuild, redraft, validation, and promotion.
- Invalid artifacts are removed from active discovery paths or quarantined with receipts.
- Invalid timeline data is removed from canonical state/projection datasets before promotion.
- Impacted prose can be redrafted by scene, section, or chapter.
- Promotion can apply removals as well as additions/replacements.
- After promotion, `outline-lineage-audit`, `section-lineage-matrix`, `integrity`, `legal-actions`, and readiness surfaces agree that the recovered book is no longer blocked by the original chimera risk.
- The same primitives can support ordinary author work:
  - retcon a prior scene
  - rewrite an old chapter without rerunning the whole book
  - reweave downstream continuity
  - compare alternate branches

## Explicit Non-Goals
- Do not implement a bespoke `fix_veiled_ledger_chimera` command.
- Do not move author reasoning or approval flow into BookForge.
- Do not let Nanda mutate files directly.
- Do not promote contaminated salvage as canonical without explicit selection.
- Do not require full-book rewrite when a scoped branch recovery is sufficient.
- Do not skip validation because a branch looks narratively plausible.

## Nanda Coordination Notes
- Nanda should add `book_timeline_impact_report_v1`.
- Nanda should compose BookForge primitives into an execution plan.
- Nanda should ask for human decisions when:
  - multiple anchors are plausible
  - salvage policy is non-obvious
  - downstream invalidation scope is larger than the directly affected scope
  - promotion would remove or quarantine significant material
- Nanda should present:
  - evidence
  - proposed plan
  - required approvals
  - BookForge tools to be invoked
  - validation gates
- BookForge should return receipts that Nanda can summarize without inferring from raw files.

---

## Source 19: `notes/2026-04-21-0010-execution.md`

# 0010 Execution Note

Date
- 2026-04-21

Scope
- Execute story `0010-freeze-scope-lineage-and-contract-vocabulary`.

Changes
- Added `src/bookforge/contracts/vocabulary.py` for frozen workflow-family, result-status, artifact-class, branch, and pointer labels.
- Added `src/bookforge/contracts/timeline_node.py` for `TimelineNodeRef`.
- Added `src/bookforge/contracts/scope_selector.py` for `ScopeSelector`.
- Added `src/bookforge/contracts/source_artifacts.py` for central source-artifact truth classification.
- Added export surface at `src/bookforge/contracts/__init__.py`.
- Updated help docs to state the runtime family split and lineage-truth rules:
  - `docs/help/workflow.md`
  - `docs/help/run.md`
  - `docs/help/outline_generate.md`
  - `docs/help/index.md`
- Tightened CLI help labels in `src/bookforge/cli.py` to match the frozen vocabulary.
- Added focused tests:
  - `tests/test_scope_contracts.py`
  - `tests/test_timeline_node.py`

Validation
- Ran:
  - `python -m pytest tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_workspace_init.py tests/test_runner_outline_gate.py`
- Result:
  - `26 passed`

Notes
- This step intentionally froze the boundary without pretending that `StateSurface`, `IssueTicket`, or branch execution already exist.
- `outline/pipeline_runs/<run_id>/...` is now documented as the preferred lineage-anchor family.
- `outline/outline.json` is now documented as a mutable compatibility view, not sufficient lineage truth by itself.
- The next story should build read-only query modules on top of these frozen contract objects instead of redefining them.

---

## Source 20: `notes/2026-04-21-0020-execution.md`

# 0020 Execution Note

Date
- 2026-04-21

Scope
- Execute story `0020-add-read-only-query-surface`.

Changes
- Added read-only query package:
  - `src/bookforge/query/__init__.py`
  - `src/bookforge/query/_common.py`
  - `src/bookforge/query/workspace.py`
  - `src/bookforge/query/lineage.py`
  - `src/bookforge/query/workflow.py`
  - `src/bookforge/query/integrity.py`
  - `src/bookforge/query/characters.py`
  - `src/bookforge/query/continuity.py`
- Query surface now provides:
  - current main-branch observed node
  - workspace status snapshot
  - workflow family / run-mode snapshot
  - immutable source-run lookup
  - chapter projection lookup
  - section-draft lineage lookup
  - `ScopeSelector -> TimelineNodeRef` matching resolution
  - integrity verdicts for source-run mismatch, stale drafts, duplicate names, and mutable-source materialization
  - read access to character and continuity state
- Added tests:
  - `tests/test_query_workspace.py`
  - `tests/test_query_lineage.py`
  - `tests/test_query_integrity.py`

Validation
- Ran:
  - `python -m pytest tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_workspace_init.py tests/test_runner_outline_gate.py`
- Result:
  - `34 passed`

Notes
- This story stays read-only. It does not introduce branch mutation or state/ticket emission early.
- Branch-addressed lookup is supported as a query seam when manifests/pointers exist, but current fixtures remain main-branch only.
- The integrity surface now exposes the `veiled_ledger_b1` class through stable helpers instead of ad hoc scripts.

---

## Source 21: `notes/2026-04-21-0030-execution.md`

# 0030 Execution Note

Date
- 2026-04-21

Scope
- Execute story `0030-emit-versioned-state-surfaces-and-issue-tickets`.

Changes
- Finished the contract-backed supervision emission layer:
  - `src/bookforge/supervision/__init__.py`
  - `src/bookforge/supervision/paths.py`
  - `src/bookforge/supervision/emit.py`
- Completed query support needed by the emitter:
  - emitted main-node preference for consumers
  - live-state bypass for the emitter so it does not read stale pointers
  - chapter status counting on workspace status
  - supervision-aware branch path lookup
  - broader write-phase recognition so paused writer nodes resolve truthfully
- Wired main-branch emission into real execution paths:
  - `initialize_section_workflow`
  - `freeze_section_from_phase03_artifact`
  - `lock_section_from_written_state`
  - `finalize_chapter_from_locked_sections`
  - writer-loop pause helpers
  - writer-loop clean exit
- Added emitted artifacts under `runtime/supervision/main/`:
  - `current_node.json`
  - `state_surface_latest.json`
  - `state_surface_history.jsonl`
  - `issues_latest.json`
  - `issues_history.jsonl`
  - `execution_results.jsonl`
- Tightened selector semantics:
  - `StateSurface` now emits as a branch-rooted surface
  - integrity tickets emit as branch-rooted concerns
  - runtime pause/result emission stays node-specific
- Added execution coverage:
  - `tests/test_supervision_emit.py`

Validation
- Ran:
  - `python -m pytest --basetemp .pytest_tmp_0030 tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_supervision_emit.py`
  - `python -m pytest --basetemp .pytest_tmp_0030b tests/test_runner_outline_gate.py tests/test_workspace_init.py`
- Result:
  - `37 passed`

Notes
- The first useful supervision slice is now real: callers can consume a book-rooted `StateSurface`, categorized `IssueTicket` output, and execution-result history without reverse-engineering logs.
- Pause visibility is now explicit for bounded retry exits. The writer loop emits `retryable_pause` results with node coordinates and ticketed reason classes instead of only leaving transport noise behind.
- Query consumers prefer emitted node pointers by default, but the emitter explicitly recomputes from live state to avoid sealing stale coordinates back into the supervision surface.

---

## Source 22: `notes/2026-04-21-0040-execution.md`

# 0040 Execution Note

Date
- 2026-04-21

Scope
- Execute story `0040-add-truthful-scoped-execution-and-bounded-resume`.

Changes
- Added the first narrow execution adapter:
  - `src/bookforge/execution/__init__.py`
  - `src/bookforge/execution/scoped.py`
- Implemented `resume_paused_section` as a main-branch-only execution path that:
  - requires `ExecutionRequest`
  - requires `expected_node`
  - refuses branch drift
  - refuses expected-node mismatch
  - refuses workflow-family mismatch
  - refuses active-section mismatch
  - resumes only the active frozen section
  - returns `success`, `retryable_pause`, or `hard_fail` through `ExecutionResult`
- Added a convenience request builder:
  - `build_resume_paused_section_request(...)`
- Added a thin CLI wrapper:
  - `bookforge workflow resume-paused-section`
- Tightened runtime truth during resume:
  - `run_loop` now clears stale pause markers when a new run starts
  - workspace family inference now treats active paused write state as authoritative and avoids stale write-family classification after lock completion
- Extended supervision emission so adapter-level results can carry `request_id`.
- Updated help docs:
  - `docs/help/workflow.md`
  - `docs/help/run.md`
  - `docs/help/index.md`
- Added tests:
  - `tests/test_scoped_execution.py`

Validation
- Ran:
  - `python -m pytest --basetemp .pytest_tmp_0040e tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py`
- Result:
  - `41 passed`

Notes
- This is intentionally not a generic scheduler. It is one truthful resume seam over the existing section workflow and writer loop.
- The CLI wrapper snapshots the current expected node immediately before submission, but the real contract remains the Python `ExecutionRequest -> ExecutionResult` path.
- `0045` can now build on stable branch/main semantics instead of implicit retry behavior.

---

## Source 23: `notes/2026-04-21-0045-execution.md`

# 0045 Execution Note

Date
- 2026-04-21

Scope
- Execute story `0045-add-isolated-branch-reruns-and-fork-group-assembly`.

Changes
- Added explicit branch primitives:
  - `src/bookforge/branching.py`
  - `src/bookforge/contracts/branch_manifest.py`
- Extended the shared contract surface:
  - `BranchManifest` now records parent node, frozen parent revision, merge operation, lifecycle state, validation state, and scope selector.
  - branch lifecycle to public-result mapping now lives in `src/bookforge/contracts/vocabulary.py`.
- Extended supervision storage and emission:
  - branch snapshot helpers in `src/bookforge/supervision/paths.py`
  - generic `emit_branch_contracts(...)` in `src/bookforge/supervision/emit.py`
  - branch-aware exports in `src/bookforge/supervision/__init__.py`
- Implemented branch operations:
  - `create_branch(...)`
  - `rerun_freeze_section_on_branch(...)`
  - `discard_branch(...)`
  - `create_assembly_branch(...)`
  - `record_assembly_validation(...)`
  - `promote_branch_to_main(...)`
- Enforced 0045 safety rules in code:
  - no silent source switching inside a branch
  - sibling fork-group branches cannot read one another
  - fork-group assembly refuses stale main-parent drift
  - assembly validation happens off `main`
  - promotion and assembly remain distinct merge paths
- Tightened branch truth in the query surface:
  - branch status now reports lifecycle state correctly
  - branch selector and current-node projection preserve the requested scope instead of collapsing back to the parent node
- Added tests:
  - `tests/test_branch_execution.py`
  - `tests/test_branch_promotion.py`
  - `tests/test_fork_group_assembly.py`
  - expanded `tests/test_scope_contracts.py`

Validation
- Ran:
  - `python -m pytest --basetemp .pytest_tmp_0045 tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scope_contracts.py`
  - `python -m pytest --basetemp .pytest_tmp_0045_regression tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py`
- Result:
  - `16 passed`
  - `37 passed`

Notes
- This step delivers the branch coordinate and isolation model, not a full parallel scheduler.
- Assembly stays off `main`; the current implementation records validation state explicitly and blocks canonical promotion until validation passes.
- Automatic seam-audit execution can attach to the assembly branch later without changing the branch contract or promotion rules.

---

## Source 24: `notes/2026-04-21-0050-execution.md`

# 0050 Execution Note

Date
- 2026-04-21

Scope
- Begin story `0050-harden-reconciliation-integrity-and-command-surface`.

Changes
- Added a reconciliation layer for main-branch execution:
  - `src/bookforge/supervision/reconcile.py`
  - `capture_main_branch_snapshot(...)`
  - `reconcile_main_branch_transition(...)`
  - `emit_reconciled_main_branch_contracts(...)`
- Wired main-branch reconciliation into:
  - `src/bookforge/section_workflow.py`
  - `src/bookforge/execution/scoped.py`
  - `src/bookforge/runner.py`
- Promotion now emits canonical reconciliation on `main` in addition to the derived-branch promotion result:
  - `src/bookforge/branching.py`
- Renamed the reconciliation receipt field from the ambiguous `requested_result_status` to `pre_reconciliation_status`.
- Added the next structural/runtime classifications:
  - `stale_write` for revision-only expected-node drift on `main`
  - `stale_parent` for active branches derived from an out-of-date main revision
  - `overscoped_recovery` for materialized section content that no longer matches its declared source run
- Split branch control into smaller modules before adding more 0050 weight:
  - `src/bookforge/branching.py` is now a thin facade
  - `src/bookforge/branching_fork.py`
  - `src/bookforge/branching_execution.py`
  - `src/bookforge/branching_lifecycle.py`
- Help/docs now describe the public reconciliation fields:
  - `docs/help/index.md`
  - `docs/help/workflow.md`
  - `docs/help/run.md`
- Expanded tests for reconciliation-facing behavior:
  - `tests/test_supervision_emit.py`
  - `tests/test_branch_promotion.py`

Validation
- Ran:
  - `python -m pytest --basetemp .pytest_tmp_0050 tests/test_supervision_emit.py tests/test_branch_promotion.py tests/test_scoped_execution.py tests/test_branch_execution.py tests/test_fork_group_assembly.py tests/test_query_workspace.py tests/test_query_integrity.py tests/test_scope_contracts.py`
  - `python -m pytest --basetemp .pytest_tmp_0050_regression tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_integrity_slice tests/test_query_integrity.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scope_contracts.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050c tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
- Result:
  - `27 passed`
  - `50 passed`
  - `27 passed`
  - `52 passed`

Notes
- This is an in-progress slice, not the full 0050 story.
- The implemented part makes main-branch results materially more truthful:
  - pre-reconciliation vs final public status
  - before/after revision ids
  - canonical vs no-op change classification
  - integrity-change direction
- The branch-control split now keeps the public import surface stable while preventing `branching.py` from becoming the next oversized coordination module.
- Remaining 0050 work is mostly deeper integrity coverage and the final branch-local reconciliation model, not a question of whether reconciliation exists at all.

---

## Source 25: `notes/2026-04-22-0050-execution.md`

# 0050 Execution Note

Date
- 2026-04-22

Scope
- Continue story `0050-harden-reconciliation-integrity-and-command-surface`.
- Finish the branch-local reconciliation slice for off-main mutation paths.

Changes
- Extended `src/bookforge/supervision/reconcile.py` with:
  - `capture_surface_snapshot(...)`
  - `reconcile_branch_transition(...)`
  - `emit_reconciled_branch_contracts(...)`
- Exported the branch-local reconciliation helpers through:
  - `src/bookforge/supervision/__init__.py`
- Wired off-main branch-local receipts into real branch mutation paths:
  - `src/bookforge/branching_execution.py`
    - `rerun_freeze_section_on_branch(...)`
  - `src/bookforge/branching_lifecycle.py`
    - `record_assembly_validation(...)`
- Hardened branch revision generation so rapid branch activity cannot reuse the same revision token inside one second:
  - `src/bookforge/branching_store.py`
- Added one more structural integrity detector:
  - `src/bookforge/query/integrity.py`
    - `workflow_family_contamination` when the emitted main-node surface no longer matches live-derived runtime truth
- Added focused receipt coverage:
  - `tests/test_branch_execution.py`
    - changed branch-local receipt after a real rerun
    - unchanged branch-local receipt when rerun hits already-materialized state
  - `tests/test_fork_group_assembly.py`
    - branch-local receipt after failed assembly validation
  - `tests/test_query_integrity.py`
    - emitted main-node drift against live runtime truth

Validation
- Ran:
  - `python -m pytest --basetemp .pytest_tmp_0050_branch_receipts tests/test_branch_execution.py tests/test_fork_group_assembly.py tests/test_branch_promotion.py tests/test_supervision_emit.py`
  - `python -m pytest --basetemp .pytest_tmp_0050_integrity_plus tests/test_query_integrity.py tests/test_supervision_emit.py tests/test_scoped_execution.py tests/test_query_workspace.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0050f tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
- Result:
  - `15 passed`
  - `14 passed`
  - `56 passed`

Notes
- Off-main execution now has a truthful receipt path that stays distinct from canonical reconciliation:
  - branch-local before/after snapshot
  - branch-only change classification via `branch_change_status`
  - integrity movement without claiming canonical mutation
- The new emitted-vs-live main-node detector is intentionally scoped to emitted-view integrity checks.
  - Live reconciliation paths call `get_integrity_verdict(..., prefer_emitted=False)` so they do not self-trigger during the window before the emitted pointer is refreshed.
- Branch creation still uses a lightweight freshness guard, not a full branch-local reconciliation pass.
- Branch discard still emits lifecycle observability only; it does not pretend to reconcile state that never reaches canonical promotion.

---

## Source 26: `notes/2026-04-22-0060-execution.md`

# 0060 Execution Note

Date
- 2026-04-22

Scope
- Start story `0060-extract-minimal-engine-execution-surface-for-nanda`.
- Land the first extracted action and legal-next-action query slice.

Changes
- Added a queryable action descriptor contract:
  - `src/bookforge/contracts/execution_option.py`
- Added the first legal-next-action query seam:
  - `src/bookforge/query/actions.py`
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
- Added the first outline/materialization execution adapter:
  - `src/bookforge/execution/materialize.py`
  - `build_initialize_workflow_request(...)`
  - `initialize_workflow(...)`
- Extended the materialization adapter slice:
  - `build_freeze_section_request(...)`
  - `freeze_section(...)`
- Completed the main-branch section materialization/finalization slice:
  - `build_lock_section_request(...)`
  - `lock_section(...)`
  - `build_finalize_chapter_request(...)`
  - `finalize_chapter(...)`
- Added the next write-surface action:
  - `build_write_section_request(...)`
  - `write_frozen_section(...)`
- Added the first extracted branch-lifecycle action:
  - `src/bookforge/execution/branch_actions.py`
  - `build_create_branch_request(...)`
  - `create_branch_action(...)`
- Extended the branch-lifecycle extraction slice:
  - `build_create_assembly_branch_request(...)`
  - `create_assembly_branch_action(...)`
  - `build_discard_branch_request(...)`
  - `discard_branch_action(...)`
  - `build_promote_branch_request(...)`
  - `promote_branch_action(...)`
  - `build_record_assembly_validation_request(...)`
  - `record_assembly_validation_action(...)`
- Threaded `request_id` through `create_branch(...)` branch-side emissions so the extracted action can return the emitted branch receipt:
  - `src/bookforge/branching_fork.py`
- Threaded `request_id` through `promote_branch_to_main(...)` emissions so the promotion adapter can return the reconciled canonical receipt instead of fabricating one:
  - `src/bookforge/branching_lifecycle.py`
- Threaded `request_id` through `discard_branch(...)` emissions for the same reason:
  - `src/bookforge/branching_lifecycle.py`
- Threaded `request_id` through `initialize_section_workflow(...)` emissions so the adapter can return the emitted `ExecutionResult` instead of fabricating a second receipt path:
  - `src/bookforge/section_workflow.py`
- Threaded `request_id` through `freeze_section_from_phase03_artifact(...)` emissions for the same reason:
  - `src/bookforge/section_workflow.py`
- Threaded `request_id` through `lock_section_from_written_state(...)` emissions for the same reason:
  - `src/bookforge/section_workflow.py`
- Threaded `request_id` through `finalize_chapter_from_locked_sections(...)` emissions for the same reason:
  - `src/bookforge/section_workflow.py`
- Routed the CLI workflow-init wrapper through the extracted action layer:
  - `src/bookforge/cli.py`
- Routed the CLI workflow-freeze wrapper through the extracted action layer:
  - `src/bookforge/cli.py`
- Routed the CLI workflow-lock wrapper through the extracted action layer:
  - `src/bookforge/cli.py`
- Routed the CLI workflow-finalize wrapper through the extracted action layer:
  - `src/bookforge/cli.py`
- Routed the CLI workflow-advance wrapper through the extracted action layer sequence:
  - `freeze_section_from_phase03_artifact`
  - `write_frozen_section` or `resume_paused_section`
  - `lock_section_from_written_state`
- Added the CLI workflow-write wrapper over the extracted write action:
  - `bookforge workflow write-section`
- Added an operator wrapper over the same discovery seam:
  - `bookforge workflow legal-actions`
- Extended the operator wrapper so legal-action discovery can target derived branches:
  - `bookforge workflow legal-actions --branch-id <id>`
- Extended main-branch legal-action discovery so fork-group scope can surface `create_assembly_branch`:
  - `bookforge workflow legal-actions --fork-group-id <id>`
- Extended derived-branch discovery to surface assembly validation when the selected branch is an active assembly branch.
- Updated help docs to reflect the new action/discovery surface:
  - `docs/help/workflow.md`
  - `docs/help/index.md`
- Added focused tests:
  - `tests/test_execution_actions.py`
  - `tests/test_action_discovery.py`

Validation
- Ran:
  - `python -m pytest --basetemp .pytest_tmp_0060_branch_action tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060c tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_branch_lifecycle tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060d tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_assembly_action tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060e tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_assembly_create tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060f tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_finalize tests/test_execution_actions.py tests/test_action_discovery.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060g tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_lock tests/test_execution_actions.py tests/test_action_discovery.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060h tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_write tests/test_execution_actions.py tests/test_action_discovery.py tests/test_scoped_execution.py tests/test_section_workflow.py tests/test_chapter_seam.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060i tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
- Result:
  - `19 passed`
  - `64 passed`
  - `28 passed`
  - `68 passed`
  - `30 passed`
  - `70 passed`
  - `32 passed`
  - `72 passed`
  - `29 passed`
  - `77 passed`
  - `31 passed`
  - `79 passed`
  - `34 passed`
  - `82 passed`

Notes
- This is intentionally the smallest honest extraction slice:
  - four outline/materialization actions
  - one write/resume action
  - the full current branch-lifecycle action family
  - one query seam for legal-next-action discovery
- The CLI no longer owns unique logic for workflow init.
- The action descriptor is still intentionally simple. It exposes:
  - action id
  - summary
  - branch policy
  - canonical-mutation flag
  - expected-node requirement
  - selector requirements
  - allowed vs blocked state
  - refusal reason
- Branch lifecycle extraction now covers:
  - `create_assembly_branch`
  - `create_branch`
  - `discard_branch`
  - `promote_branch_to_main`
  - `record_assembly_validation`
- Main-branch materialization/finalization extraction now covers:
  - `initialize_section_workflow`
  - `freeze_section_from_phase03_artifact`
  - `write_frozen_section`
  - `lock_section_from_written_state`
  - `finalize_chapter_from_locked_sections`
- The write-side choose-your-own-adventure seam now supports:
  - `freeze_section_from_phase03_artifact`
  - `write_frozen_section`
  - `lock_section_from_written_state`
  - `resume_paused_section`
- `advance-section` remains available as a macro convenience wrapper, but it no longer owns unique orchestration logic.
- The remaining obvious future gap is the deeper write/lint/repair interior if we want Nanda to steer per-scene or per-phase sub-actions instead of section-level write actions.

---

## Source 27: `notes/2026-04-23-0070-commit-slice.md`

## 2026-04-23 - 0070 commit slice

### Scope
- Extract `apply_scene_commit` as the first scene-phase action that mutates canonical main-branch state.
- Keep the action truthful to the existing runner apply path instead of exposing a fake narrow "save prose" surface.
- Extend reconciled execution emission so canonical scene actions can carry produced-artifact receipts.

### Files touched
- `src/bookforge/supervision/emit.py`
- `src/bookforge/supervision/reconcile.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/execution/__init__.py`
- `src/bookforge/query/scene_phase.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/cli.py`
- `tests/test_scene_phase_readiness.py`
- `tests/test_scene_action_execution.py`
- `tests/test_action_discovery.py`
- `docs/help/workflow.md`
- `docs/help/index.md`
- `docs/help/run.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0070-segment-section-write-into-scoped-scene-actions/step.md`

### What changed
- Added `apply_scene_commit` as an extracted main-branch scene action with:
  - request builder
  - execution adapter
  - CLI command
  - execution-option discovery
  - readiness/query support
- Extended reconciled supervision emission so main-branch execution results can include `produced_artifacts`.
- Updated scene readiness so a passing current lint report now opens `apply_scene_commit` instead of dead-ending.
- Kept commit on the real canonical apply path:
  - apply final state patch
  - apply character and continuity-system updates
  - refresh appearance projections when requested
  - apply durable mutations
  - persist scene prose/meta
  - update bible
  - compile chapter outputs on chapter end
  - advance cursor and write `state.json`

### Why
- `write_scene_prose`, `state_repair_scene_patch`, `lint_scene_prose`, and `repair_scene_prose` already gave Nanda truthful provisional scene control.
- The next missing piece was the canonical mutation boundary.
- Without an extracted commit action:
  - passing lint had no truthful next step,
  - callers had to drop back to batch wrappers for the final scene mutation,
  - and canonical scene receipts could not carry produced-artifact truth.
- This slice closes that gap while preserving the doctrine that the engine, not the caller, defines legal mutation paths.

### Validation
- `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_commit`
- `python -m pytest tests/test_scope_contracts.py tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_query_workspace.py -q --basetemp .pytest_tmp_0070_commit_regression`
- `python -m pytest tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q --basetemp .pytest_tmp_0070_commit_supervision`
- `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_commit_sceneplus`

### Follow-on
- The next 0070 slice should be wrapper integration:
  - teach `run_loop` / section-level wrappers to consume the extracted scene actions instead of owning the scene choreography directly
- 0075 remains the right place for:
  - appearance extraction/turning
  - background setting extraction
  - richer context reuse such as T1 thought-signature carry-forward into later refinement turns

---

## Source 28: `notes/2026-04-23-0070-continuity-pack-slice.md`

# 0070 Continuity-Pack Slice Execution Note

Date
- 2026-04-23

Scope
- Continue story `0070-segment-section-write-into-scoped-scene-actions`.
- Extract `generate_continuity_pack` as a truthful scene-phase action between `preflight_scene_state` and `write_scene_prose`.
- Correct the next extraction order after tracing `run_loop`: existing pipeline truth is `write -> state_repair -> lint -> repair`, so `state_repair_scene_patch` lands before `lint_scene_prose`.

Changes
- Added the continuity-pack execution action surface:
  - `build_generate_continuity_pack_request(...)`
  - `generate_continuity_pack(...)`
- Exposed the action through:
  - `bookforge.execution`
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - `bookforge workflow generate-continuity-pack`
- Kept the action narrow:
  - requires active cursor scene on `main`
  - requires existing `scene_card` and `preflight_patch`
  - produces only a `derived` continuity-pack receipt
  - does not generate prose
  - does not lint
  - does not repair
  - does not commit
  - does not mutate canonical `state.json`
- Added a materialization guard:
  - safe preflight summary changes are applied only to an in-memory working state
  - provisional character, continuity-system, or durable mutations are refused until a truthful materialization surface exists
- Updated operator docs:
  - `docs/help/workflow.md`
  - `docs/help/index.md`
  - `docs/help/run.md`
- Updated plan traceability for the landed continuity-pack guardrails.
- Added the state-repair execution action surface:
  - `build_state_repair_scene_patch_request(...)`
  - `state_repair_scene_patch(...)`
- Exposed the state-repair action through:
  - `bookforge.execution`
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - `bookforge workflow state-repair-scene-patch`
- Kept the state-repair action narrow:
  - requires active cursor scene on `main`
  - requires existing `scene_card`, `preflight_patch`, `continuity_pack`, `write_prose`, and `write_patch`
  - produces only a `provisional` corrected state patch
  - does not apply the corrected patch to canonical state
  - does not lint
  - does not repair prose
  - does not commit
- Added the lint execution action surface:
  - `build_lint_scene_prose_request(...)`
  - `lint_scene_prose(...)`
- Exposed the lint action through:
  - `bookforge.execution`
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - `bookforge workflow lint-scene-prose`
- Kept the lint action narrow:
  - requires active cursor scene on `main`
  - requires existing `scene_card`, `preflight_patch`, `continuity_pack`, `write_prose`, and `state_repair_patch`
  - produces only a `provisional` lint report
  - does not repair prose
  - does not rerun state repair
  - does not commit

Validation
- Ran:
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py tests/test_scoped_execution.py -q`
  - `python -m pytest tests/test_execution_actions.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q`
  - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py tests/test_scoped_execution.py -q`
  - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py -q`
  - `python -m pytest tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_scene_phase_readiness.py tests/test_scoped_execution.py -q`
  - `python -m pytest tests/test_execution_actions.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q`
  - `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q`
- Result:
  - `31 passed`
  - `38 passed`
  - `28 passed`
  - `41 passed`
  - `39 passed`
  - `43 passed`
  - `46 passed`
  - `44 passed`
  - `48 passed`
  - `28 passed`
  - `51 passed`

Notes
- The scene-phase traversal path now has six extracted actions:
  - `plan_scene`
  - `preflight_scene_state`
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
- The next 0070 slice should continue the post-write path:
  - `repair_scene_prose`
  - then apply/commit once lint/repair receipts are stable
- Appearance and setting extraction remain intentionally deferred to `0075`.

---

## Source 29: `notes/2026-04-23-0070-repair-slice.md`

## 2026-04-23 - 0070 repair slice

### Scope
- Extend the extracted `section_write` scene-action surface with `repair_scene_prose`.
- Make readiness and execution resolve the latest current provisional prose baseline instead of assuming `write_*` remains current forever.
- Reopen `state_repair_scene_patch` and `lint_scene_prose` truthfully after a newer repair pass.

### Files touched
- `src/bookforge/pipeline/scene_phase_artifacts.py`
- `src/bookforge/query/scene_phase.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/execution/__init__.py`
- `src/bookforge/cli.py`
- `tests/test_scene_phase_readiness.py`
- `tests/test_scene_action_execution.py`
- `tests/test_action_discovery.py`
- `docs/help/workflow.md`
- `docs/help/index.md`
- `docs/help/run.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0070-segment-section-write-into-scoped-scene-actions/step.md`

### What changed
- Added `repair_scene_prose` as an extracted main-branch scene action with:
  - request builder
  - execution adapter
  - CLI command
  - execution-option discovery
  - readiness/query support
- Added shared scene artifact-state resolution so both query and execution can agree on:
  - current prose baseline (`write_*` vs newer `repair_*`)
  - whether `state_repair_patch` is current or superseded
  - whether `lint_report` is current or superseded
  - current lint status
- Updated `state_repair_scene_patch` and `lint_scene_prose` to consume the latest current prose baseline instead of hard-coding `write_prose`.
- Updated lint result reporting so passing lint no longer falsely points at the unextracted `apply_scene_commit` action.

### Why
- The earlier extracted slices still treated any existing `state_repair` or `lint` output as terminal.
- That made the graph lie after a repair pass:
  - the user could generate repaired prose,
  - but the readiness surface would still report old downstream outputs as blocking,
  - and the execution adapters would still read stale write artifacts.
- This slice fixes that by making repair a first-class loop re-entry point instead of a dead end.

### Validation
- `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_repair`
- `python -m pytest tests/test_scoped_execution.py tests/test_execution_actions.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py -q --basetemp .pytest_tmp_0070_repair_regression`
- `python -m pytest tests/test_scope_contracts.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_contracts`
- `python -m pytest tests/test_query_workspace.py tests/test_scene_phase_readiness.py -q --basetemp .pytest_tmp_0070_query2`

### Follow-on
- Next extracted scene-phase slice is still `apply_scene_commit`.
- That slice should consume the latest current provisional baseline and latest current lint outcome rather than assuming a single pass.

---

## Source 30: `notes/2026-04-23-0070-run-loop-wrapper-slice.md`

# 2026-04-23 0070 Run-Loop Wrapper Slice

## Summary
- Routed `run_loop` scene execution through the extracted scene-phase action surface instead of keeping a second monolithic per-scene implementation in `runner.py`.
- Kept the existing outer writer behavior intact:
  - outline gate
  - character/style-anchor bootstrap
  - progress heartbeat
  - pause marker / pause contract
  - section-level wrappers at the time of this slice still called `run_loop`
- Added a small scene-sequence adapter so the runner can execute:
  - `plan_scene`
  - `preflight_scene_state`
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `apply_scene_commit`

## Why
- `0070` is no longer just about exposing narrow scene-phase actions individually.
- The batch writer path also needed to stop being a separate source of truth.
- If `run_loop` kept its own internal choreography, Nanda would still be supervising one graph while production writing used another.

## Key Changes
- Added `src/bookforge/execution/scene_sequence.py`.
  - builds live scene-phase requests against the current main-branch node
  - allows the runner to pass durable-slice expansion hints into extracted actions
- Updated `src/bookforge/execution/scene_actions.py`.
  - scene-phase request builders now resolve the live node with `prefer_emitted=False`
  - extracted phase actions now accept `durable_expand_ids` through request details and pass them to the underlying phase implementations
- Updated `src/bookforge/runner.py`.
  - added a runner-local scene-sequence driver
  - translated scene-phase `retryable_pause` results back into `draft/context/run_paused.json`
  - preserved the existing strict-mode lint failure / durable-slice pause behavior
  - kept appearance refresh after scene-card resolution before prose generation

## Validation
- `python -m pytest tests/test_runner_targeting.py tests/test_scene_action_execution.py tests/test_scene_phase_readiness.py tests/test_action_discovery.py -q --basetemp .pytest_tmp_0070_runner_wrap`
- `python -m pytest tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_0070_runner_wrap_scoped`
- `python -m pytest tests/test_scope_contracts.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_query_workspace.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_runner_wrap_regression`
- `python -m pytest tests/test_runner_targeting.py tests/test_runner_outline_gate.py tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_execution_actions.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_0070_runner_wrap_full`

## Remaining Edge
- At the time this slice landed, `run_loop` delegated per-scene work truthfully, but the section-level wrappers still depended on `run_loop` as the macro entry point rather than owning their own scene traversal.
- That gap was closed later the same day in `2026-04-23-0070-section-wrapper-tightening.md` by introducing `run_section_range(...)` for section-scoped traversal.

---

## Source 31: `notes/2026-04-23-0070-section-wrapper-tightening.md`

# 2026-04-23 0070 Section Wrapper Tightening

## Summary
- Tightened the section-level macro surface so `write_frozen_section`, `resume_paused_section`, and `advance_section_workflow` no longer depend on `run_loop(...)` as their macro entry point.
- Added a dedicated runner surface, `run_section_range(...)`, for section-scoped traversal over the extracted scene-phase sequence.
- Kept `run_loop(...)` as the batch/operator macro over the same lower-level write path instead of letting section wrappers parameterize the batch surface directly.

## Why
- `run_loop(...)` is the right batch/operator entry point, but it was still acting as the only macro-level path for section work.
- That kept section wrappers one level too indirect for truthful supervision and future skill extraction.
- The section wrappers needed a dedicated section-scoped macro so Nanda and later MCP-style capability extraction can treat section execution as a real skill boundary instead of “call the batch thing with the right arguments.”

## Changes
- `src/bookforge/runner.py`
  - split the old public runner body into `_run_write_scope(...)`
  - added `_set_cursor_for_scene_range(...)`
  - added `run_section_range(...)` for section-scoped traversal
  - kept `run_loop(...)` as a thin public wrapper over `_run_write_scope(...)`
- `src/bookforge/execution/scoped.py`
  - `write_frozen_section(...)` now calls `run_section_range(...)`
  - `resume_paused_section(...)` now calls `run_section_range(...)`
- `src/bookforge/section_workflow.py`
  - `advance_section_workflow(...)` now calls `run_section_range(...)`
  - removed the local cursor-reset helper that duplicated runner logic
- `tests/test_execution_actions.py`
  - updated the write-section adapter test to patch `run_section_range(...)`
- `tests/test_scoped_execution.py`
  - updated paused-resume tests to patch `run_section_range(...)`

## Validation
- `python -m pytest tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_targeting.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_section_range`
  - `20 passed`
- `python -m pytest tests/test_scene_phase_readiness.py tests/test_scene_action_execution.py tests/test_action_discovery.py tests/test_execution_actions.py tests/test_scoped_execution.py tests/test_runner_targeting.py tests/test_runner_outline_gate.py -q --basetemp .pytest_tmp_section_range_full`
  - `78 passed`
- `python -m pytest tests/test_scope_contracts.py tests/test_supervision_emit.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_query_workspace.py tests/test_scoped_execution.py -q --basetemp .pytest_tmp_section_range_regression`
  - `28 passed`

## Result
- Section-scoped commands now have their own truthful macro executor.
- Batch `run` and section-scoped execution still share the same lower-level extracted scene-phase path.
- The dependency direction is cleaner:
  - scene actions are the atomic truth
  - section-range execution is the section macro
  - `run_loop(...)` is the batch/operator macro

---

## Source 32: `notes/2026-04-26-0070-complete.md`

# 2026-04-26 0070 Complete

## Completed Scope
- Extracted scene-phase readiness and action surfaces for the section-write flow.
- Exposed phase-shaped actions for:
  - `plan_scene`
  - `preflight_scene_state`
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `apply_scene_commit`
- Routed `run_loop(...)` through extracted scene-phase actions.
- Added `run_section_range(...)` as the section-scoped macro so section wrappers no longer depend on `run_loop(...)` as their macro entry point.
- Added branch-scoped scene/section execution in 0071.
- Added parent-target promotion, rebase, and parallel fork write/assembly in 0072.
- Added appearance, setting, and thought-context projection layers in 0075.

## Validation
- Closeout regression:
  - `tests/test_scope_contracts.py`
  - `tests/test_scene_phase_readiness.py`
  - `tests/test_scene_action_execution.py`
  - `tests/test_action_discovery.py`
  - `tests/test_execution_actions.py`
  - `tests/test_scoped_execution.py`
  - `tests/test_runner_targeting.py`
  - `tests/test_runner_outline_gate.py`
  - `tests/test_query_workspace.py`
  - `tests/test_supervision_emit.py`
  - `tests/test_branch_execution.py`
  - `tests/test_branch_promotion.py`
  - `tests/test_fork_group_assembly.py`
  - `tests/test_scene_context_query.py`
  - `tests/test_scene_setting_actions.py`
  - `tests/test_appearance_projection_action.py`
  - `tests/test_appearance_query.py`
  - `tests/test_scene_setting_query.py`
  - `tests/test_thought_context_query.py`
  - `tests/test_character_invariants_remove.py`
- Result: `132 passed`.

## Known Follow-Up
- Broader outline tests remain a separate follow-up item.
- Prior notes identified stale dummy-client thinking-argument expectations, prompt checksum drift, and skilltree artifact fixture drift outside the 0070/0075 surface.

---

## Source 33: `notes/2026-04-26-0071-branch-scoped-writer.md`

# 2026-04-26 0071 Branch-Scoped Writer

## Summary
- Completed the first branch-scoped writer slice.
- Scene-phase readiness and execution can now resolve against a derived branch execution root instead of only canonical `main`.
- Section-range writing can run through a branch-local root and pass branch identity into the section traversal.
- Historical scene rewrites are branch-local: copied committed scene files are treated as replaceable branch baselines, and `apply_scene_commit` preserves `.original` backups before replacing them in the branch snapshot.
- `main` remains protected from accidental committed-scene overwrite.

## Code Notes
- Query surfaces now expose branch-local workspace status, current node, section status, and scene readiness.
- Scene-phase request builders and actions accept `branch_id`.
- Branch snapshots now copy writer-facing surfaces such as `draft`, `prompts`, and context folders.
- CLI workflow scene-phase commands and `write-section` now accept `--branch-id`.

## Tests
- Focused branch execution: `15 passed`.
- Broader non-outline regression set: `94 passed` before CLI/docs updates and `87 passed` for the focused scene/action/scoped set after CLI branch-id wiring.

## Open Follow-Up
- Outline tests are still tracked as a separate repair TODO because the current dirty tree includes unrelated outline edits from another agent.
- 0072 remains in progress for fork-group writer assembly.

---

## Source 34: `notes/2026-04-26-0072-complete.md`

# 2026-04-26 0072 Complete

## Summary
- Completed the conservative parent-target promotion, rebase, and fork-group writer assembly slice.

## Delivered
- Branches can derive from parent branches, not only `main`.
- Branches can promote into parent branches or `main`.
- Rebase exists as an explicit refreshed-child operation that preserves old branch history.
- Workflow CLI exposes branch lifecycle controls.
- Fork-group writer assembly stages sibling outputs off-parent, validates staged output presence, and only then permits promotion.

## Deferred
- Semantic seam and continuity validation for assembled prose belongs in a later seam/continuity validation step.
- Nanda convenience launchers for sibling execution can build on these primitives without changing the engine contract.

---

## Source 35: `notes/2026-04-26-0072-lifecycle-cli.md`

# 2026-04-26 0072 Lifecycle CLI

## Summary
- Added workflow CLI access for the branch lifecycle primitives already available through the execution layer.
- New commands:
  - `workflow create-branch`
  - `workflow create-assembly-branch`
  - `workflow discard-branch`
  - `workflow promote-branch`
  - `workflow rebase-branch`
  - `workflow record-assembly-validation`

## Intent
- Keep Nanda and operator workflows on truthful execution receipts instead of forcing direct branch manifest/file inspection.
- Support nested author branches from the command surface:
  - chapter branch
  - section branch under chapter branch
  - scene rewrite branch under section/chapter branch
  - promotion back to parent or `main`
  - explicit refreshed-child rebase

## Boundaries
- The CLI exposes lifecycle controls, but does not yet implement writer fork-group assembly.
- Rebase remains the conservative refreshed-child model; it does not silently transplant prose/state changes.

---

## Source 36: `notes/2026-04-26-0072-nested-branch-primitives.md`

# 2026-04-26 0072 Nested Branch Primitives

## Summary
- Started 0072.
- Landed the conservative branch hierarchy primitives needed before parallel writer assembly:
  - create branch from parent branch snapshot
  - promote a branch into an explicit parent branch
  - rebase by creating a refreshed child branch from the current parent snapshot and discarding the old branch without erasing history

## Current Boundaries
- These primitives now have workflow CLI wrappers as of the 0072 lifecycle CLI slice.
- The rebase path is intentionally safe and non-semantic: it refreshes the branch from the parent snapshot but does not attempt hidden prose/state transplant.
- Writer fork-group assembly remains planned, not implemented.

## Tests
- Covered by `tests/test_branch_execution.py`:
  - nested scene branch promotes into chapter parent without touching `main`
  - rebase creates a refreshed child from the updated parent and marks the old branch discarded

---

## Source 37: `notes/2026-04-26-0072-writer-assembly-staging.md`

# 2026-04-26 0072 Writer Assembly Staging

## Summary
- Extended `create_assembly_branch(...)` so it does more than create an empty off-parent branch.
- It now stages scoped draft scene outputs from fork-group sibling writer branches into the assembly branch snapshot.
- Added `validate_assembly_branch(...)` and `workflow validate-assembly-branch` to deterministically verify staged sibling writer outputs before promotion.

## Rules
- Sibling branches must still share the same parent node and parent snapshot revision.
- Parent staleness is checked against the actual parent branch:
  - `main` parent checks current `main`
  - derived parent checks the parent branch current node
- Assembly reads sibling outputs only after sibling execution, not during sibling execution.
- The assembly branch remains off-parent until validation and explicit promotion.
- Validation only checks staged output presence. It does not perform semantic seam or continuity review.

## Validation
- Added coverage that two sibling writer branches stage separate scene files into one assembly branch while leaving canonical `main` untouched.
- Added coverage that deterministic assembly validation marks a staged assembly branch as `assembled_pending_promotion`.
- Added coverage that a validated assembly branch can promote staged writer outputs to `main`.
- Focused non-outline regression set passed with `99` tests.

---

## Source 38: `notes/2026-04-26-0075-appearance-pending-fix.md`

# 2026-04-26 0075 Appearance Pending Fix

## Finding
- `_apply_character_updates(...)` could mutate `appearance_current` without marking the appearance projection as pending.
- If the legacy LLM appearance refresh stalled or failed after that mutation, query surfaces could treat the changed appearance as current instead of stale.

## Change
- `src/bookforge/pipeline/state_apply.py` now sets `appearance_projection_pending: true` whenever `appearance_updates` change `appearance_current`.
- `list_appearance_projection_views(...)` already classifies that state as:
  - `appearance_status: stale`
  - `artifact_status: provisional`
  - `staleness_reason: appearance_projection_pending`

## Validation
- Added coverage in `tests/test_character_invariants_remove.py`.
- Targeted run:
  - `tests/test_character_invariants_remove.py`
  - `tests/test_appearance_query.py`
- Result: `6 passed`.

## Remaining Follow-Up
- Legacy `_load_character_states(...)` can still derive missing `appearance_current` from base state as a read-side compatibility behavior.
- That path correctly marks `appearance_projection_pending: true`, but should be revisited later if we fully separate read-only projection preparation from canonical character-state mutation.

---

## Source 39: `notes/2026-04-26-0075-complete.md`

# 2026-04-26 0075 Complete

## Completed Scope
- Appearance projection query surface.
- Scene/cast-scoped appearance projection action.
- Scene setting projection query surface.
- Author-supplied setting projection action.
- Prose-derived setting projection action.
- Prior T1 thought-context projection query surface.
- Aggregate scene context projection query.
- Scene-phase execution receipts now include compact scene context projection snapshots.
- Appearance update path now marks projections pending when canonical appearance state changes.

## Decision
- BookForge does not run an internal author-LLM setting draft/extract turn in this step.
- For the current contract, Nanda or another author-worker caller supplies structured setting payloads to:
  - `draft_scene_setting_projection`
  - `extract_scene_setting_from_prose`
- A later BookForge-owned LLM turn can be added as a separate action without changing the query/projection contract.

## Validation
- 0075 regression plus branch/action discovery coverage:
  - `tests/test_action_discovery.py`
  - `tests/test_branch_execution.py`
  - `tests/test_fork_group_assembly.py`
  - `tests/test_scene_action_execution.py`
  - `tests/test_scene_context_query.py`
  - `tests/test_scene_setting_actions.py`
  - `tests/test_appearance_projection_action.py`
  - `tests/test_appearance_query.py`
  - `tests/test_scene_setting_query.py`
  - `tests/test_thought_context_query.py`
  - `tests/test_character_invariants_remove.py`
- Result: `91 passed`.

## Remaining Outside 0075
- Future prompt-injection work should decide when scene context projections become actual model-request inputs.
- If projections are injected into prompts, receipts must flip `used_as_prompt_input` only for actions that truly consumed them.
- Future deep state/inventory projection layers should follow the same book-rooted coordinate and artifact-status model.

---

## Source 40: `notes/2026-04-26-0075-context-receipts.md`

# 2026-04-26 0075 Scene Context Receipt Slice

## Completed
- Added `scene_context_projection` snapshots to scene-phase execution receipts.
- Covered:
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `apply_scene_commit`
- The receipt snapshot aggregates:
  - appearance projection status and source artifacts
  - scene setting status, source mode, and source artifacts
  - selected prior T1 thought signatures and limitations

## Truth Boundary
- `scene_context_projection.used_as_prompt_input` is currently `false`.
- The receipt is an observation surface, not proof that the author prompt consumed the projection payload.
- A future prompt-injection slice must only flip this field when the projection payload is actually assembled into the model request.
- Thought signatures remain context aids; execution receipts remain the truth of what happened.

## Validation
- Focused test:
  - `tests/test_scene_action_execution.py::test_write_scene_prose_generates_provisional_receipts`
- 0075 focused regression:
  - `tests/test_scene_action_execution.py`
  - `tests/test_scene_context_query.py`
  - `tests/test_scene_setting_actions.py`
  - `tests/test_appearance_projection_action.py`
  - `tests/test_appearance_query.py`
  - `tests/test_scene_setting_query.py`
  - `tests/test_thought_context_query.py`
- Result: `35 passed`.

## Remaining 0075 Work
- Decide whether prompt assembly should consume scene context projections directly in BookForge or whether Nanda should choose and pass them as explicit action inputs.
- Audit legacy character appearance mutation/refresh paths against the projection contract.

---

## Source 41: `notes/2026-04-26-0075-projection-query-slice.md`

# 2026-04-26 0075 Projection Query Slice

## Completed
- Added `bookforge.query.appearance` with branch-aware appearance projection views.
- Added `bookforge.query.setting` with scene setting projection lookup.
- Added `bookforge.query.thought_context` with prior T1 thought-signature context discovery.
- Exported all three query surfaces from `bookforge.query`.
- Added `refresh_character_appearance_projection` as a non-mutating execution action.
- Added action discovery for `refresh_character_appearance_projection`.

## Contract Notes
- Existing character `appearance_current` is not silently treated as authoritative.
- Appearance query defaults to `derived` for readable state, `provisional` when projection is pending, and `diagnostic` when missing.
- Scene setting distinguishes `author_drafted` (`provisional`), `prose_extracted` (`derived`), `outline_derived` (`derived`), and `missing` (`diagnostic`).
- Thought signatures are exposed as `diagnostic` planning-reuse context only; execution receipts remain the source of truth for what happened.
- The appearance projection action writes `draft/context/appearance/ch_###/scene_###/appearance_projection.json` and records a `ProducedArtifactReceipt`.

## Validation
- `tests/test_appearance_query.py`
- `tests/test_scene_setting_query.py`
- `tests/test_thought_context_query.py`
- `tests/test_appearance_projection_action.py`
- Focused result: 11 passed.

## Remaining 0075 Work
- Add setting/background extraction and author-drafted setting actions.
- Record appearance, setting, and thought-context artifact usage in downstream scene-phase prompt receipts.
- Consider a compact aggregate scene-context readiness/query surface once the individual projections settle.

---

## Source 42: `notes/2026-04-26-0075-setting-actions.md`

# 2026-04-26 0075 Setting Projection Actions

## Completed
- Added `draft_scene_setting_projection`.
- Added `extract_scene_setting_from_prose`.
- Added `get_scene_context_projection`.
- Exported both request builders and execution actions from `bookforge.execution`.
- Added both actions to legal-action discovery for scene scope.
- Added setting action tests.

## Contract Notes
- `draft_scene_setting_projection` writes `author_drafted.setting.json` with artifact status `provisional`.
- `extract_scene_setting_from_prose` writes `prose_extracted.setting.json` with artifact status `derived`.
- Both actions are non-canonical and non-mutating.
- `extract_scene_setting_from_prose` refuses when no scene prose exists.
- The current implementation records structured setting supplied by the caller/author worker; it does not perform an internal LLM extraction turn yet.
- If no structured extraction is supplied, the prose-extraction action keeps a source excerpt and reports conservative structured availability.
- `get_scene_context_projection` aggregates appearance, setting, and T1 thought-context availability without creating a second truth model.

## Validation
- `tests/test_scene_setting_actions.py`
- `tests/test_scene_setting_query.py`
- `tests/test_scene_context_query.py`
- `tests/test_action_discovery.py`
- Focused result: 34 passed for action discovery plus setting actions.

## Remaining 0075 Work
- Record appearance, setting, and thought-context artifact usage in downstream prompt/execution receipts.
- Decide whether to add an internal author-LLM setting draft turn or leave Nanda as the author-worker caller that supplies the structured setting payload.
- Consider an aggregate scene-context readiness surface after projection usage receipts land.

---

## Source 43: `notes/2026-04-26-0080-complete.md`

# 2026-04-26 0080 Complete

## Summary
- Completed the read-only outline lineage audit slice.
- BookForge now exposes operational evidence for chimera-class outline bleed instead of only global `chimera_risk`.
- Nanda can query affected sections, artifact-family disagreement, character-cohort conflict, stale outline artifacts, and non-mutating repair candidates before presenting author repair choices.

## Implemented Surfaces
- `bookforge.query.get_outline_lineage_audit(...)`
- `bookforge.query.get_section_lineage_matrix(...)`
- `bookforge.query.get_stale_outline_artifact_inventory(...)`
- `bookforge.query.get_outline_repair_candidates(...)`

## CLI Surfaces
- `bookforge workflow outline-lineage-audit`
- `bookforge workflow section-lineage-matrix`
- `bookforge workflow stale-outline-artifacts`
- `bookforge workflow outline-repair-candidates`

## Safety Behavior
- `get_integrity_verdict(...)` now includes localized lineage details for `overscoped_recovery`.
- Emitted issue tickets preserve those details for Nanda.
- Main-branch mutation actions are blocked when outline lineage audit reports `chimera_risk`.
- `create_branch` remains available so recovery can start from an isolated branch instead of mutating `main`.
- No repair mutation was added in this slice.

## Veiled Ledger Smoke Result
- `outline-lineage-audit` localizes the current Veiled Ledger conflict to affected sections instead of reporting only a global state.
- The audit reports:
  - first technical divergence
  - first visible story divergence
  - affected section count
  - per-section differing fields
  - character cohort deltas
  - repair candidates
- `legal-actions` now blocks unsafe main mutation for the contaminated book and recommends lineage audit first.

## Validation
- Focused lineage/action suite:
  - `python -m pytest -o addopts='' tests/test_outline_lineage_audit.py tests/test_query_integrity.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0080_focus`
- Broader query/action/supervision regression:
  - `python -m pytest -o addopts='' tests/test_outline_lineage_audit.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_supervision_emit.py tests/test_action_discovery.py tests/test_scoped_execution.py --basetemp=.pytest_tmp_0080_regression`
- Full regression:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0080_full`
  - result: `304 passed`

## Follow-Up
- Add a mutation-capable recovery-import story only after Nanda consumes this read-only audit surface.
- That future story should include branch isolation, backup/quarantine receipts, selected recovery anchor, and validation-gated promotion.

---

## Source 44: `notes/2026-04-26-0081-implementation-slice.md`

# 2026-04-26 0081 Implementation Slice

## Implemented
- Added recovery contract objects:
  - `RecoveryAnchor`
  - `RecoveryScope`
  - `RecoveryReceipt`
  - `RecoveryBranchHealth`
- Added read/query recovery surfaces:
  - recovery manifest lookup
  - recovery plan readiness
  - scope invalidation preview
  - salvage candidates
  - recovery branch health
- Added branch-first recovery execution primitives:
  - `create_recovery_branch`
  - `quarantine_artifacts`
  - `normalize_outline_scope`
  - `invalidate_scope_outputs`
  - `validate_recovery_branch`
  - `promote_recovery_branch`
- Added action discovery entries for recovery branches so Nanda can ask what is legal next.
- Added CLI wrappers for recovery query/action primitives.
- Updated promotion lifecycle so recovery branches can carry explicit removal receipts into promotion.
- Recovery branches now copy outline lineage evidence directories into the isolated branch snapshot before mutation:
  - `outline/pipeline_runs`
  - `outline/section_drafts`
- Scope invalidation records pre-normalization scene ranges so polluted extra scene files can be removed even after the branch outline is normalized.
- Added initial Nanda decision-layer metadata:
  - approval-required flags for recovery branch creation, destructive cleanup, invalidation, and promotion
  - recommended next recovery action in readiness/health surfaces
  - explicit shadow/full-execution boundary in the 0081 step doc

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_outline_lineage_audit.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_focus`
  - Result: `41 passed`
- Full regression:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_nanda_delta_full`
  - Result: `308 passed`
- Post-review module split:
  - `recovery_common.py`: 257 lines
  - `recovery_create.py`: 190 lines
  - `recovery_artifacts.py`: 126 lines
  - `recovery_outline.py`: 180 lines
  - `recovery_validation.py`: 109 lines
  - `recovery_actions.py`: 18-line facade

## Remaining Work
- Add `rebuild_state_scope`.
- Add `redraft_scope` as a scope-level orchestration primitive.
- Add postcondition receipts with integrity deltas and next legal action snapshots.
- Add impact-report-friendly blast-radius queries for prose/state/series/continuity/projection invalidation.
- Expand approval-required metadata across broad-scope state rebuild and redraft primitives when they land.
- Expand recovery validation across state/projection families instead of outline lineage only.
- Add larger multi-chapter contamination fixture coverage.

---

## Source 45: `notes/2026-04-26-0081-planning.md`

# 2026-04-26 0081 Planning

## Context
- After `0080`, BookForge can localize outline lineage contamination and block unsafe main-branch mutation.
- Nanda can now reason from structured evidence, but cannot yet execute a full timeline recovery through composable BookForge tools.
- The shared design decision is:
  - BookForge provides timeline-safe query and mutation primitives.
  - Nanda provides author-level diagnosis, impact reporting, strategy, sequencing, approval flow, and explanation.

## Planning Update
- Added `0081-add-author-operable-timeline-recovery-and-story-weaving-primitives`.
- The new step treats "repair" as complete timeline recovery, not prose patching.
- The step covers:
  - recovery branch creation
  - explicit recovery anchor selection
  - artifact quarantine
  - outline normalization
  - output invalidation
  - state/projection rebuild
  - scoped redraft
  - branch validation
  - promotion with removals

## Boundary
- BookForge should not add a one-off `fix_veiled_ledger_chimera` command.
- Nanda should not mutate files directly.
- The intended operating model is Nanda composing reusable BookForge primitives from a `book_timeline_impact_report_v1`.

## Validation
- Planning-only update.
- Regenerated compiled plan projection with `resources/plans/compile-plan.py`.

---

## Source 46: `notes/2026-04-27-0081-blast-radius-slice.md`

# 2026-04-27 0081 Recovery Blast Radius Slice

## Summary
- Added `get_recovery_blast_radius(...)` as an impact-report-friendly recovery query surface.
- Added CLI support via `bookforge workflow recovery-blast-radius`.
- The surface combines existing branch-local invalidation previews into categorized artifact families:
  - prose
  - state
  - continuity
  - projection
  - series

## Contract Notes
- The surface is read-only and intended to run before destructive recovery actions.
- Prose impacts map to `invalidate_scope_outputs`.
- State, continuity, and projection impacts map to `rebuild_state_scope`.
- Series impacts are diagnostic-only in this slice because series canon is outside the current recovery branch mutation set.
- Every impact row declares:
  - artifact family
  - path
  - artifact status
  - whether the artifact exists
  - whether it is safe as canonical
  - recommended action
  - whether BookForge currently supports mutation for that family

## Files Touched
- `src/bookforge/query/recovery.py`
- `src/bookforge/query/__init__.py`
- `src/bookforge/cli.py`
- `tests/test_recovery_actions.py`
- `docs/help/index.md`
- `docs/help/workflow.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_blast_radius_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_blast_radius_full`
  - Result: `308 passed`

## Next
- Add downstream dependency tracing after redraft.
- Add promotion-result canonical integrity deltas.
- Expand validation from outline lineage into state/projection family health.

---

## Source 47: `notes/2026-04-27-0081-continuity-validation-slice.md`

# 2026-04-27 0081 Continuity Validation Slice

## Summary
- Added recovery-branch validation for continuity-family artifacts before promotion.
- `validate_recovery_branch` now scans:
  - `draft/context/continuity_pack.json`
  - `draft/context/continuity_history/*.json`
  - `draft/context/bible.md`
  - `draft/context/last_excerpt.md`
  - affected `draft/context/chapter_seams/ch_*/**/*.json`
- The validator blocks promotion when those artifacts retain:
  - character references that are absent from the normalized branch outline
  - stale `THREAD_*` references when the normalized outline exposes thread IDs
  - stale embedded `node.branch_id` or `selector.branch_id` values in JSON artifacts

## Boundary
- This is structural validation only.
- It prevents obvious ghost timeline continuity from surviving a recovery branch.
- It does not decide whether rebuilt continuity prose is narratively complete or good.

## Why
- Continuity artifacts can stay stale even when outline, prose, and character state have been normalized.
- Nanda needs these blockers reported through validation receipts before it can safely recommend promotion.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0081_continuity_validation_focus`
  - Result: `4 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_continuity_validation_full`
  - Result: `308 passed`

---

## Source 48: `notes/2026-04-27-0081-durable-validation-slice.md`

# 2026-04-27 0081 Durable Validation Slice

## Summary
- Added recovery-branch validation for durable inventory and plot-device state before promotion.
- `validate_recovery_branch` now scans branch-local durable artifacts under `draft/context`:
  - `item_registry.json`
  - `items/index.json`
  - `plot_devices.json`
  - `plot_devices/index.json`
  - `durable_commits.json`
  - item and plot-device history JSON files
- The validator blocks promotion when these artifacts retain:
  - character references that are absent from the normalized branch outline
  - stale embedded `node.branch_id` or `selector.branch_id` values
  - item/device index entries missing from their registries
  - stale `THREAD_*` references when the normalized outline exposes a thread ID set

## Boundary
- This is deterministic structural validation, not semantic inventory reasoning.
- It catches obvious stale timeline data such as ghost custodians, stale branch coordinates, and broken registry/index agreement.
- It does not yet infer whether an item, device, or inventory fact is narratively correct after a redraft.

## Why
- Timeline recovery cannot clear `chimera_risk` safely if branch-local durable state still contains ghost timeline entities.
- Nanda needs BookForge to surface these blockers as receipts and validation details, not require raw filesystem archaeology.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_durable_validation_focus2`
  - Result: `35 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_durable_validation_full`
  - Result: `308 passed`

---

## Source 49: `notes/2026-04-27-0081-projection-validation-slice.md`

# 2026-04-27 0081 Projection Validation Slice

## Summary
- Extended `validate_recovery_branch` beyond character state files.
- Validation now inspects affected branch-local:
  - chapter summaries
  - setting projections
  - appearance projections
- The branch is blocked when these artifacts reference non-outline character IDs or carry embedded `node`/`selector` branch coordinates from outside the recovery branch.

## Why
- A recovery branch can normalize outline data and rebuild character state while stale side projections still point at the polluted timeline.
- The Nanda author agent needs BookForge to reject that state before promotion instead of relying on the user to notice ghost facts in side data.

## Current Scope
- Implemented deterministic checks:
  - `char_*` references in affected summary/projection payloads must exist in the normalized outline character set.
  - Character-reference fields such as `character_id`, `characters`, `cast`, and `pov_character` must not name non-outline characters.
  - Projection artifacts with embedded `node.branch_id` or `selector.branch_id` must match the recovery branch.
- Deferred semantic checks:
  - continuity contradictions in prose-like summaries
  - location/setting semantic drift beyond stale branch coordinates and ghost character refs
  - inventory/deep-state validation

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_projection_validation_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_projection_validation_full`
  - Result: `308 passed`

## Next
- Add inventory/deep-state validation and downstream dependency tracing.

---

## Source 50: `notes/2026-04-27-0081-promotion-postcondition-slice.md`

# 2026-04-27 0081 Recovery Promotion Postcondition

## Summary
- Added canonical postcondition details to `promote_recovery_branch`.
- The promotion result now reports:
  - pre/post outline-lineage status
  - pre/post integrity status
  - planned promotion removals
  - applied promotion removals
  - whether main cleared chimera risk
  - whether main outline lineage and integrity are healthy after promotion

## Why
- Nanda needs to verify that a recovery plan actually changed canonical timeline health.
- A successful branch promotion is not enough by itself; the author layer needs to know whether `main` is now trusted and which invalid files were removed.

## Files Touched
- `src/bookforge/execution/recovery_validation.py`
- `tests/test_recovery_actions.py`
- `docs/help/index.md`
- `docs/help/workflow.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_promotion_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_promotion_full`
  - Result: `308 passed`

## Next
- Add downstream dependency tracing after redraft.
- Expand validation from outline lineage into state/projection family health.

---

## Source 51: `notes/2026-04-27-0081-recovery-postconditions-slice.md`

# 2026-04-27 0081 Recovery Receipt Postconditions

## Summary
- Added status-aware postcondition snapshots to every branch-local recovery receipt.
- The postcondition surface lets Nanda inspect an action result and see:
  - branch health after the action
  - outline lineage status after the action
  - completed and remaining successful recovery receipts
  - blockers and warnings after the action
  - recommended next recovery action
  - approval-required metadata
  - branch-local mutation scope and canonical-change status

## Important Behavior
- Receipt prerequisites are status-aware.
- A failed `validate_recovery_branch` receipt no longer satisfies the validation prerequisite.
- This matters because recovery branches may be validated multiple times while still missing rebuild/redraft work.
- The next-action snapshot should guide the author layer back to the next missing successful step instead of treating the first failed attempt as completion.
- While validating this slice, the full suite exposed that explicit chapter finalization after lock needed to remain a truthful `no_op` when the chapter was already finalized by section lock. That behavior is now handled at the chapter workflow level without weakening recovery branch mutation status.

## Files Touched
- `src/bookforge/execution/recovery_common.py`
- `tests/test_recovery_actions.py`
- `docs/help/index.md`
- `docs/help/workflow.md`
- `resources/plans/InProgress/bookforge-supervisable-engine/steps/0081-add-author-operable-timeline-recovery-and-story-weaving-primitives/step.md`
- `src/bookforge/section_workflow.py`

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_postconditions_focus`
  - Result: `35 passed`
- Regression focus after chapter-finalize no-op correction:
  - `python -m pytest -o addopts='' tests/test_execution_actions.py::test_finalize_chapter_action_returns_main_scoped_emitted_result tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_postconditions_focus`
  - Result: `36 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_postconditions_full`
  - Result: `308 passed`

## Next
- Run the full suite.
- Add blast-radius query surfaces for prose, state, series, continuity, and projection invalidation candidates.
- Extend promotion results with canonical post-promotion integrity deltas.

---

## Source 52: `notes/2026-04-27-0081-redraft-scope-slice.md`

# 2026-04-27 0081 Redraft Scope Slice

## Implemented
- Added `redraft_scope`.
  - Derived recovery branch only.
  - Reads affected scopes from the recovery manifest.
  - Prepares normalized affected sections as branch-local frozen sections with scene ranges from the normalized outline.
  - Delegates writing to the existing scoped section writer instead of creating a second prose pipeline.
  - Emits a recovery receipt with redrafted scopes and child write result ids.
- Added `redraft_scope` to:
  - execution exports
  - legal-action ordering
  - CLI workflow commands
  - recovery health gating
  - recovery validation requirements
- Validation now requires `redraft_scope` after `rebuild_state_scope`.

## Current Behavior
- `redraft_scope` may call the LLM-backed section writer in real workspaces.
- Tests mock the writer boundary and verify orchestration without model calls.
- The action does not yet support explicit salvage-reference injection.

## Validation
- Focused suite passed:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_redraft_focus`
  - Result: `35 passed`
- Full suite passed:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_redraft_full`
  - Result: `308 passed`

## Follow-Up
- Add explicit salvage-reference injection for redraft.
- Add richer postcondition receipts with next legal actions and integrity deltas.
- Add downstream/story-weaving validation after redraft.

---

## Source 53: `notes/2026-04-27-0081-state-rebuild-slice.md`

# 2026-04-27 0081 State Rebuild Slice

## Implemented
- Added `get_state_rebuild_preview(workspace, book_id, *, branch_id)`.
  - Reports branch-local state/projection candidates that `rebuild_state_scope` will quarantine.
  - Includes affected scopes, downstream scopes, affected chapters, affected scene ids, rebuild mode, candidate paths, and rebuilt output paths.
- Added `rebuild_state_scope`.
  - Derived recovery branch only.
  - Quarantines branch-local state/projection artifacts.
  - Records promotion removals so invalid main artifacts are removed during promotion.
  - Rewrites branch `state.json` to a clean outline-derived baseline.
  - Rebuilds branch character index/state files from normalized outline characters.
  - Reinitializes durable context files and resets bible/last excerpt.
- Added `rebuild_state_scope` to:
  - execution exports
  - action discovery/legal-action ordering
  - CLI workflow commands
  - recovery health gating
  - recovery validation requirements
- Hardened quarantine moves with a hashed fallback destination for long Windows paths while preserving source paths in receipts.

## Current Behavior
- The current state rebuild is intentionally conservative:
  - it performs a full branch-local context reset rather than a partial state rollback.
  - this is truthful because current state artifacts are not event-sourced enough to safely subtract only selected scenes or sections.
- `validate_recovery_branch` now refuses until the branch has receipts for:
  - `quarantine_artifacts`
  - `normalize_outline_scope`
  - `invalidate_scope_outputs`
  - `rebuild_state_scope`

## Validation
- Focused suite passed:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_state_focus`
  - Result: `35 passed`
- Full suite passed:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_state_full`
  - Result: `308 passed`

## Follow-Up
- Add `redraft_scope` as the next mutation primitive.
- Add richer state/projection validation after redraft, especially for downstream continuity and series memory.
- Eventually replace full context reset with event-sourced state rollback once state families carry reliable provenance.

---

## Source 54: `notes/2026-04-27-0081-state-validation-slice.md`

# 2026-04-27 0081 Recovery State Validation Slice

## Summary
- Added branch-local character state/projection validation to `validate_recovery_branch`.
- Validation now blocks promotion if the recovery branch contains character index entries or character state files whose `character_id` is absent from the normalized outline.

## Why
- This directly targets the Veiled Ledger ghost-character failure mode.
- Outline lineage can be healthy while stale state/projection data still contains invalid timeline entities.
- The branch must not promote if characters like `char_artie` or `char_vex` survive in state after outline normalization and state rebuild.

## Current Scope
- Implemented:
  - `draft/context/characters/index.json`
  - `draft/context/characters/*.state.json`
- Deferred:
  - continuity prose/fact extraction
  - settings/location projections
  - inventory/deep state
  - chapter summaries
  - appearance/setting projection semantic validation

## Validation
- Focused tests:
  - `python -m pytest -o addopts='' tests/test_recovery_actions.py tests/test_action_discovery.py --basetemp=.pytest_tmp_0081_state_validation_focus`
  - Result: `35 passed`
- Full suite:
  - `python -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_state_validation_full`
  - Result: `308 passed`

## Next
- Add validation for continuity, settings, inventory/deep state, chapter summaries, and appearance/setting projections.

---

## Source 55: `promotion.md`

# Promotion

Date: 2026-04-21

## Source
- Source draft path: `resources/plans/Drafts/bookforge-supervisable-engine`
- Source commit: `6895b8fccb4d20b18eb72baaec38e824eb3538fc`
- Source snapshot note: promoted from the current local working-tree draft on top of the source commit, because the reviewed plan refinements were not yet committed as a standalone git commit.

## Reason
- The engine plan has completed the draft review loop and is approved to become the active execution baseline.

## Transformation Summary
- Created a real `InProgress` stage root in BookForge planning.
- Promoted the reviewed engine plan into `resources/plans/InProgress/bookforge-supervisable-engine`.
- Preserved the draft folder as the frozen review baseline.
- Updated the promoted copy's top-level metadata from `Draft / Drafts` to `In Progress / InProgress`.
- Recompiled the promoted copy after promotion so the execution-stage projection matches the promoted source files.
- Mirrored the promoted shared plan into the Nanda workspace to keep the shared contract copy stage-aligned.

## Scope Of Promotion
- This promotion changes planning stage only.
- No runtime or product code is changed by the promotion itself.

## Immediate Expectation
- Future implementation work for the supervisable engine should execute against the `InProgress` copy.
- The `Drafts` copy remains the reviewed baseline for comparison and audit.
