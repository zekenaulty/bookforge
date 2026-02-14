Transition gate (do-nothing by default):
- First decide whether this scene is a CONTINUATION or a DISCONTINUOUS TRANSITION.
- Treat as CONTINUATION when ALL are true:
  - scene_card.scene_target matches state.world.location, AND
  - scene_card.timeline_scope and scene_card.ontological_scope do not change relative to current state, AND
  - scene_card.transition_type is empty OR clearly indicates continuity (e.g., "continuous", "beat", "direct_continuation"), AND
  - there is no durable-constraint violation to fix.
- If CONTINUATION:
  - Output the minimal patch: {"schema_version":"1.0"} (no other fields), unless a durable constraint is violated.
  - Do NOT "normalize" inventory posture or move items just to be scene-appropriate. Only fix actual contradictions.
- Treat as DISCONTINUOUS TRANSITION when ANY are true:
  - scene_card.scene_target differs from state.world.location, OR
  - scene_card.transition_type is present and not clearly continuous, OR
  - timeline_scope / ontological_scope indicates a scope shift, OR
  - cast_present for this scene differs materially from state.world.cast_present.

World alignment (only when needed for this scene):
- If state.world.location != scene_card.scene_target, set world_updates.location = scene_card.scene_target.
- If scene_card.cast_present_ids is provided and differs from state.world.cast_present, set world_updates.cast_present = scene_card.cast_present_ids.
- Do not modify world.time unless the scene card explicitly implies a non-present timeline_scope; if you must, record why in global_continuity_system_updates.

Hidden transition state policy:
- Posture changes (stowed/held/worn, hand->pack, pack->table, etc.) are allowed ONLY during DISCONTINUOUS TRANSITION, or to satisfy a durable constraint.
- Custody changes (an item is no longer in the character's possession / custodian changes scope) are NOT implied by posture changes.
  - If and only if custody changes, you MUST:
    - update item_registry_updates for that item (custodian + last_seen), and
    - include transfer_updates with a reason (and prefer adding expected_before).
- Never "drop" an item by omitting it from an inventory array. If an item leaves a character, represent it as an explicit transfer.

Inventory transition rules:
Appearance contract:
- appearance_current atoms/marks are canonical and must not be contradicted or mutated in preflight.
- Preflight does NOT invent or change appearance; only note missing appearance_current if present in character_states.
- Ensure carried/equipped/stowed posture is scene-appropriate.
- character_updates.inventory and inventory_alignment_updates.set.inventory must be arrays of inventory objects, never id strings.
- Preserve ownership and container consistency.
- For held items use `container=hand_left` or `container=hand_right`.

Durable-constraint compliance check (must run before output):
1) Resolve constraint tokens:
   - Treat entries in required_in_custody / required_scene_accessible / required_visible_on_page / forbidden_visible / device_presence as IDs when they look like IDs.
   - If an entry does not match an ID, attempt a best-effort lookup by name/alias in item_registry / plot_devices.
   - If still ambiguous, do not guess; leave unchanged and record the unresolved token in character_updates.notes for the most relevant cast member.
2) Enforce required_in_custody:
   - Ensure the specified item's custodian is the required character/scope.
   - Ensure the item appears in that character's inventory in an appropriate container/status.
3) Enforce forbidden_visible:
   - Ensure the item is not in hand_left/hand_right and not "worn/brandished/visible" status.
   - Prefer moving it to an existing container (pack/pouch/sheath) over inventing new containers.
4) Enforce required_scene_accessible / required_visible_on_page:
   - Accessible: item can be stowed but present in-scene.
   - Visible_on_page: item must be held/worn/placed such that the writer can naturally show it early.

Dynamic continuity rules:
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
- Use canonical keys:
  - character_continuity_system_updates
  - global_continuity_system_updates

