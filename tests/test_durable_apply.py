from pathlib import Path
import json

import pytest

from bookforge.characters import create_character_state_path
from bookforge.memory.durable_state import ensure_durable_state_files, load_item_registry, load_durable_commits, save_item_registry
from bookforge.runner import _apply_durable_state_updates


def _book_root(tmp_path: Path) -> Path:
    root = tmp_path / "books" / "demo_book"
    (root / "draft" / "context").mkdir(parents=True, exist_ok=True)
    ensure_durable_state_files(root)
    return root


def _write_character_state(book_root: Path, character_id: str, inventory: list[dict]) -> Path:
    path = create_character_state_path(book_root, character_id)
    payload = {
        "schema_version": "1.0",
        "character_id": character_id,
        "inventory": inventory,
        "containers": [],
        "invariants": [],
        "history": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def test_apply_durable_transfer_updates_registry_and_character_states(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    save_item_registry(
        book_root,
        {
            "schema_version": "1.0",
            "items": [
                {
                    "item_id": "ITEM_sword",
                    "name": "Broken Tutorial Sword",
                    "type": "weapon",
                    "owner_scope": "character",
                    "custodian": "CHAR_artie",
                    "linked_threads": [],
                    "state_tags": ["carried"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "office"},
                }
            ],
        },
    )

    artie = _write_character_state(
        book_root,
        "CHAR_artie",
        [{"item_id": "ITEM_sword", "item": "Broken Tutorial Sword", "container": "hand_right", "status": "carried"}],
    )
    _write_character_state(book_root, "CHAR_fizz", [])

    patch = {
        "schema_version": "1.0",
        "transfer_updates": [
            {
                "item_id": "ITEM_sword",
                "from": {"character_id": "CHAR_artie"},
                "to": {"character_id": "CHAR_fizz", "container": "hand_right", "status": "carried"},
                "reason": "Fizz grabs the sword.",
                "reason_category": "handoff_transfer",
            }
        ],
    }

    changed = _apply_durable_state_updates(
        book_root=book_root,
        patch=patch,
        chapter=1,
        scene=2,
        phase="scene",
        state={"world": {"location": "market"}},
    )

    assert changed is True

    registry = load_item_registry(book_root)
    item = registry["items"][0]
    assert item["custodian"] == "CHAR_fizz"
    assert item["last_seen"]["chapter"] == 1
    assert item["last_seen"]["scene"] == 2

    artie_state = json.loads(artie.read_text(encoding="utf-8"))
    assert artie_state["inventory"] == []

    fizz_path = create_character_state_path(book_root, "CHAR_fizz")
    fizz_state = json.loads(fizz_path.read_text(encoding="utf-8"))
    assert any(str(entry.get("item_id")) == "ITEM_sword" for entry in fizz_state.get("inventory", []))

    # Same exact mutation hash should be deduped.
    changed_again = _apply_durable_state_updates(
        book_root=book_root,
        patch=patch,
        chapter=1,
        scene=2,
        phase="scene",
        state={"world": {"location": "market"}},
    )
    assert changed_again is False

    commits = load_durable_commits(book_root)
    assert len(commits.get("applied_hashes", [])) == 1


def test_apply_durable_updates_precondition_mismatch_fails(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    save_item_registry(
        book_root,
        {
            "schema_version": "1.0",
            "items": [
                {
                    "item_id": "ITEM_letter",
                    "name": "Sealed Letter",
                    "type": "quest",
                    "owner_scope": "character",
                    "custodian": "CHAR_a",
                    "linked_threads": [],
                    "state_tags": ["sealed"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "inn"},
                }
            ],
        },
    )

    patch = {
        "schema_version": "1.0",
        "item_registry_updates": [
            {
                "item_id": "ITEM_letter",
                "expected_before": {"custodian": "CHAR_not_a"},
                "set": {"custodian": "CHAR_b"},
                "reason": "handoff",
            }
        ],
    }

    with pytest.raises(ValueError, match="Durable precondition mismatch"):
        _apply_durable_state_updates(
            book_root=book_root,
            patch=patch,
            chapter=1,
            scene=2,
            phase="scene",
            state={"world": {"location": "inn"}},
        )
