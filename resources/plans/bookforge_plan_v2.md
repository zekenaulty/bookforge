# BookForge Implementation Plan v2

Objective
- Build a Python CLI that generates a full book from a single prompt using file-based memory, multi-provider LLMs, and a deterministic prompt system designed for token caching.
- Store all artifacts as plain JSON and Markdown in a Git-friendly workspace.
- Ensure each generation stage is tunable, isolated, versioned, and rerunnable without redoing the whole pipeline.
- Prevent repetition by design with budgeted prompts, continuity packs, opening preview gates, and cross-scene similarity checks.

Definition of Done
- CLI supports: init, author generate, outline generate, characters generate, run, compile, export synopsis.
- LLM provider is selected from .env (openai, gemini, ollama) with per-phase models.
- Workspace layout matches resources/initial_concept.md with book.json, state.json, outline, canon, draft, exports, logs.
- Series-level canon namespace exists for every book; book.json always includes series_id and series_ref (default series_id=book_id) and series/<series_id>/canon scaffolding is created.
- Author creation uses the active LLM and stores reusable author artifacts in a versioned global author library; books pin author versions.
- Prompt system uses a stable system prompt file and per-stage templates; dynamic payload is deterministic, ordered, and size-bounded.
- Prompt budgeter enforces per-step budgets and deterministic size reporting; over-budget payloads are allowed and logged.
- Continuity pack replaces raw last-scene prose and includes scene-end anchor, constraints, and a style anchor excerpt.
- Two-stage writing uses an opening preview gate before full scene generation.
- Duplication prevention includes banned phrase injection, n-gram overlap checks, and opening similarity checks before commit.
- Plan/write/lint/repair loop runs end-to-end with state patches, scene cards, and strict schema validation.
- Rerun semantics are explicit per phase (immutable, append-only, rewrite-with-archive) with versioned outputs.
- Scope resolution is explicit for every command and falls back to current_book.json only when allowed.
- docs/help contains verbose, accurate per-command help with examples and is updated with each CLI change.
- Logs capture step type, prompt hashes, model info, token estimates, registry snapshot, and budget outcomes.
- Tests cover schema validation, prompt determinism, budgeter behavior, duplication detection, and compile ordering.
- Word/page count targets are enforced per scene with configurable words-per-page rules.
- Docs explain setup, prompts, rerun controls, and the phase pipeline.

Scope
- Python project scaffolding and CLI.
- LLM provider abstraction and .env config.
- Prompt templates, registry, stable prefix caching, and prompt budgeting.
- Author creation and versioned global author library.
- Workspace init, outline generation, scene planning, writing loop, lint/repair.
- Canon store, retrieval, and rolling bible updates.
- Compiler and export commands.
- Logging, metrics, tests, and documentation.
- Series-level canon scaffolding (series/<SERIES_ID>/canon) for shared characters/locations/rules/threads.

Out of Scope
- UI or web console.
- Database, vector store, or agent framework dependencies.
- Full plagiarism detection beyond lightweight self-dup checks.
- Cross-book continuity engine (future).

Assumptions / Reuse
- Use resources/reference/iterate-book.py as a workflow reference, but avoid its duplication issues by limiting prior prose and enforcing anti-repeat gates.
- Use resources/reference/authors as examples for author persona content and tone.
- Follow the plan structure pattern in resources/reference/dod_domains_workflows_v2.md.
- Apply the duplication prevention strategy and prompt budgeting guidance in resources/steel man.md.
- Design for future cross-book continuity with series_id hooks and shared canon namespace; v1 seeds series-level canon folders but does not reconcile across books.

Current Code Anchors (reviewed)
- resources/initial_concept.md
- resources/reference/iterate-book.py
- resources/reference/authors/Eldrik Vale.md
- resources/reference/dod_domains_workflows_v2.md
- resources/steel man.md

Proposed Project Layout (target)
- pyproject.toml, .env.example, README.md
- docs/
  - help/
- schemas/
  - book.schema.json, state.schema.json, outline.schema.json, scene_card.schema.json
- src/bookforge/
  - cli.py, runner.py
  - config/, llm/, prompt/, memory/, phases/, compile/, util/
  - prompt/budgeter.py, prompt/excerpt_policy.py, prompt/injection_policy.py
