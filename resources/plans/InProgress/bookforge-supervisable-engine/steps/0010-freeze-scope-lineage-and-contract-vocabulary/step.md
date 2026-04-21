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
