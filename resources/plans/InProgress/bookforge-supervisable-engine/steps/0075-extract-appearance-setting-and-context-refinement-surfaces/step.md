# 0075 Extract Appearance, Setting, And Context Refinement Surfaces

Status: pending

## Goal
- Make character appearance, scene background/setting, and prior-stage context refinement explicit, queryable BookForge projection layers that Nanda can use without inferring truth from prose, prompt logs, or hidden runner side effects.

## Problem
- Character appearance already exists in the runtime, but it is currently too easy for it to behave like an incidental helper inside writer execution.
- The last observed state suggested at least one bug in the appearance flow, likely around stale, missing, or incorrectly refreshed projections.
- Scene setting/background is also under-specified:
  - prose may mention concrete background details that should be tracked
  - the author LLM may also need a distinct turn to deliberately establish or refine the scene's visual/background setting before prose or seam repair
- Thought signatures from earlier workflow stages preserve useful planning context, but they are not currently modeled as a controlled refinement input for later scene-phase actions.
- If these remain implicit, Nanda will eventually have to guess:
  - whether a character's visible appearance is current
  - whether a scene has a usable background/setting projection
  - which prior T1 planning signatures are safe and relevant context for the current author move

## Detailed Work
- Audit the current character appearance path.
  - Likely starting points:
    - `src/bookforge/characters.py`
    - `src/bookforge/pipeline/scene.py`
    - `src/bookforge/runner.py`
    - any helpers named like `refresh_appearance_projections(...)`
    - any helpers named like `_ensure_character_appearance_current(...)`
  - Determine whether current appearance artifacts are:
    - authoritative character truth
    - derived scene projections
    - provisional LLM outputs
    - diagnostic only
- Add an appearance projection query surface.
  - Candidate module:
    - `src/bookforge/query/appearance.py`
  - The query should be book-rooted and narrowable by:
    - `book_id`
    - optional `chapter`
    - optional `section`
    - optional `scene`
    - optional `character_id`
    - optional `branch_id`
  - It should return structured data, not raw file paths only.
  - It should report artifact status using the shared vocabulary:
    - `authoritative`
    - `provisional`
    - `derived`
    - `diagnostic`
- Add an extracted appearance scene-phase action.
  - Candidate action:
    - `refresh_character_appearance_projection`
  - The first action should be scene/cast scoped.
  - It should read:
    - scene card cast
    - character state
    - existing appearance data
    - current timeline node
  - It should emit explicit `ProducedArtifactReceipt` records.
  - It should not silently mutate canonical character state unless a later explicit apply/promote path exists.
- Add a scene background/setting projection surface.
  - Candidate query module:
    - `src/bookforge/query/setting.py`
  - Candidate execution actions:
    - `extract_scene_setting_from_prose`
    - `draft_scene_setting_projection`
  - `extract_scene_setting_from_prose` should read already-produced prose and derive setting/background details from what is actually on page.
  - `draft_scene_setting_projection` should be a distinct author-LLM turn that can establish intended scene background before prose generation or seam repair.
  - Both paths must label outputs truthfully:
    - prose-derived extraction is `derived`
    - author-drafted setting projection is `provisional` until accepted by a later commit/apply action
- Add context refinement through prior T1 thought signatures.
  - Treat T1 thought signatures from previous workflow stages as context-management artifacts, not source of truth.
  - Candidate query surface:
    - `src/bookforge/query/thought_context.py`
  - Candidate refinement behavior:
    - select relevant prior T1 signatures by `TimelineNodeRef`, phase, scene, and workflow family
    - expose them as candidate context inputs for the next scene-phase action
    - record which signatures were included in the prompt package or execution receipt
  - This is essentially reuse of previous planning work.
  - It must not replace explicit execution receipts, state surfaces, or artifact truth.
- Thread all three surfaces through the same coordinate model.
  - `TimelineNodeRef`
  - `ScopeSelector`
  - branch id
  - fork group id where relevant
  - artifact status
- Add readiness semantics.
  - A caller should be able to ask:
    - is appearance projection available for this scene/cast
    - is it stale relative to current character state or current scene node
    - is setting/background available
    - was the setting extracted from prose or drafted by the author LLM
    - which prior T1 thought signatures are available as refinement context
    - whether any of these are legal inputs for the next scene-phase action
