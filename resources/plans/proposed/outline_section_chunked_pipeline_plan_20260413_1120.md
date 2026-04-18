# Section-Chunked Outline -> Insert -> Seam -> Write Plan

Status: In Progress
Date: 2026-04-13
Owner: BookForge Outline/Writing Pipeline

## Active Plan State (2026-04-18)
Current status:
- The section workflow is real and has been exercised on live book data.
- The writer-side phases already use a real two-turn pattern (`T1` think, `T2` execute).
- On the Gemini path, `T2` already receives the prior `T1` assistant parts inside the same phase call chain.
- That carry is still implicit runtime behavior, but the next step should stay minimal: verify and preserve the existing carry contract rather than building a second redundant parent-signature graph unless logs prove it is necessary.
- The next major workflow gap is chapter assembly quality, not section production.

What is proven:
- Section-level `stub -> frozen -> locked` advancement works on live workspaces.
- The system retains full canonical state while only mutating one active section at a time.
- Resume/retry behavior is strong enough for long-running section advancement.

What is now blocking:
- Chapter assembly currently recompiles by concatenating locked scene markdown.
- That reintroduces merge-layer seam artifacts that do not show up at scene or section scope:
  - tense breaks
  - scaffold leakage
  - duplicated beats
  - redundant item re-grounding
  - factual contradictions across section joins
- repeated restart energy where a new scene restates the close of the previous scene instead of flowing forward
- overlap-heavy joins where the opening of scene N+1 partially rewrites the ending of scene N
- Thought signatures are already doing real work; the concern is not lack of signatures, but making sure we do not build duplicate machinery around what the assistant-parts/signature system already gives us.

Immediate next work:
- Verify/preserve the existing `T1 -> T2` carry contract in the writing loop with the lightest instrumentation that gives us confidence.
- Increase default lint/repair loop depth from `2` to `8`.
- Add a chapter seam audit/repair/finalization layer after the last section in a chapter is locked.
- Treat configured model selection as authoritative; do not use runtime model overrides as a throughput workaround.
- Keep writable operational data architecture flexible, with a bias toward a separate writable-data repo/workspace rather than an in-repo `app/data` split.

Progress since this state snapshot:
- Default lint/repair pass depth has been raised to `8`.
- Writer-side `T2` logging now records whether it reused the prior Gemini response-content array, including count/hash/signature metadata, without building a second signature lineage system.
- A chapter seam finalization path now exists:
  - final section lock can trigger chapter seam audit/repair/finalization
  - `workflow finalize-chapter` can backfill existing locked chapters
  - Chapter 1 in `criticulous_the_rng_hellscape` has already been finalized through this path
- The current chapter seam implementation is deliberately conservative and deterministic:
  - it removes scaffold-like seam paragraphs
  - trims overlap-heavy opening sentences at joins
  - emits a chapter seam report and only promotes `ch_XXX.md` when error-class seam issues are cleared
- Full chapter state-delta validation at finalization time is still pending; current finalization is a seam-quality gate, not yet a full semantic/state gate.

## Progress Update (2026-04-17)
Implemented and proven in the repo/workspace:
- Transitional `workflow` CLI surface exists:
  - `workflow init`
  - `workflow status`
  - `workflow freeze-section`
  - `workflow lock-section`
  - `workflow advance-section`
- Canonical workflow artifacts now exist and are maintained:
  - `outline.json`
  - `snapshot_registry.json`
  - `outline.thin.json`
  - `outline.toc.json`
  - `outline.index.json`
  - `outline.appendix.json`
  - per-section boundary artifacts
- Full end-to-end lifecycle has been proven for one real section in `criticulous_the_rng_hellscape`:
  - Chapter 1, Section 1 moved `stub -> frozen -> locked`
  - prose and meta were generated for all section scenes
  - state cursor advanced to the next expected scene
- Chapter 1, Section 2 has also been exercised far enough to prove the next real runtime failure class:
  - scenes 4 and 5 completed under the new workflow
  - scene 6 exposed a real `state_patch` normalization/schema bug in live writer execution
  - this confirms the remaining gap is now inside downstream write/state handling, not the section workflow surface itself
- Chapter 1 is now fully section-locked end to end:
  - Section 3 completed under the workflow
  - Section 4 completed under the workflow
  - cross-section and chapter-rollup behavior have now been exercised beyond the bootstrap section
- Chapter 2, Section 1 is now frozen and locked under the new workflow:
  - this proves cross-chapter boundary handoff is viable
  - this also proves the dynamic section-draft fallback is viable once section-scoped validation accepts mixed-state chapter payloads
- Chapter 2, Section 2 is now frozen and locked under the new workflow.
- Chapter 2, Section 3 has been frozen and partially advanced under the new workflow:
  - the active section is resumable after shell/provider timeouts
  - the dominant issue at this point is runtime duration, not a new correctness defect

Still open:
- section drafting must become first-class so the workflow does not depend on pre-existing chapter draft artifacts
- deeper outline phase refactor (native section-scoped 03/04A/04B/04C/04D/05/06) remains in progress
- writer/runtime model policy should explicitly support mixed-cost execution such as high-reasoning planning with cheaper execution
- chapter seam finalization is not yet first-class; chapter compilation is still too close to plain concatenation
- lint/repair diagnostics still live in a noisy artifact surface and need a clearer operational summary path

Operational findings from the first live section runs:
- The section workflow is now real enough to expose downstream defects under production-like execution instead of only outline-only artifacts.
- The current speed/cost workaround is temporary env-level model overrides. The intended steady-state policy is explicit turn-aware model routing, likely allowing higher-reasoning T1 planning with cheaper T2 execution where safe.
- Live failures must now be classified into three buckets during section advancement:
  - transport/provider failures (`503`, dropped connections)
  - token-budget failures (`MAX_TOKENS`, truncated JSON/prose)
  - real pipeline defects (schema mismatch, normalization gaps, apply-time invariants)
- Long-running workflow commands must use long timeout windows. Runtime duration is a real characteristic of the correctness-constrained pipeline, not evidence that the configured model should be overridden ad hoc.
- Workflow command wrappers and test scripts should default to multi-hour timeout windows when driving real book generation; one-hour retry loops are operationally wrong for this system.
- The configured model stack in workspace/env is authoritative. Future workflow automation must not silently or opportunistically replace it in order to chase throughput.
- Resume behavior is now part of the operational contract:
  - long-running section advancement may legitimately time out at the shell/process boundary even when the workflow itself is healthy
  - resumable progress has been proven across a partially completed frozen section
  - the workflow wrapper can now be treated as restart-safe for live advancement, not just outline bootstrap
- Progress should continue section by section under the workflow wrapper, with plan updates reflecting each newly discovered defect class and each newly proven lifecycle stage.