- workspace/
  - current_book.json
  - authors/
    - <author_slug>/
      - v1/
        - author.json
        - author_style.md
        - system_fragment.md
  - books/<BOOK_ID>/
    - book.json, state.json
    - prompts/system_v1.md, prompts/templates/, prompts/registry.json
    - outline/, canon/, draft/, exports/, logs/

Prompt and Memory Principles
- Stable prefix lives in a versioned system file and never changes mid-run.
- Dynamic payload is deterministic and ordered to maximize cache hits.
- Templates are per-stage files (plan, write, lint, repair) and can be edited and rerun independently.
- Prompt registry defines versions, templates, budgets, and policy knobs for each phase.
- Continuity pack replaces last-scene prose and includes only compact facts and constraints.
- Style anchor excerpt is generated once per book and reused to maintain voice without copying prior prose.
- state.json is authoritative; continuity pack is derived per scene from state and recent outputs and never overrides state.

Duplication Prevention Controls
- Two-stage write: opening preview gate before full scene generation.
- Opening preview is wrapped in explicit tags so it can be stripped before compile.
- Opening preview content is excluded from word/page count thresholds.
- Banned phrase list from recent scenes injected into write prompts.
- Cross-scene similarity checks (n-gram overlap, opening similarity) before commit.
- Anti-loop sentinel in state.json to tighten constraints after repeated duplication warnings.
- Scene cards enforce one scene target, one conflict pivot, one end condition.

Prompt Budgeting and Injection Policy
- Budgets per phase: stable prefix, dynamic payload, canon injection, continuity pack.
- Deterministic token estimation and logging for every step.
- No truncation by default; over-budget payloads are logged and flagged for adjustment.
- Over-budget payloads are allowed; budgets are used for reporting and future tuning.

Author Library Versioning
- Author personas are immutable per version (v1, v2, ...).
- book.json pins the author reference used for the book.
- system_v1.md is assembled from base constraints, book constitution, and the pinned author fragment.
- Updates to an author create a new version, never edit older versions.

Word and Page Count Policy
- Define words_per_page and chars_per_page in config.
- Exclude opening preview blocks from page/word counting.
- Define per-scene min/max targets and a tolerance band.
- Enforce thresholds during lint with explicit failure reasons.
Rerun and Override Semantics
- Each phase declares mutation behavior: immutable, append-only, rewrite-with-archive.
- Versioned outputs are stored under v1, v2 directories or filename suffixes.
- state.json tracks active versions for outline and scenes.
- CLI flags define rerun behavior (resume, rerun phase, new version).

Scope Resolution and Help Docs
- Book-scoped commands require --book or a valid workspace/current_book.json; --book always wins.
- Author generation requires explicit author name/slug and influence inputs or a prompt file.
- Commands that need a seed prompt require --prompt or --prompt-file (no implicit defaults).
- docs/help contains one Markdown file per command plus an index; examples must match the CLI.
- Help docs include full examples with and without optional parameters for every command.

Schema Versioning and Validation
- All JSON artifacts include schema_version.
- Schemas live in schemas/ and are used for validation at every step.
- Invalid outputs are rejected and logged; repair can be invoked for LLM outputs.

Prompt Registry Details
- registry.json declares prompt version, templates, budgets, and policy toggles.
- registry snapshots are stored per run in logs/run_<id>/registry_snapshot.json.
- Stable prefix, dynamic payload, and final prompt hashes are logged for traceability.

Refinement Workflow
- Each refinement story is handled by back-and-forth between user and agent.
- Refinement outcomes are recorded as acceptance criteria and prompt/template decisions before implementation starts.

Story Map (Backlog)

Story 1.R: Refinement - Requirements baseline and architecture handshake
Tasks
- Confirm CLI commands, workspace layout, and config keys.
- Confirm prompt versioning strategy and stable prefix contents.
- Confirm global author library location and schema.
- Confirm scope resolution rules and current_book.json location/fields.
- Confirm docs/help structure and update policy.
Definition of Done
- User approves the baseline architecture, backlog order, and acceptance criteria.

