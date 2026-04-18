from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import re


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[\"'A-Z])")
_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")
_PRESENT_TENSE_MARKERS = (
    "is",
    "are",
    "looks",
    "look",
    "stares",
    "stare",
    "rolls",
    "roll",
    "shoves",
    "shove",
    "floats",
    "float",
    "finalizes",
    "finalize",
    "spawns",
    "spawn",
    "realizes",
    "realize",
    "checks",
    "check",
    "hits",
    "hit",
    "prepares",
    "prepare",
    "clutches",
    "clutch",
)
_PAST_TENSE_MARKERS = (
    "was",
    "were",
    "had",
    "looked",
    "stared",
    "rolled",
    "shoved",
    "floated",
    "finalized",
    "spawned",
    "realized",
    "checked",
    "prepared",
    "clutched",
    "felt",
    "said",
    "walked",
    "hit",
)
_PRESENT_TO_PAST = {
    "is": "was",
    "are": "were",
    "looks": "looked",
    "look": "looked",
    "stares": "stared",
    "stare": "stared",
    "rolls": "rolled",
    "roll": "rolled",
    "shoves": "shoved",
    "shove": "shoved",
    "floats": "floated",
    "float": "floated",
    "finalizes": "finalized",
    "finalize": "finalized",
    "spawns": "spawned",
    "spawn": "spawned",
    "realizes": "realized",
    "realize": "realized",
    "checks": "checked",
    "check": "checked",
    "prepares": "prepared",
    "prepare": "prepared",
    "clutches": "clutched",
    "clutch": "clutched",
}
_SCAFFOLD_PATTERNS = (
    re.compile(r"\bready to\b", re.IGNORECASE),
    re.compile(r"\bpreparing to\b", re.IGNORECASE),
    re.compile(r"\bspawns? in\b", re.IGNORECASE),
    re.compile(r"\bfinalizes? the\b", re.IGNORECASE),
    re.compile(r"\bstares? at the\b", re.IGNORECASE),
    re.compile(r"\bfloats? in the\b", re.IGNORECASE),
    re.compile(r"\blooks? for an escape\b", re.IGNORECASE),
)
_TRACKED_ANCHOR_PHRASES = (
    "employee id badge",
    "leather wallet",
    "wallet",
    "badge",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _normalize_for_compare(text: str) -> str:
    lowered = _NORMALIZE_RE.sub(" ", str(text or "").lower())
    return " ".join(lowered.split())


def _sentence_similarity(left: str, right: str) -> float:
    left_norm = _normalize_for_compare(left)
    right_norm = _normalize_for_compare(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    left_tokens = set(left_norm.split())
    right_tokens = set(right_norm.split())
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = left_tokens & right_tokens
    if len(overlap) < 3:
        return 0.0
    union = left_tokens | right_tokens
    return len(overlap) / max(len(union), 1)


def _split_paragraphs(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", str(text or "").strip()) if part.strip()]


def _split_sentences(text: str) -> List[str]:
    stripped = str(text or "").strip()
    if not stripped:
        return []
    parts = _SENTENCE_SPLIT_RE.split(stripped)
    return [part.strip() for part in parts if part.strip()]


def _join_sentences(sentences: List[str]) -> str:
    return " ".join(part.strip() for part in sentences if part and part.strip()).strip()


def _leading_sentence(text: str) -> str:
    sentences = _split_sentences(text)
    return sentences[0] if sentences else ""


def _trailing_sentence(text: str) -> str:
    sentences = _split_sentences(text)
    return sentences[-1] if sentences else ""


def _count_markers(text: str, markers: Tuple[str, ...]) -> int:
    tokens = _normalize_for_compare(text).split()
    return sum(1 for token in tokens if token in markers)


def _is_scaffold_like_sentence(sentence: str) -> bool:
    stripped = str(sentence or "").strip()
    if not stripped or '"' in stripped:
        return False
    word_count = len(_normalize_for_compare(stripped).split())
    if word_count < 4 or word_count > 28:
        return False
    if not re.match(r"^[A-Z][A-Za-z0-9_' -]+", stripped):
        return False
    for pattern in _SCAFFOLD_PATTERNS:
        if pattern.search(stripped):
            return True
    lowered = stripped.lower()
    return any(f" {marker} " in f" {lowered} " for marker in _PRESENT_TENSE_MARKERS)


def _convert_present_sentence_to_past(sentence: str) -> str:
    updated = str(sentence or "")
    for present, past in _PRESENT_TO_PAST.items():
        updated = re.sub(rf"\b{re.escape(present)}\b", past, updated, flags=re.IGNORECASE)
    return updated


def _find_chapter_outline(outline: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    for entry in chapters:
        if not isinstance(entry, dict):
            continue
        try:
            current = int(entry.get("chapter_id"))
        except (TypeError, ValueError):
            continue
        if current == chapter_num:
            return entry
    return {}


def _section_title(section: Dict[str, Any], index: int) -> str:
    title = str(section.get("title") or "").strip()
    if title:
        return title
    return f"Section {index}"


def _scene_id_from_obj(scene_obj: Dict[str, Any], fallback: int) -> int:
    for key in ("scene_id", "beat_id", "id"):
        try:
            return int(scene_obj.get(key))
        except (TypeError, ValueError):
            continue
    return fallback


def _chapter_scene_blocks(book_root: Path, outline: Dict[str, Any], chapter_num: int) -> List[Dict[str, Any]]:
    chapter = _find_chapter_outline(outline, chapter_num)
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}"
    sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
    if not sections and isinstance(chapter, dict):
        sections = [{"section_id": 1, "title": "", "scenes": chapter.get("scenes") or chapter.get("beats") or []}]

    blocks: List[Dict[str, Any]] = []
    for section_index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            continue
        try:
            section_id = int(section.get("section_id") or section_index)
        except (TypeError, ValueError):
            section_id = section_index
        section_heading = _section_title(section, section_index)
        scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        for scene_index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                continue
            scene_id = _scene_id_from_obj(scene, scene_index)
            prose_path = chapter_dir / f"scene_{scene_id:03d}.md"
            text = f"[Missing scene {scene_id:03d}]"
            if prose_path.exists():
                text = _read_text(prose_path).strip()
            blocks.append(
                {
                    "chapter_id": chapter_num,
                    "section_id": section_id,
                    "section_title": section_heading,
                    "scene_id": scene_id,
                    "scene_ref": f"{chapter_num}:{scene_id}",
                    "prose_path": prose_path,
                    "text": text,
                }
            )
    return blocks


def _assemble_chapter_text(outline: Dict[str, Any], chapter_num: int, blocks: List[Dict[str, Any]]) -> str:
    chapter = _find_chapter_outline(outline, chapter_num)
    chapter_title = str(chapter.get("title") or "").strip()
    header = f"Chapter {chapter_num}: {chapter_title}" if chapter_title else f"Chapter {chapter_num}"
    sections: Dict[int, Dict[str, Any]] = {}
    order: List[int] = []
    for block in blocks:
        section_id = int(block.get("section_id") or 0)
        if section_id not in sections:
            sections[section_id] = {"title": str(block.get("section_title") or "").strip(), "texts": []}
            order.append(section_id)
        sections[section_id]["texts"].append(str(block.get("text") or "").strip())

    parts: List[str] = [f"# {header}"]
    for index, section_id in enumerate(order, start=1):
        section = sections[section_id]
        parts.append(f"## {_section_title({'title': section.get('title')}, index)}")
        texts = [text for text in section.get("texts", []) if str(text).strip()]
        if not texts:
            parts.append("[No scenes listed for this section]")
            continue
        parts.extend(texts)
    return "\n\n".join(parts).strip() + "\n"


def _issue(
    *,
    chapter_num: int,
    from_scene_ref: Optional[str],
    to_scene_ref: str,
    code: str,
    severity: str,
    message: str,
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "chapter_id": chapter_num,
        "to_scene_ref": to_scene_ref,
        "evidence": evidence,
    }
    if from_scene_ref:
        payload["from_scene_ref"] = from_scene_ref
    return payload


def _anchor_regrounding_issues(chapter_num: int, previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    previous_window = " ".join(_split_paragraphs(previous.get("text", ""))[-2:]).lower()
    current_window = " ".join(_split_paragraphs(current.get("text", ""))[:2]).lower()
    for phrase in _TRACKED_ANCHOR_PHRASES:
        if phrase not in previous_window or phrase not in current_window:
            continue
        issues.append(
            _issue(
                chapter_num=chapter_num,
                from_scene_ref=str(previous.get("scene_ref") or ""),
                to_scene_ref=str(current.get("scene_ref") or ""),
                code="repeated_anchor_regrounding",
                severity="warning",
                message=f"Boundary repeats tracked anchor phrase '{phrase}'.",
                evidence={"anchor_phrase": phrase},
            )
        )
    return issues


def audit_chapter_seams(book_root: Path, outline: Dict[str, Any], chapter_num: int, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    chapter_blocks = blocks if isinstance(blocks, list) else _chapter_scene_blocks(book_root, outline, chapter_num)
    issues: List[Dict[str, Any]] = []

    for index, block in enumerate(chapter_blocks):
        text = str(block.get("text") or "").strip()
        paragraphs = _split_paragraphs(text)
        first_paragraph = paragraphs[0] if paragraphs else ""
        first_sentence = _leading_sentence(first_paragraph)
        if first_sentence and _is_scaffold_like_sentence(first_sentence):
            issues.append(
                _issue(
                    chapter_num=chapter_num,
                    from_scene_ref=None,
                    to_scene_ref=str(block.get("scene_ref") or ""),
                    code="scaffold_leakage",
                    severity="error",
                    message="Scene opens with scaffold-like summary prose that reads like an intermediate directive.",
                    evidence={"sentence": first_sentence},
                )
            )

        if index == 0:
            continue

        previous = chapter_blocks[index - 1]
        previous_paragraphs = _split_paragraphs(str(previous.get("text") or "").strip())
        previous_last_paragraph = previous_paragraphs[-1] if previous_paragraphs else ""
        previous_last_sentence = _trailing_sentence(previous_last_paragraph)
        current_first_paragraph = first_paragraph
        current_first_sentence = first_sentence
        if not previous_last_sentence or not current_first_sentence:
            continue

        sentence_similarity = _sentence_similarity(previous_last_sentence, current_first_sentence)
        paragraph_similarity = _sentence_similarity(previous_last_paragraph, current_first_paragraph)
        if sentence_similarity >= 0.78:
            issues.append(
                _issue(
                    chapter_num=chapter_num,
                    from_scene_ref=str(previous.get("scene_ref") or ""),
                    to_scene_ref=str(block.get("scene_ref") or ""),
                    code="overlap_lead_sentence",
                    severity="error",
                    message="Opening sentence overlaps prior scene close and risks restart energy.",
                    evidence={
                        "previous_sentence": previous_last_sentence,
                        "current_sentence": current_first_sentence,
                        "similarity": round(sentence_similarity, 3),
                    },
                )
            )
        elif paragraph_similarity >= 0.82:
            issues.append(
                _issue(
                    chapter_num=chapter_num,
                    from_scene_ref=str(previous.get("scene_ref") or ""),
                    to_scene_ref=str(block.get("scene_ref") or ""),
                    code="restart_energy_overlap",
                    severity="error",
                    message="Opening paragraph partially restates the prior scene instead of advancing.",
                    evidence={
                        "previous_paragraph": previous_last_paragraph,
                        "current_paragraph": current_first_paragraph,
                        "similarity": round(paragraph_similarity, 3),
                    },
                )
            )

        previous_past = _count_markers(previous_last_sentence, _PAST_TENSE_MARKERS)
        previous_present = _count_markers(previous_last_sentence, _PRESENT_TENSE_MARKERS)
        current_past = _count_markers(current_first_sentence, _PAST_TENSE_MARKERS)
        current_present = _count_markers(current_first_sentence, _PRESENT_TENSE_MARKERS)
        if previous_past > previous_present and current_present > current_past:
            issues.append(
                _issue(
                    chapter_num=chapter_num,
                    from_scene_ref=str(previous.get("scene_ref") or ""),
                    to_scene_ref=str(block.get("scene_ref") or ""),
                    code="tense_shift_at_join",
                    severity="warning",
                    message="Join flips from past-dominant narration into present-dominant narration.",
                    evidence={
                        "previous_sentence": previous_last_sentence,
                        "current_sentence": current_first_sentence,
                    },
                )
            )

        issues.extend(_anchor_regrounding_issues(chapter_num, previous, block))

    error_count = sum(1 for issue in issues if str(issue.get("severity") or "").lower() == "error")
    warning_count = sum(1 for issue in issues if str(issue.get("severity") or "").lower() == "warning")
    return {
        "schema_version": "chapter_seam_report_v1",
        "chapter_id": chapter_num,
        "generated_at": _now_iso(),
        "status": "pass" if error_count == 0 else "fail",
        "issue_counts": {"error": error_count, "warning": warning_count, "total": len(issues)},
        "issues": issues,
    }


def _remove_first_sentence(text: str) -> str:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return str(text or "")
    first = paragraphs[0]
    sentences = _split_sentences(first)
    if len(sentences) <= 1:
        return "\n\n".join(paragraphs[1:]).strip()
    paragraphs[0] = _join_sentences(sentences[1:])
    return "\n\n".join(part for part in paragraphs if part.strip()).strip()


def _drop_first_paragraph(text: str) -> str:
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) <= 1:
        return str(text or "").strip()
    return "\n\n".join(paragraphs[1:]).strip()


def _replace_first_sentence(text: str, new_sentence: str) -> str:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return str(text or "")
    sentences = _split_sentences(paragraphs[0])
    if not sentences:
        return str(text or "")
    sentences[0] = new_sentence.strip()
    paragraphs[0] = _join_sentences(sentences)
    return "\n\n".join(part for part in paragraphs if part.strip()).strip()


def repair_chapter_seams(blocks: List[Dict[str, Any]], report: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    repaired = [dict(block) for block in blocks]
    actions: List[Dict[str, Any]] = []
    issues = report.get("issues") if isinstance(report.get("issues"), list) else []

    for issue in issues:
        if not isinstance(issue, dict):
            continue
        to_scene_ref = str(issue.get("to_scene_ref") or "").strip()
        if not to_scene_ref:
            continue
        target_index = next(
            (idx for idx, block in enumerate(repaired) if str(block.get("scene_ref") or "") == to_scene_ref),
            None,
        )
        if target_index is None:
            continue
        current_text = str(repaired[target_index].get("text") or "").strip()
        if not current_text:
            continue
        code = str(issue.get("code") or "").strip()

        if code == "scaffold_leakage":
            first_paragraph = _split_paragraphs(current_text)
            if first_paragraph and _is_scaffold_like_sentence(_leading_sentence(first_paragraph[0])):
                updated = _drop_first_paragraph(current_text)
                if updated and updated != current_text:
                    repaired[target_index]["text"] = updated
                    actions.append(
                        {
                            "code": code,
                            "target_scene_ref": to_scene_ref,
                            "action": "drop_first_paragraph",
                        }
                    )
                    continue

        if code in {"overlap_lead_sentence", "restart_energy_overlap"}:
            updated = _remove_first_sentence(current_text)
            if updated and updated != current_text:
                repaired[target_index]["text"] = updated
                actions.append(
                    {
                        "code": code,
                        "target_scene_ref": to_scene_ref,
                        "action": "drop_first_sentence",
                    }
                )
                continue

        if code == "tense_shift_at_join":
            first_sentence = _leading_sentence(current_text)
            if first_sentence and _is_scaffold_like_sentence(first_sentence):
                updated_sentence = _convert_present_sentence_to_past(first_sentence)
                if updated_sentence != first_sentence:
                    repaired[target_index]["text"] = _replace_first_sentence(current_text, updated_sentence)
                    actions.append(
                        {
                            "code": code,
                            "target_scene_ref": to_scene_ref,
                            "action": "convert_first_sentence_to_past",
                        }
                    )

    return repaired, actions


def _chapter_seam_dir(book_root: Path, chapter_num: int) -> Path:
    return book_root / "draft" / "context" / "chapter_seams" / f"ch_{chapter_num:03d}"


def provisional_chapter_path(book_root: Path, chapter_num: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.provisional.md"


def seam_candidate_path(book_root: Path, chapter_num: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.seam_candidate.md"


def seam_report_path(book_root: Path, chapter_num: int) -> Path:
    return _chapter_seam_dir(book_root, chapter_num) / "chapter_seam_report.json"


def finalize_locked_chapter(book_root: Path, outline: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
    blocks = _chapter_scene_blocks(book_root, outline, chapter_num)
    provisional_text = _assemble_chapter_text(outline, chapter_num, blocks)
    provisional_path = provisional_chapter_path(book_root, chapter_num)
    _write_text(provisional_path, provisional_text)

    initial_report = audit_chapter_seams(book_root, outline, chapter_num, blocks=blocks)
    repaired_blocks, repair_actions = repair_chapter_seams(blocks, initial_report)
    final_report = audit_chapter_seams(book_root, outline, chapter_num, blocks=repaired_blocks)
    final_text = _assemble_chapter_text(outline, chapter_num, repaired_blocks)

    final_path = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.md"
    candidate_path: Optional[Path] = None
    status = str(final_report.get("status") or "fail").strip().lower()
    if status == "pass":
        _write_text(final_path, final_text)
    else:
        candidate_path = seam_candidate_path(book_root, chapter_num)
        _write_text(candidate_path, final_text)

    payload = {
        "schema_version": "chapter_seam_report_v1",
        "chapter_id": chapter_num,
        "generated_at": _now_iso(),
        "status": "finalized" if status == "pass" else "attention_required",
        "provisional_path": provisional_path.relative_to(book_root).as_posix(),
        "final_path": final_path.relative_to(book_root).as_posix() if status == "pass" else None,
        "candidate_path": candidate_path.relative_to(book_root).as_posix() if candidate_path else None,
        "repair_actions": repair_actions,
        "before": initial_report,
        "after": final_report,
    }
    report_path = seam_report_path(book_root, chapter_num)
    _write_json(report_path, payload)
    return {
        "status": payload["status"],
        "report_path": report_path.relative_to(book_root).as_posix(),
        "provisional_path": payload["provisional_path"],
        "final_path": payload["final_path"],
        "candidate_path": payload["candidate_path"],
        "repair_action_count": len(repair_actions),
        "issue_counts_before": dict(initial_report.get("issue_counts") or {}),
        "issue_counts_after": dict(final_report.get("issue_counts") or {}),
    }
