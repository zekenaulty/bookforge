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
