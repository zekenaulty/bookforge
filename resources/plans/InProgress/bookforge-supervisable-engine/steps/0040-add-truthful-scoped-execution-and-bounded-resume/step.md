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
