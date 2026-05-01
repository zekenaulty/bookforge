# 2026-04-28 Branch-Local Chapter Finalize

BookForge added branch-local `finalize_chapter_from_locked_sections` support.

Why:

- Branch-local author loops need a consistent scene -> section -> chapter path.
- Nanda should not have to switch to canonical `main` just to run chapter seam
  repair/finalization for a branch candidate.

Behavior:

- `finalize_chapter_from_locked_sections` now accepts `branch_id`.
- On `main`, behavior remains canonical.
- On a derived branch:
  - finalization reads locked chapter state from the branch snapshot
  - chapter seam/finalization artifacts are written in the branch snapshot
  - canonical `main` remains unchanged
  - the branch current node advances
  - the branch manifest moves to `promote_ready`
  - receipts include `branch_change_status` and `canonical_changed: false`
  - receipts still omit `canonical_change_status`

Capability/readiness changes:

- `finalize_chapter_from_locked_sections` projection changed from `main_only`
  to branch-capable.
- Legal-action discovery reports branch-local finalization with
  `mutation_scope=branch_authoritative`.
- Writing gates now allow `chapter_finalize` on derived branches when the branch
  chapter has all sections locked.

Validation:

- Focused tests prove branch-local finalize:
  - writes only the branch snapshot
  - leaves canonical main chapter status unchanged
  - marks branch chapter status finalized
  - emits `canonical_changed: false`
  - omits `canonical_change_status`
- Legal-action tests cover branch-local finalization discovery.
- CLI parser accepts `bookforge workflow finalize-chapter --branch-id <id>`.