Concrete fixes completed during live workflow execution:
- `state_patch` normalization now converts object-style continuity removals into schema-valid string-array remove operations.
- continuity bag application now supports targeted list-item removal semantics (for example, removing a single status by name rather than dropping the whole list).
- section-scoped phase 03 validation no longer rejects a single-chapter subset just because the local payload chapter id is not `1`.
- mixed-state section validation now allows later sections to remain explicit `stub` sections with empty scene arrays during active section drafting.
- section-scoped phase 03 `T1` is now non-fatal when the provider ignores the small planning contract and emits malformed/truncated content; the workflow proceeds to `T2` instead of aborting on advisory planning output.

## Summary
Shift the pipeline from chapter-sized outline execution to section-sized chunks so outline drafting, seam insertion, seam repair, and prose writing happen in smaller, cheaper, and more stable units. Keep a thin global outline view available at all times, but only thicken the active section chunk while it is being worked.

This plan is intended to reduce the blast radius of outline failures, lower token pressure, and make output available earlier without abandoning the current phase doctrine.

## Decisions (Locked)
1. Chunk granularity: sections.
2. Section reopening: no automatic reopen of written sections.
3. Insertion budget scope: per section.
4. System prompt context: keep thin by default; transmit detailed local data per phase.
5. Maintain multiple outline views continuously:
   `outline.thin.json`
   `outline.toc.json`
   `outline.index.json`
   `outline.appendix.json`
6. Execution order is forward-only by section; no out-of-order section drafting in v1.
7. Only one active section may be draftable at a time in v1; no parallel section execution.
8. Phase 05 and Phase 06 remain active and run section-scoped before S3 freeze.
9. The configured model stack for a run is authoritative; workflow code must not silently override it in order to chase throughput.
10. Final chapter promotion requires a chapter seam audit/repair gate after the final section lock.
11. Default lint/repair pass depth target is `8` unless runtime evidence justifies a lower configured value.

## Doctrine Alignment
- LLM authors semantics; orchestrator routes and enforces deterministic invariants.
- No deterministic semantic healing; deterministic normalization is allowed only when truth is unambiguous.
- No silent drops of model-created data.
- Active work happens in bounded section windows, not whole-book rewrites.

## Canonical State Retention
The canonical book state is never reduced or discarded.

Rules:
- Scope reduction applies to mutation rights and prompt/context weight, not to durable state retention.
- `outline.json` remains the merged canonical outline for downstream compatibility.
- Frozen and locked sections remain fully present in canonical outline, registry, boundary, prose, and state artifacts.
- Only the active section is exposed as the thick mutable working set for outline and prose operations.
- Prior sections are read-only continuity context.
- Future sections remain explicit stubs until drafted.

## Core Terms
Draftable
- The active section can still be outlined, inserted into, renumbered locally, and seam-repaired.
- Draftable is the persisted execution state for the active section during S2 and all pre-freeze refinement passes.

Frozen
- The section outline is structurally clean and ready for prose generation.
- Scene order and scene refs for that section are now fixed for downstream writing.
- This is the S3 boundary.

Locked
- The section has been written, state-repaired, linted, and committed.
- No automatic mutation is allowed after this point.
- This is the S4 boundary.

## Snapshot Model
S0 - Spine (Thin)
- Chapters only: `chapter_id`, `title`, `goal`, `bridge`.
- Used in system prompts and high-level navigation.

S1 - Sections (Thin-Mid)
- Chapters plus section stubs.
- No scene bodies outside the active section.

S2 - Drafted Section (Local Thick)
- One active section contains full scene cards.
- Other sections remain stubs.
- This is the draftable state.

S3 - Frozen Section (Local Thick, Seam-Clean)
- Active section has passed insertion, relink, and seam hygiene.
- Active section has also passed cast/thread refinement (05/06).
- Section outline is now canonical for writing.

S4 - Locked Section (Written)
- Prose exists, state has been updated, and the section is immutable to automatic passes.

## Section Stub Contract
Non-active sections must not be vague placeholders. They must use a precise stub shape so prompts keep a stable outline schema without inviting hallucinated content.

Minimum stub shape:

```json
{
  "section_id": 2,
  "title": "The Gate Check",
  "intent": "Move Artie from town arrival into social danger.",
  "end_condition": "Artie is publicly flagged as an anomaly.",
  "status": "stub",
  "scenes": []
}
```

Rules:
- `status: "stub"` is required for non-active sections while the chunk is local-only.
- Stubs are read-only navigation context.
- Stubs must never be treated as writable prose-bearing sections.
- The terminal scene's `end_condition_echo` must exactly match the section stub's normalized `end_condition`.

## Pipeline Flow (Per Section)
1. Select next section from the global outline.
2. Build active section context:
   - thin global outline
   - previous section boundary seam
   - next section stub
   - local registries and state slices
3. Phase 03 drafts scene cards for the active section only.
4. Phase 04A analyzes seams inside the active section.
5. Phase 04B inserts required micro/full scenes inside the active section.
6. Phase 04C relinks structural metadata inside the active section.
7. Phase 04D repairs seam metadata and splice-successor drift inside the active section.
8. Phase 05 refines cast function inside the active section.
9. Phase 06 refines thread payoff inside the active section.
10. Freeze section at S3.
11. Run the writing loop for the frozen section.
12. Promote registries/state and lock section at S4.
13. Advance to next section.

## Chapter Finalization Flow
Section correctness is necessary but not sufficient. A chapter assembled from individually good locked sections can still expose merge artifacts.

After the final section in a chapter reaches S4:
1. Assemble provisional chapter markdown from the locked scenes/sections.
2. Run chapter seam audit on the assembled chapter.
3. If seam issues are found, run chapter seam repair scoped to seam neighborhoods and merge artifacts only.
4. Validate the repaired chapter against the expected chapter state delta and continuity contract.
5. Promote the chapter as finalized only if:
   - seam audit passes
   - chapter state delta remains valid
   - no forbidden edits escaped seam-local scope

This is not cross-chapter linting. It is chapter-finalization quality control over artifacts introduced by section assembly.

Priority seam classes for this pass:
- restart energy where scene N+1 restates the close of scene N instead of advancing
- overlap-heavy joins where adjacent scenes partially duplicate the same beat
- tense blending introduced by assembled scene boundaries
- scaffold leakage and scene-card style summary lines in final prose
- repeated re-grounding of persistent items/entities purely because they remain present in state

## Transitional Workflow Surface
The first implementation cut does not require an immediate full rewrite of every outline phase into native section-scoped execution.

Transitional rules:
- The new primary user-facing surface is a section workflow layer that links outline freeze -> write -> lock.
- Legacy `outline generate` and `run` commands remain available as lower-level/batch tools.
- The workflow layer may initially freeze sections from already-generated chapter artifacts while the deeper phase refactor is in progress.
- This is acceptable as long as the canonical state, boundary artifact, freeze/lock semantics, and writer-facing section lifecycle are already enforced.

## Boundary Ownership
Section boundaries need explicit ownership so we do not violate the "no reopen" decision.

