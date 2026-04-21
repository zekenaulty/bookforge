from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import re

from bookforge.config.env import load_config
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.phases.chapter_seam_lint_phase import _lint_chapter_seam_pair
from bookforge.phases.chapter_seam_repair_phase import _repair_chapter_seam_pair
from bookforge.pipeline.config import _lint_repair_max_passes
from bookforge.pipeline.llm_ops import _lint_status_from_issues
from bookforge.pipeline.parse import _extract_authoritative_surfaces, _extract_ui_stat_lines


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
_BOUNDARY_BRIDGE_PREFIXES = (
    "with ",
    "as ",
    "armed with ",
    "trapped under ",
    "still ",
    "after ",
    "the party ",
    "the towering ",
    "the heavy ",
    "the blast ",
    "the splintered ",
    "rhea ",
    "vance ",
)
_WINDOW_MAX_PARAGRAPHS = 2


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = str(text or "").strip()
    path.write_text(normalized + ("\n" if normalized else ""), encoding="utf-8")
    return path


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _normalize_for_compare(text: str) -> str:
    lowered = _NORMALIZE_RE.sub(" ", str(text or "").lower())
    return " ".join(lowered.split())


def _preview_text(text: str, limit: int = 220) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


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


def _join_paragraphs(paragraphs: List[str]) -> str:
    return "\n\n".join(part.strip() for part in paragraphs if str(part).strip()).strip()


def _is_ui_only_paragraph(text: str) -> bool:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return bool(lines) and all(line.startswith("[") and line.endswith("]") for line in lines)


def _split_sentences(text: str) -> List[str]:
    stripped = str(text or "").strip()
    if not stripped:
        return []
    parts = _SENTENCE_SPLIT_RE.split(stripped)
    return [part.strip() for part in parts if part.strip()]


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


def _scene_original_path(prose_path: Path) -> Path:
    return prose_path.with_name(f"{prose_path.stem}.original{prose_path.suffix}")


def _scene_fixed_path(prose_path: Path) -> Path:
    return prose_path.with_name(f"{prose_path.stem}.fixed{prose_path.suffix}")


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
                    "original_path": _scene_original_path(prose_path),
                    "fixed_path": _scene_fixed_path(prose_path),
                    "text": text,
                }
            )
    return blocks


