# 2026-04-28 Next Writing Target Query

BookForge now exposes the first loop-friendly writing cursor query for Nanda.

Surface:

- Python: `bookforge.query.get_next_writing_target(...)`
- CLI: `bookforge workflow next-writing-target`
- Capability projection: `query.next_writing_target`
- Contract: `NextWritingTarget`

Behavior:

- Read-only. It does not mutate `main`, branch snapshots, prose, outline, state,
  or phase artifacts.
- Branch-aware. A derived branch reads the branch snapshot/root and reports the
  branch id in the returned contract.
- Reports:
  - `status`: `ready`, `blocked`, or `complete`
  - `book_complete`
  - `can_continue`
  - current scene
  - next scene
  - next section
  - next chapter
  - recommended action
  - blocked reason
  - node and branch context
- Uses `ScenePhaseReadiness` for the current scene when a scene target resolves.
- Returns `continue_scene` as the recommended action only when a one-step
  scene-phase action is actually ready.
- Stops at section/chapter/book gates instead of pretending scene writing can
  continue.

Nanda use:

- `AuthorWorkLoop` can call this before scheduling another `continue_scene`.
- The UI can explain whether the loop stopped because of a section lock gate,
  missing frozen section, book completion, stale branch, or no ready scene-phase
  action.
- This is a gate/cursor query, not a mutation command.

Validation:

- Focused tests cover:
  - ready current scene target
  - initialized but unfrozen section gate
  - committed terminal scene stopping at section lock gate
  - CLI parser coverage
- Capability fixture was regenerated and projection tests now require
  `query.next_writing_target`.