Rules:
- The active section is the only writable section.
- Adjacent sections are read-only continuity context.
- The seam between section N and section N+1 is owned by section N+1 once section N is frozen.
- Chapter boundaries are transparent to the handoff protocol: the last section of chapter K emits the boundary artifact consumed by the first section of chapter K+1.
- The previous section's terminal handoff is treated as canonical input.
- The new section must align its opening scene(s) to that canonical handoff.
- Automatic repair is not allowed to mutate a frozen or locked prior section just to make the new section cleaner.
- The only section with no prior boundary artifact is the first section of the book.

## Boundary Artifacts
Each frozen section emits a boundary artifact:

- `section_boundary_seam.json`

Minimum contents:
- section id
- chunk ref
- terminal scene ref
- terminal `transition_out_text`
- terminal `transition_out_anchors`
- terminal `location_end`
- closing constraint/handoff state

Optional continuity contents:
- unresolved immediate pressure
- active thread ids
- newly hot entity ids

Usage:
- When opening section N+1, the boundary artifact from section N is injected as authoritative continuity context.
- The first section of the book opens without a prior boundary artifact and uses book-level opening context instead.
- Section-level seam repair may inspect adjacent section boundary artifacts, but may only mutate the active section.

Pre-S3 gate:
- boundary artifacts must be validated before a section can freeze
- terminal `transition_out_anchors` must be present, sensory, and non-identical to terminal `transition_in_anchors`

## Canonical Ownership and Promotion
We need explicit truth ownership to avoid multiple layers claiming the same fact.

Scene chain truth
- Owned by active section scene order plus `consumes_outcome_from` and `hands_off_to`.

Intro truth
- Owned by earliest valid `introduces` in section/chapter scene data.
- Registry must synchronize to that truth.

Section completion truth
- Owned by the terminal scene carrying the section's `end_condition_echo`.

Location identity truth
- Owned by location ids.
- Labels are presentation and may be normalized against the ids.

Thread legitimacy truth
- Owned by the thread registry.
- Scene references must point to registered threads.

Boundary seam truth
- Owned by the previous frozen section's emitted boundary artifact.

Promotion timing
- S3: section outline becomes canonical for outline semantics.
- S4: section prose/state/registry updates become authoritative for downstream continuity.

## Registry Timing
Registry timing cannot be left implicit.

At S3
- Provisional registry updates are allowed for:
  - local index projection
  - prompt context for the next section
  - validation of scene references
- Section N+1 consumes S3-provisional intro/thread/location truth from section N; it does not wait for S4.

At S4
- Registry/state updates become authoritative.
- If provisional S3 data disagrees with written-state truth after S4, rebuild projections from the S4-authoritative state.

## Persistent Outline Views
These views are always maintained and are distinct from local chunk artifacts.

`outline.thin.json`
- Thin prompt-facing view.
- Chapters plus section stubs/status.
- No inactive scene bodies.

`outline.toc.json`
- Navigation view.
- Chapters, sections, status, expected counts, lock/freeze state.

`outline.index.json`
- Fast lookup/index view.
- Scene refs, section states, registry pointers, boundary artifact pointers.

`outline.appendix.json`
- Extended metadata view.
- Minimum contents:
  - report pointers
  - boundary artifact pointers
  - freeze/lock audit summaries
  - derived diagnostics

## View Update Contract
Global views must not drift through mid-stage partial updates.

Rules:
- `outline.json` promotes atomically at the same S3/S4 boundaries as the derived views.
- Persistent views update atomically at stage transitions only.
- No persistent view updates during active in-flight mutation inside S2.
- Update points are:
  - S3 promotion (frozen section outline committed)
  - S4 promotion (written section committed)

This avoids a writer or later phase reading a half-mutated global view.

## Scene Ref Stability
Scene ids and refs need stronger rules than the current chapter-wide flow.

Rules:
- Inside an active draftable section, local insertion may renumber only that active section.
- Scene ids are allocated strictly forward-only by section order within a chapter.
- Once the section reaches S3, scene refs in that section become immutable.
- Locked sections at S4 are fully immutable to automatic mutation.
- Earlier frozen/locked section refs must never be renumbered by later section processing.

Known ordering dependency:
- 04A analyzes the pre-insertion seam graph for the active section.
- 04B may insert and renumber inside the active section.
- 04C is responsible for reconciling any local ref changes introduced by 04B before 04D/05/06 consume the result.

## Prompt Shape Strategy
- Every phase still receives a consistent full-outline shape.
- Only the active section contains thick scene data.
- Non-active sections are explicit stubs.
- System prompts read `outline.thin.json` by default.
- Chunk-specific prompts receive:
  - active thick section
  - previous boundary seam
  - next section stub
  - relevant registries and state slices
- `outline.thin.json` is navigation context only; it is never the source of truth for the active section.

## Command and Help Surface Implications
The command model changes from "batch outline, then batch write" to linked section lifecycle transitions.

Primary workflow intent:
- bootstrap workflow state from outline artifacts
- freeze the next section into canonical outline state
- write the frozen section
- lock the written section
- advance forward

Implications:
- Outline and writing are no longer presented as isolated top-level stages for the primary workflow.
- User-facing docs must explain that only one section is writable at a time, while the full canonical book state remains retained.
- `run` becomes a lower-level scene loop that can still be called directly, but the preferred iterative path is the workflow wrapper.
- Partial chapter prose is valid transitional state; chapter compilation may be provisional until all chapter sections are locked.
- Final chapter promotion is not equivalent to raw section concatenation; it includes chapter seam audit/repair/finalize.

## Scope Boundaries
- Insertions occur only in the active section.
- Repair windows occur only in the active section.
- Phase 05 and Phase 06 may only mutate the active section in the chunked model.
- Boundary repair may inspect adjacent sections but may only mutate the active one.
- Written sections are immutable unless a manual repair mode is explicitly invoked.
- A section may legally have zero required insertions; 04B treats that as a valid no-op.
- Chapter seam repair may edit only seam neighborhoods and merge-layer artifacts after all sections are locked; it is not a back door to reopen scene-authoring scope.

## Relationship to Dynamic Lint/Repair
This plan is compatible with the dynamic outline lint/repair loop plan.

Interaction model:
- Deterministic lint still detects structural, identity, and seam issues.
- Router builds repair windows inside the active section.
- Cross-section issues are expressed through boundary artifact validation, not prior-section mutation.

## Compatibility Rule
`outline.json` remains the merged authoritative outline for downstream compatibility.

Implications:
- Existing readers that expect `outline/outline.json` keep working.
- Thin and derived views are additive projections, not replacements.
- The section-chunked system changes how `outline.json` is produced and advanced, not whether it exists.
- Future sections may remain as explicit stubs inside the merged outline until they are drafted/frozen.
- Existing readers must tolerate mixed-state chapters:
  - frozen/locked sections with scenes
  - stub sections with `status: "stub"` and `scenes: []`

