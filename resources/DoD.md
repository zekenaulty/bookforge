COGNITION — DOMAIN OF DOMAINS (DoD) White Paper Level Architecture and Design Specification Status: Draft (living document) Audience: Principal Architect, future engineering collaborators, reviewers under NDA/trust Primary intent: Define a stable, metadata-driven backend substrate that maps business domains to technical domains, supports governed continuous learning, and enables any front end and any model to operate safely and reproducibly on top of a growing knowledge and integration layer.

PURPOSE AND THESIS

The Domain of Domains (DoD) is the semantic kernel and governance plane of Cognition: a stable backend substrate that defines, constrains, and routes how knowledge, tools, workflows, and agents interact. DoD exists to solve the core problem that breaks most agentic and RAG-based systems over time: uncontrolled context, uncontrolled drift, uncontrolled coupling, and unverifiable “memory.”

DoD’s purpose is to establish an operating system for “bounded cognition” where every capability is described as data (metadata), every knowledge item is captured as a versioned asset with provenance, every retrieval is scoped deterministically, every output can be traced to citations that resolve to canonical assets, and every action surface is gated and auditable.

The system is designed to become more capable over time without collapsing into a monolithic prompt, a single opaque model, or a hardcoded planner spaghetti. The growth mechanism is structured continuous learning: the system produces artifacts, stores them under strict scope and policy, indexes them as projections, evaluates them, and uses those results to refine future plans and domain definitions. This is “self-evolving” in the explicit sense of data and workflow evolution under governance, not in the ambiguous sense of uncontrolled self-modification.

DoD is not the execution engine for everything. DoD describes and governs. Execution is performed by technical domains and workflow engines that interpret metadata contracts. This separation is non-negotiable because it is the only way to preserve open/closed and prevent cross-contamination between domains.

Key outcomes DoD must deliver:

Stable backend substrate: business domains bind to technical capabilities through metadata imports and resolved bindings; front ends are replaceable.
Deterministic scoping: scope is a canonical address, not a tag; it is the backbone of isolation, retrieval, and policy.
Citation-first retrieval: vectors and graphs are projections; truth is canonical assets; retrieval returns citations that resolve to scoped assets.
Multi-tier planning as first-class: planning artifacts exist, are stored, are evaluated, and drive refinement.
Human-gated expansion: high-impact changes and side-effect actions flow through a Foundry plane with approvals, provenance, and rollback.
Multi-model and multi-provider compatibility: models are components behind contracts; embeddings are treated as separate vector spaces; runtime profiles are pinned for reproducibility.
Swarms and orchestration as first-class: multi-agent collaboration is modeled, budgeted, and auditable rather than improvised.
DEFINITIONS AND UBIQUITOUS LANGUAGE

Domain A bounded knowledge boundary and governance container. In DDD terms, a Domain is an aggregate root. It contains manifests, bounded contexts, schema definitions, policy overlays, capability imports/bindings, and knowledge assets linked by scope and provenance.

Bounded Context A sub-boundary inside a domain where language and models are consistent. A domain may contain multiple bounded contexts (e.g., MarketAnalytics vs DocumentIngestion).

Business Domain A domain whose primary content is business meaning and evolving domain knowledge (examples: RealEstate, FictionWeaver, PersonalCompanion, ResearchLabNotebook). Business domains should not implement cross-cutting infrastructure logic.

Technical Domain A reusable domain whose primary content is hardened capability surfaces (examples: Storage, Ingestion/Coupling, Email, Reporting, Statistics, Planning, Security/Policy, Workflow Execution). Technical domains are stable, audited, and broadly reusable.

DoW (Domain of Workflows) A dedicated technical domain responsible for workflow definition and execution as graphs. It owns runtime execution semantics. DoD references DoW as a governed catalog of node kinds, bindings, policies, and audit requirements, but does not compile-time depend on DoW internals.

AI.Context The scope compiler and context assembly governance layer. It enforces deterministic scope compilation, policy resolution, retrieval hygiene, and creates context packs for agents and workflows.

AI.Forge The human-gated Foundry plane that creates, modifies, versions, tests, and registers tools, workflow nodes, adapters, and high-risk job definitions. It provides safe expansion without uncontrolled self-editing.

Scope A canonical hierarchical address used to partition and govern everything: storage partitions, retrieval filters, policy resolution, indexing, citations, and event routing. Scope is deterministic and compiled from metadata templates.

Knowledge Asset A canonical stored artifact (document, note, observation, dataset, code snippet, plan, decision record, report output, evaluation result). Assets are immutable; revisions create new assets linked by provenance.

Citation A resolvable reference from a retrieved chunk to a canonical asset under the same scope. Citations are the foundation of trust, reproducibility, and debugging.

Projection A derived representation of canonical assets and metadata optimized for queries: vector indices, keyword indices, graph stores, read models. Projections are rebuildable from canonical truth.

