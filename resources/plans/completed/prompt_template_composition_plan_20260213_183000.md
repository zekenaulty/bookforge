# Prompt Template Composition Plan (20260213_183000) - Refined Execution Control Version v2

## Purpose
Reduce high-risk prompt duplication across phase templates without introducing runtime brittleness, unclear precedence, metadata sprawl, or silent behavior drift.

## Non-Negotiable Outcomes
- Build-time prompt composition only. Runtime prompt loading remains flat-file and unchanged.
- Pass 1 policy: semantic no-op composition migration, except explicitly approved dedupe spans.
- Every material change must be traceable from source fragment -> manifest entry -> compiled output -> runtime consumer.
- Every material change must have logged review and risk assessment before implementation.

## Priority Escalation (High Priority)
- Naming and semantic clarity for fragments/manifests is a high-priority gate.
- Ambiguous naming is release-blocking risk, not cleanup debt.
- Numeric-only segment names (for example, `seg_01.md`) are allowed only in forensic review artifacts, not production composition sources.

## Source Boundary Rule
- `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/` is review-only.
- Production composition sources must live only in:
  - `resources/prompt_blocks/**`
  - `resources/prompt_composition/**`
- Promotion from review artifact into production source paths must be explicit, logged, and review-approved.

## Primary References (Authoritative)
- `resources/plans/prompt_template_composition_forensics_20260213_183000/index.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/change_matrix.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/prompt_code_touchpoints.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshot_manifest.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/duplicate_lines_report.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/SOURCE_OF_TRUTH.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/compiled_manifest_index.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/artifacts/*.forensic_plan.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/reports/stability_controls.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/proposed_refactor_v1/reports/reuse_index.md`

## Locked Architecture and Policy
- No realtime dynamic prompt construction at runtime.
- Build-time composition emits flat templates in `resources/prompt_templates/*.md`.
- Existing runtime prompt readers remain unchanged:
  - `src/bookforge/pipeline/prompts.py:40-44`
  - `src/bookforge/workspace.py:203-213`
- Pass 1 semantics lock:
  - No normalization of guarded-block line wrapping, punctuation, or intra-line whitespace.
  - No guarded-block prose rewrites.
  - Dedupe only where pre-approved as dedupe-eligible.
- Opaque IDs clarification:
  - Opaque IDs (`B001`, `seg_01`) may exist as secondary references in reports/manifests.
  - Primary source identity (path + filename) must remain semantic.

## Scope
- In scope:
  - Shared prompt blocks and composition manifests.
  - Build-time composer implementation and validations.
  - `book update-templates` integration.
  - Determinism, guarded-block policy, placeholder policy, and behavior-regression gates.
  - Internal review governance and mandatory change/risk/review logging.
- Out of scope:
  - Runtime includes/partials.
  - Dynamic per-request prompt assembly.
  - Prompt precedence model changes between system/phase layers.

## Runtime Coupling Cross-Reference Matrix
| Surface | Runtime Consumer | Deterministic Coupling | Primary Failure Risk |
|---|---|---|---|
| `system_base.md` | `src/bookforge/workspace.py:302,346` | `src/bookforge/prompt/system.py:8-24` | Global phase behavior drift |
| `output_contract.md` | `src/bookforge/workspace.py:303,347` | All phase contracts | Output-shape contract drift |
| `write.md` | `src/bookforge/phases/write_phase.py:35` | `src/bookforge/pipeline/parse.py:70-88`, `src/bookforge/phases/write_phase.py:73-125` | Parse/schema churn |
| `repair.md` | `src/bookforge/phases/repair_phase.py:35` | `src/bookforge/pipeline/parse.py:70-88`, `src/bookforge/phases/repair_phase.py:66-125` | Repair loop instability |
| `state_repair.md` | `src/bookforge/phases/state_repair_phase.py:37` | `src/bookforge/phases/state_repair_phase.py:67-115`, `src/bookforge/pipeline/state_patch.py:407` | Patch canonicalization drift |
| `preflight.md` | `src/bookforge/phases/preflight_phase.py:32` | `src/bookforge/runner.py:604-639`, `src/bookforge/pipeline/state_patch.py:_sanitize_preflight_patch` | Hidden-transition custody drift |
| `lint.md` | `src/bookforge/phases/lint_phase.py:239` | `src/bookforge/phases/lint_phase.py:309-341`, `src/bookforge/pipeline/lint/tripwires.py:29-260` | False pass/fail and retry churn |
| `plan.md` | `src/bookforge/phases/plan.py:65-68` | `src/bookforge/phases/plan.py:335-430` | Scene-card schema drift |
| `outline.md` | `src/bookforge/outline.py:367-370` | Outline schema pipeline | Outline contract drift |
| `continuity_pack.md` | `src/bookforge/phases/continuity_phase.py:31` | Constraints fed into write | Constraint misalignment |

