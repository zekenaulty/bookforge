# Criticulous B1 Chapter 1 Phase-Issue Audit Report

## Report Metadata
- Timestamp: 2026-02-13 05:05:15 (local)
- Scope: `workspace/books/criticulous_b1` chapter 1 (`ch001_sc001` through `ch001_sc008`)
- Requested output: classify failures as:
1. valid failure -> why it could not be fixed
2. invalid failure -> reason -> fix
3. valid failure -> more repair retries would likely resolve
- Constraint honored: no code changes, no prompt changes

## Artifacts Reviewed
- Scene phase artifacts:
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc001/*`
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc002/*`
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc003/*`
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc004/*`
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/*`
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc006/*`
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/*`
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc008/*`
- Run logs:
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_075056.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_080621.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_082609.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_085104.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_090406.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_092801.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_093518.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_095857.log`
- LLM request/response logs:
  - `workspace/logs/llm/criticulous_b1_ch001_sc001_*`
  - `workspace/logs/llm/criticulous_b1_ch001_sc002_*`
  - `workspace/logs/llm/criticulous_b1_ch001_sc003_*`
  - `workspace/logs/llm/criticulous_b1_ch001_sc004_*`
  - `workspace/logs/llm/criticulous_b1_ch001_sc005_*`
  - `workspace/logs/llm/criticulous_b1_ch001_sc006_*`
  - `workspace/logs/llm/criticulous_b1_ch001_sc007_*`
  - `workspace/logs/llm/criticulous_b1_ch001_sc008_*`
- Character state lineage:
  - `workspace/books/criticulous_b1/draft/context/characters/history/ch000_sc000_artie__885370d6.state.json`
  - `workspace/books/criticulous_b1/draft/context/characters/history/ch000_sc000_vane__33187bc9.state.json`
  - `workspace/books/criticulous_b1/draft/context/characters/history/ch001_sc001_artie__885370d6.state.json` through `.../ch001_sc007_artie__885370d6.state.json`
  - `workspace/books/criticulous_b1/draft/context/characters/vane__33187bc9.state.json`
- Relevant code for mechanical behavior verification:
  - `src/bookforge/pipeline/lint/helpers.py`
  - `src/bookforge/pipeline/state_apply.py`
  - `src/bookforge/runner.py`

## Executive Summary
- Final lint status by scene:
  - Fail: `sc001`, `sc003`, `sc005`, `sc008`
  - Pass (warnings): `sc002`, `sc004`, `sc006`, `sc007`
- The highest-impact unresolved class is **pipeline_state_incoherent** caused by stale character invariants in lint candidate snapshots (`sc001`, `sc008`).
- The second unresolved class is **pov_drift** (`sc003`, `sc005`) that appears fixable with additional/targeted repair retries.
- State transition quality is mixed:
  - Artie transitions (wallet drop, trophy acquisition) mostly persist correctly in final state history.
  - Vane sword posture transition remains incoherent because old invariant text (`back_sheath`) persists alongside new posture (`hand_right`).

## Scene-by-Scene Classification

### Scene 001 (`ch001_sc001`)
- Lint attempt 1 (`workspace/logs/llm/criticulous_b1_ch001_sc001_lint_scene_20260213_080307.txt`):
  - `naming_custody_violation` (error), `appearance_check_missing` (warning)
- Repair prose (`workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc001/repair_prose.txt`) corrected custody sentence to canonical item naming (`Leather Wallet`).
- Lint attempt 2 (`workspace/logs/llm/criticulous_b1_ch001_sc001_lint_scene_20260213_080554.txt`):
  - `pipeline_state_incoherent` (error): wallet simultaneously dropped in must_stay_true but still carried in character invariants.
- Classification:
  - First failure: valid, fixed by repair.
  - Second failure: invalid mechanical snapshot incoherence.
- Why not fixed in-loop:
  - Prompt candidate includes stale character invariant line from character state (`...container=hand_right`) while post summary says dropped to world.
  - This mismatch appears in lint prompt itself (`workspace/logs/llm/criticulous_b1_ch001_sc001_lint_scene_20260213_080554.prompt.txt`).

### Scene 003 (`ch001_sc003`)
- Lint attempt 1 (`...083904.txt`): `pov_drift` + appearance warning.
- Repair prose still contains first-person leak (`If it touched me...`) in narration (`workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc003/repair_prose.txt`).
- Lint attempt 2 (`...085036.txt`): still `pov_drift`.
- Classification:
  - valid failure -> likely resolvable with additional retries.
- Why not fixed in-loop:
  - Repair pass addressed other content but missed one remaining first-person token in non-dialogue narration.

### Scene 005 (`ch001_sc005`)
- Lint attempt 1 (`...091539.txt`): `pov_drift`, `item_naming_custody`, `item_naming_anchor`, appearance warning.
- Repair pass removes naming errors from the second lint report.
- Lint attempt 2 (`...092746.txt`): still `pov_drift`.
- Repair prose still contains non-dialogue first-person leak (`The absurdity of it hit me...`) in `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/repair_prose.txt`.
- Classification:
  - valid failure -> likely resolvable with additional retries.
- Why not fixed in-loop:
  - Single repair pass fixed inventory naming but left one POV defect.

### Scene 007 (`ch001_sc007`)
- Lint attempt 1 (`...094738.txt`): `pov_drift` + appearance warning.
- Repair pass succeeds.
- Lint attempt 2 (`...095842.txt`): pass (warnings only).
- Classification:
  - valid failure -> fixed by one repair retry.
- Significance:
  - Confirms POV drift class is repairable when the repair pass fully rewrites drift lines.

### Scene 008 (`ch001_sc008`)
- Lint attempt 1 (`...101548.txt`): `pipeline_state_incoherent` on aggro value (92 vs 94).
- Repair/state_repair patches add REMOVE for old aggro and replace with 94 (`workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc008/repair_patch.json`, `.../state_repair_patch.json`).
- Lint attempt 2 (`...102259.txt`): new `pipeline_state_incoherent` on Vane sword posture invariant conflict.
- Evidence:
  - Vane state contains both invariants in current state file:
    - equipped back_sheath
    - held hand_right
  - `workspace/books/criticulous_b1/draft/context/characters/vane__33187bc9.state.json`
- Classification:
  - First failure: valid and fixed.
  - Second failure: invalid mechanical/merge inconsistency.
- Why not fixed in-loop:
  - Patch updated inventory/containers to hand_right but stale invariant text remained.

## Transition Integrity Audit (State Patch / Repair Patch / State Repair)

### Transition A: Death event wallet drop (`sc001 -> sc002`)
- Intended transition:
  - Wallet moves from Artie hand to world/floor in scene 1.
- Patch evidence:
  - `sc001` write/repair/state_repair all include REMOVE for carried wallet and new dropped-world entry.
- Persisted state evidence:
  - `workspace/books/criticulous_b1/draft/context/characters/history/ch001_sc001_artie__885370d6.state.json` no longer has wallet inventory item.
- Conclusion:
  - Persisted state is correct post-apply.
  - Lint fail was in candidate snapshot comparison phase, not final persistence.

### Transition B: Trophy acquisition and carry posture (`sc005+`)
- Intended transition:
  - Artie gains and carries `ITEM_PARTICIPATION_TROPHY` in `hand_left`.
- Patch evidence:
  - `sc005` write patch includes trophy held entry; persisted through subsequent patches.
- Persisted state evidence:
  - Artie history snapshots `ch001_sc005` onward include trophy held in `hand_left`.
- Conclusion:
  - This transition persisted correctly.

### Transition C: Vane sword posture (`sc008`)
- Intended transition:
  - Vane holds `ITEM_OBSIDIAN_BLADE` in `hand_right` during confrontation.
- Patch evidence:
  - `sc008` write/repair/state_repair character updates consistently show inventory+containers with `hand_right` held.
- Persisted state evidence:
  - Current Vane state has inventory/containers aligned to hand_right.
  - But invariants contain both old (`back_sheath equipped`) and new (`hand_right held`) lines.
- Conclusion:
  - Structured inventory/container state transitioned correctly.
  - Text invariants are stale/conflicting and create lint incoherence.

## Root Cause Analysis

### Root Cause 1: Lint candidate merge can retain stale character invariant strings
- Verified code behavior:
  - `src/bookforge/pipeline/lint/helpers.py` merges `character_updates` inventory/containers and continuity updates.
  - It does not apply summary `REMOVE:` directives to `character_states[].invariants` for lint candidate snapshots.
- Contrasting persistence behavior:
  - `src/bookforge/pipeline/state_apply.py` applies summary removals to persisted character invariants in `_apply_character_updates`.
- Net effect:
  - Lint can inspect a stale snapshot and raise `pipeline_state_incoherent` even when final persisted state is corrected later.

### Root Cause 2: POV drift repair quality is inconsistent, retry budget limited in practice
- Evidence:
  - `sc003` and `sc005` retain one first-person narration leak after repair.
  - `sc007` demonstrates same class can be fixed by repair.
- Interpretation:
  - This is a model-output precision issue, not a schema/mechanical impossibility.

### Root Cause 3: Warning volume includes low-signal recurring warnings
- Recurrent warnings:
  - `appearance_check_missing`
  - `stat_unowned` / `stat_mismatch`
  - `word_count_deviation`
- Impact:
  - Not blocking, but creates noise and makes real failures harder to triage quickly.

## Required Classification (Requested Format)

### A) Valid failure -> why it could not be fixed
- `sc003` final `pov_drift`:
  - Could not be fixed in available repair attempt because one first-person narration sentence remained after repair.
- `sc005` final `pov_drift`:
  - Could not be fixed in available repair attempt because one first-person narration sentence remained after repair.

### B) Invalid failure -> reason -> fix
- `sc001` final `pipeline_state_incoherent` (wallet carried vs dropped):
  - Reason: stale character invariant in lint candidate snapshot despite corrected summary facts.
  - Fix theory: align lint candidate invariant handling with apply-time removal semantics so `REMOVE:` directives and/or post-update state are reflected before incoherence checks.
- `sc008` final `pipeline_state_incoherent` (Vane back_sheath + hand_right invariant conflict):
  - Reason: old invariant text remains while structured state moved to new posture.
  - Fix theory: same invariant-removal alignment, plus explicit stale posture removal generation in repair/state_repair.

### C) Valid failure -> more repair retry attempts would likely resolve
- `pov_drift` class (sc003/sc005) is likely retry-fixable:
  - Evidence: same class resolved in `sc007` after repair retry.
  - Theory: additional retry pass with focused POV-only correction would likely clear remaining drift lines.

## Proposed Solutions and Theories (No Changes Applied)

### High-confidence mechanical fixes
- Ensure lint post-candidate character invariants use the same removal semantics as persisted apply path.
- During lint candidate assembly, apply `REMOVE:` directives against character invariant strings before incoherence checks.
- Treat unresolved duplicate posture invariants as stale-state merge artifacts unless summary/inventory/containers corroborate them.

### Prompt/process fixes with high expected value
- Strengthen repair/state_repair instructions to always remove superseded inventory posture invariants when posture changes (especially weapon/container posture shifts).
- Add explicit “POV sanitize pass” expectation in repair when `pov_drift` occurs.

### Retry strategy theory
- For `pov_drift` and similar single-line prose defects, one additional repair cycle likely gives material win-rate improvement.
- For `pipeline_state_incoherent` rooted in stale candidate merge, retries alone are low-value until snapshot logic is aligned.

## Confidence
- High confidence on mechanical stale-invariant finding (cross-validated in:
  - lint prompt payloads,
  - phase patches,
  - persisted character states,
  - code-path differences between lint merge and apply-time merge).
- Medium-high confidence on retry-likely class for POV drift (demonstrated by scene7 success on same failure type).

## Final Assessment
- The run produced a mix of:
  - true repairable prose issues (`pov_drift`), and
  - false/non-actionable incoherence failures driven by candidate state merge behavior.
- Transition data quality is mostly solid for structured inventory/containers.
- The main instability is text-invariant coherence during lint candidate evaluation, not core durable state persistence.
