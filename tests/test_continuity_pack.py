import json
import pytest

from bookforge.memory.continuity import ContinuityPack, parse_continuity_pack


def test_continuity_pack_roundtrip():
    payload = {
        "scene_end_anchor": "Anchor.",
        "constraints": ["No recap"],
        "open_threads": ["THREAD_1"],
        "cast_present": ["CHAR_1"],
        "location": "LOC_1",
        "next_action": "Proceed",
    }
    text = json.dumps(payload)
    pack = parse_continuity_pack(text)
    assert isinstance(pack, ContinuityPack)
    assert pack.to_dict() == payload


def test_continuity_pack_missing_fields():
    with pytest.raises(ValueError):
        parse_continuity_pack("{}")