## Known Risk Receipts (Current State)
- `write.md` must_stay_true end-truth line is repeated 11 times.
- `repair.md` must_stay_true reconciliation lines are duplicated 10+ times.
- Shared rules duplicated across `preflight/write/repair/state_repair`.
- Wrapped/concatenated transfer-conflict lines exist and must not be normalized in pass 1.

## Manifest Contract (Hard Gate)
### Contract Artifact
- Manifest schema path (new, required before implementation):
  - `resources/prompt_composition/manifest.schema.json`

### Required Top-Level Fields
- `schema_version` (string)
- `template` (string; target compiled template file)
- `entries` (array of manifest entries)

### Required Entry Fields and Types
- `entry_id` (string, stable within manifest)
- `semantic_id` (string, immutable identity across path changes)
- `source_path` (string, repo-relative fragment path)
- `source_prompt_span` (object):
  - `line_start` (integer >= 1)
  - `line_end` (integer >= `line_start`)
- `owner_phase` (enum): `system`, `outline`, `plan`, `preflight`, `write`, `repair`, `state_repair`, `lint`, `continuity_pack`, `characters_generate`, `author_generate`, `appearance_projection`, `style_anchor`, `output_contract`
- `applies_to` (array of strings; target template ids)
- `guard_level` (enum): `guarded`, `soft`
- `risk_class` (enum): `low`, `medium`, `high`, `critical`
- `dedupe_eligible` (boolean)
- `repeat_policy` (object):
  - `repeat_count` (integer >= 1, default 1)
  - `justification` (string; required when `repeat_count` > 1)

### Manifest Invariants (Validation Rules)
- `semantic_id` must be unique within a template manifest.
- Guarded entries must not repeat unless `repeat_policy.repeat_count` > 1 and justification exists.
- No entry may omit `owner_phase`.
- No entry may set `dedupe_eligible=true` without explicit source span.
- Manifest order is authoritative and must be deterministic.

## Placeholder Contract (Hard Gate)
### Allowlist Artifact
- Canonical allowlist file (new, required before implementation):
  - `resources/prompt_composition/prompt_tokens_allowlist.json`

### Detection Strategy
- Composer scans all `{{...}}` tokens in compiled output.
- Validation policy:
  - Exact, case-sensitive token match against allowlist = allowed.
  - Any token not in allowlist = hard failure.

### Placeholder Audit Artifact
- Required per-template output report:
  - `resources/prompt_composition/reports/placeholder_audit/<template>.json`
- Minimum fields:
  - `template`
  - `allowed_tokens` (array)
  - `unknown_tokens` (array)
  - `status` (`pass` or `fail`)

## Encoding and Newline Contract (Hard Gate)
- Output encoding: UTF-8 **without BOM**.
- Output newline policy: LF (`\n`) only.
- Intra-line policy (pass 1):
  - No punctuation normalization.
  - No intra-line whitespace normalization.
  - No guarded-block line-wrap reflow.
- Validation must assert encoding/newline policy, not only checksum identity.

## Traceability Contract (Hard Gate)
### Trace Artifact
- Required per-template trace artifact:
  - `resources/prompt_composition/reports/compiled_trace/<template>.trace.json`

