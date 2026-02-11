from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

from bookforge.pipeline.state_apply import _now_iso


def _phase_history_dir(book_root: Path) -> Path:
    return book_root / "draft" / "context" / "phase_history"


def _phase_history_path(book_root: Path, chapter: int, scene: int) -> Path:
    return _phase_history_dir(book_root) / f"ch{chapter:03d}_sc{scene:03d}.json"


def _phase_artifact_dir(book_root: Path, chapter: int, scene: int) -> Path:
    return _phase_history_dir(book_root) / f"ch{chapter:03d}_sc{scene:03d}"


def _load_phase_history(book_root: Path, chapter: int, scene: int) -> Dict[str, Any]:
    path = _phase_history_path(book_root, chapter, scene)
    if not path.exists():
        return {"scene_id": f"ch{chapter:03d}_sc{scene:03d}", "phases": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"scene_id": f"ch{chapter:03d}_sc{scene:03d}", "phases": {}}
    if not isinstance(data, dict):
        return {"scene_id": f"ch{chapter:03d}_sc{scene:03d}", "phases": {}}
    if not isinstance(data.get("phases"), dict):
        data["phases"] = {}
    if not data.get("scene_id"):
        data["scene_id"] = f"ch{chapter:03d}_sc{scene:03d}"
    return data


def _write_phase_history(book_root: Path, chapter: int, scene: int, data: Dict[str, Any]) -> Path:
    path = _phase_history_path(book_root, chapter, scene)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _record_phase_success(
    book_root: Path,
    chapter: int,
    scene: int,
    phase: str,
    artifacts: Dict[str, str],
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    data = _load_phase_history(book_root, chapter, scene)
    phases = data.setdefault("phases", {})
    entry: Dict[str, Any] = {
        "status": "success",
        "timestamp": _now_iso(),
        "artifacts": artifacts,
    }
    if isinstance(extra, dict) and extra:
        entry.update(extra)
    phases[str(phase)] = entry
    _write_phase_history(book_root, chapter, scene, data)
    return data


def _write_phase_artifact(
    book_root: Path,
    chapter: int,
    scene: int,
    name: str,
    payload: Any,
    as_json: bool = True,
) -> Path:
    dest_dir = _phase_artifact_dir(book_root, chapter, scene)
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".json" if as_json else ".txt"
    path = dest_dir / f"{name}{suffix}"
    if as_json:
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    else:
        path.write_text(str(payload), encoding="utf-8")
    return path
