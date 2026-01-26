from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast
import json
import re

from bookforge.config.env import load_config, read_env_value, read_int_env
from bookforge.characters import characters_ready, generate_characters
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message
from bookforge.memory.continuity import (
    ContinuityPack,
    continuity_pack_path,
    load_style_anchor,
    save_continuity_pack,
    save_style_anchor,
    style_anchor_path,
)
from bookforge.phases.plan import plan_scene
from bookforge.prompt.renderer import render_template_file
from bookforge.prompt.system import load_system_prompt
from bookforge.util.paths import repo_root
from bookforge.util.schema import validate_json


DEFAULT_WRITE_MAX_TOKENS = 36864
DEFAULT_LINT_MAX_TOKENS = 73728
DEFAULT_REPAIR_MAX_TOKENS = 73728
DEFAULT_CONTINUITY_MAX_TOKENS = 73728
DEFAULT_STYLE_ANCHOR_MAX_TOKENS = 16384
DEFAULT_EMPTY_RESPONSE_RETRIES = 2

SUMMARY_CHAPTER_SO_FAR_CAP = 20
SUMMARY_KEY_FACTS_CAP = 25
SUMMARY_MUST_STAY_TRUE_CAP = 20
SUMMARY_STORY_SO_FAR_CAP = 40


def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _write_max_tokens() -> int:
    return _int_env("BOOKFORGE_WRITE_MAX_TOKENS", DEFAULT_WRITE_MAX_TOKENS)


def _lint_max_tokens() -> int:
    return _int_env("BOOKFORGE_LINT_MAX_TOKENS", DEFAULT_LINT_MAX_TOKENS)


def _repair_max_tokens() -> int:
    return _int_env("BOOKFORGE_REPAIR_MAX_TOKENS", DEFAULT_REPAIR_MAX_TOKENS)


def _continuity_max_tokens() -> int:
    return _int_env("BOOKFORGE_CONTINUITY_MAX_TOKENS", DEFAULT_CONTINUITY_MAX_TOKENS)


def _style_anchor_max_tokens() -> int:
    return _int_env("BOOKFORGE_STYLE_ANCHOR_MAX_TOKENS", DEFAULT_STYLE_ANCHOR_MAX_TOKENS)


def _empty_response_retries() -> int:
    return max(0, _int_env("BOOKFORGE_EMPTY_RESPONSE_RETRIES", DEFAULT_EMPTY_RESPONSE_RETRIES))




def _lint_mode() -> str:
    raw = read_env_value("BOOKFORGE_LINT_MODE")
    if raw is None:
        raw = "warn"
    raw = str(raw).strip().lower()
    if raw in {"strict", "warn", "off"}:
        return raw
    return "warn"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_template(book_root: Path, name: str) -> Path:
    book_template = book_root / "prompts" / "templates" / name
    if book_template.exists():
        return book_template
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / name


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _response_truncated(response: LLMResponse) -> bool:
    raw = response.raw
    if not isinstance(raw, dict):
        return False
    if response.provider == "gemini":
        candidates = raw.get("candidates", [])
        if not candidates:
            return False
        finish = candidates[0].get("finishReason")
        return str(finish).upper() == "MAX_TOKENS"
    if response.provider == "openai":
        choice = raw.get("choices", [{}])[0]
        finish = choice.get("finish_reason")
        return str(finish).lower() == "length"
    return False


def _clean_json_payload(payload: str) -> str:
    cleaned = payload.strip()
    cleaned = cleaned.replace("\ufeff", "")
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"')
    cleaned = cleaned.replace("\u2018", "'").replace("\u2019", "'")
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned




