# Outline Dynamic Lint?Repair Loop Plan (Draft)

Status: Proposed
Owner: BookForge Outline Pipeline
Date: 2026-04-12

## Summary
Introduce a dynamic, iterative lint?repair?revalidate loop for outline integrity that mirrors the writing loop’s lint/repair behavior. The orchestrator deterministically detects issues, routes scoped fixes, and enforces invariants. The LLM remains the semantic author inside bounded windows. The loop converges via issue fingerprinting, retry caps, and overlap control.

This plan explicitly avoids phase sprawl by grouping repairs into three families (Structural, Identity, Seam) while retaining fine-grained routing and windowed execution.

## Doctrine Alignment
- LLM authors semantics; orchestrator routes and enforces deterministic invariants.
- No deterministic semantic healing; deterministic normalization only when truth is unambiguous.
- No silent dropping of model data; unknown or conflicting facts are routed for LLM repair or hard-failed with a clear reason.

## Goals
1. Make outline integrity self-healing via repeatable lint/repair passes.
2. Localize repairs to windows derived from deterministic lint.
3. Ensure seam metadata is complete and structurally consistent before writing.
4. Prevent cross-phase drift (repair phases should not undo prior fixes).
5. Add convergence signals beyond simple retry caps.

## Non-Goals
- No semantic rewriting of story content beyond scoped repair windows.
- No global “beautification” pass; seam hygiene is structural and localized.
- No expansion into writing-loop changes in this plan.

## Known Failure Modes (to encode explicitly)
- Splice-successor drift: inserted scene’s successor still points to pre-splice anchors.
- Cross-chapter consumes/handoff contradictions.
- Duplicate or missing scene IDs after merges.
- Section echo misplaced or duplicated.
- Optional/omitted seam metadata leading to schema drift.

## Canonical Ownership Matrix
Define which layer owns each truth to avoid contradictions:
- Scene chain truth: scene order + consumes_outcome_from + hands_off_to.
- Intro truth: earliest valid introduces in scenes; registry must match.
- Section echo truth: terminal scene of each section only.
- Location identity: ids are canonical; labels are presentation.
- Thread legitimacy: thread registry is canonical; scenes must reference defined threads.
- Bridge text: descriptive only; may drift unless explicitly regenerated.

## Lint Coverage (Prioritized)
P0 (Structural Integrity)
- Linear chain uniqueness: no fan-in/fan-out for single-chain outline.
- Cross-chapter consumes: disallow consumes_outcome_from into a terminal prior chapter.
- Section echo placement: exactly one echo on terminal scene per section.
- Illegal field combos: terminal + hands_off_to; arrival_checkpoint with no location change (if disallowed).
- Scene ID sequencing: duplicate/missing ids; order mismatch.

P1 (Identity and Registry)
- Location id/label splits (same id with different label; same label with different id).
- Character appears before introduces.
- introduces present but character not in characters array.
- Thread referenced but missing from registry.

P2 (Quality Signals)
- Anchor contradictions: zero overlap, identical in/out anchors, or direction mismatch.
- Bridge contradiction (optional/MVP): only if clearly checkable without semantics.

## Dynamic Lint?Repair Loop
1. Run outline lint (deterministic) ? produce outline_lint_report.json.
2. Router groups issues into repair families and window scopes.
3. Execute repair windows (two-turn per window: T1 plan, T2 execute).
4. Re-run lint.
5. Repeat until clean or convergence stops (retry cap + fingerprint convergence rules).

## Repair Families (Avoid Phase Explosion)
### 1) Structural Repair
Scope: edges, section echoes, chapter boundaries, illegal combinations, scene id order.
- Prefer deterministic normalizer for unambiguous fixes (terminal hands_off_to removal, cross-chapter consumes removal, duplicate echo cleanup).
- LLM repair only when local ambiguity exists.

### 2) Identity Repair
Scope: intro alignment, character presence vs introduces, location id/label drift, thread registry drift.
- LLM repair for local semantic fixes (intro placement when ambiguous).
- Deterministic fixes for registry mismatches with clear ownership rules.

### 3) Seam Repair
Scope: seam_score/resolution, transition in/out anchors and text, splice successor updates.
- LLM repair in strict window scopes.
- Explicit issue-targeted prompts (list exact seam edges to fix).

## Router Rules
- Deterministic normalize if truth is unambiguous.
- LLM repair if truth is local but semantic.
- Hard fail if truth is ambiguous and policy undefined.

## Windowing and Overlap Rules
- Windows built from lint issues; expand by ±1 only on retry.
- Overlapping windows must be merged before repair OR queued sequentially with re-lint between them.
- Deterministic ordering: severity desc ? chapter asc ? scene id asc.

## Convergence Tracking
- Issue fingerprint = hash(code + scope + refs + window).
- Track if issues persist unchanged, mutate in place, or new issues appear.
- Fail when an issue repeats unchanged beyond cap OR if repair introduces new issues outside window.

## Retry Strategy
- N attempts at original window size.
- M attempts at expanded window size.
- If still failing: hard fail with clear report (do not silently pass).

## Artifacts
- outline_lint_report.json
- outline_lint_repair_plan.json (router output)
- outline_repair_history.jsonl
- per-window inputs/outputs/validation (existing pattern)

## Integration Points (Initial)
- src/bookforge/outline.py (loop + router orchestration)
- src/bookforge/phases/outline/validators.py (lint issues + fingerprints)
- src/bookforge/phases/outline/* (repair family handlers)
- resources/prompt_blocks/phase/outline_pipeline (issue-targeted prompts)

## Rollout Stages
Stage 1: P0 lint + report emission.
Stage 2: Deterministic normalizer for obvious contract violations.
Stage 3: Router + localized LLM repair (Structural, Identity, Seam).
Stage 4: Convergence tracking + overlap management.
Stage 5: Expand P1/P2 lint scope.

## Acceptance Criteria
- Lint report produced every run with deterministic issue list.
- Repair loop converges or hard-fails with explicit reason codes.
- No repair pass touches fields outside allowlist.
- Seam metadata complete and validated before Phase 05.
- No cross-chapter consumes into terminal chapters.

## Open Questions
- Should bridge contradiction lint be MVP or deferred?
- Exact legal matrix for handoff_mode vs location jumps.
- Whether thread lifecycle checks should be P1 or P2.

