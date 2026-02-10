
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import re

from bookforge.characters import ensure_character_index, resolve_character_state_path, create_character_state_path
from bookforge.memory.durable_state import (
    ensure_durable_state_files,
    load_durable_commits,
    load_item_registry,
    load_plot_devices,
    save_durable_commits,
    save_item_registry,
    save_plot_devices,
    snapshot_item_registry,
    snapshot_plot_devices,
)
from bookforge.pipeline.state_apply import _apply_bag_updates, _now_iso


DURABLE_COMMIT_HASH_CAP = 2000
PHYSICAL_ITEM_MUTATION_KEYS = {
    "custodian",
    "container_ref",
    "carrier_ref",
    "location_ref",
    "owner_scope",
}
PHYSICAL_DEVICE_MUTATION_KEYS = {
    "custody_scope",
    "custody_ref",
    "container_ref",
    "carrier_ref",
    "location_ref",
}
ALLOWED_NON_PRESENT_REASON_CATEGORIES = {
    "knowledge_reveal",
    "timeline_override",
    "linkage_metadata_update",
}
INTANGIBLE_CUSTODY_SCOPES = {"knowledge", "thread", "faction", "global", "rule", "memory"}



def _scene_cast_ids(scene_card: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(scene_card, dict):
        return []
    values = scene_card.get("cast_present_ids")
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _is_tombstoned(entry: Dict[str, Any]) -> bool:
    tags = entry.get("state_tags")
    if not isinstance(tags, list):
        return False
    lowered = {str(tag).strip().lower() for tag in tags if str(tag).strip()}
    return bool(lowered.intersection({"destroyed", "consumed", "lost", "retired"}))


def _derive_item_scene_flags(entry: Dict[str, Any], world_location: str, cast_ids: List[str]) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {
            "derived_scene_accessible": False,
            "derived_visible": False,
            "derived_access_reason": "invalid_entry",
        }

    custodian = str(entry.get("custodian") or "").strip()
    carrier_ref = str(entry.get("carrier_ref") or "").strip()
    location_ref = str(entry.get("location_ref") or "").strip()
    container_ref = str(entry.get("container_ref") or "").strip()
    status = str(entry.get("status") or "").strip().lower()

    tombstoned = _is_tombstoned(entry)
    custodian_is_cast = custodian in cast_ids if custodian else False
    carrier_is_cast = carrier_ref in cast_ids if carrier_ref else False
    same_location = not location_ref or (world_location and location_ref == world_location)

    accessible = False
    reason = "not_accessible"
    if tombstoned:
        reason = "tombstoned"
    elif custodian_is_cast and same_location:
        accessible = True
        reason = "custodian_in_cast"
    elif carrier_is_cast and same_location:
        accessible = True
        reason = "carrier_in_cast"
    elif world_location and location_ref and location_ref == world_location and not carrier_ref:
        accessible = True
        reason = "location_match"

    carried_statuses = {"carried", "equipped", "held", "in_hand", "active", "worn"}
    non_visible_statuses = {"stowed", "cached", "stored", "packed"}
    in_hand_container = container_ref in {"hand_right", "hand_left"}

    visible = False
    if accessible:
        if status in non_visible_statuses:
            visible = False
        elif status in carried_statuses or in_hand_container:
            visible = True
        elif custodian_is_cast and not container_ref:
            visible = True

    return {
        "derived_scene_accessible": bool(accessible),
        "derived_visible": bool(visible),
        "derived_access_reason": reason,
    }


def _derive_plot_device_scene_flags(entry: Dict[str, Any], world_location: str, cast_ids: List[str]) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {
            "derived_scene_accessible": False,
            "derived_access_reason": "invalid_entry",
        }

    custody_scope = str(entry.get("custody_scope") or "").strip().lower()
    custody_ref = str(entry.get("custody_ref") or "").strip()

    if custody_scope in {"knowledge", "thread", "faction", "global"}:
        return {
            "derived_scene_accessible": True,
            "derived_access_reason": "intangible_scope",
        }

    if custody_scope in {"character", "person", "party"} and custody_ref in cast_ids:
        return {
            "derived_scene_accessible": True,
            "derived_access_reason": "custody_ref_in_cast",
        }

    if custody_scope in {"location", "world", "region"} and world_location and custody_ref == world_location:
        return {
            "derived_scene_accessible": True,
            "derived_access_reason": "custody_ref_location_match",
        }

    return {
        "derived_scene_accessible": False,
        "derived_access_reason": "not_accessible",
    }


def _durable_state_context(
    book_root: Path,
    state: Optional[Dict[str, Any]] = None,
    scene_card: Optional[Dict[str, Any]] = None,
    expanded_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    ensure_durable_state_files(book_root)
    item_registry = load_item_registry(book_root)
    plot_devices = load_plot_devices(book_root)

    if isinstance(state, dict):
        world = state.get("world") if isinstance(state.get("world"), dict) else {}
        world_location = str(world.get("location") or "").strip()
    else:
        world_location = ""
    cast_ids = _scene_cast_ids(scene_card)
    thread_ids = set()
    if isinstance(scene_card, dict):
        raw_threads = scene_card.get("thread_ids")
        if isinstance(raw_threads, list):
            thread_ids = {str(value).strip() for value in raw_threads if str(value).strip()}

    requested_ids: set[str] = set()
    if isinstance(scene_card, dict):
        for key in (
            "required_in_custody",
            "required_scene_accessible",
            "required_visible_on_page",
            "forbidden_visible",
            "device_presence",
        ):
            raw = scene_card.get(key)
            if isinstance(raw, list):
                for value in raw:
                    token = str(value).strip()
                    if token:
                        requested_ids.add(token)
    if isinstance(expanded_ids, list):
        for value in expanded_ids:
            token = str(value).strip()
            if token:
                requested_ids.add(token)

    item_entries_all: List[Dict[str, Any]] = []
    for raw_entry in item_registry.get("items", []) if isinstance(item_registry.get("items"), list) else []:
        if not isinstance(raw_entry, dict):
            continue
        entry = dict(raw_entry)
        entry.update(_derive_item_scene_flags(entry, world_location, cast_ids))
        item_entries_all.append(entry)

    device_entries_all: List[Dict[str, Any]] = []
    for raw_entry in plot_devices.get("devices", []) if isinstance(plot_devices.get("devices"), list) else []:
        if not isinstance(raw_entry, dict):
            continue
        entry = dict(raw_entry)
        entry.update(_derive_plot_device_scene_flags(entry, world_location, cast_ids))
        device_entries_all.append(entry)

    # If no scene scope exists, expose full canonical datasets.
    if not isinstance(scene_card, dict) and not requested_ids:
        item_registry_view = dict(item_registry)
        item_registry_view["items"] = item_entries_all
        plot_devices_view = dict(plot_devices)
        plot_devices_view["devices"] = device_entries_all
        return {
            "item_registry": item_registry_view,
            "plot_devices": plot_devices_view,
        }

    item_map = {
        str(entry.get("item_id") or "").strip(): entry
        for entry in item_entries_all
        if str(entry.get("item_id") or "").strip()
    }
    device_map = {
        str(entry.get("device_id") or "").strip(): entry
        for entry in device_entries_all
        if str(entry.get("device_id") or "").strip()
    }

    selected_item_ids: set[str] = set()
    selected_device_ids: set[str] = set()

    for item_id, entry in item_map.items():
        linked_threads = entry.get("linked_threads") if isinstance(entry.get("linked_threads"), list) else []
        linked_threads_set = {str(value).strip() for value in linked_threads if str(value).strip()}
        custodian = str(entry.get("custodian") or "").strip()
        carrier_ref = str(entry.get("carrier_ref") or "").strip()
        location_ref = str(entry.get("location_ref") or "").strip()

        include = False
        include = include or item_id in requested_ids
        include = include or bool(linked_threads_set.intersection(thread_ids))
        include = include or bool(entry.get("derived_scene_accessible"))
        include = include or bool(entry.get("derived_visible"))
        include = include or (custodian in cast_ids if custodian else False)
        include = include or (carrier_ref in cast_ids if carrier_ref else False)
        include = include or (bool(world_location) and bool(location_ref) and location_ref == world_location)
        linked_device_id = str(entry.get("linked_device_id") or "").strip()
        include = include or (linked_device_id in requested_ids if linked_device_id else False)
        if include:
            selected_item_ids.add(item_id)

    for device_id, entry in device_map.items():
        linked_threads = entry.get("linked_threads") if isinstance(entry.get("linked_threads"), list) else []
        linked_threads_set = {str(value).strip() for value in linked_threads if str(value).strip()}
        custody_ref = str(entry.get("custody_ref") or "").strip()
        linked_item_id = str(entry.get("linked_item_id") or "").strip()

        include = False
        include = include or device_id in requested_ids
        include = include or bool(linked_threads_set.intersection(thread_ids))
        include = include or bool(entry.get("derived_scene_accessible"))
        include = include or (custody_ref in cast_ids if custody_ref else False)
        include = include or (linked_item_id in requested_ids if linked_item_id else False)
        if include:
            selected_device_ids.add(device_id)

    # Close linked pairs so canonical counterparts are available in a single slice.
    changed = True
    while changed:
        changed = False
        for item_id in list(selected_item_ids):
            entry = item_map.get(item_id)
            if not isinstance(entry, dict):
                continue
            linked_device_id = str(entry.get("linked_device_id") or "").strip()
            if linked_device_id and linked_device_id in device_map and linked_device_id not in selected_device_ids:
                selected_device_ids.add(linked_device_id)
                changed = True
        for device_id in list(selected_device_ids):
            entry = device_map.get(device_id)
            if not isinstance(entry, dict):
                continue
            linked_item_id = str(entry.get("linked_item_id") or "").strip()
            if linked_item_id and linked_item_id in item_map and linked_item_id not in selected_item_ids:
                selected_item_ids.add(linked_item_id)
                changed = True

    item_entries = [item_map[item_id] for item_id in sorted(selected_item_ids) if item_id in item_map]
    device_entries = [device_map[device_id] for device_id in sorted(selected_device_ids) if device_id in device_map]

    item_registry_view = dict(item_registry)
    item_registry_view["items"] = item_entries

    plot_devices_view = dict(plot_devices)
    plot_devices_view["devices"] = device_entries

    return {
        "item_registry": item_registry_view,
        "plot_devices": plot_devices_view,
    }


def _durable_mutation_payload(patch: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for key in (
        "inventory_alignment_updates",
        "item_registry_updates",
        "plot_device_updates",
        "transfer_updates",
    ):
        value = patch.get(key)
        if isinstance(value, list) and value:
            payload[key] = value
    return payload


def _scene_scopes(scene_card: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    if not isinstance(scene_card, dict):
        return "present", "real"
    timeline_scope = str(scene_card.get("timeline_scope") or "present").strip().lower() or "present"
    ontological_scope = str(scene_card.get("ontological_scope") or "real").strip().lower() or "real"
    return timeline_scope, ontological_scope


def _scope_override_enabled(update: Dict[str, Any]) -> bool:
    if not isinstance(update, dict):
        return False
    for key in ("timeline_override", "scope_override", "allow_scope_override", "allow_non_present_mutation"):
        value = update.get(key)
        if isinstance(value, bool) and value:
            return True
        if isinstance(value, str) and value.strip().lower() in {"1", "true", "yes", "on"}:
            return True
    return False


def _reason_category(update: Dict[str, Any]) -> str:
    return str(update.get("reason_category") or "").strip().lower()


def _block_touches_physical_keys(update: Dict[str, Any], keys: set[str]) -> bool:
    if not isinstance(update, dict):
        return False
    for block_name in ("set", "delta"):
        block = update.get(block_name)
        if not isinstance(block, dict):
            continue
        if any(key in block for key in keys):
            return True
    remove_block = update.get("remove")
    if isinstance(remove_block, list) and any(str(key) in keys for key in remove_block):
        return True
    return False


def _plot_device_update_is_intangible(update: Dict[str, Any]) -> bool:
    if not isinstance(update, dict):
        return False
    set_block = update.get("set") if isinstance(update.get("set"), dict) else {}
    delta_block = update.get("delta") if isinstance(update.get("delta"), dict) else {}

    # Explicit intangible scope marks custody updates as non-physical semantic transitions.
    scope = str(set_block.get("custody_scope") or "").strip().lower()
    if scope not in INTANGIBLE_CUSTODY_SCOPES:
        return False

    # Any explicit location/container/carrier mutation is still physical.
    for key in ("container_ref", "carrier_ref", "location_ref"):
        if key in set_block or key in delta_block:
            return False

    return True


def _enforce_scope_policy(scene_card: Optional[Dict[str, Any]], mutations: Dict[str, Any]) -> None:
    timeline_scope, ontological_scope = _scene_scopes(scene_card)
    present_real = timeline_scope == "present" and ontological_scope == "real"
    if present_real:
        return

    for transfer in mutations.get("transfer_updates", []):
        if not isinstance(transfer, dict):
            continue
        if _scope_override_enabled(transfer):
            continue
        raise ValueError(
            "Scope policy violation: transfer_updates require timeline_scope=present and "
            "ontological_scope=real unless explicit scope override is set."
        )

    for update in mutations.get("inventory_alignment_updates", []):
        if not isinstance(update, dict):
            continue
        if _scope_override_enabled(update):
            continue
        raise ValueError(
            "Scope policy violation: inventory_alignment_updates require timeline_scope=present and "
            "ontological_scope=real unless explicit scope override is set."
        )

    for update in mutations.get("item_registry_updates", []):
        if not isinstance(update, dict):
            continue
        physical_change = _block_touches_physical_keys(update, PHYSICAL_ITEM_MUTATION_KEYS)
        if not physical_change:
            continue
        if _scope_override_enabled(update):
            continue
        raise ValueError(
            "Scope policy violation: physical item_registry_updates require timeline_scope=present and "
            "ontological_scope=real unless explicit scope override is set."
        )

    for update in mutations.get("plot_device_updates", []):
        if not isinstance(update, dict):
            continue
        physical_change = _block_touches_physical_keys(update, PHYSICAL_DEVICE_MUTATION_KEYS)
        if physical_change and _plot_device_update_is_intangible(update):
            physical_change = False

        if physical_change and not _scope_override_enabled(update):
            raise ValueError(
                "Scope policy violation: physical plot_device_updates require timeline_scope=present and "
                "ontological_scope=real unless explicit scope override is set."
            )

        if not physical_change:
            category = _reason_category(update)
            if not category:
                raise ValueError(
                    "Scope policy violation: non-physical plot_device_updates in non-present/non-real scope "
                    "must include an allowed reason_category."
                )
            if category not in ALLOWED_NON_PRESENT_REASON_CATEGORIES:
                raise ValueError(
                    "Scope policy violation: non-physical plot_device_updates in non-present/non-real scope "
                    "must use an allowed reason_category."
                )


def _durable_mutation_hash(patch: Dict[str, Any], chapter: int, scene: int, phase: str) -> str:
    payload = {
        "chapter": int(chapter),
        "scene": int(scene),
        "phase": str(phase).strip().lower(),
        "mutations": _durable_mutation_payload(patch),
    }
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()


def _entry_contains_expected_before(entry: Dict[str, Any], expected_before: Dict[str, Any]) -> bool:
    if not isinstance(entry, dict) or not isinstance(expected_before, dict):
        return False

    def _contains(actual: Any, expected: Any) -> bool:
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return False
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not _contains(actual.get(key), value):
                    return False
            return True
        if isinstance(expected, list):
            if not isinstance(actual, list):
                return False
            for index, value in enumerate(expected):
                if index >= len(actual):
                    return False
                if not _contains(actual[index], value):
                    return False
            return True
        return actual == expected

    return _contains(entry, expected_before)


def _find_entry_index(entries: List[Dict[str, Any]], id_key: str, id_value: str) -> int:
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        if str(entry.get(id_key) or "").strip() == id_value:
            return idx
    return -1


def _normalize_last_seen(chapter: int, scene: int, location: str) -> Dict[str, Any]:
    return {
        "chapter": int(chapter),
        "scene": int(scene),
        "location": str(location).strip(),
    }


def _normalize_custodian_from_endpoint(endpoint: Dict[str, Any]) -> Any:
    if not isinstance(endpoint, dict):
        return None
    if endpoint.get("custodian") is not None:
        return endpoint.get("custodian")
    for key in ("character_id", "location_ref", "carrier_ref", "container_ref"):
        value = endpoint.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _extract_character_id_from_endpoint(endpoint: Dict[str, Any]) -> Optional[str]:
    if not isinstance(endpoint, dict):
        return None
    value = endpoint.get("character_id")
    text = str(value or "").strip()
    return text or None


def _load_character_state_for_mutation(
    book_root: Path,
    cache: Dict[str, Tuple[Path, Dict[str, Any]]],
    character_id: str,
) -> Tuple[Path, Dict[str, Any]]:
    cached = cache.get(character_id)
    if cached is not None:
        return cached

    state_path = resolve_character_state_path(book_root, character_id)
    if state_path is None:
        state_path = create_character_state_path(book_root, character_id)

    state: Dict[str, Any] = {
        "schema_version": "1.0",
        "character_id": character_id,
        "inventory": [],
        "containers": [],
        "invariants": [],
        "history": [],
    }
    if state_path.exists():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state.update(loaded)
        except json.JSONDecodeError:
            pass

    cache[character_id] = (state_path, state)
    return state_path, state


def _inventory_entry_matches(entry: Dict[str, Any], item_id: str, item_name: str) -> bool:
    if not isinstance(entry, dict):
        return False
    entry_item_id = str(entry.get("item_id") or "").strip()
    if entry_item_id and item_id and entry_item_id == item_id:
        return True
    if item_name:
        entry_name = str(entry.get("item") or entry.get("item_name") or "").strip().lower()
        if entry_name and entry_name == item_name.strip().lower():
            return True
    return False


def _remove_inventory_item(state: Dict[str, Any], item_id: str, item_name: str) -> None:
    inventory = state.get("inventory")
    if not isinstance(inventory, list):
        inventory = []
    inventory = [
        entry for entry in inventory
        if not _inventory_entry_matches(entry, item_id, item_name)
    ]
    state["inventory"] = inventory


def _upsert_inventory_item(
    state: Dict[str, Any],
    item_id: str,
    item_name: str,
    container: Optional[str],
    status: Optional[str],
    quantity: Optional[Any] = None,
) -> None:
    inventory = state.get("inventory")
    if not isinstance(inventory, list):
        inventory = []

    idx = -1
    for i, entry in enumerate(inventory):
        if _inventory_entry_matches(entry, item_id, item_name):
            idx = i
            break

    resolved_container = str(container or "").strip()
    resolved_status = str(status or "").strip() or "carried"

    if idx >= 0:
        entry = inventory[idx]
        if not isinstance(entry, dict):
            entry = {}
        if item_id:
            entry["item_id"] = item_id
        if item_name:
            entry["item"] = item_name
            entry["item_name"] = item_name
        if resolved_container:
            entry["container"] = resolved_container
        entry["status"] = resolved_status
        if quantity is not None:
            entry["quantity"] = quantity
        inventory[idx] = entry
    else:
        entry: Dict[str, Any] = {
            "status": resolved_status,
        }
        if item_id:
            entry["item_id"] = item_id
        if item_name:
            entry["item"] = item_name
            entry["item_name"] = item_name
        if resolved_container:
            entry["container"] = resolved_container
        if quantity is not None:
            entry["quantity"] = quantity
        inventory.append(entry)

    state["inventory"] = inventory


def _apply_registry_update_block(
    entries: List[Dict[str, Any]],
    id_key: str,
    update: Dict[str, Any],
    chapter: int,
    scene: int,
    location: str,
    tombstone_tag: str,
) -> None:
    entry_id = str(update.get(id_key) or "").strip()
    if not entry_id:
        raise ValueError(f"{id_key} is required for durable registry update.")

    index = _find_entry_index(entries, id_key, entry_id)
    current: Dict[str, Any]
    if index >= 0:
        current = dict(entries[index])
    else:
        current = {id_key: entry_id}

    expected_before = update.get("expected_before")
    if isinstance(expected_before, dict) and not _entry_contains_expected_before(current, expected_before):
        raise ValueError(f"Durable precondition mismatch for {id_key}={entry_id}.")

    _apply_bag_updates(current, update)

    remove_block = update.get("remove")
    if isinstance(remove_block, list) and not update.get("set") and not update.get("delta"):
        tags = current.get("state_tags")
        if not isinstance(tags, list):
            tags = []
        if tombstone_tag not in tags:
            tags.append(tombstone_tag)
        current["state_tags"] = tags

    current["last_seen"] = _normalize_last_seen(chapter, scene, location)

    if index >= 0:
        entries[index] = current
    else:
        entries.append(current)


def _apply_transfer_update(
    book_root: Path,
    transfer: Dict[str, Any],
    item_entries: List[Dict[str, Any]],
    character_cache: Dict[str, Tuple[Path, Dict[str, Any]]],
    chapter: int,
    scene: int,
    location: str,
) -> None:
    item_id = str(transfer.get("item_id") or "").strip()
    if not item_id:
        raise ValueError("transfer_updates requires item_id.")

    item_index = _find_entry_index(item_entries, "item_id", item_id)
    if item_index < 0:
        raise ValueError(f"transfer_updates references unknown item_id '{item_id}'.")

    item_entry = dict(item_entries[item_index])

    expected_before = transfer.get("expected_before")
    if isinstance(expected_before, dict) and not _entry_contains_expected_before(item_entry, expected_before):
        raise ValueError(f"Durable precondition mismatch for transfer item_id={item_id}.")

    from_endpoint = transfer.get("from") if isinstance(transfer.get("from"), dict) else {}
    to_endpoint = transfer.get("to") if isinstance(transfer.get("to"), dict) else {}
    transfer_chain = transfer.get("transfer_chain")
    if isinstance(transfer_chain, list) and transfer_chain:
        first = transfer_chain[0]
        if not from_endpoint and isinstance(first, dict):
            from_endpoint = first
        last = transfer_chain[-1]
        if isinstance(last, dict):
            to_endpoint = last

    item_name = str(item_entry.get("display_name") or item_entry.get("name") or item_entry.get("item_name") or item_entry.get("item") or item_id)

    source_char_id = _extract_character_id_from_endpoint(from_endpoint)
    if source_char_id:
        _, source_state = _load_character_state_for_mutation(book_root, character_cache, source_char_id)
        _remove_inventory_item(source_state, item_id, item_name)

    target_char_id = _extract_character_id_from_endpoint(to_endpoint)
    if target_char_id:
        _, target_state = _load_character_state_for_mutation(book_root, character_cache, target_char_id)
        _upsert_inventory_item(
            target_state,
            item_id,
            item_name,
            container=str(to_endpoint.get("container") or to_endpoint.get("container_ref") or "").strip() or None,
            status=str(to_endpoint.get("status") or "").strip() or None,
            quantity=to_endpoint.get("quantity"),
        )

    custodian = _normalize_custodian_from_endpoint(to_endpoint)
    if custodian is not None:
        item_entry["custodian"] = custodian

    for key in ("container_ref", "carrier_ref", "location_ref", "owner_scope"):
        if key in to_endpoint and to_endpoint.get(key) is not None:
            item_entry[key] = to_endpoint.get(key)

    if "state_tags" in to_endpoint and isinstance(to_endpoint.get("state_tags"), list):
        item_entry["state_tags"] = to_endpoint.get("state_tags")
    if isinstance(transfer_chain, list) and transfer_chain:
        item_entry["last_transfer_chain"] = transfer_chain

    item_entry["last_seen"] = _normalize_last_seen(chapter, scene, location)
    item_entries[item_index] = item_entry


def _apply_inventory_alignment_updates(
    book_root: Path,
    updates: List[Dict[str, Any]],
    character_cache: Dict[str, Tuple[Path, Dict[str, Any]]],
    chapter: int,
    scene: int,
) -> None:
    for update in updates:
        if not isinstance(update, dict):
            continue
        char_id = str(update.get("character_id") or "").strip()
        if not char_id:
            continue
        _, state = _load_character_state_for_mutation(book_root, character_cache, char_id)

        set_block = update.get("set") if isinstance(update.get("set"), dict) else {}
        if isinstance(update.get("inventory"), list) and "inventory" not in set_block:
            set_block = dict(set_block)
            set_block["inventory"] = update.get("inventory")
        if isinstance(update.get("containers"), list) and "containers" not in set_block:
            set_block = dict(set_block)
            set_block["containers"] = update.get("containers")

        for key in ("inventory", "containers", "inventory_instances", "inventory_posture"):
            if key in set_block:
                state[key] = set_block.get(key)

        history = state.get("history") if isinstance(state.get("history"), list) else []
        note = str(update.get("reason") or "").strip()
        entry: Dict[str, Any] = {
            "chapter": chapter,
            "scene": scene,
            "changes": ["inventory_alignment_updated"],
        }
        if note:
            entry["notes"] = note
        history.append(entry)
        state["history"] = history
        state["last_touched"] = {"chapter": chapter, "scene": scene}
        state["updated_at"] = _now_iso()


def _persist_character_mutation_cache(character_cache: Dict[str, Tuple[Path, Dict[str, Any]]]) -> None:
    for state_path, state in character_cache.values():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")


def _apply_durable_state_updates(
    book_root: Path,
    patch: Dict[str, Any],
    chapter: int,
    scene: int,
    phase: str,
    state: Optional[Dict[str, Any]] = None,
    scene_card: Optional[Dict[str, Any]] = None,
) -> bool:
    mutations = _durable_mutation_payload(patch)
    if not mutations:
        return False

    ensure_durable_state_files(book_root)
    commit_data = load_durable_commits(book_root)
    applied_hashes = commit_data.get("applied_hashes") if isinstance(commit_data.get("applied_hashes"), list) else []

    latest_scene_raw = commit_data.get("latest_scene") if isinstance(commit_data.get("latest_scene"), dict) else {}
    latest_chapter = max(0, int(latest_scene_raw.get("chapter") or 0))
    latest_scene = max(0, int(latest_scene_raw.get("scene") or 0))
    if chapter < latest_chapter or (chapter == latest_chapter and scene < latest_scene):
        raise ValueError(
            f"Chronology conflict: durable state already committed through ch{latest_chapter:03d} "
            f"sc{latest_scene:03d}; cannot apply older scene ch{chapter:03d} sc{scene:03d}."
        )

    mutation_hash = _durable_mutation_hash(patch, chapter, scene, phase)
    if mutation_hash in applied_hashes:
        return False

    _enforce_scope_policy(scene_card, mutations)

    item_registry = load_item_registry(book_root)
    plot_devices = load_plot_devices(book_root)
    item_entries = list(item_registry.get("items", [])) if isinstance(item_registry.get("items", []), list) else []
    device_entries = list(plot_devices.get("devices", [])) if isinstance(plot_devices.get("devices", []), list) else []

    snapshot_item_registry(book_root, chapter, scene)
    snapshot_plot_devices(book_root, chapter, scene)

    world = state.get("world", {}) if isinstance(state, dict) and isinstance(state.get("world"), dict) else {}
    location = str(world.get("location") or "").strip()

    character_cache: Dict[str, Tuple[Path, Dict[str, Any]]] = {}

    for update in mutations.get("item_registry_updates", []):
        if not isinstance(update, dict):
            continue
        _apply_registry_update_block(
            item_entries,
            "item_id",
            update,
            chapter,
            scene,
            location,
            tombstone_tag="retired",
        )

    for update in mutations.get("plot_device_updates", []):
        if not isinstance(update, dict):
            continue
        _apply_registry_update_block(
            device_entries,
            "device_id",
            update,
            chapter,
            scene,
            location,
            tombstone_tag="retired",
        )

    for transfer in mutations.get("transfer_updates", []):
        if not isinstance(transfer, dict):
            continue
        _apply_transfer_update(
            book_root,
            transfer,
            item_entries,
            character_cache,
            chapter,
            scene,
            location,
        )

    alignment_updates = [
        update for update in mutations.get("inventory_alignment_updates", [])
        if isinstance(update, dict)
    ]
    if alignment_updates:
        _apply_inventory_alignment_updates(
            book_root,
            alignment_updates,
            character_cache,
            chapter,
            scene,
        )

    item_registry["items"] = item_entries
    plot_devices["devices"] = device_entries
    save_item_registry(book_root, item_registry)
    save_plot_devices(book_root, plot_devices)
    _persist_character_mutation_cache(character_cache)

    applied_hashes.append(mutation_hash)
    if len(applied_hashes) > DURABLE_COMMIT_HASH_CAP:
        applied_hashes = applied_hashes[-DURABLE_COMMIT_HASH_CAP:]
    commit_data["applied_hashes"] = applied_hashes
    commit_data["latest_scene"] = {"chapter": chapter, "scene": scene}
    save_durable_commits(book_root, commit_data)
    return True

