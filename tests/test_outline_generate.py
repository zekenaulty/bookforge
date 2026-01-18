from pathlib import Path
import json

from bookforge.llm.types import LLMResponse
from bookforge.outline import generate_outline
from bookforge.workspace import init_book_workspace


class DummyClient:
    def __init__(self, text: str) -> None:
        self._text = text

    def chat(self, messages, model, temperature=0.7, max_tokens=1024):
        return LLMResponse(
            text=self._text,
            raw={"candidates": [{"finishReason": "STOP"}]},
            provider="dummy",
            model=model,
        )


def test_generate_outline_writes_files(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 2},
        series_id=None,
    )

    outline = {
        "schema_version": "1.0",
        "characters": [
            {"character_id": "CHAR_kaelen", "name": "Kaelen", "pronouns": "he/him", "role": "protagonist", "intro": {"chapter": 1, "beat": 1}}
        ],
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Introduce the quest.",
                "beats": [{"beat_id": 1, "summary": "The call arrives."}],
            },
            {
                "chapter_id": 2,
                "title": "Crossing",
                "goal": "Commit to the journey.",
                "beats": [{"beat_id": 1, "summary": "They depart."}],
            },
        ],
    }

    client = DummyClient(json.dumps(outline))
    outline_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        client=client,
        model="dummy",
    )

    assert outline_path.exists()
    assert (outline_path.parent / "chapters" / "ch_001.json").exists()
    assert (outline_path.parent / "chapters" / "ch_002.json").exists()
    assert (outline_path.parent / "characters.json").exists()
