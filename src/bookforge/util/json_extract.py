from __future__ import annotations

from typing import Any, Callable, Optional
import ast
import json
import re

RepairFn = Callable[[str], str]


def _clean_json_payload(payload: str) -> str:
    cleaned = payload.strip()
    cleaned = cleaned.replace("\ufeff", "")
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"')
    cleaned = cleaned.replace("\u2018", "'").replace("\u2019", "'")
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _last_json_block(text: str) -> Optional[str]:
    end = text.rfind("}")
    if end == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for idx in range(end, -1, -1):
        ch = text[idx]
        if in_str:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "}":
            depth += 1
            continue
        if ch == "{":
            depth -= 1
            if depth == 0:
                return text[idx:end + 1]
    return None


def _candidate_payload(text: str) -> Optional[str]:
    matches = list(re.finditer(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE))
    if matches:
        return matches[-1].group(1)
    start = text.find("{")
    if start == -1:
        return None
    end = text.rfind("}")
    if end == -1:
        return text[start:]
    if end <= start:
        return None
    return text[start:end + 1]


def extract_json(
    text: str,
    *,
    label: str = "Response",
    repair_fn: Optional[RepairFn] = None,
    require_object: bool = True,
) -> Any:
    payload = _candidate_payload(text)
    if not payload:
        raise ValueError("No JSON object found in response.")
    payload = payload.strip()

    def _parse(raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            cleaned = _clean_json_payload(raw)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                repaired = None
                if repair_fn:
                    repaired = repair_fn(cleaned)
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        pass
                try:
                    return ast.literal_eval(repaired or cleaned)
                except (ValueError, SyntaxError) as exc:
                    raise ValueError("Invalid JSON in response.") from exc

    data = _parse(payload)
    if require_object and not isinstance(data, dict):
        raise ValueError(f"{label} JSON must be an object.")
    return data
