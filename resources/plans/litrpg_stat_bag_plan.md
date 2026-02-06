# LitRPG Stat Bag & Continuity Hardening Plan (Draft)

## Purpose
Lock down numeric/mechanical continuity for LitRPG-style output without building a full RPG engine. Provide a minimal structured state bag, enforce “numbers must be owned,” and add light repair checks to prevent drift in stats, UI values, and canonical tokens.

## Scope (In)
- Structured state bag for stats (character + optional global).
- State patch updates for stats (set/delta + reason).
- Prompt hardening for numeric ownership and canonical token reuse.
- Lightweight repair checks for UI/prose numeric drift.
- POV consistency enforcement (no 1st/3rd drift).

## Scope (Out)
- Full deterministic stat simulation.
- Genre-specific prompt templates.
- Thought-signature caching or multi-turn stateful sessions.

---

## Phase 1: Schema Extensions (Minimal, Flexible)
### 1.1 Character State Bag
Add to character state (book-scoped):
- `stats` (object, free-form)
  - Example keys: `hp`, `stamina`, `crit_rate`, `aggro_aura_color`
  - Values: objects or primitives (allow flexible typing)
- `skills` (object, free-form)
  - Example keys: `power_strike`, `parry`, `glitch_dash`
  - Values: objects or primitives (allow flexible typing)

Example:
```
"stats": {
  "hp": {"current": 1, "max": 1, "locked": true},
  "stamina": {"current": 42, "max": 100},
  "crit_rate": {"value": "100%", "locked": true},
  "aggro_aura_color": "gold"
},
"skills": {
  "power_strike": {"rank": 1, "cooldown_s": 8},
  "glitch_dash": {"rank": 1, "charges": 1}
}
```

### 1.2 Optional Global Bag
Add to book state:
- `run_stats` (object, free-form)
  - For global counters/flags not tied to a character

### Definition of Done
- State schema updated to allow `stats` on character state and `run_stats` on book state.
- No enforcement of specific stat names or value types.

---

## Phase 2: State Patch Updates
### 2.1 Patch Ops (Character Stats/Skills)
Add to state_patch schema:
- `character_stat_updates` (array)
  - `character_id`
  - `set` (object)
  - `delta` (object)
  - `reason` (string, optional)
- `character_skill_updates` (array)
  - `character_id`
  - `set` (object)
  - `delta` (object)
  - `reason` (string, optional)

### 2.2 Patch Ops (Global Stats/Skills)
Add to state_patch schema:
- `run_stat_updates` (object)
  - `set`, `delta`, `reason`
- `run_skill_updates` (object)
  - `set`, `delta`, `reason`

### 2.3 Apply Rules
- Apply `set` first (authoritative)
- Apply `delta` after (numeric only)
- If key missing, `delta` creates it (numeric only)
- Apply the same rules to skills as stats

### Definition of Done
- Patch schema updated with stat update sections.
- Apply pipeline persists stat updates to character state + run state.

---

## Phase 3: Prompt Hardening (Numbers Must Be Owned)
### 3.1 System-Level Rule
Add to system prompt:
> If mechanics or UI are present, all numeric values and labels (stats/skills) must be sourced from state or updated in the state_patch. Do not invent numbers or token labels.

### 3.2 Writer/Repair Rules
Add to write/repair prompts:
- “Numbers must be owned: any UI/prose number shown must exist in state or be added in the patch.”
- “Canonical descriptors (colors, item names, effect IDs) must be reused exactly; do not paraphrase.”
- “Invariants are narrative facts only. Do not store numeric stats in invariants.”
- POV lock: keep consistent POV across the scene.

### Definition of Done
- Prompts updated to enforce numeric ownership and canonical token reuse.

---

## Phase 4: Repair Pass (Light Enforcement)
### 4.1 UI/Prose Match Check
Add checks:
- If UI shows numbers not found in stats → repair required.
- If canonical tokens differ (e.g., aura color changes) → repair required.

### 4.2 Repair Prompt Behavior
Repair should:
- Preserve prose content.
- Reconcile stats + UI values.
- If introducing a new number, update stats in patch.

### Definition of Done
- Repair step detects mismatches and triggers reconciliation.

---

## Phase 5: Invariant Hygiene
### 5.1 Redirect Numeric Invariants
- Do not add numeric lines to invariants.
- If found, migrate into stats/skills during state_repair.

### Definition of Done
- Numeric invariants are avoided; stats are used instead.

---

## Phase 6: POV Consistency
### 6.1 Lint Rule
Add a simple POV lint:
- If configured 3rd person, flag first-person pronouns in new scene.

### Definition of Done
- POV drift warnings are emitted in lint output.

---

## Acceptance Criteria
- Stat and skill values remain consistent across scenes unless explicitly updated.
- Canonical tokens (e.g., aura color, item names) remain consistent.
- Viewpoint remains stable across the chapter.
- Invariants no longer accumulate numeric contradictions.
- Engine remains thin (no full stat engine).

---

## Tests to Add
- State patch updates apply to character stats/skills and run stats/skills.
- Numbers or skill values in UI not found in state trigger repair.
- POV drift detection triggers lint warning.
- Numeric invariant migration occurs in state_repair.

---

## Open Questions
- Should stat/skill keys be normalized (e.g., `crit_rate` vs `critical_hit_rate`)?
- Should “locked” fields block changes unless a reason is provided?
- Do we want optional caps on stat history growth?