## Artifacts (Per Stage)
- `outline_spine_v1.json` (S0)
- `outline_sections_v1.json` (S1)
- `outline_section_chunk_draft.json` (S2)
- `outline_section_chunk_seam_hygiened.json` (S3)
- `outline_section_chunk_written.json` (S4)
- `section_boundary_seam.json` (emitted at S3)

## Chunk Identity
`chunk_ref` is the stable string identity for an active section chunk.

Format:
- `ch{chapter_id:03d}_sec{section_id:03d}`

Usage:
- artifact names
- runtime keys
- thought signature scope
- snapshot registry entries

## State Transition Contract
The section lifecycle is explicit:

- `stub -> draftable -> frozen -> locked`

Rules:
- `stub` is the last committed state before active drafting begins.
- `draftable` is tracked in the snapshot registry while S2 and pre-freeze refinement are in progress.
- `outline.json` does not commit in-flight S2 mutations; it advances only on S3/S4 promotion.
- If a run fails before S3, the active section remains replayable from the last committed state plus local checkpoint artifacts.
- `frozen` means the section outline is canonical and scene refs are immutable.
- `locked` means written output/state has been committed and no automatic mutation is allowed.

## Crash / Resume Model
Section execution is resumable and idempotent before S3.

Rules:
- default resume granularity is the active section
- windowed phases may resume within-section from phase-local checkpoints
- if a phase cannot resume within-section, it reruns the active section from the last committed pre-S3 state
- this is legal because narrative truth is not committed until S3/S4

## Runtime Policy
The system is correctness-first on the scene/section critical path.

Rules:
- The write loop, lint/repair loop, and section workflow remain fundamentally serial across state boundaries.
- Long-running workflow commands must be given long enough timeout windows to complete naturally.
- Workflow automation and test harnesses should assume multi-hour execution windows for real multi-chapter/book runs.
- The configured workspace/env model selection is authoritative for the run.
- If future mixed-cost routing is introduced, it must be explicit configuration, not ad hoc command-level override.
- `T1 -> T2` execution in writer phases must preserve the planning carry from `T1` into `T2`; this is already true on Gemini via assistant-parts carry and should be verified with the smallest possible amount of additional instrumentation.

## Partial Chapter Compile Contract
Partially written chapters are valid workspace state, but not final compile units.

Rules:
- scene markdown and scene artifacts may exist for locked sections inside a partially written chapter
- chapter rollup summaries may be provisional while a chapter is incomplete
- chapter compile/export should treat a chapter as complete only when all of its sections are locked

## Snapshot Registry
Stage 4 in the previous draft needs to be explicit. The snapshot registry is the canonical record of committed section state.

Minimum registry responsibilities:
- section stage (`stub`, `draftable`, `frozen`, `locked`)
- boundary artifact pointer per section
- scene ref range for frozen/locked sections
- character/thread/location provisional promotion markers
- current inherited state pointer for the next active section

Minimum file set:
- `outline/snapshot_registry.json`
- `outline/outline.thin.json`
- `outline/outline.toc.json`
- `outline/outline.index.json`
- `outline/outline.appendix.json`

## Expected Code Touchpoints
This section records the likely implementation footprint based on the current codebase.

### 1. Outline Orchestrator
`src/bookforge/outline.py`

Change shape:
- Major refactor.
- Current orchestration is chapter-scoped for phases 03/04A/04B/04C/04D/05/06.
- Add a section-scoped execution path that can:
  - select the next active section
  - build S1/S2/S3/S4 snapshots
  - merge a section patch back into the merged global outline
  - emit boundary artifacts at S3
  - advance resume checkpoints by `chapter_id + section_id`
  - update persistent views atomically at S3/S4
- Add section artifact naming; current helpers are chapter-only.
- Add section merge invariants; current invariants protect only non-target chapters.

Specific current functions likely touched:
- `_chapter_artifact_prefix`
- `_chapter_artifact_name`
- `_merge_target_chapter_outline`
- `_validate_chapter_invariants`
- `_chapter_render_values`
- `_assert_chapter_scoped_template_contract`
- `_extract_chapter_patch_from_response`
- `_execute_chapter_scoped_step`
- `_save_final_outline`
- `_resolve_outline_payload_from_run`

Expected new helpers:
- generic chunk merge helper or a new `_merge_target_section_outline`
- section artifact/path helpers
- section resume cursor helpers
- atomic persistent-view writer

Implementation note:
- Do not keep expanding `outline.py` as a monolith. Add helper modules for chunking and snapshots.

### 2. Outline Context / Step Specs
`src/bookforge/phases/outline/context.py`

Change shape:
- Moderate change.
- Step ids can stay the same, but execution metadata needs section-scope support.
- Add section-aware selectors and, if needed, chunk-scope contract helpers.
- Extend validation/render contracts from chapter-only assumptions to section-aware ones.

Likely additions:
- section chunk identity helpers
- section handoff file naming conventions if we persist per-section handoffs
- optional section subset selector normalization

### 3. Outline Artifacts / Snapshot Helpers
`src/bookforge/phases/outline/artifacts.py`

Change shape:
- Moderate change or split into a new helper module.
- Today this module mostly manages run ids and report/history pointers.
- It should either grow or be complemented with helpers for:
  - snapshot registry read/write
  - persistent view read/write
  - section boundary artifact paths
  - section chunk artifact names
  - atomic promotion at S3/S4

Recommended new module if kept separate:
- `src/bookforge/phases/outline/snapshots.py`

### 4. Outline Validators
`src/bookforge/phases/outline/validators.py`

Change shape:
- Major change.
- Current validators understand full outline and chapter-window scope.
- Add section-aware validation and section-boundary checks.

Required additions:
- validate active section with non-active sections allowed as `status: "stub"`
- enforce active section non-empty before S3
- section terminal echo exactly once and only on the terminal scene
- no mutation outside active section
- frozen/locked immutability checks
- boundary artifact validation before next section opens
- section-scoped window derivation for 04C/04D
- section subset support for `validate_outline`

Existing functions likely extended or mirrored:
- `validate_outline`
- `derive_phase04c_windows`
- `derive_phase04d_windows`
- intro/handoff target derivation helpers
- chapter-boundary normalization helpers

### 5. Outline Phase Handlers
Files:
- `src/bookforge/phases/outline/phase_03_scene_draft.py`
- `src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py`
- `src/bookforge/phases/outline/phase_04b_transition_execution.py`
- `src/bookforge/phases/outline/phase_04c_metadata_relink.py`
- `src/bookforge/phases/outline/phase_04c_intro_sync.py`
- `src/bookforge/phases/outline/phase_04c_handoff_normalize.py`
- `src/bookforge/phases/outline/phase_04d_seam_hygiene.py`
- `src/bookforge/phases/outline/phase_05_cast_function_refinement.py`
- `src/bookforge/phases/outline/phase_06_thread_payoff_refinement.py`

Change shape:
- Moderate changes across all chapter-scoped handlers.
- Current handlers assume the active payload is a single chapter.
- They need to accept a single active section inside a stable merged outline shape.

