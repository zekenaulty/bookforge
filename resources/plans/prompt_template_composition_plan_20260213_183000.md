# Prompt Template Composition Plan (20260213_183000) - Refined Execution Control Version

## Purpose
Reduce high-risk prompt duplication across phase templates without introducing runtime brittleness, unclear precedence, metadata sprawl, or silent behavior drift.

## Non-Negotiable Outcomes
- Build-time prompt composition only. Runtime prompt loading remains flat-file and unchanged.
- Pass 1 policy: semantic no-op composition migration, except explicitly approved dedupe operations.
- Every material change must be traceable from source fragment -> manifest entry -> compiled output -> runtime consumer.
- Every material change must have a logged review decision and risk assessment before implementation.

## Priority Escalation (High Priority)
- Naming and semantic clarity for fragments/manifests is a high-priority gate.
- Ambiguous naming is treated as release-blocking risk, not cleanup debt.
- Numeric-only segment names (for example, `seg_01.md`) are allowed only in forensic review artifacts, not final composition source.

## Source Boundary Rule
- `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/` is a review artifact package.
- Production composition sources must live only in:
  - `resources/prompt_blocks/**`
  - `resources/prompt_composition/**`
- Promotion from review artifacts into production source paths must be explicit, logged, and review-approved.

## Primary References (Authoritative)
- Main forensic index:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/index.md`
- Prompt risk and delta inventory:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/change_matrix.md`
- Code touchpoint map:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/prompt_code_touchpoints.json`
- Prompt snapshots and checksums:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshot_manifest.json`
- Duplicate-line forensic report:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/duplicate_lines_report.json`
- Proposed compilation source of truth:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/SOURCE_OF_TRUTH.md`
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/compiled_manifest_index.json`
- Per-prompt forensic change plans:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/artifacts/*.forensic_plan.md`
- Stability and reuse reports:
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/reports/stability_controls.md`
  - `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/reports/reuse_index.md`

## Architectural Decision (Locked)
- No realtime dynamic prompt construction at runtime.
- Build-time composition generates flat templates in `resources/prompt_templates/*.md`.
- Existing runtime readers stay unchanged:
  - `src/bookforge/pipeline/prompts.py:40-44`
  - `src/bookforge/workspace.py:203-213`

## Scope
- In scope:
  - Shared prompt blocks and phase composition manifests.
  - Build-time composer implementation and validation.
  - `book update-templates` integration.
  - Determinism, placeholder validation, guarded-block validation, behavior-regression validation.
  - Review governance and mandatory logging.
- Out of scope:
  - Runtime includes/partials.
  - Dynamic per-request prompt assembly.
  - Priority/precedence model changes between system/phase prompts.

## Runtime Coupling Cross-Reference Matrix
| Surface | Runtime Consumer | Downstream Deterministic Coupling | Primary Risk If Drifted |
|---|---|---|---|
| `system_base.md` | `src/bookforge/workspace.py:302,346` | `src/bookforge/prompt/system.py:8-24` | Global behavior drift across all phases |
| `output_contract.md` | `src/bookforge/workspace.py:303,347` | All phase contract behavior | Global output-shape contract drift |
| `write.md` | `src/bookforge/phases/write_phase.py:35` | `src/bookforge/pipeline/parse.py:70-88`, `src/bookforge/phases/write_phase.py:73-125` | Parse failures, schema churn, drift in patch quality |
| `repair.md` | `src/bookforge/phases/repair_phase.py:35` | `src/bookforge/pipeline/parse.py:70-88`, `src/bookforge/phases/repair_phase.py:66-125` | Repair loop instability, malformed `STATE_PATCH` |
| `state_repair.md` | `src/bookforge/phases/state_repair_phase.py:37` | `src/bookforge/phases/state_repair_phase.py:67-115`, `src/bookforge/pipeline/state_patch.py:407` | Pre-lint patch drift, invalid canonicalization |
| `preflight.md` | `src/bookforge/phases/preflight_phase.py:32` | `src/bookforge/runner.py:604-639`, `src/bookforge/pipeline/state_patch.py:_sanitize_preflight_patch` | Hidden transition misapplication, custody drift |
| `lint.md` | `src/bookforge/phases/lint_phase.py:239` | `src/bookforge/phases/lint_phase.py:309-341`, `src/bookforge/pipeline/lint/tripwires.py:29-260` | False pass/fail, incoherence masking, retry churn |
| `plan.md` | `src/bookforge/phases/plan.py:65-68` | `src/bookforge/phases/plan.py:335-430` | Scene-card schema drift |
| `outline.md` | `src/bookforge/outline.py:367-370` | Outline schema generation/validation path | Outline contract drift |
| `continuity_pack.md` | `src/bookforge/phases/continuity_phase.py:31` | Continuity pack constraints consumed by write | Constraint misalignment |

## Known Risk Receipts (Current State)
- `write.md` duplicate must_stay_true end-truth line appears 11 times.
- `repair.md` must_stay_true reconciliation lines duplicated 10+ times.
- Shared rules duplicated across `preflight/write/repair/state_repair`.
- Multiple templates contain wrapped/concatenated lines in transfer/conflict regions that must not be normalized in pass 1.

## Composition Requirements (Enforced)
- Deterministic ordering and deterministic output bytes.
- Acyclic composition graph.
- Guarded vs soft block classification per manifest entry.
- Guarded block constraints:
  - At-most-once inclusion by default.
  - Any intentional repetition must be explicit and justified in manifest metadata.
- Dedupe constraints:
  - Dedupe is allowed only for explicit, pre-approved dedupe-eligible spans.
  - No global line-based dedupe over full templates.
- Placeholder constraints:
  - Unknown `{{...}}` tokens fail composition.
  - Known runtime tokens are allowlisted and retained.
- Encoding constraints:
  - UTF-8 and BOM policy explicit and consistent.
  - Line-ending normalization policy explicit and consistent.
- Traceability constraints:
  - Every compiled line range maps to fragment path and source span.

## Naming and Semantic Taxonomy (Gate)
- Naming format for phase fragments:
  - `phase/<phase_name>/<intent_slug>.md`
- Naming format for shared fragments:
  - `shared/<domain>/<intent_slug>.md`
- Required naming semantics:
  - The path + file name must identify phase/domain + functional purpose without opening the file.
- Prohibited in production sources:
  - Opaque numeric prefixes (`B001`, `seg_01`) as primary identity.
- Manifest must include:
  - `semantic_id`
  - `owner_phase`
  - `applies_to`
  - `risk_class`
  - `source_prompt_span`
  - `guard_level` (`guarded` or `soft`)
  - `dedupe_eligible` (`true` or `false`)

## Internal Review Model (Mandatory)
### Review Stages
1. Stage A - Design Review (before implementation)
- Validate taxonomy, manifests, guarded classifications, dedupe eligibility, placeholder allowlist, encoding policy.

2. Stage B - Implementation Review (during implementation)
- Validate composer behavior against manifest schema and policy gates.
- Validate traceability outputs and deterministic output behavior.

3. Stage C - Behavioral Review (before go/no-go)
- Validate before/after pipeline behavior on representative scenes.
- Validate no increase in parse/tripwire/repair churn.

### Review Evidence Requirements
- Every stage must produce log entries in review and decision logs.
- Every rejected item must include rejection reason and remediation path.
- Every accepted item must include scope, risk impact, and verification evidence reference.

## Tracking and Change Logging (Mandatory)
### Required Logs (must be maintained during work)
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/change_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/risk_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/decision_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/review_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/validation_log.md`

### Logging Cadence
- Update `change_log.md` for every material file modification.
- Update `risk_log.md` whenever a new risk is discovered or risk status changes.
- Update `decision_log.md` for every scope, policy, or implementation decision.
- Update `review_log.md` at the close of each review stage.
- Update `validation_log.md` after each deterministic/behavioral test run.

### Change Entry Minimum Fields
- timestamp
- author
- scope
- changed files
- reason for change
- expected behavior impact
- verification method
- result
- rollback note

## Story Breakdown (Execution Workstreams)
### Story 0 - Naming and Semantic Governance (High Priority Gate)
- Define final taxonomy and manifest schema extensions.
- Rename ambiguous fragment identifiers.
- Reject non-semantic naming in production sources.

Acceptance:
- All production-source fragment names are semantic and self-descriptive.
- Taxonomy approved and logged.

### Story 1 - Composition Spec and Inventory Hardening
- Build complete block inventory with guarded/soft classification.
- Mark dedupe-eligible spans explicitly.
- Map each block to runtime coupling risk class.

Acceptance:
- No unclassified block references.
- No dedupe operation without explicit eligibility flag.

### Story 2 - Composer Implementation and Policy Enforcement
- Implement composer and policy checks.
- Enforce placeholder allowlist and unknown-token failure.
- Enforce guarded uniqueness and encoding/line-ending policy.
- Produce optional provenance debug output (`compiled_debug/*`).

Acceptance:
- Deterministic output on repeated runs.
- Clear actionable failures for policy violations.

### Story 3 - Workflow Integration
- Integrate compose-before-copy into `book update-templates`.
- Keep runtime loading unchanged.

Acceptance:
- Existing runtime prompt resolution behavior unchanged.
- Templates distributed from composed outputs only.

### Story 4 - Determinism and Integrity Validation
- Add tests and checks for:
  - deterministic bytes
  - guarded-block uniqueness
  - unknown placeholder failure
  - source-of-truth checksum integrity

Acceptance:
- CI/local checks fail on drift or policy violations.

### Story 5 - Behavioral Regression Gate for Dedupe and Composition
- Run representative scenes through:
  - preflight -> write -> state_repair -> lint -> repair
- Compare baseline vs composed-template metrics:
  - parse/schema pass rate
  - tripwire failure rate
  - must_stay_true mismatch rate
  - repair convergence count

Acceptance:
- No material regressions attributable to composition changes.

## Go/No-Go Gates (Pass 1)
- G1: Naming gate passed.
- G2: Manifest policy gate passed (guarded/soft, dedupe eligibility, placeholder allowlist).
- G3: Determinism gate passed (byte-identical repeated runs).
- G4: Integrity gate passed (compiled checksums match approved source-of-truth).
- G5: Behavioral gate passed (no material regression).
- G6: Logging gate passed (all required logs current and complete).

## Risk Register (Refined)
| Risk ID | Risk | Trigger | Detection | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-001 | Ambiguous fragment naming causes semantic drift | Non-semantic file names | Naming lint + review | Taxonomy gate (Story 0) | Prompt composition owner | Open |
| R-002 | Unknown placeholder tokens ship into templates | New token not in allowlist | Composer validation | Allowlist enforcement + failure on unknown | Composer owner | Open |
| R-003 | Dedupe alters model behavior | Repetition removed in policy-critical lines | Baseline vs composed run metrics | Behavioral regression gate (Story 5) | Validation owner | Open |
| R-004 | Global dedupe corrupts valid JSON examples | Broad line-level dedupe | Change review + tests | Manifest-only dedupe | Composer owner | Open |
| R-005 | Encoding/line-ending drift breaks determinism | Platform/editor variance | Determinism tests + checksum mismatch | Explicit UTF-8/BOM/newline policy | Composer owner | Open |
| R-006 | Shared block change impacts unrelated phases | Shared block edit | Cross-phase diff + review | Guarded block impact review + targeted tests | Review owner | Open |
| R-007 | Review artifact and production source diverge | Direct edits in wrong tree | Path policy review | Source boundary rule + promotion logging | Composition owner | Open |

## Implementation-Time Internal Review Checklist
- Check 1: Does every modified fragment have semantic naming and manifest metadata?
- Check 2: Is every dedupe change explicitly marked dedupe-eligible?
- Check 3: Did compiled outputs change only where expected?
- Check 4: Are parser/schema-coupled examples unchanged unless explicitly approved?
- Check 5: Are runtime coupling surfaces cross-checked against touchpoint map?
- Check 6: Were change/risk/decision/review logs updated in the same work session?

## Definition of Done
- Build-time composition implemented and integrated into `book update-templates`.
- Runtime prompt loading remains single-file and unchanged.
- Naming and semantic governance gate passed.
- Guarded/soft, dedupe, placeholder, and encoding policies enforced by composer.
- Required logs are complete, current, and reviewed.
- Compiled outputs pass determinism + checksum integrity gates.
- Behavioral regression gate passes on representative end-to-end pipeline runs.
- No material regression attributable to prompt composition migration.

## Status Tracker
- Story 0 (High Priority Naming Gate): `pending`
- Story 1: `pending`
- Story 2: `pending`
- Story 3: `pending`
- Story 4: `pending`
- Story 5: `pending`

## Immediate Next Actions
1. Approve taxonomy and manifest metadata schema update (Story 0).
2. Create and start mandatory logs under `.../controls/`.
3. Freeze dedupe-eligible spans from forensic artifacts before any composer code changes.
4. Define baseline scene set for Story 5 behavioral gate.
