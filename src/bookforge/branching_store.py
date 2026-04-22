from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Dict, Iterable, Optional

from bookforge import section_workflow as sw
from bookforge.contracts import (
    ASSEMBLY_BRANCH_PREFIX,
    BranchManifest,
    ScopeSelector,
    TimelineNodeRef,
)
from bookforge.supervision import paths as supervision_paths


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _revision_token(timestamp: Optional[str] = None) -> str:
    if timestamp is None:
        raw = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z").strip().lower()
    else:
        raw = str(timestamp).strip().lower()
    token = re.sub(r"[^0-9a-z]+", "", raw)
    return token[:32] or "observed"


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _book_root(workspace: Path, book_id: str) -> Path:
    return workspace / "books" / book_id


def _branch_snapshot_root(book_root: Path, branch_id: str) -> Path:
    return supervision_paths.branch_snapshot_root(book_root, branch_id)


def _branch_outline_root(book_root: Path, branch_id: str) -> Path:
    return supervision_paths.branch_snapshot_outline_root(book_root, branch_id)


def _generate_branch_id(prefix: str, seed_parts: Iterable[str]) -> str:
    seed = "|".join([str(part or "").strip() for part in seed_parts])
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    cleaned_prefix = re.sub(r"[^a-z0-9]+", "-", str(prefix or "branch").strip().lower()).strip("-") or "branch"
    return f"{cleaned_prefix}-{digest}"


def _copy_if_exists(source: Path, dest: Path) -> None:
    if not source.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def _copytree_if_exists(source: Path, dest: Path) -> None:
    if not source.exists():
        return
    shutil.copytree(source, dest, dirs_exist_ok=True)


def _copy_canonical_projection_to_branch(book_root: Path, branch_id: str) -> None:
    snapshot_root = _branch_snapshot_root(book_root, branch_id)
    outline_root = snapshot_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)
    _copy_if_exists(book_root / "state.json", snapshot_root / "state.json")
    for name in (
        "outline.json",
        sw.REGISTRY_FILENAME,
        sw.THIN_FILENAME,
        sw.TOC_FILENAME,
        sw.INDEX_FILENAME,
        sw.APPENDIX_FILENAME,
        "characters.json",
    ):
        _copy_if_exists(book_root / "outline" / name, outline_root / name)
    _copytree_if_exists(book_root / "outline" / "boundaries", outline_root / "boundaries")
    _copytree_if_exists(book_root / "outline" / "chapters", outline_root / "chapters")


def _load_manifest(book_root: Path, branch_id: str) -> BranchManifest:
    payload = _read_json(supervision_paths.branch_manifest_path(book_root, branch_id))
    return BranchManifest.from_dict(payload)


def _write_manifest(book_root: Path, manifest: BranchManifest) -> BranchManifest:
    _write_json(supervision_paths.branch_manifest_path(book_root, manifest.branch_id), manifest.to_dict())
    return manifest


def _write_branch_node(book_root: Path, node: TimelineNodeRef) -> TimelineNodeRef:
    _write_json(supervision_paths.current_node_path(book_root, node.branch_id), node.to_dict())
    return node


def _resolved_branch_scope(
    parent_node: TimelineNodeRef,
    selector: ScopeSelector,
) -> tuple[str, Optional[int], Optional[int], Optional[int], Optional[str], Optional[str]]:
    workflow_family = selector.workflow_family or parent_node.workflow_family
    chapter = selector.chapter if selector.chapter is not None else parent_node.chapter
    if selector.section is not None:
        section = selector.section
    elif selector.chapter is None or selector.chapter == parent_node.chapter:
        section = parent_node.section
    else:
        section = None
    if selector.scene is not None:
        scene = selector.scene
    elif selector.section is not None:
        scene = None
    elif selector.chapter is None or selector.chapter == parent_node.chapter:
        scene = parent_node.scene
    else:
        scene = None
    phase_id = selector.phase_id or parent_node.phase_id
    turn_id = selector.turn_id or parent_node.turn_id
    return workflow_family, chapter, section, scene, phase_id, turn_id


def _branch_selector(
    book_id: str,
    branch_id: str,
    parent_node: TimelineNodeRef,
    selector: ScopeSelector,
    fork_group_id: Optional[str],
) -> ScopeSelector:
    workflow_family, chapter, section, scene, phase_id, turn_id = _resolved_branch_scope(parent_node, selector)
    return ScopeSelector(
        book_id=book_id,
        branch_id=branch_id,
        fork_group_id=fork_group_id,
        workflow_family=workflow_family,
        chapter=chapter,
        section=section,
        scene=scene,
        phase_id=phase_id,
        turn_id=turn_id,
    )


def _branch_node(
    parent_node: TimelineNodeRef,
    selector: ScopeSelector,
    branch_id: str,
    fork_group_id: Optional[str],
    phase_id: Optional[str] = None,
) -> TimelineNodeRef:
    workflow_family, chapter, section, scene, resolved_phase_id, turn_id = _resolved_branch_scope(parent_node, selector)
    return TimelineNodeRef(
        book_id=parent_node.book_id,
        workflow_family=workflow_family,
        source_run_id=parent_node.source_run_id,
        branch_id=branch_id,
        fork_group_id=fork_group_id,
        chapter=chapter,
        section=section,
        scene=scene,
        phase_id=phase_id or resolved_phase_id,
        turn_id=turn_id,
        revision_id=_revision_token(),
    )


def _evolve_manifest(manifest: BranchManifest, **changes: object) -> BranchManifest:
    return replace(manifest, updated_at=str(changes.pop("updated_at", _now_iso())), **changes)


def load_branch_manifest(workspace: Path, book_id: str, branch_id: str) -> BranchManifest:
    return _load_manifest(_book_root(workspace, book_id), branch_id)
