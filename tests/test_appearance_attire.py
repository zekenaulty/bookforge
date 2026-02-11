from bookforge.pipeline.appearance import _with_derived_attire


def test_with_derived_attire_uses_equipped_items() -> None:
    character_states = [
        {
            "character_id": "CHAR_A",
            "inventory": [
                {"item": "ITEM_HAT", "status": "equipped"},
                {"item": "ITEM_SWORD", "status": "carried"},
            ],
            "appearance_current": {"atoms": {"hair_color": "brown"}},
        }
    ]
    item_registry = {
        "items": [
            {"item_id": "ITEM_HAT", "display_name": "Wool Cap"},
            {"item_id": "ITEM_SWORD", "display_name": "Rusty Sword"},
        ]
    }
    enriched = _with_derived_attire(character_states, item_registry)
    assert enriched[0]["appearance_current"]["attire"]["mode"] == "derived"
    assert enriched[0]["appearance_current"]["attire"]["items"] == ["Wool Cap"]


def test_with_derived_attire_skips_signature_mode() -> None:
    character_states = [
        {
            "character_id": "CHAR_A",
            "inventory": [{"item": "ITEM_HAT", "status": "equipped"}],
            "appearance_current": {"attire": {"mode": "signature", "items": ["Iconic Hat"]}},
        }
    ]
    item_registry = {"items": [{"item_id": "ITEM_HAT", "display_name": "Wool Cap"}]}
    enriched = _with_derived_attire(character_states, item_registry)
    assert enriched[0]["appearance_current"]["attire"]["mode"] == "signature"
    assert enriched[0]["appearance_current"]["attire"]["items"] == ["Iconic Hat"]
