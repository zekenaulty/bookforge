# bookforge-supervisable-engine

## Compiled Plan Metadata

- Plan Scope: `InProgress/bookforge-supervisable-engine`
- Compiled At (UTC): `2026-04-21T19:04:50Z`
- Source Document Count: `12`
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
12. `promotion.md`

---

## Source 1: `plan.md`

# BookForge Supervisable Engine

Status: In Progress
Stage: InProgress
Owner: BookForge engine workstream
Last Updated: 2026-04-21

## Objective
- Make BookForge truthful and supervisable by Nanda without moving prose generation or canonical state mutation out of BookForge.
- Convert the current section workflow, write loop, lint/repair loop, recovery paths, and future fan-out/fan-in work into explicit engine-owned contracts that can be queried, verified, resumed, and isolated safely.

## Why Now
- The section workflow is now real, but the runtime still blurs thin outline, deep outline, section-local work, and recovery import in ways that allow scope drift.
- `veiled_ledger_b1` exposed the exact failure class this plan needs to prevent: a valid engine continuing against mixed lineage and overscoped recovery artifacts.
- Nanda planning has stabilized enough that the shared boundary is now clear: BookForge must emit truthful scope, lineage, pause, and result surfaces instead of forcing the operator layer to infer them from raw files.
- The next architectural pressure is not just safer reruns. It is safe concurrency. If the contract model cannot distinguish canonical state, isolated rerun branches, and future parallel section branches, the same chimera class will return under a different name.
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

## Non-Goals
- No Nanda supervisor logic in this repo.
- No React or operator UI work.
- No generic agent framework.
- No rewrite of the entire outline or write pipeline.
- No attempt to build a full generic scheduler for all future branches in the first slice.
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
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/scope_selector.py`
- `src/bookforge/contracts/state_surface.py`
- `src/bookforge/contracts/issue_ticket.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- Query and contract tests
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
| 0010-freeze-scope-lineage-and-contract-vocabulary | draft | - | Freeze runtime vocabulary, coordinate primitives, artifact truth rules, and caller-visible scope semantics. |
| 0020-add-read-only-query-surface | draft | 0010 | Expose workflow, lineage, integrity, character, continuity, and scope-to-node resolution through small query modules. |
| 0030-emit-versioned-state-surfaces-and-issue-tickets | draft | 0010, 0020 | Emit book-rooted state, pause, and issue contracts that carry timeline coordinates. |
| 0040-add-truthful-scoped-execution-and-bounded-resume | draft | 0010, 0020, 0030 | Support one narrow main-branch resume path with expected-node validation and truthful pause reporting. |
| 0045-add-isolated-branch-reruns-and-fork-group-assembly | draft | 0030, 0040 | Add branch isolation, sibling fork groups, promotion vs assembly semantics, and validation-gated merge paths. |
| 0050-harden-reconciliation-integrity-and-command-surface | draft | 0030, 0040, 0045 | Add post-execution and post-promotion reconciliation, stronger integrity helpers, and help-doc coherence. |

---

## Source 6: `steps/0010-freeze-scope-lineage-and-contract-vocabulary/step.md`

# 0010 Freeze Scope, Lineage, And Contract Vocabulary

Status: draft

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

---

## Source 7: `steps/0020-add-read-only-query-surface/step.md`

# 0020 Add Read-Only Query Surface

Status: draft

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

---

## Source 8: `steps/0030-emit-versioned-state-surfaces-and-issue-tickets/step.md`

# 0030 Emit Versioned State Surfaces And Issue Tickets

Status: draft

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

Status: draft

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

Status: draft

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

## Files Likely Touched
- `src/bookforge/contracts/timeline_node.py`
- `src/bookforge/contracts/state_surface.py`
- `src/bookforge/contracts/issue_ticket.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/runner.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/pipeline/chapter_seam.py`
- `docs/help/workflow.md`
- `docs/help/run.md`

## Tests
- `python -m pytest tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_query_lineage.py tests/test_query_integrity.py`
- Add coverage for:
  - branch creation from a declared parent node
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

---

## Source 11: `steps/0050-harden-reconciliation-integrity-and-command-surface/step.md`

# 0050 Harden Reconciliation, Integrity, And Command Surface

Status: draft

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
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/section_workflow.py`
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

---

## Source 12: `promotion.md`

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
