from pathlib import Path
import json

from bookforge.branching import create_branch
from bookforge.contracts import ScopeSelector
from bookforge.query import get_integrity_verdict
from bookforge.section_workflow import initialize_section_workflow
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


def _write_run_artifacts(book_root: Path, run_id: str) -> None:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (outline_root / "pipeline_latest.json").write_text(json.dumps({"run_id": run_id}, ensure_ascii=True, indent=2), encoding="utf-8")
    (run_dir / "outline_spine_v1.json").write_text(json.dumps({"chapters": []}, ensure_ascii=True, indent=2), encoding="utf-8")
    (run_dir / "outline_sections_v1.json").write_text(
        json.dumps(
            {
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
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "outline_final_v1_1.json").write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "chapters": [
                    {
                        "chapter_id": 1,
                        "title": "Opening",
                        "sections": [{"section_id": 1, "title": "Arrival", "scenes": [{"scene_id": 1, "summary": "First scene."}]}],
                    }
                ],
                "characters": [{"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"}],
                "threads": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_query_integrity_reports_healthy_workspace(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, "run_001")
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    verdict = get_integrity_verdict(tmp_path, "my_book")

    assert verdict.status == "healthy"
    assert verdict.issues == []


def test_query_integrity_detects_chimera_risk_signals(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, "run_001")
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    _write_run_artifacts(book_root, "run_002")

    outline_path = book_root / "outline" / "outline.json"
    outline = json.loads(outline_path.read_text(encoding="utf-8"))
    outline["characters"].append({"character_id": "char_rhea", "name": "Rhea", "role": "protagonist"})
    outline["characters"].append({"character_id": "rhea_dup", "name": "Rhea", "role": "protagonist"})
    outline_path.write_text(json.dumps(outline, ensure_ascii=True, indent=2), encoding="utf-8")

    section_drafts = book_root / "outline" / "section_drafts"
    section_drafts.mkdir(parents=True, exist_ok=True)
    (section_drafts / "ch_001_sec_001_phase03.json").write_text("{}", encoding="utf-8")

    verdict = get_integrity_verdict(tmp_path, "my_book")

    assert verdict.status == "chimera_risk"
    codes = {issue.code for issue in verdict.issues}
    assert "source_run_mismatch" in codes
    assert "stale_section_drafts_present" in codes
    assert "duplicate_character_name" in codes


def test_query_integrity_detects_stale_parent_branch(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, "run_001")
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
        branch_id="rerun-sec1",
    )

    registry_path = book_root / "outline" / "snapshot_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["updated_at"] = "2030-01-01T00:00:00Z"
    registry_path.write_text(json.dumps(registry, ensure_ascii=True, indent=2), encoding="utf-8")

    verdict = get_integrity_verdict(tmp_path, "my_book")

    codes = {issue.code for issue in verdict.issues}
    assert "stale_parent" in codes


def test_query_integrity_detects_materialized_section_drift_as_overscoped_recovery(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, "run_001")
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    outline_path = book_root / "outline" / "outline.json"
    registry_path = book_root / "outline" / "snapshot_registry.json"
    outline = json.loads(outline_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    section = outline["chapters"][0]["sections"][0]
    section["status"] = "frozen"
    section["scenes"] = [{"scene_id": 1, "summary": "Drifted materialization."}]
    registry["chapters"][0]["sections"][0]["status"] = "frozen"
    registry["chapters"][0]["sections"][0]["scene_ref_start"] = "1:1"
    registry["chapters"][0]["sections"][0]["scene_ref_end"] = "1:1"

    outline_path.write_text(json.dumps(outline, ensure_ascii=True, indent=2), encoding="utf-8")
    registry_path.write_text(json.dumps(registry, ensure_ascii=True, indent=2), encoding="utf-8")

    verdict = get_integrity_verdict(tmp_path, "my_book")

    codes = {issue.code for issue in verdict.issues}
    assert "overscoped_recovery" in codes


def test_query_integrity_detects_emitted_main_node_drift_against_live_runtime(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, "run_001")
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    pause_path = book_root / "draft" / "context" / "run_paused.json"
    pause_path.parent.mkdir(parents=True, exist_ok=True)
    pause_path.write_text(
        json.dumps(
            {
                "phase": "write_scene",
                "chapter": 1,
                "scene": 1,
                "section": 1,
                "updated_at": "2030-01-01T00:00:00Z",
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    verdict = get_integrity_verdict(tmp_path, "my_book")

    codes = {issue.code for issue in verdict.issues}
    assert "workflow_family_contamination" in codes
