# Writing Loop Downstream Transition Hardening Plan (20260215_193219) - Rebuild v2

## Purpose
Replace the prior vague plan with an execution-spec plan that is readable without code spelunking.

This version is explicit about:
1. LLM-owned semantic correction.
2. No deterministic semantic healing.
3. No throwing away LLM-created data.
4. Deterministic routing, gating, and audit behavior.

## Problem Statement (Current)
Observed failure classes:
1. Transition semantic fields can still be machine-generated fallback content that looks schema-valid but is prose-invalid.
2. Some workflows are still framed as reject/drop instead of classify/reconcile/persist.
3. Operator intent is not fully encoded: model should create data, system should classify and route, not discard.

## Non-Negotiable Principles (Locked)
1. LLM is the primary linter for prose and semantic transition validity.
2. Deterministic code may detect, classify, route, gate, and audit.
3. Deterministic code must never synthesize semantic/prose transition content to make validation pass.
4. LLM-created unknown data must not be silently dropped.
5. Unknown data must enter a classification workflow and be persisted in a controlled form.
6. Every failed/paused state must be user-visible in run output and report artifacts.
7. Dead fallback paths must be removed; no retained "just in case" semantic auto-heal code.

## Locked Operator Decisions (2026-02-16)
1. Unknown-key classification/preservation is high-priority and must ship early.
2. Transition insertion requirements are hard-stop critical checks.
3. If insertion is required, the system must retry with targeted LLM guidance up to a separate critical retry cap; exhaustion is terminal `ERROR`.
4. `--ack-outline-issues` cannot bypass unresolved critical transition insertion failures.
5. Location-model redesign remains in phased design scope and is not a blocker for this hardening pass.

## Core Contract: Detect -> Route -> LLM Fix -> Revalidate
For transition semantic failures and unknown-key failures:
1. Detect deterministically.
2. Emit explicit issue code(s) and machine evidence.
3. Route to targeted LLM correction/classification prompt.
4. Re-run validation/lint.
5. Stop only on pass or attempt exhaustion.

## Failure Routing Matrix
| Failure code | Detector owner | Retryable | LLM task | Terminal if exhausted |
|---|---|---|---|---|
| `transition_fields_invalid` | `outline.py` / lint orchestration | yes | rewrite transition semantic fields only | `ERROR` |
| `transition_insertion_required` | phase 04 validator | yes (critical retry cap) | insert/reshape required transition scene(s) | `ERROR` (hard stop) |
| `transition_bridge_missing` | lint semantic adjudication | yes | repair opening bridge realization | `ERROR` in strict, `SUCCESS_WITH_WARNINGS` in non-strict if policy allows |
| `location_registry_missing` | outline location compiler | yes | provide concrete location labels/identity mapping | `ERROR` |
| `unknown_world_key_unclassified` | state apply/reconcile | yes | classify unknown world key(s) | `ERROR` |
| `json_parse` | phase parser | yes | strict JSON-only retry | `ERROR` |

## Transition Semantic Quality Contract
### What is invalid (deterministic route-only detectors)
1. Meta/fallback phrasing in transition text (for example: "this beat", "realized on page", "movement from").
2. ID-like or machine-token anchors (`LOC_*`, `loc_*`, enum-only token soup).
3. Identical in/out anchor sets when seam implies movement/discontinuity.
4. Empty/missing required transition semantic fields.

### What code must never do
1. Auto-fill `transition_in_text`.
2. Auto-fill `transition_out_text`.
3. Auto-fill `transition_in_anchors`.
4. Auto-fill `transition_out_anchors`.

### What code must do instead
1. Emit `transition_fields_invalid` with scene refs + field refs + evidence.
2. Trigger targeted LLM rewrite request scoped to failing scene(s).
3. Revalidate before allowing phase progression.

### Adjudication ownership (explicit)
1. Deterministic checks are route-only and detect obvious invalidity or missing required fields.
2. Semantic transition validity (including `transition_bridge_missing`) is LLM-adjudicated.
3. Deterministic checks do not assert semantic correctness of bridge prose.
4. Severity is policy-owned in code; the model provides structured evidence and verdict rationale.

### Span usage policy (explicit)
1. Opening-span extraction is evidence/audit support only.
2. Span presence is not a standalone pass criterion for semantic validity.
3. Span metadata exists to ground adjudication and review, not to replace LLM semantic judgment.

## Unknown Data Policy (Replaces Drop/Discard Model)
### Intent
The model is allowed to create new world facts and keys. The system must classify them safely, not discard them.

### Classification baseline clarification
1. The known-key allowlist is a baseline for routing/classification, not a reject list.
2. Unknown keys must be classified and preserved; they must not be silently ignored.
3. Hard reject is reserved for explicit operator/security policy only, and raw unknown payload must still be preserved with reason code.