### Required Fields per Trace Segment
- `compiled_line_start`
- `compiled_line_end`
- `fragment_path`
- `fragment_span` (`line_start`, `line_end`)
- `manifest_entry_id`
- `semantic_id`
- `guard_level`
- `risk_class`

## Composition Requirements (Enforced)
- Deterministic output bytes.
- Acyclic composition graph.
- Guarded vs soft classification enforced.
- Manifest-driven dedupe only.
- Unknown placeholder failure with allowlist retention.
- UTF-8(no BOM)+LF enforcement.
- Trace artifact generation required.
- Optional `compiled_debug/*` provenance output may be generated for reviewers; runtime consumes only clean compiled templates.

## Naming and Semantic Taxonomy (Gate)
- Phase fragment naming:
  - `phase/<phase_name>/<intent_slug>.md`
- Shared fragment naming:
  - `shared/<domain>/<intent_slug>.md`
- Required semantic quality:
  - Path + filename must communicate purpose without opening file.
- Production prohibition:
  - Opaque numeric names as primary identities.

## Approved Naming Set (Locked 2026-02-13)
### Runtime Template Filenames (Compatibility Lock)
These runtime template filenames remain unchanged for compatibility with existing code paths.

- `appearance_projection.md`
- `author_generate.md`
- `characters_generate.md`
- `continuity_pack.md`
- `lint.md`
- `outline.md`
- `output_contract.md`
- `plan.md`
- `preflight.md`
- `repair.md`
- `state_repair.md`
- `style_anchor.md`
- `system_base.md`
- `write.md`

### Phase Fragment Rename Map (Old -> New)
| Old Name | Approved Semantic Name |
|---|---|
| `phase/appearance_projection/seg_01.md` | `phase/appearance_projection/prompt_contract_and_inputs.md` |
| `phase/author_generate/seg_01.md` | `phase/author_generate/prompt_contract_and_inputs.md` |
| `phase/characters_generate/seg_01.md` | `phase/characters_generate/prompt_contract_and_seed_schema.md` |
| `phase/continuity_pack/seg_01.md` | `phase/continuity_pack/prompt_contract_and_constraints.md` |
| `phase/lint/seg_01.md` | `phase/lint/lint_policy_rules_and_inputs.md` |
| `phase/outline/seg_01.md` | `phase/outline/prompt_contract_and_outline_schema.md` |
| `phase/output_contract/seg_01.md` | `phase/output_contract/global_output_contract_rules.md` |
| `phase/plan/seg_01.md` | `phase/plan/scene_card_prompt_contract_and_schema.md` |
| `phase/preflight/seg_01.md` | `phase/preflight/phase_intro_and_core_hard_rules.md` |
| `phase/preflight/seg_02.md` | `phase/preflight/transition_gate_world_alignment_and_constraint_enforcement.md` |
| `phase/preflight/seg_03.md` | `phase/preflight/durable_update_contracts_and_reason_categories.md` |
| `phase/preflight/seg_04.md` | `phase/preflight/input_placeholders_and_output_shape_examples.md` |
| `phase/repair/seg_01.md` | `phase/repair/phase_intro_timeline_and_state_primacy_rules.md` |
| `phase/repair/seg_02.md` | `phase/repair/inventory_mechanics_ui_and_scope_rules.md` |
| `phase/repair/seg_03.md` | `phase/repair/required_output_blocks_and_state_patch_core_rules.md` |
| `phase/repair/seg_04.md` | `phase/repair/json_shape_guardrails_core_arrays_and_summary.md` |
| `phase/repair/seg_05.md` | `phase/repair/durable_registry_transfer_and_creation_requirements.md` |
| `phase/repair/seg_06.md` | `phase/repair/durable_mutation_and_appearance_update_entry_rules.md` |
| `phase/repair/seg_07.md` | `phase/repair/appearance_update_detail_inputs_and_json_contract_examples.md` |
| `phase/state_repair/seg_01.md` | `phase/state_repair/phase_intro_goal_and_reconciliation_rules.md` |
| `phase/state_repair/seg_02.md` | `phase/state_repair/core_state_patch_rules_and_mechanics_ownership.md` |
| `phase/state_repair/seg_03.md` | `phase/state_repair/json_shape_guardrails_and_registry_requirements.md` |
| `phase/state_repair/seg_04.md` | `phase/state_repair/durable_mutation_constraints_scope_and_reason_rules.md` |
| `phase/state_repair/seg_05.md` | `phase/state_repair/input_placeholders_output_blocks_and_json_contract_examples.md` |
| `phase/style_anchor/seg_01.md` | `phase/style_anchor/prompt_contract_and_length_rules.md` |
| `phase/system_base/seg_01.md` | `phase/system_base/global_system_rules.md` |
| `phase/write/seg_01.md` | `phase/write/phase_intro_timeline_and_state_primacy_rules.md` |
| `phase/write/seg_02.md` | `phase/write/inventory_mechanics_ui_and_scope_rules.md` |
| `phase/write/seg_03.md` | `phase/write/summary_requirements_and_state_patch_core_rules.md` |
| `phase/write/seg_04.md` | `phase/write/json_shape_guardrails_core_arrays_and_summary.md` |
| `phase/write/seg_05.md` | `phase/write/durable_registry_transfer_and_creation_requirements.md` |
| `phase/write/seg_06.md` | `phase/write/durable_mutation_and_appearance_update_entry_rules.md` |
| `phase/write/seg_07.md` | `phase/write/appearance_update_detail_output_blocks_and_json_contract_examples.md` |

