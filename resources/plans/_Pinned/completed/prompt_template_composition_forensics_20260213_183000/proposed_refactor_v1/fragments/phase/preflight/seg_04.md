
Scene card:
{{scene_card}}

Current state:
{{state}}

Current summary:
{{summary}}

Character registry:
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (cast only):
{{character_states}}

Immediate previous scene (if available):
{{immediate_previous_scene}}

Last appearance prose for cast members missing from immediate previous scene:
{{cast_last_appearance}}

Output JSON shape reminder:
{
  "schema_version": "1.0",
  "character_updates": [
    {
      "character_id": "CHAR_example",
      "chapter": 1,
      "scene": 2,
      "inventory": [{"item": "ITEM_example", "container": "pockets", "status": "stowed"}],
      "containers": [],
      "persona_updates": [],
      "invariants_add": [],
      "notes": ""
    }
  ],
  "character_continuity_system_updates": [
    {
      "character_id": "CHAR_example",
      "set": {
        "titles": [{"name": "Novice"}]
      },
      "delta": {},
      "remove": [],
      "reason": "align pre-scene state"
    }
  ],
  "global_continuity_system_updates": [],
  "inventory_alignment_updates": [
    {
      "character_id": "CHAR_example",
      "set": {"inventory": [{"item": "ITEM_example", "container": "hand_right", "status": "held"}], "containers": []},
      "reason": "scene posture alignment",
      "reason_category": "after_combat_cleanup"
    }
  ],
  "item_registry_updates": [],
  "plot_device_updates": [],
  "transfer_updates": []
}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}


