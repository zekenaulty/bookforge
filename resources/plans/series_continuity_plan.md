# BookForge Series Continuity & Serial Outlining Plan (Draft)

## Purpose
Establish series-aware outlining and cross-book continuity in BookForge without overhauling the pipeline. This plan focuses on:
- Series-level state and continuity artifacts.
- Outliner awareness of serial publication (manga/novella/episodic).
- Clear rollup points at chapter/book boundaries.
- Minimal, enforceable schema/prompt changes with deterministic behavior.

## Scope (In)
- Series-aware outline inputs and outputs.
- Series-level continuity pack and summary artifacts.
- Series character state rollups at book boundaries.
- Prompt + schema updates to support serial awareness.
- New rollup/update steps in book completion flow.

## Scope (Out)
- Full redesign of generation pipeline.
- Thought-signature caching.
- Multi-turn agent architecture.

---

## Phase 0: Discovery & Alignment
### Goals
- Confirm how series_id / series_ref is already stored and used.
- Confirm current series folder layout and artifacts.

### Checklist
- Identify existing series root: `workspace/series/<series_id>/...`.
- Enumerate canonical series artifacts (characters, canon index, series.json).
- Confirm current outline prompt structure and schema version.

### Definition of Done
- We can point to the exact existing series root and artifacts.
- We agree on the exact serial data to inject into the outliner.

---

## Phase 1: Series Metadata & Outline Inputs
### 1.1 Series Brief Artifact
Introduce a series-level brief file used by outlining and writing:
- Path: `workspace/series/<series_id>/series.json`
- Fields (minimum):
  - `series_id`
  - `title`
  - `premise`
  - `tone`
  - `arc_goals` (array)
  - `open_threads` (array)
  - `invariants` (array)

### 1.2 Series Summary Artifact
Introduce a series summary file updated after each book:
- Path: `workspace/series/<series_id>/series_summary.json`
- Fields:
  - `schema_version`
  - `book_summaries` (array of book summaries)
  - `story_so_far` (array of bullets, capped)
  - `must_stay_true` (array of invariants, capped)

### 1.3 Outliner Prompt Injection
Add a series context block to the outline prompt, including:
- Series brief
- Series summary (story_so_far + must_stay_true)
- Serial mode flag

#### Serial Mode Rules (system/prompt level)
- “This is Book N in an ongoing series.”
- “Do not resolve all series arcs.”
- “Preserve open threads unless explicitly closed in this book.”
- “Avoid finality phrasing unless marked as a series milestone.”

### Definition of Done
- Outline prompt includes a clear series context block.
- Serial-mode instructions appear in the outline prompt.

---

## Phase 2: Outline Schema Extensions
### 2.1 Series-Aware Outline Fields (Top-Level)
Add optional fields to outline schema:
- `series_context` (object)
  - `serial_mode` (bool)
  - `book_number` (int)
  - `series_id` (string)

### 2.2 Book Handoff Metadata
Add a top-level or end-of-outline block:
- `handoff` (object)
  - `open_threads` (array)
  - `carry_over_facts` (array)
  - `cliffhangers` (array)
  - `next_book_setup` (array)

### 2.3 Series Milestones
Add optional array:
- `series_milestones` (array of objects)
  - `milestone_id`
  - `status` (NOT_YET / DONE / PARTIAL)
  - `notes`

### Definition of Done
- Outline schema updated with optional series context and handoff.
- Outliner prompt instructs to populate handoff + milestones.

---

## Phase 3: Series Continuity Pack (Cross-Book)
### 3.1 New Artifact
Add a series continuity pack stored under series:
- Path: `workspace/series/<series_id>/continuity_pack.json`
- Contents:
  - `story_so_far` (series-level, bullets)
  - `must_stay_true` (series invariants)
  - `open_threads`
  - `character_status` (key facts about major cast)
  - `artifacts` (key items/ownership)

### 3.2 Injection into Writing/Planning
- Writer and planner prompts receive:
  - current book continuity pack
  - series continuity pack (facts-only)
- Include only relevant characters (cast-present filter).

### Definition of Done
- Series continuity pack exists and can be loaded.
- Writer/planner prompts include a series continuity block.

---

## Phase 4: Series Character State Rollups
### 4.1 Series Character State
- Introduce a per-series character state folder:
  - `workspace/series/<series_id>/canon/characters/<slug>/state.json`
- This represents the canonical “current” state across books.

### 4.2 Book Start Initialization
When a new book starts:
- Per-book character state is seeded from series state.
- If no series state exists, seed from character canon.

### 4.3 Book End Rollup
At end of book:
- Merge per-book character state changes into series state.
- Store a book-specific character delta history.

### Definition of Done
- Per-book characters are initialized from series state.
- End-of-book updates write back to series state.

---

## Phase 5: Book-End Rollup & Continuity Updates
### 5.1 Book Summary Rollup
On book completion:
- Create `workspace/books/<book>/draft/context/book_summary.json`
  - `summary` (bullets)
  - `key_events`
  - `must_stay_true`
  - `open_threads`

### 5.2 Series Summary Update
- Append book summary to series_summary.
- Merge must_stay_true into series-level invariants (dedup/cap).

### 5.3 Series Continuity Update
- Update series continuity pack from:
  - book_summary
  - book character deltas
  - unresolved threads

### Definition of Done
- End of book produces rollup artifacts.
- Series summary/continuity updated deterministically.

---

## Phase 6: Validation & Linting (Series-Aware)
### 6.1 Timeline/Series Invariant Checks
Add basic checks:
- If series must_stay_true says “artifact X exists,” disallow disappearance.
- If series says “character dead,” disallow reappearance.

### 6.2 Outline Consistency Check
- Outliner must not close series threads unless explicitly allowed.
- Handoff block must list unresolved threads.

### Definition of Done
- Lint warns on series invariant violations.
- Outline validation includes optional handoff/milestone checks.

---

## Phase 7: CLI & Help Updates
### Commands
- `bookforge series init` (optional, if not existing)
- `bookforge series rollup --book <id>` (book-end rollup)
- `bookforge series update-continuity --book <id>`

### Docs
- Add `docs/help/series_init.md`, `series_rollup.md`, `series_continuity.md`.

### Definition of Done
- Help docs list new commands with examples.

---

## Test Plan
### Unit Tests
- Outline schema accepts series context + handoff.
- Series summary update merges caps/dedup.
- Character state rollup merges invariants.

### Integration Tests
- Init two books in same series:
  - Book 1 outline generates handoff.
  - End-of-book rollup writes series continuity.
  - Book 2 outline reads series continuity.

---

## Definition of Done (Overall)
- Outliner receives series context and outputs handoff metadata.
- Series continuity pack + summary updated at book end.
- Writer/planner receives series continuity pack.
- Character states persist across books.
- Lint flags series invariant violations.

---

## Open Questions
- Should series continuity be injected as system-level or user prompt? (Recommend user prompt.)
- Should series rollup be manual (command) or automatic at book completion? (Recommend automatic with opt-out.)
- Caps for series summaries (default suggestion: 40–60 bullets).