### Shared Fragment Rename Map (Old -> New)
| Old Name | Approved Semantic Name |
|---|---|
| `shared/B001.must_stay_true_end_truth_line.md` | `shared/summary/must_stay_true_end_state_rule.md` |
| `shared/B002.must_stay_true_reconciliation_block.md` | `shared/summary/must_stay_true_reconciliation_rule.md` |
| `shared/B003.must_stay_true_remove_block.md` | `shared/summary/must_stay_true_remove_directive_rule.md` |
| `shared/B004.scope_override_nonreal_rule.md` | `shared/scope/non_real_timeline_scope_override_rule.md` |
| `shared/B005.json_contract_block.md` | `shared/json_contract/updates_arrays_only_contract_block.md` |
| `shared/B006.global_continuity_array_guardrail.md` | `shared/continuity/global_continuity_updates_array_rule.md` |
| `shared/B007.transfer_registry_conflict_rule.md` | `shared/registry/transfer_registry_conflict_rule.md` |
| `shared/B008a.appearance_updates_object_under_character_updates.md` | `shared/appearance/appearance_updates_object_shape_rule.md` |
| `shared/B008b.appearance_updates_not_array.md` | `shared/appearance/appearance_updates_not_array_rule.md` |

### Manifest Naming Pattern (Approved)
- Approved pattern: `<template>.composition.manifest.json`
- Examples:
  - `write.composition.manifest.json`
  - `repair.composition.manifest.json`
  - `state_repair.composition.manifest.json`
  - `lint.composition.manifest.json`

Transition note:
- Existing forensic review artifact names remain unchanged under `resources/plans/**`.
- Production composition sources/manifests must use the approved semantic naming above.
## Internal Review Model (Mandatory)
### Stage A - Design Review
- Approve taxonomy, manifest schema, placeholder contract, encoding/newline contract.

### Stage B - Implementation Review
- Verify composer policy enforcement, trace generation, and deterministic behavior.

### Stage C - Behavioral Review
- Verify before/after scene pipeline metrics and no new failure classes.

### Review Evidence Rules
- Every stage must write entries into `review_log.md` and `decision_log.md`.
- Rejections must include corrective action and owner.
- Approvals must include scope, risk impact, and evidence links.