Likely runtime key changes:
- `current_chapter_id` -> keep
- add `current_section_id`
- add `current_chunk_ref`
- add `previous_boundary_artifact`
- add `phase04*_windows_by_section`
- add section-scoped allowed-field lists and touched refs

Special note:
- `phase_04d_seam_hygiene.py` already merges partial output onto a baseline chapter. The same pattern should be reused for section-scoped partial merges.

### 6. Prompt Templates / Prompt Blocks
Primary files:
- `resources/prompt_templates/outline_phase_03_scene_draft.md`
- `resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md`
- `resources/prompt_templates/outline_phase_04b_transition_execution.md`
- `resources/prompt_templates/outline_phase_04c_metadata_relink.md`
- `resources/prompt_templates/outline_phase_04c_intro_sync.md`
- `resources/prompt_templates/outline_phase_04c_handoff_normalize.md`
- `resources/prompt_templates/outline_phase_04d_seam_hygiene.md`
- `resources/prompt_templates/outline_phase_05_cast_function_refinement.md`
- `resources/prompt_templates/outline_phase_06_thread_payoff_refinement.md`

And the composed sources under:
- `resources/prompt_blocks/phase/outline_pipeline/*`

Change shape:
- Moderate to major content rewrite, but likely no filename churn.
- Replace chapter-local framing with section-local framing.
- Add explicit fields for:
  - active section thick payload
  - thin global outline
  - previous boundary seam
  - next section stub
  - section status / stage
- Keep the same T1/T2 discipline.

Template contract change:
- current chapter contract tokens are `{{chapter_target_id}}` and `{{chapter_input_outline}}`
- section rollout will need analogous section-scoped tokens

### 7. Writing Loop Orchestration
`src/bookforge/runner.py`

Change shape:
- Major change.
- Current run loop assumes the full outline scene inventory already exists and advances using chapter/scene counts.
- Under section chunking, later sections may still be stubs, so the runner must stop treating current drafted scene count as chapter-complete truth.

Required behavior changes:
- cursor becomes section-aware or section-derived
- when a frozen section is exhausted, advance to the next frozen section, not blindly to the next chapter
- if the next section is still a stub, pause or trigger the next outline chunk before continuing
- chapter rollup/compile must account for partially written chapters

Likely touchpoints:
- `_advance_cursor`
- `run_loop`
- any logic relying on `_outline_summary`

### 8. Scene Planning + Scene Artifacts
Files:
- `src/bookforge/phases/plan.py`
- `src/bookforge/pipeline/io.py`
- `src/bookforge/pipeline/phase_history.py`
- `src/bookforge/pipeline/scene.py`

Change shape:
- Moderate change.
- Scene planning already understands sections as metadata, but not section stage or section boundary ownership.
- Add section id/status into scene cards and log scope.
- Preserve existing chapter/scene file layout if possible, but attach section metadata so resume/debug remains exact.

Why this matters:
- current thought/log/artifact scope is chapter+scene only
- section-chunk drafting/writing needs exact section provenance without changing prose file names immediately

### 9. Outline Summary / Downstream Readers
`src/bookforge/pipeline/outline.py`

Change shape:
- Moderate change.
- `_outline_summary` currently reports chapter order + drafted scene counts only.
- Add a way to distinguish:
  - drafted/frozen scene count
  - remaining stub sections
  - next available frozen section

This can stay additive:
- keep `_outline_summary` for legacy paths
- add a new section-aware summary helper for the chunked runner

### 10. System Prompt Outline Injection
Files:
- `src/bookforge/pipeline/prompts.py`
- `src/bookforge/prompt/system.py`

Change shape:
- Moderate change.
- Current system prompt inclusion path always points to `outline/outline.json`.
- We want thin prompt context by default, while keeping `outline.json` as canonical merged truth.

Recommended change:
- let `_system_prompt_for_phase` choose `outline.thin.json` for prompt injection
- keep direct non-prompt readers on `outline.json`

### 11. Thought Signature Scope
Files:
- `src/bookforge/llm/signatures.py`
- `src/bookforge/llm/thoughts.py`
- `src/bookforge/cli.py`

Change shape:
- Small but important.
- Current thought signature scope keys use `book_id + phase_id + turn_id + chapter_id`.
- Under section chunking, multiple active chunks in the same chapter will collide.

Required additions:
- add `section_id` or `chunk_ref` to signature records and scope keys
- add matching filters to `llm thoughts`, `llm signatures`, and active-selection commands

This is not optional if section-chunked execution is expected to coexist with thought-signature replay/selection.

### 12. Workspace Bootstrap
`src/bookforge/workspace.py`

Change shape:
- Low to moderate.
- Only needed if we add new prompt template filenames or want to preseed empty view files.
- If we reuse current template filenames and create views lazily at runtime, this file may need little or no change.

### 13. Writer-Phase T1 -> T2 Lineage
Files:
- `src/bookforge/phases/write_phase.py`
- `src/bookforge/phases/preflight_phase.py`
- `src/bookforge/phases/repair_phase.py`
- `src/bookforge/phases/state_repair_phase.py`
- `src/bookforge/phases/lint_phase.py`
- `src/bookforge/llm/logging.py`
- `src/bookforge/llm/signatures.py`

Change shape:
- Moderate change.
- The write phases already carry `T1` assistant parts into `T2` on Gemini.
- The missing work is to make that lineage explicit and auditable in runtime artifacts rather than relying on implicit in-memory flow.

Required additions:
- record `t1_signature_id` or equivalent lineage metadata on `T2`
- persist enough metadata to prove which planning turn informed execution
- keep provider-specific behavior backward-compatible

### 14. Chapter Seam Audit / Repair / Finalization
Files:
- `src/bookforge/section_workflow.py`
- `src/bookforge/runner.py`
- `src/bookforge/pipeline/state_apply.py`
- new chapter seam audit/repair helpers or phases
- new prompt templates/blocks for chapter seam audit/repair

Change shape:
- Major change.
- Current chapter compilation is a mostly mechanical assembly step.
- It needs to become a real quality gate that can detect and repair seam-local merge artifacts before final chapter promotion.

Required additions:
- provisional chapter assembly before final promotion
- seam report artifact emission
- seam-local repair pass
- post-repair state-delta validation
- explicit final chapter promotion gate

### 15. Diagnostics / Log Split
Files:
- `src/bookforge/llm/thoughts.py`
- `src/bookforge/llm/logging.py`
- `src/bookforge/pipeline/phase_history.py`
- workflow/report helpers to be added

Change shape:
- Moderate change.
- Current raw LLM logs, thought/probe artifacts, and per-scene repair artifacts are too mixed for efficient fault classification.

Required additions:
- separate thought/probe artifacts from transport logging
- summarize lint/repair failure classes
- preserve backward compatibility with current logs while introducing a clearer operational surface