- Keep this as projection-layer work, not canonical mutation work.
  - 0075 should not solve character-state promotion, inventory promotion, or final scene commit.
  - It should make projections visible, typed, and safe to reason about.

## Surface Sketch
### Appearance Projection
- Minimum fields:
  - `book_id`
  - `selector`
  - `node`
  - `character_id`
  - `character_name`
  - `appearance_status`
  - `artifact_status`
  - `source_artifacts`
  - `staleness_reason`
  - `visible_scene_details`
  - `last_refreshed_node`

### Scene Setting Projection
- Minimum fields:
  - `book_id`
  - `selector`
  - `node`
  - `setting_status`
  - `artifact_status`
  - `source_mode`
  - `source_mode` values:
    - `prose_extracted`
    - `author_drafted`
    - `outline_derived`
    - `missing`
  - `location_id`
  - `location_label`
  - `background_details`
  - `sensory_anchors`
  - `continuity_constraints`
  - `source_artifacts`

### Thought Context Refinement
- Minimum fields:
  - `book_id`
  - `selector`
  - `node`
  - `candidate_signatures`
  - `selected_signatures`
  - `phase_id`
  - `turn_id`
  - `context_role`
  - `context_role` values:
    - `planning_reuse`
    - `constraint_reminder`
    - `style_or_voice_reference`
    - `diagnostic_context`
  - `artifact_status`
  - `limitations`
- Required limitation:
  - thought signatures are context aids only
  - execution receipts remain the truth of what happened

## Files Likely Touched
- `src/bookforge/characters.py`
- `src/bookforge/pipeline/scene.py`
- `src/bookforge/runner.py`
- `src/bookforge/query/__init__.py`
- `src/bookforge/query/appearance.py`
- `src/bookforge/query/setting.py`
- `src/bookforge/query/thought_context.py`
- `src/bookforge/execution/scene_actions.py`
- `src/bookforge/execution/__init__.py`
- `src/bookforge/contracts/`
- `src/bookforge/llm/storage.py`
- `src/bookforge/llm/signatures.py`
- `docs/help/workflow.md`
- `docs/help/index.md`

## Tests
- Add appearance projection tests, for example:
  - `tests/test_appearance_query.py`
  - `tests/test_appearance_projection_action.py`
- Add setting/background tests, for example:
  - `tests/test_scene_setting_query.py`
  - `tests/test_scene_setting_actions.py`
- Add thought-context selection tests, for example:
  - `tests/test_thought_context_query.py`
- Required behavior coverage:
  - appearance projection reports missing state without crashing
  - appearance projection detects stale state when character state revision or node changes
  - appearance projection emits explicit artifact status
  - scene setting extraction from prose is `derived`
  - author-drafted setting projection is `provisional`
  - thought-signature context selection filters to relevant prior T1 signatures
  - thought signatures are never reported as authoritative execution truth
  - readiness surfaces can report appearance, setting, and thought-context availability without starting execution

## Definition Of Done
- A caller can query character appearance projection status for a book, scene, or character without inspecting raw files.
- A caller can tell whether appearance data is current, stale, missing, derived, provisional, or authoritative.
- A caller can trigger a scene/cast-scoped appearance projection action without accidentally mutating canonical character truth.
- A caller can query scene background/setting status independently from prose generation.
- A caller can distinguish prose-extracted setting details from author-drafted setting projections.
- A caller can discover relevant prior T1 thought signatures as optional refinement context for a scene-phase action.
- Execution receipts record when appearance, setting, or thought-context artifacts were used as inputs.
- Nanda can present these capabilities honestly in the author pane using BookForge query results instead of persona claims.

## Notes
- This step is intentionally separate from 0070.
- 0070 is about segmenting the write loop into phase-shaped actions.
- 0075 is about projection-layer quality and context reuse around those actions.
- Appearance and setting should eventually inform continuity, prose writing, seam repair, and lint/repair, but they should not be hidden inside those phases.
- The scene background/setting work should support both:
  - extraction from prose already written
  - a distinct author LLM turn that drafts intended background/setting before prose or seam repair
- Prior T1 thought signatures should be treated as controlled context reuse.
  - They can reduce repeated planning work.
  - They can preserve author intent between graph nodes.
  - They cannot replace state surfaces, issue tickets, or produced-artifact receipts.
