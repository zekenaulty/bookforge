# Python BookForge: Git‑Backed, Hands‑Free Book Generator

## 1) Goal and non‑goals

### Goal

Build a **Python program that can generate an entire book hands‑free** from a single initial prompt.

* THe user provides an initial prompt (premise + constraints).
* The program creates an author persona, outline, character bibles, and then drafts the manuscript scene-by-scene.
* It manages continuity, pacing, and forward progress automatically.
* All artifacts (outline, state, scene cards, prose chunks) are stored as **local JSON + Markdown files** inside a **Git repository** for versioning and review.
* The program supports **multiple LLM providers** (Ollama, Gemini, OpenAI) selected via **.env** configuration.
* The program can **compile** the generated parts into a final **single Markdown manuscript**.

### Non‑goals (for the first prototype)

* No database (SQLite/Postgres) required.
* No UI required.
* No vector embeddings required.
* No sophisticated “agent framework” dependency required.

The first milestone is: **“I can run a command, and the program produces a book folder with a growing manuscript and a final export.”**

---

## 2) Key design idea

### Replace “chat history as memory” with **file-based structured memory**

The program will **not** feed the entire back-and-forth conversation into the model each step.

Instead, the program maintains:

* **Stable instructions** (author style + rules)
* **Structured rolling state** (what is true right now)
* **A thin outline** (what should happen at a high level)
* **Scene cards** (what must happen in the next scene)
* **A short excerpt** (the last chunk of prose to preserve voice/continuity)

This avoids exploding input tokens while still maintaining continuity.

### Self-driving loop = state machine

The program runs a deterministic loop:

1. **PLAN** the next scene (produce a scene card)
2. **WRITE** the scene prose
3. **LINT** for continuity/pacing/invariant violations
4. **REPAIR** if needed
5. **COMMIT** outputs to files
6. **ADVANCE** pointers and repeat

The loop continues until the outline is complete or a stop condition is reached.

---

## 3) Repository and workspace structure

### Project repository structure

The repository contains code + one or more book workspaces.

```
bookforge/
  pyproject.toml
  .env.example
  README.md
  src/bookforge/
    cli.py
    runner.py
    config/
    llm/
    prompt/
    memory/
    phases/
    compile/
    util/
  workspace/
    books/
      <BOOK_ID>/
        book.json
        state.json
        outline/
        canon/
        draft/
        exports/
        logs/
```

### Per-book workspace structure

Each book is a self-contained folder.

```
workspace/books/<BOOK_ID>/
  book.json                 # book metadata + invariant constraints
  state.json                # current cursor (phase/chapter/scene), run status

  prompts/
    system.md               # stable author/system instructions
    templates/              # prompt fragments used by the builder

  outline/
    outline.json            # act/chapter structure + beats
    chapters/
      ch_001.json
      ch_002.json

  canon/
    index.json              # id -> path, tags, size, updated
    characters/
      CHAR_<slug>.json
    locations/
      LOC_<slug>.json
    rules/
      RULE_<slug>.md
    threads/
      THREAD_<slug>.json

  draft/
    context/
      bible.md              # rolling “story so far” memory
      last_excerpt.md       # last prose excerpt used for continuity

    chapters/
      ch_001/
        scene_001.md
        scene_001.meta.json
        scene_002.md
        scene_002.meta.json
      ch_002/
        ...

  exports/
    manuscript.md           # compiled final output

  logs/
    run_<timestamp>.jsonl
```

**All files are plain text** (JSON/MD) so Git can diff and you can inspect everything.

---

## 4) Data model (schemas)

### 4.1 `book.json` — book-level definition

Defines stable information about the book.

* `book_id`, `title`, `genre`, `target_length`
* POV/tense/style constraints
* Non-negotiable invariants (rules that must never be violated)
* High-level completion goals (chapters/acts)

Example:

```json
{
  "book_id": "my_novel_v1",
  "title": "Untitled",
  "genre": ["fantasy"],
  "voice": {
    "pov": "third_limited",
    "tense": "past",
    "style_tags": ["no-recaps", "forward-motion", "tight-prose"]
  },
  "invariants": [
    "No world resets.",
    "No convenient amnesia as a continuity device.",
    "Do not change established names/relationships."
  ],
  "targets": {
    "chapters": 24,
    "avg_scene_words": 1900
  }
}
```