def _normalize_lint_report(report: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(report)
    if "schema_version" not in normalized:
        normalized["schema_version"] = "1.0"

    status = normalized.get("status")
    if not status:
        passed = normalized.get("pass")
        if isinstance(passed, bool):
            normalized["status"] = "pass" if passed else "fail"

    issues: List[Dict[str, Any]] = []
    raw_issues = normalized.get("issues")
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if isinstance(item, dict) and item.get("message"):
                issues.append(item)
            elif item is not None:
                issues.append({"code": "issue", "message": str(item)})

    violations = normalized.get("violations")
    if isinstance(violations, list):
        for item in violations:
            if item is not None:
                issues.append({"code": "violation", "message": str(item), "severity": "error"})

    warnings = normalized.get("warnings")
    if isinstance(warnings, list):
        for item in warnings:
            if item is not None:
                issues.append({"code": "warning", "message": str(item), "severity": "warning"})

    if not isinstance(normalized.get("issues"), list) or issues:
        normalized["issues"] = issues

    if "status" not in normalized or not normalized.get("status"):
        normalized["status"] = "fail" if normalized.get("issues") else "pass"

    return normalized


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        payload = match.group(1)
    else:
        match = re.search(r"(\{[\s\S]*\})", text)
        if not match:
            raise ValueError("No JSON object found in response.")
        payload = match.group(1)
    payload = payload.strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        cleaned = _clean_json_payload(payload)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(cleaned)
            except (ValueError, SyntaxError) as exc:
                raise ValueError("Invalid JSON in response.") from exc
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
    match = re.search(r"STATE\s*_?PATCH\s*:\s*", text, re.IGNORECASE)
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

    raise ValueError("Missing STATE_PATCH block in response.")


def _parse_until(value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not value:
        return None, None
    parts = [part.strip() for part in value.split(":") if part.strip()]
    if len(parts) == 2 and parts[0].lower() == "chapter":
        return int(parts[1]), None
    if len(parts) == 4 and parts[0].lower() == "chapter" and parts[2].lower() == "scene":
        return int(parts[1]), int(parts[3])
    raise ValueError("Invalid --until value. Expected chapter:N or chapter:N:scene:M.")


def _chapter_scene_count(chapter: Dict[str, Any]) -> int:
    count = 0
    sections = chapter.get("sections", []) if isinstance(chapter.get("sections", []), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        scenes = section.get("scenes", []) if isinstance(section.get("scenes", []), list) else []
        count += len([scene for scene in scenes if isinstance(scene, dict)])
    return count


def _outline_summary(outline: Dict[str, Any]) -> Tuple[List[int], Dict[int, int]]:
    chapter_order: List[int] = []
    scene_counts: Dict[int, int] = {}
    chapters = outline.get("chapters", []) if isinstance(outline.get("chapters", []), list) else []
    for index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            continue
        chapter_id = chapter.get("chapter_id", index)
        try:
            chapter_num = int(chapter_id)
        except (TypeError, ValueError):
            continue
        chapter_order.append(chapter_num)
        scene_counts[chapter_num] = _chapter_scene_count(chapter)
    return chapter_order, scene_counts


def _build_character_registry(outline: Dict[str, Any]) -> List[Dict[str, str]]:
    registry: List[Dict[str, str]] = []
    characters = outline.get("characters", [])
    if not isinstance(characters, list):
        return registry
    for item in characters:
        if not isinstance(item, dict):
            continue
        character_id = str(item.get("character_id") or "").strip()
        if not character_id:
            continue
        name = str(item.get("name") or "").strip()
        registry.append({"character_id": character_id, "name": name})
    return registry


def _build_thread_registry(outline: Dict[str, Any]) -> List[Dict[str, str]]:
    registry: List[Dict[str, str]] = []
    threads = outline.get("threads", [])
    if not isinstance(threads, list):
        return registry
    for item in threads:
        if not isinstance(item, dict):
            continue
        thread_id = str(item.get("thread_id") or "").strip()
        if not thread_id:
            continue
        label = str(item.get("label") or "").strip()
        status = str(item.get("status") or "").strip()
        entry = {"thread_id": thread_id}
        if label:
            entry["label"] = label
        if status:
            entry["status"] = status
        registry.append(entry)
    return registry


def _character_slug(character_id: str) -> str:
    cleaned = str(character_id or "").strip()
    if cleaned.upper().startswith("CHAR_"):
        cleaned = cleaned[5:]
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]+", "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned.lower() or "character"


def _load_character_states(book_root: Path, scene_card: Dict[str, Any]) -> List[Dict[str, Any]]:
    cast_ids = scene_card.get("cast_present_ids", []) if isinstance(scene_card, dict) else []
    if not isinstance(cast_ids, list):
        cast_ids = []
    states: List[Dict[str, Any]] = []
    for char_id in cast_ids:
        slug = _character_slug(str(char_id))
        state_path = book_root / "draft" / "context" / "characters" / f"{slug}.state.json"
        if state_path.exists():
            try:
                states.append(json.loads(state_path.read_text(encoding="utf-8")))
                continue
            except json.JSONDecodeError:
                pass
        states.append({"character_id": str(char_id), "missing": True})
    return states



def _normalize_continuity_pack(
    pack: Dict[str, Any],
    scene_card: Dict[str, Any],
    thread_registry: List[Dict[str, str]],
) -> Dict[str, Any]:
    normalized = dict(pack)
    allowed_cast = scene_card.get("cast_present", [])
    if not isinstance(allowed_cast, list):
        allowed_cast = []
    allowed_cast = [str(item) for item in allowed_cast if str(item).strip()]
    cast_present = normalized.get("cast_present", [])
    if not isinstance(cast_present, list):
        cast_present = []
    cast_present = [str(item) for item in cast_present if str(item).strip()]
    if allowed_cast:
        filtered_cast = [item for item in cast_present if item in allowed_cast]
        normalized["cast_present"] = filtered_cast or list(allowed_cast)
    else:
        normalized["cast_present"] = []

    allowed_threads = {
        str(item.get("thread_id")).strip()
        for item in thread_registry
        if isinstance(item, dict) and str(item.get("thread_id") or "").strip()
    }
    thread_ids = scene_card.get("thread_ids", [])
    if not isinstance(thread_ids, list):
        thread_ids = []
    thread_ids = [str(item) for item in thread_ids if str(item).strip()]
    open_threads = normalized.get("open_threads", [])
    if not isinstance(open_threads, list):
        open_threads = []
    open_threads = [str(item) for item in open_threads if str(item).strip()]
    if thread_ids:
        open_threads = thread_ids
    if allowed_threads:
        open_threads = [item for item in open_threads if item in allowed_threads]
    normalized["open_threads"] = open_threads

    return normalized


def _summary_list(value: Any) -> List[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [value]
    else:
        items = []
    cleaned: List[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _coerce_summary_update(patch: Dict[str, Any]) -> None:
    summary_update = patch.get("summary_update")
    if not isinstance(summary_update, dict):
        return
    for key in (
        "last_scene",
        "key_events",
        "must_stay_true",
        "chapter_so_far_add",
        "story_so_far_add",
        "threads_touched",
    ):
        if key in summary_update:
            summary_update[key] = _summary_list(summary_update.get(key))


def _dedupe_preserve(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _summary_from_state(state: Dict[str, Any]) -> Dict[str, List[str]]:
    summary = state.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    return {
        "last_scene": _summary_list(summary.get("last_scene")),
        "chapter_so_far": _summary_list(summary.get("chapter_so_far")),
        "story_so_far": _summary_list(summary.get("story_so_far")),
        "key_facts_ring": _summary_list(summary.get("key_facts_ring")),
        "must_stay_true": _summary_list(summary.get("must_stay_true")),
    }


def _merge_summary_update(state: Dict[str, Any], summary_update: Dict[str, Any]) -> None:
    summary = _summary_from_state(state)

    last_scene = _summary_list(summary_update.get("last_scene"))
    if last_scene:
        summary["last_scene"] = last_scene

    chapter_add = _summary_list(summary_update.get("chapter_so_far_add"))
    if chapter_add:
        summary["chapter_so_far"] = (summary.get("chapter_so_far", []) + chapter_add)[-SUMMARY_CHAPTER_SO_FAR_CAP:]

    story_add = _summary_list(summary_update.get("story_so_far_add"))
    if story_add:
        summary["story_so_far"] = (summary.get("story_so_far", []) + story_add)[-SUMMARY_STORY_SO_FAR_CAP:]

    key_events = _summary_list(summary_update.get("key_events"))
    must_stay_true = _summary_list(summary_update.get("must_stay_true"))
    if key_events or must_stay_true:
        ring = summary.get("key_facts_ring", []) + key_events + must_stay_true
        summary["key_facts_ring"] = _dedupe_preserve(ring)[-SUMMARY_KEY_FACTS_CAP:]

    if must_stay_true:
        merged_invariants = summary.get("must_stay_true", []) + must_stay_true
        summary["must_stay_true"] = _dedupe_preserve(merged_invariants)[-SUMMARY_MUST_STAY_TRUE_CAP:]

    state["summary"] = summary


def _contains_any(text: str, terms: List[str]) -> bool:
    for term in terms:
        if not term:
            continue
        if " " in term:
            if term in text:
                return True
        else:
            if re.search(r"\b" + re.escape(term) + r"\b", text):
                return True
    return False


def _heuristic_invariant_issues(
    prose: str,
    summary_update: Dict[str, Any],
    invariants: List[str],
) -> List[Dict[str, Any]]:
    if not invariants:
        return []
    prose_lower = prose.lower()
    observed = prose_lower
    summary_bits: List[str] = []
    for key in ("last_scene", "key_events", "must_stay_true", "chapter_so_far_add", "story_so_far_add"):
        items = summary_update.get(key)
        if isinstance(items, list):
            summary_bits.extend([str(item) for item in items if str(item).strip()])
    if summary_bits:
        observed += " " + " ".join([item.lower() for item in summary_bits])

    objects = ["shard", "blade", "sword", "knife", "dagger", "map", "canister", "oath", "mark"]
    presence = ["present", "here", "carried", "carry", "carrying", "held", "holds", "has", "in his pack", "in his satchel", "on his person"]
    absence = ["gone", "missing", "lost", "destroyed", "shattered", "dissolved", "vanished", "consumed", "erased"]
    physical = ["physical", "solid", "tangible", "carryable"]
    embedded = ["embedded", "bound", "fused", "absorbed", "within him", "in his body", "in his chest"]
    alive = ["alive", "living", "breathing"]
    dead = ["dead", "killed", "slain", "corpse"]

    issues: List[Dict[str, Any]] = []
    for invariant in invariants:
        inv_text = str(invariant).strip().lower()
        if not inv_text:
            continue
        relevant_objects = [obj for obj in objects if obj in inv_text]
        if not relevant_objects:
            continue
        for obj in relevant_objects:
            if obj not in observed:
                continue
            if _contains_any(inv_text, presence) and _contains_any(observed, absence):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests present, prose suggests absent.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, absence) and _contains_any(observed, presence):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests absent, prose suggests present.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, physical) and _contains_any(observed, embedded):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests physical, prose suggests embedded.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, embedded) and _contains_any(observed, physical):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests embedded, prose suggests physical.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, alive) and _contains_any(observed, dead):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests alive, prose suggests dead.",
                    "severity": "error",
                })
                continue
            if _contains_any(inv_text, dead) and _contains_any(observed, alive):
                issues.append({
                    "code": "invariant_contradiction",
                    "message": f"Possible contradiction for '{obj}': invariant suggests dead, prose suggests alive.",
                    "severity": "error",
                })
                continue

    milestone_patterns = {
        "shard_bind": [
            r"\bbind(?:s|ing|ed)?\b.{0,40}\bshard\b",
            r"\bshard\b.{0,40}\bbind(?:s|ing|ed)?\b",
            r"\boath\b.{0,40}\bfilament\b",
        ],
        "maps_acquired": [
            r"\bmap(?:s)?\b.{0,40}\b(acquire|acquired|retrieve|retrieved|unfurl|unfurled|take|took|get|got)\b",
            r"\b(acquire|retriev|unfurl|take|get)\w*\b.{0,40}\bmap(?:s)?\b",
            r"\bchart(?:s)?\b",
            r"\bstar[- ]?map\b",
        ],
        "shadow_form_first": [
            r"\bshadow[- ]?form\b",
            r"\bshadow\b.{0,20}\bforms\b",
        ],
    }

    milestones: List[tuple[str, str]] = []
    for invariant in invariants:
        match = re.search(r"milestone\s*:\s*([a-z0-9_\- ]+)\s*=\s*(done|not_yet)", str(invariant), re.IGNORECASE)
        if not match:
            continue
        key = match.group(1).strip().lower().replace("-", "_").replace(" ", "_")
        status = match.group(2).upper()
        if key:
            milestones.append((key, status))

    for key, status in milestones:
        patterns = milestone_patterns.get(key)
        if not patterns:
            token = key.replace("_", " ")
            if token:
                patterns = [r"\b" + re.escape(token) + r"\b"]
        hit = False
        for pattern in patterns or []:
            if re.search(pattern, prose_lower):
                hit = True
                break
        if not hit:
            continue
        if status == "DONE":
            issues.append({
                "code": "milestone_duplicate",
                "message": f"Milestone '{key}' is DONE but appears to be depicted again.",
                "severity": "warning",
            })
        elif status == "NOT_YET":
            issues.append({
                "code": "milestone_future",
                "message": f"Milestone '{key}' is NOT_YET but appears to be depicted early.",
                "severity": "warning",
            })

    invariant_text = " ".join([str(item).lower() for item in invariants])
    if "right" in invariant_text and re.search(r"\bleft\s+(arm|forearm|hand)\b.{0,40}\b(scar|mark|filament|oath|sigil)\b", prose_lower):
        issues.append({
            "code": "arm_side_mismatch",
            "message": "Possible arm-side mismatch: invariants mention right-side mark but prose mentions left-side mark.",
            "severity": "warning",
        })
    if "left" in invariant_text and re.search(r"\bright\s+(arm|forearm|hand)\b.{0,40}\b(scar|mark|filament|oath|sigil)\b", prose_lower):
        issues.append({
            "code": "arm_side_mismatch",
            "message": "Possible arm-side mismatch: invariants mention left-side mark but prose mentions right-side mark.",
            "severity": "warning",
        })

    if "longsword" in invariant_text:
        if any(term in prose_lower for term in ["short-blade", "short blade", "dagger", "knife"]) and "longsword" not in prose_lower:
            issues.append({
                "code": "inventory_mismatch",
                "message": "Possible weapon mismatch: invariants mention longsword but prose emphasizes a different blade.",
                "severity": "warning",
            })
    if any(term in invariant_text for term in ["short-blade", "short blade", "dagger", "knife"]):
        if "longsword" in prose_lower and not any(term in prose_lower for term in ["short-blade", "short blade", "dagger", "knife"]):
            issues.append({
                "code": "inventory_mismatch",
                "message": "Possible weapon mismatch: invariants mention short blade but prose emphasizes a longsword.",
                "severity": "warning",
            })

    mojibake_markers = ["\ufffd", "\u00c3", "\u00c2", "\u00e2\u0080\u0094", "\u00e2\u0080\u0099", "\u00e2\u0080\u009c", "\u00e2\u0080\u009d"]
    if any(marker in prose for marker in mojibake_markers):
        issues.append({
            "code": "encoding_mojibake",
            "message": "Possible encoding/mojibake artifacts detected in prose output.",
            "severity": "warning",
        })

    return issues


