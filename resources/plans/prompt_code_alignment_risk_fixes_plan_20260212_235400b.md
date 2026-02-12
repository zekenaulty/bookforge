# Prompt/Code Alignment Risk Fixes Plan (20260212_235400b)

## Purpose
Address high/medium/low severity prompt-code mismatches discovered in the deep review. The goal is to eliminate contradictions, close detection blind spots, and preserve the "loose but safe" system posture without introducing new deadlocks.

## Scope
Covers all issues in the review list:
1) Base rule conflict with REMOVE directives
2) Inline UI detection blind spot
3) Chapter-boundary warning carryover
4) Pipeline_state_incoherent enforcement gap
5) Prose hygiene rule not enforced
6) UI suffix tolerance mismatch
7) ui_allowed required in prompt but not schema (documented soft design)

## Guiding Principles
- Prefer soft enforcement (warnings) over hard fail for ambiguous cases.
- No new hard genre gates or strict format requirements unless required for correctness.
- Every prompt rule must be supported by code behavior or explicitly documented as advisory.

---

## Story 1 - Resolve Base Rule vs REMOVE Conflict (High)
**Problem:** Base rule says "do not drop invariants" while phase prompts require `REMOVE:`.

**Plan:**
- Update `resources/prompt_templates/system_base.md` to explicitly permit REMOVE as a sanctioned exception.
- Verify write/repair/state_repair still instruct to use REMOVE for stale invariants.

**Draft rule (base system):**
- "Do not drop invariants **unless** you explicitly remove a stale fact using `REMOVE:` and restate the current truth."

**Files:**
- `resources/prompt_templates/system_base.md`
- `resources/prompt_templates/write.md`
- `resources/prompt_templates/repair.md`
- `resources/prompt_templates/state_repair.md`

**Acceptance:**
- No contradictions between Base Rules and phase prompts.
- LLM can follow REMOVE without conflicting instructions.

---

## Story 2 - Inline UI Detection (High)
**Problem:** UI blocks embedded mid-sentence bypass deterministic UI gating.

**Plan:**
- Add a **secondary** detection pass for inline, UI-shaped tokens (`[Key: 10]`, `[HP: 1/1]`, `[System Notification: ...]`).
- Only use it for UI gating (warning or ui_allowed=false violation), not for general stat enforcement.
- Keep severity soft (warning by default) when ui_allowed missing to avoid false positives.

**Implementation shape:**
- Extend UI detection to scan for bracketed UI patterns anywhere in a line, but only those with UI shape (colon + numeric or system keywords). Do not flag `[aside]` or `[sic]`.
- Use warnings when ui_allowed missing; only error in strict mode when ui_allowed=false.

**Files:**
- `src/bookforge/pipeline/parse.py` (optional: add helper to extract inline UI-shaped tokens)
- `src/bookforge/pipeline/lint/tripwires.py` (apply ui_gate on inline hits)
- `resources/prompt_templates/lint.md` (note that inline UI is still UI and should be avoided)

**Acceptance:**
- Inline UI in narrative is detected and gated without over-flagging non-UI brackets.

---

## Story 3 - Chapter-Boundary Warning Carryover (Medium)
**Problem:** ui_gate_unknown warnings only influence the next scene in the same chapter.

**Plan:**
- Extend `recent_lint_warnings` so if `scene==1`, it checks the **last scene of previous chapter**.
- If found, pass ui_gate_unknown warnings into the plan prompt as advisory.
- Still no hard fail; only a planning nudge.

**Implementation shape:**
- If `scene==1` and `chapter>1`, load outline, find previous chapter, compute last scene index, read phase_history for that scene.

**Files:**
- `src/bookforge/phases/plan.py`
- `resources/prompt_templates/plan.md`

**Acceptance:**
- ui_gate_unknown in last scene of a chapter is surfaced to next chapter planning.

---

## Story 4 - pipeline_state_incoherent Deterministic Enforcement (Medium)
**Problem:** Prompt requires pipeline_state_incoherent single-issue, but no enforcement exists.

**Plan:**
- After LLM lint output normalization, if we detect contradictions (pre/post invariants vs candidate state), inject/replace with a deterministic pipeline_state_incoherent issue.
- If pipeline_state_incoherent is present, enforce single-issue output.

**Implementation shape:**
- Compare post_invariants (must_stay_true) to post_state candidate for obvious conflicts.
- If found, replace report.issues with single error item.

**Files:**
- `src/bookforge/phases/lint_phase.py` or `src/bookforge/pipeline/lint/helpers.py`

**Acceptance:**
- No multi-issue reports when pipeline_state_incoherent is detected.

---

## Story 5 - Prose Hygiene Enforcement (Medium)
**Problem:** Base rule forbids internal ids in prose, but no enforcement exists.

**Plan:**
- Add a lint tripwire that flags use of internal IDs (CHAR_, ITEM_, THREAD_, hand_left/hand_right) in prose.
- Severity warning in non-strict mode, error in strict mode.

**Files:**
- `src/bookforge/pipeline/lint/tripwires.py`
- `resources/prompt_templates/lint.md` (document the check)

**Acceptance:**
- Any leaked internal ids in prose become lint warnings/errors.

---

## Story 6 - Parenthetical Suffix Tolerance (Low)
**Problem:** Parser allows parenthetical suffixes after UI blocks; writer prompt only permits (locked).

**Plan:**
- Loosen writer/repair prompts to allow parenthetical annotations after UI blocks (consistent with parser).
- Keep examples minimal to avoid encouraging spammy UI.

**Files:**
- `resources/prompt_templates/write.md`
- `resources/prompt_templates/repair.md`
- `resources/prompt_templates/state_repair.md`

**Acceptance:**
- Prompt guidance matches parser tolerance; no conflicting instructions.

---

## Story 7 - ui_allowed Required in Prompt vs Optional Schema (Low)
**Problem:** Prompt says required; schema allows optional.

**Plan (soft design):**
- Document that schema remains permissive; missing ui_allowed yields ui_gate_unknown warnings.
- Optionally add a validation warning in plan normalization logs (not a hard error).

**Files:**
- `resources/prompt_templates/plan.md`
- (Optional) `src/bookforge/phases/plan.py` logging only

**Acceptance:**
- No hard failure for missing ui_allowed; warnings guide correction.

---

## Status Tracker
- Story 1 (Base Rule vs REMOVE): Completed
- Story 2 (Inline UI Detection): Completed
- Story 3 (Chapter-boundary warning carryover): Completed
- Story 4 (pipeline_state_incoherent enforcement): Completed
- Story 5 (Prose hygiene enforcement): Completed
- Story 6 (UI suffix tolerance): Completed
- Story 7 (ui_allowed soft mismatch): Completed

## Definition of Done
- No contradictions between Base Rules and phase prompts for REMOVE.
- Inline UI cannot bypass UI gating.
- ui_gate_unknown warnings propagate across chapter boundaries.
- pipeline_state_incoherent becomes deterministic and single-issue.
- Internal ids in prose are flagged consistently.
- Writer/repair prompts align with parser UI suffix tolerance.
- ui_allowed remains a soft requirement with warnings rather than hard fail.
