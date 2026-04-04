# OUTLINE PIPELINE PHASE 03: SCENE DRAFT

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object that matches outline schema v1.1.
No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Core contract:
- Each scene is one writing unit.
- Every scene must include type and outcome.
- outcome must be a concrete state change.
- Do not pad with travel/recap/mood-only scenes.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Registry policy:
- characters and threads are globally optional, but become REQUIRED when referenced.
- If any scene includes characters/introduces/callbacks entries that reference character ids, top-level characters is required.
- If any scene includes threads entries that reference thread ids, top-level threads is required.
- Use canonical registry keys only. Do not use alias keys.
  - characters[] object required keys and types:
    - character_id (string)
    - name (string)
    - intro (object) with required keys:
      - chapter (integer, >=1)
      - scene (integer, >=1)
    - optional: pronouns (string), role (string)
  - threads[] object required keys and types:
    - thread_id (string)
    - label (string)
    - status (string)
- Forbidden alias keys:
  - characters[].id, characters[].title, characters[].description
  - threads[].id, threads[].title, threads[].description

Required chapter/section/scene constraints:
- chapter_id must be sequential integers starting at 1.
- chapter required keys and types:
  - chapter_id (integer)
  - title (string)
  - goal (string)
  - chapter_role (string)
  - stakes_shift (string)
  - bridge (object) with required keys:
    - from_prev (string)
    - to_next (string)
  - pacing (object) with required keys:
    - intensity (number or string)
    - tempo (string)
    - expected_scene_count (integer, >=1)
  - sections (array)
- section_id must be sequential integers within each chapter.
- section required keys and types:
  - section_id (integer)
  - title (string)
  - intent (string)
  - scenes (array)
  - preserve and output end_condition (string) from phase 02
- scene_id is chapter-local and must be monotonic across all sections in that chapter.
- scene required keys and types:
  - scene_id (integer)
  - summary (string)
  - type (string)
  - outcome (string)
  - characters (array of character_id strings)
- optional scene keys:
  - introduces (array of character_id strings)
  - threads (array of thread_id strings)
  - callbacks (array of id strings)
- Preserve section.end_condition from phase 02 for every section.
- Each section-final scene must include end_condition_echo that exactly matches phase-02 end_condition.
- Any referenced character/thread id must match a declared top-level registry id exactly (case-sensitive).

Required transition fields (phase 03 and later):
- location_start_label (required, non-empty string)
- location_end_label (required, non-empty string)
- location_start (non-empty string)
- location_end (non-empty string)
- handoff_mode (enum string)
- constraint_state (enum string)
- transition_in_text (required for EVERY scene, including first scene in chapter; non-empty string; connective action, not recap)
- transition_in_anchors (required for EVERY scene, including first scene in chapter; array of 3-6 non-empty strings)
- For non-first scenes: consumes_outcome_from (required, chapter_id:scene_id)
- For non-last scenes in chapter (including section-final scenes when chapter continues): transition_out_text (required, non-empty), transition_out_anchors (required, 3-6 strings), and hands_off_to (required, chapter_id:scene_id)
- Anchor cardinality rule:
  - transition_in_anchors and transition_out_anchors must each contain 3-6 non-empty strings.
  - If you only have 1-2 anchors, add additional concrete anchors before returning (never return fewer than 3).
- Anchor content rule (hard):
  - Anchors must be concrete sensory/location/action tokens, not meta/template language.
  - Forbidden anchor words/tokens include: `placeholder`, `unknown`, `tbd`, `here`, `there`, `n/a`.
  - Example forbidden anchor: `placeholder textures`.
  - Replace with concrete anchors such as `wet cobblestones`, `vault glyphs`, `iron gate hinges`.
- Section-boundary continuity rule (hard):
  - Section-final scenes are NOT exempt from handoff fields unless they are also the final scene of the chapter.
  - end_condition_echo does not replace transition_out_text, transition_out_anchors, or hands_off_to.
  - If a scene is the last scene in a section but another scene exists later in the same chapter, that scene MUST include transition_out_text, transition_out_anchors, and hands_off_to.

Location id compilation:
- The orchestrator owns canonical LOC_* id generation from labels.
- You may include location_start_id/location_end_id, but labels are mandatory and ids will be validated/normalized by the orchestrator.

Transition enum guidance:
- handoff_mode: direct_continuation, escorted_transfer, detained_then_release, time_skip, hard_cut, montage, offscreen_processing, combat_disengage, arrival_checkpoint, aftermath_relocation
- constraint_state: free, pursued, detained, processed, sheltered, restricted, engaged_combat, fleeing
- Strict bridge mode rule:
  - When strict transition bridges are enabled, do NOT emit handoff_mode=hard_cut.
  - Use non-hard-cut values such as time_skip, offscreen_processing, arrival_checkpoint, or combat_disengage.

Placeholder prohibition (hard):
- Do NOT emit placeholder location/transition values such as current_location, unknown, placeholder, tbd, here, there, n/a.
- If exact location identity is unavailable, return error_v1 with reason code missing_location_context.
- Do not emit synthetic anchor labels (for example anchor_1, anchor_2).
- Because strict validation rejects placeholder tokens, do not use bare tokens `here` or `there` in transition text fields; use concrete location nouns instead.
- Lexical ban in transition text fields:
  - Forbidden words (as standalone tokens): `here`, `there`, `unknown`, `placeholder`, `tbd`, `n/a`.
  - Example: avoid `The walls here are covered...`; use `The walls of the Glitch Vault are covered...`.
  - Example: avoid `...nowhere left to run that they can't follow`; use `...no route out of Iron District Alley that the Sentinels cannot follow`.

Seam scoring fields are optional in phase 03 but recommended:
- seam_score (0-100 int)
- seam_resolution (inline_bridge|micro_scene|full_scene)

Compatibility and omission rule:
- If a field is optional, omit when unknown; do NOT emit empty strings.
- Legacy transition_in may be present only as a compatibility alias; canonical field is transition_in_text.
- Do not use alternate key names for required schema fields.
- Before returning final JSON, run this self-check:
  - Order scenes by scene_id within each chapter.
  - For every scene except the highest scene_id in that chapter:
    - hands_off_to must be present and non-empty.
    - transition_out_text must be present and non-empty.
    - transition_out_anchors must contain 3-6 non-empty strings.

Output must remain compatible with scene-count policy:
{{scene_count_policy}}

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "missing_location_context",
  "missing_fields": ["chapters[0].sections[0].scenes[0].location_start_label"],
  "phase": "phase_03_scene_draft",
  "action_hint": "Provide concrete location labels and transition payload; do not use placeholders."
}

Outline spine (phase 01):
{{outline_spine_v1}}

Section architecture (phase 02):
{{outline_sections_v1}}

Book:
{{book}}

Targets:
{{targets}}

User prompt (optional):
{{user_prompt}}

Notes:
{{notes}}

Transition hints (optional):
{{transition_hints}}
