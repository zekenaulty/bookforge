# Mainline Turn-Scoped Rebuild Plan

Date: 2026-07-15

## Decision

- Use `main` as the product baseline.
- Keep `phase-runner-changes` as a read-only research/reference branch.
- Do not merge or broadly cherry-pick `phase-runner-changes`.
- Land the writer-lock hotfix independently.
- After the hotfix is reviewed, create `codex/turn-scoped-authoring` from the updated mainline and reconstruct only the concepts that survive contract-first review.

## Repository evidence

| Surface | Observed state | Consequence |
| --- | --- | --- |
| `main` | `f48da69e`; linear `run_loop`; no execution, branch, recovery, or section-workflow stack | Clean baseline, but it needs an immediate concurrency guard |
| `phase-runner-changes` | `7b4d3bc9`; 67 commits ahead of main | Too large and coupled to treat as a feature patch |
| Branch delta | 8,127 changed paths; 3,484,439 insertions; 77,258 deletions | Review by concept and invariant, not by bulk merge |
| Prompt/schema delta | 106 changed prompt/schema artifacts; 4,609 insertions and 370 deletions | Treat prompt language, schemas, parsers, validators, retries, and fixtures as one migration unit |
| Prompt forensics | Existing snapshots, hashes, touchpoint maps, change matrix, and drift plans cover 14 mainline templates | Reuse this evidence instead of re-discovering prompt/code coupling ad hoc |
| Generated artifacts | 7,247 changed paths under `workspace/` | Must never be used as source-code migration input |
| Preserved WIP | `stash@{2026-07-15 19:24:57 -0500}`; 128 files, including the chapter/section-spine experiment and Sundered Resonance artifacts | Evidence is preserved without contaminating the hotfix branch |

## Reality of the branch and recovery features

The later branch contains real implementations, not just plans:

- `src/bookforge/branching_*.py` creates snapshots and promotes branch snapshots to main or a parent branch.
- `src/bookforge/execution/recovery_*.py` creates a recovery branch, quarantines artifacts, normalizes outline scope, invalidates outputs, rebuilds state, redrafts, validates, and promotes.
- `src/bookforge/query/outline_lineage.py` and `src/bookforge/query/recovery.py` expose lineage and recovery diagnostics.
- `src/bookforge/section_workflow.py` supplies section-scoped authoring storage and execution support.

Those features do not safely solve the original overlapping-writer incident:

1. There is no book-scoped file or process lock in either `main` or `phase-runner-changes`.
2. `get_recovery_branch_health()` counts receipt action names without filtering for `success` or `no_op`, while other recovery queries do filter statuses. `promote_recovery_branch()` trusts that health result. A failed receipt can therefore satisfy a structural prerequisite on the promotion path.
3. `promote_branch_to_main()` applies removals and copies the branch snapshot over main without comparing the current parent to the branch's recorded parent revision. A stale branch can overwrite newer canonical work.
4. Promotion and recovery writes are not enclosed by a cross-process lock or a transaction boundary.
5. The tool is anchor-and-rebuild recovery, not a semantic merge of two competing timelines. It can select a trusted timeline and redraft affected scope; it cannot prove that two independently authored timelines have been reconciled into one coherent canon.
6. Semantic recovery review is explicitly diagnostic/deferred in the implementation. Structural validation is not proof of story-level continuity.

Conclusion: the recovery stack is useful design evidence and may contain reusable diagnostics, but it is unsafe to run against the completed contaminated book or transplant wholesale into main.

## Hotfix branch

Branch: `codex/book-writer-lock-hotfix`

Scope:

- Hold one non-blocking OS-level writer lock for the entire `run_loop` call.
- Scope the lock by book, so different books remain independent.
- Fail closed before provider setup or any scene/state mutation when another run owns the book.
- Store safe owner metadata (`pid`, hostname, operation, acquisition time) for diagnosis.
- Use unique run IDs even for two starts within one second.
- Restore hierarchical LLM logging as
  `logs/llm/<book>/<run>/<chapter>/<action>/...`, with retry/error grouping and
  collision-resistant event ids.