### 4.2 `state.json` — rolling authoritative world state

This is the primary anti-drift artifact.

It contains:

* Where we are: current act/chapter/scene
* Current time/place
* Characters present
* Open plot threads with IDs
* Recent facts (short list)
* Constraints for the next steps

Example:

```json
{
  "status": "RUNNING",
  "cursor": {"chapter": 3, "scene": 2},
  "world": {
    "time": {"day": 12, "hour": 18},
    "location": "LOC_old_bridge",
    "cast_present": ["CHAR_alex", "CHAR_mira"],
    "open_threads": [
      {"id": "THREAD_black_key", "status": "active", "stakes": "high"}
    ],
    "recent_facts": [
      "Alex promised to return the key.",
      "Mira lied about the map."
    ]
  },
  "budgets": {
    "max_new_entities": 1,
    "max_new_threads": 1
  }
}
```

### 4.3 `outline.json` — thin outline

The outline is intentionally compact: one line per beat, not full prose.

* Acts and chapters
* Chapter goals and beats
* Optional “entry/exit state” constraints

### 4.4 Scene card (`scene_XXX.meta.json`) — step-level plan

Each scene has a scene card describing what must happen.

Example:

```json
{
  "scene_id": "SC_003_002",
  "chapter": 3,
  "scene": 2,
  "beat_target": "Mira reveals partial truth",
  "goal": "Force Alex to choose trust vs certainty",
  "conflict": "A witness arrives with contradictory evidence",
  "required_callbacks": ["THREAD_black_key"],
  "constraints": [
    "No new POV.",
    "End with a concrete next action."
  ],
  "end_condition": "Alex decides to follow Mira despite doubt"
}
```

### 4.5 Canon artifacts (by ID)

The canon store contains stable facts the model can retrieve.

* Character cores (identity facts)
* Rules (world mechanics)
* Locations
* Threads

Each artifact is small and versionable.

---

## 5) Provider abstraction (OpenAI, Gemini, Ollama)

### 5.1 Configuration via `.env`

The program reads `.env` to select provider and models.

Example variables:

* `LLM_PROVIDER=openai|gemini|ollama`
* Provider keys/URLs
* `PLANNER_MODEL`, `WRITER_MODEL`, `LINTER_MODEL` (optional)

### 5.2 Unified `LLMClient` interface

Implement a common interface:

* `chat(messages, model, temperature, max_tokens) -> LLMResponse`

Internally each provider adapter handles:

* API differences
* System message support differences
* Retry/backoff
* Rate limit errors

### 5.3 Optional split models

Use different models for different steps:

* Planner: cheaper/faster
* Writer: higher quality
* Linter: strict and short

---

## 6) Prompt architecture (stable prefix + step payload)

### 6.1 Stable “System” instruction document

Create `prompts/system.md` that is stable across all steps.

It contains:

* Author persona
* Style guide rules
* Output contract (formats and constraints)
* Invariant rules

This reduces prompt variance and improves caching opportunities.

### 6.2 Step payload document

For every step, the program composes a payload with:

* Cursor (chapter/scene)
* Outline window (prev/current/next beats)
* Current `state.json`
* Any relevant canon snippets by ID
* The last excerpt (short)
* The task instruction (“create scene card”, “write scene”, “lint”, etc.)

### 6.3 Output contracts (machine-readable)

Every step must produce structured outputs.

Examples:

* PLAN step returns: `scene_card` JSON only
* WRITE step returns: `prose` + `state_patch` JSON + `thread_updates`
* LINT step returns: pass/fail + issues list

The runner rejects outputs that fail schema validation.

---

## 7) Retrieval and memory system (file-based)

### 7.1 ID mapping

Every canon item has an ID (e.g., `CHAR_alex`, `RULE_magic_oath`, `THREAD_black_key`).

`canon/index.json` maps IDs to:

* file path
* tags
* short description
* size

### 7.2 Selection rules

For each scene, the runner chooses what to include:

* characters present
* active threads referenced
* location
* any rules relevant to the beat

It injects only those items into the prompt.

### 7.3 Rolling bible

