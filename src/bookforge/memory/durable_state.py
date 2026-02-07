from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import hashlib
import json
import re
import shutil

from bookforge.util.schema import SCHEMA_VERSION, validate_json


def _context_root(book_root: Path) -> Path:
    return book_root / "draft" / "context"


def item_registry_path(book_root: Path) -> Path:
    return _context_root(book_root) / "item_registry.json"


def plot_devices_path(book_root: Path) -> Path:
    return _context_root(book_root) / "plot_devices.json"


def items_index_path(book_root: Path) -> Path:
    return _context_root(book_root) / "items" / "index.json"


def plot_devices_index_path(book_root: Path) -> Path:
    return _context_root(book_root) / "plot_devices" / "index.json"


def durable_commits_path(book_root: Path) -> Path:
    return _context_root(book_root) / "durable_commits.json"


def _default_item_registry() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "items": [],
    }


def _default_plot_devices() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "devices": [],
    }


def _default_durable_commits() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "applied_hashes": [],
        "latest_scene": {"chapter": 0, "scene": 0},
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _normalize_registry(data: Any, list_key: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        data = {}
    normalized: Dict[str, Any] = dict(data)
    normalized["schema_version"] = SCHEMA_VERSION
    values = normalized.get(list_key)
    if not isinstance(values, list):
        values = []
    normalized[list_key] = values
    return normalized


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", str(value)).strip("_").lower()
    return text or "item"


def _derived_item_id(character_id: str, item_name: str) -> str:
    slug = _slugify(item_name)
    digest = hashlib.sha1(f"{character_id}|{item_name}".encode("utf-8")).hexdigest()[:8]
    return f"ITEM_{slug}_{digest}"


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _extract_thread_tokens(text: str) -> Set[str]:
    tokens: Set[str] = set()
    for match in re.findall(r"\bTHREAD_[A-Za-z0-9_]+\b", str(text)):
        token = str(match).strip()
        if token:
            tokens.add(token)
    return tokens


def _humanize_thread_id(thread_id: str) -> str:
    token = str(thread_id).strip()
    if token.upper().startswith("THREAD_"):
        token = token[7:]
    words = re.sub(r"[_\-]+", " ", token).strip()
    if not words:
        return "Unclassified Thread"
    return " ".join([part.capitalize() for part in words.split()])


def _derived_device_id(thread_id: str, label: str) -> str:
    slug = _slugify(label or thread_id)
    digest = hashlib.sha1(f"{thread_id}|{label}".encode("utf-8")).hexdigest()[:8]
    return f"DEVICE_{slug}_{digest}"


def _extract_thread_hints_from_outline(book_root: Path) -> Dict[str, str]:
    outline_path = book_root / "outline" / "outline.json"
    if not outline_path.exists():
        return {}
    try:
        outline = json.loads(outline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(outline, dict):
        return {}
    thread_map: Dict[str, str] = {}
    raw_threads = outline.get("threads")
    if not isinstance(raw_threads, list):
        return thread_map
    for entry in raw_threads:
        if isinstance(entry, dict):
            thread_id = str(entry.get("thread_id") or "").strip()
            label = str(entry.get("label") or "").strip()
        else:
            thread_id = str(entry).strip()
            label = ""
        if not thread_id:
            continue
        if not label:
            label = _humanize_thread_id(thread_id)
        thread_map[thread_id] = label
    return thread_map


def _extract_thread_hints_from_state(book_root: Path) -> Dict[str, str]:
    state_path = book_root / "state.json"
    if not state_path.exists():
        return {}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(state, dict):
        return {}

    thread_map: Dict[str, str] = {}

    world = state.get("world")
    if isinstance(world, dict):
        open_threads = world.get("open_threads")
        if isinstance(open_threads, list):
            for value in open_threads:
                thread_id = str(value).strip()
                if not thread_id:
                    continue
                thread_map[thread_id] = _humanize_thread_id(thread_id)

        recent_facts = world.get("recent_facts")
        if isinstance(recent_facts, list):
            for fact in recent_facts:
                for token in _extract_thread_tokens(str(fact)):
                    thread_map.setdefault(token, _humanize_thread_id(token))

    summary = state.get("summary")
    if isinstance(summary, dict):
        for key in (
            "last_scene",
            "chapter_so_far",
            "story_so_far",
            "key_facts_ring",
            "must_stay_true",
            "pending_story_rollups",
        ):
            values = summary.get(key)
            if not isinstance(values, list):
                continue
            for value in values:
                for token in _extract_thread_tokens(str(value)):
                    thread_map.setdefault(token, _humanize_thread_id(token))

    return thread_map


def _extract_thread_hints_from_continuity(book_root: Path) -> Dict[str, str]:
    continuity_path = _context_root(book_root) / "continuity_pack.json"
    if not continuity_path.exists():
        return {}
    try:
        payload = json.loads(continuity_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    thread_map: Dict[str, str] = {}

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            thread_id = str(value.get("thread_id") or "").strip()
            label = str(value.get("label") or "").strip()
            if thread_id:
                thread_map[thread_id] = label or _humanize_thread_id(thread_id)
            for nested in value.values():
                _walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                _walk(nested)
            return
        for token in _extract_thread_tokens(str(value)):
            thread_map.setdefault(token, _humanize_thread_id(token))

    _walk(payload)
    return thread_map


def _collect_thread_hints(book_root: Path) -> List[Tuple[str, str]]:
    merged: Dict[str, str] = {}
    for source in (
        _extract_thread_hints_from_state(book_root),
        _extract_thread_hints_from_outline(book_root),
        _extract_thread_hints_from_continuity(book_root),
    ):
        for thread_id, label in source.items():
            token = str(thread_id).strip()
            if not token:
                continue
            merged[token] = str(label).strip() or _humanize_thread_id(token)
    return [(thread_id, merged[thread_id]) for thread_id in sorted(merged.keys())]


def _iter_character_state_files(book_root: Path) -> list[Path]:
    chars_dir = _context_root(book_root) / "characters"
    if not chars_dir.exists():
        return []
    return sorted(chars_dir.glob("*.state.json"))


def _migrate_item_registry_from_character_states(book_root: Path) -> bool:
    path = item_registry_path(book_root)
    try:
        payload = _normalize_registry(json.loads(path.read_text(encoding="utf-8")), "items")
    except json.JSONDecodeError:
        payload = _default_item_registry()

    if payload.get("items"):
        return False

    items_by_id: Dict[str, Dict[str, Any]] = {}
    for state_path in _iter_character_state_files(book_root):
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(state, dict):
            continue

        character_id = str(state.get("character_id") or "").strip()
        if not character_id:
            continue

        inventory = state.get("inventory")
        if not isinstance(inventory, list):
            continue

        last_touched = state.get("last_touched") if isinstance(state.get("last_touched"), dict) else {}
        chapter = _coerce_int(last_touched.get("chapter"))
        scene = _coerce_int(last_touched.get("scene"))

        for entry in inventory:
            if not isinstance(entry, dict):
                continue
            item_name = str(entry.get("item_name") or entry.get("item") or "").strip()
            item_id = str(entry.get("item_id") or "").strip()
            if not item_id and item_name:
                item_id = _derived_item_id(character_id, item_name)
            if not item_id:
                continue
            if not item_name:
                item_name = item_id

            status = str(entry.get("status") or "").strip().lower()
            state_tags = ["unclassified"]
            if status:
                state_tags.append(status)

            if item_id in items_by_id:
                continue

            items_by_id[item_id] = {
                "item_id": item_id,
                "name": item_name,
                "type": str(entry.get("type") or "unclassified"),
                "owner_scope": str(entry.get("owner_scope") or "character"),
                "custodian": character_id,
                "linked_threads": [],
                "state_tags": state_tags,
                "last_seen": {
                    "chapter": chapter,
                    "scene": scene,
                    "location": "",
                },
            }

    if not items_by_id:
        return False

    payload["items"] = [items_by_id[key] for key in sorted(items_by_id.keys())]
    save_item_registry(book_root, payload)
    return True


def _migrate_plot_devices_from_continuity_hints(book_root: Path) -> bool:
    path = plot_devices_path(book_root)
    try:
        payload = _normalize_registry(json.loads(path.read_text(encoding="utf-8")), "devices")
    except json.JSONDecodeError:
        payload = _default_plot_devices()

    if payload.get("devices"):
        return False

    thread_hints = _collect_thread_hints(book_root)
    if not thread_hints:
        return False

    devices: List[Dict[str, Any]] = []
    for thread_id, label in thread_hints:
        device_id = _derived_device_id(thread_id, label)
        devices.append(
            {
                "device_id": device_id,
                "name": label,
                "custody_scope": "thread",
                "custody_ref": thread_id,
                "activation_state": "tracked",
                "linked_threads": [thread_id],
                "constraints": [],
                "last_seen": {"chapter": 0, "scene": 0, "location": ""},
                "state_tags": ["unclassified", "seed_from_thread_hint"],
            }
        )

    payload["devices"] = devices
    save_plot_devices(book_root, payload)
    return True


def ensure_item_registry(book_root: Path) -> Path:
    path = item_registry_path(book_root)
    if not path.exists():
        _write_json(path, _default_item_registry())
    else:
        payload = _normalize_registry(json.loads(path.read_text(encoding="utf-8")), "items")
        validate_json(payload, "item_registry")
        _write_json(path, payload)
    return path


def ensure_plot_devices(book_root: Path) -> Path:
    path = plot_devices_path(book_root)
    if not path.exists():
        _write_json(path, _default_plot_devices())
    else:
        payload = _normalize_registry(json.loads(path.read_text(encoding="utf-8")), "devices")
        validate_json(payload, "plot_devices")
        _write_json(path, payload)
    return path


def ensure_durable_state_files(book_root: Path) -> None:
    context = _context_root(book_root)
    (context / "items" / "history").mkdir(parents=True, exist_ok=True)
    (context / "plot_devices" / "history").mkdir(parents=True, exist_ok=True)

    if not items_index_path(book_root).exists():
        _write_json(items_index_path(book_root), {"schema_version": SCHEMA_VERSION, "item_ids": []})
    if not plot_devices_index_path(book_root).exists():
        _write_json(plot_devices_index_path(book_root), {"schema_version": SCHEMA_VERSION, "device_ids": []})
    if not durable_commits_path(book_root).exists():
        _write_json(durable_commits_path(book_root), _default_durable_commits())

    ensure_item_registry(book_root)
    ensure_plot_devices(book_root)
    _migrate_item_registry_from_character_states(book_root)
    _migrate_plot_devices_from_continuity_hints(book_root)


def load_item_registry(book_root: Path) -> Dict[str, Any]:
    ensure_durable_state_files(book_root)
    payload = _normalize_registry(json.loads(item_registry_path(book_root).read_text(encoding="utf-8")), "items")
    validate_json(payload, "item_registry")
    return payload


def load_plot_devices(book_root: Path) -> Dict[str, Any]:
    ensure_durable_state_files(book_root)
    payload = _normalize_registry(json.loads(plot_devices_path(book_root).read_text(encoding="utf-8")), "devices")
    validate_json(payload, "plot_devices")
    return payload


def save_item_registry(book_root: Path, payload: Dict[str, Any]) -> None:
    normalized = _normalize_registry(payload, "items")
    validate_json(normalized, "item_registry")
    _write_json(item_registry_path(book_root), normalized)
    item_ids = []
    for item in normalized.get("items", []):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id") or "").strip()
        if item_id:
            item_ids.append(item_id)
    _write_json(items_index_path(book_root), {"schema_version": SCHEMA_VERSION, "item_ids": item_ids})


def save_plot_devices(book_root: Path, payload: Dict[str, Any]) -> None:
    normalized = _normalize_registry(payload, "devices")
    validate_json(normalized, "plot_devices")
    _write_json(plot_devices_path(book_root), normalized)
    device_ids = []
    for device in normalized.get("devices", []):
        if not isinstance(device, dict):
            continue
        device_id = str(device.get("device_id") or "").strip()
        if device_id:
            device_ids.append(device_id)
    _write_json(plot_devices_index_path(book_root), {"schema_version": SCHEMA_VERSION, "device_ids": device_ids})


def load_durable_commits(book_root: Path) -> Dict[str, Any]:
    ensure_durable_state_files(book_root)
    path = durable_commits_path(book_root)
    data: Any
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    hashes = data.get("applied_hashes")
    if not isinstance(hashes, list):
        hashes = []
    normalized_hashes = []
    for value in hashes:
        text = str(value).strip()
        if text:
            normalized_hashes.append(text)
    latest_scene_raw = data.get("latest_scene") if isinstance(data.get("latest_scene"), dict) else {}
    latest_scene = {
        "chapter": max(0, _coerce_int(latest_scene_raw.get("chapter"))),
        "scene": max(0, _coerce_int(latest_scene_raw.get("scene"))),
    }

    payload = {
        "schema_version": SCHEMA_VERSION,
        "applied_hashes": normalized_hashes,
        "latest_scene": latest_scene,
    }
    _write_json(path, payload)
    return payload


def save_durable_commits(book_root: Path, payload: Dict[str, Any]) -> None:
    data = {
        "schema_version": SCHEMA_VERSION,
        "applied_hashes": [],
        "latest_scene": {"chapter": 0, "scene": 0},
    }
    if isinstance(payload, dict):
        hashes = payload.get("applied_hashes")
        if isinstance(hashes, list):
            data["applied_hashes"] = [str(item).strip() for item in hashes if str(item).strip()]

        latest_scene_raw = payload.get("latest_scene") if isinstance(payload.get("latest_scene"), dict) else {}
        data["latest_scene"] = {
            "chapter": max(0, _coerce_int(latest_scene_raw.get("chapter"))),
            "scene": max(0, _coerce_int(latest_scene_raw.get("scene"))),
        }
    _write_json(durable_commits_path(book_root), data)


def _history_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def snapshot_item_registry(book_root: Path, chapter: int, scene: int) -> Path:
    ensure_durable_state_files(book_root)
    src = item_registry_path(book_root)
    target = _context_root(book_root) / "items" / "history" / (
        f"ch{chapter:03d}_sc{scene:03d}_item_registry_{_history_stamp()}.json"
    )
    shutil.copyfile(src, target)
    return target


def snapshot_plot_devices(book_root: Path, chapter: int, scene: int) -> Path:
    ensure_durable_state_files(book_root)
    src = plot_devices_path(book_root)
    target = _context_root(book_root) / "plot_devices" / "history" / (
        f"ch{chapter:03d}_sc{scene:03d}_plot_devices_{_history_stamp()}.json"
    )
    shutil.copyfile(src, target)
    return target
