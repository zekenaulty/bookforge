# 2026-04-26 0071 Branch-Scoped Writer

## Summary
- Completed the first branch-scoped writer slice.
- Scene-phase readiness and execution can now resolve against a derived branch execution root instead of only canonical `main`.
- Section-range writing can run through a branch-local root and pass branch identity into the section traversal.
- Historical scene rewrites are branch-local: copied committed scene files are treated as replaceable branch baselines, and `apply_scene_commit` preserves `.original` backups before replacing them in the branch snapshot.
- `main` remains protected from accidental committed-scene overwrite.

## Code Notes
- Query surfaces now expose branch-local workspace status, current node, section status, and scene readiness.
- Scene-phase request builders and actions accept `branch_id`.
- Branch snapshots now copy writer-facing surfaces such as `draft`, `prompts`, and context folders.
- CLI workflow scene-phase commands and `write-section` now accept `--branch-id`.

## Tests
- Focused branch execution: `15 passed`.
- Broader non-outline regression set: `94 passed` before CLI/docs updates and `87 passed` for the focused scene/action/scoped set after CLI branch-id wiring.

## Open Follow-Up
- Outline tests are still tracked as a separate repair TODO because the current dirty tree includes unrelated outline edits from another agent.
- 0072 remains in progress for fork-group writer assembly.
