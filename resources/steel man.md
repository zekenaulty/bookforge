# Steelman Review & Fix Plan

This document strengthens the current BookForge plan by addressing known failure modes (especially **repetition/duplication and “chapter restart” behavior**) and by adding explicit, testable engineering stories for **prompt budgeting**, **author versioning**, **rerun semantics**, and **schema/version governance**.

It assumes the end goal remains: **one seed prompt → hands-free generation of a full book**, with artifacts stored as JSON/Markdown in a Git-friendly workspace.

---

## 0) Why duplication happens in these systems (root causes)

Duplication is rarely “just a model thing.” In long-horizon book generation it usually comes from one or more of the following:

1. **Prompt leakage of prior prose**

   * If the prompt includes large verbatim excerpts of recent prose, the model often begins by paraphrasing or echoing those lines.
   * The risk is highest at the **start of a new chapter/scene**, where the model reflexively “re-orients.”

2. **Recap pressure from the model’s learned distribution**

   * Many writing models learned “chapter openings recap the situation.”
   * If you don’t explicitly counter-program this, you get: “As the sun rose… we remember…”

3. **Ambiguous scene boundaries**

   * If the system doesn’t clearly separate “previous scene ended here” vs “new scene must begin with new action,” the model blends them.

4. **Lack of pre-generation novelty constraints**

   * If you only dedupe after generating (lint/repair), you’re paying for generation, retries, and time.
   * Lint catches too late and will create churn.

5. **State and outline not strict enough**

   * If beats are vague, the model fills space with repetition.
   * If the next beat isn’t concrete, the model rephrases old beats.

6. **Cross-run / rerun overwrites**

   * If rerun semantics are unclear, you can unknowingly regenerate a scene with slight differences and end up with duplicated content across versions.

This review focuses on designing the system so duplication is **unlikely before generation**, not just caught after.

---

## 1) Add a dedicated “Prompt Payload Budgeter” subsystem (missing story)

### 1.1 Why this must be its own subsystem

A prompt system isn’t “templates.” It’s:

* **templates + budgeting rules + excerpt policy + retrieval selection policy**

If budgeting is ad-hoc, the system drifts into:

* too much excerpt → duplication
* too little state → continuity errors
* too much canon → token bloat

So create a first-class module:

* `prompt/budgeter.py`
* `prompt/excerpt_policy.py`
* `prompt/injection_policy.py`

### 1.2 Define explicit budgets per step

Budgets should be defined in a versioned registry (per prompt version):

* stable prefix budget (estimated)
* dynamic payload budget
* excerpt budget
* canon injection budget

Example budgeting concept (not literal numbers):

* PLAN: small, state-heavy, no prose excerpt
* WRITE: medium, scene-card-heavy, minimal prose excerpt
* LINT: small, prose + state
* REPAIR: medium, issues + prose + constraints

### 1.3 Deterministic token estimation

Even if provider doesn’t return token counts reliably:

* implement a rough estimator
* log characters and estimated tokens
* enforce hard cutoffs

Key: token estimator must be deterministic and consistent across runs.

### 1.4 “Budget actions” when payload is too large

When payload exceeds budget, you must have deterministic truncation rules:

Priority order (highest to keep):

1. invariants / hard constraints
2. scene card
3. structured state
4. outline window
5. selected canon (ID snippets)
6. style anchor excerpt
7. last-scene prose excerpt (this should be the FIRST to be reduced)

Rule: **never truncate JSON mid-object**; reduce by dropping optional sections.

---

## 2) Replace “last excerpt” with a safer “continuity pack” to prevent repetition

### 2.1 The big change

Do not feed the model “the last scene” as prose.

Instead feed a **Continuity Pack** composed of:

1. **Scene-end anchor (2–4 sentences)**

   * A minimal summary of exactly how the prior scene ended.
   * NOT prose. It should be factual and compact.

2. **Immediate continuity constraints (bullets)**

   * “Characters present: …”
   * “Location: …”
   * “Open threads touched: …”
   * “Next action implied: …”

3. **Style anchor excerpt (fixed, reused)**

   * A short sample created once (early) that represents desired voice.
   * This is stable across steps, which also helps caching.

4. **Banned phrase list** (see section 3)

This preserves continuity without giving the model text it can copy.

### 2.2 Maintain two different “excerpts”

To avoid duplication while retaining voice:

* **Style Anchor Excerpt** (fixed, reused across many calls)

  * generated once per book (or per author persona)
  * included in stable or semi-stable portion

* **Content Continuity Pack** (facts, not prose)

  * changes per scene

This is one of the best “prevention” moves: you stop handing it copyable prose.

### 2.3 A “cold start opener” rule for every scene

Scene openings are where duplication happens most.

Impose a strict rule in the WRITE template:

* The first paragraph must begin with **new action or new sensory anchor**.
* It must not mention the previous scene except via a single implicit continuation.
* It must not restate character motivations already known.

