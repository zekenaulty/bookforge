# 0060 Extract Minimal Engine Execution Surface For Nanda

Status: completed

## Goal
- Extract a smaller execution surface from the current workflow wrappers so Nanda can compose outlining, writing, linting, and repair as narrow engine actions instead of depending on large fixed command chains.

## Problem
- The current command surface is still too macro-shaped:
  - `workflow init`
  - `workflow freeze-section`
  - `workflow advance-section`
  - `workflow resume-paused-section`
  - `run`
- That is acceptable for transitional operator use, but it is the wrong long-term seam for an author agent.
- Nanda will need to steer execution as a choose-your-own-adventure loop:
  - inspect current truth
  - discover legal next actions
  - choose one narrow action
  - inspect the resulting receipt
  - continue or branch without re-encoding engine behavior outside BookForge
- If the CLI remains the only orchestration surface, two bad things happen:
  - BookForge logic gets trapped in wrapper commands instead of reusable engine actions
  - Nanda is forced to infer valid transitions from docs and historical behavior instead of asking the engine directly

## Detailed Work
- Split oversized workflow-control modules before extending the execution surface further.
  - `src/bookforge/branching.py` should be split by concern before more branch lifecycle and reconciliation logic lands.
  - Natural seams:
    - branch store / manifest / snapshot helpers
    - branch execution isolation helpers
    - branch lifecycle / promotion / assembly gating
- Define a smaller action catalog under `src/bookforge/execution/` or equivalent.
- Separate two layers explicitly:
  - macro workflow wrappers for CLI/operator convenience
  - narrow engine actions for programmatic composition
- Define at least one shared action descriptor contract for queryable action discovery, for example:
  - `ExecutionOption`
  - `AvailableAction`
  - or equivalent
- Each narrow action should declare:
  - supported workflow family
  - supported branch policy
  - required selector shape
  - required lineage preconditions
  - whether it may mutate canonical state
  - emitted receipt/result contract
  - legal next actions on success / pause / failure
- First extraction target should cover at least one path in each family:
  - outline/materialization:
    - initialize workflow
    - freeze section
    - finalize chapter
  - write/lint/repair:
    - resume paused write
    - write frozen section
    - optional narrower scene-step actions later if the runtime split is justified
  - branch lifecycle:
    - create branch
    - discard branch
    - validate assembly
    - promote branch
- Add a query seam that returns legal next actions from the current engine state.
  - Inputs:
    - `ScopeSelector`
    - current `TimelineNodeRef`
    - integrity verdict
    - branch lifecycle state when applicable
  - Output:
    - explicit legal action list
    - refusal reasons for currently illegal actions
- Keep BookForge as the authority on valid transitions.
  - Nanda should choose among legal actions.
  - Nanda should not own the engine transition graph.
- Make the CLI wrappers consume the same action layer instead of duplicating orchestration logic.
- Document the choose-your-own-adventure rule clearly:
  - query truth
  - query legal next actions
  - execute one narrow action
  - inspect receipt
  - repeat

## Files Likely Touched
- `src/bookforge/execution/__init__.py`
- `src/bookforge/execution/scoped.py`
- `src/bookforge/execution/` new action modules
- `src/bookforge/query/workflow.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/contracts/` new action-discovery contract if needed
- `src/bookforge/cli.py`
- `src/bookforge/branching.py` or its split replacements
- `docs/help/workflow.md`
- `docs/help/run.md`
- `docs/help/index.md`

## Tests
- Add execution-surface tests, for example:
  - `tests/test_execution_actions.py`
  - `tests/test_action_discovery.py`
  - `tests/test_branch_action_lifecycle.py`
- Add at least one integration test that proves:
  - query current truth
  - query legal next actions
  - execute a narrow action
  - observe the next legal action set change
- Add at least one real branch flow integration test:
  - create branch
  - run scoped action in branch
  - promote branch
  - verify canonical surface and lineage receipt on `main`
