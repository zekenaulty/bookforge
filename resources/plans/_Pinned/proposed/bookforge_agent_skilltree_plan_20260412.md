# BookForge Agent Skilltree Plan (2026-04-12)

## Purpose
Create a portable, phase-mapped skill tree for BookForge that works across Claude-style docs, Codex-style skill docs, and MCP/tool-driven orchestration without inventing a second pipeline model.

## Source Anchors
- `resources/plans/`
- `resources/plans/proposed/`
- `resources/prompt_blocks/`
- `docs/help/`
- `src/bookforge/phases/outline/context.py`
- `src/bookforge/runner.py`
- `C:\Users\Zythis\source\repos\__draft_old\cognition\src\Cognition.Clients\Tools\Planning\`

## Locked Design Decisions
1. Skill leaves map to real BookForge graph nodes, not abstract personas.
2. Non-graph command surfaces are handled by orchestrator skills, not by duplicating leaf nodes.
3. Every concrete skill folder includes:
   - `README.md`
   - `AGENT.md`
   - `SKILL.md`
   - `CLAUDE.md`
   - `HELP.md`
   - `skill.py`
4. Canonical Markdown filenames are uppercase for portability with toolchains that look for `README.md`, `SKILL.md`, or `CLAUDE.md` by exact name.
5. Skill execution is param-driven and template-string based.
6. Gemini is the portable execution target for examples through the standard `google-genai` package.
7. A manifest is the source of truth; generated skill folders are build artifacts derived from that manifest.

## Why This Shape
BookForge already has two real execution graphs:
1. Outline pipeline graph:
   - `phase_01_chapter_spine`
   - `phase_02_section_architecture`
   - `phase_03_scene_draft`
   - `phase_04a_transition_seam_analysis`
   - `phase_04b_transition_execution`
   - `phase_04c_metadata_relink`
   - `phase_04c_intro_sync`
   - `phase_04c_handoff_normalize`
   - `phase_04d_seam_hygiene`
   - `phase_05_cast_function_refinement`
   - `phase_06_thread_payoff_refinement`
2. Scene run graph:
   - `plan`
   - `preflight`
   - `continuity_pack`
   - `write`
   - `repair`
   - `state_repair`
   - `lint`
   - `commit`

The older Cognition planning code reinforces the same separation:
1. Metadata and capability discovery.
2. Step descriptors and template IDs.
3. Transcript/artifact capture.
4. Orchestrators that route work without becoming the skill itself.

The new skill tree keeps those boundaries intact.

## Target Skill Tree
```text
skills/
  bookforge/
    skilltree.manifest.json
    README.md
    orchestrators/
      book-workflow/
      outline-pipeline/
      run-pipeline/
    outline/
      chapter-spine/
      section-architecture/
      scene-draft/
      transition-seam-analysis/
      transition-execution/
      metadata-relink/
      intro-sync/
      handoff-normalize/
      seam-hygiene/
      cast-function-refinement/
      thread-payoff-refinement/
    run/
      scene-planning/
      preflight-state/
      continuity-pack/
      scene-writing/
      scene-repair/
      state-repair/
      scene-lint/
      scene-commit/
```

## Mapping Rules
### Orchestrators
- `book-workflow`
  - Routes init-like, setup-like, export-like, and end-to-end book requests.
  - May delegate into `outline-pipeline` or `run-pipeline`.
- `outline-pipeline`
  - Routes `outline generate`, reruns, resume windows, backup/restore style tasks.
  - Owns the outline-phase leaf skills.
- `run-pipeline`
  - Routes `run` loop tasks and draft-generation requests.
  - Owns the scene-phase leaf skills.

### Outline leaf skills
- Each leaf maps 1:1 to a real outline graph node from `src/bookforge/phases/outline/context.py`.
- Skill folder names are semantic; `phase_id` stays exact inside metadata.

### Run leaf skills
- Each leaf maps 1:1 to a real runner phase from `src/bookforge/runner.py`.
- `scene-commit` exists even though it is deterministic because the orchestrator still needs a routable action node.

## Skill Contract
Each skill must expose:
1. Human-readable name.
2. LLM-oriented description.
3. `skill_id`
4. `graph_node`
5. `phase_id`
6. `logical_phase`
7. Required params
8. Optional params
9. Source references
10. Help references
11. Prompt contract summary
12. Example params

## Portable Python Runtime
### Package
- `src/bookforge/skill_runtime/`

### Responsibilities
1. Load skill metadata.
2. Render prompt templates from passed params.
3. Produce dry-run prompt bundles for orchestrators and tests.
4. Execute Gemini calls through `google-genai`.
5. Keep imports lazy so the runtime works even when the extra dependency is not installed.

### Runtime principles
1. Passed params are authoritative.
2. Source refs are traceability aids, not hidden runtime fetches.
3. Skills stay self-describing and file-local.
4. Prompt rendering must be deterministic.

## Generation Strategy
1. Maintain a single `skills/bookforge/skilltree.manifest.json`.
2. Generate the repetitive doc set and `skill.py` from the manifest.
3. Keep manual edits in the manifest and runtime, not by hand-editing dozens of skill folders.

## Example Runtime Surface
Each generated `skill.py` should support:
1. `--dump-definition`
2. `--dump-example`
3. `--dry-run`
4. `--params-file`
5. `--set key=value`

This gives orchestrators and humans the same interface.

## Rollout
1. Create the plan artifact.
2. Add the portable runtime and dependency extra.
3. Add the manifest and generator.
4. Materialize the first complete tree under `skills/bookforge/`.
5. Add tests that ensure every manifest entry has a generated skill folder and required files.

## Acceptance Criteria
1. Every leaf skill corresponds to a real BookForge graph node.
2. The tree contains orchestrators plus phase-mapped leaves.
3. Every generated skill folder contains the required docs and `skill.py`.
4. `skill.py --dump-example` and `skill.py --dry-run` work without network calls.
5. The runtime can call Gemini through `google-genai` when the `skills` extra is installed.
6. The plan, manifest, and generated tree all agree on naming and routing.
