from bookforge.runner import (
    _apply_bag_updates,
    _coerce_stat_updates,
    _coerce_transfer_updates,
    _coerce_inventory_alignment_updates,
    _coerce_character_updates,
    _heuristic_invariant_issues,
    _pov_drift_issues,
    _extract_authoritative_surfaces,
    _stat_mismatch_issues,
    _durable_scene_constraint_issues,
    _linked_durable_consistency_issues,
)


def test_apply_bag_updates_set_wins_over_delta_for_same_key() -> None:
    bag = {
        "stamina": 20,
        "hp": {"current": 1, "max": 1},
    }
    updates = {
        "set": {
            "stamina": 100,
            "hp": {"current": 5, "max": 5},
        },
        "delta": {
            "stamina": 5,
            "hp": {"current": 2},
            "agility": 3,
        },
    }

    _apply_bag_updates(bag, updates)

    assert bag["stamina"] == 100
    assert bag["hp"]["current"] == 5
    assert bag["agility"] == 3


def test_milestone_duplicate_detected_for_shard_bind() -> None:
    invariants = ["milestone: shard_bind = DONE"]
    prose = "He bound and then binding the shard to his bloodline in a panic."

    issues = _heuristic_invariant_issues(prose, {}, invariants, [])

    assert any(issue.get("code") == "milestone_duplicate" for issue in issues)


def test_milestone_early_detected_for_maps_acquired() -> None:
    invariants = ["milestone: maps_acquired = NOT_YET"]
    prose = "She retrieved the maps and unfurled them on the table."

    issues = _heuristic_invariant_issues(prose, {}, invariants, [])

    assert any(issue.get("code") == "milestone_future" for issue in issues)


def test_pov_drift_detects_first_person_in_third_person() -> None:
    issues = _pov_drift_issues("I run through the gate while he watches.", "third_limited")

    assert any(issue.get("code") == "pov_drift" for issue in issues)


def test_pov_drift_strict_flags_error() -> None:
    issues = _pov_drift_issues("I run through the gate.", "third_limited", strict=True)

    assert any(issue.get("code") == "pov_drift" and issue.get("severity") == "error" for issue in issues)


def test_stat_mismatch_uses_any_cast_member_match() -> None:
    prose = "[HP: 10/10]"
    character_states = [
        {"character_id": "CHAR_a", "stats": {"hp": {"current": 1, "max": 1}}},
        {"character_id": "CHAR_b", "stats": {"hp": {"current": 10, "max": 10}}},
    ]

    issues = _stat_mismatch_issues(prose, character_states, {})

    assert not any(issue.get("code") == "stat_mismatch" for issue in issues)
    assert not any(issue.get("code") == "stat_unowned" for issue in issues)


def test_stat_mismatch_warns_when_no_candidate_matches() -> None:
    prose = "[Stamina: 42/100]"
    character_states = [
        {"character_id": "CHAR_a", "stats": {"stamina": {"current": 20, "max": 20}}},
    ]

    issues = _stat_mismatch_issues(prose, character_states, {})

    assert any(issue.get("code") == "stat_mismatch" for issue in issues)


def test_stat_mismatch_skips_ambiguous_multi_cast_without_owner() -> None:
    prose = "[Stamina: 42/100]"
    character_states = [
        {"character_id": "CHAR_a", "stats": {"stamina": {"current": 20, "max": 20}}},
        {"character_id": "CHAR_b", "stats": {"stamina": {"current": 30, "max": 100}}},
    ]

    issues = _stat_mismatch_issues(prose, character_states, {})

    assert not any(issue.get("code") in {"stat_mismatch", "stat_unowned"} for issue in issues)


def test_stat_unowned_when_missing_in_cast_and_run() -> None:
    prose = "[MP: 7/10]"
    character_states = [{"character_id": "CHAR_a", "stats": {"hp": {"current": 1, "max": 1}}}]

    issues = _stat_mismatch_issues(prose, character_states, {})

    assert any(issue.get("code") == "stat_unowned" for issue in issues)


def test_stat_mismatch_owner_key_uses_matching_cast_member() -> None:
    prose = "[Artie HP: 1/1]"
    character_states = [
        {
            "character_id": "CHAR_artie",
            "name": "Artie",
            "character_continuity_system_state": {"stats": {"hp": {"current": 1, "max": 1}}},
        },
        {
            "character_id": "CHAR_fizz",
            "name": "Fizz",
            "character_continuity_system_state": {"stats": {"hp": {"current": 10, "max": 10}}},
        },
    ]

    issues = _stat_mismatch_issues(prose, character_states, {})

    assert not any(issue.get("code") == "stat_mismatch" for issue in issues)
    assert not any(issue.get("code") == "stat_unowned" for issue in issues)


