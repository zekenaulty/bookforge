# System UI Gating & Planner Alignment Plan (20260212_235400)

## Purpose
Prevent premature UI blocks (pre-System scenes) and avoid UI bleed into non-LitRPG genres by adding an explicit, system-level UI gate that overrides author fragments. Align planning, writing, repair, and linting so UI appears only when the scene context allows it.

## Context / Observed Failure
- Author system fragments are injected into `system_v1.md` and can enforce UI unconditionally.
- Planner emits `ui_mechanics_expected` even in pre-System scenes, so UI gets treated as required.
- Writer/repair then inject UI blocks before the world/System is introduced.
- UI rules are LitRPG-specific and currently leak into other genres.

## Observed UI Surface Patterns (Criticulous archive)
These patterns should shape detection + prompt rules:
- Multiple UI blocks can appear on a single line (e.g. `[Vane - Lvl 42] [Class: Shadow Stalker] [HP: 450/450]`).
- UI blocks can include trailing parenthetical suffixes (e.g. `[HP: 1/1] (locked)` or `[HP: 1/1] (Warning: Critical Condition)`).
- UI blocks are often stacked and purely line-based (system notifications, errors, tips, loading screens, combat logs).
- Mixed casing and emphatic headers are common (e.g. `SYSTEM ALERT`, `CRITICAL ERROR`).
- These are still authoritative UI surfaces and must be gated when `ui_allowed=false`.

## Decisions (Data Contract)
- Use a single, explicit boolean: `scene_card.ui_allowed`.
- Keep `scene_card.ui_mechanics_expected` (array of strings) but require it to be empty when `ui_allowed=false`.
- No alias field (`system_active`) to avoid multiple sources of truth.
- Legacy scene cards: if `ui_allowed` is missing, derive it from `ui_mechanics_expected` (non-empty -> true, else false) and normalize.

### Missing `ui_allowed` Fallback Policy (Minimize Genre Bleed)
- Planner must always emit `ui_allowed`; missing is treated as a legacy/manual-card error state.
- Normalization should fill `ui_allowed` from `ui_mechanics_expected` when possible.
- Lint behavior when `ui_allowed` is still missing after normalization:
  - If `ui_mechanics_expected` exists and is non-empty, treat as `ui_allowed=true`.
  - Else if authoritative UI blocks appear, emit `ui_gate_unknown` (warning) that requests the planner to set `ui_allowed` explicitly.
  - Do **not** hard-fail UI when the flag is missing; avoid deadlocks and cross-genre false positives.
- This preserves safety without letting UI bleed silently into other genres.


### JSON Examples (Greedy Guidance)
Valid (pre-System / UI not allowed):
{
  "ui_allowed": false,
  "ui_mechanics_expected": []
}

Valid (System active / UI allowed):
{
  "ui_allowed": true,
  "ui_mechanics_expected": ["HP", "Stamina", "Crit Rate"]
}

Invalid (contradiction):
{
  "ui_allowed": false,
  "ui_mechanics_expected": ["HP"]
}

## Touchpoint Map
### Prompt Templates
- `resources/prompt_templates/system_base.md` (system-level gate that overrides author persona)
- `resources/prompt_templates/plan.md` (adds `ui_allowed`, enforces gating rules, includes valid/invalid examples)
- `resources/prompt_templates/write.md` (UI gate: no UI blocks unless `ui_allowed=true`)
- `resources/prompt_templates/repair.md` (same gate; remove UI blocks if disallowed)
- `resources/prompt_templates/state_repair.md` (same gate; do not preserve UI when disallowed)
- `resources/prompt_templates/lint.md` (UI gate check, issue when UI appears with `ui_allowed=false`)

### Schemas
- `schemas/scene_card.schema.json`
  - Add `ui_allowed` (boolean)
  - Add `ui_mechanics_expected` (array of strings)
  - Decide whether to bump schema version (1.2) and update `SCENE_CARD_SCHEMA_VERSION`

### Code
- `src/bookforge/prompt/system.py` (verify base rules precedence; no change expected)
- `src/bookforge/phases/plan.py`
  - Normalize `ui_allowed` when missing
  - Enforce `ui_mechanics_expected=[]` when `ui_allowed=false`
  - Bump schema version if needed
- `src/bookforge/runner.py`
  - When loading existing scene cards (resume), inject derived `ui_allowed` before validation if missing
- `src/bookforge/pipeline/lint/tripwires.py` or `src/bookforge/pipeline/lint/helpers.py`
  - Deterministic UI gate check for bracketed UI blocks vs `ui_allowed`

### Author Data
- `workspace/authors/eldrik-vale/v2/system_fragment.md` (conditional UI language)
- `workspace/authors/eldrik-vale/index.json` (add v2)
- `workspace/books/criticulous_b1/book.json` (author_ref -> v2)

