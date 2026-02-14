<!-- begin entry=E001 semantic=write.phase_intro_timeline_and_state_primacy_rules source=resources/prompt_blocks/phase/write/phase_intro_timeline_and_state_primacy_rules.md repeat=1/1 -->
# WRITE
Write the scene described by the scene card.
- YOU MUST ALWAYS RETURN PROSE AND THE STATE_PATCH.
- Start in motion. No recap.
- Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
- Use the continuity pack and state for continuity.
- Use character_registry to keep names consistent in prose.
- Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
- State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
- Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.

<!-- end entry=E001 semantic=write.phase_intro_timeline_and_state_primacy_rules -->
<!-- begin entry=E002 semantic=write.must_stay_true_end_state_rule source=resources/prompt_blocks/shared/summary/must_stay_true_end_state_rule.md repeat=1/1 -->
- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.

<!-- end entry=E002 semantic=write.must_stay_true_end_state_rule -->
<!-- begin entry=E003 semantic=write.must_stay_true_remove_directive_rule source=resources/prompt_blocks/shared/summary/must_stay_true_remove_directive_rule.md repeat=1/1 -->
- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).

<!-- end entry=E003 semantic=write.must_stay_true_remove_directive_rule -->
<!-- begin entry=E004 semantic=write.inventory_mechanics_ui_and_scope_rules source=resources/prompt_blocks/phase/write/inventory_mechanics_ui_and_scope_rules.md repeat=1/1 -->
- Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
- Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])

- For held items, specify container=hand_left or container=hand_right.
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
Durable vs ephemeral mechanics:
- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, do not include UI blocks; rephrase into narrative prose.
- UI/system readouts must be on their own line, starting with '[' and ending with ']'.
- Do NOT embed bracketed UI in narrative sentences.
- Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).

- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- If item_registry or plot_devices are provided, they are canonical durable-state references for ownership/custody labels in authoritative outputs.
- Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
- APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).

Durable item naming discipline:
- When you first describe a durable item, anchor it by using the canonical display_name within the same paragraph (or within the next 2 sentences).
- After anchoring, you may use brief descriptors for style if unambiguous.
- During any custody/handling change, include the canonical display_name in that sentence.
- If a required event is not in the Scene Card, do not perform it.
- Enforce scene-card durable constraints: honor `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, and `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
- Respect `timeline_scope` and `ontological_scope` when proposing durable mutations; do not mutate physical custody in non-present/non-real scope unless explicitly marked override.

<!-- end entry=E004 semantic=write.inventory_mechanics_ui_and_scope_rules -->
<!-- begin entry=E005 semantic=write.non_real_timeline_scope_override_rule source=resources/prompt_blocks/shared/scope/non_real_timeline_scope_override_rule.md repeat=1/1 -->
- Scope override rule (non-present / non-real scenes):
  - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".

<!-- end entry=E005 semantic=write.non_real_timeline_scope_override_rule -->
<!-- begin entry=E006 semantic=write.summary_requirements_and_state_patch_core_rules source=resources/prompt_blocks/phase/write/summary_requirements_and_state_patch_core_rules.md repeat=1/1 -->
- summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
- STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.

- must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.

- If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.

- Return prose plus a state_patch JSON block.
STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).

- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
- Include character_continuity_system_updates for cast_present_ids when mechanics change.
  - Use set/delta/remove/reason.
  - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  - If a new mechanic family appears, add it under set with a stable key.
- Include global_continuity_system_updates only if global mechanics change.

<!-- end entry=E006 semantic=write.summary_requirements_and_state_patch_core_rules -->
<!-- begin entry=E007 semantic=write.global_continuity_updates_array_rule source=resources/prompt_blocks/shared/continuity/global_continuity_updates_array_rule.md repeat=1/1 -->
- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]

<!-- end entry=E007 semantic=write.global_continuity_updates_array_rule -->
<!-- begin entry=E008 semantic=write.json_shape_guardrails_core_arrays_and_summary source=resources/prompt_blocks/phase/write/json_shape_guardrails_core_arrays_and_summary.md repeat=1/1 -->
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}


