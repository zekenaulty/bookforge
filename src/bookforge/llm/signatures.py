from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import os
import time

from .storage import (
    legacy_signature_active_lock_path,
    legacy_signature_active_path,
    legacy_signature_index_path,
    legacy_signature_ledger_path,
    signature_active_lock_path,
    signature_active_path,
    signature_index_path,
    signature_ledger_path,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ledger_path(workspace: Path) -> Path:
    return signature_ledger_path(workspace)


def index_path(workspace: Path) -> Path:
    return signature_index_path(workspace)


def active_path(workspace: Path) -> Path:
    return signature_active_path(workspace)


def active_lock_path(workspace: Path) -> Path:
    return signature_active_lock_path(workspace)


def _preferred_or_legacy_path(preferred: Path, legacy: Path) -> Path:
    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return preferred


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _bootstrap_ledger_target(workspace: Path) -> Path:
    preferred = ledger_path(workspace)
    legacy = legacy_signature_ledger_path(workspace)
    if not preferred.exists() and legacy.exists():
        _ensure_parent(preferred)
        preferred.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
    return preferred


def _bootstrap_index_target(workspace: Path) -> Path:
    preferred = index_path(workspace)
    legacy = legacy_signature_index_path(workspace)
    if not preferred.exists() and legacy.exists():
        _ensure_parent(preferred)
        preferred.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
    return preferred


def _bootstrap_active_target(workspace: Path) -> Path:
    preferred = active_path(workspace)
    legacy = legacy_signature_active_path(workspace)
    if not preferred.exists() and legacy.exists():
        _ensure_parent(preferred)
        preferred.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
    return preferred


def _bootstrap_active_lock_target(workspace: Path) -> Path:
    preferred = active_lock_path(workspace)
    legacy = legacy_signature_active_lock_path(workspace)
    if not preferred.exists() and legacy.exists():
        _ensure_parent(preferred)
        preferred.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
    return preferred


def _load_index(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "thought_signature_index_v1",
            "updated_at": _utc_now_iso(),
            "latest": None,
            "by_scope": {},
            "by_signature_id": {},
            "global_author": None,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "schema_version": "thought_signature_index_v1",
            "updated_at": _utc_now_iso(),
            "latest": None,
            "by_scope": {},
            "by_signature_id": {},
            "global_author": None,
        }
    if not isinstance(payload, dict):
        return {
            "schema_version": "thought_signature_index_v1",
            "updated_at": _utc_now_iso(),
            "latest": None,
            "by_scope": {},
            "by_signature_id": {},
            "global_author": None,
        }
    payload.setdefault("by_scope", {})
    payload.setdefault("by_signature_id", {})
    payload.setdefault("latest", None)
    payload.setdefault("global_author", None)
    return payload


def _empty_index_payload() -> Dict[str, Any]:
    return {
        "schema_version": "thought_signature_index_v1",
        "updated_at": _utc_now_iso(),
        "latest": None,
        "by_scope": {},
        "by_signature_id": {},
        "global_author": None,
    }


def _load_active(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "thought_signature_active_v1",
            "updated_at": _utc_now_iso(),
            "by_phase": {},
            "global": {},
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "schema_version": "thought_signature_active_v1",
            "updated_at": _utc_now_iso(),
            "by_phase": {},
            "global": {},
        }
    if not isinstance(payload, dict):
        return {
            "schema_version": "thought_signature_active_v1",
            "updated_at": _utc_now_iso(),
            "by_phase": {},
            "global": {},
        }
    payload.setdefault("by_phase", {})
    payload.setdefault("global", {})
    return payload


def _empty_active_payload() -> Dict[str, Any]:
    return {
        "schema_version": "thought_signature_active_v1",
        "updated_at": _utc_now_iso(),
        "by_phase": {},
        "global": {},
    }


def _scope_key(record: Dict[str, Any]) -> str:
    parts = [
        str(record.get("book_id") or ""),
        str(record.get("phase_id") or ""),
        str(record.get("turn_id") or ""),
        str(record.get("chapter_id") or ""),
    ]
    return "|".join(parts)


def _policy_for_phase(phase_id: str) -> str:
    phase_key = str(phase_id or "").strip().upper()
    if phase_key:
        override = os.environ.get(f"THOUGHT_ACTIVE_POLICY_{phase_key}")
        if override:
            return str(override).strip().lower()
    default_policy = os.environ.get("THOUGHT_ACTIVE_POLICY_DEFAULT") or "prefer_t1_with_outcome"
    return str(default_policy).strip().lower()


def _summarize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    keep = {
        "schema_version": record.get("schema_version"),
        "signature_id": record.get("signature_id"),
        "created_at": record.get("created_at"),
        "label": record.get("label"),
        "provider": record.get("provider"),
        "model": record.get("model"),
        "phase_id": record.get("phase_id"),
        "turn_id": record.get("turn_id"),
        "book_id": record.get("book_id"),
        "chapter_id": record.get("chapter_id"),
        "scene_id": record.get("scene_id"),
        "assistant_parts_path": record.get("assistant_parts_path"),
        "log_path": record.get("log_path"),
        "scope": record.get("scope"),
    }
    return keep


def _build_index_payload(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    payload = _empty_index_payload()
    by_scope: Dict[str, Any] = {}
    by_signature_id: Dict[str, Any] = {}
    latest: Optional[Dict[str, Any]] = None
    global_author: Optional[Dict[str, Any]] = None
    for record in records:
        if not isinstance(record, dict):
            continue
        summary = dict(record)
        signature_id = str(record.get("signature_id") or "")
        if signature_id:
            by_signature_id[signature_id] = summary
        by_scope[_scope_key(record)] = summary
        latest = summary
        if record.get("scope") == "global_author":
            global_author = summary
    payload["by_scope"] = by_scope
    payload["by_signature_id"] = by_signature_id
    payload["latest"] = latest
    payload["global_author"] = global_author
    payload["updated_at"] = _utc_now_iso()
    return payload


def _build_active_payload(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    payload = _empty_active_payload()
    by_phase: Dict[str, Any] = {}
    global_slot: Dict[str, Any] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        phase_id = str(record.get("phase_id") or "")
        turn_id = str(record.get("turn_id") or "")
        summary = _summarize_record(record)
        policy = _policy_for_phase(phase_id)
        phase_bucket = by_phase.get(phase_id) if isinstance(by_phase.get(phase_id), dict) else {}
        phase_bucket["policy"] = policy
        phase_bucket["last"] = summary
        if policy in {"prefer_t1", "prefer_t1_with_outcome"}:
            if turn_id.upper() == "T1":
                phase_bucket["intent"] = summary
            elif turn_id.upper() == "T2":
                phase_bucket["outcome"] = summary
        elif policy == "prefer_t2":
            if turn_id.upper() == "T2":
                phase_bucket["intent"] = summary
            else:
                phase_bucket.setdefault("intent", summary)
        elif policy == "prefer_latest":
            phase_bucket["intent"] = summary
            phase_bucket["outcome"] = summary
        else:
            phase_bucket["intent"] = summary
        by_phase[phase_id] = phase_bucket

        global_slot["last"] = summary
        if turn_id.upper() == "T1":
            global_slot["intent"] = summary
        elif turn_id.upper() == "T2":
            global_slot["outcome"] = summary
    payload["by_phase"] = by_phase
    payload["global"] = global_slot
    payload["updated_at"] = _utc_now_iso()
    return payload


def _acquire_lock(lock_path: Path, ttl_seconds: int = 30) -> bool:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    try:
        lock_path.open("x").write(str(now))
        return True
    except FileExistsError:
        try:
            mtime = lock_path.stat().st_mtime
        except OSError:
            return False
        if now - mtime > ttl_seconds:
            try:
                lock_path.unlink()
            except OSError:
                return False
            try:
                lock_path.open("x").write(str(now))
                return True
            except OSError:
                return False
        return False


def _release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except OSError:
        pass


def append_signature_records(workspace: Path, records: Iterable[Dict[str, Any]]) -> None:
    records_list = [record for record in records if isinstance(record, dict)]
    if not records_list:
        return
    ledger = _bootstrap_ledger_target(workspace)
    _ensure_parent(ledger)
    with ledger.open("a", encoding="utf-8") as handle:
        for record in records_list:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    index_file = _bootstrap_index_target(workspace)
    index_payload = _load_index(index_file)
    by_scope = index_payload.get("by_scope") if isinstance(index_payload.get("by_scope"), dict) else {}
    by_signature_id = index_payload.get("by_signature_id") if isinstance(index_payload.get("by_signature_id"), dict) else {}
    for record in records_list:
        summary = dict(record)
        signature_id = str(record.get("signature_id") or "")
        if signature_id:
            by_signature_id[signature_id] = summary
        by_scope[_scope_key(record)] = summary
        index_payload["latest"] = summary
        if record.get("scope") == "global_author":
            index_payload["global_author"] = summary
    index_payload["by_scope"] = by_scope
    index_payload["by_signature_id"] = by_signature_id
    index_payload["updated_at"] = _utc_now_iso()
    index_file.write_text(json.dumps(index_payload, ensure_ascii=True, indent=2), encoding="utf-8")


def update_active_signatures(workspace: Path, records: Iterable[Dict[str, Any]]) -> None:
    records_list = [record for record in records if isinstance(record, dict)]
    if not records_list:
        return
    lock_path = _bootstrap_active_lock_target(workspace)
    if not _acquire_lock(lock_path):
        return
    try:
        active_file = _bootstrap_active_target(workspace)
        active_payload = _load_active(active_file)
        by_phase = active_payload.get("by_phase") if isinstance(active_payload.get("by_phase"), dict) else {}
        global_slot = active_payload.get("global") if isinstance(active_payload.get("global"), dict) else {}

        for record in records_list:
            phase_id = str(record.get("phase_id") or "")
            turn_id = str(record.get("turn_id") or "")
            summary = _summarize_record(record)
            policy = _policy_for_phase(phase_id)
            phase_bucket = by_phase.get(phase_id) if isinstance(by_phase.get(phase_id), dict) else {}
            phase_bucket["policy"] = policy
            # Always update last seen for the phase.
            phase_bucket["last"] = summary
            if policy in {"prefer_t1", "prefer_t1_with_outcome"}:
                if turn_id.upper() == "T1":
                    phase_bucket["intent"] = summary
                elif turn_id.upper() == "T2":
                    phase_bucket["outcome"] = summary
                else:
                    # If no turn_id, treat as last; do not override intent/outcome.
                    pass
            elif policy == "prefer_t2":
                if turn_id.upper() == "T2":
                    phase_bucket["intent"] = summary
                else:
                    phase_bucket.setdefault("intent", summary)
            elif policy == "prefer_latest":
                phase_bucket["intent"] = summary
                phase_bucket["outcome"] = summary
            else:
                phase_bucket["intent"] = summary
            by_phase[phase_id] = phase_bucket

            # Global slot tracks latest overall signature and intent/outcome if turn_id supplied.
            global_slot["last"] = summary
            if turn_id.upper() == "T1":
                global_slot["intent"] = summary
            elif turn_id.upper() == "T2":
                global_slot["outcome"] = summary

        active_payload["by_phase"] = by_phase
        active_payload["global"] = global_slot
        active_payload["updated_at"] = _utc_now_iso()
        active_file.write_text(json.dumps(active_payload, ensure_ascii=True, indent=2), encoding="utf-8")
    finally:
        _release_lock(lock_path)


def set_active_signature(
    workspace: Path,
    record: Dict[str, Any],
    *,
    intent: bool = True,
    outcome: bool = False,
) -> None:
    if not isinstance(record, dict):
        return
    lock_path = _bootstrap_active_lock_target(workspace)
    if not _acquire_lock(lock_path):
        return
    try:
        active_file = _bootstrap_active_target(workspace)
        active_payload = _load_active(active_file)
        by_phase = active_payload.get("by_phase") if isinstance(active_payload.get("by_phase"), dict) else {}
        global_slot = active_payload.get("global") if isinstance(active_payload.get("global"), dict) else {}

        phase_id = str(record.get("phase_id") or "")
        summary = _summarize_record(record)
        phase_bucket = by_phase.get(phase_id) if isinstance(by_phase.get(phase_id), dict) else {}
        phase_bucket["last"] = summary
        if intent:
            phase_bucket["intent"] = summary
        if outcome:
            phase_bucket["outcome"] = summary
        by_phase[phase_id] = phase_bucket

        global_slot["last"] = summary
        if intent:
            global_slot["intent"] = summary
        if outcome:
            global_slot["outcome"] = summary
        active_payload["by_phase"] = by_phase
        active_payload["global"] = global_slot
        active_payload["updated_at"] = _utc_now_iso()
        active_file.write_text(json.dumps(active_payload, ensure_ascii=True, indent=2), encoding="utf-8")
    finally:
        _release_lock(lock_path)


def load_signature_ledger(workspace: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    path = _preferred_or_legacy_path(ledger_path(workspace), legacy_signature_ledger_path(workspace))
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    if limit is not None and limit > 0:
        return records[-limit:]
    return records


def load_signature_index(workspace: Path) -> Dict[str, Any]:
    path = _preferred_or_legacy_path(index_path(workspace), legacy_signature_index_path(workspace))
    return _load_index(path)


def select_signature(
    workspace: Path,
    *,
    signature_id: Optional[str] = None,
    phase_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    book_id: Optional[str] = None,
    global_author: bool = False,
) -> Optional[Dict[str, Any]]:
    index_payload = load_signature_index(workspace)
    if global_author:
        record = index_payload.get("global_author")
        return record if isinstance(record, dict) else None
    by_signature_id = (
        index_payload.get("by_signature_id")
        if isinstance(index_payload.get("by_signature_id"), dict)
        else {}
    )
    if signature_id:
        record = by_signature_id.get(signature_id)
        return record if isinstance(record, dict) else None
    scope_key = "|".join([str(book_id or ""), str(phase_id or ""), str(turn_id or ""), str(chapter_id or "")])
    by_scope = index_payload.get("by_scope") if isinstance(index_payload.get("by_scope"), dict) else {}
    record = by_scope.get(scope_key)
    if isinstance(record, dict):
        return record
    latest = index_payload.get("latest")
    return latest if isinstance(latest, dict) else None


def purge_signatures(workspace: Path, *, book_id: Optional[str] = None) -> Dict[str, int]:
    records = load_signature_ledger(workspace, limit=None)
    if book_id:
        kept = [
            record
            for record in records
            if str(record.get("book_id") or "") != str(book_id)
        ]
    else:
        kept = []

    ledger = ledger_path(workspace)
    _ensure_parent(ledger)
    with ledger.open("w", encoding="utf-8") as handle:
        for record in kept:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    index_file = index_path(workspace)
    _ensure_parent(index_file)
    index_payload = _build_index_payload(kept)
    index_file.write_text(json.dumps(index_payload, ensure_ascii=True, indent=2), encoding="utf-8")

    active_file = active_path(workspace)
    _ensure_parent(active_file)
    active_payload = _build_active_payload(kept)
    active_file.write_text(json.dumps(active_payload, ensure_ascii=True, indent=2), encoding="utf-8")

    return {
        "removed": len(records) - len(kept),
        "kept": len(kept),
    }