### Book Overrides / Artifacts
- `book update-templates` to propagate template changes
- Regenerate `system_v1.md` after base rules change

### Docs
- Update help docs if new planner fields or behavior needs to be user-visible (optional)

## Story Breakdown (Detailed)

### Story 1: System Base Rules UI Gate
Summary:
Add a system-level rule that gates UI regardless of author persona.

Files:
- `resources/prompt_templates/system_base.md`

Draft rule (first-pass wording):
- "UI/system blocks (lines starting with '[' and ending with ']') are permitted only when `scene_card.ui_allowed=true`. If `ui_allowed=false`, do not include UI blocks even if an author persona says 'always include'."

Code cross-check:
- Confirm `system_base.md` is injected above author persona (`src/bookforge/prompt/system.py`).

Validation:
- Regenerate `system_v1.md` and verify gate appears under "Base Rules".

### Story 2: Planner UI Gate + Scene Card Schema
Summary:
Planner must emit `ui_allowed` and gate `ui_mechanics_expected` accordingly. Schema and normalization enforce the contract.

Files:
- `resources/prompt_templates/plan.md`
- `schemas/scene_card.schema.json`
- `src/bookforge/phases/plan.py`
- `src/bookforge/runner.py` (resume handling)

Draft prompt changes:
- Add explicit field description: `ui_allowed` (boolean).
- Rules:
  - "Set `ui_allowed=true` only if the scene explicitly depicts System activation or is set in the game world."
  - "If `ui_allowed=false`, `ui_mechanics_expected` MUST be empty."
- Provide valid/invalid JSON examples (see above) directly in prompt.

Code changes:
- In `_normalize_scene_card`, if `ui_allowed` missing, derive from `ui_mechanics_expected` and set default.
- If `ui_allowed=false`, clear `ui_mechanics_expected` to [].
- Update schema (and `SCENE_CARD_SCHEMA_VERSION` if bumping) to include new fields.
- When loading existing scene cards on resume, normalize before validation to avoid schema failures.

Validation:
- Plan a pre-System scene; confirm `ui_allowed=false` and empty `ui_mechanics_expected`.
- Plan a System-active scene; confirm `ui_allowed=true` with UI mechanics list.

### Story 3: Writer/Repair/State Repair Alignment
Summary:
Writer and repair phases must respect `ui_allowed` and avoid emitting UI when disallowed.

Files:
- `resources/prompt_templates/write.md`
- `resources/prompt_templates/repair.md`
- `resources/prompt_templates/state_repair.md`

Draft rule:
- "If `scene_card.ui_allowed=false`, do NOT include UI blocks. Remove or rephrase any existing UI into narrative prose."
- "If `scene_card.ui_allowed=true`, UI blocks are permitted but must still follow UI formatting rules."
- "UI blocks may appear as multiple bracketed segments on a single UI-only line (e.g. `[Name] [HP: ...]`). Do not embed bracketed UI inside narrative sentences."
- "Parenthetical suffixes after a UI block are allowed only as annotations (e.g. `(locked)`, `(Warning: ...)`)."

Validation:
- Pre-System scene should have zero bracketed UI lines.
- System-active scene should still include UI when expected.

### Story 4: Lint UI Gate (Prompt + Deterministic Guard)
Summary:
Lint must enforce the UI gate regardless of LLM drift. Add a prompt rule and a deterministic tripwire.

Files:
- `resources/prompt_templates/lint.md`
- `src/bookforge/pipeline/lint/tripwires.py` (or `helpers.py`)

Draft prompt rule:
- "If `scene_card.ui_allowed=false` and any authoritative UI blocks appear, emit `ui_gate_violation` (warning or error based on lint mode). Cite the offending lines."
- "If `ui_allowed` is missing, do not assume UI is allowed; emit `ui_gate_unknown` when UI blocks appear to request an explicit flag. Do not fail the scene solely for missing `ui_allowed`."

Code rule (deterministic):
- Detect any line containing one or more bracketed UI blocks; treat multi-block lines as UI lines and extract each block for evidence.
- Allow a trailing parenthetical annotation after the final UI block (e.g. `(locked)`), but still treat the line as UI.
- If `ui_allowed=false`, append issue with evidence lines and code `ui_gate_violation`.
- If `ui_allowed` missing after normalization, apply the fallback policy:
  - If `ui_mechanics_expected` is non-empty, treat as allowed.
  - Else if UI blocks appear, emit `ui_gate_unknown` (warning) to prompt explicit `ui_allowed`.
  - Do not emit `ui_gate_violation` when the flag is missing.

Validation:
- A UI block in pre-System scene triggers the issue even if LLM misses it.

