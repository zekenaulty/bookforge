from pathlib import Path
import json

import pytest

from bookforge.characters import create_character_state_path
from bookforge.memory.durable_state import ensure_durable_state_files, load_item_registry, load_durable_commits, save_item_registry, save_plot_devices
from bookforge.runner import _apply_durable_state_updates, _durable_state_context, _durable_slice_retry_ids, _linked_durable_consistency_issues


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

def test_apply_durable_transfer_scope_policy_blocks_non_present_without_override(tmp_path: Path) -> None:
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

    _write_character_state(
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
                "reason": "flashback handoff",
                "reason_category": "handoff_transfer",
            }
        ],
    }

    with pytest.raises(ValueError, match="Scope policy violation"):
        _apply_durable_state_updates(
            book_root=book_root,
            patch=patch,
            chapter=1,
            scene=2,
            phase="scene",
            state={"world": {"location": "market"}},
            scene_card={"timeline_scope": "flashback", "ontological_scope": "real"},
        )


def test_apply_durable_transfer_scope_policy_allows_override(tmp_path: Path) -> None:
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

    _write_character_state(
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
                "reason": "flashback handoff",
                "reason_category": "timeline_override",
                "timeline_override": True,
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
        scene_card={"timeline_scope": "flashback", "ontological_scope": "real"},
    )

    assert changed is True


def test_apply_durable_transfer_chain_uses_first_as_source_and_last_as_destination(tmp_path: Path) -> None:
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

    patch = {
        "schema_version": "1.0",
        "transfer_updates": [
            {
                "item_id": "ITEM_sword",
                "transfer_chain": [
                    {"character_id": "CHAR_artie", "container": "hand_right", "status": "carried"},
                    {"location_ref": "LOC_inn_room_3", "container_ref": "CHEST_1", "status": "cached"},
                ],
                "reason": "Artie stashes the sword at the inn chest.",
                "reason_category": "stowed_at_inn",
            }
        ],
    }

    changed = _apply_durable_state_updates(
        book_root=book_root,
        patch=patch,
        chapter=1,
        scene=3,
        phase="scene",
        state={"world": {"location": "market"}},
        scene_card={"timeline_scope": "present", "ontological_scope": "real"},
    )

    assert changed is True
    registry = load_item_registry(book_root)
    item = registry["items"][0]
    assert item["custodian"] == "LOC_inn_room_3"
    assert item["container_ref"] == "CHEST_1"
    assert item.get("last_transfer_chain")

    artie_state = json.loads(artie.read_text(encoding="utf-8"))
    assert artie_state["inventory"] == []


def test_durable_context_derives_scene_accessibility_for_stowed_item(tmp_path: Path) -> None:
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
                    "carrier_ref": "CHAR_artie",
                    "container_ref": "pack_main",
                    "location_ref": "LOC_market",
                    "status": "stowed",
                    "linked_threads": [],
                    "state_tags": ["carried"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "market"},
                }
            ],
        },
    )

    scene_card = {"cast_present_ids": ["CHAR_artie"]}
    state_market = {"world": {"location": "LOC_market"}}
    ctx_market = _durable_state_context(book_root, state_market, scene_card)
    item_market = ctx_market["item_registry"]["items"][0]
    assert item_market["derived_scene_accessible"] is True
    assert item_market["derived_visible"] is False

    state_inn = {"world": {"location": "LOC_inn_room_3"}}
    ctx_inn = _durable_state_context(book_root, state_inn, scene_card)
    item_inn = ctx_inn["item_registry"]["items"][0]
    assert item_inn["derived_scene_accessible"] is False


