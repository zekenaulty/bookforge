from bookforge.pipeline.lint.helpers import _merged_character_states_for_lint


def test_merged_character_states_applies_continuity_updates() -> None:
    character_states = [
        {
            "character_id": "CHAR_A",
            "name": "Alice",
            "character_continuity_system_state": {
                "stats": {"hp_max": 10},
                "titles": [],
            },
        }
    ]
    patch = {
        "character_continuity_system_updates": [
            {
                "character_id": "CHAR_A",
                "set": {
                    "stats": {"hp_max": 1, "stat_points": 0},
                    "titles": [{"name": "Novice"}],
                },
            }
        ]
    }
    merged = _merged_character_states_for_lint(character_states, patch)
    assert len(merged) == 1
    state = merged[0]
    continuity = state.get("character_continuity_system_state", {})
    stats = continuity.get("stats", {})
    assert stats.get("hp_max") == 1
    assert stats.get("stat_points") == 0
    assert any(title.get("name") == "Novice" for title in continuity.get("titles", []))
    assert state.get("stats", {}).get("hp_max") == 1

def test_merged_character_states_applies_appearance_updates() -> None:
    character_states = [
        {
            "character_id": "CHAR_A",
            "appearance_current": {"atoms": {"hair_color": "brown"}, "marks": []},
        }
    ]
    patch = {
        "character_updates": [
            {
                "character_id": "CHAR_A",
                "appearance_updates": {
                    "set": {
                        "atoms": {"hair_color": "blonde"},
                        "marks_add": [{"name": "scar", "location": "brow"}],
                    }
                },
            }
        ]
    }
    merged = _merged_character_states_for_lint(character_states, patch)
    assert len(merged) == 1
    appearance = merged[0].get("appearance_current", {})
    assert appearance.get("atoms", {}).get("hair_color") == "blonde"
    assert {"name": "scar", "location": "brow"} in appearance.get("marks", [])


def test_merged_character_states_applies_summary_remove_to_invariants() -> None:
    character_states = [
        {
            "character_id": "CHAR_ARTIE",
            "name": "Artie",
            "invariants": [
                "inventory: CHAR_ARTIE -> Leather Wallet (status=carried, container=hand_right)",
                "inventory: CHAR_ARTIE -> Corporate ID Badge (status=equipped, container=neck)",
            ],
            "inventory": [
                {"item": "ITEM_ID_BADGE", "status": "equipped", "container": "neck"}
            ],
            "containers": [
                {"container": "neck", "owner": "CHAR_ARTIE", "contents": ["ITEM_ID_BADGE"]}
            ],
        }
    ]
    patch = {
        "summary_update": {
            "must_stay_true": [
                "REMOVE: inventory: CHAR_ARTIE -> Leather Wallet (status=carried, container=hand_right)",
                "inventory: world -> Leather Wallet (status=dropped, container=floor)",
            ]
        }
    }

    merged = _merged_character_states_for_lint(character_states, patch)
    invariants = merged[0].get("invariants", [])
    assert "inventory: CHAR_ARTIE -> Leather Wallet (status=carried, container=hand_right)" not in invariants


def test_merged_character_states_reconciles_inventory_posture_without_remove() -> None:
    character_states = [
        {
            "character_id": "CHAR_VANE",
            "name": "Vane",
            "invariants": [
                "inventory: CHAR_VANE -> Obsidian Greatsword (status=equipped, container=back_sheath)",
                "inventory: CHAR_VANE -> Obsidian Greatsword (status=held, container=hand_right)",
            ],
            "inventory": [
                {"item": "ITEM_OBSIDIAN_BLADE", "status": "held", "container": "hand_right"}
            ],
            "containers": [
                {"container": "hand_right", "owner": "CHAR_VANE", "contents": ["ITEM_OBSIDIAN_BLADE"]},
                {"container": "back_sheath", "owner": "CHAR_VANE", "contents": []},
            ],
        }
    ]
    patch = {
        "summary_update": {
            "must_stay_true": [
                "inventory: CHAR_VANE -> Obsidian Greatsword (status=held, container=hand_right)"
            ]
        }
    }

    merged = _merged_character_states_for_lint(character_states, patch)
    invariants = merged[0].get("invariants", [])
    assert "inventory: CHAR_VANE -> Obsidian Greatsword (status=held, container=hand_right)" in invariants
    assert "inventory: CHAR_VANE -> Obsidian Greatsword (status=equipped, container=back_sheath)" not in invariants


def test_reconciliation_skips_when_summary_conflicts_with_structured_state() -> None:
    character_states = [
        {
            "character_id": "CHAR_VANE",
            "name": "Vane",
            "invariants": [
                "inventory: CHAR_VANE -> Obsidian Greatsword (status=equipped, container=back_sheath)",
            ],
            "inventory": [
                {"item": "ITEM_OBSIDIAN_BLADE", "status": "held", "container": "hand_right"}
            ],
            "containers": [
                {"container": "hand_right", "owner": "CHAR_VANE", "contents": ["ITEM_OBSIDIAN_BLADE"]},
                {"container": "back_sheath", "owner": "CHAR_VANE", "contents": []},
            ],
        }
    ]
    patch = {
        "summary_update": {
            "must_stay_true": [
                "inventory: CHAR_VANE -> Obsidian Greatsword (status=equipped, container=back_sheath)"
            ]
        }
    }

    merged = _merged_character_states_for_lint(character_states, patch)
    invariants = merged[0].get("invariants", [])
    assert invariants == [
        "inventory: CHAR_VANE -> Obsidian Greatsword (status=equipped, container=back_sheath)"
    ]