- Bind both status-log and LLM-log routing to the current execution context so
  concurrent runs for different books cannot cross-write each other's logs.
- Make reset/archive understand both the new recursive tree and all companion files
  from the legacy flat layout.
- Add isolated lock/integration tests without invoking a provider or generating prose.

Logging-path reality:

- Research commit `9daed528` introduced the useful book/chapter/action hierarchy and
  `19197553` refined retry/action grouping.
- That implementation still used second-resolution filenames, so repeated attempts
  could overwrite one another. It also omitted run correlation, left the active run
  log in a process-global variable, and cleared only legacy `.json` files in the
  book-scoped reset path.
- The hotfix reconstructs the hierarchy rather than cherry-picking those commits. It
  adds microsecond-plus-random ids, bounded Windows-safe path components, a run scope,
  context-local routing, atomic latest-run pointer replacement, recursive reset, and
  legacy `.json`/`.txt`/`.prompt.txt`/other companion cleanup.
- Seventeen focused filesystem, concurrency, archive, and lock checks pass without a
  provider call or generation run. The tracked UTF-8 BOM in
  `resources/prompt_blocks/phase/system_base/global_system_rules.md` was then repaired
  through its source fragment, manifest span, compiled template, trace, and expected
  checksum. Prompt composition validates all 14 templates, and the full offline suite
  passes 123 tests.

Deliberate limitations:

- The hotfix serializes whole runs. It favors safety over throughput.
- It protects the production `run_loop`, which is the path involved in the incident. It does not claim that every helper capable of writing a file is transaction-safe.
- It does not repair an already contaminated book.
- It does not add optimistic concurrency to the unmerged recovery stack.

## Prompt/code coupling is a first-class architecture boundary

Prompts are executable interfaces in this project. The migration unit is therefore
not a prompt file, schema file, parser function, or retry loop in isolation. It is a
versioned `PromptContractBundle` containing all of the following:

- action ID and contract version;
- canonical source-block/manifests and compiled prompt hash;
- declared placeholders plus the input/context schema and assembly budget;
- output envelope and JSON Schema version;
- extractor/parser and any deterministic normalization rules;
- semantic validators that go beyond JSON Schema;
- failure taxonomy and the exact bounded retry/repair prompt for each repairable class;
- provider output-mode and continuation requirements;
- persisted artifact schema and `PromptContractRef` shape;
- positive, negative, truncation, stale-input, and retry fixtures.

Every `ThoughtArtifact`, staged `WriteBundle`, lint/repair artifact, and commit receipt
must carry the exact `PromptContractRef` used to create it. The reference includes the
action ID, contract version, compiled prompt hash, input schema version, output schema
version, parser/validator version, provider/model capability profile, and source hashes.
A write or repair action fails closed if its input artifact was produced under an
incompatible contract.

### Branch evidence and consequence

- The research branch changes 20 canonical prompt blocks, adds 12 outline composition
  manifests and 14 action templates, and changes six schema surfaces.
- Its workspace initializer copies the new outline templates and outline phase specs
  invoke them directly, but `resources/prompt_registry.json` does not register those
  outline phases. This is concrete registry/runtime drift.
- State-patch repair wording is partly centralized in `pipeline/llm_ops.py`, while
  write, repair, state-repair, preflight, and plan retain separate parse/retry loops.
  A wording or schema fix can therefore land in one phase and miss another.
- The outline pipeline has valuable prompt constraint work, but its roughly 2,460-line
  validator module and multiple 04a/04b/04c/04d handoffs mean no prompt can be judged
  independently of handoff keys, schema checks, normalization, and downstream phases.
- Existing mainline forensics classify `write`, `repair`, `state_repair`,
  `system_base`, and `output_contract` as high/critical risk and already map runtime
  consumers and canonical shared blocks. That evidence remains part of the review set.

Conclusion: prompt engineering from `phase-runner-changes` is valuable migration
evidence, not disposable branch noise, but it must be reconstructed action by action
with its complete contract bundle. A prompt-only cherry-pick is prohibited.