### Allowlist origin (explicit)
The authoritative known-world key set comes from:
1. `schemas/state.schema.json` world structure.
2. `schemas/state_patch.schema.json` `world_updates` expectations.
3. Runtime registry module (new): `src/bookforge/pipeline/state_world_registry.py`.

### Unknown world key lifecycle
When `world_updates` contains unknown keys:
1. Capture raw unknown key/value and source phase in run artifacts.
2. Do not drop.
3. Route to LLM classifier prompt (`state_world_key_classification_v1`).
4. Classifier must return one of:
   - `map_to_existing` (map key/value into known canonical key path),
   - `store_extension` (persist under `world.extensions.<key>` with metadata),
   - `requires_human_decision` (ambiguous/high risk).
5. Apply classified result deterministically.
6. Persist classification ledger entry.

### Persistence requirements
Unknown data must be preserved in at least one durable artifact:
1. `draft/context/phase_history/...` (raw patch remains intact).
2. New ledger artifact: `draft/context/world_key_classification_log.json`.
3. If `store_extension`, persist structured extension payload under state world extensions.

### Disallowed behavior
1. Silent key drop.
2. Silent key overwrite to empty/null.
3. Unknown key acceptance without classification record.

## World Extensions Model (New)
Add controlled extension container:
1. `state.world.extensions` is a dict namespace for model-created world fields that are not yet canonical.
2. Extension entries include:
   - `value`
   - `source_phase`
   - `introduced_at` (chapter/scene)
   - `classification_reason`
   - `promoted` (bool)
3. Promotion to canonical schema requires code/schema update + tests.

## Strictness and Gating
### Run gating
Writing must block when:
1. outline status is `ERROR` or `PAUSED`.
2. unresolved `transition_insertion_required` exists.
3. unresolved `unknown_world_key_unclassified` exists.
4. critical retry cap is exhausted for required transition insertion.

### Override behavior
1. `--ack-outline-issues` can bypass warnings only.
2. Override cannot bypass unresolved hard errors.
3. Override cannot bypass `transition_insertion_required` critical failures.

## Workstream Implementation (File-by-File)

## WS1 - Transition No-Heal Enforcement
### Objective
Guarantee deterministic code cannot synthesize semantic transition content.

### Code files
1. `src/bookforge/outline.py`
2. `src/bookforge/phases/plan.py`

### Changes
1. Keep fallback semantic synthesis removed.
2. Enforce `transition_fields_invalid` for invalid semantic patterns.
3. Enforce `transition_insertion_required` for phase-04 LLM-required insertions with critical retry cap.
4. Planner normalization must fail-route when required semantic fields are unusable.
5. Remove dead transition fallback code paths rather than keeping disabled branches.

### Why
Prevents laundering invalid semantics into passable artifacts.

### Ramifications
1. Higher early failure visibility.
2. More targeted LLM retries.
3. Fewer downstream seam regressions.

## WS2 - Lint Semantic Adjudication Contract
### Objective
Use LLM semantic adjudication for bridge validity with structured evidence.

### Code files
1. `src/bookforge/pipeline/lint/tripwires.py`
2. `src/bookforge/phases/lint_phase.py`

### Prompt files
1. `resources/prompt_templates/lint.md`
2. `workspace/books/<book_id>/prompts/templates/lint.md`
3. `resources/prompt_blocks/phase/lint/lint_policy_rules_and_inputs.md`

### Changes
1. Add transition adjudication sub-contract response schema.
2. Require evidence payload fields and verdict rationale.
3. Severity policy is code-owned; model does not choose severity class.
4. Route-only deterministic tripwires may flag known-bad patterns, but semantic bridge pass/fail remains LLM-adjudicated.

## WS3 - Repair/Regeneration Loop Hardening
### Objective
When transition issues are raised, run targeted LLM repair instead of deterministic patching.

### Code files
1. `src/bookforge/phases/repair_phase.py`
2. `src/bookforge/phases/state_repair_phase.py`
3. `src/bookforge/runner.py`

### Prompt files
1. `resources/prompt_templates/repair.md`
2. `workspace/books/<book_id>/prompts/templates/repair.md`

### Changes
1. Add targeted repair instruction payload with scene refs and failing fields.
2. Route `transition_fields_invalid` and `transition_bridge_missing` into scoped repair tasks.
3. Re-lint mandatory after repair.

## WS4 - Unknown World Key Classification Pipeline
### Objective
Replace drop/reject-only patterns with classify-and-store workflow.

### Code files
1. `src/bookforge/pipeline/state_apply.py`
2. `src/bookforge/pipeline/state_patch.py`
3. `src/bookforge/phases/state_repair_phase.py`
4. New: `src/bookforge/pipeline/state_world_registry.py`
5. New: `src/bookforge/phases/world_key_classification_phase.py` (or helper invoked from state repair)