### Story 5: Author v2 (Eldrik Vale)
Summary:
Create a new author version with conditional UI language.

Files:
- `workspace/authors/eldrik-vale/v2/system_fragment.md`
- `workspace/authors/eldrik-vale/index.json`
- `workspace/books/criticulous_b1/book.json`

Draft fragment line:
- "Always include explicit game UI elements when the System is active or the scene is set in a game world."

Validation:
- Ensure author v1 remains unchanged.
- Criticulous uses v2 when approved.


## Edge Cases / Risk Review
- Mid-scene activation: allow `ui_allowed=true`, but restrict `ui_mechanics_expected` to what is introduced in the scene.
- Epistolary/log formats in non-LitRPG books: require explicit `ui_allowed=true` in scene card to allow UI-style formatting.
- Dream/simulation scenes: UI may be allowed if System is explicitly active; otherwise keep `ui_allowed=false`.
- Legacy scene cards: ensure normalization avoids schema failures on resume.
- Multi-block UI lines (`[A] [B]`) and UI lines with parenthetical suffixes should still count as UI for gating.
- Bracketed UI must remain line-only; if prose embeds `[HP: 1/1]` mid-sentence, treat as UI and flag when `ui_allowed=false`.
- Manual/legacy scene cards edited outside planner may omit `ui_allowed` even in UI-heavy scenes.
- UI-looking bracketed prose (e.g., `[aside]`, `[sic]`, or stylistic bracket use) could be misread as UI; consider lint severity (warning) only when `ui_allowed` missing.
- UI blocks inside code fences or quoted examples should still be treated as UI if they appear in prose (avoid false negatives).
- Mixed-format lines: UI blocks followed by narrative text on the same line should still be gated; prompt should discourage this but lint should catch if it happens.
- Resume without re-planning can leave `ui_allowed` missing; warnings must persist to influence the next planning pass.
- Scenes that intentionally mimic UI for a non-System artifact (e.g., in-world signage) may look like UI; writers should use narrative framing or a non-bracket format if `ui_allowed=false`.
- If `ui_mechanics_expected` is non-empty but UI blocks are absent, decide whether to warn for missing expected UI (optional; avoid blocking).



## Prompt/Code Alignment Requirements (Expanded)
- Any JSON shape change must include explicit valid/invalid examples in prompts.
- Schema updates must be in lockstep with prompt and code changes.
- If code enforces a rule, the prompt must state it; if prompt introduces a rule, code must either validate or explicitly ignore it.
- Add a verification step per story that confirms prompt output is accepted by code without manual fixes.

## What We Are NOT Doing
- We are not introducing a hard dependency on genre tags for UI gating.
- We are not failing scenes solely because `ui_allowed` is missing.
- We are not auto-classifying genre or trying to infer UI intent from prose alone.
- We are not changing the core UI formatting contract beyond gating and clarity.

## Operational Guidance (Warnings -> Planner Correction)
- `ui_gate_unknown` is advisory only and must not block the scene.
- Warnings should be persisted (phase history + run log) so they can be surfaced to the next planning pass.
- Planner prompt should include recent UI warnings and explicitly set `ui_allowed` on the next scene card.
- If a run resumes without re-planning, the warning remains advisory (no hard fail).

## Definition of Done
- System base rules include a UI gate that overrides author persona.
- Planner emits `ui_allowed`, and `ui_mechanics_expected` is empty when `ui_allowed=false`.
- Writer/repair/state_repair honor the gate consistently.
- Lint flags UI blocks when `ui_allowed=false` (prompt + deterministic guard).
- Eldrik v2 created and criticulous book updated.
- Pre-System scenes contain no UI blocks unless explicitly allowed.

## Tests / Validation
- Generate a pre-System scene:
  - `ui_allowed=false`
  - `ui_mechanics_expected=[]`
  - no UI blocks in prose
- Generate a system-active scene:
  - `ui_allowed=true`
  - UI blocks present and formatted correctly
- Intentionally inject a UI block in a pre-System scene:
  - lint emits `ui_gate_violation` with evidence
- Legacy scene card missing `ui_allowed` (no `ui_mechanics_expected`) with UI blocks:
  - lint emits `ui_gate_unknown` warning

## Status Tracker
- Story 1 (System Base Rules UI Gate): Not started
- Story 2 (Planner UI Gate + Schema): Not started
- Story 3 (Writer/Repair/State Repair alignment): Not started
- Story 4 (Lint guard): Not started
- Story 5 (Eldrik v2 author fragment): Not started

## Notes
- UI gating must be in Base Rules to override author fragments.
- Do not edit author v1 in place; create v2 and update book refs.
- Run `book update-templates` after template changes to propagate overrides.



