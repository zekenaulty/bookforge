# Prompt Composition Forensic Index (20260213_183000)

## Objective
Produce a forensic-grade planning package for prompt-template composition that is safe against semantic drift.

This package provides, for **every prompt template**:
- A full numbered snapshot with hash
- Code touchpoints with source-line citations
- A prompt-specific change plan with line spans and replacement language strategy

## Folder Layout
- `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshot_manifest.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/prompt_code_touchpoints.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/duplicate_lines_report.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/*.snapshot.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/artifacts/*.forensic_plan.md`

## Composition Architecture (Planned)
- Source blocks: `resources/prompt_blocks/**`
- Phase manifests: `resources/prompt_composition/**`
- Generated outputs remain flat: `resources/prompt_templates/*.md`
- Runtime remains unchanged: phases still load single flat files.

## Canonical Shared Blocks (Planned Introductions)
These are planned source blocks used to replace duplicated spans while preserving language.

### `B001.must_stay_true_end_truth_line`
- Canonical source: `resources/prompt_templates/write.md:11`
- Text:
```text
- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
```
- Duplicate spans currently: `resources/prompt_templates/write.md:24,65,68,71,81,105,155,158,194,197`

### `B002.must_stay_true_reconciliation_block`
- Canonical source: `resources/prompt_templates/repair.md:8-10`
- Text:
```text
- must_stay_true reconciliation (mandatory):
  - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - Remove conflicting old invariants rather than preserving them.
```
- Duplicate spans currently: `resources/prompt_templates/repair.md:55-58,60-63,65-68,82-85,87-90,108-111,134-137,189-192,194-197`

### `B003.must_stay_true_remove_block`
- Canonical source: `resources/prompt_templates/write.md:12-15`
- Text:
```text
- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
```

### `B004.scope_override_nonreal_rule`
- Canonical source: `resources/prompt_templates/write.md:59-62`
- Equivalent spans also in:
  - `resources/prompt_templates/preflight.md:23-26`
  - `resources/prompt_templates/repair.md:71-74`
  - `resources/prompt_templates/state_repair.md:119-122`
- Text retained per phase with no semantic change.

### `B005.json_contract_block`
- Canonical source candidate: `resources/prompt_templates/write.md:215-233`
- Equivalent blocks in:
  - `resources/prompt_templates/preflight.md:135-153`
  - `resources/prompt_templates/repair.md:233-251`
  - `resources/prompt_templates/state_repair.md:163-181`

### `B006.global_continuity_array_guardrail`
- Canonical source: `resources/prompt_templates/write.md:91-93`
- Equivalent spans in:
  - `resources/prompt_templates/preflight.md:99-101`
  - `resources/prompt_templates/repair.md:120-122`
  - `resources/prompt_templates/state_repair.md:68-70`
  - `resources/prompt_templates/output_contract.md:19-21`

### `B007.transfer_registry_conflict_rule`
- Canonical source family:
  - `resources/prompt_templates/write.md:127-130`
  - `resources/prompt_templates/preflight.md:115-118`
  - `resources/prompt_templates/repair.md:158-161`
  - `resources/prompt_templates/state_repair.md:103-106`
- Note: multiple prompts currently contain line-wrap/concatenation artifacts in this region; composition pass must preserve current behavior unless explicitly approved to normalize text.

### `B008.appearance_updates_object_guardrail`
- Canonical source family:
  - `resources/prompt_templates/write.md:107-109` and `140-142`
  - `resources/prompt_templates/repair.md:138-140` and `174-176`
  - `resources/prompt_templates/state_repair.md:83-85`

## Code Coupling Map (Critical)
- Template distribution and prompt assembly:
  - `src/bookforge/workspace.py:41-53`
  - `src/bookforge/workspace.py:203-213`
- Runtime template resolution:
  - `src/bookforge/pipeline/prompts.py:40-44`
  - `src/bookforge/phases/plan.py:65-68`
  - `src/bookforge/outline.py:367-370`
- System prompt assembly:
  - `src/bookforge/workspace.py:302-303`
  - `src/bookforge/workspace.py:346-347`
  - `src/bookforge/prompt/system.py:8-24`
- JSON/contract-sensitive consumers:
  - Write parse/validation: `src/bookforge/pipeline/parse.py:70-88`, `src/bookforge/phases/write_phase.py:73-125`
  - Lint parse/normalization/tripwires: `src/bookforge/phases/lint_phase.py:309-341`, `src/bookforge/pipeline/lint/tripwires.py:29-260`
  - Preflight/state application: `src/bookforge/phases/preflight_phase.py:32-71`, `src/bookforge/runner.py:604-639`

## Prompt Artifact Inventory
- `appearance_projection.md.forensic_plan.md`
- `author_generate.md.forensic_plan.md`
- `characters_generate.md.forensic_plan.md`
- `continuity_pack.md.forensic_plan.md`
- `lint.md.forensic_plan.md`
- `outline.md.forensic_plan.md`
- `output_contract.md.forensic_plan.md`
- `plan.md.forensic_plan.md`
- `preflight.md.forensic_plan.md`
- `repair.md.forensic_plan.md`
- `state_repair.md.forensic_plan.md`
- `style_anchor.md.forensic_plan.md`
- `system_base.md.forensic_plan.md`
- `write.md.forensic_plan.md`

## Review Workflow
1. Review each `snapshots/*.snapshot.md` file for exact current text.
2. Review each `artifacts/*.forensic_plan.md` file for span-level proposed operations.
3. Approve or reject operations per prompt.
4. Only after approval: execute composition implementation and generated-template migration.

## Status
- Snapshot capture: `completed`
- Code touchpoint mapping: `completed`
- Per-prompt forensic plans: `in_progress`
- External review package readiness: `in_progress`