- Current executed validation:
  - `python -m pytest --basetemp .pytest_tmp_0060_branch_action tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060c tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_branch_lifecycle tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060d tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_assembly_action tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060e tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_assembly_create tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060f tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_finalize tests/test_execution_actions.py tests/test_action_discovery.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060g tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_lock tests/test_execution_actions.py tests/test_action_discovery.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_scoped_execution.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060h tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`
  - `python -m pytest --basetemp .pytest_tmp_0060_write tests/test_execution_actions.py tests/test_action_discovery.py tests/test_scoped_execution.py tests/test_section_workflow.py tests/test_chapter_seam.py`
  - `python -m pytest --basetemp .pytest_tmp_regression_0060i tests/test_execution_actions.py tests/test_action_discovery.py tests/test_branch_execution.py tests/test_branch_promotion.py tests/test_fork_group_assembly.py tests/test_scoped_execution.py tests/test_supervision_emit.py tests/test_query_workspace.py tests/test_query_lineage.py tests/test_query_integrity.py tests/test_scope_contracts.py tests/test_timeline_node.py tests/test_section_workflow.py tests/test_chapter_seam.py tests/test_runner_outline_gate.py tests/test_workspace_init.py`

## Definition Of Done
- BookForge exposes a smaller execution action surface that is distinct from CLI wrappers.
- At least one outline/materialization path and one write/resume path are callable through narrow engine actions.
- The engine can report legal next actions from current truth without requiring Nanda to infer them externally.
- CLI wrappers call the extracted action layer instead of retaining unique orchestration logic.
- Branch lifecycle actions are available through the same execution-surface model.
- The action layer preserves the current truth model:
  - `TimelineNodeRef`
  - `ScopeSelector`
  - reconciliation receipts
  - integrity and lineage enforcement
- No new control-surface work is added by growing `branching.py` further; oversized modules are split first.

## Notes
- This is not a generic agent framework story.
- It is a controlled extraction story: turn the existing engine into a smaller, composable action surface while keeping BookForge in charge of prose generation and canonical mutation.
- Current implemented slice:
  - `ExecutionOption` contract for queryable action discovery
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
  - narrow `initialize_section_workflow` execution adapter under `bookforge.execution`
  - narrow `freeze_section_from_phase03_artifact` execution adapter under `bookforge.execution`
  - narrow `write_frozen_section` execution adapter under `bookforge.execution`
  - narrow `lock_section_from_written_state` execution adapter under `bookforge.execution`
  - narrow `finalize_chapter_from_locked_sections` execution adapter under `bookforge.execution`
  - narrow `create_assembly_branch` execution adapter under `bookforge.execution`
  - narrow `create_branch` execution adapter under `bookforge.execution`
  - narrow `discard_branch` execution adapter under `bookforge.execution`
  - narrow `promote_branch_to_main` execution adapter under `bookforge.execution`
  - narrow `record_assembly_validation` execution adapter under `bookforge.execution`
  - existing `resume_paused_section` adapter remains the pause-aware write/resume counterpart
  - `bookforge workflow init`, `bookforge workflow freeze-section`, `bookforge workflow write-section`, `bookforge workflow lock-section`, and `bookforge workflow finalize-chapter` now route through the extracted execution adapters
  - `bookforge workflow legal-actions` exposes the same action-discovery seam for operator use
  - `bookforge workflow legal-actions --branch-id <id>` now exposes derived-branch legality for discard/promotion/assembly-validation checks
  - `bookforge workflow legal-actions --fork-group-id <id>` now exposes main-branch fork-group legality for assembly creation
  - `bookforge workflow advance-section` now composes extracted actions instead of calling its own orchestration path
- Follow-on work:
  - extract deeper write/lint/repair sub-actions if the choose-your-own-adventure author loop needs per-scene or per-phase control beyond section-level write and truthful pause/resume
  - add success/pause/failure next-action hints to the action descriptors if the current simpler descriptor stops being sufficient
