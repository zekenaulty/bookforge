from __future__ import annotations

from typing import Any, Dict, List


_EQUIPPED_STATUSES = {"equipped", "worn"}


def _item_display_name_map(item_registry: Dict[str, Any]) -> Dict[str, str]:
    items = item_registry.get("items") if isinstance(item_registry, dict) else None
    if not isinstance(items, list):
        return {}
    mapping: Dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id") or "").strip()
        if not item_id:
            continue
        display = str(item.get("display_name") or "").strip()
        if not display:
            display = str(item.get("name") or "").strip()
        if display:
            mapping[item_id] = display
    return mapping


def _derive_attire_items(inventory: List[Dict[str, Any]], name_map: Dict[str, str]) -> List[str]:
    items: List[str] = []
    for entry in inventory:
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status") or "").strip().lower()
        if status not in _EQUIPPED_STATUSES:
            continue
        item = str(entry.get("item") or "").strip()
        if not item:
            continue
        display = name_map.get(item, item)
        items.append(display)
    return items


def _with_derived_attire(
    character_states: List[Dict[str, Any]],
    item_registry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    name_map = _item_display_name_map(item_registry)
    enriched: List[Dict[str, Any]] = []
    for state in character_states:
        if not isinstance(state, dict):
            continue
        copy_state = dict(state)
        appearance = copy_state.get("appearance_current")
        if not isinstance(appearance, dict):
            enriched.append(copy_state)
            continue
        attire = appearance.get("attire") if isinstance(appearance.get("attire"), dict) else {}
        mode = str(attire.get("mode") or "").strip().lower()
        if mode == "signature":
            enriched.append(copy_state)
            continue
        inventory = copy_state.get("inventory")
        if not isinstance(inventory, list):
            enriched.append(copy_state)
            continue
        derived_items = _derive_attire_items(inventory, name_map)
        appearance_copy = dict(appearance)
        appearance_copy["attire"] = {
            "mode": "derived",
            "items": derived_items,
        }
        copy_state["appearance_current"] = appearance_copy
        enriched.append(copy_state)
    return enriched
