# bookforge-supervisable-engine

## Compiled Plan Metadata

- Plan Scope: `InProgress/bookforge-supervisable-engine`
- Compiled At (UTC): `2026-04-22T13:12:14Z`
- Source Document Count: `21`
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
13. `notes/2026-04-21-0010-execution.md`
14. `notes/2026-04-21-0020-execution.md`
15. `notes/2026-04-21-0030-execution.md`
16. `notes/2026-04-21-0040-execution.md`
17. `notes/2026-04-21-0045-execution.md`
18. `notes/2026-04-21-0050-execution.md`
19. `notes/2026-04-22-0050-execution.md`
20. `notes/2026-04-22-0060-execution.md`
21. `promotion.md`

---

## Source 1: `plan.md`

# BookForge Supervisable Engine

Status: In Progress
Stage: InProgress
Owner: BookForge engine workstream
Last Updated: 2026-04-22

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
- Nanda should eventually be able to run BookForge as a choose-your-own-adventure author loop:
  - observe current node and integrity
  - ask BookForge what actions are legal next
  - choose one narrow action
  - inspect the resulting receipt
  - continue without depending on a monolithic command path
- The important boundary rule does not change:
  - BookForge still owns prose generation and canonical state mutation
  - Nanda chooses among legal engine actions and evaluates the outcomes
- This means the medium-term API shape is:
  - query surfaces for truth and legal-next-action discovery
  - execution actions for narrow engine moves
  - macro workflow commands as wrappers over those same actions, not a separate logic layer

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
- Add a read-only query surface under `src/bookforge/query/`.
- Emit versioned engine contracts:
  - `TimelineNodeRef`
  - `ScopeSelector`
  - `StateSurface`
  - `IssueTicket`
  - `ExecutionRequest`
  - `ExecutionResult`
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

## Constraints
- BookForge keeps ownership of prose generation and canonical workspace mutation.
- Query modules stay read-only.
- New modules should target roughly `80-250` lines. Split aggressively at `>300`.
- Prefer small typed data objects at the boundary instead of raw dict blobs passed through unrelated modules.
- Do not normalize legacy accidental behavior as a contract just because live workspaces already contain it.
- Every non-main branch must declare its parent `TimelineNodeRef`.
- No silent source switching inside a branch.
- No promotion or assembly without explicit reconciliation and integrity validation.
- Parallel siblings may not read one another during execution.
- Fork-group assembly must use the frozen parent snapshot declared at fork time unless an explicit rebase or recreation step occurs.
- Existing working-tree changes outside this plan scope are not part of this draft and must remain untouched.

## Dependencies
- The section-chunked workflow remains the primary runtime spine.
- Current chapter seam audit/finalization work remains a dependency, not a replacement for these contracts.
- The Nanda operator plan depends on this plan's steps `0010-0045`.
- The future Nanda author-loop work depends on a later extraction step that turns the workflow wrappers into a smaller choose-your-own-adventure execution surface.

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

## Source 13: `notes/2026-04-21-0010-execution.md`

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

## Source 14: `notes/2026-04-21-0020-execution.md`

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

## Source 15: `notes/2026-04-21-0030-execution.md`

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

## Source 16: `notes/2026-04-21-0040-execution.md`

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

## Source 17: `notes/2026-04-21-0045-execution.md`

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

## Source 18: `notes/2026-04-21-0050-execution.md`

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

## Source 19: `notes/2026-04-22-0050-execution.md`

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

## Source 20: `notes/2026-04-22-0060-execution.md`

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

## Source 21: `promotion.md`

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
