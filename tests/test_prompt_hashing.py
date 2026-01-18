from bookforge.prompt.hashing import hash_prompt_parts, hash_text


def test_hash_text_is_stable():
    assert hash_text("abc") == hash_text("abc")


def test_hash_prompt_parts():
    hashes = hash_prompt_parts("a", "b", "c")
    assert hashes.stable_prefix != hashes.dynamic_payload
    assert hashes.dynamic_payload != hashes.assembled_prompt
