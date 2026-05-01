# 2026-04-27 Execution Note

## Summary
- Promoted `bookforge-action-skill-projection-for-nanda` from `Drafts` to `InProgress`.
- Added BookForge-owned capability projection contracts:
  - `CapabilityProjection`
  - `CapabilityDescriptor`
  - `CapabilityEvidenceSource`
  - `CapabilityRefusalSemantics`
- Added `bookforge.query.get_capability_projection(...)`.
- Added CLI surface:
  - `bookforge capabilities`
  - `bookforge capabilities --json`
  - `bookforge capabilities --book <id>`
- Added Nanda fixture:
  - `tests/fixtures/capability_projection_v1.json`
- Added docs:
  - `docs/help/capabilities.md`
  - `docs/help/index.md` capability entries
  - `docs/help/workflow.md` static-vs-dynamic pointer
- Closed the first Nanda fallback gaps by adding BookForge-owned read-only query surfaces:
  - book cards/library: `bookforge.query.list_book_cards(...)`
  - canonical reader views: `bookforge.query.get_book_reader_view(...)`
  - branch/fork inventory: `bookforge.query.get_branch_inventory(...)`
- Added operator CLI surfaces:
  - `bookforge book list`
  - `bookforge book reader`
  - `bookforge workflow branch-inventory`
- Added branch-live inspection surface for Nanda:
  - `bookforge.query.get_branch_detail(...)`
  - `bookforge.query.get_branch_artifact_index(...)`
  - `bookforge.query.get_branch_diff_summary(...)`
  - `bookforge.query.get_recovery_anchor_candidates(...)`
  - `bookforge.query.get_recovery_plan_preview(...)`
  - `bookforge workflow branch-detail`
  - `bookforge workflow branch-artifact-index`
  - `bookforge workflow branch-diff-summary`
  - `bookforge workflow recovery-anchor-candidates`
  - `bookforge workflow recovery-plan-preview`
  - bundles branch manifest/current node, main node, branch-local workspace status, legal actions, optional reader selection, optional scene readiness, and recovery health when applicable
  - indexes branch artifacts by class and main/branch relationship without reading prose content

## Capability Coverage
- Implemented action descriptors for all public `ExecutionOption.action` strings currently emitted by `src/bookforge/query/actions.py`.
- Implemented query descriptors for workspace, workflow, integrity, outline lineage, recovery, character, continuity, appearance, setting, scene context, and thought context surfaces.
- Implemented readiness descriptors for legal next actions, scene-phase readiness, recovery plan readiness, and recovery semantic review readiness.
- Added explicit designed-gap descriptors for Nanda-visible surfaces not yet executable in BookForge:
  - author create/refine/select asset API
  - book intent/synopsis surface
  - pairwise scene seam alignment
  - adaptive bridge-scene insertion
  - deep state/inventory projection layer
  - compile/export and reader quality gates
- Promoted prior designed gaps to implemented query descriptors:
  - canonical reader/manuscript surface
  - book library/card index
  - branch/fork inventory
  - branch workbench detail view
  - branch artifact index
  - branch diff summary
  - recovery anchor candidate report
  - recovery plan preview

## Guardrails Preserved
- Capability projection is static engine truth.
- Dynamic readiness remains separate and must be queried by scope through legal-action/readiness surfaces.
- Macro workflows expose child actions but do not force rails.
- Designed gaps are visible but non-executable.
- The projection does not expose helper functions as capabilities.

## Validation
- `python -m pytest tests\test_capability_projection.py`
  - 6 passed.
- `python -m pytest tests\test_reader_books_branches_query.py tests\test_capability_projection.py`
  - 9 passed.
- `python -m pytest`
  - 319 passed.
- CLI smoke:
  - `.\.venv\Scripts\bookforge.exe --workspace workspace capabilities --json`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace capabilities --book veiled_ledger_b1`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace book list`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace book reader --book veiled_ledger_b1 --chapter 3 --scene 1 --max-text-chars 200`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace workflow branch-inventory --book veiled_ledger_b1`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace workflow branch-detail --book veiled_ledger_b1 --branch-id main --chapter 3 --scene 1 --max-text-chars 120`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace workflow branch-artifact-index --book veiled_ledger_b1 --branch-id main --limit 20`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace workflow branch-diff-summary --book veiled_ledger_b1 --branch-id main`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace workflow recovery-anchor-candidates --book veiled_ledger_b1 --json`
  - `.\.venv\Scripts\bookforge.exe --workspace workspace workflow recovery-plan-preview --book veiled_ledger_b1 --json`

## Current Counts
- Static projection with no book context:
  - 73 capabilities total
  - 68 implemented
  - 5 designed gaps
- Book-scoped projection for `veiled_ledger_b1`:
  - source: `static_registry+execution_options`
  - 73 capabilities total
  - 68 implemented
  - 5 designed gaps

## Veiled Ledger Recovery Planning Observation
- `recovery-anchor-candidates` on `veiled_ledger_b1` reports:
  - status: `auto_selected`
  - recommended candidate: `declared_source_run`
  - auto-selected candidate: `declared_source_run`
  - affected scopes: 9 sections across chapters 1-3
- `recovery-plan-preview` on `veiled_ledger_b1` selects:
  - anchor type: `declared_source_run`
  - source run: `20260419_050005`
  - 10-step recovery plan through branch creation, quarantine, normalization, invalidation, state rebuild, redraft, review, validation, and promotion
- Follow-up QA clarified that `create_recovery_branch` is isolation, not decontamination:
  - branch creation snapshots current branch state and copies recovery evidence
  - `outline/section_drafts` may still exist in the branch immediately after creation
  - the branch reports `cleanliness_status=isolated_not_clean`
  - cleanup begins with `quarantine_artifacts` and `normalize_outline_scope`
  - Nanda should not describe the branch as clean until recovery receipts and validation prove it

## Author UI Support And Rich Profile Surface
- Added `bookforge.query.authors` with:
  - `list_author_profiles(...)`
  - `get_author_profile(...)`
- Author profile payloads expose:
  - versioned author refs and selected versions
  - authoritative artifact status and source paths
  - voice, themes, sensory bias, pacing, style rules, cadence rules, taboos, banned phrases, and influences
  - full style Markdown, system fragment, and derived `profile_markdown`
- Added CLI support:
  - `bookforge author list`
  - `bookforge author profile <author_ref>`
- Added capability descriptors:
  - `query.author_profiles`
  - `query.author_profile`
- Updated Nanda integration:
  - `/api/authors` now prefers BookForge author query surfaces
  - `/api/authors/profile?author_ref=...` returns a specific author version
  - Author detail can select an associated book, derive book scope, and render the exact author version pinned by the selected book
- Validation:
  - BookForge focused tests: 12 passed
  - Nanda tests: passed
  - Nanda UI build: passed

## Next Successor Candidates
- `bookforge-manuscript-output-and-reader-quality-gates`
- `bookforge-author-assets-api` for preview/select/rollback/book-assignment actions; author list/read/profile and create/refine actions are now implemented
- `bookforge-book-intent-and-synopsis-surface`
- `bookforge-lint-repair-routing`
- `bookforge-outline-contract-hardening`
