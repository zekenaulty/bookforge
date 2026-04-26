from __future__ import annotations

import json
from pathlib import Path

from bookforge.query import list_appearance_projection_views


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def test_appearance_projection_reports_missing_outline_character(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    _write_json(
        book_root / "outline" / "outline.json",
        {
            "characters": [
                {"character_id": "char_rhea", "name": "Rhea"},
            ]
        },
    )

    views = list_appearance_projection_views(tmp_path, "book", chapter_id=1, scene_id=1)

    assert len(views) == 1
    view = views[0]
    assert view.character_id == "char_rhea"
    assert view.character_name == "Rhea"
    assert view.appearance_status == "missing"
    assert view.artifact_status == "diagnostic"
    assert view.visible_scene_details == {}


def test_appearance_projection_reports_stale_pending_state(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    state_rel = "draft/context/characters/rhea.state.json"
    _write_json(
        book_root / "draft" / "context" / "characters" / "index.json",
        {"characters": [{"character_id": "char_rhea", "state_path": state_rel}]},
    )
    _write_json(
        book_root / state_rel,
        {
            "character_id": "char_rhea",
            "name": "Rhea",
            "appearance_current": {
                "summary": "Obsidian dust over a torn frontier coat.",
                "attire": [{"item_id": "coat", "label": "frontier coat"}],
            },
            "appearance_projection_pending": True,
            "last_touched": {"chapter": 1, "scene": 2},
        },
    )

    [view] = list_appearance_projection_views(
        tmp_path,
        "book",
        chapter_id=1,
        scene_id=3,
        character_id="char_rhea",
    )

    assert view.appearance_status == "stale"
    assert view.artifact_status == "provisional"
    assert view.staleness_reason == "appearance_projection_pending"
    assert view.visible_scene_details["summary"].startswith("Obsidian dust")
    assert view.source_artifacts == [state_rel]


def test_appearance_projection_reads_branch_snapshot(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    branch_root = book_root / "runtime" / "supervision" / "branches" / "branch-a" / "snapshot"
    state_rel = "draft/context/characters/rhea.state.json"
    _write_json(
        branch_root / "draft" / "context" / "characters" / "index.json",
        {"characters": [{"character_id": "char_rhea", "state_path": state_rel}]},
    )
    _write_json(
        branch_root / state_rel,
        {
            "character_id": "char_rhea",
            "name": "Branch Rhea",
            "appearance_current": {"summary": "Branch-local scar detail."},
            "appearance_artifact_status": "derived",
        },
    )

    [view] = list_appearance_projection_views(
        tmp_path,
        "book",
        branch_id="branch-a",
        chapter_id=2,
        scene_id=1,
    )

    assert view.selector.branch_id == "branch-a"
    assert view.character_name == "Branch Rhea"
    assert view.appearance_status == "current"
    assert view.visible_scene_details["summary"] == "Branch-local scar detail."
