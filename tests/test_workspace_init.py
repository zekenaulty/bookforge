from pathlib import Path
import json

from bookforge.workspace import init_book_workspace, reset_book_workspace, reset_book_workspace_detailed


def test_init_book_workspace(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    book_dir = init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 24},
        series_id=None,
    )

    book_path = book_dir / "book.json"
    state_path = book_dir / "state.json"
    assert book_path.exists()
    assert state_path.exists()

    book = json.loads(book_path.read_text(encoding="utf-8"))
    assert book["book_id"] == "my_book"
    assert book["author_ref"] == "eldrik-vale/v1"

    assert book["series_id"] == "my_book"
    assert book["series_ref"] == "series/my_book"

    series_root = tmp_path / "series" / "my_book"
    assert (series_root / "series.json").exists()
    series_manifest = json.loads((series_root / "series.json").read_text(encoding="utf-8"))
    assert "my_book" in series_manifest.get("books", [])

    system_text = (book_dir / "prompts" / "system_v1.md").read_text(encoding="utf-8")
    assert "Author fragment." in system_text

    assert (book_dir / "prompts" / "templates" / "plan.md").exists()
    assert (book_dir / "prompts" / "registry.json").exists()
    assert (book_dir / "draft" / "context" / "item_registry.json").exists()
    assert (book_dir / "draft" / "context" / "plot_devices.json").exists()
    assert (book_dir / "draft" / "context" / "items" / "index.json").exists()
    assert (book_dir / "draft" / "context" / "plot_devices" / "index.json").exists()
    assert (book_dir / "draft" / "context" / "durable_commits.json").exists()


def test_reset_book_workspace_resets_durable_context(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    book_dir = init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 24},
        series_id=None,
    )

    commits_path = book_dir / "draft" / "context" / "durable_commits.json"
    commits_path.write_text(json.dumps({"schema_version": "1.0", "applied_hashes": ["abc"]}), encoding="utf-8")
    history_path = book_dir / "draft" / "context" / "items" / "history" / "junk.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text("{}", encoding="utf-8")

    reset_book_workspace(tmp_path, "my_book")

    reset_commits = json.loads(commits_path.read_text(encoding="utf-8"))
    assert reset_commits.get("applied_hashes") == []
    assert not history_path.exists()

def test_reset_book_workspace_detailed_clears_book_scoped_logs(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 24},
        series_id=None,
    )

    logs_dir = tmp_path / "logs" / "llm"
    logs_dir.mkdir(parents=True, exist_ok=True)
    book_log = logs_dir / "my_book_ch001_sc001_write_scene_20260207_010101.json"
    other_log = logs_dir / "other_book_ch001_sc001_write_scene_20260207_010101.json"
    book_log.write_text("{}", encoding="utf-8")
    other_log.write_text("{}", encoding="utf-8")

    _, report = reset_book_workspace_detailed(tmp_path, "my_book", keep_logs=False, logs_scope="book")

    assert report["book_log_files_deleted"] == 1
    assert book_log.exists() is False
    assert other_log.exists() is True


def test_reset_book_workspace_detailed_clears_all_logs_when_requested(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 24},
        series_id=None,
    )

    logs_dir = tmp_path / "logs" / "llm"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "my_book_a.json").write_text("{}", encoding="utf-8")
    (logs_dir / "other_book_b.json").write_text("{}", encoding="utf-8")

    _, report = reset_book_workspace_detailed(tmp_path, "my_book", keep_logs=False, logs_scope="all")

    assert report["all_log_files_deleted"] == 2
    assert list(logs_dir.glob("*.json")) == []


def test_reset_book_workspace_detailed_keep_logs_preserves_workspace_logs(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 24},
        series_id=None,
    )

    logs_dir = tmp_path / "logs" / "llm"
    logs_dir.mkdir(parents=True, exist_ok=True)
    keep_log = logs_dir / "my_book_ch001_sc001_write_scene_20260207_010101.json"
    keep_log.write_text("{}", encoding="utf-8")

    _, report = reset_book_workspace_detailed(tmp_path, "my_book", keep_logs=True, logs_scope="book")

    assert report["book_log_files_deleted"] == 0
    assert report["all_log_files_deleted"] == 0
    assert keep_log.exists() is True