RLRAG (Recursive Layered RAG) A governed loop that repeatedly retrieves scoped evidence, plans, generates, validates, stores artifacts, and updates projections. It is a continuous learning substrate built on assets + citations + evaluation, not weight updates.

Runtime Profile A pinned configuration for a given output: embedding flavor(s), reranker, generation model, retrieval parameters, policy set versions, and context budgets used for that output.

DESIGN PRINCIPLES AND INVARIANTS

3.1 DDD and boundary hygiene

Business domains must not embed technical domain logic.
Technical domains must not accumulate business-specific rules.
Integration occurs through metadata: capability imports and resolved bindings.

3.2 SOLID as architecture constraints

Single responsibility: DoD governs; DoW executes; technical domains implement surfaces; business domains hold meaning.
Open/closed: new domains, tools, node kinds, and scope types should be definable through descriptors, schemas, and adapters without modifying core engines.
Dependency inversion: front ends depend on stable contracts and projections; execution depends on descriptors and adapters, not on business code.

3.3 DRY, KISS, and the YAGNI leash

DRY and KISS apply to code and metadata templates.
YAGNI is the guardrail against turning DoD into a hidden programming language. If metadata requires branching loops to function, execution logic belongs in a technical domain engine, not in DoD descriptors.

3.4 Deterministic scope compilation

Scope strings must be canonical and compiled by a stable engine from metadata templates and dimension values.
The same inputs must compile to the same scope in any environment.
Scope must be usable as an address across stores.

3.5 Canonical truth is immutable assets

Assets are append-only and content-hashed.
Revisions create new assets and provenance links.
Projections are derived and rebuildable.

3.6 Retrieval is scoped, policy-filtered, citation-first

Retrieval must enforce scope and policy before returning any chunk.
Retrieval returns citations that resolve to canonical assets.
Retrieved content is treated as untrusted data and cannot override system governance.

3.7 Reproducibility is a first-class product requirement

Every output stores the runtime profile.
The system can explain “why it said that” with citations and policy decisions.
Debugging is performed by replaying the retrieval plan and comparing outputs under pinned profiles.

3.8 Human gating for side effects and capability expansion

High-risk tool calls and workflow runs require explicit approvals.
Tool definitions and workflow node types cannot be auto-deployed without Foundry gating.
Every expansion is traceable and rollbackable.
ARCHITECTURE OVERVIEW

Cognition is composed of interacting planes. DoD is the kernel of the governance plane, and everything else is either execution, learning, interaction, or Foundry.

4.1 Governance plane (DoD kernel)

Domain registry and lifecycle
Manifest modeling and capability imports/bindings
Scope types and scope compilation rules
Policy model and resolution engine
Metadata schemas and versioning
Event types and audit requirements

4.2 Execution plane (technical domains)

Storage domain: asset persistence, hashing, retention
Ingestion/Coupling domain: API coupling, polling, change detection, normalization
Email domain: composition, templates, sending gates, audit trails
Reporting domain: report definitions, rendering, scheduling, distribution
Statistics domain: metrics, aggregations, dashboards, evaluation feeds
Planning domain: multi-tier planners and artifact outputs
Security/Policy domain: enforcement primitives and redaction logic
DoW: graph workflows and node execution semantics

4.3 Learning plane (RLRAG loop and projections)

Ingestion → asset creation → chunking → embedding (per flavor) → citation creation
Projection workers: vector indices, graph projections, keyword indices, read models
Evaluation harness: golden queries, regression checks, drift detection
Artifact feedback loop: plans and validations become assets and retrievable knowledge

4.4 Interaction plane (front ends and clients)

Chat UI, admin UI, dashboards, CLI tools, API-based applications
All front ends use stable contracts and read models, not prompt-specific shapes

4.5 Foundry plane (AI.Forge)

Tool generation and registration
Workflow node kind generation and registration
Adapter creation for new providers (models, vector engines, email transports, reporting renderers)
Approval workflows, review, rollback, provenance
FRONT-END INDEPENDENCE: STABLE CONTRACTS

A system cannot truly support “any front end” unless it exposes stable contracts that are independent of model quirks and prompt formats. DoD defines the shape of these contracts, versioning, and policy requirements.

Contract categories:

Command contracts (intent and mutation) Used to create/modify domains, register assets, propose workflows, request approvals.

Query contracts (read and search) Used to retrieve domain manifests, scope trees, asset metadata, citations, projections.

Event contracts (signals and audit) Used to publish system events: AssetIngested, ScopeCompiled, RetrievalPerformed, ToolProposed, ApprovalGranted, WorkflowExecuted, EvaluationCompleted.

View contracts (projection read models) Used to drive UIs: domain summaries, capability maps, workflow run history, policy decision logs, evaluation dashboards.

A crucial rule: front ends do not parse “LLM output” as the system of record. LLM output is a generated artifact that is stored and cited. Contracts drive the state; artifacts decorate and enrich it.

DOMAIN MODEL AND LIFECYCLE

