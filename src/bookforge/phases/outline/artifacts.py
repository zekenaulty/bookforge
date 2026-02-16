from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json


PIPELINE_HISTORY_FILE = "phase_history.json"
PIPELINE_LATEST_FILE = "pipeline_latest.json"
PIPELINE_LATEST_ALIAS_FILE = "outline_pipeline_latest.json"
PIPELINE_REPORT_FILE = "outline_pipeline_report.json"
PIPELINE_REPORT_LATEST_FILE = "outline_pipeline_report_latest.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def pipeline_root(book_root: Path) -> Path:
    return book_root / "outline" / "pipeline_runs"


def run_dir(book_root: Path, run_id: str) -> Path:
    return pipeline_root(book_root) / run_id


def create_run(book_root: Path, run_id: Optional[str] = None) -> Tuple[str, Path]:
    value = run_id or generate_run_id()
    path = run_dir(book_root, value)
    path.mkdir(parents=True, exist_ok=True)
    return value, path


def write_latest_pointer(outline_root: Path, run_id: str) -> None:
    payload = {
        "run_id": run_id,
        "updated_at": utc_now_iso(),
        "path": f"pipeline_runs/{run_id}",
    }
    write_json(outline_root / PIPELINE_LATEST_FILE, payload)
    write_json(outline_root / PIPELINE_LATEST_ALIAS_FILE, payload)


def read_latest_run_id(outline_root: Path) -> Optional[str]:
    for name in (PIPELINE_LATEST_ALIAS_FILE, PIPELINE_LATEST_FILE):
        path = outline_root / name
        if not path.exists():
            continue
        try:
            payload = read_json(path)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        run_id = str(payload.get("run_id") or "").strip()
        if run_id:
            return run_id
    return None


def step_artifact_name(step_id: str, kind: str, attempt: Optional[int] = None) -> str:
    prefix = step_id
    if attempt is not None:
        return f"{prefix}_{kind}_{attempt}.json"
    return f"{prefix}_{kind}.json"


def load_history(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "outline_phase_history_v1",
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "steps": {},
        }
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {
            "schema_version": "outline_phase_history_v1",
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "steps": {},
        }
    if not isinstance(payload.get("steps"), dict):
        payload["steps"] = {}
    return payload


def write_history(path: Path, history: Dict[str, Any]) -> None:
    history["updated_at"] = utc_now_iso()
    write_json(path, history)


def load_report_path(outline_root: Path) -> Optional[Path]:
    latest_path = outline_root / PIPELINE_REPORT_LATEST_FILE
    if latest_path.exists():
        try:
            payload = read_json(latest_path)
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            raw = str(payload.get("path") or "").strip()
            if raw:
                candidate = outline_root / raw
                if candidate.exists():
                    return candidate
    run_id = read_latest_run_id(outline_root)
    if run_id:
        candidate = outline_root / "pipeline_runs" / run_id / PIPELINE_REPORT_FILE
        if candidate.exists():
            return candidate
    return None


def write_latest_report_pointer(outline_root: Path, run_id: str) -> Path:
    run_report = outline_root / "pipeline_runs" / run_id / PIPELINE_REPORT_FILE
    payload = {
        "run_id": run_id,
        "updated_at": utc_now_iso(),
        "path": relpath(outline_root, run_report),
    }
    target = outline_root / PIPELINE_REPORT_LATEST_FILE
    write_json(target, payload)
    return target