## New Helper Modules Recommended
To avoid further inflating existing large files, the first implementation pass should likely add:
- `src/bookforge/phases/outline/chunks.py`
  - section selection
  - section merge helpers
  - section ref helpers
- `src/bookforge/phases/outline/snapshots.py`
  - snapshot registry
  - persistent view builders
  - boundary artifact builders/readers

Optional later helper:
- `src/bookforge/pipeline/outline_progress.py`
  - section-aware progress summary for the writer loop

## Runtime / Schema Additions Expected
Additive only; avoid breaking current outline schema unless necessary.

Likely new fields or runtime records:
- section `status`: `stub | draftable | frozen | locked`
- snapshot registry entries keyed by `chapter_id + section_id`
- boundary artifact payloads
- section-aware resume cursor:
  - `next_chapter_id`
  - `next_section_id`
  - optional `next_scene_id`
- section-aware thought signature metadata

Existing `outline.json` chapter/section/scene structure should remain intact.

## First Implementation Cut
To reduce blast radius, the first code slice should target the minimum set below.

Slice A - Outline-only skeleton
- `src/bookforge/outline.py`
- `src/bookforge/phases/outline/context.py`
- `src/bookforge/phases/outline/artifacts.py` or new `snapshots.py`
- `src/bookforge/phases/outline/validators.py`
- phase 03/04A/04B/04C/04D handlers
- outline prompt templates/blocks

Outcome:
- section-scoped outline chunking
- S3 freeze
- boundary artifacts
- persistent outline views
- no writer integration yet

Slice B - Writer integration
- `src/bookforge/runner.py`
- `src/bookforge/phases/plan.py`
- `src/bookforge/pipeline/outline.py`
- `src/bookforge/pipeline/io.py`
- `src/bookforge/pipeline/phase_history.py`
- `src/bookforge/pipeline/prompts.py`
- `src/bookforge/prompt/system.py`

Outcome:
- writer can consume frozen sections incrementally
- cursor and resume become section-aware

Slice C - Thought/log exactness
- `src/bookforge/llm/signatures.py`
- `src/bookforge/llm/thoughts.py`
- `src/bookforge/cli.py`

Outcome:
- active thought selection and replay remain exact under section scope

## Implementation Stories
These stories translate the plan into executable work units. They are ordered by dependency and blast radius, not by convenience.

### Story 1 - Snapshot Registry + Persistent Views
Goal:
- Introduce the section snapshot registry and the four persistent outline projections without changing the writer yet.

Primary files:
- `src/bookforge/phases/outline/artifacts.py`
- `src/bookforge/phases/outline/snapshots.py` (new)
- `src/bookforge/outline.py`

Scope:
- Add `snapshot_registry.json`
- Add builders/writers for:
  - `outline.thin.json`
  - `outline.toc.json`
  - `outline.index.json`
  - `outline.appendix.json`
- Keep `outline.json` authoritative and merged
- Make view writes atomic at S3/S4 only

Not in scope:
- writer loop changes
- section-scoped prompt execution

Acceptance:
- A run can emit/update the registry and derived views without changing the existing meaning of `outline.json`
- Rebuilding views from `outline.json + snapshot_registry.json` is deterministic
- No partial view writes are visible if a run dies mid-update

Dependencies:
- none

### Story 2 - Section Stub Contract + Section Selection
Goal:
- Make section status first-class and selectable so the outline pipeline can operate on one section at a time.

Primary files:
- `src/bookforge/phases/outline/context.py`
- `src/bookforge/phases/outline/chunks.py` (new)
- `src/bookforge/phases/outline/validators.py`
- `src/bookforge/outline.py`

Scope:
- Add stub contract enforcement with `status: "stub"`
- Add section selection helpers
- Add section chunk identity helpers (`chapter_id`, `section_id`, `chunk_ref`)
- Add section-aware resume cursor shape

Not in scope:
- section-scoped LLM execution
- writing loop changes

Acceptance:
- The orchestrator can identify the next active stub/draftable section deterministically
- Validators accept non-active sections as stubs and reject malformed stubs
- Resume/checkpoint data can name a section exactly

Dependencies:
- Story 1

### Story 3 - Section-Scoped Phase 03 Draft
Goal:
- Move scene drafting from chapter scope to section scope behind a feature flag.

Primary files:
- `src/bookforge/outline.py`
- `src/bookforge/phases/outline/phase_03_scene_draft.py`
- `src/bookforge/phases/outline/context.py`
- `resources/prompt_templates/outline_phase_03_scene_draft.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft*`

Scope:
- Add section-scoped render values
- Replace chapter-only prompt contract with section-local contract
- Merge drafted section back into merged `outline.json`
- Emit S2 section draft artifact

Not in scope:
- 04A/04B insertion
- writer loop changes

Acceptance:
- Phase 03 can draft exactly one active section while other sections remain stubs
- Non-active sections are not mutated
- Existing chapter-scoped mode remains available until rollout flips

Dependencies:
- Story 1
- Story 2

### Story 4 - Boundary Artifact Emission + Consumption
Goal:
- Define and persist the section boundary handoff so the next section can inherit continuity without mutating prior frozen output.

Primary files:
- `src/bookforge/phases/outline/snapshots.py`
- `src/bookforge/outline.py`
- `src/bookforge/phases/outline/validators.py`
- prompt templates for 03/04A/04B/04D

Scope:
- Emit `section_boundary_seam.json` at S3
- Inject prior boundary seam into the next section's prompts
- Add deterministic validation for missing/invalid boundary artifacts

Not in scope:
- prior-section mutation
- writer integration

Acceptance:
- Section N+1 can open using Section N's boundary artifact as authoritative continuity context, including cross-chapter boundaries
- The first section of the book can open without a prior boundary artifact
- Missing boundary artifact blocks opening the next section
- No code path mutates the frozen/locked prior section automatically

Dependencies:
- Story 3

### Story 5 - Section-Scoped 04A / 04B / 04C / 04D / 05 / 06
Goal:
- Move insertion and all remaining outline refinements from chapter scope to section scope.

Primary files:
- `src/bookforge/outline.py`
- `src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py`
- `src/bookforge/phases/outline/phase_04b_transition_execution.py`
- `src/bookforge/phases/outline/phase_04c_metadata_relink.py`
- `src/bookforge/phases/outline/phase_04c_intro_sync.py`
- `src/bookforge/phases/outline/phase_04c_handoff_normalize.py`
- `src/bookforge/phases/outline/phase_04d_seam_hygiene.py`
- `src/bookforge/phases/outline/validators.py`
- `src/bookforge/phases/outline/phase_05_cast_function_refinement.py`
- `src/bookforge/phases/outline/phase_06_thread_payoff_refinement.py`
- corresponding outline prompt templates/blocks

Scope:
- Section-local windows for 04C/04D
- Section-local insertion budget
- Section-local runtime keys
- Partial patch merge onto baseline section
- Section-local cast/thread refinement before freeze
- S3 promotion of seam-clean and refinement-complete section