def test_durable_state_context_slices_and_expands_ids(tmp_path: Path) -> None:
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
                    "carrier_ref": "CHAR_artie",
                    "status": "carried",
                    "linked_threads": [],
                    "state_tags": ["carried"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "market"},
                },
                {
                    "item_id": "ITEM_hidden_key",
                    "name": "Hidden Key",
                    "type": "quest",
                    "owner_scope": "location",
                    "custodian": "LOC_vault",
                    "location_ref": "LOC_vault",
                    "status": "cached",
                    "linked_threads": [],
                    "state_tags": ["stored"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "vault"},
                },
            ],
        },
    )

    scene_card = {"cast_present_ids": ["CHAR_artie"], "thread_ids": []}
    state = {"world": {"location": "LOC_market"}}

    sliced = _durable_state_context(book_root, state, scene_card)
    sliced_ids = {entry.get("item_id") for entry in sliced["item_registry"]["items"]}
    assert "ITEM_sword" in sliced_ids
    assert "ITEM_hidden_key" not in sliced_ids

    expanded = _durable_state_context(book_root, state, scene_card, expanded_ids=["ITEM_hidden_key"])
    expanded_ids = {entry.get("item_id") for entry in expanded["item_registry"]["items"]}
    assert "ITEM_hidden_key" in expanded_ids


def test_durable_slice_retry_ids_extracts_unique_ids() -> None:
    report = {
        "schema_version": "1.0",
        "status": "fail",
        "issues": [
            {
                "code": "durable_slice_missing",
                "message": "missing",
                "retry_hint": "expand_durable_slice:id:ITEM_alpha",
            },
            {
                "code": "durable_slice_missing",
                "message": "missing",
                "retry_hint": "expand_durable_slice:id:ITEM_beta",
            },
            {
                "code": "durable_slice_missing",
                "message": "missing",
                "retry_hint": "expand_durable_slice:id:ITEM_alpha",
            },
            {
                "code": "other",
                "message": "ignore",
                "retry_hint": "expand_durable_slice:id:ITEM_gamma",
            },
        ],
    }

    ids = _durable_slice_retry_ids(report)

    assert ids == ["ITEM_alpha", "ITEM_beta"]

