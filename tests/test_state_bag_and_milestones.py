from bookforge.runner import (
    _apply_bag_updates,
    _coerce_stat_updates,
    _heuristic_invariant_issues,
    _pov_drift_issues,
    _stat_mismatch_issues,
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

    issues = _heuristic_invariant_issues(prose, {}, invariants)

    assert any(issue.get("code") == "milestone_duplicate" for issue in issues)


def test_milestone_early_detected_for_maps_acquired() -> None:
    invariants = ["milestone: maps_acquired = NOT_YET"]
    prose = "She retrieved the maps and unfurled them on the table."

    issues = _heuristic_invariant_issues(prose, {}, invariants)

    assert any(issue.get("code") == "milestone_future" for issue in issues)


def test_pov_drift_detects_first_person_in_third_person() -> None:
    issues = _pov_drift_issues("I run through the gate while he watches.", "third_limited")

    assert any(issue.get("code") == "pov_drift" for issue in issues)


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
        {"character_id": "CHAR_b", "stats": {"stamina": {"current": 30, "max": 100}}},
    ]

    issues = _stat_mismatch_issues(prose, character_states, {})

    assert any(issue.get("code") == "stat_mismatch" for issue in issues)


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