Not in scope:
- writer loop
- global reopen/manual repair mode

Acceptance:
- 04A/04B/04C/04D/05/06 operate on only the active section
- Later sections remain stubs
- Frozen sections remain unchanged
- Window validation enforces local scope correctly

Dependencies:
- Story 3
- Story 4

### Story 6 - Freeze / Lock / Immutability Enforcement
Goal:
- Make S3 freeze and S4 lock real enforcement states, not just plan language.

Primary files:
- `src/bookforge/phases/outline/validators.py`
- `src/bookforge/phases/outline/snapshots.py` (new)
- `src/bookforge/outline.py`

Scope:
- Enforce:
  - draftable sections may renumber locally
  - frozen sections are scene-ref immutable
  - locked sections are fully immutable to automatic mutation
- Add deterministic checks for mutation outside active section

Not in scope:
- manual reopen implementation

Acceptance:
- Any automatic mutation against frozen/locked sections fails validation
- Snapshot registry stage transitions are explicit and auditable
- Scene-ref ranges for frozen/locked sections stay stable
- Frozen/locked section violations have explicit runtime handling:
  - fail the active run
  - mark the violating section as `reopen_required` in diagnostics
  - do not mutate automatically

Dependencies:
- Story 5

### Story 7 - Writer Loop Consumes Frozen Sections
Goal:
- Let the existing writing loop advance through frozen sections instead of assuming the full chapter scene inventory already exists.

Primary files:
- `src/bookforge/runner.py`
- `src/bookforge/phases/plan.py`
- `src/bookforge/pipeline/outline.py`
- `src/bookforge/pipeline/io.py`
- `src/bookforge/pipeline/phase_history.py`
- `src/bookforge/pipeline/scene.py`

Scope:
- Make cursor progression section-aware
- Stop at the end of the last frozen section instead of pretending the rest of the chapter exists
- Preserve chapter/scene prose file naming, but attach section metadata to scene cards and artifacts
- Allow partial chapter rollup/compile behavior to be explicit
- Rebuild provisional S3-derived projections from S4-authoritative written state when they diverge

Not in scope:
- rewriting prose storage layout
- full manual reopen flow

Acceptance:
- Writer can consume one frozen section, stop, then resume after the next section is frozen
- Scene planning carries exact `section_id`
- Resume remains exact at scene level even when the chapter is only partially outlined/written
- If S3-provisional registry/view data diverges from S4-written truth, projections are rebuilt deterministically

Dependencies:
- Story 6

### Story 8 - T1 -> T2 Signature Lineage Hardening
Goal:
- Verify and preserve the existing `T1 -> T2` carry contract in the writing loop without building duplicate signature machinery unless runtime evidence shows it is needed.

Primary files:
- `src/bookforge/phases/write_phase.py`
- `src/bookforge/phases/preflight_phase.py`
- `src/bookforge/phases/repair_phase.py`
- `src/bookforge/phases/state_repair_phase.py`
- `src/bookforge/phases/lint_phase.py`
- `src/bookforge/llm/logging.py`
- `src/bookforge/llm/signatures.py`

Scope:
- Keep the existing Gemini assistant-parts carry intact
- Add only the minimum instrumentation needed to confirm that `T2` was executed against the immediately preceding `T1` planning context
- Prefer tests and compact diagnostics over building a second parent/child signature graph by default
- Preserve current Gemini assistant-parts carry behavior
- Make lineage failures diagnosable instead of implicit

Not in scope:
- changing the prompt content itself
- introducing new model-routing policy
- building a heavyweight signature relationship system unless simpler verification proves insufficient

Acceptance:
- Each two-turn writer phase can verify that `T2` used the immediately preceding `T1` planning context
- Operators can diagnose broken carry without reconstructing the full path manually from raw transport logs
- The implementation remains backward-compatible with providers that do not expose the same assistant-parts shape

Dependencies:
- Story 7

### Story 9 - Chapter Seam Audit
Goal:
- Detect chapter-level merge artifacts that emerge only after all sections in a chapter have been locked and assembled.

Primary files:
- `src/bookforge/section_workflow.py`
- `src/bookforge/runner.py`
- `src/bookforge/pipeline/state_apply.py`
- new chapter seam audit phase/helpers
- new prompt templates/blocks for seam audit

Scope:
- Assemble provisional chapter markdown
- Audit for merge-layer defects:
  - repeated restart energy where a scene re-announces the prior scene close
  - overlap-heavy joins where adjacent scenes partially duplicate the same beat
  - tense breaks
  - scaffold leakage
  - duplicated beats
  - redundant item re-grounding
  - factual contradictions at joins
- Emit a structured chapter seam report

Not in scope:
- rewriting full scenes
- cross-chapter prose linting

Acceptance:
- Clean chapters can produce an explicit no-op audit result
- Dirty chapters produce a structured seam report with seam-local targets
- The seam report is available before final chapter promotion

Dependencies:
- Story 7

### Story 10 - Chapter Seam Repair + Finalization Gate
Goal:
- Repair seam-local chapter merge artifacts and gate final chapter promotion on seam cleanliness plus state integrity.

Primary files:
- `src/bookforge/section_workflow.py`
- `src/bookforge/runner.py`
- `src/bookforge/pipeline/state_apply.py`
- new chapter seam repair phase/helpers
- new prompt templates/blocks for seam repair

Scope:
- Repair only seam neighborhoods and merge-layer artifacts
- Specifically target overlap/restart-energy cleanup so assembled chapters advance instead of re-entering the same beat at every join
- Validate repaired output against expected chapter state delta
- Finalize the chapter only after seam audit/repair passes

Not in scope:
- manual reopen mode
- scene-interior rewrites beyond allowed seam-local edits

Acceptance:
- Chapter finalization is no longer a blind concatenation path
- State-delta failures route back to seam repair with context
- Repair retries are bounded and escalate cleanly when seam repair cannot preserve state integrity

Dependencies:
- Story 9

### Story 11A - Outline-Phase Thin Prompt Injection
Goal:
- Reduce prompt weight for outline-facing prompts by using the thin view as global navigation context.

Primary files:
- `src/bookforge/pipeline/prompts.py`
- `src/bookforge/prompt/system.py`

Scope:
- Keep non-prompt readers on `outline.json`
- Allow outline-oriented prompt injection to prefer `outline.thin.json`

Not in scope:
- changing the canonical merged outline file

Acceptance:
- Outline-side prompt loading can consume the thin view without losing active-section truth
- Existing behavior can be toggled or safely rolled out without breaking current runs

Dependencies:
- Story 1

### Story 11B - Writer-Phase Thin Prompt Injection
Goal:
- Shift writer/preflight/repair/state_repair system-prompt outline injection to `outline.thin.json` once the writer is section-aware.

Primary files:
- `src/bookforge/pipeline/prompts.py`
- `src/bookforge/prompt/system.py`

Scope:
- Keep non-prompt readers on `outline.json`
- Use `outline.thin.json` for writer-side system prompt inclusion where outline injection is enabled

