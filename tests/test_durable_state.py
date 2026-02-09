from pathlib import Path
import json

from bookforge.memory.durable_state import (
    durable_commits_path,
    ensure_durable_state_files,
    item_registry_path,
    items_index_path,
    load_durable_commits,
    load_item_registry,
    load_plot_devices,
    plot_devices_index_path,
    plot_devices_path,
    save_item_registry,
    save_plot_devices,
    snapshot_item_registry,
    snapshot_plot_devices,
)


def _book_root(tmp_path: Path) -> Path:
    root = tmp_path / "books" / "demo_book"
    (root / "draft" / "context").mkdir(parents=True, exist_ok=True)
    return root


def test_ensure_durable_state_files_creates_defaults(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    ensure_durable_state_files(book_root)

    item_path = item_registry_path(book_root)
    device_path = plot_devices_path(book_root)
    assert item_path.exists()
    assert device_path.exists()
    assert items_index_path(book_root).exists()
    assert plot_devices_index_path(book_root).exists()
    assert durable_commits_path(book_root).exists()

    item_data = json.loads(item_path.read_text(encoding="utf-8"))
    device_data = json.loads(device_path.read_text(encoding="utf-8"))
    assert item_data["items"] == []
    assert device_data["devices"] == []


def test_load_and_save_durable_state_roundtrip(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)
    ensure_durable_state_files(book_root)

    save_item_registry(
        book_root,
        {
            "schema_version": "1.0",
            "items": [
                {
                    "item_id": "ITEM_ring",
                    "name": "Ring",
                    "type": "artifact",
                    "owner_scope": "character",
                    "custodian": "CHAR_a",
                    "linked_threads": [],
                    "state_tags": ["carried"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "inn"},
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
                    "device_id": "DEVICE_oath",
                    "name": "Oath",
                    "custody_scope": "knowledge",
                    "custody_ref": "CHAR_a",
                    "activation_state": "active",
                    "linked_threads": ["THREAD_oath"],
                    "constraints": [],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "inn"},
                }
            ],
        },
    )

    item_data = load_item_registry(book_root)
    device_data = load_plot_devices(book_root)

    assert item_data["items"][0]["item_id"] == "ITEM_ring"
    assert device_data["devices"][0]["device_id"] == "DEVICE_oath"

    item_index = json.loads(items_index_path(book_root).read_text(encoding="utf-8"))
    device_index = json.loads(plot_devices_index_path(book_root).read_text(encoding="utf-8"))
    assert item_index["item_ids"] == ["ITEM_ring"]
    assert device_index["device_ids"] == ["DEVICE_oath"]


def test_load_durable_commits_normalizes_file(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)
    ensure_durable_state_files(book_root)

    commits = load_durable_commits(book_root)

    assert commits["schema_version"] == "1.0"
    assert commits["applied_hashes"] == []
    assert commits["latest_scene"] == {"chapter": 0, "scene": 0}


def test_durable_state_snapshots_created(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)
    ensure_durable_state_files(book_root)

    item_snapshot = snapshot_item_registry(book_root, chapter=1, scene=2)
    device_snapshot = snapshot_plot_devices(book_root, chapter=1, scene=2)

    assert item_snapshot.exists()
    assert device_snapshot.exists()
    assert "ch001_sc002_item_registry" in item_snapshot.name
    assert "ch001_sc002_plot_devices" in device_snapshot.name

def test_ensure_durable_state_files_backfills_item_registry_from_character_states(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)
    chars_dir = book_root / "draft" / "context" / "characters"
    chars_dir.mkdir(parents=True, exist_ok=True)
    state_path = chars_dir / "artie__abc12345.state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "character_id": "CHAR_artie",
                "inventory": [
                    {
                        "item": "Broken Tutorial Sword",
                        "container": "hand_right",
                        "status": "carried",
                    }
                ],
                "last_touched": {"chapter": 1, "scene": 1},
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    ensure_durable_state_files(book_root)
    registry = load_item_registry(book_root)

    assert len(registry.get("items", [])) == 1
    entry = registry["items"][0]
    assert entry["name"] == "Broken Tutorial Sword"
    assert entry["custodian"] == "CHAR_artie"
    assert entry["last_seen"]["chapter"] == 1
    assert entry["last_seen"]["scene"] == 1

    # Migration is deterministic and should not duplicate on subsequent ensures.
    ensure_durable_state_files(book_root)
    registry2 = load_item_registry(book_root)
    assert len(registry2.get("items", [])) == 1
    assert registry2["items"][0]["item_id"] == entry["item_id"]

def test_ensure_durable_state_files_backfills_plot_devices_from_thread_hints(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)

    # Seed thread hints in state and outline so migration has deterministic inputs.
    state_path = book_root / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "world": {"open_threads": ["THREAD_void_breach"], "recent_facts": []},
                "summary": {
                    "last_scene": [],
                    "chapter_so_far": [],
                    "story_so_far": [],
                    "key_facts_ring": ["Escalation on THREAD_void_breach"],
                    "must_stay_true": [],
                    "pending_story_rollups": [],
                },
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    outline_dir = book_root / "outline"
    outline_dir.mkdir(parents=True, exist_ok=True)
    (outline_dir / "outline.json").write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "threads": [
                    {"thread_id": "THREAD_void_breach", "label": "Void Breach"},
                    {"thread_id": "THREAD_oath_chain", "label": "Oath Chain"},
                ],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    ensure_durable_state_files(book_root)
    devices = load_plot_devices(book_root).get("devices", [])

    assert len(devices) == 2
    by_thread = {tuple(device.get("linked_threads", []))[0]: device for device in devices}
    assert "THREAD_void_breach" in by_thread
    assert "THREAD_oath_chain" in by_thread
    assert by_thread["THREAD_void_breach"]["custody_scope"] == "thread"
    assert by_thread["THREAD_void_breach"]["custody_ref"] == "THREAD_void_breach"

    # Migration is deterministic and should not duplicate on subsequent ensures.
    ensure_durable_state_files(book_root)
    devices2 = load_plot_devices(book_root).get("devices", [])
    assert len(devices2) == 2
    assert sorted([entry["device_id"] for entry in devices2]) == sorted([entry["device_id"] for entry in devices])



def test_item_registry_normalizes_display_name_from_id(tmp_path: Path) -> None:
    book_root = _book_root(tmp_path)
    ensure_durable_state_files(book_root)

    save_item_registry(
        book_root,
        {
            "schema_version": "1.0",
            "items": [
                {
                    "item_id": "ITEM_rusty_dagger_abcdef12",
                    "name": "ITEM_rusty_dagger_abcdef12",
                    "type": "weapon",
                    "owner_scope": "character",
                    "custodian": "CHAR_a",
                    "linked_threads": [],
                    "state_tags": ["carried"],
                    "last_seen": {"chapter": 1, "scene": 1, "location": "inn"},
                }
            ],
        },
    )

    item_data = load_item_registry(book_root)
    entry = item_data["items"][0]
    assert entry["name"] == "Rusty Dagger"
    assert entry["display_name"] == "Rusty Dagger"
