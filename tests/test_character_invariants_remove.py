from pathlib import Path
import json

from bookforge.characters import create_character_state_path
from bookforge.pipeline.state_apply import _apply_character_updates
from bookforge.query import list_appearance_projection_views


def test_character_invariants_remove_from_summary(tmp_path: Path) -> None:
    book_root = tmp_path / "book"
    state_path = create_character_state_path(book_root, "CHAR_ARTIE")
    state = {
        "schema_version": "1.0",
        "character_id": "CHAR_ARTIE",
        "inventory": [],
        "containers": [],
        "invariants": [
            "Artie HP is 0/0 (deceased).",
            "inventory: CHAR_ARTIE -> rusted key (status=carried, container=pocket)",
        ],
        "history": [],
    }
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    patch = {
        "summary_update": {
            "must_stay_true": [
                "REMOVE: Artie HP is 0/0 (deceased).",
                "Artie HP is locked at 1/1.",
            ]
        },
        "character_updates": [
            {
                "character_id": "CHAR_ARTIE",
                "chapter": 1,
                "scene": 1,
                "inventory": [],
                "containers": [],
                "invariants_add": ["Artie HP is locked at 1/1."],
            }
        ],
    }

    _apply_character_updates(book_root, patch, 1, 1)

    updated = json.loads(state_path.read_text(encoding="utf-8"))
    invariants = updated.get("invariants", [])
    assert "Artie HP is 0/0 (deceased)." not in invariants
    assert "Artie HP is locked at 1/1." in invariants


def test_apply_character_updates_reconciles_conflicting_inventory_invariants(tmp_path: Path) -> None:
    book_root = tmp_path / "book"
    state_path = create_character_state_path(book_root, "CHAR_VANE")
    state = {
        "schema_version": "1.0",
        "character_id": "CHAR_VANE",
        "name": "Vane",
        "inventory": [
            {"item": "ITEM_OBSIDIAN_BLADE", "status": "held", "container": "hand_right"}
        ],
        "containers": [
            {"container": "hand_right", "owner": "CHAR_VANE", "contents": ["ITEM_OBSIDIAN_BLADE"]},
            {"container": "back_sheath", "owner": "CHAR_VANE", "contents": []},
        ],
        "invariants": [
            "inventory: CHAR_VANE -> Obsidian Greatsword (status=equipped, container=back_sheath)",
            "inventory: CHAR_VANE -> Obsidian Greatsword (status=held, container=hand_right)",
        ],
        "history": [],
    }
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    patch = {
        "summary_update": {
            "must_stay_true": [
                "inventory: CHAR_VANE -> Obsidian Greatsword (status=held, container=hand_right)",
            ]
        },
        "character_updates": [
            {
                "character_id": "CHAR_VANE",
                "chapter": 1,
                "scene": 8,
                "inventory": [
                    {"item": "ITEM_OBSIDIAN_BLADE", "status": "held", "container": "hand_right"}
                ],
                "containers": [
                    {"container": "hand_right", "owner": "CHAR_VANE", "contents": ["ITEM_OBSIDIAN_BLADE"]},
                    {"container": "back_sheath", "owner": "CHAR_VANE", "contents": []},
                ],
                "invariants_add": [],
            }
        ],
    }

    _apply_character_updates(book_root, patch, 1, 8)

    updated = json.loads(state_path.read_text(encoding="utf-8"))
    invariants = updated.get("invariants", [])
    assert "inventory: CHAR_VANE -> Obsidian Greatsword (status=held, container=hand_right)" in invariants
    assert "inventory: CHAR_VANE -> Obsidian Greatsword (status=equipped, container=back_sheath)" not in invariants


def test_apply_character_updates_marks_appearance_projection_pending(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo_book"
    state_path = create_character_state_path(book_root, "CHAR_RHEA")
    state_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "character_id": "CHAR_RHEA",
                "name": "Rhea",
                "appearance_current": {"atoms": {"hair_color": "black"}, "marks": []},
                "appearance_projection_pending": False,
                "history": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    patch = {
        "character_updates": [
            {
                "character_id": "CHAR_RHEA",
                "chapter": 1,
                "scene": 2,
                "appearance_updates": {
                    "set": {
                        "marks_add": [{"name": "ash smear", "location": "cheek"}],
                    },
                    "reason": "Rhea crawled through the firebreak.",
                },
            }
        ]
    }

    _apply_character_updates(book_root, patch, 1, 2)

    updated = json.loads(state_path.read_text(encoding="utf-8"))
    assert updated["appearance_projection_pending"] is True
    [view] = list_appearance_projection_views(
        tmp_path,
        "demo_book",
        chapter_id=1,
        scene_id=2,
        character_id="CHAR_RHEA",
        prefer_emitted=False,
    )
    assert view.appearance_status == "stale"
    assert view.artifact_status == "provisional"
    assert view.staleness_reason == "appearance_projection_pending"