Story 1: Repo scaffolding and core package layout
Tasks
- Create pyproject.toml, src/bookforge package layout, and cli entrypoint.
- Add .env.example with provider and model keys.
- Add minimal README with command list and setup.
- Add docs/help/index.md and per-command help doc stubs.
Definition of Done
- CLI entrypoint runs and package layout matches the target structure.

Story 2.R: Refinement - LLM provider abstraction
Tasks
- Confirm provider list, required env keys, and model selection rules.
- Define LLMClient interface and retry/backoff expectations.
- Define config fields for per-task provider/model overrides (reserved for future use).
Definition of Done
- Provider interface and config keys are approved.

Story 2: LLM provider layer
Tasks
- Implement provider adapters for openai, gemini, and ollama.
- Implement unified LLMClient interface and response normalization.
- Add unit tests for provider selection and config validation.
Definition of Done
- Provider is selected via .env and basic calls work for each adapter.

Story 3.R: Refinement - Schema governance and validation
Tasks
- Define schemas for book.json, state.json, outline.json, scene card, and patches.
- Define schema_version strategy and validation rules per phase.
Definition of Done
- Schema set and validation rules are approved.

Story 3: Schema versioning and validation implementation
Tasks
- Add schemas/ files and validation helpers.
- Enforce schema validation on all read/write paths.
- Add tests for schema validation failures and recovery.
Definition of Done
- Schema validation blocks invalid outputs and reports errors clearly.

Story 4.R: Refinement - Prompt system and caching rules
Tasks
- Define stable prefix components and dynamic payload schema.
- Define prompt registry schema and template file layout.
- Define deterministic JSON serialization rules and hash logging fields.
Definition of Done
- Prompt boundaries, registry schema, and hashing requirements are approved.

Story 4: Prompt templates and registry implementation
Tasks
- Implement prompt registry loader and template renderer.
- Implement deterministic JSON serialization and prompt hashing.
- Add system_v1.md creation and template files for plan/write/lint/repair.
Definition of Done
- Prompts assemble deterministically and are versioned by file.

Story 5.R: Refinement - Prompt budgeter and continuity pack
Tasks
- Define per-step budgets and over-budget reporting rules.
- Define continuity pack schema and style anchor behavior.
- Confirm continuity pack is generated by the LLM and stored as a first-class artifact.
- Define deterministic token estimation method.
- Define over-budget handling (log-only, no truncation).
Definition of Done
- Budgeting rules and continuity pack spec are approved.

Story 5: Budgeter and continuity pack implementation
Tasks
- Implement budgeter.py, excerpt_policy.py, injection_policy.py.
- Add continuity pack builder and style anchor storage.
- Add tests for deterministic budgeting and over-budget logging behavior.
Definition of Done
- Budgeter reports budgets and continuity pack replaces raw prose excerpts.

Story 6.R: Refinement - Author library versioning and generation UX
Tasks
- Define author.json and author_style.md schemas and storage location.
- Define immutable author version rules and per-book pinning.
- Define influence intake rules and guardrails against imitation.
Definition of Done
- Author schema, versioning, and generation rules are approved.

Story 6: Author creation pipeline
Tasks
- Implement author generate command using active LLM provider.
- Store versioned author artifacts and register in an index.
- Assemble system_v1.md from pinned author fragment and base constraints.
Definition of Done
- New authors can be created, versioned, and reused across books.

Story 7.R: Refinement - Workspace init and book schema
Tasks
- Define book.json and state.json defaults and required fields.
- Ensure series_id and series_ref are always present; default series_id to book_id and seed series workspace.
- Confirm prompt templates and registry placement per book.
- Define init command inputs (book id, author ref, genre, targets).
Definition of Done
- Workspace schema and init inputs are approved.

Story 7: Workspace init command
Tasks
- Implement init to scaffold the per-book folder structure.
- Create book.json, state.json, prompts/system_v1.md, and templates.
- Add idempotent behavior and clear errors on conflicts.
Definition of Done
- init creates a valid workspace matching the concept spec.

Story 8.R: Refinement - Outline and scene card schemas
Tasks
- Define outline.json schema and chapter/section/scene fields.
- Define scene card schema and output contract for plan step.
- Define how outline window and state are included in payload.
Definition of Done
- Outline and scene card schemas are approved.

