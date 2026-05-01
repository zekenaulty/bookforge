# Slice Note: Branch Writing Target Advancement

Date: 2026-04-29

Repo: BookForge / `ai-book`

Owner: BookForge engine workstream

## Slice

Close a branch-local author-loop gap discovered while cross-checking Nanda's `AuthorWorkLoop` needs.

`get_next_writing_target(...)` already reported scene continuation and writing gates, but it only advanced from a committed scene to the next scene when `branch_id == "main"`.

That was wrong for branch-live authoring. A derived branch with scene 1 committed and scene 2 unwritten should recommend continuing scene 2, not stall at scene 1.

## Change

`bookforge.query.get_next_writing_target(...)` now applies committed-scene progression on derived branches as well as `main`:

- if the selected committed scene is not the last scene in the section, the next target is the next scene
- the recommended action remains `continue_scene`
- the selector preserves the selected branch id
- if the selected committed scene is terminal for the section, the next gate remains `lock_section_from_written_state`

## Why This Matters To Nanda

Nanda's parent `AuthorWorkLoop` is supposed to:

1. run one `continue_scene`
2. refresh branch detail/readiness/legal actions/writing target
3. decide whether another step is legal

Without branch-local target advancement, a loop could preserve the branch correctly but still stop too early after committing a scene.

## Validation

Added regression coverage:

- `test_next_writing_target_advances_to_next_scene_on_branch_after_commit`

Focused command:

```powershell
python -m pytest tests/test_writing_target.py -q
```

Result:

```text
9 passed
```

## Nanda Consumption Note

After a branch-local `continue_scene` commits a scene, Nanda should re-query:

- branch detail
- `get_next_writing_target`
- writing gates
- scene readiness for the returned target selector

If the target selector moves from scene `N` to scene `N+1`, Nanda should show that as fresh BookForge truth rather than deriving cursor movement in the UI.
