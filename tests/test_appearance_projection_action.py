from __future__ import annotations

import json
from pathlib import Path

from bookforge.contracts import ScopeSelector, TimelineNodeRef
from bookforge.execution import (
    build_refresh_character_appearance_projection_request,
    refresh_character_appearance_projection,
)
from bookforge.query import list_execution_options
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
    path = supervision_paths.current_node_path(book_root, branch_id)
    _write_json(path, node.to_dict())
    if branch_id == "main":
        _write_json(
            book_root / "outline" / "snapshot_registry.json",
            {
                "source_run_id": "run_001",
                "updated_at": "2026-04-20T00:00:00Z",
                "active_section": {
                    "chapter_id": 1,
                    "section_id": 1,
                    "status": "frozen",
                },
            },
        )
        _write_json(
            book_root / "state.json",
            {
                "cursor": {"chapter": 1, "scene": 1},
                "updated_at": "2026-04-20T00:00:01Z",
            },
        )
        _write_json(
            book_root / "draft" / "context" / "run_paused.json",
            {
                "phase": "write_scene",
                "chapter": 1,
                "section": 1,
                "scene": 1,
                "created_at": "2026-04-20T00:00:02Z",
            },
        )
    return node


def test_refresh_character_appearance_projection_action_writes_derived_receipt(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    state_rel = "draft/context/characters/rhea.state.json"
    _write_current_node(book_root)
    _write_json(
        book_root / "draft" / "context" / "characters" / "index.json",
        {"characters": [{"character_id": "char_rhea", "state_path": state_rel}]},
    )
    _write_json(
        book_root / state_rel,
        {
            "character_id": "char_rhea",
            "name": "Rhea",
            "appearance_current": {"summary": "Ash on her coat."},
        },
    )

    request = build_refresh_character_appearance_projection_request(
        tmp_path,
        "book",
        chapter_id=1,
        section_id=1,
        scene_id=1,
    )
    result = refresh_character_appearance_projection(tmp_path, request)

    assert result.status == "success"
    assert result.produced_artifacts[0].artifact_key == "appearance_projection"
    assert result.produced_artifacts[0].artifact_status == "derived"
    projection_path = book_root / result.produced_artifacts[0].path
    payload = json.loads(projection_path.read_text(encoding="utf-8"))
    assert payload["artifact_status"] == "derived"
    assert payload["characters"][0]["character_id"] == "char_rhea"
    assert payload["limitations"] == [
        "derived from current character state and outline metadata",
        "does not mutate canonical character truth",
    ]
    unchanged_state = json.loads((book_root / state_rel).read_text(encoding="utf-8"))
    assert unchanged_state["appearance_current"]["summary"] == "Ash on her coat."


def test_refresh_character_appearance_projection_is_discoverable(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "book"
    _write_current_node(book_root)

    options = list_execution_options(
        tmp_path,
        ScopeSelector(
            book_id="book",
            branch_id="main",
            workflow_family="section_write",
            chapter=1,
            section=1,
            scene=1,
        ),
        prefer_emitted=False,
    )

    option = next(item for item in options if item.action == "refresh_character_appearance_projection")
    assert option.allowed is True
    assert option.mutates_canonical_state is False
    assert option.details["mutation_scope"] == "derived_projection"