Story 8: Outline generation and scene planning
Tasks
- Implement outline generate command and outline.json creation.
- Implement plan step to produce scene cards and scene meta files.
- Update state.json cursor and pointers after planning.
Definition of Done
- Outline and scene cards are generated and stored per book.

Story 9.R: Refinement - Writing loop and state patches
Tasks
- Define state patch schema and update rules.
- Define word/page count targets and thresholds per scene.
- Define resume rules, stop conditions, and thread caps.
- Define compliance checklist fields for writer output.
Definition of Done
- State update rules and resume behavior are approved.

Story 9: Writing loop implementation
Tasks
- Implement run loop: plan -> opening preview -> write -> lint -> repair -> commit -> advance.
- Write scene markdown and scene meta.json with state patches.
- Update continuity pack, style anchor, and rolling bible after each scene.
Definition of Done
- run produces scenes with updated state and resumes safely.

Story 10.R: Refinement - Pre-generation duplication prevention
Tasks
- Define opening preview prompt and pass/fail checks.
- Define machine-detectable opening preview format (BEGIN/END tags).
- Define banned phrase extraction scope and max list size.
- Define novelty rules for opening paragraphs.
Definition of Done
- Opening preview and banned phrase rules are approved.

Story 10: Opening preview and banned phrases
Tasks
- Implement opening preview step and regeneration on failure.
- Extract banned phrases from recent scenes and inject into prompts.
- Enforce "start in motion, no recap" constraints in write templates.
- Ensure opener stripping happens before compile and export.
Definition of Done
- Opening previews pass gates before full scene generation.

Story 11.R: Refinement - Lint, repair, and cross-scene similarity checks
Tasks
- Define lint rules for continuity, invariants, and no-recap policy.
- Define duplication detection thresholds and failure handling.
- Define repair template behavior and retry limits.
Definition of Done
- Lint, similarity thresholds, and repair behavior are approved.

Story 11: Lint, repair, and similarity gates
Tasks
- Implement lint checks (regex, state consistency, duplication).
- Implement cross-scene similarity checks (n-gram overlap and opening similarity).
- Implement repair loop that rewrites prose and patches.
- Block commits when lint or similarity gates fail after retries.
Definition of Done
- Lint prevents duplicate content and enforces invariants.

Story 12.R: Refinement - Canon store and retrieval rules
Tasks
- Define canon item schemas and index.json format.
- Define selection rules for injecting canon into prompts.
- Define series-level canon namespace and merge order without cross-book reconciliation.
- Define update rules for canon changes after scenes.
Definition of Done
- Canon schema and retrieval rules are approved.

Story 12: Canon store and retrieval
Tasks
- Implement canon index and retrieval by ID.
- Inject relevant canon into plan/write/lint steps only.
- Update canon and bible after scenes where needed.
Definition of Done
- Canon is stored, retrieved, and kept in sync with state.

Story 13.R: Refinement - Compile and export
Tasks
- Define manuscript assembly rules and scene ordering.
- Define synopsis export format and input sources.
Definition of Done
- Compile and export specs are approved.

Story 13: Compile and export implementation
Tasks
- Implement compile command for exports/manuscript.md.
- Implement export synopsis command using outline + bible.
Definition of Done
- Exports are generated with correct ordering and headings.

Story 14.R: Refinement - CLI orchestration and rerun controls
Tasks
- Define CLI options for rerun, resume, and version bumping.
- Confirm docs/help examples cover all CLI variants and optional flags.
- Define per-phase mutation rules (immutable, append-only, rewrite-with-archive).
- Define current_book.json schema and book set-current/show-current semantics.
Definition of Done
- CLI behavior for rerun and resume is approved.

Story 14: CLI commands and rerun controls
Tasks
- Implement subcommands and shared options.
- Add flags to rerun individual phases or extend runs.
- Ensure outputs are isolated by versioned prompts and archive rules.
- Implement book set-current/show-current/clear-current and enforce scope validation.
Definition of Done
- CLI supports isolated reruns without corrupting prior output.

Story 15.R: Refinement - Observability and prompt hashing
Tasks
- Define JSONL log schema and required fields.
- Define token estimate method and budget tracking.
Definition of Done
- Logging schema and prompt hash requirements are approved.

