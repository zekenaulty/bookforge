from bookforge.runner import _apply_state_patch


def _base_state() -> dict:
    return {
        "schema_version": "1.0",
        "status": "DRAFT",
        "cursor": {"chapter": 1, "scene": 1},
        "world": {
            "time": {},
            "location": "",
            "cast_present": [],
            "open_threads": [],
            "recent_facts": [],
        },
        "budgets": {},
        "duplication_warnings_in_row": 0,
        "summary": {
            "last_scene": [],
            "chapter_so_far": [],
            "story_so_far": [],
            "key_facts_ring": [],
            "must_stay_true": [],
            "pending_story_rollups": [],
        },
    }


def test_story_so_far_pending_rollup_flush() -> None:
    state = _base_state()
    patch = {"summary_update": {"story_so_far_add": ["Event A"]}}
    _apply_state_patch(state, patch, chapter_end=False)
    assert state["summary"]["story_so_far"] == []
    assert state["summary"]["pending_story_rollups"] == ["Event A"]

    _apply_state_patch(state, {"summary_update": {}}, chapter_end=True)
    assert state["summary"]["story_so_far"] == ["Event A"]
    assert state["summary"]["pending_story_rollups"] == []
