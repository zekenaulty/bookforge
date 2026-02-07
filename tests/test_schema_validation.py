import pytest

from bookforge.util.schema import SchemaValidationError, validate_json


def test_book_schema_valid():
    data = {
        "schema_version": "1.0",
        "book_id": "test-book",
        "title": "Test",
        "genre": ["fantasy"],
        "targets": {},
        "voice": {},
        "invariants": [],
        "author_ref": "eldrik-vale/v1",
    }
    validate_json(data, "book")


def test_book_schema_missing_required():
    data = {
        "schema_version": "1.0",
        "title": "Test",
        "genre": ["fantasy"],
        "targets": {},
        "voice": {},
        "invariants": [],
        "author_ref": "eldrik-vale/v1",
    }
    with pytest.raises(SchemaValidationError):
        validate_json(data, "book")


def test_item_registry_schema_valid() -> None:
    data = {
        "schema_version": "1.0",
        "items": [
            {
                "item_id": "ITEM_demo_sword",
                "name": "Demo Sword",
                "type": "weapon",
                "owner_scope": "character",
                "custodian": "CHAR_demo",
                "linked_threads": ["THREAD_demo"],
                "state_tags": ["carried"],
                "last_seen": {"chapter": 1, "scene": 1, "location": "test_loc"},
            }
        ],
    }
    validate_json(data, "item_registry")


def test_plot_devices_schema_valid() -> None:
    data = {
        "schema_version": "1.0",
        "devices": [
            {
                "device_id": "DEVICE_secret",
                "name": "The Secret",
                "custody_scope": "knowledge",
                "custody_ref": "CHAR_demo",
                "activation_state": "active",
                "linked_threads": ["THREAD_demo"],
                "constraints": ["must_not_leak"],
                "last_seen": {"chapter": 1, "scene": 1, "location": "test_loc"},
            }
        ],
    }
    validate_json(data, "plot_devices")