Story 15: Logging and metrics
Tasks
- Implement JSONL logs per step with prompt hashes and metrics.
- Track dynamic payload size and token estimates.
- Snapshot prompt registry per run and log hash changes.
Definition of Done
- Logs provide traceability for prompt changes and outputs.

Story 16.R: Refinement - Tests and documentation
Tasks
- Define test matrix and required doc topics.
- Define baseline examples for README and prompts.
Definition of Done
- Test plan and doc outline are approved.

Story 16: Tests and documentation
Tasks
- Add tests for schema validation, determinism, budgeter, and lint rules.
- Add tests for opening preview gates and similarity checks.
- Document setup, CLI usage, prompt tuning, and rerun flows.
Definition of Done
- Tests pass and docs cover the full workflow.

Deliverables
- Python CLI and modular package structure.
- Workspace init and generation pipeline with stored artifacts.
- Prompt system with stable prefixes, templates, registry, and budgeter.
- Author library with versioning and per-book pinning.
- Duplication prevention gates and similarity checks.
- Compiler, logs, tests, and docs.

Data / API / CLI Changes
- Data: JSON/MD files under workspace/authors and workspace/books.
- API: No public API; internal LLM adapter interface only.
- CLI: New subcommands and flags as defined in the story map.

Migration / Rollout Order
1) Scaffolding and provider layer
2) Schema validation and prompt system
3) Prompt budgeter and continuity pack
4) Author library and workspace init
5) Outline planning and writing loop
6) Opening preview and duplication gates
7) Lint/repair, canon, and compile
8) Rerun controls, logs, tests, and docs

Testing / Verification
- Unit tests for schemas, prompt assembly determinism, budgeter rules, and lint checks.
- Tests for opening preview gate, banned phrase extraction, and similarity checks.
- Integration test for a short run that produces outline, one scene, and compile output.
- Manual verification that reruns do not overwrite without explicit flags.

Risks / Rollback
- Risk: Duplication still leaks through prompts. Mitigation: continuity pack, opening preview gate, and similarity checks.
- Risk: Prompt drift due to edits. Mitigation: versioned system prompt and registry snapshots.
- Risk: Canon bloat increases token usage. Mitigation: priority tags and injection caps.
- Rollback: disable a phase, restore previous prompt version, or revert workspace artifacts via Git.

Worklog Protocol
- Create step notes under resources/plans/steps_YYYYMMDD_HHMM_<slug>.md.
- Each note includes Goal, Context, Commands, Files, Tests, Issues, Decision, Completion, Next Actions.

Refinement Notes
- Story 1.R accepted: resources/plans/steps_20260118_0012_story1r_scope_help.md
- Story 2.R accepted: resources/plans/steps_20260118_0016_story2r_llm_provider.md
- Story 3.R accepted: resources/plans/steps_20260118_0035_story3r_schema_governance.md
- Story 4.R accepted: resources/plans/steps_20260118_0036_story4r_prompt_system.md
- Story 5.R accepted: resources/plans/steps_20260118_0041_story5r_budgeter_continuity.md
- Story 6.R accepted: resources/plans/steps_20260118_0050_story6r_author_library.md
- Story 7.R accepted: resources/plans/steps_20260118_0053_story7r_workspace_schema.md
- Story 8.R accepted: resources/plans/steps_20260118_0055_story8r_outline_scene_schema.md
- Story 9.R accepted: resources/plans/steps_20260118_0100_story9r_writing_loop.md
- Story 10.R accepted: resources/plans/steps_20260118_0106_story10r_dup_prevention.md
- Story 11.R accepted: resources/plans/steps_20260118_0107_story11r_lint_similarity.md
- Story 12.R accepted: resources/plans/steps_20260118_0108_story12r_canon_retrieval.md
- Story 13.R accepted: resources/plans/steps_20260118_0109_story13r_compile_export.md
- Story 14.R accepted: resources/plans/steps_20260118_0111_story14r_cli_rerun.md
- Story 15.R accepted: resources/plans/steps_20260118_0113_story15r_observability.md
- Story 16.R accepted: resources/plans/steps_20260118_0115_story16r_tests_docs.md

