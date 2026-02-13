# Prompt Template Composition Plan (20260213_183000)

## Purpose
Reduce high-risk prompt duplication across phase templates without introducing runtime brittleness, unclear precedence, or a metadata-heavy maintenance burden.

## Key Decision (Architecture)
- We are **not** introducing realtime dynamic prompt construction at run time.
- We are introducing a **build-time prompt composition step** that produces flat phase templates.
- Runtime behavior remains unchanged: runner/phases still read a single flat template file per phase.
- Composition should run as part of `book update-templates` (and optionally as a standalone dev command).

This keeps runtime deterministic and debuggable while reducing duplication in source prompt assets.

## Priority Escalation (High Priority)
- Naming and semantic clarity for fragments/manifests is now a **high-priority gate**.
- Implementation should not proceed beyond planning/spec work until naming conventions are approved.
- File paths and names must make fragment intent obvious without opening the file.
- Numeric-only segment names (for example, `seg_01.md`) are allowed only as temporary forensic artifacts, not final composition source names.

## Source Boundary Rule
- `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/` is a review artifact package.
- Production composition sources must live in canonical paths only:
  - `resources/prompt_blocks/**`
  - `resources/prompt_composition/**`
- Promotion from review artifact to production source must be explicit and review-gated.

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
  - Validation/linting for composition correctness and no unknown placeholders.
  - Explicit review-to-production promotion protocol for composition sources.
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
- Guarded vs soft block policy is required:
  - Guarded blocks: schema/contract-critical; may appear at most once unless explicitly exempted.
  - Soft blocks: phase-local policy prose; may vary by phase.
- Dedupe must be manifest-driven only:
  - Dedupe-eligible spans/blocks must be explicitly declared.
  - No global line-level dedupe over full templates.
- Placeholder validation must be allowlist-based:
  - Fail fast on unknown `{{...}}` placeholders after composition.
  - Allow known runtime renderer tokens by explicit allowlist.
- Block-level comments allowed in source, stripped or normalized in output.
- No circular includes (spec must be acyclic).
- Semantic naming policy is mandatory:
  - Use domain/phase/intent naming (for example, `phase/write/state_patch_rules.md`).
  - Shared blocks must be namespaced by domain (for example, `shared/state_patch/...`).
  - Avoid opaque numeric IDs as primary file names.
- Manifest metadata is mandatory for each fragment reference:
  - `semantic_id`
  - `owner_phase`
  - `applies_to`
  - `risk_class`
  - `source_prompt_span`
- Reverse traceability is required from compiled output back to source fragment path and span.
- Output encoding and line-ending policy is mandatory:
  - UTF-8 policy must be explicit (BOM preserved or stripped consistently).
  - Line endings normalized deterministically per policy.
- Optional audit output:
  - Generate `compiled_debug/*` with provenance markers for reviewers.
  - Runtime uses only clean compiled templates (no provenance markers).

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
### Story 0: Naming and Semantic Governance (High Priority Gate)
- Define and approve naming taxonomy for shared and phase blocks.
- Rename ambiguous draft block names to semantic names.
- Add/validate manifest metadata required for semantic ownership and traceability.
- Add a naming-lint rule that rejects opaque source fragment names in composition sources.

Acceptance:
- Every composition source path is self-descriptive by domain + intent.
- No final composition source files use opaque `seg_*`/`B00*` naming as primary identifiers.
- Every manifest entry includes semantic ownership metadata and source-span traceability.

### Story 1: Composition Spec and Block Inventory
- Inventory repeated sections and classify by:
  - Cross-phase shared, phase-specific, system-only, JSON-schema-contract blocks.
- Define first-pass block IDs and required order constraints.
- Classify each block as guarded or soft in manifest metadata.
- Produce composition manifests for:
  - `preflight.md`, `write.md`, `repair.md`, `state_repair.md`, `lint.md`.

Acceptance:
- Every phase template can be generated from manifest + blocks.
- Guarded/soft classifications are complete and reviewable.
- No missing critical rules in generated output.

### Story 2: Build-Time Composer Implementation
- Implement composer module.
- Enforce:
  - Acyclic graph.
  - Guarded block uniqueness constraints.
  - Dedupe only on explicit dedupe-eligible spans.
  - Placeholder allowlist validation (unknown-token failure).
  - BOM and line-ending policy normalization.
- Emit deterministic output with stable encoding/line endings.
- Emit optional `compiled_debug/*` provenance output for audits.

Acceptance:
- Running composer twice yields byte-identical output.
- Unknown placeholders fail with actionable errors.
- Guarded block policy violations fail with actionable errors.
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
  - Guarded block uniqueness.
  - No unknown placeholder tags.
  - Generated templates preserve required marker blocks.
  - Source checksum/index integrity against source-of-truth manifest.
- Add a lightweight doc note: templates are generated artifacts.
- Add policy: checksum changes require explicit semantic-change annotation.

Acceptance:
- CI/local tests fail on drift or composition regressions.
- Source-of-truth checksum drift cannot be accepted silently.

### Story 5: Behavioral Regression Gate for Dedupe Changes
- Run representative scenes through:
  - preflight -> write -> state_repair -> lint -> repair
- Run before/after comparison (legacy templates vs composed templates).
- Compare these metrics:
  - parse/schema pass rate
  - tripwire failure rate
  - must_stay_true mismatch incidence
  - repair convergence count

Acceptance:
- No material regression in schema/parse/tripwire behavior.
- No increase in repair churn attributable to composition changes.

## Go/No-Go Gates (Pass 1)
- Composer determinism: repeated runs are byte-identical.
- Compiled set integrity: compiled outputs match approved source-of-truth checksums.
- Guarded block enforcement: no duplicate guarded blocks in compiled templates.
- Placeholder enforcement: no unknown placeholders survive composition.
- Behavioral regression: representative pipeline runs show no material regression.

## Risk Register
- Risk: Ambiguous fragment names cause semantic drift, collisions, and reviewer/operator confusion.
  - Mitigation: enforce semantic naming taxonomy and naming-lint gate before implementation.
- Risk: Placeholder validation false-positive blocks valid runtime placeholders.
  - Mitigation: explicit allowlist for renderer-supported placeholders; fail only on unknown tokens.
- Risk: Dedupe changes alter model behavior by removing repeated weighting.
  - Mitigation: run Story 5 behavior regression gate before rollout.
- Risk: Naive global dedupe removes valid repeated JSON/example structures.
  - Mitigation: dedupe only on explicitly declared dedupe-eligible spans/blocks.
- Risk: BOM/line-ending instability causes flaky determinism and checksum drift.
  - Mitigation: enforce explicit encoding and newline normalization policy in composer.
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
- Naming/semantic governance gate is satisfied (taxonomy approved and lint-enforced).
- Guarded/soft policy is enforced in manifests and composer checks.
- Placeholder allowlist/unknown-token enforcement is in place.
- Duplicate-heavy blocks are centralized once in source blocks.
- Generated flat templates retain all required rules and pass existing pipeline validation.
- Behavior regression gate passes on representative end-to-end runs.
- No regression in current run behavior attributable to prompt loading mechanics.

## Status Tracker
- Story 0 (High Priority Naming Gate): `pending`
- Story 1: `pending`
- Story 2: `pending`
- Story 3: `pending`
- Story 4: `pending`
- Story 5: `pending`
