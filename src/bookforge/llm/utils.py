from __future__ import annotations

from typing import Iterable, List, Tuple
import json
import urllib.request
import urllib.error

from .types import Message


def split_system_messages(messages: Iterable[Message]) -> Tuple[str, List[Message]]:
    system_parts: List[str] = []
    non_system: List[Message] = []
    for msg in messages:
        role = msg.get("role", "")
        if role == "system":
            system_parts.append(msg.get("content", ""))
        else:
            non_system.append(msg)
    return "\n\n".join([part for part in system_parts if part.strip()]), non_system


def post_json(url: str, payload: dict, headers: dict, timeout: int = 30) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response from {url}: {body}") from exc
