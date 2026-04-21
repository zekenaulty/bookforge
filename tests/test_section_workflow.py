from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.section_workflow import _find_phase03_section, initialize_section_workflow
from bookforge.workspace import init_book_workspace


def _init_book(tmp_path: Path) -> Path:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")
    return init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 1},
        series_id=None,
    )


def _write_run_artifacts(book_root: Path, run_id: str = "run_001") -> Path:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (outline_root / "pipeline_latest.json").write_text(
        json.dumps({"run_id": run_id}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    spine = {
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Start the story.",
                "chapter_role": "hook",
                "stakes_shift": "Pressure escalates.",
                "bridge": {"from_prev": "", "to_next": "Move into danger."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 3},
            }
        ]
    }
    sections = {
        "chapters": [
            {
                "chapter_id": 1,
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Get inside.",
                        "section_role": "setup",
                        "target_scene_count": 1,
                        "end_condition": "The door opens.",
                    },
                    {
                        "section_id": 2,
                        "title": "Breach",
                        "intent": "Push deeper.",
                        "section_role": "pressure",
                        "target_scene_count": 2,
                        "end_condition": "The threat is visible.",
                    },
                ],
            }
        ]
    }
    (run_dir / "outline_spine_v1.json").write_text(
        json.dumps(spine, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "outline_sections_v1.json").write_text(
        json.dumps(sections, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return run_dir


def test_find_phase03_section_falls_back_to_finalized_outline_payload(tmp_path: Path) -> None:
    run_dir = tmp_path / "pipeline_runs" / "run_001"
    run_dir.mkdir(parents=True)
    final_outline = {
        "schema_version": "1.1",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "scenes": [{"scene_id": 1, "summary": "First scene."}],
                    },
                    {
                        "section_id": 2,
                        "title": "Breach",
                        "scenes": [
                            {"scene_id": 2, "summary": "Second scene."},
                            {"scene_id": 3, "summary": "Third scene."},
                        ],
                    },
                ],
            }
        ],
        "characters": [{"character_id": "CHAR_lead", "name": "Lead"}],
        "threads": [{"thread_id": "THREAD_pressure", "label": "Pressure"}],
    }
    (run_dir / "outline_final_v1_1.json").write_text(
        json.dumps(final_outline, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    resolved = _find_phase03_section(run_dir, 1, 2)

    assert resolved["payload"]["characters"][0]["character_id"] == "CHAR_lead"
    assert resolved["section"]["section_id"] == 2
    assert [scene["scene_id"] for scene in resolved["section"]["scenes"]] == [2, 3]


def test_initialize_section_workflow_overwrite_clears_stale_outline_derivatives(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    outline_root = book_root / "outline"

    stale_section_draft = outline_root / "section_drafts" / "ch_001_sec_001_phase03.json"
    stale_section_draft.parent.mkdir(parents=True, exist_ok=True)
    stale_section_draft.write_text("{}", encoding="utf-8")

    stale_boundary = outline_root / "boundaries" / "ch_001_sec_001_boundary.json"
    stale_boundary.parent.mkdir(parents=True, exist_ok=True)
    stale_boundary.write_text("{}", encoding="utf-8")

    result = initialize_section_workflow(
        workspace=tmp_path,
        book_id="my_book",
        overwrite=True,
    )

    assert result["initialized"] is True
    assert not (outline_root / "section_drafts").exists()
    assert not (outline_root / "boundaries").exists()

    outline = json.loads((outline_root / "outline.json").read_text(encoding="utf-8"))
    chapter = outline["chapters"][0]
    assert [section["status"] for section in chapter["sections"]] == ["stub", "stub"]


def test_initialize_section_workflow_rejects_run_lineage_mismatch(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, run_id="run_001")
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    _write_run_artifacts(book_root, run_id="run_002")

    with pytest.raises(ValueError, match="forked from its source run"):
        initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=False)


def test_initialize_section_workflow_rejects_materialized_section_drift_against_source_run(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    run_dir = _write_run_artifacts(book_root, run_id="run_001")
    source_outline = {
        "schema_version": "1.1",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Get inside.",
                        "section_role": "setup",
                        "target_scene_count": 1,
                        "end_condition": "The door opens.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "Rhea arrives.",
                                "characters": ["rhea_mercer"],
                            }
                        ],
                    },
                    {
                        "section_id": 2,
                        "title": "Breach",
                        "intent": "Push deeper.",
                        "section_role": "pressure",
                        "target_scene_count": 2,
                        "end_condition": "The threat is visible.",
                        "scenes": [
                            {
                                "scene_id": 2,
                                "summary": "The door opens.",
                                "characters": ["rhea_mercer"],
                            }
                        ],
                    },
                ],
            }
        ],
        "characters": [{"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"}],
        "threads": [],
    }
    (run_dir / "outline_final_v1_1.json").write_text(
        json.dumps(source_outline, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    outline_root = book_root / "outline"
    workflow_outline = json.loads((outline_root / "outline.json").read_text(encoding="utf-8"))
    workflow_registry = json.loads((outline_root / "snapshot_registry.json").read_text(encoding="utf-8"))

    workflow_outline["characters"] = [
        {"character_id": "char_rhea", "name": "Rhea", "role": "protagonist"},
        {"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"},
    ]
    chapter = workflow_outline["chapters"][0]
    section = chapter["sections"][0]
    section["status"] = "locked"
    section["scenes"] = [
        {
            "scene_id": 1,
            "summary": "Old lineage scene.",
            "characters": ["char_rhea"],
        }
    ]
    workflow_registry["chapters"][0]["sections"][0]["status"] = "locked"
    workflow_registry["chapters"][0]["sections"][0]["scene_ref_start"] = "1:1"
    workflow_registry["chapters"][0]["sections"][0]["scene_ref_end"] = "1:1"

    (outline_root / "outline.json").write_text(
        json.dumps(workflow_outline, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (outline_root / "snapshot_registry.json").write_text(
        json.dumps(workflow_registry, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="forked from its source run"):
        initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=False)
