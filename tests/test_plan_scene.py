from pathlib import Path
import json

from bookforge.llm.types import LLMResponse
from bookforge.phases.plan import plan_scene
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


def test_plan_scene_writes_scene_card(tmp_path: Path) -> None:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")

    book_dir = init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 1},
        series_id=None,
    )

    outline = {
        "schema_version": "1.0",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "goal": "Introduce the quest.",
                "beats": [{"beat_id": 1, "summary": "The call arrives."}],
            }
        ],
    }

    outline_path = book_dir / "outline" / "outline.json"
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    outline_path.write_text(json.dumps(outline, ensure_ascii=True, indent=2), encoding="utf-8")

    scene_card = {
        "schema_version": "1.0",
        "scene_id": "SC_001_001",
        "chapter": 1,
        "scene": 1,
        "beat_target": "The call arrives.",
        "goal": "Force a decision.",
        "conflict": "A warning complicates the offer.",
        "required_callbacks": [],
        "constraints": [],
        "end_condition": "The hero commits.",
    }

    client = DummyClient(json.dumps(scene_card))
    scene_path = plan_scene(
        workspace=tmp_path,
        book_id="my_book",
        client=client,
        model="dummy",
    )

    assert scene_path.exists()
    state = json.loads((book_dir / "state.json").read_text(encoding="utf-8"))
    assert state["cursor"]["chapter"] == 1
    assert state["cursor"]["scene"] == 1
    assert state.get("plan", {}).get("scene_card")
