# Prompt Template Composition Plan (20260213_183000)

## Purpose
Reduce high-risk prompt duplication across phase templates without introducing runtime brittleness, unclear precedence, or a metadata-heavy maintenance burden.

## Key Decision (Architecture)
- We are **not** introducing realtime dynamic prompt construction at run time.
- We are introducing a **build-time prompt composition step** that produces flat phase templates.
- Runtime behavior remains unchanged: runner/phases still read a single flat template file per phase.
- Composition should run as part of `book update-templates` (and optionally as a standalone dev command).

This keeps runtime deterministic and debuggable while reducing duplication in source prompt assets.

## Why This Approach
- Current renderer is simple token replacement and has no include/partial semantics (`src/bookforge/prompt/renderer.py`).
- Runtime template resolution is intentionally simple (book override file, else global) (`src/bookforge/pipeline/prompts.py`).
- Adding include logic to runtime prompt loading would increase blast radius and make failures harder to localize.

## Current Risk Receipts
- Severe duplication exists in live templates:
  - `resources/prompt_templates/write.md`: repeated durable/must_stay_true lines (11 duplicates of one line).
  - `resources/prompt_templates/repair.md`: repeated must_stay_true reconciliation blocks (10+ repeats).
  - Shared scope/rules duplicated across `preflight/write/repair/state_repair`.
- Duplication causes drift risk and conflicting edits across phases.

## Scope
- In scope:
  - Source-of-truth shared prompt blocks.
  - Composition pipeline that emits phase-flat templates.
  - Template update workflow integration.
  - Validation/linting for composition correctness and no unresolved placeholders.
- Out of scope:
  - Runtime include/partial loading.
  - Dynamic per-request prompt assembly.
  - Author/system prompt priority changes.

## Design
### Layer Model
- Layer A: Shared block source files (new folder, e.g. `resources/prompt_blocks/`).
- Layer B: Phase composition specs (declarative ordering per phase).
- Layer C: Generated flat templates (written to `resources/prompt_templates/*.md` and then copied to books).

### Composition Requirements
- Deterministic ordering.
- Strict duplicate policy for guarded blocks (especially JSON contract and must_stay_true rules).
- Block-level comments allowed in source, stripped or normalized in output.
- No circular includes (spec must be acyclic).
- Fail fast if unresolved placeholders remain after composition.

### Example Flow
1. Edit shared block(s) and phase spec(s).
2. Run composer (`book update-templates` internally invokes compose first).
3. Composer writes flat templates to `resources/prompt_templates`.
4. Existing template copy behavior proceeds unchanged.
5. Existing system prompt regeneration proceeds unchanged.

## Touchpoints
### New/Updated Code
- `src/bookforge/workspace.py`
  - Update `update_book_templates()` and init path to compose before copy.
- New module (proposed): `src/bookforge/pipeline/prompt_compose.py`
  - Parse phase composition specs.
  - Compose blocks.
  - Validate output.
- Optional CLI hook:
  - `book prompts compose` (dev-focused helper), while `book update-templates` remains primary path.

### New Assets
- `resources/prompt_blocks/` (shared source blocks).
- `resources/prompt_composition/` (phase composition manifests/specs).

### Existing Assets Affected
- `resources/prompt_templates/*.md` become generated artifacts from composition sources.

## Story Breakdown
### Story 1: Composition Spec and Block Inventory
- Inventory repeated sections and classify by:
  - Cross-phase shared, phase-specific, system-only, JSON-schema-contract blocks.
- Define first-pass block IDs and required order constraints.
- Produce composition manifests for:
  - `preflight.md`, `write.md`, `repair.md`, `state_repair.md`, `lint.md`.

Acceptance:
- Every phase template can be generated from manifest + blocks.
- No missing critical rules in generated output.

### Story 2: Build-Time Composer Implementation
- Implement composer module.
- Enforce:
  - Acyclic graph.
  - Duplicate guardrails.
  - Placeholder sanity checks.
- Emit deterministic output with stable line endings.

Acceptance:
- Running composer twice yields byte-identical output.
- Composer fails with actionable error messages on malformed specs.

### Story 3: Workflow Integration
- Integrate composer into `update_book_templates` path before copy.
- Ensure init workspace also composes from latest sources.
- Add optional standalone compose command for quick iteration.

Acceptance:
- `book update-templates` always distributes freshly composed templates.
- Existing books still get flat templates only.

### Story 4: Validation and Regression Safety
- Add tests:
  - Composition determinism.
  - No duplicate forbidden blocks.
  - No unresolved placeholder tags.
  - Generated templates preserve required marker blocks.
- Add a lightweight doc note: templates are generated artifacts.

Acceptance:
- CI/local tests fail on drift or composition regressions.

## Risk Register
- Risk: Composition manifests become new maintenance burden.
  - Mitigation: keep manifests small and phase-local; avoid nested composition chains.
- Risk: Shared block change accidentally impacts unrelated phases.
  - Mitigation: block tagging + per-phase golden text tests.
- Risk: Team edits generated templates directly and loses changes.
  - Mitigation: header notice in generated templates + compose-before-copy workflow.
- Risk: Book overrides diverge silently.
  - Mitigation: keep output flat and maintain current book override model.

## Edge Cases
- Book-local custom templates that intentionally diverge from global defaults.
- Partial migration period where some phases are composed and others are legacy.
- Prompt contract changes that require schema changes in code.
- Large JSON contract blocks requiring strict verbatim duplication across multiple phases.

## Definition of Done
- Build-time composition exists and is integrated into `book update-templates`.
- Runtime prompt loading remains single-file and unchanged.
- Duplicate-heavy blocks are centralized once in source blocks.
- Generated flat templates retain all required rules and pass existing pipeline validation.
- No regression in current run behavior attributable to prompt loading mechanics.

## Status Tracker
- Story 1: `pending`
- Story 2: `pending`
- Story 3: `pending`
- Story 4: `pending`
