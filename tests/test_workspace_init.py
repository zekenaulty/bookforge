from pathlib import Path
import json

from bookforge.workspace import init_book_workspace


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

    system_text = (book_dir / "prompts" / "system_v1.md").read_text(encoding="utf-8")
    assert "Author fragment." in system_text

    assert (book_dir / "prompts" / "templates" / "plan.md").exists()
    assert (book_dir / "prompts" / "registry.json").exists()
