import json
import urllib.error

import pytest

from bookforge.llm.utils import post_json


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_post_json_retries_on_timeout_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    outcomes = [TimeoutError("read timed out"), _FakeResponse({"ok": True})]
    sleeps: list[float] = []

    def _fake_urlopen(request, timeout):
        current = outcomes.pop(0)
        if isinstance(current, BaseException):
            raise current
        return current

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda sec: sleeps.append(sec))

    result = post_json(
        url="https://example.invalid",
        payload={"a": 1},
        headers={"Content-Type": "application/json"},
        timeout=600,
        max_retries=1,
        retry_backoff=0.5,
    )

    assert result == {"ok": True}
    assert sleeps == [0.5]


def test_post_json_raises_clear_timeout_on_exhausted_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_urlopen(request, timeout):
        raise urllib.error.URLError(TimeoutError("The read operation timed out"))

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda _: None)

    with pytest.raises(RuntimeError) as excinfo:
        post_json(
            url="https://example.invalid",
            payload={"a": 1},
            headers={"Content-Type": "application/json"},
            timeout=600,
            max_retries=1,
            retry_backoff=0.1,
        )

    message = str(excinfo.value)
    assert "Transport timeout calling" in message
    assert "timeout=600s" in message
    assert "The read operation timed out" in message
