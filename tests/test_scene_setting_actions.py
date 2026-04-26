from __future__ import annotations

import json
from pathlib import Path

from bookforge.contracts import TimelineNodeRef
from bookforge.execution import (
    build_draft_scene_setting_projection_request,
    build_extract_scene_setting_from_prose_request,
    draft_scene_setting_projection,
    extract_scene_setting_from_prose,
)
from bookforge.query import get_scene_setting_projection
from bookforge.supervision import paths as supervision_paths


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _write_current_node(book_root: Path, *, branch_id: str = "main") -> TimelineNodeRef:
    node = TimelineNodeRef(
        book_id=book_root.name,
        workflow_family="section_write",
        source_run_id="run_001",
        branch_id=branch_id,
        chapter=1,
        section=1,
        scene=1,
        phase_id="write_scene_prose",
        revision_id="rev001",
    )
    _write_json(supervision_paths.current_node_path(book_root, branch_id), node.to_dict())
    if branch_id == "main":
        _write_json(
            book_root / "outline" / "snapshot_registry.json",
            {
                "source_run_id": "run_001",
                "active_section": {"chapter_id": 1, "section_id": 1, "status": "frozen"},
            },
        )
    return node


def test_draft_scene_setting_projection_writes_provisional_artifact(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    _write_current_node(book_root)

    request = build_draft_scene_setting_projection_request(
        tmp_path,
        "book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        setting={
            "location_id": "loc_vault",
            "location_label": "Mercy Cache vault",
            "background_details": ["blue ledger light", "cracked glass lockers"],
            "sensory_anchors": ["cold brass", "static"],
        },
    )
    result = draft_scene_setting_projection(tmp_path, request)

    assert result.status == "success"
    assert result.produced_artifacts[0].artifact_key == "author_drafted_setting_projection"
    assert result.produced_artifacts[0].artifact_status == "provisional"
    view = get_scene_setting_projection(tmp_path, "book", chapter_id=1, scene_id=1, prefer_emitted=False)
    assert view.source_mode == "author_drafted"
    assert view.artifact_status == "provisional"
    assert view.location_label == "Mercy Cache vault"
    assert view.background_details == ["blue ledger light", "cracked glass lockers"]


def test_extract_scene_setting_from_prose_writes_derived_artifact(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    _write_current_node(book_root)
    prose_path = book_root / "draft" / "chapters" / "ch_001" / "scene_001.md"
    prose_path.parent.mkdir(parents=True, exist_ok=True)
    prose_path.write_text("Rhea crossed the ash market under buzzing debt signs.", encoding="utf-8")

    request = build_extract_scene_setting_from_prose_request(
        tmp_path,
        "book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
        extracted_setting={
            "location_label": "ash market",
            "background_details": ["buzzing debt signs"],
            "sensory_anchors": ["ash", "electric hum"],
        },
    )
    result = extract_scene_setting_from_prose(tmp_path, request)

    assert result.status == "success"
    assert result.produced_artifacts[0].artifact_key == "prose_extracted_setting_projection"
    assert result.produced_artifacts[0].artifact_status == "derived"
    assert result.produced_artifacts[0].details["source_prose_path"] == "draft/chapters/ch_001/scene_001.md"
    view = get_scene_setting_projection(tmp_path, "book", chapter_id=1, scene_id=1, prefer_emitted=False)
    assert view.source_mode == "prose_extracted"
    assert view.artifact_status == "derived"
    assert view.location_label == "ash market"


def test_extract_scene_setting_from_prose_refuses_without_prose(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    _write_current_node(book_root)

    request = build_extract_scene_setting_from_prose_request(
        tmp_path,
        "book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
    )
    result = extract_scene_setting_from_prose(tmp_path, request)

    assert result.status == "hard_fail"
    assert result.details["failure_code"] == "missing_scene_prose"
