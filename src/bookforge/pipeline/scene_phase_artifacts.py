from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json

from .phase_history import _load_phase_history


def _resolve_artifact_path(book_root: Path, raw_path: object) -> Optional[Path]:
    candidate = Path(str(raw_path or "").strip())
    if not str(candidate):
        return None
    if not candidate.is_absolute():
        candidate = book_root / candidate
    return candidate if candidate.exists() else None


def _phase_entry(phase_history: Dict[str, Any], phase: str) -> Dict[str, Any]:
    phases = phase_history.get("phases") if isinstance(phase_history, dict) else None
    if not isinstance(phases, dict):
        return {}
    entry = phases.get(phase)
    return entry if isinstance(entry, dict) else {}


def _phase_artifact(book_root: Path, phase_history: Dict[str, Any], phase: str, artifact_key: str) -> Optional[Path]:
    entry = _phase_entry(phase_history, phase)
    artifacts = entry.get("artifacts") if isinstance(entry.get("artifacts"), dict) else None
    if not isinstance(artifacts, dict):
        return None
    return _resolve_artifact_path(book_root, artifacts.get(artifact_key))


def _artifact_version(*paths: Optional[Path]) -> int:
    versions = [int(path.stat().st_mtime_ns) for path in paths if isinstance(path, Path) and path.exists()]
    return max(versions, default=0)


@dataclass(frozen=True, slots=True)
class ScenePhaseArtifactState:
    phase_history: Dict[str, Any]
    scene_card_path: Optional[Path]
    preflight_patch_path: Optional[Path]
    continuity_pack_path: Optional[Path]
    write_prose_path: Optional[Path]
    write_patch_path: Optional[Path]
    repair_prose_path: Optional[Path]
    repair_patch_path: Optional[Path]
    state_repair_patch_path: Optional[Path]
    lint_report_path: Optional[Path]
    write_version: int
    repair_version: int
    state_repair_version: int
    lint_version: int
    current_prose_phase: Optional[str]
    current_prose_path: Optional[Path]
    current_patch_path: Optional[Path]
    current_prose_version: int
    state_repair_current: bool
    lint_current: bool
    lint_status: Optional[str]

    @property
    def has_write_pair(self) -> bool:
        return self.write_prose_path is not None and self.write_patch_path is not None

    @property
    def has_repair_pair(self) -> bool:
        return self.repair_prose_path is not None and self.repair_patch_path is not None


def load_scene_phase_artifact_state(book_root: Path, chapter: int, scene: int) -> ScenePhaseArtifactState:
    phase_history = _load_phase_history(book_root, chapter, scene)

    scene_card_path = _phase_artifact(book_root, phase_history, "plan", "scene_card")
    preflight_patch_path = _phase_artifact(book_root, phase_history, "preflight", "patch")
    continuity_pack_path = _phase_artifact(book_root, phase_history, "continuity_pack", "pack")
    write_prose_path = _phase_artifact(book_root, phase_history, "write", "prose")
    write_patch_path = _phase_artifact(book_root, phase_history, "write", "patch")
    repair_prose_path = _phase_artifact(book_root, phase_history, "repair", "prose")
    repair_patch_path = _phase_artifact(book_root, phase_history, "repair", "patch")
    state_repair_patch_path = _phase_artifact(book_root, phase_history, "state_repair", "patch")
    lint_report_path = _phase_artifact(book_root, phase_history, "lint", "report")

    write_version = _artifact_version(write_prose_path, write_patch_path)
    repair_version = _artifact_version(repair_prose_path, repair_patch_path)
    state_repair_version = _artifact_version(state_repair_patch_path)
    lint_version = _artifact_version(lint_report_path)

    current_prose_phase: Optional[str] = None
    current_prose_path: Optional[Path] = None
    current_patch_path: Optional[Path] = None
    current_prose_version = 0
    if repair_prose_path is not None and repair_patch_path is not None and repair_version >= write_version and repair_version > 0:
        current_prose_phase = "repair"
        current_prose_path = repair_prose_path
        current_patch_path = repair_patch_path
        current_prose_version = repair_version
    elif write_prose_path is not None and write_patch_path is not None and write_version > 0:
        current_prose_phase = "write"
        current_prose_path = write_prose_path
        current_patch_path = write_patch_path
        current_prose_version = write_version

    state_repair_current = (
        state_repair_patch_path is not None
        and state_repair_version > 0
        and current_prose_version > 0
        and state_repair_version >= current_prose_version
    )
    lint_current = (
        lint_report_path is not None
        and lint_version > 0
        and state_repair_current
        and lint_version >= state_repair_version
    )

    lint_status = None
    if lint_current and lint_report_path is not None:
        try:
            payload = json.loads(lint_report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            status = str(payload.get("status") or "").strip()
            lint_status = status or None

    return ScenePhaseArtifactState(
        phase_history=phase_history,
        scene_card_path=scene_card_path,
        preflight_patch_path=preflight_patch_path,
        continuity_pack_path=continuity_pack_path,
        write_prose_path=write_prose_path,
        write_patch_path=write_patch_path,
        repair_prose_path=repair_prose_path,
        repair_patch_path=repair_patch_path,
        state_repair_patch_path=state_repair_patch_path,
        lint_report_path=lint_report_path,
        write_version=write_version,
        repair_version=repair_version,
        state_repair_version=state_repair_version,
        lint_version=lint_version,
        current_prose_phase=current_prose_phase,
        current_prose_path=current_prose_path,
        current_patch_path=current_patch_path,
        current_prose_version=current_prose_version,
        state_repair_current=state_repair_current,
        lint_current=lint_current,
        lint_status=lint_status,
    )
