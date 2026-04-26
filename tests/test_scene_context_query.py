from __future__ import annotations

import json
from pathlib import Path

from bookforge.llm.signatures import append_signature_records
from bookforge.query import get_scene_context_projection


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def test_scene_context_projection_aggregates_projection_availability(tmp_path: Path) -> None:
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
            "appearance_current": {"summary": "Ash-dark coat."},
        },
    )
    _write_json(
        book_root / "draft" / "context" / "settings" / "ch_001" / "scene_002" / "author_drafted.setting.json",
        {
            "location_label": "Mercy Cache vault",
            "background_details": ["blue ledger light"],
        },
    )
    append_signature_records(
        tmp_path,
        [
            {
                "signature_id": "sig-plan",
                "book_id": "book",
                "workflow_family": "section_write",
                "phase_id": "write_scene",
                "turn_id": "T1",
                "chapter_id": 1,
                "scene_id": 2,
            }
        ],
    )

    view = get_scene_context_projection(
        tmp_path,
        "book",
        chapter_id=1,
        section_id=1,
        scene_id=2,
        phase_id="write_scene",
    )

    assert view.availability == {
        "appearance_available": True,
        "appearance_missing_count": 0,
        "appearance_stale_count": 0,
        "setting_available": True,
        "setting_source_mode": "author_drafted",
        "setting_artifact_status": "provisional",
        "thought_context_available": True,
        "thought_context_count": 1,
    }
    payload = view.to_dict()
    assert payload["appearance"][0]["character_id"] == "char_rhea"
    assert payload["setting"]["source_mode"] == "author_drafted"
    assert payload["thought_context"]["selected_signatures"][0]["signature_id"] == "sig-plan"
