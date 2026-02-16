# WRITE
Write the scene described by the scene card.
- YOU MUST ALWAYS RETURN PROSE AND THE STATE_PATCH.
- Start in motion. No recap.
- Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
- Use the continuity pack and state for continuity.
- Use character_registry to keep names consistent in prose.
- Transition realization contract:
  - If scene_card.handoff_mode != "direct_continuation", the opening paragraph MUST realize scene_card.transition_in_text in 1-3 connective-action sentences.
  - Respect scene_card.location_start_id and scene_card.location_end_id as canonical transition identity.
  - Do not replace transition realization with recap exposition.
  - Opening transition realization must include at least one concrete action verb and one concrete world noun tied to the handoff context.
  - Acceptable realization forms: exact transition_in_text or equivalent phrasing that includes all scene_card.transition_in_anchors.
- Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
- State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
- Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
