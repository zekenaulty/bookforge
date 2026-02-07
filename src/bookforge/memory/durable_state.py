from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import json
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

    ensure_item_registry(book_root)
    ensure_plot_devices(book_root)


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


def save_plot_devices(book_root: Path, payload: Dict[str, Any]) -> None:
    normalized = _normalize_registry(payload, "devices")
    validate_json(normalized, "plot_devices")
    _write_json(plot_devices_path(book_root), normalized)


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