6.1 Domain lifecycle states Draft A domain exists but is not active; manifests and policies may be incomplete; indexing may be limited; execution bindings may be absent.

Active Domain meets activation validators: manifest exists, baseline policy exists, scope types exist, capability imports resolved to bindings, evaluation harness exists at least at minimal level.

Archived Domain is read-only; no new assets except archival notes; retrieval may remain available with restrictive policies.

6.2 Domain composition Each domain contains:

Domain identity and canonical key
Domain kind (business or technical)
Bounded contexts
Domain manifest versions
Capability imports and resolved bindings
Scope types used by the domain
Policy overlays and inheritance rules
Knowledge assets and provenance graph
Evaluation assets and golden queries
Workflow bindings (references to DoW templates and node kinds)

6.3 Canonical keys and naming Domains and contexts require deterministic canonical identifiers to prevent duplication and enable stable references. Names may change; canonical keys must not.

MANIFESTS, CAPABILITIES, IMPORTS, AND BINDINGS

The keystone for mapping business domains to technical domains is explicit capability modeling.

7.1 Capability import (declared need) A business domain declares that it requires a capability category, not a specific implementation. Examples:

“Need a messaging channel for outbound notifications”
“Need a scheduled report generation capability”
“Need an ingestion pipeline for external APIs”
“Need a canonical asset store and chunking/embedding pipeline”

7.2 Capability binding (resolved mapping) DoD resolves imports to bindings: specific tool descriptors, workflow templates, and node kinds provided by technical domains. Bindings are versioned. A binding includes:

Which technical domain provides the capability
Which tool(s) and job(s) satisfy it
Which workflow templates are allowed
Side-effect profiles and required gating
Policy requirements and permitted scopes
Runtime profile defaults (embedding flavors, reranker preference)

7.3 Why imports/bindings matter They formalize the separation of concerns: business domains stay clean, technical domains stay reusable, and the platform remains open/closed. You can replace an email transport, a report renderer, or a vector engine without rewriting business domain definitions.

AI.CONTEXT: SCOPE AND CONTEXT PACKS

AI.Context is the layer that makes “knowing the user” and “preventing contamination” real, even for a simple companion app.

8.1 Scope types and templates A scope type is a template with ordered dimensions and canonicalization rules. Example dimensions (illustrative):

tenant
user
project
domain
context
privacy
geo
time

8.2 Scope compilation rules

Ordered dimensions produce stable hierarchical paths.
Missing optional dimensions are omitted deterministically.
Canonicalization normalizes casing, separators, and permitted characters.
Scope strings can be used as partition keys and retrieval filters.

8.3 Context packs AI.Context produces a Context Pack artifact for every retrieval/assembly request. A context pack includes:

the compiled scope(s) used
policy resolution results and redactions applied
retrieval plan and parameters
citations returned (not raw ungoverned chunks)
budget decisions (token budget, chunk limits, truncation choices)
runtime profile references

Context packs become assets. They are searchable, auditable, and reproducible.

8.4 Retrieval hygiene and injection resistance Retrieved content is treated as data. A context pack may contain untrusted text; it cannot alter governance. Tool calls and policy decisions are controlled outside the retrieval payload.

KNOWLEDGE ASSETS, PROVENANCE, AND CITATIONS

9.1 Asset immutability Assets are append-only. Updates create new assets linked by provenance. Each asset has:

AssetId
ScopeString
ContentHash
AssetType
CreatedAt
CreatedBy (human or agent identity)
Source provenance (ingestion origin, conversation reference, external dataset reference)
Metadata schema version reference

9.2 Chunking and stable references Chunking must produce stable references so citations remain resolvable. Stability is achieved by:

deterministic chunking rules per asset type and schema
storing chunk boundaries with the asset or in an associated chunk index
including content hash and chunk offsets in citations

9.3 Citation-first retrieval Vectors and graph links point to citations; citations point to canonical assets. A citation minimally includes:

CitationId
AssetId
ScopeString
ContentHash
ChunkAddress (start/end offsets or chunk id)
RetrievalTimestamp
Provenance reference

9.4 Anti “receipt laundering” rule Generated summaries and model outputs are assets, but they are labeled as generated. They cannot be the sole evidence for claims about user facts or durable preferences. Durable claims must ground in human-origin or external-source assets, or be explicitly marked as unverified hypotheses with confidence and decay rules.

RLRAG: RECURSIVE LAYERED RAG AS A GOVERNED LOOP

RLRAG is the core learning and refinement loop. It creates the effect of “the system getting smarter” through governed artifacts and evaluations rather than weight updates.

A canonical RLRAG cycle:

10.1 Retrieve (scoped)

compile scopes and envelopes
resolve policy and redactions
query projections: vector + keyword + graph
return citations and evidence snippets as a context pack

10.2 Plan (multi-tier)

create a plan artifact describing intent, constraints, and steps
create a retrieval plan artifact (what must be fetched, from where, under what scope)
create a validation plan artifact (what will be proven, what tests must pass)