### Contract drift gates

For each action, one offline gate must prove:

1. Registry, workspace distribution, phase/action lookup, and composition manifest
   name the same template and contract version.
2. Every placeholder required by the compiled prompt is declared and supplied; no
   undeclared runtime injection can silently alter the contract.
3. Valid examples in the prompt validate against the actual JSON Schema and semantic
   validator; invalid examples fail for the documented reason.
4. Parser/extractor fixtures accept every documented envelope and reject prose,
   duplicate blocks, extra data, or partial JSON when the contract forbids them.
5. `transport`, `empty_response`, `generation_budget_exhausted`, `json_syntax`,
   `schema`, `semantic`, and `stale_input_contract` failures remain distinct. Each
   retryable class maps to one explicit bounded repair action and artifact.
6. Canonical source blocks are the only hand-edited prompt source. Compiled templates,
   traces, checksum files, and book-local copies are generated and drift-checked.
7. A book-local prompt override declares its parent contract and is rejected when its
   schema/parser/validator versions no longer match the running action.

Prompt phrasing, ordering, examples, and negative instructions are behavior. Golden
fixtures may assert required/forbidden clauses and compiled hashes, but hashes alone
do not prove semantic alignment; contract fixtures and consumer tests are mandatory.

### Prompt extraction review sequence

For each action, review and migrate in this order:

1. Freeze the current mainline prompt, schema, parser, validator, retry behavior, and
   fixtures as the baseline contract.
2. Diff the research branch's canonical prompt blocks and code consumers against that
   baseline; record every retained clause with source commit/path provenance.
3. Classify each delta as schema-required, parser-required, semantic guardrail,
   provider-specific instruction, repair instruction, quality guidance, or obsolete
   workaround. Quality guidance is preserved unless it contradicts the new boundary.
4. Define the new action's input and output schemas before editing prompt prose.
5. Reconcile prompt examples and repair messages against the actual parser and
   validators, then generate the compiled prompt and contract reference.
6. Pass offline positive/negative/drift fixtures before implementing provider-backed
   execution or moving to the next action.

Extraction order is section-outline think/write, scene think/write, staged scene
lint/repair, then chapter-seam think/write/lint/repair. Cross-cutting state-patch rules
are introduced as shared versioned blocks only when all consuming action bundles move
together; until then they remain duplicated but contract-tested to avoid partial drift.

## Migration policy

### Reconstruct on the next branch

- A chapter/section spine that can exist before scene detail.
- Just-in-time expansion of exactly one target scope.
- Explicit scene, section, and chapter work-unit references.
- Immutable thought/decision artifacts bound to an input revision.
- A separate write action that consumes one exact thought artifact.
- Versioned prompt-contract bundles for every think, write, lint, and repair action.
- Staged output plus compare-and-swap commit.
- Pairwise chapter-seam lint and repair as a required chapter-finalization gate.
- Lineage hashes and non-mutating contamination diagnostics.

### Re-evaluate as small independent patches

- Cooperative provider retry/fail-fast behavior from the preserved WIP.
- Closed-enum seam prompt corrections, bounded-window heuristics, and deterministic
  seam checks after they are separated from the research branch's mutation path.
- Research-branch prompt clauses and repair examples, but only after mapping each one
  to its schema, parser, validator, failure class, and focused fixtures.
- Read-only lineage reports whose dependencies can be reduced to mainline contracts.

These should be manually reconstructed with focused tests. Literal cherry-picks are acceptable only if a patch has no dependency on the supervision, action, branch, recovery, or generated-workspace layers.

### Do not port

- Generated books, logs, test workspaces, or runtime receipts.
- The expanded CLI/action surface as a block.
- Promotion code without parent-revision compare-and-swap.
- Recovery health logic that treats failed receipts as completed work.
- Compatibility wrappers whose only purpose is to bridge intermediate commits on the research branch.
- Generated prompt templates or checksum/report artifacts copied without their
  canonical source blocks and contract tests.

## Exact extraction nucleus