Acceptance:
- System prompts for write/preflight/repair/state_repair can load the thin outline view
- Existing behavior can be toggled or safely rolled out without breaking current runs

Dependencies:
- Story 1
- Story 7

### Story 12 - Section-Aware Thought Scope
Goal:
- Keep thought signature logging and selection exact under section chunking.

Primary files:
- `src/bookforge/llm/signatures.py`
- `src/bookforge/llm/thoughts.py`
- `src/bookforge/cli.py`
- logging call sites in `src/bookforge/outline.py` and writer phases as needed

Scope:
- Add `section_id` or `chunk_ref` to signature records
- Extend scope keys and filters
- Keep current `phase_id + turn_id + chapter_id` behavior backward-compatible

Not in scope:
- changing the current-thoughts prompt itself

Acceptance:
- Two different sections in the same chapter do not collide in active thought selection
- CLI filters can target section-scoped thoughts
- Existing ledger/index files remain readable

Dependencies:
- Story 3 for outline-side scope
- Story 7 for writer-side scope

### Story 13 - Dynamic Outline Lint / Repair Integration
Goal:
- Reapply the existing dynamic lint/repair plan in section scope once section chunking is stable.

Primary files:
- `src/bookforge/phases/outline/validators.py`
- `src/bookforge/outline.py`
- repair-family helpers/modules to be added under `src/bookforge/phases/outline/`
- relevant prompt templates/blocks

Scope:
- Structural / Identity / Seam repair families
- issue routing within the active section
- convergence tracking and overlap handling

Not in scope:
- prior-section mutation

Acceptance:
- Outline repair windows are constrained to the active section
- Convergence tracking can distinguish “same issue persisted” from “new issue introduced”
- Boundary failures route through boundary artifact validation instead of mutating prior sections

Dependencies:
- Story 6
- Story 5

### Story 14 - Lint/Repair Diagnostics + Thought/Log Split
Goal:
- Make lint/repair failures diagnosable without digging through mixed raw LLM transport logs.

Primary files:
- `src/bookforge/llm/thoughts.py`
- `src/bookforge/llm/logging.py`
- `src/bookforge/pipeline/phase_history.py`
- workflow/report helpers to be added

Scope:
- separate introspection/probe artifacts from transport logs
- add per-scene/per-chapter diagnostics summaries for:
  - real truncation / `MAX_TOKENS`
  - malformed JSON
  - schema mismatch
  - repeated lint issues across repair passes
- keep existing logs readable during migration

Not in scope:
- deleting or rewriting historical logs

Acceptance:
- Operators can identify whether a failure is prompt-shape, token-budget, provider, or schema-related from summary artifacts
- Thought/probe artifacts no longer live only as overwritten or mixed log outputs

Dependencies:
- Story 8
- Story 10

### Story 15 - Writable Data Boundary Direction
Goal:
- Keep writable operational data storage flexible while biasing toward a separate writable-data repo/workspace rather than committing to an in-repo `app/data` split too early.

Primary files:
- planning/docs first
- storage/root resolution helpers as needed later

Scope:
- define storage assumptions so new diagnostics/thought/seam artifacts are not hard-coded into a monorepo-only layout
- preserve current workspace behavior while leaving room to move writable data out of the code repo

Not in scope:
- performing the repo split now
- migrating historical data

Acceptance:
- New artifact work does not assume a permanent in-repo `app/data` structure
- Storage touchpoints stay abstract enough to support a later separate writable-data repo/workspace migration

Dependencies:
- Story 14

## Story Order Recommendation
Implement in this order:
1. Story 1
2. Story 2
3. Story 3
4. Story 4
5. Story 5
6. Story 6
7. Story 7
8. Story 8
9. Story 9
10. Story 10
11. Story 11A
12. Story 11B
13. Story 12
14. Story 13
15. Story 14
16. Story 15

Reasoning:
- Stories 1-6 establish the new outline truth model.
- Story 7 is the first place the writing loop needs to care.
- Story 8 hardens the already-existing two-turn writer behavior into an explicit contract before more workflow complexity is added.
- Stories 9-10 close the now-visible chapter assembly quality gap.
- Story 11A is a lightweight outline-side optimization once thin view production is trustworthy.
- Story 11B depends on a section-aware writer.
- Story 12 must follow once section identity is real across execution paths.
- Story 13 should not be built on shifting ownership rules.
- Story 14 becomes more valuable after the seam/finalization loop exists and real failure classes can be summarized.
- Story 15 remains intentionally late because it should constrain new storage coupling without forcing the repo split decision up front.

## Deterministic Checks Required
Before rollout reaches writing, add checks for:
- section terminal echo exactly once and on terminal scene
- no duplicate or skipped scene ids in active section
- no cross-section mutation outside active section
- boundary artifact presence before opening next section
- no mutation of frozen/locked sections
- chapter seam finalization gate present before final chapter promotion
- `T1 -> T2` lineage metadata present for two-turn writer phases
- configured-model policy respected by workflow commands
- default lint/repair pass budget raised to `8`
- workflow/test command wrappers use timeout windows appropriate for multi-hour runs

## Risks / Watchouts
- Section-level insertion can still create ugly cross-section seams if boundary ownership is not enforced.
- Active-section-only mutation means the new section must absorb seam responsibility from the old one.
- Registry timing must not let draft churn become authoritative too early.
- View updates must be atomic or prompts will consume mixed-stage truth.
- Chapter seam repair must not become a disguised scene rewrite pass.
- If `T1 -> T2` lineage remains implicit, later debugging will keep conflating good planning with bad execution.
- Long runtime is a real property of the correctness-constrained pipeline; trying to "fix" it by silently changing model config is an orchestration bug, not an optimization.
- Diagnostics/storage work should not accidentally lock the project into an in-repo writable-data layout if the long-term direction is a separate writable-data repo/workspace.

## Rollout Stages
Stage 1
- Add section-scoped Phase 03 runner behind a flag.
- Implement stub contract.
- Keep `outline.json` as canonical merged outline.
- Add snapshot registry + persistent thin/toc/index/appendix views.

Stage 2
- Route 04A/04B/04C/04D to section scope.
- Add boundary artifact emission/consumption.
- Extend validators to section scope and immutability checks.

Stage 3
- Freeze at S3 and run section-level writing loop.
- Enforce scene-ref immutability at S3.
- Make runner/cursor section-aware.

Stage 4
- Harden `T1 -> T2` writer-phase lineage.
- Add chapter seam audit/repair/finalization after the last locked section in a chapter.

Stage 5
- Promote provisional registry data at S4.
- Wire thin outline into system prompt injection.

Stage 6
- Integrate dynamic lint/repair windows with active-section routing.
- Add section-aware thought signature scope and CLI filters.
- Add diagnostics summaries and separate thought/probe artifacts from raw transport logging.

## Open Questions
- Whether manual reopen mode should exist at all, and if so, what its explicit scope is.
