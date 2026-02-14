from __future__ import annotations

from typing import Any, Dict, List
import re


def _coerce_summary_update(patch: Dict[str, Any]) -> None:
    summary_update = patch.get("summary_update")
    if not isinstance(summary_update, dict):
        return

    def _ensure_list(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value is None:
            return []
        return [str(value).strip()]

    summary_update["last_scene"] = _ensure_list(summary_update.get("last_scene"))
    summary_update["key_events"] = _ensure_list(summary_update.get("key_events"))
    summary_update["must_stay_true"] = _ensure_list(summary_update.get("must_stay_true"))
    summary_update["chapter_so_far_add"] = _ensure_list(summary_update.get("chapter_so_far_add"))

    for key in ("key_facts_ring_add", "story_so_far_add"):
        value = summary_update.get(key)
        if value is None:
            continue
        summary_update[key] = _ensure_list(value)


def _coerce_character_updates(patch: Dict[str, Any]) -> None:
    updates = patch.get("character_updates")
    if not isinstance(updates, list):
        return

    alignment_updates = patch.get("inventory_alignment_updates")
    alignment_map: Dict[str, Dict[str, Dict[str, Any]]] = {}
    if isinstance(alignment_updates, list):
        for entry in alignment_updates:
            if not isinstance(entry, dict):
                continue
            character_id = str(entry.get("character_id") or "").strip()
            if not character_id:
                continue
            inventory = entry.get("inventory")
            if not isinstance(inventory, list):
                continue
            for item in inventory:
                if not isinstance(item, dict):
                    continue
                item_id = item.get("item") or item.get("item_id")
                item_id = str(item_id).strip()
                if not item_id:
                    continue
                alignment_map.setdefault(character_id, {})[item_id] = {
                    "container": item.get("container"),
                    "status": item.get("status"),
                }

    def _ensure_list(value: Any) -> List[Any]:
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return [value]

    def _container_map(containers: Any) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        if not isinstance(containers, list):
            return mapping
        for container in containers:
            if not isinstance(container, dict):
                continue
            name = str(container.get("container") or "").strip()
            contents = container.get("contents")
            if not name or not isinstance(contents, list):
                continue
            for item_id in contents:
                item_key = str(item_id).strip()
                if item_key and item_key not in mapping:
                    mapping[item_key] = name
        return mapping

    for update in updates:
        if not isinstance(update, dict):
            continue
        update["persona_updates"] = _ensure_list(update.get("persona_updates"))
        update["invariants_add"] = _ensure_list(update.get("invariants_add"))

        character_id = str(update.get("character_id") or "").strip()
        alignment_for_char = alignment_map.get(character_id, {})
        container_map = _container_map(update.get("containers"))

        inventory = update.get("inventory")
        if isinstance(inventory, list):
            normalized_inventory = []
            for item in inventory:
                if isinstance(item, dict):
                    if "item" not in item and "item_id" in item:
                        item["item"] = item.get("item_id")
                    item_id = str(item.get("item") or "").strip()
                    if item_id:
                        alignment_info = alignment_for_char.get(item_id)
                        if alignment_info:
                            if not item.get("container") and alignment_info.get("container"):
                                item["container"] = alignment_info.get("container")
                            if not item.get("status") and alignment_info.get("status"):
                                item["status"] = alignment_info.get("status")
                        if not item.get("container") and item_id in container_map:
                            item["container"] = container_map.get(item_id)
                    if "status" not in item:
                        item["status"] = "held"
                    normalized_inventory.append(item)
                elif item is not None:
                    item_id = str(item).strip()
                    entry = {"item": item_id}
                    alignment_info = alignment_for_char.get(item_id)
                    if alignment_info:
                        if alignment_info.get("container"):
                            entry["container"] = alignment_info.get("container")
                        if alignment_info.get("status"):
                            entry["status"] = alignment_info.get("status")
                    if "container" not in entry and item_id in container_map:
                        entry["container"] = container_map.get(item_id)
                    if "status" not in entry:
                        entry["status"] = "held"
                    normalized_inventory.append(entry)
            update["inventory"] = normalized_inventory

        containers = update.get("containers")
        if isinstance(containers, list):
            normalized_containers = []
            for container in containers:
                if isinstance(container, dict):
                    contents = container.get("contents")
                    if contents is None:
                        container["contents"] = []
                    elif not isinstance(contents, list):
                        container["contents"] = [contents]
                    normalized_containers.append(container)
            update["containers"] = normalized_containers

def _fill_character_update_context(patch: Dict[str, Any], scene_card: Dict[str, Any]) -> None:
    updates = patch.get("character_updates")
    if not isinstance(updates, list):
        return
    chapter = scene_card.get("chapter")
    scene = scene_card.get("scene")
    for update in updates:
        if not isinstance(update, dict):
            continue
        if chapter is not None:
            update.setdefault("chapter", chapter)
        if scene is not None:
            update.setdefault("scene", scene)


def _fill_character_continuity_update_context(patch: Dict[str, Any], scene_card: Dict[str, Any]) -> None:
    updates = patch.get("character_continuity_system_updates")
    if not isinstance(updates, list):
        return
    chapter = scene_card.get("chapter")
    scene = scene_card.get("scene")
    for update in updates:
        if not isinstance(update, dict):
            continue
        if chapter is not None:
            update.setdefault("chapter", chapter)
        if scene is not None:
            update.setdefault("scene", scene)


def _coerce_stat_updates(patch: Dict[str, Any]) -> None:
    updates = patch.get("character_continuity_system_updates")
    if not isinstance(updates, list):
        return

    for update in updates:
        if not isinstance(update, dict):
            continue
        set_block = update.get("set") if isinstance(update.get("set"), dict) else {}
        delta_block = update.get("delta") if isinstance(update.get("delta"), dict) else {}

        for key in list(update.keys()):
            if key in {"character_id", "set", "delta", "remove", "chapter", "scene"}:
                continue
            set_block[key] = update.pop(key)

        titles = set_block.get("titles")
        if isinstance(titles, list):
            normalized_titles = []
            for item in titles:
                if isinstance(item, dict):
                    if "name" not in item and "title" in item:
                        item["name"] = item.get("title")
                    normalized_titles.append(item)
                elif item is not None:
                    normalized_titles.append({"name": str(item)})
            set_block["titles"] = normalized_titles

        update["set"] = set_block
        update["delta"] = delta_block


def _coerce_inventory_alignment_updates(patch: Dict[str, Any]) -> None:
    updates = patch.get("inventory_alignment_updates")
    if updates is None:
        return
    if isinstance(updates, dict):
        reason_category = updates.get("reason_category")
        reason = updates.get("reason")
        expected_before = updates.get("expected_before")
        updates_list = updates.get("updates") if isinstance(updates.get("updates"), list) else []
        for update in updates_list:
            if not isinstance(update, dict):
                continue
            if reason_category and "reason_category" not in update:
                update["reason_category"] = reason_category
            if reason and "reason" not in update:
                update["reason"] = reason
            if expected_before and "expected_before" not in update:
                update["expected_before"] = expected_before
        patch["inventory_alignment_updates"] = updates_list
        updates = updates_list

    if not isinstance(updates, list):
        return
    for update in updates:
        if not isinstance(update, dict):
            continue
        inventory = update.get("inventory")
        if isinstance(inventory, list):
            normalized_inventory = []
            for item in inventory:
                if isinstance(item, dict):
                    if "item" not in item and "item_id" in item:
                        item["item"] = item.get("item_id")
                    if "status" not in item:
                        item["status"] = "held"
                    normalized_inventory.append(item)
                elif item is not None:
                    normalized_inventory.append({"item": item, "status": "held"})
            update["inventory"] = normalized_inventory

        remove_block = update.get("remove")
        if isinstance(remove_block, dict):
            normalized_remove = [str(key).strip() for key in remove_block.keys() if str(key).strip()]
            if normalized_remove:
                update["remove"] = normalized_remove
            else:
                update.pop("remove", None)
        elif isinstance(remove_block, list):
            normalized_remove: List[str] = []
            for entry in remove_block:
                if isinstance(entry, str):
                    text = entry.strip()
                    if text:
                        normalized_remove.append(text)
                    continue
                if isinstance(entry, dict):
                    extracted = ""
                    for key in ("path", "field", "key", "item_id", "device_id", "character_id", "id", "name"):
                        candidate = str(entry.get(key) or "").strip()
                        if candidate:
                            extracted = candidate
                            break
                    if extracted:
                        normalized_remove.append(extracted)
                    continue
                if entry is not None:
                    text = str(entry).strip()
                    if text:
                        normalized_remove.append(text)
            if normalized_remove:
                update["remove"] = normalized_remove
            else:
                update.pop("remove", None)


def _coerce_transfer_endpoint(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = str(value or "").strip()
    if not text:
        return {}
    if text.lower() == "world":
        return {"custodian": "world"}
    if text.upper().startswith("CHAR_"):
        return {"character_id": text, "custodian": text}
    return {"custodian": text}


def _merge_transfer_endpoints(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(primary) if isinstance(primary, dict) else {}
    if not isinstance(fallback, dict):
        return merged
    for key, value in fallback.items():
        if key not in merged or merged.get(key) in (None, ""):
            merged[key] = value
    return merged


def _coerce_transfer_updates(patch: Dict[str, Any]) -> None:
    updates = patch.get("transfer_updates")
    if updates is None:
        return
    if isinstance(updates, dict):
        updates = [updates]
        patch["transfer_updates"] = updates
    if not isinstance(updates, list):
        return
    for update in updates:
        if not isinstance(update, dict):
            continue
        if "reason" not in update or not str(update.get("reason") or "").strip():
            reason = update.get("reason_category") or "transfer_alignment"
            update["reason"] = str(reason)
        source_alias = (
            update.get("source_character_id")
            or update.get("source")
            or update.get("from_character_id")
            or update.get("from_custodian")
        )
        destination_alias = (
            update.get("destination_custodian")
            or update.get("destination")
            or update.get("to_character_id")
            or update.get("to_custodian")
        )

        from_endpoint = _coerce_transfer_endpoint(update.get("from"))
        to_endpoint = _coerce_transfer_endpoint(update.get("to"))
        from_endpoint = _merge_transfer_endpoints(from_endpoint, _coerce_transfer_endpoint(source_alias))
        to_endpoint = _merge_transfer_endpoints(to_endpoint, _coerce_transfer_endpoint(destination_alias))

        update["from"] = from_endpoint
        update["to"] = to_endpoint

        for alias_key in (
            "source",
            "source_character_id",
            "from_character_id",
            "from_custodian",
            "destination",
            "destination_custodian",
            "to_character_id",
            "to_custodian",
        ):
            update.pop(alias_key, None)

def _coerce_registry_updates(patch: Dict[str, Any], *, key: str, id_key: str) -> None:
    raw_updates = patch.get(key)
    if raw_updates is None:
        return
    if isinstance(raw_updates, list):
        return
    if not isinstance(raw_updates, dict):
        patch[key] = [raw_updates]
        return

    if id_key in raw_updates:
        patch[key] = [dict(raw_updates)]
        return

    set_block = raw_updates.get("set") if isinstance(raw_updates.get("set"), dict) else {}
    delta_block = raw_updates.get("delta") if isinstance(raw_updates.get("delta"), dict) else {}
    remove_block = raw_updates.get("remove")
    top_reason = raw_updates.get("reason")
    top_category = raw_updates.get("reason_category")
    top_expected = raw_updates.get("expected_before")

    ids: set[str] = set()
    ids.update(set_block.keys())
    ids.update(delta_block.keys())
    if isinstance(remove_block, dict):
        ids.update(remove_block.keys())

    if not ids:
        patch[key] = [dict(raw_updates)]
        return

    normalized = []
    for item_id in sorted(ids):
        update: Dict[str, Any] = {id_key: str(item_id)}
        if item_id in set_block and isinstance(set_block.get(item_id), dict):
            update["set"] = set_block.get(item_id)
        if item_id in delta_block and isinstance(delta_block.get(item_id), dict):
            update["delta"] = delta_block.get(item_id)
        if isinstance(remove_block, dict) and item_id in remove_block:
            update["remove"] = remove_block.get(item_id)
        elif isinstance(remove_block, list) and len(ids) == 1:
            update["remove"] = remove_block

        if top_reason and not update.get("reason"):
            update["reason"] = top_reason
        if top_category and not update.get("reason_category"):
            update["reason_category"] = top_category
        if top_expected and not update.get("expected_before"):
            update["expected_before"] = top_expected

        normalized.append(update)

    patch[key] = normalized


def _migrate_numeric_invariants(patch: Dict[str, Any]) -> None:
    updates = patch.get("character_updates")
    if not isinstance(updates, list):
        return
    continuity_updates = patch.get("character_continuity_system_updates")
    if not isinstance(continuity_updates, list):
        continuity_updates = []
        patch["character_continuity_system_updates"] = continuity_updates

    def _ensure_update(character_id: str) -> Dict[str, Any]:
        for update in continuity_updates:
            if isinstance(update, dict) and update.get("character_id") == character_id:
                return update
        new_update = {"character_id": character_id, "set": {}}
        continuity_updates.append(new_update)
        return new_update

    for update in updates:
        if not isinstance(update, dict):
            continue
        character_id = update.get("character_id")
        if not character_id:
            continue
        invariants = update.get("invariants_add")
        if not isinstance(invariants, list):
            continue
        remaining = []
        for invariant in invariants:
            text = str(invariant)
            if re.search(r"\b(hp|mp|stamina|mana|crit|accuracy)\s*[:=]\s*\d", text, re.IGNORECASE):
                target = _ensure_update(character_id)
                set_block = target.get("set") if isinstance(target.get("set"), dict) else {}
                set_block.setdefault("system_tracking_metadata", {}).setdefault("raw_invariants", []).append(text)
                target["set"] = set_block
            else:
                remaining.append(invariant)
        update["invariants_add"] = remaining


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


def _scene_scopes(scene_card: Dict[str, Any] | None) -> tuple[str, str]:
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


def _block_touches_physical_keys(update: Dict[str, Any], keys: set[str]) -> bool:
    if not isinstance(update, dict):
        return False
    for block_name in ("set", "delta"):
        block = update.get(block_name)
        if isinstance(block, dict) and any(key in block for key in keys):
            return True
    remove_block = update.get("remove")
    if isinstance(remove_block, list) and any(str(item) in keys for item in remove_block):
        return True
    return False


def _normalize_state_patch_for_validation(
    patch: Dict[str, Any],
    scene_card: Dict[str, Any],
    *,
    preflight: bool = False,
) -> Dict[str, Any]:
    normalized = _sanitize_preflight_patch(patch, scene_card) if preflight else patch
    if "schema_version" not in normalized:
        normalized["schema_version"] = "1.0"
    _coerce_summary_update(normalized)
    _coerce_character_updates(normalized)
    _coerce_stat_updates(normalized)
    _coerce_transfer_updates(normalized)
    _coerce_inventory_alignment_updates(normalized)
    _coerce_registry_updates(normalized, key="item_registry_updates", id_key="item_id")
    _coerce_registry_updates(normalized, key="plot_device_updates", id_key="device_id")
    _migrate_numeric_invariants(normalized)
    _fill_character_update_context(normalized, scene_card)
    _fill_character_continuity_update_context(normalized, scene_card)
    return normalized


def _sanitize_preflight_patch(
    patch: Dict[str, Any],
    scene_card: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    allowed_keys = {
        "schema_version",
        "world_updates",
        "thread_updates",
        "world",
        "canon_updates",
        "character_updates",
        "character_continuity_system_updates",
        "global_continuity_system_updates",
        "character_stat_updates",
        "character_skill_updates",
        "run_stat_updates",
        "run_skill_updates",
        "inventory_alignment_updates",
        "item_registry_updates",
        "plot_device_updates",
        "transfer_updates",
    }
    sanitized: Dict[str, Any] = {}
    for key, value in patch.items():
        if key in allowed_keys:
            sanitized[key] = value
    sanitized.setdefault("schema_version", "1.0")

    timeline_scope, ontological_scope = _scene_scopes(scene_card)
    if timeline_scope != "present" or ontological_scope != "real":
        inventory_updates = []
        for update in sanitized.get("inventory_alignment_updates", []) or []:
            if isinstance(update, dict) and _scope_override_enabled(update):
                inventory_updates.append(update)
        if inventory_updates:
            sanitized["inventory_alignment_updates"] = inventory_updates
        else:
            sanitized.pop("inventory_alignment_updates", None)

        transfer_updates = []
        for update in sanitized.get("transfer_updates", []) or []:
            if isinstance(update, dict) and _scope_override_enabled(update):
                transfer_updates.append(update)
        if transfer_updates:
            sanitized["transfer_updates"] = transfer_updates
        else:
            sanitized.pop("transfer_updates", None)

        item_updates = []
        for update in sanitized.get("item_registry_updates", []) or []:
            if not isinstance(update, dict):
                continue
            physical = _block_touches_physical_keys(update, PHYSICAL_ITEM_MUTATION_KEYS)
            if physical and not _scope_override_enabled(update):
                continue
            item_updates.append(update)
        if item_updates:
            sanitized["item_registry_updates"] = item_updates
        else:
            sanitized.pop("item_registry_updates", None)

        device_updates = []
        for update in sanitized.get("plot_device_updates", []) or []:
            if not isinstance(update, dict):
                continue
            physical = _block_touches_physical_keys(update, PHYSICAL_DEVICE_MUTATION_KEYS)
            if physical and not _scope_override_enabled(update):
                continue
            device_updates.append(update)
        if device_updates:
            sanitized["plot_device_updates"] = device_updates
        else:
            sanitized.pop("plot_device_updates", None)

    return sanitized