10.3 Generate (bounded)

produce output as a stored artifact
embed citations directly into the artifact structure
attach runtime profile used

10.4 Validate (auditable) Validation is not “the model thinks it’s correct.” Validation is:

citation resolution checks (all citations resolve to assets/chunks)
schema validation (if output has structured schema)
invariant checks (domain constraints, policy constraints)
regression checks against golden queries
contradiction detection against known facts with traceable citations

10.5 Capture (store everything) Store: plan artifacts, context pack, generated artifact, validation results, and event trail.

10.6 Project (update projections) Projection workers update:

vector indices (per embedding flavor)
graph relationships (domain links, workflow lineage, provenance)
read models (UI-friendly summaries)
evaluation dashboards
WORKFLOWS AND ORCHESTRATION AS FIRST-CLASS SYSTEMS

11.1 DoW as generalized graph engine A workflow is a graph: nodes and edges with metadata. Node meaning is expressed by node kind descriptors rather than hardcoded classes. Execution is performed by DoW runtime using adapters.

11.2 DoD’s role in workflows DoD provides:

node kind catalog and schemas
tool descriptors and bindings usable by nodes
policy rules for which node kinds and tools can run under which scopes
audit requirements and gating rules
workflow template registry

11.3 Workflows as knowledge graphs Workflows produce rich lineage: what happened, what evidence was used, what outputs were produced, what validations passed. That lineage is itself knowledge. The system can later retrieve:

“what workflows produced this report?”
“what evidence supported this decision?”
“what changed since last successful run?”
AGENT SWARMS AND INTERACTIVITY AS FIRST-CLASS

Swarms are not an emergent accident. They are modeled, budgeted, and governed.

12.1 Swarm template A swarm template defines:

roles (Retriever, Planner, Synthesizer, Validator/Auditor, Recorder)
allowed models per role and runtime profile defaults
budgets per role (token/time/cost)
termination rules (max turns, convergence criteria)
output artifacts required per role
veto rules (validator can block publication)
gating rules (human approval requirements for side effects)

12.2 Why swarms exist Swarms are justified when:

tasks require cross-checking, validation, and compositional planning
outputs must be citation-grounded and reproducible
the system must be robust against single-model failure modes

12.3 Interactivity as system surface User interaction is not just chat messages. It includes:

reviewing citations and drilling into sources
approving or rejecting proposed actions
editing proposed domain manifests and templates
correcting stored beliefs and preferences
exploring scope trees and retrieval envelopes Interactivity requires stable view contracts and audit trails.
TECHNICAL DOMAINS: MINIMUM SET AND RESPONSIBILITIES

The platform becomes real when technical domains are modeled with hardened surfaces. The “ready examples” are not arbitrary; they force edge cases and provide human-testable proofs.

13.1 Storage domain Responsibilities:

canonical asset persistence (NoSQL + blob)
content hashing
retention and lifecycle policies
revision management and provenance links
chunk boundary storage and retrieval support

Key invariants:

assets are immutable
revisions are new assets
content hash integrity is enforced
scope partitioning is supported directly

13.2 Ingestion/Coupling domain Responsibilities:

API coupling and ingestion pipelines
polling and change detection
normalization and schema snapshots
transactional outbox for eventing
durable ingestion logs and replay

Key invariants:

ingestion produces assets with provenance
failures produce diagnostic assets
pipelines are versioned and testable
replay is possible without duplicating truth

13.3 Email domain Responsibilities:

message composition as an artifact
templates and personalization rules
outbound sending as gated action
audit logs and delivery receipts as assets

Key invariants:

no send without gate when policy requires
sent messages are stored with citations to their composing evidence if applicable

13.4 Reporting domain Responsibilities:

report definitions as versioned assets
rendering pipelines (PDF/HTML/JSON)
scheduled jobs and triggered runs
distribution bindings (often via Email domain)
report outputs are assets with provenance

Key invariants:

reports are reproducible under pinned profiles
report outputs cite underlying evidence assets where meaningful
job execution is auditable and gated where required

13.5 Statistics domain Responsibilities:

metric definitions and schemas
aggregations and trend analysis
evaluation dashboards and drift indicators
feeding planning quality metrics

Key invariants:

metrics have provenance to source assets
aggregations are rebuildable
evaluation results are stored assets used in RLRAG validation

13.6 Planning domain Responsibilities:

multi-tier planning artifact schemas
planners as role-based tools or workflows
plan validation and refinement loops
plan libraries and templates

Key invariants:

plans are stored assets
plans include assumptions and required evidence citations
plans produce executable workflow proposals
BUSINESS DOMAINS AND THE BUSINESS→TECHNICAL MAP

Business domains declare meaning and needs; they do not implement infrastructure.

A business domain typically includes:

domain glossary and semantics
bounded contexts and schema definitions
capability imports
policies and privacy rules
evaluation harness relevant to the domain
workflow templates that compose technical capabilities

