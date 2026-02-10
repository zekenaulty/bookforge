# BookForge Implementation Plan v1

Objective
- Build a Python CLI that generates a full book from a single prompt using file-based memory, multi-provider LLMs, and a deterministic prompt system designed for token caching.
- Store all artifacts as plain JSON and Markdown in a Git-friendly workspace.
- Ensure each generation stage is tunable, isolated, and rerunnable without redoing the whole pipeline.

Definition of Done
- CLI supports: init, author generate, outline generate, characters generate, run, compile, export synopsis.
- LLM provider is selected from .env (openai, gemini, ollama) with per-phase models.
- Workspace layout matches resources/initial_concept.md with book.json, state.json, outline, canon, draft, exports, logs.
- Author creation uses the active LLM and stores reusable author artifacts in a global author library.
- Prompt system uses a stable system prompt file and per-stage templates; dynamic payload is deterministic and size-bounded.
- Plan/write/lint/repair loop runs end-to-end with state patches, scene cards, and last excerpt management.
- Duplication and recap checks prevent previous scene content from bleeding into later scenes.
- Logs capture step type, prompt hashes, model info, and token estimates.
- Tests cover schema validation, prompt rendering determinism, duplication detection, and compile ordering.
- Docs explain setup, prompts, rerun controls, and the phase pipeline.

Scope
- Python project scaffolding and CLI.
- LLM provider abstraction and .env config.
- Prompt templates, registry, and stable prefix caching.
- Author creation and global author library.
- Workspace init, outline generation, scene planning, writing loop, lint/repair.
- Canon store, retrieval, and rolling bible updates.
- Compiler and export commands.
- Logging, metrics, tests, and documentation.

Out of Scope
- UI or web console.
- Database, vector store, or agent framework dependencies.
- Full plagiarism detection beyond lightweight self-dup checks.

Assumptions / Reuse
- Use resources/reference/iterate-book.py as a workflow reference, but avoid its duplication issues by limiting prior prose in prompts and enforcing strict anti-repeat linting.
- Use resources/reference/authors as examples for author persona content and tone.
- Follow the plan structure pattern in resources/reference/dod_domains_workflows_v2.md.

Current Code Anchors (reviewed)
- resources/initial_concept.md
- resources/reference/iterate-book.py
- resources/reference/authors/Eldrik Vale.md
- resources/reference/dod_domains_workflows_v2.md

Proposed Project Layout (target)
- pyproject.toml, .env.example, README.md
- src/bookforge/
  - cli.py, runner.py
  - config/, llm/, prompt/, memory/, phases/, compile/, util/
- workspace/
  - authors/
    - author_<slug>/
      - author.json
      - author_style.md
      - system_v1.md
  - books/<BOOK_ID>/
    - book.json, state.json
    - prompts/system_v1.md, prompts/templates/
    - outline/, canon/, draft/, exports/, logs/

Prompt and Memory Principles
- Stable prefix lives in a versioned system file and never changes mid-run.
- Dynamic payload is deterministic and ordered to maximize cache hits.
- Templates are per-stage files (plan, write, lint, repair) and can be edited and rerun independently.
- Prompt registry defines versions, templates, and budgets for each phase.
- Only the last excerpt and selected canon are included to prevent prompt bloat.

Refinement Workflow
- Each refinement story is handled by back-and-forth between user and agent.
- Refinement outcomes are recorded as acceptance criteria and prompt/template decisions before implementation starts.

Story Map (Backlog)

Story 1.R: Refinement - Requirements baseline and architecture handshake
Tasks
- Confirm CLI commands, workspace layout, and config keys.
- Confirm prompt versioning strategy and stable prefix contents.
- Confirm global author library location and schema.
Definition of Done
- User approves the baseline architecture, backlog order, and acceptance criteria.

Story 1: Repo scaffolding and core package layout
Tasks
- Create pyproject.toml, src/bookforge package layout, and cli entrypoint.
- Add .env.example with provider and model keys.
- Add minimal README with command list and setup.
Definition of Done
- CLI entrypoint runs and package layout matches the target structure.

Story 2.R: Refinement - LLM provider abstraction
Tasks
- Confirm provider list, required env keys, and model selection rules.
- Define LLMClient interface and retry/backoff expectations.
Definition of Done
- Provider interface and config keys are approved.