## Tracking and Change Logging (Mandatory)
### Required Logs
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/change_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/risk_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/decision_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/review_log.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/controls/validation_log.md`

### Logging Cadence
- Update change log for every material file edit.
- Update risk log whenever risk status changes.
- Update decision log for every scope/policy/implementation decision.
- Update review log at close of each review stage.
- Update validation log after each deterministic or behavioral run.

### Log Enforcement
- CI/pipeline check (new, required before implementation complete):
  - Validate required control logs exist.
  - Validate new entries follow required field template for material changes.
  - Fail validation if code/prompt composition changes occur without corresponding log entries.

### Change Entry Minimum Fields
- `timestamp`
- `author`
- `scope`
- `changed_files`
- `reason`
- `expected_behavior_impact`
- `verification_method`
- `result`
- `rollback_note`

## Story Breakdown (Execution Workstreams)
### Story 0 - Governance Contract Lock (High Priority Gate)
- Finalize and approve remaining governance contract items (naming set approved; see Approved Naming Set):
  - naming taxonomy
  - `manifest.schema.json`
  - `prompt_tokens_allowlist.json` policy
  - encoding/newline contract
- Clarify pass 1 semantic lock wording in all review docs.

Acceptance:
- Governance contract approved and logged.
- No implementation work proceeds before Story 0 approval.

### Story 1 - Inventory and Classification Hardening
- Complete block inventory.
- Assign `guard_level`, `risk_class`, and `dedupe_eligible` per entry.
- Map each block to runtime coupling risk.

Acceptance:
- No unclassified entries.
- No dedupe without explicit eligibility.

### Story 2 - Composer Implementation and Policy Enforcement
- Implement composer with policy checks:
  - manifest schema validation
  - guarded uniqueness enforcement
  - placeholder allowlist enforcement
  - encoding/newline enforcement
- Generate artifacts:
  - `compiled_trace/*.trace.json`
  - `placeholder_audit/*.json`
  - optional `compiled_debug/*`

Acceptance:
- Deterministic outputs and actionable policy failures.
- Required audit artifacts are produced.

### Story 3 - Workflow Integration
- Integrate compose-before-copy into `book update-templates`.
- Keep runtime loading unchanged.

Acceptance:
- Runtime behavior path unchanged.
- Composed templates are the only distributed source.

### Story 4 - Determinism and Integrity Validation
- Add automated checks for:
  - deterministic bytes
  - encoding/BOM/newline compliance
  - guarded-block uniqueness
  - unknown-placeholder failure
  - checksum integrity against approved source-of-truth

Acceptance:
- Validation fails on any contract drift.

### Story 5 - Behavioral Regression Gate
### Baseline Suite Definition (required)
- Minimum suite size: 8 representative scenes.
- Must include at least:
  - 2 previously problematic/pathological scenes
  - 2 inventory/posture-heavy scenes
  - 2 UI/continuity-heavy scenes
  - 2 normal-control scenes
- Run count: minimum 3 seeded runs per scene for baseline and candidate.

### Compared Metrics
- parse/schema pass rate
- tripwire failure rate
- must_stay_true mismatch rate
- mean repair iterations and P95 repair iterations
- new failure-code class appearance

### Acceptance Thresholds (required)
- Parse/schema pass rate drop must be <= 0.5 percentage points.
- Tripwire failure rate increase must be <= 1.0 percentage point.
- must_stay_true mismatch increase must be <= 1.0 percentage point.
- Mean repair iterations increase must be <= 0.2.
- P95 repair iterations increase must be <= 1.
- No new failure-code classes introduced without explicit approval.

Acceptance:
- No threshold breaches attributable to composition changes.

## Go/No-Go Gates (Pass 1)
- G1: Governance contract gate passed (Story 0).
- G2: Manifest policy gate passed.
- G3: Placeholder gate passed (no unknown tokens).
- G4: Encoding/newline gate passed.
- G5: Determinism and checksum integrity gates passed.
- G6: Behavioral regression gate passed.
- G7: Logging gate passed.

## Risk Register (Refined)
| Risk ID | Risk | Trigger | Detection | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-001 | Ambiguous naming causes semantic drift | Non-semantic source names | Naming lint + review | Story 0 taxonomy gate | Composition owner | Open |
| R-002 | Unknown placeholders ship | Token not in allowlist | Placeholder audit | Allowlist hard-fail | Composer owner | Open |
| R-003 | Dedupe changes alter model behavior | Repetition removal in critical text | Story 5 metrics | Threshold gate + targeted review | Validation owner | Open |
| R-004 | Naive dedupe corrupts examples | Broad line-level dedupe | Review + tests | Manifest-only dedupe | Composer owner | Open |
| R-005 | Encoding drift breaks determinism | BOM/newline variance | Encoding checks + checksum drift | UTF-8(no BOM)+LF contract | Composer owner | Open |
| R-006 | Shared block edit breaks other phases | Shared fragment change | Cross-phase diff + runs | Required cross-phase targeted behavioral runs | Review owner | Open |
| R-007 | Review and production trees diverge | Edits in wrong path | Path checks + review | Source boundary rule + promotion logging | Composition owner | Open |
| R-008 | Manifest order drift creates precedence drift | Entry reorder or insertion | Trace diff + behavior diff | Ordered manifest review + trace artifact | Review owner | Open |
| R-009 | Composer version skew causes checksum churn | Different local composer versions | Metadata/version mismatch | Pin composer version and stamp in validation logs | Tooling owner | Open |

## Implementation-Time Internal Review Checklist
- Check 1: Manifest entries validate against locked schema.
- Check 2: Every modified fragment has semantic naming and ownership metadata.
- Check 3: Dedupe changes are explicitly dedupe-eligible.
- Check 4: Guarded-block text has no unauthorized normalization.
- Check 5: Placeholder audit has zero unknown tokens.
- Check 6: Trace artifacts fully map compiled segments to sources.
- Check 7: Runtime coupling surfaces cross-checked against touchpoint map.
- Check 8: Required control logs updated in same work session.

## Definition of Done
- Build-time composition implemented and integrated into `book update-templates`.
- Runtime prompt loading remains single-file and unchanged.
- Governance contract (schema, allowlist, encoding/newline policy) is locked and enforced.
- Guarded/soft, dedupe, placeholder, traceability, and encoding policies enforced by composer.
- Required logs are complete, current, and validated.
- Compiled outputs pass determinism and checksum integrity gates.
- Behavioral regression suite passes all thresholds.
- No material regression attributable to composition migration.

## Status Tracker
- Story 0 (Governance Contract Lock): `completed`
- Story 1: `completed`
- Story 2: `completed`
- Story 3: `completed`
- Story 4: `completed`
- Story 5: `in_progress` (targeted chapter-2 scene-sequence validation passed; full 8x3 behavioral baseline still pending)

### Targeted Validation Update (Completed 2026-02-14)
- Executed scene-by-scene resume testing for `workspace/books/criticulous_b1` chapter 2 completed scenes (`scene_001` through `scene_006`) and collected phase-history/lint/repair artifacts.
- Validation objective passed for this run scope: phase pipeline completed and artifacts were produced for each completed scene.
- Deep trace investigation identified one potential prompt wording gap in stale invariant reconciliation behavior during repair/state_repair cycles.
- Fix applied: strengthened system-level invariant carry-forward wording to require stale or superseded facts be explicitly removed with `REMOVE: <exact prior invariant text>` before restating current truth.
- Updated files for wording fix:
  - `resources/prompt_templates/system_base.md`
  - `workspace/books/criticulous_b1/prompts/templates/system_base.md`
  - `workspace/books/criticulous_b1/prompts/system_v1.md`
  - `resources/prompt_blocks/phase/system_base/global_system_rules.md`

## Immediate Next Actions
1. Execute the remaining Story 5 baseline matrix (8 scenes x 3 seeds) and record threshold comparison metrics in `validation_log.md`.
2. Run Stage C behavioral review and capture approvals/rejections in `review_log.md` + `decision_log.md`.
3. Wire `scripts/validate_prompt_composition_controls.py` into CI with changed-file inputs from git diff.
4. If Story 5 thresholds pass, move Go/No-Go gate status to release-ready and capture final sign-off evidence.


