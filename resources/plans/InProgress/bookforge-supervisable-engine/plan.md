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
