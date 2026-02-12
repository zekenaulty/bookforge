from pathlib import Path
import json

from bookforge.runner import _apply_state_patch, _rollup_chapter_summary


def _base_state() -> dict:
    return {
        "schema_version": "1.0",
        "status": "DRAFTING",
        "cursor": {"chapter": 1, "scene": 1},
        "world": {"time": {}, "location": "", "cast_present": [], "open_threads": [], "recent_facts": []},
        "summary": {
            "last_scene": [],
            "chapter_so_far": [],
            "story_so_far": [],
            "key_facts_ring": [],
            "must_stay_true": [],
        },
        "budgets": {},
        "duplication_warnings_in_row": 0,
    }


def test_apply_state_patch_summary_merge() -> None:
    state = _base_state()
    patch = {
        "summary_update": {
            "last_scene": ["Scene ends with the shard secured."],
            "key_events": ["Shard secured."],
            "must_stay_true": ["Shard remains physical."],
            "chapter_so_far_add": ["Kaelen binds the shard."],
            "story_so_far_add": ["Kaelen binds the shard."],
        }
    }
    updated = _apply_state_patch(state, patch, chapter_end=False)
    summary = updated["summary"]
    assert summary["last_scene"] == ["Scene ends with the shard secured."]
    assert summary["chapter_so_far"] == ["Kaelen binds the shard."]
    assert summary["story_so_far"] == []
    assert "Shard secured." in summary["key_facts_ring"]
    assert "Shard remains physical." in summary["key_facts_ring"]
    assert "Shard remains physical." in summary["must_stay_true"]



def test_apply_state_patch_summary_remove() -> None:
    state = _base_state()
    state["summary"]["must_stay_true"] = ["Artie HP is 0/0 (deceased)."]
    state["summary"]["key_facts_ring"] = ["Artie HP is 0/0 (deceased)."]
    patch = {
        "summary_update": {
            "must_stay_true": [
                "REMOVE: Artie HP is 0/0 (deceased).",
                "Artie HP is locked at 1/1.",
            ]
        }
    }
    updated = _apply_state_patch(state, patch, chapter_end=False)
    summary = updated["summary"]
    assert "Artie HP is 0/0 (deceased)." not in summary["must_stay_true"]
    assert "Artie HP is 0/0 (deceased)." not in summary["key_facts_ring"]
    assert "Artie HP is locked at 1/1." in summary["must_stay_true"]

def test_apply_state_patch_story_so_far_on_chapter_end() -> None:
    state = _base_state()
    patch = {"summary_update": {"story_so_far_add": ["Chapter 1 ends with escape."]}}
    updated = _apply_state_patch(state, patch, chapter_end=True)
    assert updated["summary"]["story_so_far"] == ["Chapter 1 ends with escape."]


def test_rollup_chapter_summary(tmp_path: Path) -> None:
    book_root = tmp_path / "book"
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    chapter_dir.mkdir(parents=True)
    meta1 = {
        "key_events": ["Shard secured.", "Varkas slain."],
        "must_stay_true": ["Shard remains physical."],
    }
    meta2 = {
        "key_events": ["Maps retrieved."],
        "must_stay_true": ["Kaelen injured shoulder."],
    }
    (chapter_dir / "scene_001.meta.json").write_text(json.dumps(meta1), encoding="utf-8")
    (chapter_dir / "scene_002.meta.json").write_text(json.dumps(meta2), encoding="utf-8")

    state = _base_state()
    state["summary"]["chapter_so_far"] = ["Temp bullet."]

    _rollup_chapter_summary(book_root, state, 1)

    assert state["summary"]["chapter_so_far"] == []
    assert "Shard secured." in state["summary"]["story_so_far"]
    assert "Kaelen injured shoulder." in state["summary"]["story_so_far"]

    summary_path = book_root / "draft" / "context" / "chapter_summaries" / "ch_001.json"
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["chapter"] == 1
    assert "Shard secured." in payload["key_events"]
    assert "Shard remains physical." in payload["must_stay_true"]