A business→technical map is formed by:

capability imports (declared need)
resolved bindings (selected implementation surfaces)
scope constraints (which scopes the bindings may operate in)
runtime profile defaults (embedding flavors, rerankers, model classes)
gating requirements (approval levels)
EMBEDDINGS, VECTOR SPACES, AND MULTI-MODEL STRATEGY

15.1 Embedding vs vector

An embedding model maps inputs to vectors.
A vector is the numeric representation in a particular embedding space. Vectors from different embedding models are not generally comparable.

15.2 Multi-encoder strategy To support multiple vector engines or provider embeddings:

store canonical chunk text (asset is truth)
generate multiple embeddings for the same chunk (per flavor)
store them in separate indices or separately keyed fields
query the correct index based on domain manifest and runtime profile

15.3 Runtime profile pinning Every output stores:

embedding flavor used for retrieval
reranker identity and version
generator model identity/class
retrieval parameters (k, filters, rerank thresholds)
context budget and truncation strategy

This is the foundation of reproducibility.

SECURITY, POLICY, AND ZERO-TRUST GOVERNANCE

16.1 Deny-by-default policy resolution Policies are hierarchical and deterministic. Resolution order is explicit (domain → context → schema/field → asset tags). Conflicts resolve by rule, not by intuition.

16.2 Field-level redaction Sensitive fields may exist inside structured assets. Retrieval and view models must support redaction so that:

vectors are filtered by policy before retrieval
returned snippets are redacted when required
citations remain resolvable but may lead to redacted displays depending on viewer permissions

16.3 Tool gating and side-effect profiles Tools are categorized by side-effect profile:

None (pure compute, read-only)
Low (minor side effect, reversible)
High (external actions: send email, schedule jobs, delete, purchase)

Policies can require:

no gate (low risk)
single approval
multi-approval
staged rollout (e.g., dry-run then execute)

16.4 Prompt injection defense posture

retrieved assets are treated as untrusted data
tool execution requires explicit tool descriptors and permission checks
no retrieved content can override governance instructions
the system records retrieval sources and policy decisions for auditing
EVENTING, CONSISTENCY, AND PROJECTIONS

17.1 Transactional outbox pattern Canonical writes (domain changes, asset creation) emit events via an outbox to avoid dual-write corruption between databases and projections.

17.2 Projection workers Separate workers update:

vector indices
graph projections
keyword indices
UI read models Projection workers are idempotent and rebuildable.

17.3 Rebuild procedures A mandatory operational requirement: you can wipe projections and rebuild from canonical truth. If you cannot rebuild, you do not control your system.

OBSERVABILITY, AUDITABILITY, AND DEBUGGABILITY

A long-lived cognition system is mostly a debugging system.

Every retrieval should record:

request identity
compiled scopes and envelopes
policy decisions and redactions applied
indices queried and parameters used
citations returned and scores
rerank results
truncation choices

Every workflow run should record:

workflow template id and version
node executions, inputs/outputs
tool calls and gating events
produced assets and citations
validation results
runtime profile

Every approval should record:

who approved
what was approved
what evidence supported approval
what rollback path exists
EVALUATION AND DRIFT CONTROL

Evaluation is a first-class domain concern, not an afterthought.

19.1 Golden queries Each domain maintains a minimal set of golden queries with expected citation patterns and expected constraints. Examples:

“What are my persistent preferences?” (must cite user-origin assets)
“What changed since last week in MarketAnalytics?” (must cite weekly ingestion assets)
“Why did you recommend this?” (must cite evidence assets and show runtime profile)

19.2 Regression harness

run golden queries on schedule or after significant changes
store evaluation outputs as assets
compare drift metrics over time
block promotions if key evaluations fail

19.3 Truth vs consistency A dangerous failure mode is optimizing for consistency with prior outputs instead of correctness grounded in evidence. Evaluation must reward citation grounding and correct sourcing patterns, not just self-consistency.

THE DOMAIN THAT DEFINES DOMAINS: SELF-REFERENTIAL GOVERNANCE

After proof-of-concept domains validate the plumbing, the platform must model the meta-domain that defines how future domains are created and evolved.

20.1 Meta-domain responsibilities

domain templates (business/technical)
bounded context templates
scope type catalogs and canonicalization rules
policy templates and redaction templates
validation templates and golden query templates
workflow templates for “create domain,” “activate domain,” “archive domain,” “propose domain change”
capability import catalogs and resolution strategies

20.2 Domain creation as a governed workflow A “CreateDomain” workflow should produce draft assets:

domain manifest
bounded contexts
required scope types
baseline policy set
capability imports
initial bindings proposal
evaluation harness (golden queries) Human review is required before activation.

20.3 Evolution without runaway self-editing The system may propose changes; it may not self-deploy high-impact changes. Promotions require:

validation pass
evaluation pass
approvals where required
versioning and rollback plan
PROOF-OF-CONCEPT DOMAINS: INTRICATE BUT HUMAN-TESTABLE

POCs must hit edge cases early while remaining understandable.

POC A: Companion-grade Personal Ops domain

captures user notes, preferences, goals, plans
enforces privacy scopes and anti-receipt laundering
demonstrates that “knowing the user” is evidence-grounded
minimal technical bindings: Storage + Planning + Statistics (and optionally Email for reminders with gating)

POC B: RealEstate MarketAnalytics domain

ingestion/coupling pipeline (polling, change detection, normalization)
statistics aggregations and trend outputs
report generation and distribution through Email domain with gating
demonstrates end-to-end assets→citations→reports→audits

POC C: DoD self-modeling slice

models a small set of domain templates and validators
runs “create domain” workflow and produces drafts
demonstrates self-referential governance without uncontrolled changes
FAILURE MODES AND GUARDRAILS

22.1 Metadata rules-engine collapse Symptom: descriptors begin to require loops, branching, and exceptions. Guardrail: descriptors must remain declarative; branching belongs in technical domain engines with versioned code and tests.

22.2 Scope explosion and retrieval starvation Symptom: retrieval finds nothing because scopes are too narrow, or costs explode due to too many partitions. Guardrail: define scope tiers and controlled “search envelopes” that can widen within policy rules; record envelope expansions as audit artifacts.

22.3 Projection drift and stale indices Symptom: citations resolve but retrieval misses critical evidence, or indices lag behind truth. Guardrail: rebuild procedures, projection health checks, and evaluation harness that catches retrieval degradation.

22.4 Receipt laundering and self-reinforcing hallucinations Symptom: system cites its own generated summaries as proof and amplifies errors. Guardrail: generated assets are labeled; durable user claims require grounding in user-origin or external-source assets; validators detect self-citation loops.

22.5 Swarm cost blowouts and non-convergence Symptom: most compute spent on agent chatter, no commitment to execution. Guardrail: strict budgets, termination rules, single-writer patterns, validator veto, and enforced artifact outputs.

22.6 Governance deadlock Symptom: Foundry approvals block progress and nothing ships. Guardrail: risk-tiered gating; low-risk auto-approve with audit; medium-risk single approval; high-risk multi-approval; staged rollouts.

VALID USE CASES THAT JUSTIFY THE ARCHITECTURE

23.1 Companion and assistant applications Justification: long-lived evolution, deterministic scoping, receipts for memory claims, tool gating, and reproducibility are essential for trust. A companion that cannot explain its memory or cannot avoid privacy contamination becomes unusable over time.

23.2 Integration and reporting fabrics Justification: recurring ingestion, schema drift, report reproducibility, audit trails, and distribution pipelines require canonical assets and governed workflows.

23.3 Regulated decision support Justification: citations, provenance, policy enforcement, redaction, and auditability are requirements, not enhancements.

23.4 Long-lived R&D notebooks Justification: experiments, evaluations, and changing hypotheses require a governed artifact loop to prevent drift and to preserve lineage.

DEFINITION OF DONE FOR DoD

A Definition of Done (DoD) for DoD is required because the architecture can expand indefinitely. Completion must be defined in layers: Kernel, Platform, and Meta-domain.

24.1 DoD Kernel: minimum viable, companion-grade completion criteria

A. Canonical asset store is authoritative

Every persisted memory, plan, preference, decision, note, ingestion record, report output, and evaluation is a content-hashed immutable asset.
Revisions create new assets linked by provenance.
Canonical truth can be exported and re-imported without losing identity.

B. Deterministic scope compiler exists and is metadata-driven

Scope types are defined by templates with ordered dimensions and canonicalization rules.
New scope types and dimensions can be introduced without modifying core compilation code (template/data change only).
Same input values produce the same scope string in every environment.

C. Retrieval returns citations that resolve to canonical assets

Retrieval outputs are citations and snippets anchored to asset/chunk references.
Citations include scope and content hash.
A user-facing evidence viewer can resolve any citation to its source (subject to policy).

D. Deny-by-default policy resolution is enforced

Retrieval is policy-filtered before returning any chunk.
Redactions are applied deterministically.
Audit logs record policy decisions for retrieval and action attempts.

E. Runtime profiles are pinned and stored

Each output artifact stores embedding flavor, reranker identity, generator model class, retrieval parameters, and context budget strategy.
Outputs can be replayed in a controlled manner for debugging.

F. Anti receipt laundering is enforced

Generated assets are labeled.
Durable claims about the user cannot be supported solely by generated assets; they must ground in user-origin or external-source assets or be flagged as unverified hypotheses with decay.

G. Minimal evaluation harness exists

Golden queries exist for identity and key preferences.
Drift is measured and stored as evaluation assets.
Failures produce actionable diagnostics.

24.2 DoD Platform: stable substrate completion criteria

A. Business→technical mapping is implemented and enforced