Also include a required “Scene Starter” instruction:

* “Start in motion; no recap; no summary; no reflection on the previous scene.”

---

## 3) Pre-generation duplication prevention (not just dedupe after)

This is the most important upgrade.

### 3.1 Add a “Two-Stage Write” with a cheap opening gate

Instead of generating the entire scene at once:

**Step A: OPENING_PREVIEW (very small)**

* Ask for only:

  * first 3–6 sentences
  * plus a paragraph outline (3–5 bullets)

Run fast checks on the opening preview:

* self-copy risk
* recap risk
* banned phrases present
* too-similar-to-last-opening

If it fails, regenerate only the opening preview.

Only once the opening passes do you run:

**Step B: FULL_WRITE**

* generate the full scene using the approved opening as a hard start

This prevents wasting a full scene generation on a bad opening.

### 3.2 “Banned phrase list” injection

The runner should automatically extract from the last N scenes:

* common 3-grams / 4-grams
* distinctive phrases (quoted strings, repeated metaphors)
* last scene’s first paragraph phrases

Then pass a list like:

* “Do not use these phrases verbatim: …”

This is a simple and extremely effective guardrail.

Important: keep it short (top 30–80 items), otherwise it becomes noise.

### 3.3 “Novelty constraints” in the prompt

Beyond “don’t recap,” add a positive novelty requirement:

* “The opening paragraph must introduce at least one NEW concrete event or observation not stated in the continuity pack.”
* “Each paragraph must advance a different micro-beat; do not restate prior paragraphs.”

This is preventative because it forces forward motion.

### 3.4 Cross-scene similarity checks (fast and local)

Even with prompt engineering, add lightweight *local* checks before commit.

Recommended simple checks (no heavy deps required):

1. **N-gram overlap ratio**

* build sets of 4-grams from current scene vs last 1–3 scenes
* block commit if overlap exceeds threshold

2. **SimHash / MinHash signature**

* store a signature per scene
* compare Hamming distance
* quick “too similar” gate

3. **Opening similarity check**

* compare the first 200–400 characters of scenes
* block if too close

The point is not “perfect plagiarism detection,” it’s preventing the exact self-copy loop you already experienced.

### 3.5 “Anti-loop sentinel” state

Add a counter in state:

* `duplication_warnings_in_row`

If it triggers repeatedly:

* automatically adjust:

  * lower excerpt size
  * increase strictness of banned phrase list
  * force shorter scenes
  * force a more concrete conflict

This makes the system adaptive without manual intervention.

---

## 4) Make outline and beat enforcement more explicit (prevents rambling)

Duplication often hides inside “rambling.” Tight beats reduce that.

### 4.1 Require every scene to satisfy exactly one beat

Scene card should include:

* one beat target
* one conflict pivot
* one end condition

Lint should fail if the end condition isn’t met.

### 4.2 Enforce “micro-beats per paragraph”

In the WRITE prompt:

* require a brief paragraph plan (not visible in final output)
* each paragraph corresponds to a micro-beat

Then in lint:

* check whether paragraphs are distinct (via keyword overlap / repeated sentences)

This reduces internal repetition within a scene.

### 4.3 Avoid “summary drift” by preferring structured state over prose bible

The “bible.md” should be treated as human-facing.

For machine continuity:

* keep `state.json` authoritative
* optionally keep `bible.json` (facts list) separate from `bible.md`

This prevents the system from inheriting a narrative style of summary and then rewriting it in prose.

---

## 5) Author library semantics and version pinning (cross-book drift risk)

The plan needs explicit rules for how global authors relate to per-book prompts.

### 5.1 Use immutable author versions

When an author persona changes, you create a new version folder:

* `workspace/authors/<author_slug>/v1/`
* `workspace/authors/<author_slug>/v2/`

Each version contains:

* `author.json`
* `author_style.md`
* `system_fragment.md` (persona rules)

### 5.2 Per-book pinning

Each book references a specific author version:

* in `book.json`: `author_ref: authors/<slug>/v2`

When initializing a book:

* copy the author’s `system_fragment.md` into the book’s `prompts/` as a snapshot
* record the version used

This prevents retroactive changes to old books.

### 5.3 Derivation rules: global → book

Define an explicit “system prompt assembly” step:

* `system.md` = base hard constraints + book constitution + author fragment + output contract

Only this assembled file is used at runtime.

---

## 6) Rerun and override semantics (must be explicit)

### 6.1 Every phase must declare its mutation behavior

For each CLI command / phase, define one of:

* **Append-only**: adds new files, never overwrites
* **Rewrite-with-archive**: overwrites but moves old to archive
* **Immutable**: refuses if output exists unless `--force`

### 6.2 Recommended defaults

