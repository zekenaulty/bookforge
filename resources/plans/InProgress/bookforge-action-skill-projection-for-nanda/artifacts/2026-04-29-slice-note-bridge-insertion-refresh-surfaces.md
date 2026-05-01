# Slice Note: Bridge Insertion Refresh Surfaces

Date: 2026-04-29

Repo: BookForge / `ai-book`

Owner: BookForge engine workstream

## Slice

Follow up on Nanda's `apply_bridge_scene_insertion` wiring by verifying the read-side refresh surfaces after the branch-local apply job completes.

Nanda's next hardening item is post-job refresh:

- reader state
- branch artifact index
- branch diff summary
- branch detail/legal actions
- apply report visibility

## Change

BookForge now classifies bridge-scene insertion artifacts more explicitly in branch artifact indexes:

- `draft/context/bridge_scenes/**/*_apply_report.json`
  - `artifact_class=adaptive_authoring_report`
  - `artifact_status=diagnostic`
- other `draft/context/bridge_scenes/**`
  - `artifact_class=adaptive_authoring_plan`
  - `artifact_status=provisional`

This keeps branch artifact query status aligned with execution receipts:

- planning artifacts are provisional
- apply reports are diagnostic
- branch outline and snapshot registry remain authoritative in the execution receipt for the apply action

## Verified Refresh Behavior

After `apply_bridge_scene_insertion` succeeds:

- `get_branch_artifact_index(...)` includes the apply report.
- `get_branch_diff_summary(...)` includes:
  - bridge apply report
  - changed branch outline
  - shifted scene artifact path, such as `draft/chapters/ch_001/scene_003.md`
- `get_book_reader_scene(..., scene_id=<inserted>)` includes the inserted scene from branch-local outline.
- The inserted scene is visible as `status=missing` and `artifact_status=diagnostic` until prose is written.
- `get_branch_detail(..., scene_id=<inserted>)` returns scene readiness with `recommended_next_action=plan_scene`.
- Branch detail legal actions expose the primitive next action (`plan_scene`); Nanda should use author-loop envelope/writing-gate surfaces for the macro `continue_scene`.

## Validation

Added regression coverage:

- `test_apply_bridge_scene_insertion_refresh_surfaces_include_inserted_scene_and_report`

Focused command:

```powershell
python -m pytest tests/test_adaptive_authoring_actions.py::test_apply_bridge_scene_insertion_refresh_surfaces_include_inserted_scene_and_report -q
```

Result:

```text
1 passed
```

## Nanda Consumption Note

After the apply job completes, Nanda should refresh these surfaces in this order:

1. branch detail for the inserted scene
2. branch artifact index
3. branch diff summary
4. branch reader scene for the inserted scene
5. author loop envelopes or writing gates

Do not derive scene-id movement in React. Use the returned apply receipt's `inserted_scene_id`, then re-query BookForge.
