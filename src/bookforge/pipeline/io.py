
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import shutil

from bookforge.characters import ensure_character_index, resolve_character_state_path
from bookforge.pipeline.state_apply import _now_iso, _summary_list


def _maybe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _last_touched_from_character_state(state: Dict[str, Any]) -> Tuple[int, int]:
    if isinstance(state.get("last_touched"), dict):
        chapter = _maybe_int(state.get("last_touched", {}).get("chapter"))
        scene = _maybe_int(state.get("last_touched", {}).get("scene"))
        if chapter is not None and scene is not None:
            return chapter, scene

    history = state.get("history")
    if isinstance(history, list):
        for entry in reversed(history):
            if not isinstance(entry, dict):
                continue
            chapter = _maybe_int(entry.get("chapter"))
            scene = _maybe_int(entry.get("scene"))
            if chapter is not None and scene is not None:
                return chapter, scene
    return 0, 0


def _snapshot_character_states_before_preflight(
    book_root: Path,
    scene_card: Dict[str, Any],
) -> List[Path]:
    cast_ids = scene_card.get("cast_present_ids", []) if isinstance(scene_card, dict) else []
    if not isinstance(cast_ids, list):
        cast_ids = []
    cast_ids = [str(item) for item in cast_ids if str(item).strip()]
    if not cast_ids:
        return []

    history_dir = book_root / "draft" / "context" / "characters" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    ensure_character_index(book_root)

    snapshots: List[Path] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    for char_id in cast_ids:
        state_path = resolve_character_state_path(book_root, char_id)
        if state_path is None or not state_path.exists():
            continue
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(loaded, dict):
            continue

        touched_ch, touched_sc = _last_touched_from_character_state(loaded)
        prefix = f"ch{touched_ch:03d}_sc{touched_sc:03d}_"
        candidate = history_dir / f"{prefix}{state_path.name}"
        if candidate.exists():
            candidate = history_dir / f"{prefix}{stamp}_{state_path.name}"
        shutil.copyfile(state_path, candidate)
        snapshots.append(candidate)
    return snapshots


def _log_scope(book_root: Path, scene_card: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scope: Dict[str, Any] = {"book_id": book_root.name}
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        if chapter is not None:
            scope["chapter"] = chapter
        scene = _maybe_int(scene_card.get("scene"))
        if scene is not None:
            scope["scene"] = scene
    return scope


def _write_scene_files(
    book_root: Path,
    chapter: int,
    scene: int,
    prose: str,
    scene_card: Dict[str, Any],
    patch: Dict[str, Any],
    lint_report: Dict[str, Any],
    write_attempts: int,
) -> Path:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    prose_path = chapter_dir / f"scene_{scene:03d}.md"
    if prose_path.exists():
        raise FileExistsError(f"Scene already exists: {prose_path}")
    prose_path.write_text(prose.strip() + "\n", encoding="utf-8")

    meta_path = chapter_dir / f"scene_{scene:03d}.meta.json"
    meta = dict(scene_card)
    meta["prose_path"] = prose_path.relative_to(book_root).as_posix()
    meta["state_patch"] = patch
    summary_update = patch.get("summary_update") if isinstance(patch, dict) else {}
    if not isinstance(summary_update, dict):
        summary_update = {}
    meta["scene_summary"] = _summary_list(summary_update.get("last_scene"))
    meta["key_events"] = _summary_list(summary_update.get("key_events"))
    meta["must_stay_true"] = _summary_list(summary_update.get("must_stay_true"))
    meta["threads_touched"] = _summary_list(summary_update.get("threads_touched"))
    meta["lint_report"] = lint_report
    meta["write_attempts"] = write_attempts
    meta["updated_at"] = _now_iso()
    meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")

    last_excerpt_path = book_root / "draft" / "context" / "last_excerpt.md"
    last_excerpt_path.write_text(prose.strip() + "\n", encoding="utf-8")

    return prose_path
