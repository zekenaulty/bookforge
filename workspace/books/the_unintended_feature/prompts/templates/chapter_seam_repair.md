# CHAPTER SEAM REPAIR

Repair the seam between Scene A and Scene B by rewriting ONLY the writable boundary windows.
Return ONLY JSON. No markdown, no commentary.

Goal:
- Rewrite the end of Scene A and the beginning of Scene B so they read as one continuous flow.
- Preserve all established facts, events, outcomes, voice, and chapter intent.
- Remove duplicated UI/system surfaces, repeated bodily state, restart energy, and obvious seam artifacts.

Hard rules:
- Do NOT change anything outside the supplied writable windows.
- Do NOT introduce new plot events, new mechanics, new characters, new locations, or new durable facts.
- Do NOT remove required information from the seam if it is the first legitimate appearance of that information.
- If a UI/system surface should survive, keep one coherent version instead of duplicating or mutating it across both scenes.
- Prefer forward motion. Scene B should continue from Scene A, not restate it.
- Preserve the local tone and tense used by the surrounding prose.

Required output schema:
{
  "schema_version": "chapter_seam_repair_v1",
  "status": "repaired",
  "scene_a_tail": "",
  "scene_b_head": "",
  "notes": []
}

Rules for output fields:
- `scene_a_tail` must be the full replacement text for Scene A's writable tail window.
- `scene_b_head` must be the full replacement text for Scene B's writable head window.
- Keep both as valid prose fragments that splice cleanly back into their parent scenes.
- `status` may be `repaired` or `no_change`.
- `notes` must be an array of short strings and may be empty.

Scene pair:
{{pair_payload}}

Lint issues:
{{issues}}