def test_stat_mismatch_owner_key_does_not_fallback_to_other_cast() -> None:
    prose = "[Artie HP: 10/10]"
    character_states = [
        {
            "character_id": "CHAR_artie",
            "name": "Artie",
            "character_continuity_system_state": {"stats": {"hp": {"current": 1, "max": 1}}},
        },
        {
            "character_id": "CHAR_fizz",
            "name": "Fizz",
            "character_continuity_system_state": {"stats": {"hp": {"current": 10, "max": 10}}},
        },
    ]

    issues = _stat_mismatch_issues(prose, character_states, {})

    assert any(issue.get("code") == "stat_mismatch" for issue in issues)


def test_coerce_stat_updates_folds_dynamic_top_level_fields_into_set() -> None:
    patch = {
        "character_continuity_system_updates": [
            {
                "character_id": "CHAR_artie",
                "stats": {"hp": {"current": 1, "max": 1}},
                "titles": ["Anomaly"],
                "system_tracking_metadata": {"ui_theme": "retro"},
                "custom_mechanic_sheet": {"crit_chain": 3},
            }
        ]
    }

    _coerce_stat_updates(patch)
    updates = patch["character_continuity_system_updates"][0]
    set_block = updates.get("set", {})

    assert set_block.get("stats", {}).get("hp", {}).get("current") == 1
    assert set_block.get("titles") == [{"name": "Anomaly"}]
    assert set_block.get("system_tracking_metadata", {}).get("ui_theme") == "retro"
    assert set_block.get("custom_mechanic_sheet", {}).get("crit_chain") == 3


def test_coerce_stat_updates_normalizes_title_objects_from_mixed_values() -> None:
    patch = {
        "character_continuity_system_updates": [
            {
                "character_id": "CHAR_artie",
                "set": {
                    "titles": ["Novice", {"title": "Anomaly", "source": "system"}],
                },
            }
        ]
    }

    _coerce_stat_updates(patch)
    set_block = patch["character_continuity_system_updates"][0].get("set", {})

    assert set_block.get("titles") == [
        {"name": "Novice"},
        {"title": "Anomaly", "source": "system", "name": "Anomaly"},
    ]


def test_authoritative_surfaces_extracts_ui_blocks() -> None:
    prose = """Narrative line.
[HP: 1/1]
[System Notification: Entering Oakhaven]
[Warning: Near-Miss!]
Another line."""

    surfaces = _extract_authoritative_surfaces(prose)

    assert len(surfaces) == 3
    assert surfaces[0]["kind"] == "ui_stat"
    assert surfaces[1]["kind"] == "system_notification"


def test_stat_mismatch_uses_only_authoritative_surfaces_when_provided() -> None:
    prose = "Narrative with [HP: 999/999] in dialogue but no actual UI block."
    character_states = [{"character_id": "CHAR_a", "stats": {"hp": {"current": 1, "max": 1}}}]
    authoritative_surfaces = []

    issues = _stat_mismatch_issues(
        prose,
        character_states,
        {},
        authoritative_surfaces=authoritative_surfaces,
    )

    # No authoritative UI surfaces means no UI stat drift check for this text.
    assert not any(issue.get("code") in {"stat_mismatch", "stat_unowned"} for issue in issues)

def test_durable_scene_constraint_detects_required_access_failure() -> None:
    prose = "Narrative only."
    scene_card = {"required_scene_accessible": ["ITEM_sword"]}
    durable = {
        "item_registry": {
            "items": [
                {
                    "item_id": "ITEM_sword",
                    "name": "Broken Tutorial Sword",
                    "derived_scene_accessible": False,
                    "derived_access_reason": "location_mismatch",
                }
            ]
        },
        "plot_devices": {"devices": []},
    }

    issues = _durable_scene_constraint_issues(prose, scene_card, durable)

    assert any(issue.get("code") == "durable_required_inaccessible" for issue in issues)


def test_durable_scene_constraint_detects_required_visible_on_page_missing() -> None:
    prose = "Artie runs through the alley."
    scene_card = {"required_visible_on_page": ["ITEM_sword"]}
    durable = {
        "item_registry": {
            "items": [
                {
                    "item_id": "ITEM_sword",
                    "name": "Broken Tutorial Sword",
                    "aliases": ["tutorial blade"],
                    "derived_scene_accessible": True,
                    "derived_visible": True,
                }
            ]
        },
        "plot_devices": {"devices": []},
    }

    issues = _durable_scene_constraint_issues(prose, scene_card, durable)

    assert any(issue.get("code") == "durable_required_visible_missing" for issue in issues)


def test_durable_scene_constraint_detects_slice_missing() -> None:
    issues = _durable_scene_constraint_issues(
        "Prose",
        {"required_in_custody": ["ITEM_missing"]},
        {"item_registry": {"items": []}, "plot_devices": {"devices": []}},
    )

    assert any(issue.get("code") == "durable_slice_missing" for issue in issues)


