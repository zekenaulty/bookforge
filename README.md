# BookForge

BookForge is a Python CLI that generates a full book from a single seed prompt. It is designed for long-horizon writing with tight continuity control, low prompt bloat, and reproducible outputs. Every artifact is stored as plain JSON and Markdown so the process is transparent and Git-friendly.

## What we are building
- A CLI-driven book generator that takes a premise and produces a complete manuscript.
- A file-based memory system (state, outline, canon, scene cards, rolling bible) instead of long chat history.
- A deterministic prompt system with a stable prefix and versioned templates to maximize caching and minimize drift.
- A multi-provider LLM layer (OpenAI, Gemini, Ollama) selected via .env with per-phase models.
- A staged generation loop with strict validation and repair gates.
- Explicit anti-duplication controls to prevent scene-to-scene repetition and recap openings.
- Versioned author personas and per-book pinning so a book never changes retroactively.
- Rerun and override rules that avoid silent overwrites.

## Goals (v1)
- One command sequence creates a book workspace and produces a growing manuscript.
- Continuity and forward motion are enforced through state and scene cards.
- Every step writes artifacts to disk with schema validation.
- Prompting is tunable per phase and can be rerun in isolation.
- A final compile step produces a single manuscript file.

## Non-goals (v1)
- No UI or web console.
- No database or vector store.
- No external agent framework dependency.

## Core pipeline
1) PLAN: produce a scene card from outline + state.
2) OPENING PREVIEW: generate a short opening and check for recap/duplication.
3) WRITE: generate full prose using the approved opening.
4) LINT: check continuity, invariants, and anti-dup rules.
5) REPAIR: rewrite if lint fails.
6) COMMIT: write artifacts and advance state.

## Workspace structure (target)
```
workspace/
  authors/
    <author_slug>/
      v1/
        author.json
        author_style.md
        system_fragment.md
  books/<BOOK_ID>/
    book.json
    state.json
    prompts/
      system_v1.md
      templates/
      registry.json
    outline/
    canon/
    draft/
    exports/
    logs/
```

## Prompt system and caching
- Stable prefix is assembled once per book and kept byte-identical across runs.
- Dynamic payload is deterministic and ordered to maximize cache hits.
- Prompt registry defines templates, budgets, and policies per phase.
- Prompt budgeter enforces token limits with deterministic truncation rules.

## Continuity and anti-duplication
- Continuity pack replaces raw last-scene prose with factual anchors and constraints.
- A style anchor excerpt is reused to preserve voice without copy risk.
- Opening preview gate prevents recap openings and repeated phrasing.
- Banned phrase list is injected from recent scenes.
- Cross-scene similarity checks run before commit.

## Author library
- Author personas are versioned and immutable (v1, v2, ...).
- Each book pins a specific author version.
- Book system prompts are assembled from base rules, book constitution, and the pinned author fragment.

## Rerun and versioning
- Each phase declares its mutation behavior: immutable, append-only, or rewrite-with-archive.
- Outputs are versioned by folder or filename suffix.
- state.json tracks the active versions to keep runs reproducible.

## CLI commands (planned)
- init
- author generate
- outline generate
- characters generate
- run
- compile
- export synopsis

## Configuration (.env)
- LLM_PROVIDER=openai|gemini|ollama
- PLANNER_MODEL, WRITER_MODEL, LINTER_MODEL
- Provider-specific keys and endpoints

## Logging and validation
- JSONL logs with prompt hashes, model info, token estimates, and results.
- Schemas in `schemas/` and enforced for every JSON artifact.
- Invalid outputs are rejected and optionally repaired.

## References
- Concept spec: `resources/initial_concept.md`
- Steelman review: `resources/steel man.md`
- Plan: `resources/plans/bookforge_plan_v2.md`

## Current status
- Phase:
- Active story:
- Next milestone:
- Blockers:
- Notes:
