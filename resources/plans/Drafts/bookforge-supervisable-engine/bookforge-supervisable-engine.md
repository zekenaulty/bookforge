# bookforge-supervisable-engine

## Compiled Plan Metadata

- Plan Scope: `Drafts/bookforge-supervisable-engine`
- Compiled At (UTC): `2026-04-21T17:42:50Z`
- Source Document Count: `10`
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
10. `steps/0050-harden-reconciliation-integrity-and-command-surface/step.md`

---

## Source 1: `plan.md`

# BookForge Supervisable Engine

Status: Draft
Stage: Drafts
Owner: BookForge engine workstream
Last Updated: 2026-04-21

## Objective
- Make BookForge truthful and supervisable by Nanda without moving prose generation or canonical state mutation out of BookForge.
- Convert the current section workflow, write loop, lint/repair loop, and recovery paths into explicit engine-owned contracts that can be queried, verified, and resumed safely.

## Why Now
- The section workflow is now real, but the runtime still blurs thin outline, deep outline, section-local work, and recovery import in ways that allow scope drift.
- `veiled_ledger_b1` exposed the exact failure class this plan needs to prevent: a valid engine continuing against mixed lineage and overscoped recovery artifacts.
- Nanda planning has stabilized enough that the shared boundary is now clear: BookForge must emit truthful scope, lineage, pause, and result surfaces instead of forcing the operator layer to infer them from raw files.
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

## Scope
- Freeze BookForge-owned mode vocabulary and lineage rules:
  - `thin_outline`
  - `deep_outline`
  - `section_local_outline`
  - `section_write`
  - `recovery_import`
  - `retryable_pause`
  - `hard_fail`
- Add a read-only query surface under `src/bookforge/query/`.
- Emit versioned engine contracts:
  - `StateSurface`
  - `IssueTicket`
  - `ExecutionRequest`
  - `ExecutionResult`
- Support one truthful scoped execution path with bounded pause/resume behavior.
- Reconcile and validate lineage before returning control to the caller.
- Align help docs and command labels with actual runtime semantics.

## Non-Goals
- No Nanda supervisor logic in this repo.
- No React or operator UI work.
- No generic agent framework.
- No rewrite of the entire outline or write pipeline.
- No silent fallback between workflow families.
- No use of mutable compatibility views such as `outline.json` as implicit canonical lineage anchors when immutable run artifacts exist.
- No duplicate thought-signature lineage system unless existing carry paths prove insufficient.

