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
