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