Reconstruct this lifecycle in order. Each numbered item is an independently
reviewable contract or action; no step may silently absorb the next one.

1. `PromptContractBundle` and `PromptContractRef` for one named action, including the
   source/compiled prompt hashes, input/output schemas, parser/validator versions,
   repair mapping, provider capability requirements, and offline fixtures.
2. `WorkUnitRef` for exactly one scene, section, or chapter, including book ID,
   canonical revision, outline-slice hash, and declared read/write set.
3. Convert `BookIntent` into a persisted chapter/section spine without requiring
   scene prose or a fully expanded scene outline.
4. `ThinkSectionScenes` reads one section spine under one prompt-contract reference
   and persists an immutable thought artifact plus provider continuation. It does not
   mutate the outline or write prose.
5. `WriteSectionScenes` consumes that exact thought artifact, continuation, and a
   compatible write contract, then stages the section's scene outline. It cannot
   re-plan outside the section.
6. `FreezeSection` validates and commits the staged scene outline for one section.
7. `ThinkScene` reads the frozen section slice and persists one immutable scene
   thought artifact plus provider continuation.
8. `WriteScene` consumes that exact scene thought/continuation pair under a compatible
   prompt contract and stages prose and state for one scene.
9. `LintRepairStagedScene` works only on the staged scene bundle. Lint and repair use
   separate declared contract bundles; neither can mutate canonical prose, and every
   attempt emits its own evidence.
10. `CommitWorkUnit` acquires the book lock and performs compare-and-swap against the
    expected canonical revision and source hashes before promoting staged files.
11. `NextTargetQuery` is read-only and returns no more than one actionable scene,
    section, chapter-seam pair, or chapter-finalization target.
12. `LockSection` verifies that every scene in the section has a successful commit
    receipt for the frozen section hash. It performs no provider calls.
13. `RepairChapterSeams` is mandatory after all chapter sections are locked. It
    processes one adjacent scene pair per think/write cycle and commits only a
    bounded seam patch under chapter-level CAS.
14. `FinalizeChapter` only assembles committed scene revisions after every seam for
    the current chapter revision has passed. It performs no provider calls.

The sequence deliberately makes section locking, seam repair, and chapter
finalization separate actions. Locking the last section must not automatically
start an unbounded provider loop.

## Two-turn reasoning continuity is a correctness requirement

This is not only a prompting preference. Reasoning tokens share the generated-token
budget with visible output. On sufficiently large story context and planning scope,
a model can spend the response budget reasoning and reach `max_output_tokens` before
it emits usable prose or structured output. The authoring architecture therefore
requires a fresh response for execution after planning completes.

Track two different exhaustion modes:

- `context_window_exhausted`: input, retained conversation items, available reasoning
  state, and the new response cannot fit the model context window. Work-unit slicing,
  bounded prompt assembly, and explicit compaction address this ceiling.
- `generation_budget_exhausted`: the current response spends `max_output_tokens` on
  reasoning and formatting before it emits the required visible artifact. The
  persisted think response plus fresh write response addresses this ceiling.

A turn boundary does not excuse an oversized input context, and context trimming
must not discard the exact continuation items required by the provider.

The handoff has two distinct artifacts:

1. `ThoughtArtifact`: provider-neutral, inspectable planning decisions, constraints,
   source hashes, work-unit identity, expected revision, and exact think-contract ref.
2. `ProviderContinuation`: opaque provider-native response items needed to preserve
   the model's reasoning state. It is bound to provider, model/snapshot, response ID,
   work-unit ID, and source hashes, and it must be replayed without modification.

The semantic artifact is the durable audit contract; it is not a substitute for the
opaque continuation. The opaque continuation preserves model reasoning; it is not
portable evidence and must never be interpreted as canonical story state.

Provider rules verified against current documentation on 2026-07-15:

