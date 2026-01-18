# DoD Domains + Workflows Data Layer v2

Objective
- Add a dedicated DoD domain model and relational persistence layer, plus a workflows core library, while reusing existing AI orchestration, relational access, and vector storage.
- Stand up a free, .NET-friendly NoSQL document store for long-form DoD artifacts (manifests, assets) without replacing current relational or vector stores.
- Replace the current React console with a bare-bones DoD-first console and update the solution build process to use the new console output.

Definition of Done
- New projects (`Cognition.Domains`, `Cognition.Domains.Relational`, `Cognition.Domains.Documents`, `Cognition.Workflows`, `Cognition.Workflows.Relational`) build in `Cognition.sln` with clean dependency boundaries.
- EF Core DbContext and migrations exist for the DoD minimum schema with constraints that enforce core invariants.
- RavenDB Community integration is implemented with document repositories and DI wiring.
- Optional baseline seed data is documented and repeatable; API/Jobs wiring supports future services.
- Tests validate DbContext invariants and migration apply; docs describe configuration and verification.
- New DoD-first console builds and is wired into the solution so the build process outputs the new console assets instead of the legacy console.
- Conversation flow issues are triaged against hub/bus paths and the new console follows `docs/chat_flow_spec.md` for validation.

Scope
- DoD domain entities/value objects, relational mappings, and migrations.
- Workflow graph abstractions and core models (no execution engine yet).
- Workflow relational persistence for graph definitions and execution state.
- RavenDB document storage for long-form DoD artifacts.
- DI wiring and minimal service layer (repositories + seed utilities).
- New bare-bones React console focused on DoD exploration and workflow visibility.

Out of Scope
- UI/console changes, new LLM clients, or new vector store implementations.
- Full workflow execution runtime, planners, or orchestration pipelines (tracked separately).
- Large-scale data backfills or production rollout choreography beyond local dev.

Assumptions / Reuse
- AI client orchestration uses `Cognition.Clients` (no new LLM/embeddings clients).
- Relational access for existing features remains in `Cognition.Data.Relational`.
- Vector search/embeddings remain in `Cognition.Data.Vectors` (OpenSearch).
- NoSQL store: RavenDB Community (best-case free .NET option); swapable later if needed.
- Existing API/hub endpoints are reused; the new console should not require backend rewrites.
- Each new data system (DoD and Workflows) gets its own Postgres database and Docker volume.

Current Code Anchors (reviewed)
- `src/Cognition.Data.Relational/CognitionDbContext.cs` (monolithic DbContext, module config pattern).
- `src/Cognition.Data.Relational/Modules/Conversations/WorkflowEvent.cs` and `ConversationWorkflowState.cs` (existing workflow logging).
- `src/Cognition.Jobs/WorkflowEventLogger.cs` (workflow event writer).
- `src/Cognition.Api/Program.cs` and `src/Cognition.Jobs/Program.cs` (DI patterns for Db/Vectors/Clients).
- `src/Cognition.Data.Vectors/OpenSearch` (vector store implementation to reuse).

Project Layout (v2)
- `Cognition.Domains`
  - DoD domain model (Domain, BoundedContext, DomainManifest, ScopeType, ScopeInstance, KnowledgeAsset, ToolDescriptor, Policy, EventType, etc.).
  - Value objects and invariants only (no EF Core).
- `Cognition.Domains.Relational`
  - EF Core DbContext + configurations + migrations for DoD data.
  - Depends on `Cognition.Domains` and EF Core.
- `Cognition.Domains.Documents`
  - RavenDB repositories + document models for long-form artifacts.
- `Cognition.Workflows`
  - Workflow graph types (Workflow, Node, Edge, ExecutionState), contracts for future engines.
- `Cognition.Workflows.Relational`
  - Workflow definitions + execution persistence (EF Core) with migrations.
- Extend `Cognition.Contracts` for DoD/workflow events instead of adding a new contracts project.
- `Cognition.Console.Dod` (name TBD if you prefer)
  - Bare-bones Vite/React console aligned to DoD model and workflow views.
  - Build output wired to `Cognition.Api/wwwroot` (replaces legacy console output).

Story Map (Large Chunks)
- Story 1: Project scaffolding and dependency boundaries
  - Add new projects and wire into `Cognition.sln`.
  - Decide connection string keys (e.g., `DomainsPostgres`, `DomainsNoSql`).
  - Confirm RavenDB Community as NoSQL store; document fallback options.
  - Update `docker-compose.yml` with distinct Postgres containers for DoD/Workflows plus RavenDB.