* `outline generate`: immutable by default; new outline requires `--new-version`
* `characters generate`: rewrite-with-archive per character; new version saved
* `run`: append-only for new scenes; repairs create revisions
* `repair`: rewrite-with-archive on the scene

### 6.3 Versioned output paths

Store versions using folders instead of overwriting:

* `outline/v1/outline.json`

* `outline/v2/outline.json`

* `draft/chapters/ch_003/scene_004_v1.md`

* `draft/chapters/ch_003/scene_004_v2.md`

Then `state.json` points to the active versions.

This eliminates silent corruption and makes Git history clearer.

---

## 7) Schema versioning and validation (make it enforceable)

### 7.1 Store schemas in a dedicated folder

Add:

* `schemas/`

  * `book.schema.json`
  * `state.schema.json`
  * `outline.schema.json`
  * `scene_card.schema.json`

### 7.2 Embed schema versions in artifacts

Every JSON artifact includes:

* `schema_version: "1.0"`

The validator selects the correct schema.

### 7.3 Validation is non-negotiable

If any step output fails schema validation:

* do not commit
* log the failure
* optionally run a REPAIR prompt to regenerate valid JSON

This prevents subtle tool failures from cascading.

---

## 8) Prompt registry details (make it real, not hand-wavy)

### 8.1 Registry file defines:

* prompt version
* template files per step
* budgets per step
* excerpt policies per step
* injection policies per step
* linter strictness level

Example conceptual fields:

* `write.opening_preview.enabled: true`
* `write.continuity_pack.max_chars: 1500`
* `write.banned_phrases.max_items: 60`
* `write.style_anchor.enabled: true`

### 8.2 Registry is immutable during a run

When a run begins:

* snapshot registry into `logs/run_<id>/registry_snapshot.json`

This makes runs reproducible and cache-friendly.

---

## 9) Provider-specific reliability pitfalls (and how to defend)

### 9.1 “System message” differences

Some providers treat “system” differently or require different message formats.

Mitigation:

* build a canonical message structure in your code
* provider adapters transform it internally
* keep stable prefix content identical even if wrapped differently

### 9.2 Rate-limit behavior

Plan for:

* exponential backoff
* “cooldown” that increments `state.json` to pause run
* resuming is safe and deterministic

### 9.3 Model variance across providers

A prompt that works on one model may duplicate on another.

Mitigation:

* keep duplication prevention mostly in:

  * opening preview gate
  * banned phrase list
  * continuity pack
  * cross-scene checks

These are model-agnostic.

---

## 10) Additional hidden risks and fixes

### 10.1 “Canon inflation” and prompt bloat

If canon store grows without curation, prompts explode.

Fix:

* tag canon items with priority and relevance
* inject only those referenced by scene card
* cap total injected canon size

### 10.2 “Thread explosion”

If the system creates new plot threads endlessly, it repeats and loses focus.

Fix:

* cap open threads
* require closing or escalating an existing thread before adding new

### 10.3 “Planner/writer disagreement”

Planner creates a scene card; writer ignores it.

Fix:

* writer must include a short compliance checklist in JSON:

  * `beat_completed: true/false`
  * `end_condition_met: true/false`

Lint fails if false.

### 10.4 “Self-contradiction patches”

State patches can drift and become inconsistent.

Fix:

* only allow state updates through a patch schema
* require linter to validate state transitions

---

## 11) Concrete new stories to add to the backlog

### Story A.R: Refinement — Prompt budgeting + excerpt policy

* Define budgets per step
* Define continuity pack schema
* Define truncation strategy

### Story A: Implement Budgeter + Continuity Pack

* budgeter.py
* excerpt_policy.py
* injection_policy.py
* tests for determinism

### Story B.R: Refinement — Pre-generation duplication prevention

* Define opening preview gate
* Define banned phrase extraction
* Define overlap thresholds

### Story B: Implement Opening Preview + Banned Phrases

* write_opening_preview step
* fast local checks
* regenerate opening if needed

### Story C.R: Refinement — Cross-scene anti-self-copy gate

* Decide thresholds
* Decide which scenes to compare against

### Story C: Implement n-gram overlap + signature checks

* compute per-scene signatures
* block commit if similarity too high

### Story D.R: Refinement — Author library version semantics

* define immutable versions
* define per-book pinning

### Story D: Implement author versioning + snapshotting

### Story E.R: Refinement — Rerun/override semantics

* define immutable/append/rewrite-with-archive policies per phase

### Story E: Implement explicit rerun policy + archives

---

## 12) Summary: what changes most improve reliability

If you do only five upgrades, do these:

1. Replace “last excerpt” with a **Continuity Pack** (facts, not prose).
2. Add **Opening Preview** gating before full write.
3. Add **Banned Phrase List** injection from recent scenes.
4. Add **cross-scene n-gram overlap** block before commit.
5. Make author personas **versioned and pinned per book**.

These changes directly attack the repetition loop before it happens, rather than after you’ve paid for a full generation.
