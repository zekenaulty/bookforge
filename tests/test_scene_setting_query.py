from __future__ import annotations

import json
from pathlib import Path

from bookforge.query import get_scene_setting_projection


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def test_scene_setting_projection_prefers_author_drafted(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    setting_dir = book_root / "draft" / "context" / "settings" / "ch_001" / "scene_002"
    _write_json(
        setting_dir / "prose_extracted.setting.json",
        {
            "location_label": "old extracted hall",
            "background_details": ["draft dust"],
        },
    )
    _write_json(
        setting_dir / "author_drafted.setting.json",
        {
            "location_id": "loc_cache",
            "location_label": "Mercy Cache vault",
            "background_details": ["blue ledgers in cracked glass"],
            "sensory_anchors": ["static", "cold brass"],
            "continuity_constraints": ["the vault door is already open"],
        },
    )

    view = get_scene_setting_projection(tmp_path, "book", chapter_id=1, scene_id=2)

    assert view.setting_status == "available"
    assert view.artifact_status == "provisional"
    assert view.source_mode == "author_drafted"
    assert view.location_id == "loc_cache"
    assert view.location_label == "Mercy Cache vault"
    assert view.background_details == ["blue ledgers in cracked glass"]


def test_scene_setting_projection_marks_prose_extracted_as_derived(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    setting_dir = book_root / "draft" / "context" / "settings" / "ch_001" / "scene_002"
    _write_json(
        setting_dir / "prose_extracted.setting.json",
        {
            "location_label": "ash market",
            "background_details": ["hissing debt kiosks"],
        },
    )

    view = get_scene_setting_projection(tmp_path, "book", chapter_id=1, scene_id=2)

    assert view.setting_status == "available"
    assert view.artifact_status == "derived"
    assert view.source_mode == "prose_extracted"
    assert view.background_details == ["hissing debt kiosks"]


def test_scene_setting_projection_falls_back_to_outline(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    _write_json(
        book_root / "outline" / "outline.json",
        {
            "chapters": [
                {
                    "chapter_id": 1,
                    "sections": [
                        {
                            "section_id": 1,
                            "scenes": [
                                {
                                    "scene_id": 2,
                                    "location_start": "frontier platform",
                                    "transition_in_anchors": ["cold obsidian", "blue prompt"],
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    )

    view = get_scene_setting_projection(tmp_path, "book", chapter_id=1, scene_id=2)

    assert view.setting_status == "available"
    assert view.artifact_status == "derived"
    assert view.source_mode == "outline_derived"
    assert view.location_label == "frontier platform"
    assert view.sensory_anchors == ["cold obsidian", "blue prompt"]


def test_scene_setting_projection_reports_missing(tmp_path: Path) -> None:
    view = get_scene_setting_projection(tmp_path, "book", chapter_id=1, scene_id=2)

    assert view.setting_status == "missing"
    assert view.artifact_status == "diagnostic"
    assert view.source_mode == "missing"
    assert view.source_artifacts == []