Story 2: LLM provider layer
Tasks
- Implement provider adapters for openai, gemini, and ollama.
- Implement unified LLMClient interface and response normalization.
- Add unit tests for provider selection and config validation.
Definition of Done
- Provider is selected via .env and basic calls work for each adapter.

Story 3.R: Refinement - Prompt system and caching rules
Tasks
- Define stable prefix components and dynamic payload schema.
- Define prompt registry schema and template file layout.
- Define deterministic JSON serialization rules and hash logging fields.
Definition of Done
- Prompt boundaries, registry schema, and hashing requirements are approved.

Story 3: Prompt templates and registry implementation
Tasks
- Implement prompt registry loader and template renderer.
- Implement deterministic JSON serialization and prompt hashing.
- Add system_v1.md creation and template files for plan/write/lint/repair.
Definition of Done
- Prompts assemble deterministically and are versioned by file.

Story 4.R: Refinement - Author library and generation UX
Tasks
- Define author.json and author_style.md schemas and storage location.
- Define influence intake rules and guardrails against imitation.
- Define author generation prompt template.
Definition of Done
- Author schema and generation rules are approved.

Story 4: Author creation pipeline
Tasks
- Implement author generate command using active LLM provider.
- Store author artifacts in workspace/authors and register in an index.
- Add validation for author.json and author_style.md.
Definition of Done
- New authors can be created, validated, and reused across books.

Story 5.R: Refinement - Workspace init and book schema
Tasks
- Define book.json and state.json schemas and defaults.
- Confirm prompt templates and registry placement per book.
- Define init command inputs (book id, author, genre, targets).
Definition of Done
- Workspace schema and init inputs are approved.

Story 5: Workspace init command
Tasks
- Implement init to scaffold the per-book folder structure.
- Create book.json, state.json, prompts/system_v1.md, and templates.
- Add idempotent behavior and clear errors on conflicts.
Definition of Done
- init creates a valid workspace matching the concept spec.

Story 6.R: Refinement - Outline and scene card schemas
Tasks
- Define outline.json schema and chapter/beat fields.
- Define scene card schema and output contract for plan step.
- Define how outline window and state are included in payload.
Definition of Done
- Outline and scene card schemas are approved.

Story 6: Outline generation and scene planning
Tasks
- Implement outline generate command and outline.json creation.
- Implement plan step to produce scene cards and scene meta files.
- Update state.json cursor and pointers after planning.
Definition of Done
- Outline and scene cards are generated and stored per book.

Story 7.R: Refinement - Writing loop and state patches
Tasks
- Define state patch schema and update rules.
- Define excerpt length and rolling bible update format.
- Define resume rules and stop conditions.
Definition of Done
- State update rules and resume behavior are approved.

Story 7: Writing loop implementation
Tasks
- Implement run loop: plan -> write -> commit -> advance.
- Write scene markdown and scene meta.json with state patches.
- Update last_excerpt and rolling bible after each scene.
Definition of Done
- run produces scenes with updated state and resumes safely.

Story 8.R: Refinement - Lint, repair, and anti-dup rules
Tasks
- Define lint rules for continuity, invariants, and no-recap policy.
- Define duplication detection thresholds and failure handling.
- Define repair template behavior and retry limits.
Definition of Done
- Lint and anti-dup rule list is approved.

Story 8: Lint and repair implementation
Tasks
- Implement lint checks (regex, state consistency, duplication).
- Implement repair loop that rewrites prose and patches.
- Block commits when lint fails after retries.
Definition of Done
- Lint prevents duplicate content and enforces invariants.

Story 9.R: Refinement - Canon store and retrieval rules
Tasks
- Define canon item schemas and index.json format.
- Define selection rules for injecting canon into prompts.
- Define update rules for canon changes after scenes.
Definition of Done
- Canon schema and retrieval rules are approved.

Story 9: Canon store and retrieval
Tasks
- Implement canon index and retrieval by ID.
- Inject relevant canon into plan/write/lint steps only.
- Update canon and bible after scenes where needed.
Definition of Done
- Canon is stored, retrieved, and kept in sync with state.

Story 10.R: Refinement - Compile and export
Tasks
- Define manuscript assembly rules and scene ordering.
- Define synopsis export format and input sources.
Definition of Done
- Compile and export specs are approved.

Story 10: Compile and export implementation
Tasks
- Implement compile command for exports/manuscript.md.
- Implement export synopsis command using outline + bible.
Definition of Done
- Exports are generated with correct ordering and headings.