def test_linked_durable_consistency_detects_tombstone_activation_conflict() -> None:
    durable = {
        "item_registry": {
            "items": [
                {
                    "item_id": "ITEM_shard",
                    "name": "Shard",
                    "state_tags": ["destroyed"],
                    "custodian": "CHAR_artie",
                    "linked_device_id": "DEV_shard_core",
                }
            ]
        },
        "plot_devices": {
            "devices": [
                {
                    "device_id": "DEV_shard_core",
                    "name": "Shard Core",
                    "activation_state": "active",
                    "custody_scope": "character",
                    "custody_ref": "CHAR_artie",
                }
            ]
        },
    }

    issues = _linked_durable_consistency_issues(durable)

    assert any(issue.get("code") == "durable_link_state_conflict" for issue in issues)


def test_coerce_character_updates_converts_string_inventory_from_alignment_and_containers() -> None:
    patch = {
        "inventory_alignment_updates": [
            {
                "character_id": "CHAR_ARTIE",
                "inventory": [
                    {"item": "ITEM_smartphone_dead_1dc98ace", "container": "hand_right", "status": "held"},
                    {"item": "ITEM_pocket_lint_d2b2744e", "container": "pockets", "status": "stowed"},
                ],
            }
        ],
        "character_updates": [
            {
                "character_id": "CHAR_ARTIE",
                "chapter": 1,
                "scene": 1,
                "inventory": ["ITEM_smartphone_dead_1dc98ace", "ITEM_pocket_lint_d2b2744e"],
                "containers": [
                    {"container": "hand_right", "contents": ["ITEM_smartphone_dead_1dc98ace"]},
                    {"container": "pockets", "contents": ["ITEM_pocket_lint_d2b2744e"]},
                ],
                "persona_updates": [],
                "invariants_add": [],
            }
        ],
    }

    _coerce_character_updates(patch)

    inventory = patch["character_updates"][0]["inventory"]
    assert isinstance(inventory, list)
    assert inventory[0]["item"] == "ITEM_smartphone_dead_1dc98ace"
    assert inventory[0]["container"] == "hand_right"
    assert inventory[0]["status"] == "held"
    assert inventory[1]["item"] == "ITEM_pocket_lint_d2b2744e"
    assert inventory[1]["container"] == "pockets"
    assert inventory[1]["status"] == "stowed"


def test_coerce_character_updates_normalizes_dict_item_id_and_derived_status() -> None:
    patch = {
        "character_updates": [
            {
                "character_id": "CHAR_ARTIE",
                "chapter": 1,
                "scene": 1,
                "inventory": [{"item_id": "ITEM_broken_tutorial_sword", "container": "hand_left"}],
                "containers": [],
                "persona_updates": [],
                "invariants_add": [],
            }
        ]
    }

    _coerce_character_updates(patch)

    inventory = patch["character_updates"][0]["inventory"]
    assert inventory == [{"item_id": "ITEM_broken_tutorial_sword", "container": "hand_left", "item": "ITEM_broken_tutorial_sword", "status": "held"}]


def test_coerce_transfer_updates_adds_required_reason_when_missing() -> None:
    patch = {
        "transfer_updates": [
            {
                "item_id": "ITEM_broken_tutorial_sword",
                "from": "bad",
                "to": {"character_id": "CHAR_ARTIE"},
                "reason_category": "after_combat_cleanup",
            }
        ]
    }

    _coerce_transfer_updates(patch)

    updates = patch["transfer_updates"]
    assert isinstance(updates, list) and len(updates) == 1
    assert updates[0]["reason"] == "after_combat_cleanup"
    assert updates[0]["from"] == {}


def test_coerce_transfer_updates_uses_default_reason_when_missing_category() -> None:
    patch = {"transfer_updates": [{"item_id": "ITEM_pocket_lint"}]}

    _coerce_transfer_updates(patch)

    assert patch["transfer_updates"][0]["reason"] == "transfer_alignment"


def test_coerce_inventory_alignment_updates_unwraps_object() -> None:
    patch = {
        "inventory_alignment_updates": {
            "reason_category": "location_jump_normalize",
            "updates": [
                {"character_id": "CHAR_ARTIE", "inventory": [{"item": "ITEM_x"}]}
            ],
        }
    }

    _coerce_inventory_alignment_updates(patch)

    updates = patch["inventory_alignment_updates"]
    assert isinstance(updates, list)
    assert updates[0]["character_id"] == "CHAR_ARTIE"
    assert updates[0]["reason_category"] == "location_jump_normalize"


def test_pov_drift_ignores_first_person_dialogue() -> None:
    prose = "He said, \"I will go now,\" and left."
    issues = _pov_drift_issues(prose, "third_limited")
    assert not issues