Business domains declare capability imports.
DoD resolves imports to versioned bindings referencing technical domains’ tool and workflow descriptors.
Contamination validators prevent business domains from embedding technical logic.

B. Core technical domains are modeled and operational

Storage, Ingestion/Coupling, Email, Reporting, Statistics, Planning, Security/Policy, and DoW bindings exist as technical domains with hardened descriptors.

C. Front-end independence contracts exist and are versioned

Command/Query/Event/View contracts exist with schema versioning.
UIs and clients can be built against these contracts without depending on prompt formats or model idiosyncrasies.

D. Polyglot persistence with rebuildable projections exists

Relational store holds invariants.
NoSQL/blob holds canonical assets.
Vector and graph stores are projections with rebuild procedures.
Transactional outbox and projection workers avoid dual-write corruption.

E. RLRAG loop is operational end-to-end

Retrieve → Plan → Generate → Validate → Capture → Project is implemented as a workflow family.
Each stage produces stored artifacts.
Validation can veto publication/promotion.

F. Foundry gating exists for capability expansion

Tools, node kinds, and adapters are versioned and registered via approvals.
Rollback paths exist and are tested.
Provenance links every capability to an approval trail.

G. Swarm orchestration is first-class and budgeted

Swarm templates exist with roles, budgets, termination rules, and output artifact requirements.
Orchestration is auditable and reproducible.

24.3 DoD Meta-domain: Domain that defines Domains completion criteria

A. Domain creation is a governed workflow

A workflow produces domain drafts (manifest, contexts, scopes, policies, imports, validation harness).
Human review is required prior to activation.
Activation validators are enforced.

B. Templates and validators are first-class assets

Domain templates and policy templates are versioned assets.
Validators prevent contamination, enforce scope determinism, enforce citation requirements, and require an evaluation harness.

C. Evolution is controlled and promotable

The system can propose changes and run validations/evaluations.
Promotions require explicit approvals and successful regression checks.
Rollback is possible and documented.
REFERENCE CONCEPTUAL DATA MODEL

The following conceptual schemas are illustrative and intended to be refined into implementation schemas. They are presented to ground the architecture in concrete objects.

Domain (aggregate root)

DomainId (guid)
CanonicalKey (string)
Name (string)
Kind (Business | Technical)
Status (Draft | Active | Archived)
ParentDomainId (optional)
Description (text)
BoundedContexts (list)
ManifestCurrent (DomainManifest ref)
ManifestHistory (list of DomainManifest refs)
CapabilityImports (list of CapabilityImport)
CapabilityBindings (list of CapabilityBinding)
PolicyRefs (list)
ScopeTypeRefs (list)
WorkflowBindingRefs (list)
CreatedAt, UpdatedAt

BoundedContext

ContextId
DomainId
Name
ContextKey
Description
SchemaRefs
ToolBindingRefs
WorkflowBindingRefs

DomainManifest (versioned, immutable once published)

ManifestId
DomainId
Version
AllowedEmbeddingFlavors
DefaultEmbeddingFlavor
IndexIsolationPolicy (Shared | Dedicated | Hybrid)
AllowedToolCategories
SafetyProfile
RequiredMetadataSchemas
RuntimeProfileDefaults
PublishedAt

CapabilityImport

ImportId
DomainId
CapabilityKey (e.g., “messaging.outbound”, “reporting.generate”, “ingestion.api”)
Constraints (json)
RequiredSafetyProfile
RequiredScopeConstraints

CapabilityBinding (versioned resolution)

BindingId
DomainId
ImportId
ProvidingTechnicalDomainKey
ToolDescriptorRefs
JobDescriptorRefs
WorkflowTemplateRefs
GatingRequirements
AllowedScopes
RuntimeProfileDefaults
Version
ActivatedAt

ScopeType

ScopeTypeId
Name
OrderedDimensions (list)
TemplatePattern
CanonicalizationRules
ValidationRules

ScopeInstance

ScopeInstanceId
ScopeTypeId
DimensionValues (key/value)
CompiledScopeString
LinkedDomainId (optional)
LinkedContextId (optional)

KnowledgeAsset (immutable)

AssetId
DomainId
ContextId (optional)
ScopeString
AssetType
ContentRef (document/blob pointer)
ContentHash
Metadata (json)
Provenance (append-only chain)
CreatedAt
CreatedBy

Citation

CitationId
AssetId
ScopeString
ContentHash
ChunkAddress (chunk id or offset range)
RetrievedAt
RetrievalContextPackId

ContextPack (AI.Context output, immutable)

ContextPackId
RequestId
ScopeStringsUsed
PolicyDecisionLogRef
RetrievalPlanRef
CitationsReturned
BudgetDecisions
RuntimeProfileRef
CreatedAt

ToolDescriptor

ToolId
Name
OwningTechnicalDomainKey
Category
Description
InputSchemaRef
OutputSchemaRef
SideEffectProfile
HumanGateRequired
RequiredApprovals
RateLimits
AuditTags
Version

