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