## Deliverables
- `src/bookforge/query/__init__.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/integrity.py`
- `src/bookforge/query/characters.py`
- `src/bookforge/query/continuity.py`
- `src/bookforge/contracts/__init__.py`
- `src/bookforge/contracts/state_surface.py`
- `src/bookforge/contracts/issue_ticket.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- Query and contract tests
- One narrow execution adapter backed by the existing workflow/write surfaces
- Help and command-surface updates that tell the truth about scope and recovery

## Plan-Level Definition Of Done
- A caller can query workflow family, run mode, source run, source artifact class, active section, and integrity verdict through stable Python entry points.
- BookForge emits a versioned state surface and categorized issue tickets after at least one real execution path.
- Provider exhaustion resolves to `retryable_pause` or `hard_fail`, not multi-hour hidden retries as the only visible behavior.
- One narrow `ExecutionRequest -> ExecutionResult` path works without a hidden workflow-family switch.
- Section materialization can be traced to immutable source runs or frozen chapter projections instead of mutable merged outline views.
- Reconciliation and lineage validation run before control returns to the caller.
- Help docs stop implying scope that the runtime does not actually execute.

## Constraints
- BookForge keeps ownership of prose generation and canonical workspace mutation.
- Query modules stay read-only.
- New modules should target roughly `80-250` lines. Split aggressively at `>300`.
- Prefer small typed data objects at the boundary instead of raw dict blobs passed through unrelated modules.
- Do not normalize legacy accidental behavior as a contract just because live workspaces already contain it.
- Existing working-tree changes outside this plan scope are not part of this draft and must remain untouched.

## Dependencies
- The section-chunked workflow remains the primary runtime spine.
- Current chapter seam audit/finalization work remains a dependency, not a replacement for these contracts.
- The Nanda operator plan depends on this plan's steps `0010-0040`.

## Step Outline
- See `steps/index.md` and the numbered step folders for execution-shaped stories.

---

## Source 2: `decisions/initial-decisions.md`

# Initial Decisions

- BookForge remains the only system allowed to generate prose or mutate canonical book state.
- Nanda will consume BookForge truth; it should not have to reverse-engineer hidden runtime mode from raw files forever.
- Thin outline, deep outline, section-local outline, section write, and recovery import are distinct runtime modes and may not silently promote into one another.
- Immutable outline run artifacts and frozen chapter projections are the preferred lineage anchors.
- Mutable compatibility artifacts such as `outline.json` are never sufficient by themselves to justify scoped materialization.
- Query modules belong under `src/bookforge/query/` and must remain read-only.
- Shared engine contract objects belong under `src/bookforge/contracts/`.
- The first truthful supervised issue class is lineage/integrity conflict, because it is both mechanical and already proven by live failures.
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
- Derived prose features can sprawl into expensive or low-signal machinery if introduced before the state and ticket contracts are stable.
- The repo already contains older and newer planning shapes; without discipline, this plan can become another disconnected artifact instead of the local BookForge source of truth.

---

## Source 4: `validation/acceptance.md`

# Acceptance

This plan is ready for promotion only when the target implementation can satisfy all of the following:

- BookForge exposes workflow, lineage, integrity, and book state through stable read-only query modules.
- At least one real execution path emits:
  - a versioned `StateSurface`
  - categorized `IssueTicket` output
  - a truthful pause/result status
- One narrow `ExecutionRequest -> ExecutionResult` path can be executed and verified without hidden scope switching.
- Lineage validation runs before section materialization or resume proceeds.
- Provider exhaustion can be observed as `retryable_pause` or `hard_fail` without reading raw transport logs.
- Help docs and CLI labels match the actual runtime mode and recovery behavior.
- New code follows the small-file rule and does not normalize `300-600` line modules as acceptable.

---

## Source 5: `steps/index.md`

# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-freeze-scope-lineage-and-contract-vocabulary | draft | - | Freeze runtime vocabulary, artifact truth rules, and caller-visible scope semantics. |
| 0020-add-read-only-query-surface | draft | 0010 | Expose workflow, lineage, integrity, character, and continuity reads through small query modules. |
| 0030-emit-versioned-state-surfaces-and-issue-tickets | draft | 0010, 0020 | Emit engine-owned state, pause, and issue surfaces after execution. |
| 0040-add-truthful-scoped-execution-and-bounded-resume | draft | 0010, 0020, 0030 | Support one narrow same-mode execution/resume path with truthful result reporting. |
| 0050-harden-reconciliation-integrity-and-command-surface | draft | 0030, 0040 | Add post-execution reconciliation, stronger integrity helpers, and help-doc coherence. |

---

## Source 6: `steps/0010-freeze-scope-lineage-and-contract-vocabulary/step.md`

# 0010 Freeze Scope, Lineage, And Contract Vocabulary

Status: draft

## Goal
- Freeze the BookForge-owned runtime vocabulary before more code lands on top of accidental behavior.

## Problem
- Current docs and runtime behavior still permit ambiguous interpretations of:
  - thin outline vs deep outline
  - section-local work vs batch outline
  - same-mode resume vs recovery import
  - immutable lineage anchors vs mutable compatibility views
- Without a frozen vocabulary, both BookForge changes and Nanda integration will keep normalizing scope drift.

## Detailed Work
- Define the engine-owned runtime modes and result states in one place.
- Freeze which existing artifacts count as:
  - immutable lineage anchors
  - frozen projections
  - mutable compatibility views
  - diagnostic-only artifacts
- Align help docs with those definitions.
- Add a small central code surface for caller-visible mode labels and source artifact classification.
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
- `src/bookforge/contracts/state_surface.py`

## Tests
- `python -m pytest tests/test_section_workflow.py tests/test_workspace_init.py tests/test_runner_outline_gate.py`
- Add a small contract-label test if central enums/labels are introduced, for example `tests/test_scope_contracts.py`

## Definition Of Done
- Runtime mode vocabulary is frozen in code and docs.
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
- Expose stable, small, testable read APIs over current BookForge workflow state, lineage anchors, and integrity evidence.

## Problem
- Current diagnostics require direct file inspection across many workspace artifacts.
- That forces Nanda to scrape raw files and makes BookForge runtime truth harder to reuse inside its own tests and command paths.

## Detailed Work
- Add `src/bookforge/query/workspace.py` for:
  - active book/cursor
  - section status
  - active section
  - current pause marker or progress heartbeat
- Add `src/bookforge/query/workflow.py` for:
  - workflow family
  - run mode
  - last explicit workflow action
  - source artifact class
- Add `src/bookforge/query/lineage.py` for:
  - immutable source run lookup
  - frozen chapter projection lookup
  - section draft lineage
  - materialization source classification
- Add `src/bookforge/query/integrity.py` for:
  - outline vs prose vs state disagreement summaries
  - mutable-source usage detection
  - chimera-risk indicators
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

## Definition Of Done
- A caller can ask BookForge for workflow family, source run, active section, and integrity verdict without hand-reading JSON files.
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
- Make BookForge emit engine-owned state, issue, and pause surfaces after execution so supervision can act on explicit truth instead of inference.

## Problem
- Current execution artifacts are rich but uneven:
  - progress heartbeats
  - run logs
  - phase history
  - outline artifacts
  - scene meta
- They do not yet combine into one stable, versioned contract surface.

## Detailed Work
- Implement contract objects under `src/bookforge/contracts/`:
  - `state_surface.py`
  - `issue_ticket.py`
  - `execution_request.py`
  - `execution_result.py`
- Define revision behavior for `StateSurface` so pre/post execution comparisons are deterministic.
- Emit categorized `IssueTicket` output from the first supervised issue class:
  - `scope_contract_violation`
  - `lineage_conflict`
  - `chimera_risk`
  - `provider_retry_exhausted`
  - `recovery_mode_required`
- Emit explicit pause state when bounded retry policy is exhausted.
- Thread emission into existing section-local execution without building a second state system.
- Persist enough scope metadata to reconstruct:
  - workflow family
  - chapter/section/scene target
  - source lineage
  - pre/post revision ids

## Files Likely Touched
- `src/bookforge/contracts/__init__.py`
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
- `python -m pytest tests/test_state_surface.py tests/test_issue_tickets.py tests/test_pause_marker.py tests/test_section_workflow.py tests/test_runner_targeting.py`
- Add one integration-style assertion that a real scoped run emits a revisioned state surface and categorized issue output

## Definition Of Done
- One real execution path emits a versioned `StateSurface`.
- One real integrity failure emits categorized `IssueTicket` output.
- One bounded provider stall can be observed as a pause/result state rather than opaque log churn.
- Revision ids make pre/post execution comparisons unambiguous.

## Notes
- This story should stay focused on the first useful contract surface, not every future metric or detector.

---

## Source 9: `steps/0040-add-truthful-scoped-execution-and-bounded-resume/step.md`

# 0040 Add Truthful Scoped Execution And Bounded Resume

Status: draft

## Goal
- Support one narrow `ExecutionRequest -> ExecutionResult` path without pretending BookForge already has a generic agent runtime.

## Problem
- Current command surfaces can resume real work, but they still expose too much implicit behavior:
  - same-mode resume
  - recovery import
  - outline gate bypass
  - provider stall handling
- That makes it too easy for external callers to request one thing and get another.

## Detailed Work
- Pick one narrow execution class as the first truthful path:
  - default candidate: resume a paused section within the same workflow family and lineage
- Define the minimum `ExecutionRequest` fields required for that path:
  - target scope
  - expected workflow family
  - expected source lineage
  - allowed move class or explicit recovery approval marker
- Add a small execution adapter that translates the request into existing BookForge operations.
- Refuse overscoped or mismatched requests explicitly instead of silently switching modes.
- Bound provider retry behavior so the caller gets either:
  - `success`
  - `retryable_pause`
  - `hard_fail`
- Return `ExecutionResult` with:
  - status
  - artifact refs
  - pre/post revisions
  - new issue tickets
  - whether the run remained in the requested mode

## Files Likely Touched
- `src/bookforge/cli.py`
- `src/bookforge/runner.py`
- `src/bookforge/section_workflow.py`
- `src/bookforge/workspace.py`
- `src/bookforge/contracts/execution_request.py`
- `src/bookforge/contracts/execution_result.py`
- `docs/help/workflow.md`
- `docs/help/run.md`

## Tests
- `python -m pytest tests/test_scoped_execution.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_runner_targeting.py tests/test_pause_marker.py`
- Add coverage for refusal paths where requested workflow family or source lineage does not match live workspace truth

## Definition Of Done
- A caller can submit one narrow execution request without knowing internal phase choreography.
- The request cannot silently switch workflow families or source lineage.
- Provider exhaustion yields a truthful pause/fail result.
- The result contains enough information for a delegate/verify loop.

## Notes
- A truthful narrow execution path is better than a fake generic control surface.

---

## Source 10: `steps/0050-harden-reconciliation-integrity-and-command-surface/step.md`

# 0050 Harden Reconciliation, Integrity, And Command Surface

Status: draft

## Goal
- Make the first supervised path safe enough for repeated use and difficult to misuse through misleading docs, stale artifacts, or partial reconciliation.

## Problem
- The first four stories can expose truthful surfaces, but callers still need strong guarantees that:
  - state was reconciled before control returned
  - no-op or stale writes are visible
  - degraded integrity is surfaced instead of swallowed
  - help text does not overclaim runtime scope

## Detailed Work
- Add mandatory post-execution reconciliation before returning control.
- Add pre/post revision diff helpers for state-surface comparison.
- Strengthen integrity helpers so they can flag:
  - mixed workflow-family contamination
  - mutable-source materialization
  - outline/prose/state disagreement
  - overscoped recovery
- Surface no-op, stale-write, downgraded-integrity, and recovery-required outcomes explicitly.
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

## Definition Of Done
- Every supported execution result can be classified as success, no-op, pause, hard-fail, or integrity-degraded.
- Integrity regressions introduced during repair are surfaced, not swallowed.
- Help docs do not imply a broader runtime scope than the code actually executes.
- Callers can tell whether a request changed canonical state and whether integrity improved or worsened.

## Notes
- This story is where the command/help surface finally becomes trustworthy enough for external orchestration.