After each scene, a summarizer step updates `bible.md` (short), containing:

* what changed
* what is now true
* unresolved threads

This is not used as the only memory; it is a navigation aid.

---

## 8) Linting and repair gates (anti-drift and anti-ramble)

### 8.1 Lint rules (automated checks)

The linter enforces:

* No forbidden devices (world reset, convenient amnesia)
* No recap openings
* No contradictions against `state.json` (names, relationships, location)
* Beat completion (scene achieved a target)
* Budget compliance (new entities/threads)

Some checks are regex-based; others are model-based.

### 8.2 Repair loop

If lint fails:

* The program runs a REPAIR prompt that supplies:

  * the lint issues list
  * the scene text
  * the relevant canon and state

It outputs corrected prose and corrected patches.

The program retries repair up to N times then stops.

---

## 9) Orchestrator / runner

### 9.1 Runner responsibilities

* Load config
* Load book workspace
* Determine next phase from `state.json`
* Run the appropriate phase module
* Persist outputs
* Append to logs

### 9.2 Stop conditions

* Outline complete
* Maximum chapters/scenes reached
* Too many consecutive failures
* Budget exhaustion

### 9.3 Logging

Write JSONL logs with:

* step type
* timestamps
* prompt hashes
* token usage (if provided)
* model/provider info
* result status

---

## 10) CLI commands and phases

### `init`

Create a new book workspace with templates and empty state.

### `author generate`

Generate author persona + system.md instructions.

### `outline generate`

Generate `outline.json`.

### `characters generate`

Generate character cores and place in canon.

### `run`

Hands-free loop:

* plan scene
* write scene
* lint
* repair if needed
* commit
* advance

Supports options:

* `--steps N`
* `--until chapter:5`
* `--resume`

### `compile`

Compile all scene markdown files into `exports/manuscript.md`.

### `export synopsis`

Generate synopsis from bible + outline.

---

## 11) Compiler (build final Markdown)

### Inputs

* `draft/chapters/ch_*/scene_*.md`

### Output

* `exports/manuscript.md`

### Compilation logic

* Add chapter headings
* Concatenate scenes in order
* Normalize spacing
* Optional: create table of contents

---

## 12) Implementation plan (fast and incremental)

### Milestone 1: One scene works

* Repo scaffold
* Provider clients
* Prompt builder
* A single WRITE step that produces one scene

### Milestone 2: Outline → scene loop

* Outline generation
* Scene card planning
* Draft multiple scenes

### Milestone 3: State + lint gate

* Rolling state patches
* Lint checks
* Repair loop

### Milestone 4: Canon + retrieval

* Canon index
* Inject relevant canon by ID

### Milestone 5: Compile

* Produce a single manuscript.md

---

## 13) What success looks like

A new developer can:

1. run `init`
2. run `author generate`
3. run `outline generate`
4. run `characters generate`
5. run `run --steps 1000`
6. run `compile`

…and get a complete, readable manuscript with:

* consistent characters
* forward motion
* minimal drift
* artifacts stored in Git


# Input Token Caching, Prompt Templating, and Maintainable Personas

## 1) What we’re optimizing for

### Primary goal

Reduce **repeated input tokens** (the expensive part of long-horizon writing) while keeping:

* strong continuity
* steady forward motion
* consistent voice
* manageable code and prompt assets

### Key constraint

Token “caching” (when available) only helps if the **prefix** of your request is:

* **byte-identical** (same characters, same ordering, same whitespace)
* repeated across calls

So the system must be designed around **stable prompt prefixes** and **small per-step deltas**.

### What “maintainable” means here

A maintainable prompt system:

* is modular (small prompt fragments)
* is versioned (explicit V1/V2)
* is deterministic (no accidental variations)
* is debuggable (you can see exactly what was sent)
* can be evolved without rewriting the whole system

---

## 2) The stable-prefix / dynamic-payload boundary

### Stable prefix (cache target)

This is content that should rarely change and should be identical across most calls.

Typical stable-prefix components:

1. **System persona** (the “Author Engine” personality, general rules)
2. **Book constitution** (genre, themes, hard constraints, rating/tone boundaries)
3. **Output contract** (schemas, allowed formats, required fields)
4. **Safety/quality invariants** (no reboots, no recaps, no name drift, etc.)
5. **Author persona** (the created author profile for this book)