- Story 2: DoD domain modeling (Cognition.Domains)
  - Implement DoD aggregates and value objects (POCO-first; invariants enforced via relational constraints and services).
  - Define canonical keys and scope string rules aligned with existing `ScopePath` patterns.
- Story 3: Relational persistence (Cognition.Domains.Relational)
  - Create DoD DbContext, entity configurations, and migrations.
  - Add indexes/constraints for canonical keys, manifest versioning, and policy defaults.
- Story 4: NoSQL documents (Cognition.Domains.Documents)
  - Store long-form manifests, assets, and provenance payloads in RavenDB.
  - Add repository interfaces and DI wiring for read/write.
- Story 5: Workflows core library (Cognition.Workflows)
  - Define workflow graph types and metadata contracts.
  - Map to existing `WorkflowEvent` logging without migrating legacy tables yet.
- Story 6: Workflow relational persistence (Cognition.Workflows.Relational)
  - Define workflow schema (definitions, nodes, edges, executions) and migrations.
  - Provide adapters to emit or read from existing workflow event logs as needed.
- Story 7: Integration, seeding, and verification
  - DI wiring in `Cognition.Api` and `Cognition.Jobs`.
  - Optional seed data for core technical domains and policies.
  - Tests + docs: Sqlite in-memory DbContext tests and migration apply.
- Story 8: DoD-first console and chat flow stabilization
  - Scaffold `Cognition.Console.Dod` and define minimal routes (domains, contexts, workflows, assets).
  - Wire new console build output into API hosting (replace legacy console build in `Cognition.Api/wwwroot`).
  - Triage hub/bus conversation flow issues and validate against `docs/chat_flow_spec.md`.

Deliverables
- New domain and workflow projects with clean boundaries.
- EF Core DbContext, configurations, and baseline migrations for DoD.
- RavenDB-backed document repositories.
- Workflow relational schema + migrations.
- Tests for invariants and migration apply; docs for configuration and verification.
- New console app with DoD-first navigation and a verified build pipeline integration.

Data / API / Service / UI Changes
- Data: new DoD schema/tables and NoSQL collections for manifests/assets.
- API: internal services only; no new public endpoints in v2.
- Services: repositories for domain lifecycle and manifest publishing.
- UI: new DoD-first console; legacy console deprecated.

Migration / Rollout Order
1) Add projects and baseline models.
2) Implement DoD DbContext + migrations.
3) Add RavenDB integration and repositories.
4) Implement workflow relational persistence.
5) Wire DI and optional seed data.
6) Replace console build output with the new DoD console.
7) Document rollback and future backfill strategy.

Testing / Verification
- DbContext tests with Sqlite in-memory for invariants and constraints.
- Migration apply test for a clean database.
- `dotnet build` and `dotnet test` with new projects included.
- Manual verification of conversation flow using `docs/chat_flow_spec.md` plus hub/bus diagnostics.

Risks / Rollback
- Dependency drift if DoD projects take on existing feature modules; keep boundaries strict.
- NoSQL choice risk; isolate RavenDB behind repository interfaces for future swap.
- Console replacement risk: ensure build output swap is explicit and revertible.
- Rollback: disable DoD DI wiring, drop DoD schema/collections, remove migrations.

Worklog Protocol
- Create step notes under `plans/dod_domains_workflows_v2_step_YYYYMMDD_HHMM_<slug>.md`.
- One discrete action per step note with Goal, Context, Commands, Files, Tests, Issues, Decision, Completion, Next Actions.

Checklist
- [x] Story 1: Create `Cognition.Domains`, `Cognition.Domains.Relational`, `Cognition.Domains.Documents`, `Cognition.Workflows`, `Cognition.Workflows.Relational` projects and add to solution.
- [x] Story 1: Decide connection string keys and RavenDB defaults.
- [x] Story 1: Update `docker-compose.yml` with distinct Postgres containers and RavenDB.
- [x] Story 2: Implement DoD entities/value objects with invariants (via constraints/services).
- [x] Story 3: Implement DoD DbContext, configs, and baseline migration.
- [x] Story 3: Add relational indexes/constraints for canonical keys and manifest versions.
- [x] Story 4: Add RavenDB document repository and DI wiring.
- [x] Story 5: Implement workflow graph core types and metadata contracts.
- [x] Story 6: Implement workflow relational schema + migrations.
- [x] Story 7: Add optional seed data and DI registration.
- [x] Story 7: Add tests (model validation + migration reflection) for DbContext invariants and migration apply.
- [x] Story 7: Update docs with configuration, verification, and rollback.
- [x] Story 8: Scaffold new DoD console and wire build output to replace legacy console assets.
- [ ] Story 8: Triage hub/bus conversation flow issues; validate with `docs/chat_flow_spec.md`.
