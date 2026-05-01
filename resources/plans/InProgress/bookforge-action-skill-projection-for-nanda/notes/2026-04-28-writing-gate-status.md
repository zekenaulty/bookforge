# 2026-04-28 Writing Gate Status

BookForge now exposes the first writing gate readiness surface for Nanda.

Surface:

- Python: `bookforge.query.get_writing_gate_status(...)`
- CLI: `bookforge workflow writing-gates`
- Capability projection: `readiness.writing_gate_status`
- Contracts: `WritingGateStatus`, `WritingGate`

Behavior:

- Read-only. It does not mutate `main`, branches, prose, outline, state, or
  phase artifacts.
- Branch-aware. Derived branches read branch snapshots, but main-only gates are
  reported as blocked when branch semantics are not yet audited.
- Emits gate rows for:
  - `scene_continue`
  - `section_lock`
  - `chapter_finalize`
  - `book_continue`
  - `manuscript_export`
- Each gate row reports:
  - status
  - ready flag
  - scope
  - action, when a real BookForge action exists
  - blocked reason
  - details
- `book_continue` is the broad loop gate. It can point at `continue_scene`,
  `freeze_section_from_phase03_artifact`, `lock_section_from_written_state`, or
  `finalize_chapter_from_locked_sections` depending on the current state.
- `manuscript_export` is intentionally blocked because compile/export quality
  gates remain a designed gap.

Nanda use:

- `AuthorWorkLoop` can use this surface to explain why it stopped.
- The Branch Workbench can render gate cards instead of inferring state from
  cursor position or filesystem artifacts.
- Book completion now has a BookForge-owned gate surface.

Validation:

- Focused tests cover:
  - scene continue gate ready
  - section lock gate ready
  - book complete with export still blocked as a designed gap
  - CLI parser coverage
- Capability fixture was regenerated and projection tests now require
  `readiness.writing_gate_status`.