def test_apply_durable_updates_blocks_out_of_order_scene_commits(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    save_item_registry(
        book_root,
        {
            "schema_version": "1.0",
            "items": [
                {
                    "item_id": "ITEM_oath",
                    "name": "Oath Sigil",
                    "type": "artifact",
                    "owner_scope": "character",
                    "custodian": "CHAR_artie",
                    "linked_threads": ["THREAD_oath"],
                    "state_tags": ["carried"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "inn"},
                }
            ],
        },
    )

    patch_newer = {
        "schema_version": "1.0",
        "item_registry_updates": [
            {
                "item_id": "ITEM_oath",
                "set": {"custodian": "CHAR_fizz"},
                "reason": "handoff",
            }
        ],
    }
    changed = _apply_durable_state_updates(
        book_root=book_root,
        patch=patch_newer,
        chapter=1,
        scene=5,
        phase="scene",
        state={"world": {"location": "inn"}},
        scene_card={"timeline_scope": "present", "ontological_scope": "real"},
    )
    assert changed is True

    patch_older = {
        "schema_version": "1.0",
        "item_registry_updates": [
            {
                "item_id": "ITEM_oath",
                "set": {"custodian": "CHAR_artie"},
                "reason": "older scene replay",
            }
        ],
    }

    with pytest.raises(ValueError, match="Chronology conflict"):
        _apply_durable_state_updates(
            book_root=book_root,
            patch=patch_older,
            chapter=1,
            scene=3,
            phase="scene",
            state={"world": {"location": "inn"}},
            scene_card={"timeline_scope": "present", "ontological_scope": "real"},
        )

def test_apply_plot_device_intangible_update_allowed_in_flashback_with_reason_category(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    save_plot_devices(
        book_root,
        {
            "schema_version": "1.0",
            "devices": [
                {
                    "device_id": "DEV_secret",
                    "name": "Hidden Covenant",
                    "custody_scope": "knowledge",
                    "custody_ref": "CHAR_fizz",
                    "activation_state": "dormant",
                    "linked_threads": ["THREAD_secret"],
                    "constraints": [],
                    "last_seen": {"chapter": 1, "scene": 1, "location": ""},
                }
            ],
        },
    )

    patch = {
        "schema_version": "1.0",
        "plot_device_updates": [
            {
                "device_id": "DEV_secret",
                "set": {
                    "custody_scope": "knowledge",
                    "custody_ref": "CHAR_artie",
                    "activation_state": "revealed",
                },
                "reason": "Artie learns the covenant through recovered memory.",
                "reason_category": "knowledge_reveal",
            }
        ],
    }

    changed = _apply_durable_state_updates(
        book_root=book_root,
        patch=patch,
        chapter=2,
        scene=1,
        phase="scene",
        state={"world": {"location": "LOC_memory"}},
        scene_card={"timeline_scope": "flashback", "ontological_scope": "non_real"},
    )

    assert changed is True


def test_apply_plot_device_intangible_update_requires_reason_category_in_flashback(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    save_plot_devices(
        book_root,
        {
            "schema_version": "1.0",
            "devices": [
                {
                    "device_id": "DEV_secret",
                    "name": "Hidden Covenant",
                    "custody_scope": "knowledge",
                    "custody_ref": "CHAR_fizz",
                    "activation_state": "dormant",
                    "linked_threads": ["THREAD_secret"],
                    "constraints": [],
                    "last_seen": {"chapter": 1, "scene": 1, "location": ""},
                }
            ],
        },
    )

    patch = {
        "schema_version": "1.0",
        "plot_device_updates": [
            {
                "device_id": "DEV_secret",
                "set": {
                    "custody_scope": "knowledge",
                    "custody_ref": "CHAR_artie",
                    "activation_state": "revealed",
                },
                "reason": "Artie learns the covenant through recovered memory.",
            }
        ],
    }

    with pytest.raises(ValueError, match="must include an allowed reason_category"):
        _apply_durable_state_updates(
            book_root=book_root,
            patch=patch,
            chapter=2,
            scene=1,
            phase="scene",
            state={"world": {"location": "LOC_memory"}},
            scene_card={"timeline_scope": "flashback", "ontological_scope": "non_real"},
        )

def test_linked_item_device_drift_detected_after_scene_mutation(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    save_item_registry(
        book_root,
        {
            "schema_version": "1.0",
            "items": [
                {
                    "item_id": "ITEM_shard",
                    "name": "Star Shard",
                    "type": "artifact",
                    "owner_scope": "character",
                    "custodian": "CHAR_artie",
                    "linked_threads": ["THREAD_starfall"],
                    "state_tags": ["carried"],
                    "linked_device_id": "DEV_shard_core",
                    "last_seen": {"chapter": 1, "scene": 1, "location": "crater"},
                }
            ],
        },
    )
    save_plot_devices(
        book_root,
        {
            "schema_version": "1.0",
            "devices": [
                {
                    "device_id": "DEV_shard_core",
                    "name": "Shard Core",
                    "custody_scope": "character",
                    "custody_ref": "CHAR_artie",
                    "activation_state": "active",
                    "linked_threads": ["THREAD_starfall"],
                    "constraints": [],
                    "linked_item_id": "ITEM_shard",
                    "last_seen": {"chapter": 1, "scene": 1, "location": "crater"},
                }
            ],
        },
    )

    patch = {
        "schema_version": "1.0",
        "item_registry_updates": [
            {
                "item_id": "ITEM_shard",
                "set": {"state_tags": ["destroyed"]},
                "reason": "Shard is shattered by overload.",
            }
        ],
    }

    changed = _apply_durable_state_updates(
        book_root=book_root,
        patch=patch,
        chapter=1,
        scene=2,
        phase="scene",
        state={"world": {"location": "crater"}},
        scene_card={"timeline_scope": "present", "ontological_scope": "real"},
    )
    assert changed is True

    durable = _durable_state_context(book_root, None, None)
    issues = _linked_durable_consistency_issues(durable)

    assert any(issue.get("code") == "durable_link_state_conflict" for issue in issues)

