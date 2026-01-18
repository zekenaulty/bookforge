from pathlib import Path
import json

from bookforge.llm.types import LLMResponse
from bookforge.outline import generate_outline
from bookforge.workspace import init_book_workspace


class DummyClient:
    def __init__(self, text: str) -> None:
        self._text = text
        self.messages = None

    def chat(self, messages, model, temperature=0.7, max_tokens=1024):
        self.messages = messages
        return LLMResponse(
            text=self._text,
            raw={"candidates": [{"finishReason": "STOP"}]},
            provider="dummy",
            model=model,
        )


def _basic_outline() -> dict:
    return {
        "schema_version": "1.1",
        "characters": [
            {
                "character_id": "CHAR_kaelen",
                "name": "Kaelen",
                "pronouns": "he/him",
                "role": "protagonist",
                "intro": {"chapter": 1, "scene": 1},
            }
        ],
        "threads": [
            {"thread_id": "THREAD_prophecy", "label": "The call", "status": "open"}
        ],
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Introduce the quest.",
                "chapter_role": "hook",
                "stakes_shift": "The summons arrives.",
                "bridge": {"from_prev": "", "to_next": "The hero accepts."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 2},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Spark the inciting incident.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "The call arrives.",
                                "type": "setup",
                                "outcome": "The hero receives the summons.",
                                "characters": ["CHAR_kaelen"],
                                "introduces": ["CHAR_kaelen"],
                                "threads": ["THREAD_prophecy"],
                            }
                        ],
                    }
                ],
            },
            {
                "chapter_id": 2,
                "title": "Crossing",
                "goal": "Commit to the journey.",
                "chapter_role": "journey",
                "stakes_shift": "The path narrows.",
                "bridge": {"from_prev": "The hero accepts.", "to_next": "The first trial looms."},
                "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 2},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Departure",
                        "intent": "Leave home behind.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "They depart.",
                                "type": "transition",
                                "outcome": "The journey begins.",
                                "characters": ["CHAR_kaelen"],
                                "threads": ["THREAD_prophecy"],
                            }
                        ],
                    }
                ],
            },
        ],
    }


def _broken_outline_extra_data_json() -> str:
    outline = _basic_outline()
    reordered = {
        "schema_version": outline["schema_version"],
        "chapters": outline["chapters"],
        "threads": outline["threads"],
        "characters": outline["characters"],
    }
    raw = json.dumps(reordered)
    parts = raw.rsplit('], "threads"', 1)
    raw = ']}, "threads"'.join(parts)
    return raw


def _broken_outline_json() -> str:
    outline = _basic_outline()
    reordered = {
        "schema_version": outline["schema_version"],
        "chapters": outline["chapters"],
        "threads": outline["threads"],
        "characters": outline["characters"],
    }
    raw = json.dumps(reordered)
    chapter_boundary = '}]}]}, {"chapter_id": 2'
    assert chapter_boundary in raw
    raw = raw.replace(chapter_boundary, '}]}], "chapter_id": 2', 1)
    threads_boundary = '}]}]}], "threads"'
    assert threads_boundary in raw
    raw = raw.replace(threads_boundary, '}]}], "threads"', 1)
    return raw


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

    client = DummyClient(json.dumps(_basic_outline()))
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


def test_generate_outline_includes_prompt_file(tmp_path: Path) -> None:
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

    prompt_path = tmp_path / "outline_prompt.txt"
    prompt_path.write_text("A ruined city hides the true heir.", encoding="utf-8")

    client = DummyClient(json.dumps(_basic_outline()))
    generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        prompt_file=prompt_path,
        client=client,
        model="dummy",
    )

    assert client.messages
    user_messages = [msg for msg in client.messages if msg.get("role") == "user"]
    assert user_messages
    assert "A ruined city hides the true heir." in user_messages[0].get("content", "")


def test_generate_outline_repairs_missing_chapter_boundaries(tmp_path: Path) -> None:
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

    client = DummyClient(_broken_outline_json())
    outline_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        client=client,
        model="dummy",
    )

    assert outline_path.exists()


def test_generate_outline_repairs_extra_data_before_threads(tmp_path: Path) -> None:
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

    client = DummyClient(_broken_outline_extra_data_json())
    outline_path = generate_outline(
        workspace=tmp_path,
        book_id="my_book",
        new_version=False,
        client=client,
        model="dummy",
    )

    assert outline_path.exists()