def _blocks_with_original_texts(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    original_blocks: List[Dict[str, Any]] = []
    for block in blocks:
        original_path = block.get("original_path")
        text = str(block.get("text") or "").strip()
        if isinstance(original_path, Path) and original_path.exists():
            text = _read_text(original_path).strip()
        original_blocks.append({**block, "text": text})
    return original_blocks


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


def _pair_window_text(text: str, *, from_end: bool) -> str:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return ""
    count = min(_WINDOW_MAX_PARAGRAPHS, len(paragraphs))
    selected = paragraphs[-count:] if from_end else paragraphs[:count]
    return _join_paragraphs(selected)


def _pair_window_count(text: str) -> int:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return 0
    return min(_WINDOW_MAX_PARAGRAPHS, len(paragraphs))


def _replace_window(text: str, *, from_end: bool, paragraph_count: int, new_window: str) -> str:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return str(new_window or "").strip()
    count = max(1, min(paragraph_count or 1, len(paragraphs)))
    replacement = _split_paragraphs(new_window)
    if not replacement:
        replacement = [str(new_window or "").strip()]
    if from_end:
        paragraphs[-count:] = replacement
    else:
        paragraphs[:count] = replacement
    return _join_paragraphs(paragraphs)


def _pair_payload(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    previous_text = str(previous.get("text") or "").strip()
    current_text = str(current.get("text") or "").strip()
    previous_count = _pair_window_count(previous_text)
    current_count = _pair_window_count(current_text)
    previous_tail = _pair_window_text(previous_text, from_end=True)
    current_head = _pair_window_text(current_text, from_end=False)
    return {
        "chapter_id": int(previous.get("chapter_id") or current.get("chapter_id") or 0),
        "scene_a": {
            "scene_ref": str(previous.get("scene_ref") or ""),
            "scene_id": int(previous.get("scene_id") or 0),
            "section_id": int(previous.get("section_id") or 0),
            "section_title": str(previous.get("section_title") or ""),
            "full_text": previous_text,
            "writable_window": previous_tail,
            "writable_window_position": "tail",
            "writable_window_paragraphs": previous_count,
        },
        "scene_b": {
            "scene_ref": str(current.get("scene_ref") or ""),
            "scene_id": int(current.get("scene_id") or 0),
            "section_id": int(current.get("section_id") or 0),
            "section_title": str(current.get("section_title") or ""),
            "full_text": current_text,
            "writable_window": current_head,
            "writable_window_position": "head",
            "writable_window_paragraphs": current_count,
        },
    }


def _pair_issue_key(issue: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    evidence = issue.get("evidence") if isinstance(issue.get("evidence"), dict) else {}
    return (
        str(issue.get("code") or ""),
        str(issue.get("message") or ""),
        str(issue.get("severity") or ""),
        str(issue.get("from_scene_ref") or ""),
        str(evidence.get("excerpt") or ""),
    )


def _merge_issues(*groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, str, str, str]] = set()
    for group in groups:
        for issue in group:
            if not isinstance(issue, dict):
                continue
            key = _pair_issue_key(issue)
            if key in seen:
                continue
            seen.add(key)
            merged.append(issue)
    return merged


def _anchor_regrounding_issues(chapter_num: int, previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    previous_window = _pair_window_text(str(previous.get("text") or ""), from_end=True).lower()
    current_window = _pair_window_text(str(current.get("text") or ""), from_end=False).lower()
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


def _ui_boundary_issues(chapter_num: int, previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    previous_window = _pair_window_text(str(previous.get("text") or ""), from_end=True)
    current_window = _pair_window_text(str(current.get("text") or ""), from_end=False)
    previous_surfaces = _extract_authoritative_surfaces(previous_window)
    current_surfaces = _extract_authoritative_surfaces(current_window)

    previous_texts = {str(surface.get("text") or "").strip() for surface in previous_surfaces if isinstance(surface, dict)}
    current_texts = {str(surface.get("text") or "").strip() for surface in current_surfaces if isinstance(surface, dict)}
    for shared in sorted(text for text in previous_texts & current_texts if text):
        issues.append(
            _issue(
                chapter_num=chapter_num,
                from_scene_ref=str(previous.get("scene_ref") or ""),
                to_scene_ref=str(current.get("scene_ref") or ""),
                code="duplicate_ui_surface",
                severity="error",
                message="Boundary duplicates the same authoritative UI/system surface across adjacent scenes.",
                evidence={"excerpt": shared},
            )
        )

    previous_stats = _extract_ui_stat_lines("", authoritative_surfaces=previous_surfaces)
    current_stats = _extract_ui_stat_lines("", authoritative_surfaces=current_surfaces)
    current_by_key = {str(item.get("key") or "").strip().lower(): item for item in current_stats if isinstance(item, dict)}
    for previous_item in previous_stats:
        if not isinstance(previous_item, dict):
            continue
        key = str(previous_item.get("key") or "").strip().lower()
        if not key or key not in current_by_key:
            continue
        current_item = current_by_key[key]
        if previous_item.get("current") == current_item.get("current") and previous_item.get("max") == current_item.get("max"):
            continue
        issues.append(
            _issue(
                chapter_num=chapter_num,
                from_scene_ref=str(previous.get("scene_ref") or ""),
                to_scene_ref=str(current.get("scene_ref") or ""),
                code="ui_value_drift",
                severity="error",
                message=f"Boundary repeats the same UI surface '{previous_item.get('key')}' with altered values.",
                evidence={
                    "previous": previous_item,
                    "current": current_item,
                },
            )
        )
    return issues


def _is_bridge_heavy_opening(sentence: str) -> bool:
    lowered = str(sentence or "").strip().lower()
    return any(lowered.startswith(prefix) for prefix in _BOUNDARY_BRIDGE_PREFIXES)


def _scene_opening_issues(chapter_num: int, block: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
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
    return issues


def _boundary_issues(chapter_num: int, previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    previous_paragraphs = _split_paragraphs(str(previous.get("text") or "").strip())
    current_paragraphs = _split_paragraphs(str(current.get("text") or "").strip())
    previous_last_paragraph = previous_paragraphs[-1] if previous_paragraphs else ""
    previous_last_sentence = _trailing_sentence(previous_last_paragraph)
    current_first_paragraph = current_paragraphs[0] if current_paragraphs else ""
    current_first_sentence = _leading_sentence(current_first_paragraph)

    if previous_last_sentence and current_first_sentence:
        sentence_similarity = _sentence_similarity(previous_last_sentence, current_first_sentence)
        paragraph_similarity = _sentence_similarity(previous_last_paragraph, current_first_paragraph)
        if sentence_similarity >= 0.20:
            issues.append(
                _issue(
                    chapter_num=chapter_num,
                    from_scene_ref=str(previous.get("scene_ref") or ""),
                    to_scene_ref=str(current.get("scene_ref") or ""),
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
        elif paragraph_similarity >= 0.20 or (sentence_similarity >= 0.14 and _is_bridge_heavy_opening(current_first_sentence)):
            issues.append(
                _issue(
                    chapter_num=chapter_num,
                    from_scene_ref=str(previous.get("scene_ref") or ""),
                    to_scene_ref=str(current.get("scene_ref") or ""),
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
                    to_scene_ref=str(current.get("scene_ref") or ""),
                    code="tense_shift_at_join",
                    severity="warning",
                    message="Join flips from past-dominant narration into present-dominant narration.",
                    evidence={
                        "previous_sentence": previous_last_sentence,
                        "current_sentence": current_first_sentence,
                    },
                )
            )

    issues.extend(_anchor_regrounding_issues(chapter_num, previous, current))
    issues.extend(_ui_boundary_issues(chapter_num, previous, current))
    return issues


def audit_scene_boundary(chapter_num: int, previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
    return _merge_issues(
        _scene_opening_issues(chapter_num, current),
        _boundary_issues(chapter_num, previous, current),
    )


def audit_chapter_seams(book_root: Path, outline: Dict[str, Any], chapter_num: int, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    chapter_blocks = blocks if isinstance(blocks, list) else _chapter_scene_blocks(book_root, outline, chapter_num)
    issues: List[Dict[str, Any]] = []
    if chapter_blocks:
        issues.extend(_scene_opening_issues(chapter_num, chapter_blocks[0]))
    for index in range(1, len(chapter_blocks)):
        issues.extend(audit_scene_boundary(chapter_num, chapter_blocks[index - 1], chapter_blocks[index]))

    error_count = sum(1 for issue in issues if str(issue.get("severity") or "").lower() == "error")
    warning_count = sum(1 for issue in issues if str(issue.get("severity") or "").lower() == "warning")
    return {
        "schema_version": "chapter_seam_audit_v2",
        "chapter_id": chapter_num,
        "generated_at": _now_iso(),
        "status": "pass" if error_count == 0 else "fail",
        "issue_counts": {"error": error_count, "warning": warning_count, "total": len(issues)},
        "issues": issues,
    }


def _combined_pair_report(llm_report: Dict[str, Any], deterministic_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    llm_issues = llm_report.get("issues") if isinstance(llm_report.get("issues"), list) else []
    issues = _merge_issues(llm_issues, deterministic_issues)
    return {
        "schema_version": "1.0",
        "status": _lint_status_from_issues(issues),
        "issues": issues,
    }


def _apply_pair_repair(previous: Dict[str, Any], current: Dict[str, Any], pair_payload: Dict[str, Any], repair_payload: Dict[str, Any]) -> Dict[str, Any]:
    previous_window_count = int(pair_payload.get("scene_a", {}).get("writable_window_paragraphs") or 1)
    current_window_count = int(pair_payload.get("scene_b", {}).get("writable_window_paragraphs") or 1)
    previous_before = str(previous.get("text") or "").strip()
    current_before = str(current.get("text") or "").strip()
    previous_after = _replace_window(
        previous_before,
        from_end=True,
        paragraph_count=previous_window_count,
        new_window=str(repair_payload.get("scene_a_tail") or "").strip(),
    )
    current_after = _replace_window(
        current_before,
        from_end=False,
        paragraph_count=current_window_count,
        new_window=str(repair_payload.get("scene_b_head") or "").strip(),
    )
    previous["text"] = previous_after
    current["text"] = current_after
    return {
        "changed": previous_after != previous_before or current_after != current_before,
        "scene_a_tail_preview": _preview_text(repair_payload.get("scene_a_tail") or ""),
        "scene_b_head_preview": _preview_text(repair_payload.get("scene_b_head") or ""),
        "notes": list(repair_payload.get("notes") if isinstance(repair_payload.get("notes"), list) else []),
    }


def _run_chapter_seam_pairs(
    book_root: Path,
    outline: Dict[str, Any],
    chapter_num: int,
    blocks: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if len(blocks) < 2:
        return [dict(block) for block in blocks], []

    config = load_config()
    workspace = book_root.parents[1]
    system_path = book_root / "prompts" / "system_v1.md"
    linter_client = get_llm_client(config, phase="linter")
    repair_client = get_llm_client(config, phase="repair")
    linter_model = resolve_model("linter", config)
    repair_model = resolve_model("repair", config)
    working_blocks = [dict(block) for block in blocks]
    max_passes = max(1, _lint_repair_max_passes())

    pair_reports: List[Dict[str, Any]] = []
    for index in range(1, len(working_blocks)):
        previous = working_blocks[index - 1]
        current = working_blocks[index]
        pass_records: List[Dict[str, Any]] = []
        pair_status = "pass"
        repair_applied = False
        final_report: Optional[Dict[str, Any]] = None
        initial_issues = audit_scene_boundary(chapter_num, previous, current)

        for pass_index in range(1, max_passes + 1):
            pair_payload = _pair_payload(previous, current)
            deterministic_issues = audit_scene_boundary(chapter_num, previous, current)
            llm_report = _lint_chapter_seam_pair(
                workspace=workspace,
                book_root=book_root,
                system_path=system_path,
                pair_payload=pair_payload,
                deterministic_issues=deterministic_issues,
                client=linter_client,
                model=linter_model,
            )
            combined_report = _combined_pair_report(llm_report, deterministic_issues)
            record: Dict[str, Any] = {
                "pass": pass_index,
                "lint": combined_report,
            }
            pass_records.append(record)
            if combined_report.get("status") == "pass":
                final_report = combined_report
                break

            repair_payload = _repair_chapter_seam_pair(
                workspace=workspace,
                book_root=book_root,
                system_path=system_path,
                pair_payload=pair_payload,
                issues=list(combined_report.get("issues") or []),
                client=repair_client,
                model=repair_model,
            )
            repair_record = _apply_pair_repair(previous, current, pair_payload, repair_payload)
            repair_record["status"] = str(repair_payload.get("status") or "repaired")
            record["repair"] = repair_record
            repair_applied = repair_applied or bool(repair_record.get("changed"))
            if not repair_record.get("changed"):
                pair_status = "attention_required"
                final_report = _combined_pair_report({"issues": []}, audit_scene_boundary(chapter_num, previous, current))
                break

        if final_report is None:
            final_report = _combined_pair_report({"issues": []}, audit_scene_boundary(chapter_num, previous, current))
        if final_report.get("status") != "pass":
            pair_status = "attention_required"
        pair_reports.append(
            {
                "pair_index": index,
                "from_scene_ref": str(previous.get("scene_ref") or ""),
                "to_scene_ref": str(current.get("scene_ref") or ""),
                "status": pair_status,
                "repair_applied": repair_applied,
                "passes_used": len(pass_records),
                "issues_before": initial_issues,
                "issues_after": list(final_report.get("issues") or []),
                "pass_records": pass_records,
            }
        )

    return working_blocks, pair_reports


def _snapshot_original_scene_versions(blocks: List[Dict[str, Any]]) -> List[str]:
    created: List[str] = []
    for block in blocks:
        prose_path = block.get("prose_path")
        original_path = block.get("original_path")
        if not isinstance(prose_path, Path) or not isinstance(original_path, Path):
            continue
        if original_path.exists():
            continue
        if prose_path.exists():
            _write_text(original_path, _read_text(prose_path))
        else:
            _write_text(original_path, str(block.get("text") or ""))
        created.append(original_path.name)
    return created


def _write_fixed_scene_versions(book_root: Path, blocks: List[Dict[str, Any]], *, promote: bool) -> List[Dict[str, str]]:
    scene_artifacts: List[Dict[str, str]] = []
    for block in blocks:
        prose_path = block.get("prose_path")
        fixed_path = block.get("fixed_path")
        original_path = block.get("original_path")
        if not isinstance(prose_path, Path) or not isinstance(fixed_path, Path) or not isinstance(original_path, Path):
            continue
        text = str(block.get("text") or "").strip()
        _write_text(fixed_path, text)
        if promote:
            _write_text(prose_path, text)
        scene_artifacts.append(
            {
                "scene_ref": str(block.get("scene_ref") or ""),
                "current_path": prose_path.relative_to(book_root).as_posix(),
                "original_path": original_path.relative_to(book_root).as_posix(),
                "fixed_path": fixed_path.relative_to(book_root).as_posix(),
            }
        )
    return scene_artifacts


def _count_repair_actions(pair_reports: List[Dict[str, Any]]) -> int:
    count = 0
    for pair in pair_reports:
        if not isinstance(pair, dict):
            continue
        passes = pair.get("pass_records") if isinstance(pair.get("pass_records"), list) else []
        for entry in passes:
            if not isinstance(entry, dict):
                continue
            repair = entry.get("repair") if isinstance(entry.get("repair"), dict) else {}
            if repair.get("changed"):
                count += 1
    return count


def _chapter_seam_dir(book_root: Path, chapter_num: int) -> Path:
    return book_root / "draft" / "context" / "chapter_seams" / f"ch_{chapter_num:03d}"


def original_chapter_path(book_root: Path, chapter_num: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.original.md"


def fixed_chapter_path(book_root: Path, chapter_num: int) -> Path:
    return book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.fixed.md"


def provisional_chapter_path(book_root: Path, chapter_num: int) -> Path:
    return original_chapter_path(book_root, chapter_num)


def seam_candidate_path(book_root: Path, chapter_num: int) -> Path:
    return fixed_chapter_path(book_root, chapter_num)


def seam_report_path(book_root: Path, chapter_num: int) -> Path:
    return _chapter_seam_dir(book_root, chapter_num) / "chapter_seam_report.json"


def finalize_locked_chapter(book_root: Path, outline: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
    blocks = _chapter_scene_blocks(book_root, outline, chapter_num)
    original_scene_snapshots = _snapshot_original_scene_versions(blocks)
    original_blocks = _blocks_with_original_texts(blocks)

    original_text = _assemble_chapter_text(outline, chapter_num, original_blocks)
    original_path = original_chapter_path(book_root, chapter_num)
    _write_text(original_path, original_text)

    initial_report = audit_chapter_seams(book_root, outline, chapter_num, blocks=blocks)
    repaired_blocks, pair_reports = _run_chapter_seam_pairs(book_root, outline, chapter_num, blocks)
    final_report = audit_chapter_seams(book_root, outline, chapter_num, blocks=repaired_blocks)

    fixed_text = _assemble_chapter_text(outline, chapter_num, repaired_blocks)
    fixed_path = fixed_chapter_path(book_root, chapter_num)
    _write_text(fixed_path, fixed_text)

    status = str(final_report.get("status") or "fail").strip().lower()
    final_path = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.md"
    candidate_path: Optional[Path] = None
    scene_artifacts = _write_fixed_scene_versions(book_root, repaired_blocks, promote=status == "pass")
    if status == "pass":
        _write_text(final_path, fixed_text)
    else:
        candidate_path = fixed_path

    payload = {
        "schema_version": "chapter_seam_report_v2",
        "chapter_id": chapter_num,
        "generated_at": _now_iso(),
        "status": "finalized" if status == "pass" else "attention_required",
        "original_path": original_path.relative_to(book_root).as_posix(),
        "fixed_path": fixed_path.relative_to(book_root).as_posix(),
        "provisional_path": original_path.relative_to(book_root).as_posix(),
        "final_path": final_path.relative_to(book_root).as_posix() if status == "pass" else None,
        "candidate_path": candidate_path.relative_to(book_root).as_posix() if candidate_path else None,
        "repair_action_count": _count_repair_actions(pair_reports),
        "original_scene_snapshots_created": original_scene_snapshots,
        "scene_artifacts": scene_artifacts,
        "pairs": pair_reports,
        "before": initial_report,
        "after": final_report,
    }
    report_path = seam_report_path(book_root, chapter_num)
    _write_json(report_path, payload)
    return {
        "status": payload["status"],
        "report_path": report_path.relative_to(book_root).as_posix(),
        "original_path": payload["original_path"],
        "fixed_path": payload["fixed_path"],
        "provisional_path": payload["provisional_path"],
        "final_path": payload["final_path"],
        "candidate_path": payload["candidate_path"],
        "repair_action_count": payload["repair_action_count"],
        "issue_counts_before": dict(initial_report.get("issue_counts") or {}),
        "issue_counts_after": dict(final_report.get("issue_counts") or {}),
    }