Story 11.R: Refinement - CLI orchestration and rerun controls
Tasks
- Define CLI options for rerun, resume, and version bumping.
- Define how per-phase reruns avoid overwriting unless requested.
Definition of Done
- CLI behavior for rerun and resume is approved.

Story 11: CLI commands and rerun controls
Tasks
- Implement subcommands and shared options.
- Add flags to rerun individual phases or extend runs.
- Ensure outputs are isolated by versioned prompts where needed.
Definition of Done
- CLI supports isolated reruns without corrupting prior output.

Story 12.R: Refinement - Observability and prompt hashing
Tasks
- Define JSONL log schema and required fields.
- Define token estimate method and budget tracking.
Definition of Done
- Logging schema and prompt hash requirements are approved.

Story 12: Logging and metrics
Tasks
- Implement JSONL logs per step with prompt hashes and metrics.
- Track dynamic payload size and token estimates.
Definition of Done
- Logs provide traceability for prompt changes and outputs.

Story 13.R: Refinement - Tests and documentation
Tasks
- Define test matrix and required doc topics.
- Define baseline examples for README and prompts.
Definition of Done
- Test plan and doc outline are approved.

Story 13: Tests and documentation
Tasks
- Add tests for schema validation, determinism, and lint rules.
- Document setup, CLI usage, prompt tuning, and rerun flows.
Definition of Done
- Tests pass and docs cover the full workflow.

Deliverables
- Python CLI and modular package structure.
- Workspace init and generation pipeline with stored artifacts.
- Prompt system with stable prefixes, templates, and registry.
- Author library and generation tools.
- Lint/repair and anti-dup safeguards.
- Compiler, logs, tests, and docs.

Data / API / CLI Changes
- Data: JSON/MD files under workspace/authors and workspace/books.
- API: No public API; internal LLM adapter interface only.
- CLI: New subcommands and flags as defined in the story map.

Migration / Rollout Order
1) Scaffolding and provider layer
2) Prompt system and author library
3) Workspace init and outline planning
4) Writing loop with state updates
5) Lint/repair and anti-dup guards
6) Canon retrieval and bible updates
7) Compiler and exports
8) Logs, tests, and docs

Testing / Verification
- Unit tests for schemas, prompt assembly determinism, and lint rules.
- Integration test for a short run that produces outline, one scene, and compile output.
- Manual verification that reruns do not duplicate or overwrite without flags.

Risks / Rollback
- Risk: Duplication still leaks through prompts. Mitigation: strict lint and smaller excerpts.
- Risk: Prompt drift due to edits. Mitigation: versioned system prompt and registry.
- Rollback: disable a phase, restore previous prompt version, or revert workspace artifacts via Git.

Worklog Protocol
- Create step notes under resources/plans/steps_YYYYMMDD_HHMM_<slug>.md.
- Each note includes Goal, Context, Commands, Files, Tests, Issues, Decision, Completion, Next Actions.

Checklist
- [ ] Story 1.R: Requirements baseline and architecture handshake
- [ ] Story 1: Repo scaffolding and core package layout
- [ ] Story 2.R: LLM provider abstraction refinement
- [ ] Story 2: LLM provider layer
- [ ] Story 3.R: Prompt system and caching refinement
- [ ] Story 3: Prompt templates and registry implementation
- [ ] Story 4.R: Author library and generation refinement
- [ ] Story 4: Author creation pipeline
- [ ] Story 5.R: Workspace init and book schema refinement
- [ ] Story 5: Workspace init command
- [ ] Story 6.R: Outline and scene card schema refinement
- [ ] Story 6: Outline generation and scene planning
- [ ] Story 7.R: Writing loop and state patch refinement
- [ ] Story 7: Writing loop implementation
- [ ] Story 8.R: Lint, repair, and anti-dup refinement
- [ ] Story 8: Lint and repair implementation
- [ ] Story 9.R: Canon store and retrieval refinement
- [ ] Story 9: Canon store and retrieval
- [ ] Story 10.R: Compile and export refinement
- [ ] Story 10: Compile and export implementation
- [ ] Story 11.R: CLI orchestration and rerun controls refinement
- [ ] Story 11: CLI commands and rerun controls
- [ ] Story 12.R: Observability and prompt hashing refinement
- [ ] Story 12: Logging and metrics
- [ ] Story 13.R: Tests and documentation refinement
- [ ] Story 13: Tests and documentation