### Schema files
1. `schemas/state.schema.json`
2. `schemas/state_patch.schema.json`

### Prompt files
1. New: `resources/prompt_templates/world_key_classification.md`
2. New block: `resources/prompt_blocks/phase/state/world_key_classification_contract.md`

### Changes
1. Introduce known-world-key registry helper.
2. Detect unknown keys in `world_updates` and emit `unknown_world_key_unclassified`.
3. Invoke LLM classifier to map/store/escalate.
4. Persist classification ledger artifact.
5. Add `world.extensions` structured container.
6. Explicitly prohibit silent ignore/reject handling of unknown world keys in normal flow.

### Why
Model creativity is preserved while state integrity remains deterministic.

### Ramifications
1. More artifacts and state metadata.
2. Better retention of emergent worldbuilding.
3. Less information loss and fewer "where did this go" defects.

## WS5 - Prompt and System Instruction Alignment
### Objective
Ensure system-level text matches runtime behavior and user intent.

### Files
1. `resources/prompt_blocks/phase/system_base/global_system_rules.md`
2. `resources/prompt_templates/system_base.md`
3. `workspace/books/<book_id>/prompts/system_v1.md`
4. `resources/prompt_templates/write.md`
5. `resources/prompt_templates/lint.md`
6. `resources/prompt_templates/repair.md`

### Changes
1. Explicitly prohibit internal ID tokens in prose including `LOC_*` and `loc_*` forms.
2. Keep anchors as metadata/hints, not phrase-match pass/fail authority.
3. Encode "semantic fields are LLM-owned" language in system-level instructions.

## WS6 - Reporting and Operator Visibility
### Objective
Make failures impossible to miss.

### Files
1. `src/bookforge/outline.py`
2. `src/bookforge/runner.py`
3. `docs/help/run.md`
4. `docs/help/outline_generate.md`

### Changes
1. Report includes counts and scene refs for:
   - `transition_fields_invalid`
   - `transition_insertion_required`
   - `unknown_world_key_unclassified`
2. Console summary prints top reason codes and report path every run.
3. Write gate banner prints hard block reason and exact unblock path.

## WS7 - Test Coverage and Gates
### New/updated tests
1. `tests/test_outline_transition_policy.py`
2. `tests/test_lint_transition_semantic_adjudication.py` (new)
3. `tests/test_repair_transition_contract.py` (new)
4. `tests/test_state_world_key_classification.py` (new)
5. `tests/test_state_world_extensions.py` (new)
6. `tests/test_runner_outline_gate.py`

### Acceptance gates
1. No deterministic semantic auto-fill paths remain for transition fields.
2. Invalid transition semantics always route to LLM correction flow.
3. Unknown world keys never disappear silently.
4. Unknown world keys are classified and persisted with audit trail.
5. Strict mode blocks unresolved hard issues.

## Execution Sequence
1. WS4 unknown world key classification pipeline (priority-first slice).
2. WS1 transition no-heal enforcement.
3. WS2 lint semantic adjudication.
4. WS3 repair/regeneration routing.
5. WS5 prompt/system alignment.
6. WS6 reporting and gating.
7. WS7 tests and signoff.

## Progress Tracker
1. WS1: in_progress
2. WS2: pending
3. WS3: pending
4. WS4: pending
5. WS5: pending
6. WS6: pending
7. WS7: pending

## Risk Level and Mitigation
Overall risk: High.

Top risks:
1. Retry churn increases after no-heal enforcement.
2. Classifier misclassification for unknown keys.
3. Extension namespace bloat.
4. Critical insertion retry exhaustion can block runs more often during early rollout.

Mitigations:
1. Bounded retries with targeted fix payloads.
2. Classifier schema + confidence + escalation mode.
3. Periodic extension promotion/cleanup workflow with tests.
4. Separate critical retry cap plus explicit operator-visible failure reporting.

## Definition of Done
1. Plan is understandable without reading code internals.
2. Deterministic code does not generate semantic prose fields.
3. LLM correction loops are primary for semantic defects.
4. Unknown model-created data is classified and preserved, not dropped.
5. Tests and docs match implementation behavior.

## Reconciled Reviewer Findings
1. Concern about allowlist-neutering is valid as a risk class; this plan now explicitly bans unknown-key ignore/reject in normal flow.
2. Concern about mixed transition ownership is valid as a wording risk; this plan now explicitly locks semantic bridge validity to LLM adjudication and keeps deterministic checks route-only.
3. Concern about span misuse is valid as an implementation risk; this plan now explicitly limits span handling to audit/evidence support.
