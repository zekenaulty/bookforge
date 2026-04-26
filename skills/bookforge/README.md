# BookForge Skill Tree

Schema version: `bookforge_skilltree_v1`

This tree is generated from `skills/bookforge/skilltree.manifest.json`.

## Orchestrators
- `bookforge.orchestrators.book-workflow` -> `skills/bookforge/orchestrators/book-workflow` (book_workflow / book_workflow)
- `bookforge.orchestrators.outline-pipeline` -> `skills/bookforge/orchestrators/outline-pipeline` (outline_pipeline / outline_pipeline)
- `bookforge.orchestrators.run-pipeline` -> `skills/bookforge/orchestrators/run-pipeline` (run_pipeline / run_pipeline)

## Outline
- `bookforge.outline.chapter-spine` -> `skills/bookforge/outline/chapter-spine` (outline.phase_01_chapter_spine / phase_01_chapter_spine)
- `bookforge.outline.section-architecture` -> `skills/bookforge/outline/section-architecture` (outline.phase_02_section_architecture / phase_02_section_architecture)
- `bookforge.outline.scene-draft` -> `skills/bookforge/outline/scene-draft` (outline.phase_03_scene_draft / phase_03_scene_draft)
- `bookforge.outline.transition-seam-analysis` -> `skills/bookforge/outline/transition-seam-analysis` (outline.phase_04a_transition_seam_analysis / phase_04a_transition_seam_analysis)
- `bookforge.outline.transition-execution` -> `skills/bookforge/outline/transition-execution` (outline.phase_04b_transition_execution / phase_04b_transition_execution)
- `bookforge.outline.metadata-relink` -> `skills/bookforge/outline/metadata-relink` (outline.phase_04c_metadata_relink / phase_04c_metadata_relink)
- `bookforge.outline.intro-sync` -> `skills/bookforge/outline/intro-sync` (outline.phase_04c_intro_sync / phase_04c_intro_sync)
- `bookforge.outline.handoff-normalize` -> `skills/bookforge/outline/handoff-normalize` (outline.phase_04c_handoff_normalize / phase_04c_handoff_normalize)
- `bookforge.outline.seam-hygiene` -> `skills/bookforge/outline/seam-hygiene` (outline.phase_04d_seam_hygiene / phase_04d_seam_hygiene)
- `bookforge.outline.cast-function-refinement` -> `skills/bookforge/outline/cast-function-refinement` (outline.phase_05_cast_function_refinement / phase_05_cast_function_refinement)
- `bookforge.outline.thread-payoff-refinement` -> `skills/bookforge/outline/thread-payoff-refinement` (outline.phase_06_thread_payoff_refinement / phase_06_thread_payoff_refinement)

## Run
- `bookforge.run.scene-planning` -> `skills/bookforge/run/scene-planning` (run.plan_scene / plan_scene)
- `bookforge.run.preflight-state` -> `skills/bookforge/run/preflight-state` (run.preflight / preflight)
- `bookforge.run.continuity-pack` -> `skills/bookforge/run/continuity-pack` (run.continuity_pack / continuity_pack)
- `bookforge.run.scene-writing` -> `skills/bookforge/run/scene-writing` (run.write_scene / write_scene)
- `bookforge.run.scene-repair` -> `skills/bookforge/run/scene-repair` (run.repair_scene / repair_scene)
- `bookforge.run.state-repair` -> `skills/bookforge/run/state-repair` (run.state_repair / state_repair)
- `bookforge.run.scene-lint` -> `skills/bookforge/run/scene-lint` (run.lint_scene / lint_scene)
- `bookforge.run.scene-commit` -> `skills/bookforge/run/scene-commit` (run.apply_commit / apply_commit)
