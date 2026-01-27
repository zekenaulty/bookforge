from bookforge.runner import _extract_prose_and_patch


def test_extract_state_patch_marker() -> None:
    text = "PROSE:\nHello.\nSTATE_PATCH:\n{\"schema_version\": \"1.0\"}"
    prose, patch = _extract_prose_and_patch(text)
    assert prose == "Hello."
    assert patch["schema_version"] == "1.0"


def test_extract_state_patch_json_only() -> None:
    text = "STATE_PATCH:\n{\"schema_version\": \"1.0\"}"
    prose, patch = _extract_prose_and_patch(text)
    assert prose == ""
    assert patch["schema_version"] == "1.0"


def test_extract_fenced_json_no_ok() -> None:
    text = "PROSE:\nHello.\n```json\n{\"schema_version\": \"1.0\"}\n```"
    prose, patch = _extract_prose_and_patch(text)
    assert prose == "Hello."
    assert patch["schema_version"] == "1.0"


def test_extract_legacy_okpatch() -> None:
    text = "PROSE:\nHello.\nSTATE_OKPATCH:\n{\"schema_version\": \"1.0\"}"
    prose, patch = _extract_prose_and_patch(text)
    assert prose == "Hello."
    assert patch["schema_version"] == "1.0"
