# 0071 Make Scene And Section Write Execution Branch-Scoped

Status: pending

## Goal
- Let BookForge run scene-phase and section-range writing inside real derived branches instead of only on `main`, so the author or supervisor can rewrite old scenes, revise prior chapters, and isolate risky authoring work without forcing a full-book rerun.

## Problem
- `0070` gives us truthful scene-phase actions and a truthful section-range macro on `main`.
- That is necessary, but it is still single-root execution:
  - scene readiness is effectively `main` + active cursor only
  - scene actions are still `main_only`
  - section wrappers are still `main`-family commands even though they now use a dedicated section-range macro
- The current branch model is real, but shallow for writing:
  - branch manifests and branch-local current nodes already exist
  - branch snapshot roots already exist
  - rerun-freeze/materialization already exists on branches
  - promotion/assembly lifecycle already exists
- What is missing is branch-local writer truth.
- Today the system cannot truthfully support:
  - rewrite Chapter 1 Scene 2 while `main` is currently writing Chapter 9 Section 3
  - run two isolated scene writes in parallel without racing on canonical `main` state
  - let Nanda treat rewrite/recon work as a branch-scoped author move
- If we loosen `main` instead of making the writer branch-aware, we will recreate the same chimera class under a different name.

## Detailed Work
- Introduce an execution-root abstraction for write work.
  - `main` execution root points at the canonical book root.
  - derived-branch execution root points at the branch snapshot root.
  - scene-phase and section-range code must read/write only through that execution root.
- Make branch snapshots writer-complete.
  - Branch creation currently copies outline/state projections.
  - Expand the branch snapshot so it includes the write-side material a branch-scoped writer actually needs, such as:
    - `draft/chapters`
    - `draft/context`
    - phase-history content required for scene-phase reuse or resume
    - branch-local continuity/style anchor surfaces as needed
  - Keep the copied surface minimal but sufficient for truthful write execution.
- Generalize scene-phase readiness to branch scope.
  - `ScenePhaseReadiness` must resolve against:
    - `main`
    - or a derived branch selected through `ScopeSelector.branch_id`
  - It must stop assuming the active cursor scene on `main` is the only legal scene-phase target.
  - In a derived branch, the active cursor and active section come from the branch snapshot, not canonical `main`.
- Generalize scene-phase execution to branch scope.
  - Scene-phase request builders and executors must support derived branch execution.
  - Expected-node validation must compare against the branch-local current node, not `main`.
  - Produced-artifact receipts must be emitted to the branch-local supervision surface.
  - Scene actions should still refuse stale or mismatched lineage truthfully.
- Generalize section-range execution to branch scope.
  - `run_section_range(...)` should accept an execution root / branch selector.
  - A branch-local section-range run should:
    - use branch-local cursor truth
    - emit branch-local pause markers and execution receipts
    - not mutate canonical `main`
- Preserve strict `main` semantics.
  - `main` remains the canonical single-writer path.
  - Branch-scoped execution is the truthful route for:
    - off-cursor rewrite
    - recon work
    - parallel sibling write work
    - risky repair exploration
- Add branch-scoped write entry points.
  - Candidate first execution surfaces:
    - branch-scoped `scene-readiness`
    - branch-scoped `plan_scene`
    - branch-scoped `write_scene_prose`
    - branch-scoped `repair_scene_prose`
    - branch-scoped `apply_scene_commit`
    - branch-scoped section-range execution
  - Keep the first slice narrow. We do not need to expose every scene action in the first branch-aware pass if write/repair/commit prove the root.
- Keep branch writes isolated.
  - Branch-scoped execution must never mutate canonical state or canonical files directly.
  - All write outputs, receipts, pause markers, and current-node movement must stay branch-local until promotion.

## Surface Refinements
### Execution Root Rule
- Any write-capable action must execute against a resolved execution root.
- The root is determined by:
  - `main` branch => canonical book root
  - derived branch => branch snapshot root
- Query surfaces and execution surfaces must agree on the same root for one action request.

### Branch-Scoped Readiness
- A caller should be able to ask:
  - what is the current scene/section cursor inside branch `X`
  - what scene-phase actions are legal there
  - whether a historical scene is writable inside that branch even when `main` is elsewhere
  - what artifacts already exist inside the branch
  - whether the branch is stale relative to its parent snapshot

### Branch-Scoped Receipts
- Scene-phase and section-range receipts inside a branch must:
  - carry the branch-local `TimelineNodeRef`
  - write to branch-local supervision paths
  - declare artifact status using the shared vocabulary
  - never imply canonical mutation until promotion

## Nanda Impact
- This step is what turns "rewrite an older scene" from a hand-wavy future capability into a truthful engine-owned path.
- Nanda should eventually be able to:
  - inspect `main`
  - choose an old scene or section
  - create an isolated branch for rewrite
  - ask branch-local readiness questions
  - run branch-local scene or section write work
  - compare branch-local results without touching `main`
- This is also the prerequisite for honest author-side parallelism.

## Files Likely Touched
- `src/bookforge/runner.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/execution/scene_sequence.py`
- `src/bookforge/execution/scoped.py`
- `src/bookforge/query/scene_phase.py`
- `src/bookforge/query/actions.py`
- `src/bookforge/query/lineage.py`
- `src/bookforge/query/workspace.py`
- `src/bookforge/branching_store.py`
- `src/bookforge/branching_fork.py`
- `src/bookforge/branching_execution.py`
- `src/bookforge/execution/branch_actions.py`
- `src/bookforge/contracts/`
- `docs/help/workflow.md`
- `docs/help/run.md`
- `docs/help/index.md`

## Tests
- Add branch-scoped writer tests, for example:
  - `tests/test_branch_scene_phase_readiness.py`
  - `tests/test_branch_scene_action_execution.py`
  - `tests/test_branch_section_range_execution.py`
- Required behavior coverage:
  - create a branch from canonical state and run scene readiness against a historical scene while `main` is elsewhere
  - branch-scoped scene execution writes only into the branch snapshot
  - branch-scoped section-range execution can pause and resume without mutating `main`
  - branch-scoped commit produces authoritative artifacts inside the branch snapshot only
  - stale branch parent or stale expected node is detected truthfully
  - `main` remains unchanged after branch-local scene or section execution

## Definition Of Done
- A derived branch can resolve its own active cursor and scene-phase readiness without consulting canonical `main` cursor truth.
- A derived branch can execute at least one real scene-phase write path and one real section-range write path.
- A historical scene can be rewritten inside a branch even when `main` is currently writing a different chapter/section.
- Branch-local writer execution emits branch-local receipts, pause markers, and produced-artifact records.
- Canonical `main` state remains unchanged until explicit promotion.
- Truthful refusal surfaces exist for stale parent lineage, stale expected node, or invalid branch scope.

## Notes
- This step is about isolated authoring roots, not merge semantics.
- It intentionally stops short of:
  - parent-target promotion
  - rebase
  - parallel sibling assembly
- Those belong in the next step because they change merge and lifecycle contracts.
