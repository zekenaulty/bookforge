# 2026-04-28 Branch-Local Section Lock

BookForge added branch-local `lock_section_from_written_state` support.

Why:

- `AuthorWorkLoop` can now move beyond one scene on a branch without requiring a
  canonical main mutation.
- A branch-local section that has all required scene prose/meta files can be
  locked inside the branch snapshot.
- Nanda can present section locking as a safe branch-local finalize step when a
  derived branch is selected.

Behavior:

- `lock_section_from_written_state` now accepts `branch_id`.
- On `main`, behavior remains canonical.
- On a derived branch:
  - the branch snapshot `outline/outline.json` and
    `outline/snapshot_registry.json` are updated
  - canonical `main` outline/registry remain unchanged
  - the branch current node advances
  - the branch manifest moves to `promote_ready`
  - receipts include `branch_change_status` and `canonical_changed: false`
  - receipts still omit `canonical_change_status`
- If all chapter sections are locked in the branch, chapter finalization runs in
  the branch snapshot, not on `main`.

Capability/readiness changes:

- `lock_section_from_written_state` projection changed from `main_only` to
  branch-capable.
- Legal-action discovery reports branch-local lock with
  `mutation_scope=branch_authoritative`.
- Writing gates now allow `section_lock` on derived branches when the branch
  section is frozen and all required scene artifacts exist.

Validation:

- Focused tests prove branch-local lock:
  - writes only the branch snapshot
  - leaves canonical main section status frozen
  - marks branch section status locked
  - emits `canonical_changed: false`
  - omits `canonical_change_status`
  - marks the branch promote-ready
- Legal-action tests cover branch-local lock discovery.
- CLI parser accepts `bookforge workflow lock-section --branch-id <id>`.
