# 2026-04-28 Adaptive Seam, Bridge, And Loop Surfaces

## Summary
- Added the next BookForge-side adaptive authoring surfaces Nanda needs after `continue_scene`:
  - branch-local scene-pair seam alignment
  - read-only chapter seam queue
  - read-only scene-pair seam detail
  - branch-local bridge-scene insertion planning
  - same-section branch-local bridge-scene insertion apply/materialization
  - query-only higher-level author loop envelopes
- These surfaces preserve the graph-traversal model:
  - BookForge reports legal moves, readiness, receipts, and artifact truth.
  - Nanda chooses loop policy, budgets, interruption behavior, and user-facing explanation.

## Implemented Surfaces
- `bookforge.query.get_author_loop_envelopes(...)`
  - Returns `continue_one_step`, `continue_scene`, `continue_section`, and `continue_chapter` envelope options.
  - Read-only. It does not start a loop.
  - Carries target scope, allowed actions, mutation scope, stop conditions, canonical-change expectation, and blocked reason.
- `align_scene_pair_seam_action(...)`
  - Derived-branch only.
  - Uses the existing LLM chapter seam repair prompt contract against one adjacent scene pair.
  - Preserves original scene markdown before replacement.
  - Emits pair seam report plus branch-local scene artifact receipts.
  - Does not mutate canonical `main`.
- `bookforge.query.get_chapter_seam_queue(...)`
  - Read-only.
  - Lists adjacent outline scene pairs for a selected chapter and branch.
  - Reports whether each pair is ready, blocked, or already aligned.
  - Surfaces existing scene-pair seam report status/path when present.
  - Maps ready pairs to `align_scene_pair_seam` without executing it.
- `bookforge.query.get_scene_pair_seam_detail(...)`
  - Read-only.
  - Inspects one adjacent scene pair.
  - Reuses queue readiness/blocking logic.
  - Surfaces report status, before/after issue counts, repair count, emitted scene artifact refs, and optionally the full report payload.
- `plan_bridge_scene_insertion_action(...)`
  - Derived-branch only.
  - Writes a provisional bridge-scene proposal artifact.
  - Does not mutate outline order, renumber scenes, create a scene card, or write prose.
- `apply_bridge_scene_insertion_action(...)`
  - Derived-branch only.
  - Consumes an existing bridge-scene insertion proposal.
  - Inserts an unwritten bridge scene into the same section by shifting following branch-local integer scene ids.
  - Updates branch-local outline, snapshot registry, and outline projections.
  - Moves following branch-local prose/meta, phase-history, setting, and appearance artifacts up by one scene id.
  - Leaves prose generation to normal `plan_scene` / `continue_scene` traversal.

## Capability Projection
- Added implemented descriptors:
  - `query.author_loop_envelopes`
  - `query.chapter_seam_queue`
  - `query.scene_pair_seam_detail`
  - `action.align_scene_pair_seam`
  - `action.plan_bridge_scene_insertion`
  - `action.apply_bridge_scene_insertion`
- Replaced older designed-gap descriptors for generic scene-pair alignment and scene insertion with implemented baseline surfaces.

## Nanda Contract Notes
- Nanda can now show a truthful "continue section/chapter" envelope without claiming BookForge has started a hidden long-running loop.
- Nanda can query the chapter seam queue before offering pairwise seam workbench actions.
- Nanda can inspect one seam pair report/detail after queue selection or after alignment.
- Nanda can use seam alignment as an optional branch-local action after adjacent scenes exist.
- Nanda can use bridge-scene planning as evidence when a transition needs a new beat.
- Nanda can apply same-section bridge insertion inside a derived branch, then use normal scene-phase actions to plan and write the inserted scene.
- Nanda should still treat cross-section bridge insertion as unsupported until a future ref-map/downstream-validation expansion exists.

## Validation
- Focused adaptive tests:
  - `python -m pytest tests/test_adaptive_authoring_actions.py -q`
- Capability projection tests:
  - `python -m pytest tests/test_capability_projection.py -q`
- Serial focused regression:
  - `python -m pytest tests/test_action_discovery.py tests/test_branch_execution.py tests/test_capability_projection.py tests/test_writing_target.py tests/test_adaptive_authoring_actions.py -q`

## Follow-Up
- Expand `apply_bridge_scene_insertion` beyond same-section pairs only after stable cross-section ref-map and downstream-validation rules are pinned.
- Add a narrower scene-pair seam readiness-only projection only if Nanda needs it separate from queue/detail.
- Add richer real-prompt seam fixtures for duplicated UI prompt overlap, repeated regrounding, and tense-blending examples.
