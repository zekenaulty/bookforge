from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import re

from bookforge.util.json_extract import extract_json


def _extract_json(text: str) -> Dict[str, Any]:
    data = extract_json(text, label="Response")
    if not isinstance(data, dict):
        raise ValueError("Response JSON must be an object.")
    return data


def _strip_compliance_block(text: str) -> str:
    if not re.match(r"^COMPLIANCE\s*:", text.strip(), flags=re.IGNORECASE):
        return text
    match = re.search(r"\bPROSE\s*:\s*", text, re.IGNORECASE)
    if match:
        return text[match.end():].strip()
    parts = re.split(r"\n\s*\n", text, maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return ""


def _extract_prose_and_patch(text: str) -> Tuple[str, Dict[str, Any]]:
    match = None
    for candidate in re.finditer(r"STATE\s*_(?:OKPATCH|PATCH)\s*:\s*", text, re.IGNORECASE):
        match = candidate
    if not match:
        return _extract_prose_and_patch_fallback(text)
    prose_block = text[:match.start()].strip()
    patch_block = text[match.end():].strip()
    prose_block = _strip_compliance_block(prose_block)
    prose = re.sub(r"^PROSE\s*:\s*", "", prose_block, flags=re.IGNORECASE).strip()
    if not prose:
        prose = prose_block.strip()
    patch = _extract_json(patch_block)
    if "schema_version" not in patch:
        patch["schema_version"] = "1.0"
    return prose, patch


def _extract_prose_and_patch_fallback(text: str) -> Tuple[str, Dict[str, Any]]:
    fence_matches = list(re.finditer(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE))
    if fence_matches:
        match = fence_matches[-1]
        patch_block = match.group(1).strip()
        prose_block = text[:match.start()].strip()
        prose_block = _strip_compliance_block(prose_block)
        prose = re.sub(r"^PROSE\s*:\s*", "", prose_block, flags=re.IGNORECASE).strip()
        if not prose:
            prose = prose_block.strip()
        patch = _extract_json(patch_block)
        if "schema_version" not in patch:
            patch["schema_version"] = "1.0"
        return prose, patch

    match = re.search(r"(\{[\s\S]*\})\s*$", text)
    if match:
        patch_block = match.group(1).strip()
        prose_block = text[:match.start()].strip()
        prose_block = _strip_compliance_block(prose_block)
        prose = re.sub(r"^PROSE\s*:\s*", "", prose_block, flags=re.IGNORECASE).strip()
        if not prose:
            prose = prose_block.strip()
        patch = _extract_json(patch_block)
        if "schema_version" not in patch:
            patch["schema_version"] = "1.0"
        return prose, patch

    raise ValueError(
        "Missing STATE_PATCH/STATE_OKPATCH block in response (searched for explicit marker, fenced JSON, or trailing JSON)."
    )


def _extract_authoritative_surfaces(prose: str) -> List[Dict[str, Any]]:
    surfaces: List[Dict[str, Any]] = []
    for line_no, raw_line in enumerate(str(prose).splitlines(), start=1):
        if not raw_line.strip():
            continue
        line = raw_line.lstrip()
        if not line.startswith("["):
            continue

        pos = 0
        tokens: List[str] = []
        while True:
            while pos < len(line) and line[pos].isspace():
                pos += 1
            if pos >= len(line) or line[pos] != "[":
                break
            end = line.find("]", pos)
            if end == -1:
                break
            tokens.append(line[pos:end + 1].strip())
            pos = end + 1

        tail = line[pos:].strip()
        if tail and not re.fullmatch(r'[\.!?;,:"\'\)\]]*', tail):
            continue

        for text in tokens:
            kind = "ui_block"
            if re.match(r"^\[[^\]:]{1,80}:\s*[-+0-9]", text):
                kind = "ui_stat"
            elif text.lower().startswith("[system"):
                kind = "system_notification"
            elif text.lower().startswith("[warning"):
                kind = "system_notification"
            surfaces.append({"line": line_no, "kind": kind, "text": text})
    return surfaces


def _extract_ui_stat_lines(
    prose: str,
    authoritative_surfaces: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    lines: List[Dict[str, Any]] = []
    source_texts: List[str] = []

    if authoritative_surfaces is not None:
        for surface in authoritative_surfaces:
            if not isinstance(surface, dict):
                continue
            text = surface.get("text")
            if isinstance(text, str) and text.strip():
                source_texts.append(text)
    else:
        source_texts = [str(prose)]

    number = r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
    pattern = re.compile(r"\[([^\]:]{1,80}):\s*(" + number + r")(?:\s*/\s*(" + number + r"))?\s*%?\]")

    def _parse_num(value: str) -> Any:
        if value is None:
            return None
        cleaned = value.replace(",", "").strip()
        if not cleaned:
            return None
        return float(cleaned) if "." in cleaned else int(cleaned)

    for chunk in source_texts:
        for match in pattern.finditer(chunk):
            key = match.group(1).strip()
            current_raw = match.group(2)
            max_raw = match.group(3)
            current = _parse_num(current_raw)
            maximum = _parse_num(max_raw) if max_raw is not None else None
            if current is None:
                continue
            lines.append({"key": key, "current": current, "max": maximum})
    return lines


def _strip_dialogue(text: str) -> str:
    if not text:
        return ""
    output: List[str] = []
    in_double = False
    in_single = False
    idx = 0
    while idx < len(text):
        ch = text[idx]
        if ch in {'"', "\u201c", "\u201d"}:
            in_double = not in_double
            idx += 1
            continue
        if ch == "'" and not in_double:
            if in_single:
                in_single = False
                idx += 1
                continue
            prev = text[idx - 1] if idx > 0 else ""
            nxt = text[idx + 1] if idx + 1 < len(text) else ""
            if (prev.isspace() or prev in "([{\"") and nxt.isalpha():
                rest = text[idx + 1:]
                end = rest.find("'")
                newline = rest.find("\n")
                if end != -1 and (newline == -1 or end < newline):
                    in_single = True
                    idx += 1
                    continue
        if in_double or in_single:
            if ch == "\n":
                output.append(ch)
            idx += 1
            continue
        output.append(ch)
        idx += 1
    return "".join(output)


def _find_first_match_evidence(pattern: str, text: str) -> Optional[Dict[str, Any]]:
    match = re.search(pattern, text)
    if not match:
        return None
    start = match.start()
    line_no = text.count("\n", 0, start) + 1
    lines = text.splitlines()
    line_text = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ""
    return {"line": line_no, "excerpt": line_text}