- OpenAI Responses should use `previous_response_id` with a supported persisted-
  reasoning mode, or replay all prior response output items. For stateless/ZDR use,
  preserve and replay the encrypted reasoning items exactly. Raw reasoning text is
  not exposed. See the [OpenAI reasoning guide](https://developers.openai.com/api/docs/guides/reasoning).
- Gemini is stateless unless conversation state is carried. Preserve the complete
  model parts and every `thoughtSignature` exactly as returned; do not merge or
  reconstruct signed parts. See the [Gemini thought-signature guide](https://ai.google.dev/gemini-api/docs/generate-content/thought-signatures).

If the selected provider/model cannot carry compatible reasoning state between the
think and write responses, the high-context authoring action must fail capability
validation rather than silently fall back to a single overflowing response.

### Reality of the research branch's continuation support

There is useful partial implementation to study:

- The Gemini client preserves the complete returned content `parts` array.
- LLM logging writes those assistant parts, extracts `thoughtSignature` values, and
  maintains signature ledger/index files.
- Several two-turn phases replay the in-memory T1 parts into a Gemini T2 request.
- The signature tests verify logging, intent/outcome indexing, purging, and metadata
  extraction.

It is not yet the required cross-provider contract:

- The OpenAI client uses Chat Completions and treats returned text as assistant
  parts. It does not retain Responses API response IDs, reasoning output items, or
  encrypted reasoning content, and its `thinking_level` argument is unused.
- Replay is explicitly Gemini-only and scattered through phase implementations.
  It is not resolved through one exact `ProviderContinuation` bound to a
  `ThoughtArtifact`, work-unit ID, and source hashes.
- The `current_thoughts` helper may fall back to the globally latest signature and
  asks a new model call to reconstruct a summary. That is a diagnostic convenience,
  not proof that a write consumed the thought state for its exact input revision.
- Existing signature tests do not submit a preserved continuation through the real
  provider adapter and do not verify that T2 rejects a missing, reordered, stale,
  wrong-model, or wrong-work-unit continuation.

Extraction should therefore reuse the knowledge and fixture shapes, not transplant
the ledger/active-signature selection behavior as the authoring authority.

## Chapter seam repair: retain the capability, replace the implementation

### What is real and worth extracting

- The latest research-branch implementation can target one adjacent scene pair
  rather than rewriting an entire chapter in one operation.
- Its writable input is conceptually limited to the last two paragraphs of Scene A
  and the first two paragraphs of Scene B.
- It combines deterministic boundary checks with model linting and retains
  original, fixed, and final evidence.
- It separates thinking and execution into two provider calls. That fresh second
  response is the behavior that protects the repair output budget.
- It refuses to promote a candidate when the deterministic post-repair audit still
  contains an error.

### Why the branch implementation is not portable

1. T1 is not a durable thought artifact. Its parsed JSON is discarded. Only Gemini
   assistant parts are conditionally replayed into T2; other providers execute T2
   without consuming the semantic result or provider reasoning state from T1.
2. Both turns use a default 67,000-token output allowance, and the default repair
   loop permits eight passes. A persistently failing pair can make 32 provider calls
   (lint T1/T2 plus repair T1/T2, eight times). A ten-scene chapter can reach 288
   calls across its nine seams.
3. The supposedly bounded pair payload also includes the full text of both scenes,
   duplicating the boundary windows and expanding the input envelope.
4. The replacement function limits the input window to two paragraphs but accepts
   an arbitrary number of output paragraphs. The declared write boundary is not
   enforced on model output.
5. The last-section lock calls chapter finalization synchronously, so a small state
   transition can unexpectedly launch the entire provider-backed seam loop.
6. Repaired scene files, chapter markdown, registry fields, and reports are written
   directly and sequentially with no book lock, revision CAS, or transactional
   promotion. A failure or competing writer can leave mixed revisions.
7. The focused chapter-seam tests replace the provider-backed pair loop with stubs,
   while the adaptive-action test replaces the seam implementation itself. They
   prove some artifact and branch-routing behavior, not the real two-turn repair
   path, truncation behavior, or atomicity.

### Replacement seam contract

Treat a seam as a bounded child target of one chapter `WorkUnitRef`:

```text
ChapterSeamRef = chapter_work_unit + scene_a_ref + scene_b_ref
                 + scene_a_hash + scene_b_hash + boundary_window_hash
```

For each adjacent pair:

1. A read-only deterministic lint decides whether the pair needs model review.
2. `ThinkChapterSeam` receives bounded windows plus frozen scene/section/chapter
   intent summaries. It persists both a `SeamThoughtArtifact` and the exact provider
   continuation; it receives no duplicate full-scene text and writes no prose.
3. `WriteChapterSeam` runs as a fresh response and consumes that exact thought and
   continuation. It stages replacement windows only.
4. A structural validator rejects empty output, unexpected fields, paragraph/word
   expansion beyond configured limits, or any attempted change outside the two
   declared windows.
5. Deterministic and model lint run against the staged splice. Retries are explicit,
   small, and create new artifacts; they are never an invisible loop.
6. The book lock is acquired only for a short CAS commit. The commit verifies the
   chapter revision and both source scene hashes, promotes the two staged windows,
   writes the seam receipt last, and releases the lock.
7. A stale or failed candidate remains inspectable and non-canonical. It is never
   automatically merged or used to finalize the chapter.

The initial implementation should cap repair attempts at two and process only one
pair per command. A later policy may increase those bounds, but only with measured
provider and failure evidence.

## Next branch architecture

Proposed branch after the hotfix is accepted: `codex/turn-scoped-authoring`

### Invariant 1: think in one turn

A think action:

- Reads one immutable baseline revision.
- Targets exactly one `scene`, `section`, or `chapter` work-unit reference.
- May expand outline detail only inside that target.
- Emits an immutable `ThoughtArtifact` containing assumptions, intent, constraints, source hashes, and the expected parent revision.
- Persists the complete provider-native continuation needed by the next response,
  including opaque reasoning items, signed content parts, or response linkage as
  supported by that provider/model.
- Does not write prose or mutate canonical outline/state.

### Invariant 2: write in the next turn

A write action:

- Requires one exact `ThoughtArtifact` ID.
- Requires and validates the matching `ProviderContinuation`; it may not substitute
  a prose summary or silently start an unrelated model conversation.
- Starts a fresh provider response so planning cannot consume the write response's
  generated-token budget.
- Writes only the selected work unit.
- Cannot silently re-plan the chapter or expand adjacent scope.
- Emits a staged prose/state bundle and validation result.
- Does not become canonical until commit succeeds.

### Invariant 3: one explicit work boundary

Every action carries a `WorkUnitRef`:

```text
book_id + branch_id + unit_kind + chapter + optional section + optional scene
```

Rules:

- Scene is the default atomic prose/state commit.
- Section work may coordinate its scenes, but its read and write set cannot escape the section.
- Chapter work may assemble or validate its sections, but it cannot mutate another chapter.
- A command that needs broader scope must declare a new work unit; it may not widen scope during execution.

### Invariant 4: inline outline, frozen write input

1. Store the chapter and section spine.
2. Expand only the selected unit just before authoring.
3. Freeze the resulting outline slice and hash it.
4. Think against that frozen slice.
5. Write against the thought artifact and same slice hash.
6. Reject commit if the canonical revision or slice hash changed.

### Invariant 5: short commit, durable evidence

Provider calls happen outside the canonical commit section. Commit then:

1. Acquires the book writer lock.
2. Compares the expected parent revision, cursor, and outline-slice hash.
3. Writes staged files through temporary paths.
4. Replaces canonical files in a declared order.
5. Writes the commit receipt last.
6. Advances the canonical revision.
7. Releases the lock.

If compare-and-swap fails, the staged result remains non-canonical and inspectable. It is never auto-merged.

### Invariant 6: prompt contract closure

- No provider-backed action is implemented until its complete `PromptContractBundle` exists.
- Think and write are separate action contracts even when they share source blocks.
- Retry and repair are explicit child contracts, not hidden prompt concatenation.
- Prompt, schema, parser, semantic validator, retry mapping, and fixtures change in
  the same reviewable patch.
- Contract compatibility is checked before provider work and again before commit.
- A generated template or book-local override can never become the silent source of truth.

## Implementation slices

1. **Contract inventory and gates** - freeze the mainline prompt/code baseline; map
   each research-branch prompt clause to its action, schema, parser, validator, repair
   path, and fixtures; implement registry/composition/placeholder/example drift checks.
2. **Foundational contracts** - `PromptContractBundle`, `PromptContractRef`,
   `WorkUnitRef`, `ThoughtArtifact`, `ProviderContinuation`, `WriteBundle`,
   `CommitReceipt`, revision/hash rules, and schema tests.
3. **Book-intent spine** - persisted chapter/section structure with no eager scene prose.
4. **Read-only selection** - resolve and render one scene/section/chapter slice without mutation.
5. **Provider continuation adapters** - exact OpenAI reasoning-item/response linkage
   and Gemini signed-part replay, capability-gated by provider and model.
6. **Section think/write/freeze** - reconstruct the paired section prompt contracts,
   then implement persisted `ThinkSectionScenes`, fresh-response `WriteSectionScenes`
   consuming the exact thought/continuation pair, and provider-free freeze.
7. **Scene think/write** - reconstruct separate scene think/write contract bundles,
   then implement persisted `ThinkScene`, fresh-response `WriteScene`, and staged output only.
8. **Staged lint/repair** - reconstruct lint and repair contract bundles and operate
   only on the selected staged work unit with explicit bounded repair artifacts.
9. **Commit action** - book lock plus compare-and-swap and failure receipts.
10. **One-target query and section lock** - select one next unit and lock a section without provider work.
11. **Chapter seam gate** - reconstruct seam think/write/lint/repair bundles, process
    one adjacent pair per persisted think/write cycle, bounded staged splice, and locked CAS commit.
12. **Chapter finalization** - provider-free assembly from committed scenes after
    current-revision seam receipts pass.
13. **Diagnostics** - lineage and contamination reports, still read-only.
14. **Recovery redesign** - only after commit/CAS invariants exist;
    successful-receipt gates and stale-parent rejection are mandatory.

Each slice should be independently reviewable. Provider-backed story generation is
not required to validate slices 1, 2, 3, 4, 9, 10, 12, or 13. Continuation adapters need
recorded fixture/eval coverage but not a live book-generation run.

## Completed contaminated book

- Preserve the completed manuscript and every source artifact as immutable evidence.
- Do not promote, normalize, or redraft it with the current research-branch recovery implementation.
- Build an offline timeline inventory and hash manifest first.
- Identify trusted chapter/section anchors with human review.
- Treat contaminated prose as `reference_only` unless a later recovery action explicitly selects and validates it.
- Perform salvage on a derived copy/branch after the new commit/CAS model exists.
- Keep the original completion untouched so every salvage decision remains reversible.

## Exit criteria

The project is ready for a controlled salvage attempt only when:

- Two same-book writers cannot overlap.
- Different-book runs cannot cross-route status or LLM logs, and two rapid events
  cannot overwrite each other.
- Every provider-backed action has a versioned prompt-contract bundle whose prompt,
  schema, parser, semantic validator, repair mapping, and fixtures pass as one unit.
- Registry, composition manifest, workspace copy list, and runtime action resolution
  cannot drift without an offline test failure.
- Think and write artifacts are separately addressable and immutable.
- Every high-context think action persists both an inspectable semantic artifact
  and an exact provider-native continuation bound to the same work unit and hashes.
- Every corresponding write action starts a fresh response and consumes both; it
  fails closed when the provider/model cannot preserve compatible reasoning state.
- Every write declares exactly one work unit.
- Stale commits and stale promotions fail closed.
- Locking the final section performs no provider calls.
- Chapter seam repair operates on one adjacent pair at a time, enforces a bounded
  output splice, and cannot finalize from stale or failed seam evidence.
- Chapter finalization performs no provider calls and assembles only committed
  scene revisions covered by current-revision seam receipts.
- Only successful/no-op receipts satisfy recovery prerequisites.
- The recovery path never mutates the sole copy of the completed book.
- Structural validation and semantic/human review are reported as separate gates.