Implementation Notes
- Lint mode + normalization: resources/plans/steps_20260118_1920_lint_mode_normalization.md
- Phase API key overrides: resources/plans/steps_20260118_1845_phase_api_keys.md
- Story 9 implementation: resources/plans/steps_20260118_1805_story9_write_loop_impl.md
- Outline character hooks + scene/section variance: resources/plans/steps_20260118_1210_outline_characters_beats.md
- Outline prompt file support: resources/plans/steps_20260118_1330_outline_prompt_file.md
- Outline sections + scene terminology: resources/plans/steps_20260118_1245_outline_sections_scenes.md
- Series canon scaffolding: resources/plans/steps_20260118_1130_series_canon_seed.md
- Request timeout increase: resources/plans/steps_20260118_1115_request_timeout.md
- Outline max tokens default: resources/plans/steps_20260118_1056_outline_max_tokens.md
- Outline JSON repair fallback: resources/plans/steps_20260118_1410_outline_json_repair.md
- Outline enum softening: resources/plans/steps_20260118_1510_outline_enum_soften.md
- Outline enum warnings: resources/plans/steps_20260118_1530_outline_enum_warning.md
- Outline JSON extra-data repair: resources/plans/steps_20260118_1600_outline_json_extra_data_repair.md
- Outline intensity softening: resources/plans/steps_20260118_1650_outline_intensity_soften.md
- Pretty LLM text logs: resources/plans/steps_20260118_1605_llm_pretty_logs.md
- Prompt logging: resources/plans/steps_20260118_1715_prompt_logging.md
- Story 8 implementation: resources/plans/steps_20260118_1035_story8_outline_plan_impl.md
- Story 7 implementation: resources/plans/steps_20260118_0940_story7_workspace_init.md
- Story 1 implementation: resources/plans/steps_20260118_0121_story1_scaffold.md
- Story 2 implementation: resources/plans/steps_20260118_0130_story2_llm_provider_impl.md
- Story 3 implementation: resources/plans/steps_20260118_0147_story3_schema_impl.md
- Story 4 implementation: resources/plans/steps_20260118_0151_story4_prompt_impl.md
- Story 5 implementation: resources/plans/steps_20260118_0216_story5_budgeter_continuity_impl.md
- Story 6 implementation: resources/plans/steps_20260118_0222_story6_author_impl.md
- Gemini quota handling: resources/plans/steps_20260118_0211_gemini_throttle_quota.md
- Env path fix: resources/plans/steps_20260118_0229_env_path_fix.md
- Author logging and token caps: resources/plans/steps_20260118_0918_story6_author_logging.md


Checklist
- [x] Story 1.R: Requirements baseline and architecture handshake
- [x] Story 1: Repo scaffolding and core package layout
- [x] Story 2.R: LLM provider abstraction refinement
- [x] Story 2: LLM provider layer
- [x] Story 3.R: Schema governance and validation refinement
- [x] Story 3: Schema versioning and validation implementation
- [x] Story 4.R: Prompt system and caching refinement
- [x] Story 4: Prompt templates and registry implementation
- [x] Story 5.R: Prompt budgeter and continuity pack refinement
- [x] Story 5: Budgeter and continuity pack implementation
- [x] Story 6.R: Author library versioning refinement
- [x] Story 6: Author creation pipeline
- [x] Story 7.R: Workspace init and book schema refinement
- [x] Story 7: Workspace init command
- [x] Story 8.R: Outline and scene card schema refinement
- [x] Story 8: Outline generation and scene planning
- [x] Story 9.R: Writing loop and state patch refinement
- [x] Story 9: Writing loop implementation
- [x] Story 10.R: Pre-generation duplication prevention refinement
- [ ] Story 10: Opening preview and banned phrases
- [x] Story 11.R: Lint, repair, and similarity checks refinement
- [ ] Story 11: Lint, repair, and similarity gates
- [x] Story 12.R: Canon store and retrieval refinement
- [ ] Story 12: Canon store and retrieval
- [x] Story 13.R: Compile and export refinement
- [ ] Story 13: Compile and export implementation
- [x] Story 14.R: CLI orchestration and rerun controls refinement
- [ ] Story 14: CLI commands and rerun controls
- [x] Story 15.R: Observability and prompt hashing refinement
- [ ] Story 15: Logging and metrics
- [x] Story 16.R: Tests and documentation refinement
- [ ] Story 16: Tests and documentation