This stable prefix should be assembled once and stored on disk as a single file:

* `prompts/system_v1.md`

That file should not be edited during runs. If you need to change it, you create:

* `prompts/system_v2.md`

### Dynamic payload (changes every step)

This is the “current situation” for the agent:

* current cursor (chapter/scene)
* outline window (prev/current/next)
* rolling structured state
* scene card
* last excerpt
* selected canon snippets relevant to this step

The dynamic payload must be:

* compact
* structured
* deterministic in formatting

---

## 3) Prompt templating approach

### Three layers of prompt templates

Use a small set of templates for distinct actions:

1. **PLAN template**

* Input: outline window + state
* Output: scene card JSON

2. **WRITE template**

* Input: scene card + state + last excerpt
* Output: prose + patch JSON

3. **LINT template**

* Input: prose + state + invariants
* Output: pass/fail + issues list

4. **REPAIR template**

* Input: issues list + last prose + state
* Output: corrected prose + corrected patches

Each template should live as a file:

* `prompts/templates/plan.md`
* `prompts/templates/write.md`
* `prompts/templates/lint.md`
* `prompts/templates/repair.md`

### Deterministic “rendering” rules

To improve caching and reproducibility:

* templates are plain text
* placeholders are substituted in a fixed order
* JSON blocks are serialized with:

  * stable key ordering
  * stable indentation
  * no random fields

Avoid including anything that changes per call in the stable prefix, including:

* timestamps
* run ids
* “Generated at …” lines
* random seeds (unless you always keep them constant)

---

## 4) Making caching actually hit

### Byte identity is everything

Even “small differences” can break prefix caching:

* changing whitespace
* re-wrapping lines
* reordering bullet points
* different JSON key ordering
* injecting a changing summary into the stable prompt

### Practical operational rules

1. **Freeze stable prompts**

* Build `system.md` once per author+book.
* Never regenerate it unless version bumping.

2. **Hash every prompt component**
   Record:

* hash of the stable system prompt
* hash of the dynamic payload
* hash of the final assembled prompt

This makes debugging trivial: you can prove what changed.

3. **Log token estimates and lengths**
   Even without exact provider token counts:

* log characters and rough token estimate
* enforce budgets (e.g., dynamic payload < X tokens)

4. **Canonicalize dynamic payload formatting**
   For example:

* always place sections in the same order
* always label sections with the same header tokens
* always serialize JSON blocks in the same style

---

## 5) Maintainable prompt assets

### Prompt registry

Create a registry file that defines what the system uses:

* `prompt_registry.json`

Example fields:

* prompt version
* template paths
* schema versions
* budgets per phase

This enables controlled evolution:

* `system_v1.md` + templates v1
* then `system_v2.md` + templates v2

### Separating “rules” from “style”

Maintain two distinct prompt sections:

* **Rules (hard constraints)**

  * invariants
  * output contract
  * forbidden devices

* **Style (soft constraints)**

  * voice
  * pacing preferences
  * dialogue density

This makes it easier to adjust voice without breaking core reliability.

---

# Safe Author Creation Without Copyright Problems

## 6) What copyright does and doesn’t cover (practical framing)

### The safe principle

**Style is not copyrightable**, but **specific expression is**.

That means it’s generally okay to:

* take inspiration from authors you like
* describe traits (clear plotting, cinematic action, mythic tone)
* build a new persona that uses those traits

But it’s not okay to:

* reproduce recognizable passages
* replicate unique phrasing patterns so closely that it reads like a rewrite
* lift proprietary names/lines/world details

So the author creator must be designed to:

* translate “I like these authors” into **abstract craft traits**
* require **original output**
* include guardrails that discourage pastiche-by-copy

## 7) “Influence blending” as a trait system, not imitation

### User-facing input

Users will say:

* “I like the style of Author A, Author B, Author C.”

The system should interpret that as:

* “Create a new author persona whose craft traits blend the *high-level* characteristics commonly associated with those influences.”

### Convert authors into craft-trait vectors

Instead of “write like X,” store a neutral trait model:

