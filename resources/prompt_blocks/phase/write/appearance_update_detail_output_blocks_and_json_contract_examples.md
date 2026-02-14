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