JobDescriptor

JobId
Name
OwningTechnicalDomainKey
ScheduleCapabilities
Inputs
Outputs
GateRules
Version

WorkflowTemplate (DoW reference)

WorkflowTemplateId
Name
NodeKindsUsed
InputContracts
OutputContracts
GatingRules
Version

EventType

EventTypeId
Name
SchemaRef
EmissionPolicies
RoutingRules
RetentionRules

EvaluationAsset

EvaluationId
DomainId
ScopeString
GoldenQueryId
RunTimestamp
RuntimeProfileRef
OutcomeMetrics
Failures
LinkedArtifacts (context packs, outputs, validations)
CONCRETE END-TO-END EXAMPLE

Business Domain: RealEstate Bounded Context: MarketAnalytics Scope: tenant:T1/project:P7/domain:RealEstate/context:MarketAnalytics/geo:CaryNC/time:2026-W06/privacy:org

Declared capability imports

ingestion.api.marketdata (requires nightly polling, schema snapshotting)
statistics.trends (requires weekly aggregation)
reporting.generate (requires PDF + JSON outputs)
messaging.outbound (requires email distribution with approval gate)

Resolved bindings (example)

ingestion.api.marketdata → provided by Ingestion/Coupling domain: PollingPipeline v3 + Normalizer v2
statistics.trends → provided by Statistics domain: TrendAggregator v1
reporting.generate → provided by Reporting domain: ReportRenderer v4
messaging.outbound → provided by Email domain: OutboundMailer v2 (human approval required)

Nightly workflow run

Ingestion pipeline polls external API and detects changes.
Normalizer writes canonical assets: raw payload asset, normalized snapshot asset, schema snapshot asset; provenance links connect them.
Projection worker chunks and embeds normalized snapshot using the embedding flavor specified by the domain manifest. Citations are created for each chunk.
Weekly aggregator retrieves scoped snapshots via citations and produces a trend asset with provenance.
Reporting renderer produces a PDF report asset and a JSON report asset; both cite the trend asset and key snapshot citations.
Email domain composes an outbound message asset linking the report; send is gated.
Approval is requested and recorded; upon approval, send occurs; delivery receipt becomes an asset.
Evaluation harness runs golden queries: “what changed,” “why,” “show evidence,” and stores evaluation assets. Failures block promotion of new pipeline versions.

This example is intentionally mundane because it is testable. It forces the architecture to prove that scope, citations, gating, and reproducibility are real.

ROADMAP AND PHASING

Phase 0: Kernel substrate

Asset store (immutable) + hashing
Scope types + deterministic compiler
Policy deny-by-default enforcement
Citation object + resolvers
Minimal retrieval pipeline returning context packs
Runtime profile recording
Minimal evaluation harness

Phase 1: Technical domain skeletons

Storage domain complete
Ingestion/Coupling basic pipeline and replay
Reporting definition and output assets
Email composition + gated send
Statistics basic aggregations
Planning artifacts

Phase 2: DoW bindings and workflow graphs

Workflow templates and node kind registry
Orchestration logging and artifacts
Tool descriptors integrated into DoW nodes

Phase 3: Foundry (AI.Forge)

Tool/node/adapters versioning
Approval workflows
Rollbacks
Promotion gates tied to evaluations

Phase 4: Swarms as first-class templates

Role contracts, budgets, termination rules
Validator veto system
Single-writer and recorder roles standardized

Phase 5: Meta-domain self-definition

Domain templates and validators as assets
Create/activate domain workflows
Safe evolution policies and promotion gates
ACCEPTANCE TESTS AS HARD GATES
Trust test: every durable claim about the user or domain state includes resolvable citations to canonical assets.
Scope test: same inputs compile to the same scope string; retrieval cannot escape allowed scopes.
Contamination test: business domains do not implement technical logic; technical domains remain reusable across business domains.
Rebuild test: wipe projections and rebuild them from assets and events; evaluations still pass.
Safety test: no high-risk action executes without required approvals and audit trail.
Debug test: “why did it say that?” yields citations, policy decisions, and runtime profile used.
Drift test: golden queries detect regressions and block promotion.

APPENDIX: MINIMUM VIABLE IMPLEMENTATION NOTES (GROUNDING WITHOUT COMMITTING TO A STACK)

Canonical truth store should support: immutable documents, content hashing, and partitioning by scope. A relational store is appropriate for invariants and registries (domains, manifests, scope types, policy rules, tool descriptors). A document store is appropriate for assets and long-form artifacts. Vector and graph stores are projections, selected based on operational constraints and runtime profiles. The exact vendor choices can change; the architecture requires that projections be rebuildable and that vector spaces not be mixed.

The practical “companion app” takeaway: even a basic assistant needs deterministic scope, receipts for memory, policy gating for privacy and actions, and runtime profile pinning for reproducibility. This white paper treats those as baseline requirements, not premium features.