* prose density: sparse ↔ lush
* pacing: brisk ↔ contemplative
* viewpoint: tight limited ↔ broad omniscient
* dialogue ratio: low ↔ high
* exposition strategy: explicit ↔ implied
* action choreography: minimal ↔ cinematic
* morality tone: bright ↔ grim
* worldbuilding style: hard rules ↔ mythic ambiguity
* humor: dry ↔ none ↔ playful
* sentence rhythm: short punchy ↔ long flowing

Then blend influences by weighted averaging.

### Output of the author creator

The author creator should produce a structured author persona:

* `author.json`
* `author_style.md`

These should contain:

* a named persona (original name)
* a trait profile
* do/don’t lists
* example “micro-guidelines” (not passages)
* banned list (no copying, no unique phrases, no known proprietary names)

## 8) Handling living authors and sensitive imitation

### Practical safety posture

Even if “style” isn’t copyright, **close imitation can create risk**.

So the author creation tool should:

* avoid producing output described as “exactly like [living author]”
* phrase it as:

  * “inspired by”
  * “blending high-level craft traits associated with”
* enforce originality rules

### What the author creator should NOT do

* It should not generate “a chapter written in the voice of X” as a template.
* It should not generate a “fake excerpt from X’s novel.”

### What it CAN do

* Provide **guidelines** for the persona:

  * “prioritize clear cause/effect action chains”
  * “keep magic mechanics explicit and consistent”
  * “emphasize moral choices and oaths”

These are craft patterns, not protected text.

## 9) A safe “influence merging” workflow

### Step 1: Influence intake

User provides:

* influence list (names)
* optional weights (e.g., 50/30/20)
* optional “what I like” notes

### Step 2: Trait inference

The system maps each influence to neutral trait ranges.

Important: This mapping should be treated as a heuristic. It is not a factual claim about the author; it is a convenience model.

### Step 3: Persona synthesis

The system outputs:

* an original persona name
* a trait profile
* a writing contract
* a revision checklist

### Step 4: User refinement (editor-friendly)

Users can:

* edit the trait profile
* add banned tropes
* add target audiences
* adjust pacing and tone

This supports “use external tools to refine/expand.”

## 10) Author persona artifacts (recommended schema)

### `author.json`

* `persona_name`
* `influences` (names + weights)
* `trait_profile`
* `style_rules`
* `taboos`
* `cadence_rules`

### `author_style.md`

A human-readable summary:

* paragraph-based “how this author writes”
* bullet craft rules
* revision checklist

### Example trait profile fields

* `pacing`: 0–100
* `prose_density`: 0–100
* `dialogue_ratio`: 0–100
* `description_focus`: 0–100
* `worldbuilding_explicitness`: 0–100

## 11) Guardrails to avoid accidental plagiarism

### Originality constraints in the system prompt

Include explicit rules:

* “Do not reproduce recognizable phrases.”
* “Do not imitate a specific author’s distinctive language.”
* “Use original metaphors and original sentence constructions.”

### Programmatic checks (lightweight)

For a first prototype:

* enforce “no named proprietary entities” list
* flag repeated unusual phrases across scenes
* detect long repeated sequences within your own manuscript (anti-loop)

If desired later:

* optional similarity checks against your own canon store to prevent self-copy loops

---

# How prompt templating and author personas fit together

## 12) The maintainable integration point

The author creator outputs a persona that becomes part of the **stable system prompt**.

That means:

* changing author persona = creating `system_v2.md`
* not rewriting templates

Templates remain stable; only the persona content changes via version bumps.

## 13) Practical advice for maintainability

1. Keep the persona **short and trait-based**

* avoid long descriptive walls of text

2. Put the persona into the stable prompt

* so it doesn’t get re-sent as dynamic payload

3. Put “current situation” into dynamic payload

* never mix current cursor/state into persona

4. Version everything

* author_v1.json → author_v2.json
* system_v1.md → system_v2.md

5. Keep templates small and phase-specific

* plan/write/lint/repair are separate

---

## 14) Outcome

With this structure:

* The expensive repeated tokens stay stable and cacheable.
* The per-step payload stays small.
* Personas can be created from “influence lists” safely.
* The system remains modular, debuggable, and maintainable.