<!-- end entry=E008 semantic=write.json_shape_guardrails_core_arrays_and_summary -->
<!-- begin entry=E009 semantic=write.appearance_updates_object_shape_rule source=resources/prompt_blocks/shared/appearance/appearance_updates_object_shape_rule.md repeat=1/1 -->
  - appearance_updates MUST be an object under character_updates.
    - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}

<!-- end entry=E009 semantic=write.appearance_updates_object_shape_rule -->
<!-- begin entry=E010 semantic=write.durable_registry_transfer_and_creation_requirements source=resources/prompt_blocks/phase/write/durable_registry_transfer_and_creation_requirements.md repeat=1/1 -->
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.

<!-- end entry=E010 semantic=write.durable_registry_transfer_and_creation_requirements -->
<!-- begin entry=E011 semantic=write.transfer_registry_conflict_rule source=resources/prompt_blocks/shared/registry/transfer_registry_conflict_rule.md repeat=1/1 -->
- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
  - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
  - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.

<!-- end entry=E011 semantic=write.transfer_registry_conflict_rule -->
<!-- begin entry=E012 semantic=write.durable_mutation_and_appearance_update_entry_rules source=resources/prompt_blocks/phase/write/durable_mutation_and_appearance_update_entry_rules.md repeat=1/1 -->
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If you mutate durable state, do not leave the same mutation only in prose.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
- appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.

<!-- end entry=E012 semantic=write.durable_mutation_and_appearance_update_entry_rules -->
<!-- begin entry=E013 semantic=write.appearance_updates_not_array_rule source=resources/prompt_blocks/shared/appearance/appearance_updates_not_array_rule.md repeat=1/1 -->
  - appearance_updates MUST be an object, not an array.
    - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}

<!-- end entry=E013 semantic=write.appearance_updates_not_array_rule -->
<!-- begin entry=E014 semantic=write.appearance_update_detail_output_blocks_and_json_contract_examples source=resources/prompt_blocks/phase/write/appearance_update_detail_output_blocks_and_json_contract_examples.md repeat=1/1 -->
  - appearance_updates.set may include atoms and marks only (canonical truth).
    - Do NOT put marks_add at the top level; it belongs under set.
    - Use set.marks_add / set.marks_remove for marks changes.
    - Use set.atoms for atom changes.
  - appearance_updates.reason is required (brief, factual).
  - Do NOT set summary or art text in appearance_updates (derived after acceptance)
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - character_updates.inventory MUST be an array of objects, never string item ids.
  - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:

  - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.

  - inventory: CHAR_example -> shard (carried, container=satchel)
  - inventory: CHAR_example -> longsword (carried, container=hand_right)
  - container: satchel (owner=CHAR_example, contents=[shard, maps])
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
  - injury: right forearm scar / left arm filament
  - ownership: shard (carried) / shard (bound but physical)

Scene card:
{{scene_card}}

Continuity pack:
{{continuity_pack}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

Style anchor:
{{style_anchor}}

State:
{{state}}

Output (required, no code fences):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>

Current arm-side / inventory facts: <from must_stay_true>

Durable changes committed: <final durable values to record in continuity updates>

APPEARANCE_CHECK:
- CHAR_ID: <4-8 tokens from atoms/marks>

PROSE:
<scene prose>
STATE_PATCH:
<json>

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}


<!-- end entry=E014 semantic=write.appearance_update_detail_output_blocks_and_json_contract_examples -->
<!-- begin entry=E015 semantic=write.updates_arrays_only_contract_block source=resources/prompt_blocks/shared/json_contract/updates_arrays_only_contract_block.md repeat=1/1 -->
JSON Contract Block (strict; arrays only):
- All *_updates must be arrays of objects, even when there is only one update.
- INVALID vs VALID examples:
  - item_registry_updates:
    - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
    - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates:
    - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
    - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
  - transfer_updates:
    - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
    - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
  - inventory_alignment_updates:
    - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
    - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
  - global_continuity_system_updates:
    - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
    - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- custodian must be a non-null string id or "world"; never null.

<!-- end entry=E015 semantic=write.updates_arrays_only_contract_block -->
