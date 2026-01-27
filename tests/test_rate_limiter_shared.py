from bookforge.llm import factory


def test_shared_rate_limiter_reuse() -> None:
    factory._RATE_LIMITERS.clear()
    limiter_a = factory._shared_rate_limiter("gemini", "writer", 5)
    limiter_b = factory._shared_rate_limiter("gemini", "writer", 5)
    limiter_c = factory._shared_rate_limiter("gemini", "planner", 5)
    assert limiter_a is limiter_b
    assert limiter_a is not None
    assert limiter_c is not None
    assert limiter_a is not limiter_c
