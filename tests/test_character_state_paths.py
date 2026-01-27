import json
from pathlib import Path

from bookforge.characters import _character_state_filename
from bookforge.runner import _load_character_states


def test_character_state_filename_unique() -> None:
    name_a = _character_state_filename("CHAR_A-1")
    name_b = _character_state_filename("CHAR_A 1")
    assert name_a != name_b


def test_load_character_states_uses_index(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "testbook"
    characters_dir = book_root / "draft" / "context" / "characters"
    characters_dir.mkdir(parents=True)

    char_id = "CHAR_KAELEN"
    state_path = characters_dir / _character_state_filename(char_id)
    state_path.write_text(json.dumps({"character_id": char_id}), encoding="utf-8")

    index_path = characters_dir / "index.json"
    index_path.write_text(
        json.dumps({
            "characters": [
                {
                    "character_id": char_id,
                    "state_path": str(state_path.relative_to(book_root)).replace("\\", "/"),
                }
            ]
        }),
        encoding="utf-8",
    )

    scene_card = {"cast_present_ids": [char_id]}
    states = _load_character_states(book_root, scene_card)
    assert len(states) == 1
    assert states[0].get("character_id") == char_id
