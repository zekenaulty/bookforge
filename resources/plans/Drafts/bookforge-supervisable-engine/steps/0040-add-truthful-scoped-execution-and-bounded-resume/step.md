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
