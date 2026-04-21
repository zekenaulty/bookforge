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