def _rollup_chapter_summary(book_root: Path, state: Dict[str, Any], chapter_num: int) -> None:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}"
    if not chapter_dir.exists():
        return

    key_events: List[str] = []
    must_stay_true: List[str] = []
    for meta_path in sorted(chapter_dir.glob("scene_*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        key_events.extend(_summary_list(meta.get("key_events")))
        must_stay_true.extend(_summary_list(meta.get("must_stay_true")))

    summary = _summary_from_state(state)
    chapter_summary = _dedupe_preserve(key_events + must_stay_true)
    if chapter_summary:
        summary["story_so_far"] = (summary.get("story_so_far", []) + chapter_summary)[-SUMMARY_STORY_SO_FAR_CAP:]
    summary["chapter_so_far"] = []
    state["summary"] = summary

    summaries_dir = book_root / "draft" / "context" / "chapter_summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summaries_dir / f"ch_{chapter_num:03d}.json"
    payload = {
        "chapter": chapter_num,
        "key_events": _dedupe_preserve(key_events),
        "must_stay_true": _dedupe_preserve(must_stay_true),
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _find_chapter_outline(outline: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
    chapters = outline.get("chapters", []) if isinstance(outline, dict) else []
    if isinstance(chapters, list):
        for entry in chapters:
            if not isinstance(entry, dict):
                continue
            chapter_id = entry.get("chapter_id")
            try:
                chapter_id_int = int(chapter_id)
            except (TypeError, ValueError):
                continue
            if chapter_id_int == chapter_num:
                return entry
    return {}


def _section_title(section: Dict[str, Any], index: int) -> str:
    title = str(section.get("title", "")).strip()
    if title:
        return title
    return f"Section {index}"


def _scene_id_from_obj(scene_obj: Dict[str, Any], fallback: int) -> int:
    for key in ("scene_id", "beat_id", "id"):
        value = scene_obj.get(key)
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return fallback


def _compile_chapter_markdown(book_root: Path, outline: Dict[str, Any], chapter_num: int) -> Path:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    chapter = _find_chapter_outline(outline, chapter_num)
    chapter_title = str(chapter.get("title", "")).strip() if chapter else ""
    if chapter_title:
        header = f"Chapter {chapter_num}: {chapter_title}"
    else:
        header = f"Chapter {chapter_num}"

    sections = chapter.get("sections", []) if isinstance(chapter, dict) else []
    if not isinstance(sections, list) or not sections:
        fallback_scenes = []
        if isinstance(chapter, dict):
            raw = chapter.get("scenes") or chapter.get("beats") or []
            if isinstance(raw, list):
                fallback_scenes = raw
        sections = [{"section_id": 1, "title": "", "scenes": fallback_scenes}]

    blocks: List[str] = [f"# {header}"]
    for idx_section, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            continue
        blocks.append(f"## {_section_title(section, idx_section)}")
        scenes = section.get("scenes", [])
        if not isinstance(scenes, list):
            scenes = []
        if not scenes:
            blocks.append("[No scenes listed for this section]")
            continue
        for idx_scene, scene_obj in enumerate(scenes, start=1):
            scene_id = _scene_id_from_obj(scene_obj, idx_scene)
            scene_path = chapter_dir / f"scene_{scene_id:03d}.md"
            if scene_path.exists():
                scene_text = scene_path.read_text(encoding="utf-8").strip()
                blocks.append(scene_text)
            else:
                blocks.append(f"[Missing scene {scene_id:03d}]")

    compiled = "\n\n".join([block for block in blocks if str(block).strip()]) + "\n"

    chapter_file = book_root / "draft" / "chapters" / f"ch_{chapter_num:03d}.md"
    chapter_file.write_text(compiled, encoding="utf-8")
    return chapter_file


def _cursor_beyond_target(
    chapter: int,
    scene: int,
    target: Tuple[Optional[int], Optional[int]],
    scene_counts: Dict[int, int],
) -> bool:
    target_chapter, target_scene = target
    if target_chapter is None:
        return False
    if chapter > target_chapter:
        return True
    if chapter < target_chapter:
        return False
    if target_scene is None:
        target_scene = scene_counts.get(target_chapter, 0)
    if target_scene <= 0:
        return False
    return scene > target_scene


def _advance_cursor(
    chapter_order: List[int],
    scene_counts: Dict[int, int],
    chapter: int,
    scene: int,
) -> Tuple[int, int, bool]:
    total_scenes = scene_counts.get(chapter, 0)
    if total_scenes and scene < total_scenes:
        return chapter, scene + 1, False
    if chapter in chapter_order:
        index = chapter_order.index(chapter)
        if index + 1 < len(chapter_order):
            return chapter_order[index + 1], 1, False
    return chapter + 1, 1, True


def _existing_scene_card(state: Dict[str, Any], book_root: Path) -> Optional[Path]:
    plan_data = state.get("plan", {}) if isinstance(state.get("plan"), dict) else {}
    rel_path = plan_data.get("scene_card")
    if not rel_path:
        return None
    path = book_root / rel_path
    if not path.exists():
        return None

    cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
    chapter = int(cursor.get("chapter", 0) or 0)
    scene = int(cursor.get("scene", 0) or 0)
    try:
        card = _load_json(path)
    except Exception:
        return None
    card_chapter = int(card.get("chapter", 0) or 0)
    card_scene = int(card.get("scene", 0) or 0)
    if chapter and scene and (card_chapter != chapter or card_scene != scene):
        return None
    return path



def _author_fragment_path(workspace: Path, author_ref: str) -> Path:
    parts = [part for part in author_ref.split("/") if part]
    if len(parts) != 2:
        raise ValueError("author_ref must look like <author_slug>/vN")
    return workspace / "authors" / parts[0] / parts[1] / "system_fragment.md"


def _maybe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _log_scope(book_root: Path, scene_card: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scope: Dict[str, Any] = {"book_id": book_root.name}
    if scene_card:
        chapter = _maybe_int(scene_card.get("chapter"))
        if chapter is not None:
            scope["chapter"] = chapter
        scene = _maybe_int(scene_card.get("scene"))
        if scene is not None:
            scope["scene"] = scene
    return scope


def _chat(
    workspace: Path,
    label: str,
    client: LLMClient,
    messages: List[Message],
    model: str,
    temperature: float,
    max_tokens: int,
    log_extra: Optional[Dict[str, Any]] = None,
) -> LLMResponse:
    key_slot = getattr(client, "key_slot", None)
    merged_extra: Dict[str, Any] = {}
    if log_extra:
        merged_extra.update(log_extra)
    if key_slot:
        merged_extra["key_slot"] = key_slot
    extra = merged_extra or None
    request = {"model": model, "temperature": temperature, "max_tokens": max_tokens}
    retries = _empty_response_retries()
    attempt = 0
    while True:
        try:
            response = client.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        except LLMRequestError as exc:
            if should_log_llm():
                log_llm_error(workspace, f"{label}_error", exc, request=request, messages=messages, extra=extra)
            raise
        label_used = label if attempt == 0 else f"{label}_retry{attempt}"
        if should_log_llm():
            log_llm_response(workspace, label_used, response, request=request, messages=messages, extra=extra)
        if str(response.text).strip() or attempt >= retries:
            return response
        attempt += 1



def _fallback_style_anchor(author_fragment: str) -> str:
    cleaned = re.sub(r"^You are [^.]+\.\s*", "", author_fragment, flags=re.IGNORECASE).strip()
    if cleaned:
        return cleaned
    return "Write in tight third-person limited with concrete sensory detail and forward motion."


def _ensure_style_anchor(
    workspace: Path,
    book_root: Path,
    book: Dict[str, Any],
    system_path: Path,
    client: LLMClient,
    model: str,
) -> str:
    anchor_path = style_anchor_path(book_root)
    existing = load_style_anchor(anchor_path)
    if existing.strip():
        return existing
    author_ref = str(book.get("author_ref", ""))
    fragment_path = _author_fragment_path(workspace, author_ref)
    if not fragment_path.exists():
        raise FileNotFoundError(f"Author fragment not found: {fragment_path}")
    author_fragment = fragment_path.read_text(encoding="utf-8")

    template = _resolve_template(book_root, "style_anchor.md")
    prompt = render_template_file(
        template,
        {
            "author_fragment": author_fragment,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "style_anchor",
        client,
        messages,
        model=model,
        temperature=0.7,
        max_tokens=_style_anchor_max_tokens(),
        log_extra=_log_scope(book_root),
    )
    text = response.text.strip()
    if not text:
        retry_prompt = (
            prompt
            + "\n\nOutput must be non-empty and 200-400 words."
            + " If you are unsure, write 8-12 sentences of neutral prose with no names."
        )
        retry_messages: List[Message] = [
            {"role": "system", "content": system_path.read_text(encoding="utf-8")},
            {"role": "user", "content": retry_prompt},
        ]
        response = _chat(
            workspace,
            "style_anchor_retry",
            client,
            retry_messages,
            model=model,
            temperature=0.7,
            max_tokens=_style_anchor_max_tokens(),
            log_extra=_log_scope(book_root),
        )
        text = response.text.strip()
    if not text:
        text = _fallback_style_anchor(author_fragment)
    if not text:
        raise ValueError("Style anchor generation returned empty output.")
    save_style_anchor(anchor_path, text)
    return text


def _generate_continuity_pack(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "continuity_pack.md")
    recent_facts = state.get("world", {}).get("recent_facts", [])
    prompt = render_template_file(
        template,
        {
            "state": state,
            "summary": _summary_from_state(state),
            "recent_facts": recent_facts,
            "scene_card": scene_card,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "continuity_pack",
        client,
        messages,
        model=model,
        temperature=0.4,
        max_tokens=_continuity_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    data = _extract_json(response.text)
    data = _normalize_continuity_pack(data, scene_card, thread_registry)
    data["summary"] = _summary_from_state(state)
    pack = ContinuityPack.from_dict(data)
    save_continuity_pack(continuity_pack_path(book_root), pack)
    return pack.to_dict()


def _write_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    scene_card: Dict[str, Any],
    continuity_pack: Dict[str, Any],
    state: Dict[str, Any],
    style_anchor: str,
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Tuple[str, Dict[str, Any]]:
    template = _resolve_template(book_root, "write.md")
    prompt = render_template_file(
        template,
        {
            "scene_card": scene_card,
            "continuity_pack": continuity_pack,
            "state": state,
            "style_anchor": style_anchor,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": load_system_prompt(system_path, book_root / "outline" / "outline.json", include_outline=True)},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "write_scene",
        client,
        messages,
        model=model,
        temperature=0.7,
        max_tokens=_write_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    try:
        prose, patch = _extract_prose_and_patch(response.text)
    except ValueError as exc:
        extra = ""
        if _response_truncated(response):
            extra = f" Model output hit MAX_TOKENS ({_write_max_tokens()}); increase BOOKFORGE_WRITE_MAX_TOKENS."
        raise ValueError(f"{exc}{extra}") from exc

    _coerce_summary_update(patch)
    validate_json(patch, "state_patch")
    return prose, patch


def _lint_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    state: Dict[str, Any],
    patch: Dict[str, Any],
    scene_card: Dict[str, Any],
    invariants: List[str],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "lint.md")
    prompt = render_template_file(
        template,
        {
            "prose": prose,
            "state": state,
            "summary": _summary_from_state(state),
            "invariants": invariants,
            "character_states": character_states,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "lint_scene",
        client,
        messages,
        model=model,
        temperature=0.0,
        max_tokens=_lint_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    report = _extract_json(response.text)
    report = _normalize_lint_report(report)
    summary_update = patch.get("summary_update") if isinstance(patch, dict) else {}
    if not isinstance(summary_update, dict):
        summary_update = {}
    heuristic_issues = _heuristic_invariant_issues(prose, summary_update, invariants)
    if heuristic_issues:
        report["issues"] = list(report.get("issues", [])) + heuristic_issues
        report["status"] = "fail"
        report.setdefault("mode", "heuristic")
    validate_json(report, "lint_report")
    return report


def _repair_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    lint_report: Dict[str, Any],
    state: Dict[str, Any],
    scene_card: Dict[str, Any],
    character_registry: List[Dict[str, str]],
    thread_registry: List[Dict[str, str]],
    character_states: List[Dict[str, Any]],
    client: LLMClient,
    model: str,
) -> Tuple[str, Dict[str, Any]]:
    template = _resolve_template(book_root, "repair.md")
    prompt = render_template_file(
        template,
        {
            "issues": lint_report.get("issues", []),
            "prose": prose,
            "state": state,
            "scene_card": scene_card,
            "character_registry": character_registry,
            "thread_registry": thread_registry,
            "character_states": character_states,
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": load_system_prompt(system_path, book_root / "outline" / "outline.json", include_outline=True)},
        {"role": "user", "content": prompt},
    ]

    response = _chat(
        workspace,
        "repair_scene",
        client,
        messages,
        model=model,
        temperature=0.4,
        max_tokens=_repair_max_tokens(),
        log_extra=_log_scope(book_root, scene_card),
    )

    try:
        prose, patch = _extract_prose_and_patch(response.text)
    except ValueError as exc:
        extra = ""
        if _response_truncated(response):
            extra = f" Model output hit MAX_TOKENS ({_repair_max_tokens()}); increase BOOKFORGE_REPAIR_MAX_TOKENS."
        raise ValueError(f"{exc}{extra}") from exc

    _coerce_summary_update(patch)
    validate_json(patch, "state_patch")
    return prose, patch


def _apply_state_patch(state: Dict[str, Any], patch: Dict[str, Any], chapter_end: bool = False) -> Dict[str, Any]:
    world_updates = patch.get("world_updates")
    if world_updates is None and isinstance(patch.get("world"), dict):
        world_updates = patch.get("world")
    if isinstance(world_updates, dict):
        world = state.get("world", {}) if isinstance(state.get("world", {}), dict) else {}
        for key, value in world_updates.items():
            world[key] = value
        state["world"] = world

    thread_updates = patch.get("thread_updates")
    if isinstance(thread_updates, list):
        world = state.get("world", {}) if isinstance(state.get("world", {}), dict) else {}
        world["open_threads"] = thread_updates
        state["world"] = world

    summary_update = patch.get("summary_update")
    if isinstance(summary_update, dict):
        if not chapter_end and "story_so_far_add" in summary_update:
            summary_update = dict(summary_update)
            summary_update.pop("story_so_far_add", None)
        _merge_summary_update(state, summary_update)
    else:
        if "summary" not in state:
            state["summary"] = _summary_from_state(state)

    delta = patch.get("duplication_warnings_in_row_delta")
    if isinstance(delta, int):
        current = int(state.get("duplication_warnings_in_row", 0) or 0)
        state["duplication_warnings_in_row"] = max(0, current + delta)

    return state


def _apply_character_updates(book_root: Path, patch: Dict[str, Any], chapter_num: int, scene_num: int) -> None:
    updates = patch.get("character_updates") if isinstance(patch, dict) else None
    if not isinstance(updates, list):
        return
    characters_dir = book_root / "draft" / "context" / "characters"
    characters_dir.mkdir(parents=True, exist_ok=True)
    for update in updates:
        if not isinstance(update, dict):
            continue
        char_id = str(update.get("character_id") or "").strip()
        if not char_id:
            continue
        slug = _character_slug(char_id)
        state_path = characters_dir / f"{slug}.state.json"
        state: Dict[str, Any] = {
            "schema_version": "1.0",
            "character_id": char_id,
            "inventory": [],
            "containers": [],
            "invariants": [],
            "history": [],
        }
        if state_path.exists():
            try:
                loaded = json.loads(state_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    state.update(loaded)
            except json.JSONDecodeError:
                pass

        chapter = int(update.get("chapter", chapter_num) or chapter_num)
        scene = int(update.get("scene", scene_num) or scene_num)

        inventory = update.get("inventory")
        if isinstance(inventory, list):
            state["inventory"] = inventory
        containers = update.get("containers")
        if isinstance(containers, list):
            state["containers"] = containers

        invariants_add = update.get("invariants_add")
        if isinstance(invariants_add, list):
            existing = state.get("invariants", [])
            if not isinstance(existing, list):
                existing = []
            combined = existing + [str(item) for item in invariants_add if str(item).strip()]
            deduped = []
            seen = set()
            for item in combined:
                key = str(item).strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                deduped.append(item)
            state["invariants"] = deduped

        history_entry: Dict[str, Any] = {"chapter": chapter, "scene": scene, "changes": []}
        persona_updates = update.get("persona_updates")
        if isinstance(persona_updates, list):
            history_entry["persona_updates"] = [str(item) for item in persona_updates if str(item).strip()]
        notes = update.get("notes")
        if isinstance(notes, str) and notes.strip():
            history_entry["notes"] = notes.strip()
        if isinstance(inventory, list):
            history_entry["changes"].append("inventory_updated")
        if isinstance(containers, list):
            history_entry["changes"].append("containers_updated")
        if history_entry.get("persona_updates") or history_entry.get("notes") or history_entry.get("changes"):
            history = state.get("history", [])
            if not isinstance(history, list):
                history = []
            history.append(history_entry)
            state["history"] = history

        state["updated_at"] = _now_iso()
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")



def _update_bible(book_root: Path, patch: Dict[str, Any]) -> None:
    world_updates = patch.get("world_updates")
    if not isinstance(world_updates, dict):
        return
    recent_facts = world_updates.get("recent_facts")
    if not isinstance(recent_facts, list):
        return
    lines = [str(item).strip() for item in recent_facts if str(item).strip()]
    if not lines:
        return
    bible_path = book_root / "draft" / "context" / "bible.md"
    existing = ""
    if bible_path.exists():
        existing = bible_path.read_text(encoding="utf-8")
    if existing and not existing.endswith("\n"):
        existing += "\n"
    update = "\n".join([f"- {item}" for item in lines]) + "\n"
    bible_path.write_text(existing + update, encoding="utf-8")


def _write_scene_files(
    book_root: Path,
    chapter: int,
    scene: int,
    prose: str,
    scene_card: Dict[str, Any],
    patch: Dict[str, Any],
    lint_report: Dict[str, Any],
    write_attempts: int,
) -> Path:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    prose_path = chapter_dir / f"scene_{scene:03d}.md"
    if prose_path.exists():
        raise FileExistsError(f"Scene already exists: {prose_path}")
    prose_path.write_text(prose.strip() + "\n", encoding="utf-8")

    meta_path = chapter_dir / f"scene_{scene:03d}.meta.json"
    meta = dict(scene_card)
    meta["prose_path"] = prose_path.relative_to(book_root).as_posix()
    meta["state_patch"] = patch
    summary_update = patch.get("summary_update") if isinstance(patch, dict) else {}
    if not isinstance(summary_update, dict):
        summary_update = {}
    meta["scene_summary"] = _summary_list(summary_update.get("last_scene"))
    meta["key_events"] = _summary_list(summary_update.get("key_events"))
    meta["must_stay_true"] = _summary_list(summary_update.get("must_stay_true"))
    meta["threads_touched"] = _summary_list(summary_update.get("threads_touched"))
    meta["lint_report"] = lint_report
    meta["write_attempts"] = write_attempts
    meta["updated_at"] = _now_iso()
    meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")

    last_excerpt_path = book_root / "draft" / "context" / "last_excerpt.md"
    last_excerpt_path.write_text(prose.strip() + "\n", encoding="utf-8")

    return prose_path


def run_loop(
    workspace: Path,
    book_id: str,
    steps: Optional[int] = None,
    until: Optional[str] = None,
    resume: bool = False,
) -> None:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    book_path = book_root / "book.json"
    state_path = book_root / "state.json"
    outline_path = book_root / "outline" / "outline.json"
    system_path = book_root / "prompts" / "system_v1.md"

    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state.json: {state_path}")
    if not outline_path.exists():
        raise FileNotFoundError(f"Missing outline.json: {outline_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    book = _load_json(book_path)
    outline = _load_json(outline_path)
    validate_json(outline, "outline")

    chapter_order, scene_counts = _outline_summary(outline)
    character_registry = _build_character_registry(outline)
    thread_registry = _build_thread_registry(outline)
    if not chapter_order:
        raise ValueError("Outline is missing chapters; cannot run writer loop.")

    target = _parse_until(until)
    if steps is None and target == (None, None):
        steps_remaining: Optional[int] = 1
    else:
        steps_remaining = steps

    config = load_config()
    planner_client = get_llm_client(config, phase="planner")
    continuity_client = get_llm_client(config, phase="continuity")
    writer_client = get_llm_client(config, phase="writer")
    repair_client = get_llm_client(config, phase="repair")
    linter_client = get_llm_client(config, phase="linter")
    planner_model = resolve_model("planner", config)
    continuity_model = resolve_model("continuity", config)

    if not characters_ready(book_root):
        generate_characters(workspace=workspace, book_id=book_id)
    writer_model = resolve_model("writer", config)
    repair_model = resolve_model("repair", config)
    linter_model = resolve_model("linter", config)

    style_anchor = _ensure_style_anchor(
        workspace,
        book_root,
        book,
        system_path,
        writer_client,
        writer_model,
    )

    while True:
        state = _load_json(state_path)
        cursor = state.get("cursor", {}) if isinstance(state.get("cursor"), dict) else {}
        chapter = int(cursor.get("chapter", 0) or 0)
        scene = int(cursor.get("scene", 0) or 0)

        if chapter <= 0:
            chapter = chapter_order[0]
        if scene <= 0:
            scene = 1

        if _cursor_beyond_target(chapter, scene, target, scene_counts):
            break
        if steps_remaining is not None and steps_remaining <= 0:
            break

        scene_card_path = _existing_scene_card(state, book_root) if resume else None
        if scene_card_path is None:
            scene_card_path = plan_scene(
                workspace=workspace,
                book_id=book_id,
                client=planner_client,
                model=planner_model,
            )

        scene_card = _load_json(scene_card_path)
        validate_json(scene_card, "scene_card")

        state = _load_json(state_path)

        character_states = _load_character_states(book_root, scene_card)

        continuity_pack = _generate_continuity_pack(
            workspace,
            book_root,
            system_path,
            state,
            scene_card,
            character_registry,
            thread_registry,
            character_states,
            continuity_client,
            continuity_model,
        )

        base_invariants = book.get("invariants", []) if isinstance(book.get("invariants", []), list) else []
        summary = _summary_from_state(state)
        invariants = list(base_invariants)
        invariants += summary.get("must_stay_true", [])
        invariants += summary.get("key_facts_ring", [])

        prose, patch = _write_scene(
            workspace,
            book_root,
            system_path,
            scene_card,
            continuity_pack,
            state,
            style_anchor,
            character_registry,
            thread_registry,
            character_states,
            writer_client,
            writer_model,
        )

        lint_mode = _lint_mode()

        if lint_mode == "off":
            lint_report = {"schema_version": "1.0", "status": "pass", "issues": [], "mode": "off"}
        else:
            lint_report = _lint_scene(
                workspace,
                book_root,
                system_path,
                prose,
                state,
                patch,
                scene_card,
                invariants,
                character_states,
                linter_client,
                linter_model,
            )

        write_attempts = 1
        if lint_mode != "off" and lint_report.get("status") == "fail":
            prose, patch = _repair_scene(
                workspace,
                book_root,
                system_path,
                prose,
                lint_report,
                state,
                scene_card,
                character_registry,
                thread_registry,
                character_states,
                repair_client,
                repair_model,
            )
            write_attempts += 1
            lint_report = _lint_scene(
                workspace,
                book_root,
                system_path,
                prose,
                state,
                patch,
                scene_card,
                invariants,
                character_states,
                linter_client,
                linter_model,
            )
            if lint_report.get("status") == "fail" and lint_mode == "strict":
                raise ValueError("Lint failed after repair; see lint logs for details.")

        chapter_num = int(scene_card.get("chapter", chapter))
        scene_num = int(scene_card.get("scene", scene))
        chapter_total = scene_counts.get(chapter_num)
        chapter_end = isinstance(chapter_total, int) and chapter_total > 0 and scene_num >= chapter_total

        state = _apply_state_patch(state, patch, chapter_end=chapter_end)
        _apply_character_updates(book_root, patch, chapter_num, scene_num)

        cursor_override = patch.get("cursor_advance") if isinstance(patch.get("cursor_advance"), dict) else None
        if cursor_override:
            next_chapter = int(cursor_override.get("chapter", chapter_num) or chapter_num)
            next_scene = int(cursor_override.get("scene", scene_num + 1) or (scene_num + 1))
            completed = False
        else:
            next_chapter, next_scene, completed = _advance_cursor(
                chapter_order,
                scene_counts,
                chapter_num,
                scene_num,
            )

        _write_scene_files(
            book_root,
            chapter_num,
            scene_num,
            prose,
            scene_card,
            patch,
            lint_report,
            write_attempts,
        )

        _update_bible(book_root, patch)

        if chapter_end:
            _rollup_chapter_summary(book_root, state, chapter_num)
            _compile_chapter_markdown(book_root, outline, chapter_num)

        state["cursor"] = {"chapter": next_chapter, "scene": next_scene}
        if completed:
            state["status"] = "COMPLETE"
        else:
            state["status"] = "DRAFTING"

        validate_json(state, "state")
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

        if steps_remaining is not None:
            steps_remaining -= 1


def run() -> None:
    raise NotImplementedError("Use run_loop via CLI.")
