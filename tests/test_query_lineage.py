from pathlib import Path
import json

from bookforge.contracts import ScopeSelector
from bookforge.query import get_frozen_chapter_projection, get_source_run, resolve_scope_selector
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


def _write_run_artifacts(book_root: Path) -> None:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / "run_001"
    run_dir.mkdir(parents=True, exist_ok=True)
    (outline_root / "pipeline_latest.json").write_text(json.dumps({"run_id": "run_001"}, ensure_ascii=True, indent=2), encoding="utf-8")
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
                "characters": [],
                "threads": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_query_lineage_prefers_immutable_run_anchor(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    source = get_source_run(tmp_path, "my_book")

    assert source is not None
    assert source["artifact_class"] == "immutable_lineage_anchor"
    assert source["run_id"] == "run_001"


def test_query_lineage_resolves_matching_scope_selector(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    node = resolve_scope_selector(
        tmp_path,
        ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline"),
    )

    assert node is not None
    assert node.workflow_family == "section_local_outline"
    assert node.branch_id == "main"


def test_query_lineage_returns_none_for_non_matching_scope(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    node = resolve_scope_selector(tmp_path, ScopeSelector(book_id="my_book", chapter=9))

    assert node is None


def test_query_lineage_reads_frozen_chapter_projection(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    chapter_path = book_root / "outline" / "chapters" / "ch_001.json"
    chapter_path.parent.mkdir(parents=True, exist_ok=True)
    chapter_path.write_text("{}", encoding="utf-8")

    projection = get_frozen_chapter_projection(tmp_path, "my_book", 1)

    assert projection is not None
    assert projection["artifact_class"] == "frozen_projection"
