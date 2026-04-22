# BookForge Help

This folder contains per-command help with exact usage and examples.

Runtime family vocabulary
- `deep_outline`: full batch outline generation under `bookforge outline generate`
- `section_local_outline`: section-scoped freeze/materialization under `bookforge workflow ...`
- `section_write`: lower-level prose loop under `bookforge run`
- `resume_paused_section`: truthful main-branch same-lineage resume adapter under `bookforge workflow resume-paused-section`
- `thin_outline`: reserved vocabulary, not a public command yet
- `recovery_import`: explicit recovery/import lineage, not a same-family resume

Result truth
- Supervised execution results classify outcomes as one of:
  - `success`
  - `no_op`
  - `retryable_pause`
  - `hard_fail`
  - `integrity_degraded`
  - `promotion_required`
- Main-branch execution results now carry reconciliation details so callers can see:
  - `pre_reconciliation_status`
  - `state_change_status`
  - `canonical_change_status`
  - `integrity_change`
  - `pre_revision_id`
  - `post_revision_id`
- Programmatic execution discovery now has a first-class seam:
  - Python:
    - `bookforge.execution.build_create_assembly_branch_request(...)`
    - `bookforge.execution.create_assembly_branch_action(...)`
    - `bookforge.execution.build_create_branch_request(...)`
    - `bookforge.execution.create_branch_action(...)`
    - `bookforge.execution.build_discard_branch_request(...)`
    - `bookforge.execution.discard_branch_action(...)`
    - `bookforge.query.list_execution_options(...)`
    - `bookforge.query.legal_next_actions(...)`
    - `bookforge.execution.build_finalize_chapter_request(...)`
    - `bookforge.execution.finalize_chapter(...)`
    - `bookforge.execution.build_initialize_workflow_request(...)`
    - `bookforge.execution.initialize_workflow(...)`
    - `bookforge.execution.build_lock_section_request(...)`
    - `bookforge.execution.lock_section(...)`
    - `bookforge.execution.build_promote_branch_request(...)`
    - `bookforge.execution.promote_branch_action(...)`
    - `bookforge.execution.build_record_assembly_validation_request(...)`
    - `bookforge.execution.record_assembly_validation_action(...)`
    - `bookforge.execution.build_resume_paused_section_request(...)`
    - `bookforge.execution.resume_paused_section(...)`
    - `bookforge.execution.build_write_section_request(...)`
    - `bookforge.execution.write_frozen_section(...)`
  - CLI:
    - `bookforge workflow legal-actions`
    - `bookforge workflow legal-actions --branch-id <id>`
    - `bookforge workflow legal-actions --fork-group-id <id>`

Lineage rule
- Immutable run artifacts under `outline/pipeline_runs/<run_id>/...` are the preferred lineage anchors.
- Mutable compatibility views such as `outline/outline.json` are useful, but they are not enough by themselves when immutable run artifacts exist.

Stub commands
- The following commands exist in CLI but are not implemented yet: compile, export synopsis, book set-current, book show-current, book clear-current.

Commands
- init: docs/help/init.md
- author generate: docs/help/author_generate.md
- workflow: docs/help/workflow.md
- outline generate: docs/help/outline_generate.md
- outline backup: docs/help/outline_backup.md
- outline restore: docs/help/outline_restore.md
- characters generate: docs/help/characters_generate.md
- run: docs/help/run.md
- llm utilities: docs/help/llm.md
- compile (stub): docs/help/compile.md
- export synopsis (stub): docs/help/export_synopsis.md
- book set-current (stub): docs/help/book_set_current.md
- book show-current (stub): docs/help/book_show_current.md
- book clear-current (stub): docs/help/book_clear_current.md
- book reset: docs/help/book_reset.md
- book update-templates: docs/help/book_update_templates.md
