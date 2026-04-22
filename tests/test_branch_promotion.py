from __future__ import annotations

import json
from pathlib import Path

from bookforge.branching import create_branch, load_branch_manifest, promote_branch_to_main, rerun_freeze_section_on_branch
from bookforge.contracts import ScopeSelector
from bookforge.section_workflow import initialize_section_workflow
from bookforge.supervision import paths as supervision_paths
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


def _write_run_artifacts(book_root: Path, run_id: str = "run_001") -> None:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (outline_root / "pipeline_latest.json").write_text(json.dumps({"run_id": run_id}, ensure_ascii=True, indent=2), encoding="utf-8")
    (run_dir / "outline_spine_v1.json").write_text(
        json.dumps({"chapters": [{"chapter_id": 1, "title": "Opening", "goal": "Start the story.", "chapter_role": "hook", "stakes_shift": "Pressure escalates.", "bridge": {"from_prev": "", "to_next": "Move into danger."}, "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1}}]}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "outline_sections_v1.json").write_text(
        json.dumps({"chapters": [{"chapter_id": 1, "sections": [{"section_id": 1, "title": "Arrival", "intent": "Get inside.", "section_role": "setup", "target_scene_count": 1, "end_condition": "The door opens."}]}]}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "outline_final_v1_1.json").write_text(
        json.dumps({"schema_version": "1.1", "chapters": [{"chapter_id": 1, "title": "Opening", "sections": [{"section_id": 1, "title": "Arrival", "intent": "Get inside.", "end_condition": "The door opens.", "scenes": [{"scene_id": 1, "summary": "First scene.", "handoff_mode": "terminal", "transition_out_anchors": ["door"], "threads": []}]}]}], "characters": [{"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"}], "threads": []}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_last_jsonl(path: Path) -> dict:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    return json.loads(lines[-1])


def test_promote_branch_to_main_copies_snapshot_back_to_canonical(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )
    rerun_freeze_section_on_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
    )

    manifest = promote_branch_to_main(tmp_path, "my_book", "rerun-sec1")
    canonical_outline = _read_json(book_root / "outline" / "outline.json")
    main_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root))

    assert manifest.lifecycle_state == "promoted"
    assert canonical_outline["chapters"][0]["sections"][0]["status"] == "frozen"
    assert main_execution_result["action"] == "promote_branch_to_main"
    assert main_execution_result["status"] == "success"
    assert main_execution_result["details"]["source_branch_id"] == "rerun-sec1"
    assert main_execution_result["details"]["canonical_change_status"] == "canonical"
