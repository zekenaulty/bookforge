from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import logging
import shutil
from jsonschema import Draft202012Validator

from bookforge.config.env import load_config, read_int_env
from bookforge.llm.client import LLMClient
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message
from bookforge.llm.errors import LLMRequestError
from bookforge.prompt.renderer import render_template_file
from bookforge.util.paths import repo_root
from bookforge.util.json_extract import extract_json
from bookforge.util.schema import validate_json


OUTLINE_SCHEMA_VERSION = "1.1"
OUTLINE_PHASE_ORDER = [
    "phase_01_chapter_spine",
    "phase_02_section_architecture",
    "phase_03_scene_draft",
    "phase_04_transition_causality_refinement",
    "phase_05_cast_function_refinement",
    "phase_06_thread_payoff_refinement",
]
OUTLINE_PHASE_IDS = set(OUTLINE_PHASE_ORDER)

OUTLINE_PHASE_TEMPLATE_BY_ID = {
    "phase_01_chapter_spine": "outline_phase_01_chapter_spine.md",
    "phase_02_section_architecture": "outline_phase_02_section_architecture.md",
    "phase_03_scene_draft": "outline_phase_03_scene_draft.md",
    "phase_04_transition_causality_refinement": "outline_phase_04_transition_causality_refinement.md",
    "phase_05_cast_function_refinement": "outline_phase_05_cast_function_refinement.md",
    "phase_06_thread_payoff_refinement": "outline_phase_06_thread_payoff_refinement.md",
}

OUTLINE_PHASE_BLOCK_FALLBACK = {
    "phase_01_chapter_spine": "resources/prompt_blocks/phase/outline_pipeline/phase_01_chapter_spine_prompt_contract.md",
    "phase_02_section_architecture": "resources/prompt_blocks/phase/outline_pipeline/phase_02_section_architecture_prompt_contract.md",
    "phase_03_scene_draft": "resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md",
    "phase_04_transition_causality_refinement": "resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md",
    "phase_05_cast_function_refinement": "resources/prompt_blocks/phase/outline_pipeline/phase_05_cast_function_refinement_prompt_contract.md",
    "phase_06_thread_payoff_refinement": "resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md",
}

OUTLINE_SYSTEM_BLOCK_FALLBACK = (
    "resources/prompt_blocks/phase/outline_pipeline/outline_system_execution_contract.md"
)

OUTLINE_PIPELINE_MAX_ATTEMPTS = 2
OUTLINE_PIPELINE_PAUSE_MARKER = "pipeline_run_paused.json"
OUTLINE_PIPELINE_HISTORY = "phase_history.json"
OUTLINE_PIPELINE_LATEST = "pipeline_latest.json"
OUTLINE_PIPELINE_LATEST_ALIAS = "outline_pipeline_latest.json"
OUTLINE_PIPELINE_REPORT_LATEST = "outline_pipeline_report_latest.json"
OUTLINE_PIPELINE_REPORT_LATEST_SNAPSHOT = "outline_pipeline_report_latest.snapshot.json"

OUTLINE_PHASE_HANDOFF_KEY = {
    "phase_01_chapter_spine": "outline_spine_v1",
    "phase_02_section_architecture": "outline_sections_v1",
    "phase_03_scene_draft": "outline_draft_v1_1",
    "phase_04_transition_causality_refinement": "outline_transitions_refined_v1_1",
    "phase_05_cast_function_refinement": "outline_cast_refined_v1_1",
    "phase_06_thread_payoff_refinement": "outline_final_v1_1",
}

OUTLINE_PHASE_HANDOFF_FILE = {
    "phase_01_chapter_spine": "outline_spine_v1.json",
    "phase_02_section_architecture": "outline_sections_v1.json",
    "phase_03_scene_draft": "outline_draft_v1_1.json",
    "phase_04_transition_causality_refinement": "outline_transitions_refined_v1_1.json",
    "phase_05_cast_function_refinement": "outline_cast_refined_v1_1.json",
    "phase_06_thread_payoff_refinement": "outline_final_v1_1.json",
}

OUTLINE_WRAPPER_SCHEMA_BY_PHASE = {
    "phase_04_transition_causality_refinement": "transition_refine_v1",
    "phase_05_cast_function_refinement": "cast_refine_v1",
}

OPTIONAL_EDGE_FIELDS = {
    "transition_in",
    "transition_out",
    "transition_out_text",
    "edge_intent",
    "consumes_outcome_from",
    "hands_off_to",
}

TRANSITION_REQUIRED_SCENE_FIELDS = {
    "location_start_label",
    "location_end_label",
    "location_start_id",
    "location_end_id",
    "location_start",
    "location_end",
    "handoff_mode",
    "constraint_state",
    "transition_in_text",
    "transition_in_anchors",
}

TRANSITION_OUT_REQUIRED_FIELDS = {
    "transition_out_text",
    "transition_out_anchors",
}

SEAM_REQUIRED_SCENE_FIELDS = {
    "seam_score",
    "seam_resolution",
}

HANDOFF_MODE_VALUES = {
    "direct_continuation",
    "escorted_transfer",
    "detained_then_release",
    "time_skip",
    "hard_cut",
    "montage",
    "offscreen_processing",
    "combat_disengage",
    "arrival_checkpoint",
    "aftermath_relocation",
}

CONSTRAINT_STATE_VALUES = {
    "free",
    "pursued",
    "detained",
    "processed",
    "sheltered",
    "restricted",
    "engaged_combat",
    "fleeing",
}

SEAM_RESOLUTION_VALUES = {
    "inline_bridge",
    "micro_scene",
    "full_scene",
}

BLOCKED_BY_BUDGET_ATTENTION_THRESHOLD = 70

SEAM_INLINE_MAX_SCORE = 24
SEAM_MICRO_MAX_SCORE = 54
SEAM_MICRO_MIN_SCORE = 25

CONSTRAINED_STATES = {
    "pursued",
    "detained",
    "processed",
    "restricted",
    "engaged_combat",
    "fleeing",
}

SETTLED_STATES = {"free", "sheltered"}

HIGH_PRESSURE_SCENE_TYPES = {"action", "escalation", "choice"}
LOW_PRESSURE_SCENE_TYPES = {"aftermath", "setup", "transition"}

MAJOR_TURN_KEYWORDS = (
    "scan",
    "detain",
    "capture",
    "bounty",
    "curse",
    "anomaly",
    "contract",
    "duel",
    "injury",
)

REF_PATTERN = re.compile(r"^[1-9][0-9]*:[1-9][0-9]*$")
LOCATION_ID_PATTERN = re.compile(r"^LOC_[A-Z0-9_]+$")
PLACEHOLDER_TOKEN_PATTERN = re.compile(r"\b(current_location|unknown|placeholder|tbd|here|there|n/?a)\b", re.IGNORECASE)
PLACEHOLDER_ANCHOR_PATTERN = re.compile(r"^anchor_[0-9]+$", re.IGNORECASE)

RETRYABLE_REASON_CODES = {
    "json_parse",
    "outline_schema",
    "transition_placeholder",
    "location_registry_missing",
    "phase_contract_invalid",
}

SUCCESSFUL_OUTLINE_STATUSES = {"SUCCESS", "SUCCESS_WITH_WARNINGS"}


@dataclass
class OutlinePhaseFailure(Exception):
    phase: str
    reasons: List[str]
    validator_evidence: List[Dict[str, Any]]

    def as_error_payload(self) -> Dict[str, Any]:
        return {
            "result": "ERROR",
            "schema_version": "error_v1",
            "phase": self.phase,
            "reasons": list(self.reasons),
            "validator_evidence": list(self.validator_evidence),
            "retryable": False,
        }

    def __str__(self) -> str:
        reason = "; ".join(self.reasons) if self.reasons else "Unknown phase failure."
        return f"{self.phase}: {reason}"

logger = logging.getLogger(__name__)

PREFERRED_CHAPTER_ROLES = {
    "hook",
    "setup",
    "pressure",
    "reversal",
    "revelation",
    "investigation",
    "journey",
    "trial",
    "alliance",
    "betrayal",
    "siege",
    "confrontation",
    "climax",
    "aftermath",
    "transition",
    "hinge",
}

PREFERRED_SCENE_TYPES = {
    "setup",
    "action",
    "reveal",
    "escalation",
    "choice",
    "consequence",
    "aftermath",
    "transition",
}

PREFERRED_TEMPOS = {
    "slow_burn",
    "steady",
    "rush",
}

PREFERRED_INTENSITY_RANGE = (1, 5)


MAX_ENUM_CONTEXT = 3
DEFAULT_JSON_RETRY_COUNT = 1

def _int_env(name: str, default: int) -> int:
    return read_int_env(name, default)


def _parse_scene_count_range(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if ":" not in raw:
        raise ValueError("Invalid --scene-count-range. Expected min:max.")
    left, right = raw.split(":", 1)
    try:
        minimum = int(left.strip())
        maximum = int(right.strip())
    except ValueError as exc:
        raise ValueError("Invalid --scene-count-range. Expected integer min:max.") from exc
    if minimum <= 0 or maximum <= 0:
        raise ValueError("Invalid --scene-count-range. Values must be positive integers.")
    if minimum > maximum:
        raise ValueError("Invalid --scene-count-range. min cannot exceed max.")
    return minimum, maximum


def _normalize_phase_selector(
    *,
    from_phase: Optional[str],
    to_phase: Optional[str],
    phase: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    normalized_from = str(from_phase).strip() if from_phase else None
    normalized_to = str(to_phase).strip() if to_phase else None
    normalized_single = str(phase).strip() if phase else None

    if normalized_single:
        if normalized_from or normalized_to:
            raise ValueError("--phase cannot be combined with --from-phase or --to-phase.")
        normalized_from = normalized_single
        normalized_to = normalized_single

    for label, candidate in (("from", normalized_from), ("to", normalized_to)):
        if candidate and candidate not in OUTLINE_PHASE_IDS:
            raise ValueError(f"Invalid --{label}-phase '{candidate}'.")

    if normalized_from and normalized_to:
        if OUTLINE_PHASE_ORDER.index(normalized_from) > OUTLINE_PHASE_ORDER.index(normalized_to):
            raise ValueError("--from-phase cannot be after --to-phase.")

    return normalized_from, normalized_to


def _outline_max_tokens() -> int:
    return _int_env("BOOKFORGE_OUTLINE_MAX_TOKENS", 98304)


def _json_retry_count() -> int:
    return max(0, _int_env("BOOKFORGE_JSON_RETRY_COUNT", DEFAULT_JSON_RETRY_COUNT))


def _response_truncated(response: LLMResponse) -> bool:
    raw = response.raw
    if not isinstance(raw, dict):
        return False
    candidates = raw.get("candidates", [])
    if not candidates:
        return False
    finish = candidates[0].get("finishReason")
    return str(finish).upper() == "MAX_TOKENS"



def _find_matching_bracket(payload: str, start_index: int) -> Optional[int]:
    depth = 0
    in_string = False
    escape = False

    for i in range(start_index, len(payload)):
        ch = payload[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                return i

    return None


def _append_missing_closers(payload: str) -> str:
    stack: List[str] = []
    in_string = False
    escape = False

    for ch in payload:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch in "{[":
            stack.append(ch)
            continue
        if ch in "}]":
            if not stack:
                continue
            opener = stack[-1]
            if (opener == "{" and ch == "}") or (opener == "[" and ch == "]"):
                stack.pop()

    if not stack:
        return payload

    closers = {"{": "}", "[": "]"}
    return payload + "".join(closers[ch] for ch in reversed(stack))


def _repair_outline_extra_chapters(payload: str) -> str:
    chapters_key = payload.find('"chapters"')
    if chapters_key == -1:
        return payload
    start = payload.find('[', chapters_key)
    if start == -1:
        return payload
    end = _find_matching_bracket(payload, start)
    if end is None:
        return payload

    remainder = payload[end + 1:]
    trimmed = remainder.lstrip()
    if not trimmed:
        return payload

    if trimmed.startswith('}'):
        tail = trimmed[1:].lstrip()
        if tail.startswith(']'):
            tail_after = tail[1:].lstrip()
            if re.match(r'^,\s*"(threads|characters)"', tail_after):
                after = remainder
                match = re.match(r'\s*}\s*]', after)
                if match:
                    after = after[match.end():]
                return payload[:end + 1] + after
        if re.match(r'^,\s*"(threads|characters)"', tail):
            after = remainder
            match = re.match(r'\s*}', after)
            if match:
                after = after[match.end():]
            return payload[:end + 1] + after

    probe = trimmed
    if probe.startswith('}'):
        probe = probe[1:].lstrip()

    if not re.match(r'^,\s*\{\s*"chapter_id"', probe):
        return payload

    after = remainder
    match = re.match(r'\s*}', after)
    if match:
        after = after[match.end():]
    return payload[:end] + after


def _repair_outline_json(payload: str) -> str:
    repaired = payload
    repaired = re.sub(r'}\]\}\]\s*,\s*"chapter_id"', r'}]}]}, {"chapter_id"', repaired)
    repaired = re.sub(r'}\]\}\]\s*,\s*"threads"', r'}]}]}], "threads"', repaired)
    repaired = re.sub(r'}\]\}\]\s*,\s*"characters"', r'}]}]}], "characters"', repaired)
    for _ in range(5):
        updated = _repair_outline_extra_chapters(repaired)
        if updated == repaired:
            break
        repaired = updated
    return _append_missing_closers(repaired)


def _add_enum_warning(collection: Dict[str, List[str]], value: str, context: str) -> None:
    contexts = collection.setdefault(value, [])
    if len(contexts) < MAX_ENUM_CONTEXT and context not in contexts:
        contexts.append(context)


def _format_enum_warnings(collection: Dict[str, List[str]]) -> str:
    parts: List[str] = []
    for value in sorted(collection.keys()):
        contexts = collection[value]
        if contexts:
            parts.append(f"{value} ({', '.join(contexts)})")
        else:
            parts.append(value)
    return "; ".join(parts)


def _warn_outline_enum_values(outline: Dict[str, Any]) -> None:
    chapters = outline.get("chapters")
    if not isinstance(chapters, list):
        return
    unknown_roles: Dict[str, List[str]] = {}
    unknown_tempos: Dict[str, List[str]] = {}
    unknown_scene_types: Dict[str, List[str]] = {}
    unknown_intensities: Dict[str, List[str]] = {}

    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = chapter.get("chapter_id", "?")
        role = chapter.get("chapter_role")
        if isinstance(role, str) and role and role not in PREFERRED_CHAPTER_ROLES:
            _add_enum_warning(unknown_roles, role, f"chapter {chapter_id}")

        pacing = chapter.get("pacing")
        if isinstance(pacing, dict):
            tempo = pacing.get("tempo")
            if isinstance(tempo, str) and tempo and tempo not in PREFERRED_TEMPOS:
                _add_enum_warning(unknown_tempos, tempo, f"chapter {chapter_id}")
            intensity = pacing.get("intensity")
            if isinstance(intensity, (int, float)):
                low, high = PREFERRED_INTENSITY_RANGE
                if intensity < low or intensity > high:
                    _add_enum_warning(unknown_intensities, str(intensity), f"chapter {chapter_id}")
            elif isinstance(intensity, str):
                try:
                    numeric = float(intensity)
                except ValueError:
                    _add_enum_warning(unknown_intensities, intensity, f"chapter {chapter_id}")
                else:
                    low, high = PREFERRED_INTENSITY_RANGE
                    if numeric < low or numeric > high:
                        _add_enum_warning(unknown_intensities, intensity, f"chapter {chapter_id}")
            elif intensity is not None:
                _add_enum_warning(unknown_intensities, str(intensity), f"chapter {chapter_id}")

        sections = chapter.get("sections")
        if not isinstance(sections, list):
            continue
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_id = section.get("section_id", "?")
            scenes = section.get("scenes")
            if not isinstance(scenes, list):
                continue
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_id = scene.get("scene_id", "?")
                scene_type = scene.get("type")
                if isinstance(scene_type, str) and scene_type and scene_type not in PREFERRED_SCENE_TYPES:
                    _add_enum_warning(
                        unknown_scene_types,
                        scene_type,
                        f"ch {chapter_id} sec {section_id} scene {scene_id}",
                    )

    if unknown_roles:
        logger.warning(
            "Outline uses non-standard chapter_role values: %s",
            _format_enum_warnings(unknown_roles),
        )
    if unknown_tempos:
        logger.warning(
            "Outline uses non-standard tempo values: %s",
            _format_enum_warnings(unknown_tempos),
        )
    if unknown_scene_types:
        logger.warning(
            "Outline uses non-standard scene type values: %s",
            _format_enum_warnings(unknown_scene_types),
        )
    if unknown_intensities:
        logger.warning(
            "Outline uses intensity values outside 1-5: %s",
            _format_enum_warnings(unknown_intensities),
        )


def _extract_json(text: str) -> Dict[str, Any]:
    data = extract_json(text, label="Outline response", repair_fn=_repair_outline_json)
    if not isinstance(data, dict):
        raise ValueError("Outline response JSON must be an object.")
    return data


def _extract_json_object_only(text: str, label: str) -> Dict[str, Any]:
    raw = str(text or "").strip()
    if not raw:
        raise ValueError(f"{label} response is empty.")
    if not (raw.startswith("{") and raw.endswith("}")):
        raise ValueError(f"{label} must be exactly one JSON object with no surrounding text.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} JSON parse failed: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} JSON must be an object.")
    return data




def _slugify(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s-]+", "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or "character"


def _ensure_character_ids(characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for idx, character in enumerate(characters, start=1):
        if not isinstance(character, dict):
            continue
        if not character.get("character_id"):
            name = str(character.get("name") or character.get("persona_name") or f"character_{idx}")
            character["character_id"] = f"CHAR_{_slugify(name)}"
    return characters


def _next_outline_version(outline_root: Path) -> int:
    highest = 0
    for path in outline_root.glob("outline_v*.json"):
        match = re.match(r"outline_v(\d+)\.json", path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def _archive_outline(outline_root: Path) -> None:
    outline_path = outline_root / "outline.json"
    if not outline_path.exists():
        return
    version = _next_outline_version(outline_root)
    outline_path.replace(outline_root / f"outline_v{version}.json")

    chapters_dir = outline_root / "chapters"
    if chapters_dir.exists():
        chapters_dir.replace(outline_root / f"chapters_v{version}")


def _resolve_outline_template(book_root: Path) -> Path:
    book_template = book_root / "prompts" / "templates" / "outline.md"
    if book_template.exists():
        return book_template
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / "outline.md"


def _has_drafted_scene_outputs(book_root: Path) -> bool:
    draft_chapters = book_root / "draft" / "chapters"
    if draft_chapters.exists():
        if any(draft_chapters.glob("ch_*/scene_*.md")):
            return True
        if any(draft_chapters.glob("ch_*/scene_*.meta.json")):
            return True

    phase_history = book_root / "draft" / "context" / "phase_history"
    if phase_history.exists():
        if any(phase_history.glob("ch*_sc*.json")):
            return True
        if any(path.is_dir() for path in phase_history.glob("ch*_sc*")):
            return True

    if (book_root / "draft" / "context" / "run_paused.json").exists():
        return True

    return False




def _read_prompt_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _write_outline_chapters(chapters_dir: Path, chapters: List[Dict[str, Any]]) -> None:
    chapters_dir.mkdir(parents=True, exist_ok=True)
    for idx, chapter in enumerate(chapters, start=1):
        path = chapters_dir / f"ch_{idx:03d}.json"
        path.write_text(json.dumps(chapter, ensure_ascii=True, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _phase_number(phase_id: str) -> int:
    return OUTLINE_PHASE_ORDER.index(phase_id) + 1


def _phase_prefix(phase_id: str) -> str:
    return f"phase_{_phase_number(phase_id):02d}"


def _phase_artifact_name(phase_id: str, kind: str, attempt: Optional[int] = None) -> str:
    prefix = _phase_prefix(phase_id)
    if kind == "attempt":
        if attempt is None:
            raise ValueError("Attempt number is required for attempt artifact names.")
        return f"{prefix}_attempt_{attempt}.raw.json"
    return f"{prefix}_{kind}.json"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relpath(base: Path, path: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _issue(
    code: str,
    message: str,
    *,
    path: Optional[str] = None,
    scene_ref: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"code": code, "message": message}
    if path:
        payload["path"] = path
    if scene_ref:
        payload["scene_ref"] = scene_ref
    return payload


def _collect_transition_hint_ids(payload: Any) -> List[str]:
    ids: List[str] = []
    if isinstance(payload, dict):
        maybe_hints = payload.get("hints")
        if isinstance(maybe_hints, list):
            payload = maybe_hints
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            hint_id = str(item.get("hint_id") or "").strip()
            if hint_id and hint_id not in ids:
                ids.append(hint_id)
    return ids


def _load_transition_hints_payload(path: Optional[Path]) -> Tuple[str, Any]:
    if path is None:
        return "", {}
    text = _read_prompt_file(path)
    parsed: Any = {}
    stripped = text.strip()
    if stripped:
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = {"raw": stripped}
    return stripped, parsed


def _validate_transition_hints_payload(payload: Any) -> None:
    schema_path = repo_root(Path(__file__).resolve()) / "schemas" / "outline_transition_hints.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Missing transition hints schema: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        first = errors[0]
        path = ".".join(str(token) for token in first.path)
        location = path or "<root>"
        raise ValueError(f"Invalid --transition-hints-file at {location}: {first.message}")


def _resolve_phase_template(book_root: Path, phase_id: str) -> Path:
    template_name = OUTLINE_PHASE_TEMPLATE_BY_ID[phase_id]
    book_template = book_root / "prompts" / "templates" / template_name
    if book_template.exists():
        return book_template

    repo_template = repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / template_name
    if repo_template.exists():
        return repo_template

    fallback = repo_root(Path(__file__).resolve()) / OUTLINE_PHASE_BLOCK_FALLBACK[phase_id]
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Missing outline phase template for {phase_id}: {template_name}")


def _resolve_outline_system_overlay(book_root: Path) -> str:
    book_overlay = book_root / "prompts" / "templates" / "outline_system_execution_contract.md"
    if book_overlay.exists():
        return book_overlay.read_text(encoding="utf-8").strip()
    fallback = repo_root(Path(__file__).resolve()) / OUTLINE_SYSTEM_BLOCK_FALLBACK
    if fallback.exists():
        return fallback.read_text(encoding="utf-8").strip()
    return ""


def _canonical_phase_template_checksum(phase_id: str) -> str:
    template_name = OUTLINE_PHASE_TEMPLATE_BY_ID[phase_id]
    canonical_path = repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / template_name
    if not canonical_path.exists():
        raise FileNotFoundError(f"Missing canonical outline template: {canonical_path}")
    return _sha256_file(canonical_path)


def _enforce_template_drift_guard(book_root: Path, template_paths: Dict[str, Path], template_checksums: Dict[str, str]) -> None:
    for phase_id in OUTLINE_PHASE_ORDER:
        resolved = template_paths.get(phase_id)
        if not isinstance(resolved, Path):
            continue
        if not str(resolved).lower().replace("\\", "/").endswith("/prompts/templates/" + OUTLINE_PHASE_TEMPLATE_BY_ID[phase_id]):
            continue
        canonical_checksum = _canonical_phase_template_checksum(phase_id)
        resolved_checksum = str(template_checksums.get(phase_id) or "").strip()
        if resolved_checksum and canonical_checksum != resolved_checksum:
            raise ValueError(
                f"Template drift detected for {OUTLINE_PHASE_TEMPLATE_BY_ID[phase_id]}. "
                f"Run: bookforge book update-templates --book {book_root.name}"
            )


def _active_location_registry_path(outline_root: Path) -> Path:
    return outline_root / "location_registry_active.json"


def _extract_json_strict(text: str, label: str) -> Dict[str, Any]:
    return _extract_json_object_only(text, label)


def _extract_phase_json(phase_id: str, text: str) -> Dict[str, Any]:
    return _extract_json_strict(text, label=f"{phase_id} response")


def _section_end_condition_lookup(sections_payload: Optional[Dict[str, Any]]) -> Dict[Tuple[int, int], str]:
    lookup: Dict[Tuple[int, int], str] = {}
    if not isinstance(sections_payload, dict):
        return lookup
    chapters = sections_payload.get("chapters")
    if not isinstance(chapters, list):
        return lookup
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id is None:
            continue
        sections = chapter.get("sections")
        if not isinstance(sections, list):
            continue
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_id = _to_int(section.get("section_id"))
            if section_id is None:
                continue
            end_condition = str(section.get("end_condition") or "").strip()
            if end_condition:
                lookup[(chapter_id, section_id)] = end_condition
    return lookup


def _build_run_fingerprint(
    *,
    book: Dict[str, Any],
    user_prompt: str,
    transition_hints: str,
    template_checksums: Dict[str, str],
    settings: Dict[str, Any],
    prior_handoff_hashes: Dict[str, str],
) -> str:
    payload = {
        "book": book,
        "targets": book.get("targets", {}),
        "user_prompt": user_prompt,
        "transition_hints": transition_hints,
        "template_checksums": template_checksums,
        "settings": settings,
        "prior_handoff_hashes": prior_handoff_hashes,
    }
    return _sha256_text(_stable_json(payload))


def _default_phase_history(
    *,
    book_id: str,
    run_id: str,
    fingerprint: str,
    settings: Dict[str, Any],
    template_checksums: Dict[str, str],
) -> Dict[str, Any]:
    now = _now_iso()
    return {
        "book_id": book_id,
        "run_id": run_id,
        "created_at": now,
        "updated_at": now,
        "input_fingerprint": fingerprint,
        "settings": settings,
        "template_checksums": template_checksums,
        "phases": {},
    }


def _phase_entry_reusable(run_dir: Path, entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("status") != "success":
        return False
    artifacts = entry.get("artifacts")
    if not isinstance(artifacts, dict):
        return False
    handoff = artifacts.get("handoff")
    output = artifacts.get("output")
    validation = artifacts.get("validation")
    if not handoff or not output or not validation:
        return False
    for rel in (handoff, output, validation):
        if not (run_dir / str(rel)).exists():
            return False
    return True


def _parse_scene_ref(value: Any) -> Optional[Tuple[int, int]]:
    text = str(value or "").strip()
    if not text:
        return None
    if not REF_PATTERN.match(text):
        return None
    left, right = text.split(":", 1)
    return int(left), int(right)


def _load_latest_run_metadata(outline_root: Path) -> Tuple[Optional[str], Optional[Path], Dict[str, Any]]:
    latest_path = outline_root / OUTLINE_PIPELINE_LATEST
    if not latest_path.exists():
        alias_path = outline_root / OUTLINE_PIPELINE_LATEST_ALIAS
        if alias_path.exists():
            latest_path = alias_path
        else:
            return None, None, {}
    try:
        payload = _read_json(latest_path)
    except Exception:
        return None, None, {}
    if not isinstance(payload, dict):
        return None, None, {}
    run_id = str(payload.get("run_id") or "").strip()
    if not run_id:
        return None, None, {}
    run_dir = outline_root / "pipeline_runs" / run_id
    return run_id, run_dir, payload


def _write_latest_run_metadata(outline_root: Path, run_id: str) -> None:
    payload = {
        "run_id": run_id,
        "updated_at": _now_iso(),
        "path": f"outline/pipeline_runs/{run_id}",
    }
    _write_json(outline_root / OUTLINE_PIPELINE_LATEST, payload)
    _write_json(outline_root / OUTLINE_PIPELINE_LATEST_ALIAS, payload)


def _write_latest_report_pointer(outline_root: Path, run_dir: Path) -> Path:
    report_path = run_dir / "outline_pipeline_report.json"
    latest_pointer = outline_root / OUTLINE_PIPELINE_REPORT_LATEST
    latest_snapshot = outline_root / OUTLINE_PIPELINE_REPORT_LATEST_SNAPSHOT
    payload = {
        "run_id": run_dir.name,
        "updated_at": _now_iso(),
        "path": _relpath(outline_root, report_path),
    }
    _write_json(latest_pointer, payload)
    if report_path.exists():
        shutil.copy2(report_path, latest_snapshot)
    return latest_pointer


def _load_history(run_dir: Path) -> Dict[str, Any]:
    path = run_dir / OUTLINE_PIPELINE_HISTORY
    if not path.exists():
        return {"phases": {}}
    try:
        data = _read_json(path)
    except Exception:
        return {"phases": {}}
    if not isinstance(data, dict):
        return {"phases": {}}
    if not isinstance(data.get("phases"), dict):
        data["phases"] = {}
    return data


def _write_pause_marker(
    *,
    outline_root: Path,
    book_id: str,
    run_id: str,
    phase: str,
    reason_code: str,
    message: str,
    attempt: Optional[int] = None,
    resume_from_phase: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Path:
    payload: Dict[str, Any] = {
        "book_id": book_id,
        "run_id": run_id,
        "phase": phase,
        "reason_code": reason_code,
        "message": message,
        "created_at": _now_iso(),
    }
    if attempt is not None:
        payload["attempt"] = attempt
    if resume_from_phase:
        payload["resume_from_phase"] = resume_from_phase
    if details:
        payload["details"] = details
    pause_path = outline_root / OUTLINE_PIPELINE_PAUSE_MARKER
    _write_json(pause_path, payload)
    return pause_path


def _phase_retry_message(phase_id: str, validation: Dict[str, Any]) -> str:
    errors = validation.get("errors", []) if isinstance(validation, dict) else []
    top_codes: List[str] = []
    for item in errors:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        if code and code not in top_codes:
            top_codes.append(code)
    lines = [
        f"Your previous {phase_id} output failed deterministic validation.",
        "Return exactly ONE JSON object and nothing else.",
        "Do not emit markdown, code fences, preambles, or trailing commentary.",
        "Fix these errors:",
    ]
    if top_codes:
        lines.append("Top reason codes:")
        for code in top_codes[:5]:
            lines.append(f"- {code}")
    for item in errors[:12]:
        if isinstance(item, dict):
            code = item.get("code", "validation_error")
            message = item.get("message", "")
            lines.append(f"- [{code}] {message}")
    return "\n".join(lines)


def _is_error_v1_payload(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    if str(payload.get("result") or "").strip().upper() != "ERROR":
        return False
    return str(payload.get("schema_version") or "").strip() == "error_v1"


def _error_v1_to_validation(phase_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    try:
        validate_json(payload, "error_v1")
    except Exception as exc:
        errors.append(_issue("error_v1_schema", str(exc), path="<root>"))
        return {"status": "fail", "errors": errors, "warnings": [], "metrics": {}}
    reason_code = str(payload.get("reason_code") or "error_v1").strip()
    missing_fields = payload.get("missing_fields")
    if not isinstance(missing_fields, list):
        missing_fields = []
    action_hint = str(payload.get("action_hint") or "").strip()
    message = f"{phase_id} returned error_v1: {reason_code}."
    if missing_fields:
        message += f" missing_fields={','.join(str(item) for item in missing_fields[:10])}."
    if action_hint:
        message += f" action_hint={action_hint}"
    errors.append(_issue(reason_code, message, path="<root>"))
    validator_evidence = payload.get("validator_evidence")
    if isinstance(validator_evidence, list):
        for item in validator_evidence:
            if isinstance(item, dict):
                errors.append(item)
    return {"status": "fail", "errors": errors, "warnings": [], "metrics": {}}


def _validation_signature(validation: Dict[str, Any]) -> str:
    errors = validation.get("errors") if isinstance(validation.get("errors"), list) else []
    if not errors:
        return ""
    first = errors[0]
    if not isinstance(first, dict):
        return str(first)
    code = str(first.get("code") or "").strip()
    message = str(first.get("message") or "").strip()
    path = str(first.get("path") or "").strip()
    scene_ref = str(first.get("scene_ref") or "").strip()
    return f"{code}|{path}|{scene_ref}|{message[:160]}"


def _is_retryable_validation(validation: Dict[str, Any]) -> bool:
    errors = validation.get("errors") if isinstance(validation.get("errors"), list) else []
    if not errors:
        return False
    first = errors[0] if isinstance(errors[0], dict) else {}
    code = str(first.get("code") or "").strip()
    return code in RETRYABLE_REASON_CODES


def _phase_handoff_payload(phase_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if phase_id in OUTLINE_WRAPPER_SCHEMA_BY_PHASE:
        outline = payload.get("outline")
        if isinstance(outline, dict):
            return outline
        raise ValueError(f"{phase_id} output is missing wrapper outline object.")
    return payload


def _iter_outline_scene_entries(outline: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    chapters = outline.get("chapters")
    if not isinstance(chapters, list):
        return entries
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id is None:
            continue
        sections = chapter.get("sections")
        if not isinstance(sections, list):
            continue
        for section in sections:
            if not isinstance(section, dict):
                continue
            scenes = section.get("scenes")
            if not isinstance(scenes, list):
                continue
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_id = _to_int(scene.get("scene_id"))
                if scene_id is None:
                    continue
                entries.append(
                    {
                        "chapter_id": chapter_id,
                        "scene_id": scene_id,
                        "scene_ref": f"{chapter_id}:{scene_id}",
                        "scene": scene,
                    }
                )
    return entries


def _to_int_or_none(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _validation_rollup(run_dir: Path, phase_entries: Dict[str, Any]) -> Tuple[int, int, Dict[str, Dict[str, int]]]:
    warnings_count = 0
    errors_count = 0
    per_phase: Dict[str, Dict[str, int]] = {}
    for phase_id in OUTLINE_PHASE_ORDER:
        entry = phase_entries.get(phase_id)
        if not isinstance(entry, dict):
            continue
        artifacts = entry.get("artifacts")
        if not isinstance(artifacts, dict):
            continue
        validation_rel = artifacts.get("validation")
        if not validation_rel:
            continue
        validation_path = run_dir / str(validation_rel)
        if not validation_path.exists():
            continue
        try:
            payload = _read_json(validation_path)
        except Exception:
            continue
        phase_errors = len(payload.get("errors", [])) if isinstance(payload.get("errors"), list) else 0
        phase_warnings = len(payload.get("warnings", [])) if isinstance(payload.get("warnings"), list) else 0
        errors_count += phase_errors
        warnings_count += phase_warnings
        per_phase[phase_id] = {"errors": phase_errors, "warnings": phase_warnings}
    return errors_count, warnings_count, per_phase


def _phase_validation_payload(run_dir: Path, phase_entries: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
    entry = phase_entries.get(phase_id)
    if not isinstance(entry, dict):
        return {}
    artifacts = entry.get("artifacts")
    if not isinstance(artifacts, dict):
        return {}
    validation_rel = artifacts.get("validation")
    if not validation_rel:
        return {}
    validation_path = run_dir / str(validation_rel)
    if not validation_path.exists():
        return {}
    try:
        payload = _read_json(validation_path)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _collect_reason_codes(run_dir: Path, phase_entries: Dict[str, Any]) -> List[str]:
    ordered: List[str] = []
    seen: set[str] = set()
    for phase_id in OUTLINE_PHASE_ORDER:
        payload = _phase_validation_payload(run_dir, phase_entries, phase_id)
        errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
        for item in errors:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            ordered.append(code)
    return ordered


def _phase_attempt_usage(phase_entries: Dict[str, Any]) -> Dict[str, str]:
    usage: Dict[str, str] = {}
    for phase_id in OUTLINE_PHASE_ORDER:
        entry = phase_entries.get(phase_id)
        if not isinstance(entry, dict):
            continue
        attempts = _to_int(entry.get("attempts"))
        if attempts is None:
            continue
        usage[phase_id] = f"{attempts}/{OUTLINE_PIPELINE_MAX_ATTEMPTS}"
    return usage


def _phase_failed(phase_entries: Dict[str, Any]) -> str:
    for phase_id in OUTLINE_PHASE_ORDER:
        entry = phase_entries.get(phase_id)
        if not isinstance(entry, dict):
            continue
        if str(entry.get("status") or "").strip() in {"failed", "paused"}:
            return phase_id
    return ""


def _phase_output_payload(run_dir: Path, phase_entries: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
    entry = phase_entries.get(phase_id)
    if not isinstance(entry, dict):
        return {}
    artifacts = entry.get("artifacts")
    if not isinstance(artifacts, dict):
        return {}
    output_rel = artifacts.get("output")
    if not output_rel:
        return {}
    output_path = run_dir / str(output_rel)
    if not output_path.exists():
        return {}
    try:
        payload = _read_json(output_path)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _phase04_budget_blocked(phase_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocked_items: List[Dict[str, Any]] = []
    raw = phase_report.get("blocked_by_budget")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                blocked_items.append(
                    {
                        "scene_ref": str(item.get("scene_ref") or item.get("from") or "").strip(),
                        "seam_score": _to_int_or_none(item.get("seam_score")),
                        "reason": str(item.get("reason") or "blocked_by_budget").strip(),
                    }
                )
            elif isinstance(item, str):
                blocked_items.append({"scene_ref": item.strip(), "seam_score": None, "reason": "blocked_by_budget"})
    elif isinstance(raw, int) and raw > 0:
        for _ in range(raw):
            blocked_items.append({"scene_ref": "", "seam_score": None, "reason": "blocked_by_budget"})
    return blocked_items


def _phase04_downgraded(phase_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    downgraded: List[Dict[str, Any]] = []
    raw = phase_report.get("downgraded_resolution")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                downgraded.append(
                    {
                        "scene_ref": str(item.get("scene_ref") or item.get("from") or "").strip(),
                        "reason": str(item.get("reason") or "downgraded_resolution").strip(),
                    }
                )
            elif isinstance(item, str):
                downgraded.append({"scene_ref": item.strip(), "reason": "downgraded_resolution"})
    return downgraded


def _phase04_exact_conflicts(phase_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    raw = phase_report.get("exact_scene_count_transition_conflict")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                conflicts.append(
                    {
                        "scene_ref": str(item.get("scene_ref") or "").strip(),
                        "to_scene_ref": str(item.get("to_scene_ref") or "").strip(),
                        "seam_score": _to_int_or_none(item.get("seam_score")),
                        "required_resolution": str(item.get("required_resolution") or "").strip(),
                    }
                )
            elif isinstance(item, str):
                conflicts.append(
                    {
                        "scene_ref": item.strip(),
                        "to_scene_ref": "",
                        "seam_score": None,
                        "required_resolution": "",
                    }
                )
    return conflicts


def _normalize_text_token(value: Any) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
    token = token.strip("_")
    return token or "unknown"


def _is_placeholder_text(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return bool(PLACEHOLDER_TOKEN_PATTERN.search(text))


def _is_placeholder_anchor(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return bool(PLACEHOLDER_ANCHOR_PATTERN.fullmatch(text) or PLACEHOLDER_TOKEN_PATTERN.search(text))


def _unique_non_empty(values: List[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _default_location_registry() -> Dict[str, Any]:
    return {"schema_version": "location_registry_v1", "locations": []}


def _load_location_registry(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return _default_location_registry()
    try:
        payload = _read_json(path)
    except Exception:
        return _default_location_registry()
    if not isinstance(payload, dict):
        return _default_location_registry()
    locations = payload.get("locations")
    if not isinstance(locations, list):
        payload["locations"] = []
    if str(payload.get("schema_version") or "").strip() != "location_registry_v1":
        payload["schema_version"] = "location_registry_v1"
    return payload


def _write_location_registry(path: Path, registry: Dict[str, Any]) -> None:
    payload = _default_location_registry()
    payload["locations"] = registry.get("locations") if isinstance(registry.get("locations"), list) else []
    validate_json(payload, "outline_location_registry")
    _write_json(path, payload)


def _location_stability_key(label: str, parent_location_id: str = "") -> str:
    normalized = _normalize_text_token(label)
    parent = _normalize_text_token(parent_location_id)
    return f"{parent}::{normalized}" if parent and parent != "unknown" else normalized


def _location_display_slug(label: str) -> str:
    token = _normalize_text_token(label).upper()
    if token == "UNKNOWN":
        token = "GENERIC_LOCATION"
    return token


def _compile_location_id(label: str, stability_key: str) -> str:
    slug = _location_display_slug(label)
    candidate = f"LOC_{slug}"
    if len(candidate) <= 48:
        return candidate
    digest = hashlib.sha1(stability_key.encode("utf-8")).hexdigest()[:8].upper()
    return f"LOC_{slug[:39]}_{digest}"


def _resolve_location_registry_entry(
    *,
    registry: Dict[str, Any],
    label: str,
    scene_ref: str,
    parent_location_id: str = "",
) -> Tuple[str, bool]:
    locations = registry.get("locations")
    if not isinstance(locations, list):
        locations = []
        registry["locations"] = locations
    clean_label = str(label or "").strip()
    stability_key = _location_stability_key(clean_label, parent_location_id)
    normalized = _normalize_text_token(clean_label)

    for entry in locations:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("stability_key") or "").strip() == stability_key:
            aliases = entry.get("aliases")
            if not isinstance(aliases, list):
                aliases = []
                entry["aliases"] = aliases
            if clean_label and clean_label != str(entry.get("display_name") or "").strip() and clean_label not in aliases:
                aliases.append(clean_label)
            return str(entry.get("location_id") or "").strip(), False

    for entry in locations:
        if not isinstance(entry, dict):
            continue
        display = _normalize_text_token(entry.get("display_name"))
        aliases = entry.get("aliases") if isinstance(entry.get("aliases"), list) else []
        alias_tokens = {_normalize_text_token(item) for item in aliases}
        if normalized and (normalized == display or normalized in alias_tokens):
            aliases_list = entry.get("aliases")
            if not isinstance(aliases_list, list):
                aliases_list = []
                entry["aliases"] = aliases_list
            if clean_label and clean_label not in aliases_list and clean_label != str(entry.get("display_name") or "").strip():
                aliases_list.append(clean_label)
            if not entry.get("stability_key"):
                entry["stability_key"] = stability_key
            return str(entry.get("location_id") or "").strip(), False

    candidate = _compile_location_id(clean_label, stability_key)
    existing_ids = {
        str(entry.get("location_id") or "").strip()
        for entry in locations
        if isinstance(entry, dict) and str(entry.get("location_id") or "").strip()
    }
    if candidate in existing_ids:
        digest = hashlib.sha1(stability_key.encode("utf-8")).hexdigest()[:8].upper()
        candidate = f"{candidate}_{digest}"

    new_entry: Dict[str, Any] = {
        "location_id": candidate,
        "display_name": clean_label,
        "aliases": [],
        "stability_key": stability_key,
        "introduced_in": scene_ref,
    }
    parent = str(parent_location_id or "").strip()
    if parent:
        new_entry["parent_location_id"] = parent
    locations.append(new_entry)
    return candidate, True


def _normalize_transition_aliases(scene: Dict[str, Any]) -> None:
    transition_in_text = str(scene.get("transition_in_text") or "").strip()
    legacy_in = str(scene.get("transition_in") or "").strip()
    if not transition_in_text and legacy_in:
        scene["transition_in_text"] = legacy_in
    if "transition_in" in scene:
        scene.pop("transition_in", None)

    transition_out_text = str(scene.get("transition_out_text") or "").strip()
    legacy_out = str(scene.get("transition_out") or "").strip()
    if not transition_out_text and legacy_out:
        scene["transition_out_text"] = legacy_out
    if "transition_out" in scene:
        scene.pop("transition_out", None)


def _compile_outline_location_identity(
    *,
    outline: Dict[str, Any],
    registry: Dict[str, Any],
) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    minted: List[Dict[str, Any]] = []

    chapters = outline.get("chapters")
    if not isinstance(chapters, list):
        return {"errors": errors, "warnings": warnings, "minted": minted}

    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id is None:
            continue
        entries = _chapter_scene_entries(chapter)
        for idx, entry in enumerate(entries):
            scene = entry["scene"]
            scene_id = _to_int(scene.get("scene_id")) or (idx + 1)
            scene_ref = f"{chapter_id}:{scene_id}"
            _normalize_transition_aliases(scene)

            start_label = str(scene.get("location_start_label") or scene.get("location_start") or "").strip()
            end_label = str(scene.get("location_end_label") or scene.get("location_end") or "").strip()
            if start_label:
                scene["location_start_label"] = start_label
                scene["location_start"] = start_label
            if end_label:
                scene["location_end_label"] = end_label
                scene["location_end"] = end_label

            if start_label and _is_placeholder_text(start_label):
                errors.append(_issue("transition_placeholder", "location_start_label must not contain placeholder values.", scene_ref=scene_ref))
            if end_label and _is_placeholder_text(end_label):
                errors.append(_issue("transition_placeholder", "location_end_label must not contain placeholder values.", scene_ref=scene_ref))
            start_label_placeholder = bool(start_label and _is_placeholder_text(start_label))
            end_label_placeholder = bool(end_label and _is_placeholder_text(end_label))

            start_id = str(scene.get("location_start_id") or "").strip()
            end_id = str(scene.get("location_end_id") or "").strip()
            handoff_mode = str(scene.get("handoff_mode") or "").strip()

            if not start_id and start_label and not start_label_placeholder:
                start_id, created = _resolve_location_registry_entry(
                    registry=registry,
                    label=start_label,
                    scene_ref=scene_ref,
                )
                if created:
                    minted.append({"scene_ref": scene_ref, "field": "location_start_id", "location_id": start_id, "label": start_label})
            if not start_id and handoff_mode == "direct_continuation" and idx > 0:
                prev_scene = entries[idx - 1]["scene"]
                prev_end = str(prev_scene.get("location_end_id") or "").strip()
                if prev_end and LOCATION_ID_PATTERN.fullmatch(prev_end):
                    start_id = prev_end
            if start_id:
                scene["location_start_id"] = start_id

            if not end_id and end_label and not end_label_placeholder:
                end_id, created = _resolve_location_registry_entry(
                    registry=registry,
                    label=end_label,
                    scene_ref=scene_ref,
                    parent_location_id=start_id,
                )
                if created:
                    minted.append({"scene_ref": scene_ref, "field": "location_end_id", "location_id": end_id, "label": end_label})
            if end_id:
                scene["location_end_id"] = end_id

            if not str(scene.get("location_start_id") or "").strip():
                errors.append(_issue("location_registry_missing", "location_start_id could not be derived from labels or continuation inheritance.", scene_ref=scene_ref))
            if not str(scene.get("location_end_id") or "").strip():
                errors.append(_issue("location_registry_missing", "location_end_id could not be derived from labels or registry.", scene_ref=scene_ref))

    return {"errors": errors, "warnings": warnings, "minted": minted}


def _scene_character_ids(scene: Dict[str, Any]) -> set[str]:
    values = scene.get("characters")
    if not isinstance(values, list):
        return set()
    return {str(item).strip() for item in values if str(item).strip()}


def _seam_resolution_for_score(score: int) -> str:
    if score >= 55:
        return "full_scene"
    if score >= SEAM_MICRO_MIN_SCORE:
        return "micro_scene"
    return "inline_bridge"


def _score_transition_edge(current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> int:
    score = 0

    current_end = _normalize_text_token(current_scene.get("location_end_id") or current_scene.get("location_end"))
    next_start = _normalize_text_token(next_scene.get("location_start_id") or next_scene.get("location_start"))
    if current_end != "unknown" and next_start != "unknown" and current_end != next_start:
        score += 25

    current_state = str(current_scene.get("constraint_state") or "").strip()
    next_state = str(next_scene.get("constraint_state") or "").strip()
    if current_state in CONSTRAINED_STATES and next_state in SETTLED_STATES:
        score += 35
    elif current_state != next_state and (current_state in CONSTRAINED_STATES or next_state in CONSTRAINED_STATES):
        score += 20
    elif current_state != next_state:
        score += 10

    handoff_mode = str(next_scene.get("handoff_mode") or "").strip()
    if handoff_mode and handoff_mode != "direct_continuation":
        score += 15

    current_cast = _scene_character_ids(current_scene)
    next_cast = _scene_character_ids(next_scene)
    if next_cast and (next_cast - current_cast):
        score += 10

    if handoff_mode in {"detained_then_release", "offscreen_processing", "arrival_checkpoint", "escorted_transfer"}:
        score += 10

    current_type = str(current_scene.get("type") or "").strip()
    next_type = str(next_scene.get("type") or "").strip()
    if current_type in HIGH_PRESSURE_SCENE_TYPES and next_type in LOW_PRESSURE_SCENE_TYPES:
        score += 10

    current_outcome = str(current_scene.get("outcome") or "").lower()
    if any(keyword in current_outcome for keyword in MAJOR_TURN_KEYWORDS):
        score += 10

    return max(0, min(100, score))


def _fallback_transition_in_text(
    scene: Dict[str, Any],
    prev_scene: Optional[Dict[str, Any]],
) -> str:
    start_location = str(scene.get("location_start") or "").strip() or "the current location"
    handoff_mode = str(scene.get("handoff_mode") or "").strip() or "direct_continuation"
    if prev_scene is None:
        return f"The scene opens at {start_location}."
    prev_end = str(prev_scene.get("location_end") or prev_scene.get("location_start") or "").strip()
    if prev_end and prev_end != start_location:
        return f"After moving from {prev_end}, the action resumes at {start_location}."
    if handoff_mode != "direct_continuation":
        return f"Following a {handoff_mode.replace('_', ' ')}, the action resumes at {start_location}."
    return f"The action continues at {start_location}."


def _fallback_transition_out_text(scene: Dict[str, Any], next_scene: Dict[str, Any]) -> str:
    next_location = str(next_scene.get("location_start") or next_scene.get("location_end") or "").strip() or "the next location"
    handoff_mode = str(next_scene.get("handoff_mode") or "").strip()
    if handoff_mode and handoff_mode != "direct_continuation":
        return f"This beat pushes into a {handoff_mode.replace('_', ' ')} toward {next_location}."
    return f"This beat carries directly into {next_location}."


def _fallback_transition_anchors(scene: Dict[str, Any]) -> List[str]:
    return _unique_non_empty(
        [
            _normalize_text_token(scene.get("location_start_id")),
            _normalize_text_token(scene.get("location_end_id")),
            _normalize_text_token(scene.get("location_start")),
            _normalize_text_token(scene.get("location_end")),
            _normalize_text_token(scene.get("handoff_mode")),
            _normalize_text_token(scene.get("constraint_state")),
        ]
    )


def _chapter_scene_entries(chapter: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    sections = chapter.get("sections")
    if not isinstance(sections, list):
        return entries
    for section in sections:
        if not isinstance(section, dict):
            continue
        scenes = section.get("scenes")
        if not isinstance(scenes, list):
            continue
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            entries.append({"section": section, "scenes": scenes, "scene": scene})
    return entries


def _ensure_transition_contract_for_scene(
    scene: Dict[str, Any],
    prev_scene: Optional[Dict[str, Any]],
    next_scene: Optional[Dict[str, Any]],
) -> None:
    _normalize_transition_aliases(scene)

    location_start_id = str(scene.get("location_start_id") or "").strip()
    if location_start_id:
        scene["location_start_id"] = location_start_id
    else:
        scene.pop("location_start_id", None)

    location_end_id = str(scene.get("location_end_id") or "").strip()
    if location_end_id:
        scene["location_end_id"] = location_end_id
    else:
        scene.pop("location_end_id", None)

    location_start_label = str(scene.get("location_start_label") or "").strip()
    location_end_label = str(scene.get("location_end_label") or "").strip()
    location_start = str(scene.get("location_start") or location_start_label).strip()
    location_end = str(scene.get("location_end") or location_end_label).strip()
    if location_start:
        scene["location_start"] = location_start
        scene["location_start_label"] = location_start_label or location_start
    else:
        scene.pop("location_start", None)
        scene.pop("location_start_label", None)
    if location_end:
        scene["location_end"] = location_end
        scene["location_end_label"] = location_end_label or location_end
    else:
        scene.pop("location_end", None)
        scene.pop("location_end_label", None)

    handoff_mode = str(scene.get("handoff_mode") or "").strip()
    if handoff_mode:
        scene["handoff_mode"] = handoff_mode
    else:
        scene.pop("handoff_mode", None)

    constraint_state = str(scene.get("constraint_state") or "").strip()
    if constraint_state:
        scene["constraint_state"] = constraint_state
    else:
        scene.pop("constraint_state", None)

    transition_in_text = str(scene.get("transition_in_text") or "").strip()
    if transition_in_text:
        scene["transition_in_text"] = transition_in_text
    else:
        scene.pop("transition_in_text", None)

    anchors = scene.get("transition_in_anchors")
    if isinstance(anchors, list):
        cleaned = _unique_non_empty([str(item).strip() for item in anchors])
    else:
        cleaned = []
    if not cleaned:
        cleaned = _fallback_transition_anchors(scene)
    if cleaned:
        scene["transition_in_anchors"] = cleaned[:6]
    else:
        scene.pop("transition_in_anchors", None)

    out_anchors = scene.get("transition_out_anchors")
    if isinstance(out_anchors, list):
        out_cleaned = _unique_non_empty([str(item).strip() for item in out_anchors])
    else:
        out_cleaned = []
    if not out_cleaned and next_scene is not None:
        out_cleaned = _fallback_transition_anchors(scene)
    if out_cleaned:
        scene["transition_out_anchors"] = out_cleaned[:6]
    else:
        scene.pop("transition_out_anchors", None)

    if next_scene is None:
        if "transition_out_text" in scene and not str(scene.get("transition_out_text") or "").strip():
            scene.pop("transition_out_text", None)
    else:
        transition_out_text = str(scene.get("transition_out_text") or "").strip()
        if transition_out_text:
            scene["transition_out_text"] = transition_out_text
        else:
            scene.pop("transition_out_text", None)

    for optional_field in OPTIONAL_EDGE_FIELDS:
        if optional_field in scene and not str(scene.get(optional_field) or "").strip():
            scene.pop(optional_field, None)


def _build_inserted_transition_scene(
    *,
    current_scene: Dict[str, Any],
    next_scene: Dict[str, Any],
    seam_score: int,
    seam_resolution: str,
) -> Dict[str, Any]:
    location_start = str(current_scene.get("location_end") or current_scene.get("location_start") or "").strip()
    location_end = str(next_scene.get("location_start") or next_scene.get("location_end") or "").strip() or location_start

    location_start_id = str(current_scene.get("location_end_id") or current_scene.get("location_start_id") or "").strip()
    location_end_id = str(next_scene.get("location_start_id") or next_scene.get("location_end_id") or "").strip() or location_start_id

    def _derive_location_id(value: str) -> str:
        if not value:
            return ""
        token = _normalize_text_token(value).upper()
        return f"LOC_{token}" if token and token != "UNKNOWN" else ""

    if not location_start_id:
        location_start_id = _derive_location_id(location_start)
    if not location_end_id:
        location_end_id = _derive_location_id(location_end)

    handoff_mode = str(next_scene.get("handoff_mode") or "").strip()
    if handoff_mode not in HANDOFF_MODE_VALUES or handoff_mode == "direct_continuation":
        handoff_mode = "offscreen_processing"
    constraint_state = str(next_scene.get("constraint_state") or current_scene.get("constraint_state") or "").strip()
    if constraint_state not in CONSTRAINT_STATE_VALUES:
        constraint_state = "processed"

    characters = sorted(_scene_character_ids(current_scene) | _scene_character_ids(next_scene))
    threads: List[str] = []
    current_threads = current_scene.get("threads") if isinstance(current_scene.get("threads"), list) else []
    next_threads = next_scene.get("threads") if isinstance(next_scene.get("threads"), list) else []
    for thread_id in [str(item).strip() for item in current_threads + next_threads]:
        if thread_id and thread_id not in threads:
            threads.append(thread_id)

    transition_text = (
        f"After a {handoff_mode.replace('_', ' ')}, the movement from {location_start} to {location_end} is realized on page."
    )
    transition_scene: Dict[str, Any] = {
        "scene_id": 0,
        "summary": f"Transition handoff from {location_start} to {location_end}.",
        "type": "transition",
        "outcome": "The handoff is concretely realized and constraints are carried forward.",
        "characters": characters,
        "location_start_label": location_start,
        "location_end_label": location_end,
        "location_start_id": location_start_id,
        "location_end_id": location_end_id,
        "location_start": location_start,
        "location_end": location_end,
        "handoff_mode": handoff_mode,
        "constraint_state": constraint_state,
        "transition_in_text": transition_text,
        "transition_in_anchors": _fallback_transition_anchors(
            {
                "location_start_id": location_start_id,
                "location_end_id": location_end_id,
                "location_start": location_start,
                "location_end": location_end,
                "handoff_mode": handoff_mode,
                "constraint_state": constraint_state,
            }
        ),
        "transition_out_text": _fallback_transition_out_text(
            {"location_start": location_start, "location_end": location_end},
            next_scene,
        ),
        "transition_out_anchors": _fallback_transition_anchors(
            {
                "location_start_id": location_start_id,
                "location_end_id": location_end_id,
                "location_start": location_start,
                "location_end": location_end,
                "handoff_mode": handoff_mode,
                "constraint_state": constraint_state,
            }
        ),
        "seam_score": int(max(0, min(100, seam_score))),
        "seam_resolution": seam_resolution if seam_resolution in SEAM_RESOLUTION_VALUES else "micro_scene",
        "inserted_by_pipeline": True,
        "purpose": "handoff_realization",
    }
    if threads:
        transition_scene["threads"] = threads
    return transition_scene


def _apply_phase04_transition_policy(
    payload: Dict[str, Any],
    *,
    exact_scene_count: bool,
    allow_transition_scene_insertions: bool,
    transition_insert_budget_per_chapter: int,
) -> Dict[str, Any]:
    if payload.get("schema_version") != "transition_refine_v1":
        return payload

    outline = payload.get("outline")
    if not isinstance(outline, dict):
        return payload

    phase_report = payload.get("phase_report")
    if not isinstance(phase_report, dict):
        phase_report = {}
        payload["phase_report"] = phase_report

    blocked_by_budget: List[Dict[str, Any]] = []
    downgraded_resolution: List[Dict[str, Any]] = []
    exact_conflicts: List[Dict[str, Any]] = []
    edits_applied: List[str] = []

    chapters = outline.get("chapters")
    if not isinstance(chapters, list):
        return payload

    budget_per_chapter = max(0, int(transition_insert_budget_per_chapter))

    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id is None or chapter_id <= 0:
            continue

        entries = _chapter_scene_entries(chapter)
        if not entries:
            continue

        for idx, entry in enumerate(entries):
            prev_scene = entries[idx - 1]["scene"] if idx > 0 else None
            next_scene = entries[idx + 1]["scene"] if idx + 1 < len(entries) else None
            _ensure_transition_contract_for_scene(entry["scene"], prev_scene, next_scene)

        candidates: List[Dict[str, Any]] = []
        for idx in range(len(entries) - 1):
            current_scene = entries[idx]["scene"]
            next_scene = entries[idx + 1]["scene"]
            seam_score = _score_transition_edge(current_scene, next_scene)
            required_resolution = _seam_resolution_for_score(seam_score)
            current_scene["seam_score"] = seam_score
            current_scene["seam_resolution"] = required_resolution
            candidates.append(
                {
                    "idx": idx,
                    "score": seam_score,
                    "required_resolution": required_resolution,
                    "scene_ref": f"{chapter_id}:{idx + 1}",
                    "to_scene_ref": f"{chapter_id}:{idx + 2}",
                }
            )

        entries[-1]["scene"]["seam_score"] = 0
        entries[-1]["scene"]["seam_resolution"] = "inline_bridge"

        required_insertions = [item for item in candidates if item["required_resolution"] != "inline_bridge"]
        selected_indexes: set[int] = set()

        if required_insertions:
            if exact_scene_count:
                for item in required_insertions:
                    exact_conflicts.append(
                        {
                            "scene_ref": item["scene_ref"],
                            "to_scene_ref": item["to_scene_ref"],
                            "seam_score": item["score"],
                            "required_resolution": item["required_resolution"],
                        }
                    )
            elif allow_transition_scene_insertions and budget_per_chapter > 0:
                ordered = sorted(
                    required_insertions,
                    key=lambda item: (-int(item["score"]), int(item["idx"]), str(item["scene_ref"]), str(item["to_scene_ref"])),
                )
                selected_indexes = {int(item["idx"]) for item in ordered[:budget_per_chapter]}
                for item in ordered[budget_per_chapter:]:
                    blocked_by_budget.append(
                        {
                            "scene_ref": item["scene_ref"],
                            "to_scene_ref": item["to_scene_ref"],
                            "seam_score": item["score"],
                            "reason": "blocked_by_budget",
                        }
                    )
            else:
                for item in required_insertions:
                    blocked_by_budget.append(
                        {
                            "scene_ref": item["scene_ref"],
                            "to_scene_ref": item["to_scene_ref"],
                            "seam_score": item["score"],
                            "reason": "insertions_disabled",
                        }
                    )

        for item in required_insertions:
            if int(item["idx"]) in selected_indexes:
                continue
            downgraded_resolution.append(
                {
                    "scene_ref": item["scene_ref"],
                    "to_scene_ref": item["to_scene_ref"],
                    "seam_score": item["score"],
                    "reason": "downgraded_to_inline_bridge",
                }
            )
            entries[int(item["idx"])]["scene"]["seam_resolution"] = "inline_bridge"

        if selected_indexes and not exact_scene_count:
            for idx in sorted(selected_indexes, reverse=True):
                refreshed = _chapter_scene_entries(chapter)
                if idx < 0 or idx + 1 >= len(refreshed):
                    continue
                current_scene = refreshed[idx]["scene"]
                next_scene = refreshed[idx + 1]["scene"]
                next_section = refreshed[idx + 1]["section"]
                section_scenes = next_section.get("scenes")
                if not isinstance(section_scenes, list):
                    continue
                try:
                    insert_pos = section_scenes.index(next_scene)
                except ValueError:
                    insert_pos = 0

                seam_score = _score_transition_edge(current_scene, next_scene)
                seam_resolution = _seam_resolution_for_score(seam_score)
                inserted_scene = _build_inserted_transition_scene(
                    current_scene=current_scene,
                    next_scene=next_scene,
                    seam_score=seam_score,
                    seam_resolution=seam_resolution,
                )
                section_scenes.insert(insert_pos, inserted_scene)
                edits_applied.append(
                    f"inserted_transition_scene {chapter_id}:{idx + 1}->{chapter_id}:{idx + 2} score={seam_score} resolution={seam_resolution}"
                )

        refreshed_entries = _chapter_scene_entries(chapter)
        for idx, entry in enumerate(refreshed_entries, start=1):
            entry["scene"]["scene_id"] = idx

        for idx, entry in enumerate(refreshed_entries):
            scene = entry["scene"]
            prev_scene = refreshed_entries[idx - 1]["scene"] if idx > 0 else None
            next_scene = refreshed_entries[idx + 1]["scene"] if idx + 1 < len(refreshed_entries) else None
            _ensure_transition_contract_for_scene(scene, prev_scene, next_scene)

            if idx == 0:
                scene.pop("consumes_outcome_from", None)
            else:
                scene["consumes_outcome_from"] = f"{chapter_id}:{idx}"

            if next_scene is None:
                scene.pop("hands_off_to", None)
                scene.pop("transition_out", None)
                scene["seam_score"] = 0
                scene["seam_resolution"] = "inline_bridge"
                continue

            scene["hands_off_to"] = f"{chapter_id}:{idx + 2}"

            seam_score = _score_transition_edge(scene, next_scene)
            seam_resolution = _seam_resolution_for_score(seam_score)
            if seam_resolution != "inline_bridge" and exact_scene_count:
                seam_resolution = "inline_bridge"
            if seam_resolution != "inline_bridge" and not allow_transition_scene_insertions:
                seam_resolution = "inline_bridge"
            scene["seam_score"] = seam_score
            scene["seam_resolution"] = seam_resolution

    existing_blocked = phase_report.get("blocked_by_budget")
    merged_blocked: List[Any] = []
    if isinstance(existing_blocked, list):
        merged_blocked.extend(existing_blocked)
    merged_blocked.extend(blocked_by_budget)
    if merged_blocked:
        phase_report["blocked_by_budget"] = merged_blocked

    existing_downgraded = phase_report.get("downgraded_resolution")
    merged_downgraded: List[Any] = []
    if isinstance(existing_downgraded, list):
        merged_downgraded.extend(existing_downgraded)
    merged_downgraded.extend(downgraded_resolution)
    if merged_downgraded:
        phase_report["downgraded_resolution"] = merged_downgraded

    if exact_conflicts:
        phase_report["exact_scene_count_transition_conflict"] = exact_conflicts

    existing_edits = phase_report.get("edits_applied")
    merged_edits: List[str] = []
    if isinstance(existing_edits, list):
        merged_edits.extend([str(item).strip() for item in existing_edits if str(item).strip()])
    merged_edits.extend(edits_applied)
    if merged_edits:
        phase_report["edits_applied"] = _unique_non_empty(merged_edits)

    phase_report["orphan_outcomes_after"] = 0
    phase_report["weak_handoffs_after"] = 0
    phase_report["orphan_scene_refs_after"] = []
    phase_report["weak_handoff_refs_after"] = []

    return payload


def _apply_phase03_transition_policy(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload


def _build_transition_summary(
    *,
    outline_payload: Dict[str, Any],
    phase04_report: Dict[str, Any],
    strict_transition_bridges: bool,
    strict_location_identity: bool,
) -> Dict[str, Any]:
    entries = _iter_outline_scene_entries(outline_payload)
    inserted_count = 0
    inline_count = 0
    hard_cut_count = 0
    top_candidates: List[Dict[str, Any]] = []
    placeholder_identity_items: List[Dict[str, Any]] = []

    for entry in entries:
        scene = entry["scene"]
        seam_resolution = str(scene.get("seam_resolution") or "").strip()
        handoff_mode = str(scene.get("handoff_mode") or "").strip()
        if scene.get("inserted_by_pipeline") is True:
            inserted_count += 1
        if seam_resolution == "inline_bridge":
            inline_count += 1
        if handoff_mode == "hard_cut":
            hard_cut_count += 1

        seam_score = _to_int_or_none(scene.get("seam_score"))
        hands_to = str(scene.get("hands_off_to") or "").strip()
        if seam_score is None or not hands_to:
            continue
        reason = str(scene.get("insert_reason") or scene.get("edge_intent") or "").strip()
        top_candidates.append(
            {
                "from_scene_ref": entry["scene_ref"],
                "to_scene_ref": hands_to,
                "seam_score": seam_score,
                "seam_resolution": seam_resolution or "unknown",
                "reason": reason,
            }
        )

        placeholder_fields: List[str] = []
        for field in (
            "location_start_id",
            "location_end_id",
            "location_start",
            "location_end",
            "location_start_label",
            "location_end_label",
            "transition_in_text",
            "transition_out_text",
        ):
            value = str(scene.get(field) or "").strip()
            if value and _is_placeholder_text(value):
                placeholder_fields.append(field)
        anchors = scene.get("transition_in_anchors")
        if isinstance(anchors, list):
            for anchor in anchors:
                if _is_placeholder_anchor(anchor):
                    placeholder_fields.append("transition_in_anchors")
                    break
        if placeholder_fields:
            placeholder_identity_items.append(
                {
                    "scene_ref": entry["scene_ref"],
                    "fields": sorted(set(placeholder_fields)),
                }
            )

    top_candidates.sort(
        key=lambda item: (
            -int(item.get("seam_score") or 0),
            str(item.get("from_scene_ref") or ""),
            str(item.get("to_scene_ref") or ""),
        )
    )

    blocked_items = _phase04_budget_blocked(phase04_report)
    downgraded_items = _phase04_downgraded(phase04_report)
    exact_conflicts = _phase04_exact_conflicts(phase04_report)
    blocked_high = [
        item
        for item in blocked_items
        if item.get("seam_score") is not None and int(item["seam_score"]) >= BLOCKED_BY_BUDGET_ATTENTION_THRESHOLD
    ]
    if not blocked_high and blocked_items:
        blocked_high = list(blocked_items)

    attention_items: List[Dict[str, Any]] = []
    if blocked_high:
        attention_items.append(
            {
                "code": "blocked_by_budget",
                "severity": "error" if strict_transition_bridges else "warning",
                "message": f"{len(blocked_high)} transition seam(s) were blocked by insertion budget.",
                "items": blocked_high,
            }
        )
    if downgraded_items:
        attention_items.append(
            {
                "code": "downgraded_resolution",
                "severity": "error" if strict_transition_bridges else "warning",
                "message": f"{len(downgraded_items)} seam(s) were downgraded during resolution.",
                "items": downgraded_items,
            }
        )
    if hard_cut_count > 0:
        attention_items.append(
            {
                "code": "hard_cut_used",
                "severity": "error" if strict_transition_bridges else "warning",
                "message": f"{hard_cut_count} scene(s) use handoff_mode=hard_cut.",
                "items": [],
            }
        )
    if exact_conflicts:
        attention_items.append(
            {
                "code": "exact_scene_count_transition_conflict",
                "severity": "error",
                "message": f"{len(exact_conflicts)} seam(s) require insertion but exact scene-count mode is enabled.",
                "items": exact_conflicts,
            }
        )
    if placeholder_identity_items:
        attention_items.append(
            {
                "code": "placeholder_location_identity",
                "severity": "error" if strict_location_identity else "warning",
                "message": f"{len(placeholder_identity_items)} scene(s) contain placeholder location/transition identity values.",
                "items": placeholder_identity_items[:20],
            }
        )

    requires_attention = len(attention_items) > 0
    strict_blocking = any(
        str(item.get("severity") or "").strip().lower() == "error" for item in attention_items
    ) and (strict_transition_bridges or strict_location_identity or len(exact_conflicts) > 0)

    return {
        "inserted_scenes_count": inserted_count,
        "inline_bridges_count": inline_count,
        "hard_cut_count": hard_cut_count,
        "blocked_by_budget_count": len(blocked_items),
        "top_seam_decisions": top_candidates[:3],
        "attention_items": attention_items,
        "requires_user_attention": requires_attention,
        "strict_blocking": strict_blocking,
    }


def _latest_outline_payload(handoffs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    for key in (
        "outline_final_v1_1",
        "outline_cast_refined_v1_1",
        "outline_transitions_refined_v1_1",
        "outline_draft_v1_1",
    ):
        payload = handoffs.get(key)
        if isinstance(payload, dict):
            return payload
    return {}


def _build_outline_pipeline_report_payload(
    *,
    run_dir: Path,
    phase_entries: Dict[str, Any],
    handoff_payloads: Dict[str, Dict[str, Any]],
    book_id: str,
    run_id: str,
    phase_from: str,
    phase_to: str,
    effective_from_phase: str,
    executed_phases: List[str],
    reused_phases: List[str],
    settings: Dict[str, Any],
    scene_count_mode: Dict[str, Any],
    template_checksums: Optional[Dict[str, str]] = None,
    terminal_status: Optional[str] = None,
    terminal_reason_code: str = "",
    raw_model_output_path: str = "",
    retry_directive: str = "",
) -> Dict[str, Any]:
    errors_count, warnings_count, per_phase_validation = _validation_rollup(run_dir, phase_entries)
    phase04_output = _phase_output_payload(run_dir, phase_entries, "phase_04_transition_causality_refinement")
    phase04_report = phase04_output.get("phase_report") if isinstance(phase04_output.get("phase_report"), dict) else {}
    if not isinstance(phase04_report, dict):
        phase04_report = {}

    outline_payload = _latest_outline_payload(handoff_payloads)
    strict_transition_bridges = bool(settings.get("strict_transition_bridges"))
    strict_location_identity = bool(settings.get("strict_location_identity", True))
    transition_summary = _build_transition_summary(
        outline_payload=outline_payload,
        phase04_report=phase04_report,
        strict_transition_bridges=strict_transition_bridges,
        strict_location_identity=strict_location_identity,
    )

    requires_user_attention = bool(transition_summary.get("requires_user_attention"))
    attention_items = transition_summary.get("attention_items", []) if isinstance(transition_summary.get("attention_items"), list) else []
    phase_failed = _phase_failed(phase_entries)
    reason_codes = _collect_reason_codes(run_dir, phase_entries)
    if terminal_reason_code and terminal_reason_code not in reason_codes:
        reason_codes.insert(0, terminal_reason_code)
    attempt_usage = _phase_attempt_usage(phase_entries)
    top_errors: List[Dict[str, Any]] = []
    if phase_failed:
        failed_validation = _phase_validation_payload(run_dir, phase_entries, phase_failed)
        errors = failed_validation.get("errors") if isinstance(failed_validation.get("errors"), list) else []
        top_errors = [item for item in errors[:10] if isinstance(item, dict)]

    if terminal_status:
        overall_status = terminal_status
    elif errors_count > 0:
        overall_status = "ERROR"
    elif requires_user_attention or warnings_count > 0:
        overall_status = "SUCCESS_WITH_WARNINGS"
    else:
        overall_status = "SUCCESS"

    if bool(transition_summary.get("strict_blocking")) and overall_status in {"SUCCESS", "SUCCESS_WITH_WARNINGS"}:
        overall_status = "ERROR"
    if overall_status in {"ERROR", "PAUSED"}:
        requires_user_attention = True

    artifact_paths: Dict[str, Any] = {
        "run_dir": _relpath(run_dir.parent.parent.parent, run_dir),
        "phase_history": _relpath(run_dir, run_dir / OUTLINE_PIPELINE_HISTORY),
        "report": _relpath(run_dir, run_dir / "outline_pipeline_report.json"),
        "decisions": _relpath(run_dir, run_dir / "outline_pipeline_decisions.json"),
    }

    report_payload = {
        "book_id": book_id,
        "run_id": run_id,
        "timestamp": _now_iso(),
        "overall_status": overall_status,
        "phase_failed": phase_failed,
        "reason_codes": reason_codes,
        "attempt_usage": attempt_usage,
        "top_errors": top_errors,
        "requested_from_phase": phase_from,
        "requested_to_phase": phase_to,
        "effective_from_phase": effective_from_phase,
        "executed_phases": executed_phases,
        "reused_phases": reused_phases,
        "warnings_count": warnings_count,
        "errors_count": errors_count,
        "requires_user_attention": requires_user_attention,
        "strict_blocking": bool(transition_summary.get("strict_blocking")),
        "attention_items": attention_items,
        "raw_model_output_path": raw_model_output_path,
        "retry_directive": retry_directive,
        "mode_values": {
            "strict_transition_hints": bool(settings.get("strict_transition_hints")),
            "strict_transition_bridges": bool(settings.get("strict_transition_bridges")),
            "strict_location_identity": bool(settings.get("strict_location_identity", True)),
            "transition_insert_budget_per_chapter": int(settings.get("transition_insert_budget_per_chapter", 2)),
            "allow_transition_scene_insertions": bool(settings.get("allow_transition_scene_insertions", True)),
            "exact_scene_count": bool(settings.get("exact_scene_count")),
            "scene_count_range": str(settings.get("scene_count_range") or ""),
            "scene_count_default_policy": str(scene_count_mode.get("default_policy") or "strong_non_exact"),
        },
        "seam_outcomes": {
            "inserted_scenes_count": int(transition_summary.get("inserted_scenes_count", 0)),
            "inline_bridges_count": int(transition_summary.get("inline_bridges_count", 0)),
            "hard_cut_count": int(transition_summary.get("hard_cut_count", 0)),
            "blocked_by_budget_count": int(transition_summary.get("blocked_by_budget_count", 0)),
        },
        "top_seam_decisions": transition_summary.get("top_seam_decisions", []),
        "settings": settings,
        "scene_count_mode": scene_count_mode,
        "phase_validation_counts": per_phase_validation,
        "artifact_paths": artifact_paths,
        "location_registry_active": {
            "path": str(settings.get("location_registry_active_path") or ""),
            "sha256": str(settings.get("location_registry_active_sha256") or ""),
        },
    }
    if isinstance(template_checksums, dict):
        report_payload["template_checksums"] = template_checksums
    return report_payload


def _validate_spine_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    chapters = payload.get("chapters")
    if payload.get("schema_version") != "spine_v1":
        errors.append(_issue("schema_version", "schema_version must be 'spine_v1'.", path="schema_version"))
    if not isinstance(chapters, list) or not chapters:
        errors.append(_issue("chapters_required", "chapters must be a non-empty array.", path="chapters"))
    else:
        for index, chapter in enumerate(chapters, start=1):
            if not isinstance(chapter, dict):
                errors.append(_issue("chapter_type", "Chapter entries must be objects.", path=f"chapters[{index - 1}]"))
                continue
            chapter_id = _to_int(chapter.get("chapter_id"))
            if chapter_id != index:
                errors.append(
                    _issue(
                        "chapter_id_sequential",
                        f"chapter_id must be sequential starting at 1 (expected {index}).",
                        path=f"chapters[{index - 1}].chapter_id",
                    )
                )
            for key in ("title", "goal", "chapter_role", "stakes_shift", "bridge", "pacing"):
                if key not in chapter:
                    errors.append(_issue("chapter_field_missing", f"Missing '{key}'.", path=f"chapters[{index - 1}].{key}"))
            bridge = chapter.get("bridge")
            if isinstance(bridge, dict):
                if "from_prev" not in bridge or "to_next" not in bridge:
                    errors.append(
                        _issue(
                            "bridge_shape",
                            "bridge must include from_prev and to_next.",
                            path=f"chapters[{index - 1}].bridge",
                        )
                    )
            else:
                errors.append(_issue("bridge_type", "bridge must be an object.", path=f"chapters[{index - 1}].bridge"))
            pacing = chapter.get("pacing")
            if isinstance(pacing, dict):
                expected = _to_int(pacing.get("expected_scene_count"))
                if expected is None or expected <= 0:
                    errors.append(
                        _issue(
                            "expected_scene_count",
                            "pacing.expected_scene_count must be a positive integer.",
                            path=f"chapters[{index - 1}].pacing.expected_scene_count",
                        )
                    )
            else:
                errors.append(_issue("pacing_type", "pacing must be an object.", path=f"chapters[{index - 1}].pacing"))
    return {"status": "pass" if not errors else "fail", "errors": errors, "warnings": warnings, "metrics": {}}


def _validate_sections_payload(payload: Dict[str, Any], spine_payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    chapters = payload.get("chapters")
    if payload.get("schema_version") != "sections_v1":
        errors.append(_issue("schema_version", "schema_version must be 'sections_v1'.", path="schema_version"))
    if not isinstance(chapters, list) or not chapters:
        errors.append(_issue("chapters_required", "chapters must be a non-empty array.", path="chapters"))
        return {"status": "fail", "errors": errors, "warnings": warnings, "metrics": {}}

    expected_chapter_ids: List[int] = []
    if isinstance(spine_payload, dict):
        spine_chapters = spine_payload.get("chapters")
        if isinstance(spine_chapters, list):
            for chapter in spine_chapters:
                if isinstance(chapter, dict):
                    chapter_id = _to_int(chapter.get("chapter_id"))
                    if chapter_id is not None:
                        expected_chapter_ids.append(chapter_id)

    for chapter_index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            errors.append(_issue("chapter_type", "Chapter entries must be objects.", path=f"chapters[{chapter_index - 1}]"))
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id is None:
            errors.append(_issue("chapter_id_type", "chapter_id must be an integer.", path=f"chapters[{chapter_index - 1}].chapter_id"))
            continue
        if expected_chapter_ids and chapter_id not in expected_chapter_ids:
            errors.append(
                _issue(
                    "chapter_id_unknown",
                    f"chapter_id {chapter_id} is not present in phase_01 chapter spine.",
                    path=f"chapters[{chapter_index - 1}].chapter_id",
                )
            )
        sections = chapter.get("sections")
        if not isinstance(sections, list) or not sections:
            errors.append(_issue("sections_required", "sections must be a non-empty array.", path=f"chapters[{chapter_index - 1}].sections"))
            continue
        for section_index, section in enumerate(sections, start=1):
            if not isinstance(section, dict):
                errors.append(
                    _issue(
                        "section_type",
                        "Section entries must be objects.",
                        path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}]",
                    )
                )
                continue
            section_id = _to_int(section.get("section_id"))
            if section_id != section_index:
                errors.append(
                    _issue(
                        "section_id_sequential",
                        f"section_id must be sequential within chapter (expected {section_index}).",
                        path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}].section_id",
                    )
                )
            end_condition = str(section.get("end_condition") or "").strip()
            if not end_condition:
                errors.append(
                    _issue(
                        "end_condition_required",
                        "Section end_condition is required and must be non-empty.",
                        path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}].end_condition",
                    )
                )

    return {"status": "pass" if not errors else "fail", "errors": errors, "warnings": warnings, "metrics": {}}


def _validate_outline_payload(
    *,
    outline: Dict[str, Any],
    section_end_lookup: Dict[Tuple[int, int], str],
    require_transition_links: bool,
    require_seam_fields: bool,
    strict_transition_hints: bool,
    strict_transition_bridges: bool,
    strict_location_identity: bool,
    transition_hint_ids: List[str],
    phase_report: Optional[Dict[str, Any]],
    scene_count_range: Optional[Tuple[int, int]],
    exact_scene_count: bool,
) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    try:
        validate_json(outline, "outline")
    except Exception as exc:
        errors.append(_issue("outline_schema", str(exc), path="<root>"))
        return {"status": "fail", "errors": errors, "warnings": warnings, "metrics": metrics}

    chapters = outline.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        errors.append(_issue("chapters_required", "Outline chapters must be a non-empty array.", path="chapters"))
        return {"status": "fail", "errors": errors, "warnings": warnings, "metrics": metrics}

    character_refs: set[str] = set()
    thread_refs: set[str] = set()
    orphan_refs: List[str] = []
    weak_handoff_refs: List[str] = []

    for chapter_index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            errors.append(_issue("chapter_type", "Chapter entries must be objects.", path=f"chapters[{chapter_index - 1}]"))
            continue
        chapter_id = _to_int(chapter.get("chapter_id"))
        if chapter_id != chapter_index:
            errors.append(
                _issue(
                    "chapter_id_sequential",
                    f"chapter_id must be sequential and start at 1 (expected {chapter_index}).",
                    path=f"chapters[{chapter_index - 1}].chapter_id",
                )
            )
            continue

        sections = chapter.get("sections")
        if not isinstance(sections, list) or not sections:
            errors.append(_issue("sections_required", "sections must be a non-empty array.", path=f"chapters[{chapter_index - 1}].sections"))
            continue

        scene_entries: List[Dict[str, Any]] = []
        for section_index, section in enumerate(sections, start=1):
            if not isinstance(section, dict):
                errors.append(
                    _issue(
                        "section_type",
                        "Section entries must be objects.",
                        path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}]",
                    )
                )
                continue
            section_id = _to_int(section.get("section_id"))
            if section_id != section_index:
                errors.append(
                    _issue(
                        "section_id_sequential",
                        f"section_id must be sequential within chapter (expected {section_index}).",
                        path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}].section_id",
                    )
                )
                continue
            section_end_condition = str(section.get("end_condition") or "").strip()
            if not section_end_condition:
                errors.append(
                    _issue(
                        "end_condition_required",
                        "Section end_condition is required and must be non-empty.",
                        path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}].end_condition",
                    )
                )
            scenes = section.get("scenes")
            if not isinstance(scenes, list) or not scenes:
                errors.append(
                    _issue(
                        "scenes_required",
                        "scenes must be a non-empty array.",
                        path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}].scenes",
                    )
                )
                continue
            for scene_index, scene in enumerate(scenes, start=1):
                if not isinstance(scene, dict):
                    errors.append(
                        _issue(
                            "scene_type",
                            "Scene entries must be objects.",
                            path=f"chapters[{chapter_index - 1}].sections[{section_index - 1}].scenes[{scene_index - 1}]",
                        )
                    )
                    continue
                scene_entries.append(
                    {
                        "chapter_id": chapter_id,
                        "section_id": section_id,
                        "section_index": section_index,
                        "scene_index": scene_index,
                        "scene_id": _to_int(scene.get("scene_id")),
                        "scene": scene,
                        "section": section,
                        "chapter_index": chapter_index,
                    }
                )

        for expected_scene_id, entry in enumerate(scene_entries, start=1):
            scene_id = entry["scene_id"]
            if scene_id != expected_scene_id:
                errors.append(
                    _issue(
                        "scene_id_monotonic",
                        f"scene_id must be chapter-local monotonic sequence (expected {expected_scene_id}).",
                        path=(
                            f"chapters[{entry['chapter_index'] - 1}].sections[{entry['section_index'] - 1}]."
                            f"scenes[{entry['scene_index'] - 1}].scene_id"
                        ),
                        scene_ref=f"{chapter_id}:{scene_id or expected_scene_id}",
                    )
                )

        index_by_scene_id = {entry["scene_id"]: idx for idx, entry in enumerate(scene_entries) if entry["scene_id"] is not None}
        consumed_target_refs: set[str] = set()

        for idx, entry in enumerate(scene_entries):
            scene = entry["scene"]
            scene_id = entry["scene_id"]
            section_id = entry["section_id"]
            if scene_id is None:
                continue
            scene_ref = f"{chapter_id}:{scene_id}"

            _normalize_transition_aliases(scene)
            transition_in_text = str(scene.get("transition_in_text") or "").strip()
            transition_out_text = str(scene.get("transition_out_text") or "").strip()

            expected_end = section_end_lookup.get((chapter_id, section_id))
            if expected_end:
                is_section_final = entry["scene_index"] == len(entry["section"].get("scenes", []))
                if is_section_final:
                    echo = str(scene.get("end_condition_echo") or "").strip()
                    if not echo:
                        errors.append(
                            _issue(
                                "end_condition_echo_required",
                                "Section-final scene must include non-empty end_condition_echo.",
                                path=(
                                    f"chapters[{entry['chapter_index'] - 1}].sections[{entry['section_index'] - 1}]."
                                    f"scenes[{entry['scene_index'] - 1}].end_condition_echo"
                                ),
                                scene_ref=scene_ref,
                            )
                        )
                    elif echo.casefold() != expected_end.casefold():
                        errors.append(
                            _issue(
                                "end_condition_echo_mismatch",
                                "end_condition_echo must match phase_02 section end_condition.",
                                path=(
                                    f"chapters[{entry['chapter_index'] - 1}].sections[{entry['section_index'] - 1}]."
                                    f"scenes[{entry['scene_index'] - 1}].end_condition_echo"
                                ),
                                scene_ref=scene_ref,
                            )
                        )

            for field in OPTIONAL_EDGE_FIELDS:
                if field in scene and not str(scene.get(field) or "").strip():
                    errors.append(
                        _issue(
                            "optional_empty_string",
                            f"Optional field '{field}' must be omitted when unknown; do not emit empty strings.",
                            path=(
                                f"chapters[{entry['chapter_index'] - 1}].sections[{entry['section_index'] - 1}]."
                                f"scenes[{entry['scene_index'] - 1}].{field}"
                            ),
                            scene_ref=scene_ref,
                        )
                    )

            for required_field in TRANSITION_REQUIRED_SCENE_FIELDS:
                if required_field == "transition_in_text":
                    value = transition_in_text
                else:
                    value = scene.get(required_field)
                if required_field == "transition_in_anchors":
                    if not isinstance(value, list):
                        errors.append(
                            _issue(
                                "transition_field_required",
                                "transition_in_anchors is required and must be an array of 3-6 non-empty strings.",
                                scene_ref=scene_ref,
                            )
                        )
                    else:
                        anchors = [str(item).strip() for item in value if str(item).strip()]
                        if len(anchors) < 3 or len(anchors) > 6:
                            errors.append(
                                _issue(
                                    "transition_anchors_count",
                                    "transition_in_anchors must include 3-6 non-empty strings.",
                                    scene_ref=scene_ref,
                                )
                            )
                        elif any(_is_placeholder_anchor(anchor) for anchor in anchors):
                            issue = _issue(
                                "transition_placeholder",
                                "transition_in_anchors must not contain placeholder values.",
                                scene_ref=scene_ref,
                            )
                            if strict_location_identity:
                                errors.append(issue)
                            else:
                                warnings.append(issue)
                else:
                    text = str(value or "").strip()
                    if not text:
                        errors.append(
                            _issue(
                                "transition_field_required",
                                f"{required_field} is required and must be non-empty.",
                                scene_ref=scene_ref,
                            )
                        )
                    else:
                        if required_field in {"location_start_id", "location_end_id"} and LOCATION_ID_PATTERN.fullmatch(text) is None:
                            errors.append(
                                _issue(
                                    "location_id_format",
                                    f"{required_field} must match LOC_[A-Z0-9_]+ format.",
                                    scene_ref=scene_ref,
                                )
                            )
                        if required_field in {
                            "location_start_id",
                            "location_end_id",
                            "location_start",
                            "location_end",
                            "location_start_label",
                            "location_end_label",
                            "transition_in_text",
                        } and _is_placeholder_text(text):
                            issue = _issue(
                                "transition_placeholder",
                                f"{required_field} must not contain placeholder values.",
                                scene_ref=scene_ref,
                            )
                            if strict_location_identity:
                                errors.append(issue)
                            else:
                                warnings.append(issue)

            handoff_mode = str(scene.get("handoff_mode") or "").strip()
            if handoff_mode and handoff_mode not in HANDOFF_MODE_VALUES:
                errors.append(_issue("handoff_mode_enum", f"handoff_mode '{handoff_mode}' is not in allowed enum.", scene_ref=scene_ref))

            constraint_state = str(scene.get("constraint_state") or "").strip()
            if constraint_state and constraint_state not in CONSTRAINT_STATE_VALUES:
                errors.append(_issue("constraint_state_enum", f"constraint_state '{constraint_state}' is not in allowed enum.", scene_ref=scene_ref))

            if strict_transition_bridges and handoff_mode == "hard_cut":
                hard_cut_justification = str(scene.get("hard_cut_justification") or "").strip()
                intentional_cinematic_cut = scene.get("intentional_cinematic_cut")
                if not hard_cut_justification or intentional_cinematic_cut is not True:
                    errors.append(
                        _issue(
                            "hard_cut_disallowed_strict",
                            "hard_cut requires hard_cut_justification and intentional_cinematic_cut=true in strict transition mode.",
                            scene_ref=scene_ref,
                        )
                    )

            for character_id in scene.get("characters", []) if isinstance(scene.get("characters"), list) else []:
                token = str(character_id or "").strip()
                if token:
                    character_refs.add(token)
            for introduce_id in scene.get("introduces", []) if isinstance(scene.get("introduces"), list) else []:
                token = str(introduce_id or "").strip()
                if token:
                    character_refs.add(token)
            for thread_id in scene.get("threads", []) if isinstance(scene.get("threads"), list) else []:
                token = str(thread_id or "").strip()
                if token:
                    thread_refs.add(token)
            for callback in scene.get("callbacks", []) if isinstance(scene.get("callbacks"), list) else []:
                token = str(callback or "").strip()
                if token.startswith("CHAR_"):
                    character_refs.add(token)
                if token.startswith("THREAD_"):
                    thread_refs.add(token)

            consumes_raw = scene.get("consumes_outcome_from")
            hands_raw = scene.get("hands_off_to")
            consumes = str(consumes_raw).strip() if consumes_raw is not None else ""
            hands = str(hands_raw).strip() if hands_raw is not None else ""

            is_first = idx == 0
            is_last = idx == len(scene_entries) - 1

            if require_transition_links and (not is_first) and not consumes:
                errors.append(
                    _issue(
                        "consumes_required",
                        "consumes_outcome_from is required for non-first scenes at phase 04+.",
                        scene_ref=scene_ref,
                    )
                )
            if require_transition_links and (not is_last) and not hands:
                errors.append(
                    _issue(
                        "hands_required",
                        "hands_off_to is required for non-last scenes at phase 04+.",
                        scene_ref=scene_ref,
                    )
                )
            if not is_last:
                if not transition_out_text:
                    errors.append(
                        _issue(
                            "transition_out_required",
                            "transition_out_text is required for non-last scenes.",
                            scene_ref=scene_ref,
                        )
                    )
                elif _is_placeholder_text(transition_out_text):
                    issue = _issue(
                        "transition_placeholder",
                        "transition_out_text must not contain placeholder values.",
                        scene_ref=scene_ref,
                    )
                    if strict_location_identity:
                        errors.append(issue)
                    else:
                        warnings.append(issue)
                out_anchors = scene.get("transition_out_anchors")
                if not isinstance(out_anchors, list):
                    errors.append(
                        _issue(
                            "transition_out_anchors_required",
                            "transition_out_anchors is required for non-last scenes.",
                            scene_ref=scene_ref,
                        )
                    )
                else:
                    cleaned_out_anchors = [str(item).strip() for item in out_anchors if str(item).strip()]
                    if len(cleaned_out_anchors) < 3 or len(cleaned_out_anchors) > 6:
                        errors.append(
                            _issue(
                                "transition_out_anchors_count",
                                "transition_out_anchors must include 3-6 non-empty strings.",
                                scene_ref=scene_ref,
                            )
                        )
                    elif any(_is_placeholder_anchor(anchor) for anchor in cleaned_out_anchors):
                        issue = _issue(
                            "transition_placeholder",
                            "transition_out_anchors must not contain placeholder values.",
                            scene_ref=scene_ref,
                        )
                        if strict_location_identity:
                            errors.append(issue)
                        else:
                            warnings.append(issue)

            if require_seam_fields:
                seam_score = scene.get("seam_score")
                seam_resolution = str(scene.get("seam_resolution") or "").strip()
                if not isinstance(seam_score, int) or seam_score < 0 or seam_score > 100:
                    errors.append(_issue("seam_score_required", "seam_score is required and must be an integer between 0 and 100.", scene_ref=scene_ref))
                if seam_resolution not in SEAM_RESOLUTION_VALUES:
                    errors.append(_issue("seam_resolution_enum", "seam_resolution is required and must be one of inline_bridge|micro_scene|full_scene.", scene_ref=scene_ref))

            parsed_consumes = _parse_scene_ref(consumes) if consumes else None
            parsed_hands = _parse_scene_ref(hands) if hands else None

            if consumes and parsed_consumes is None:
                errors.append(_issue("scene_ref_format", "consumes_outcome_from must use chapter_id:scene_id format.", scene_ref=scene_ref))
            if hands and parsed_hands is None:
                errors.append(_issue("scene_ref_format", "hands_off_to must use chapter_id:scene_id format.", scene_ref=scene_ref))

            if parsed_consumes:
                target_chapter, target_scene = parsed_consumes
                if target_chapter != chapter_id:
                    errors.append(_issue("cross_chapter_ref", "Cross-chapter transition links are out-of-scope for v2.", scene_ref=scene_ref))
                elif target_scene not in index_by_scene_id:
                    errors.append(_issue("missing_scene_ref", f"consumes_outcome_from references unknown scene {target_chapter}:{target_scene}.", scene_ref=scene_ref))
                else:
                    target_idx = index_by_scene_id[target_scene]
                    if target_idx >= idx:
                        errors.append(_issue("consumes_direction", "consumes_outcome_from must point to a prior scene.", scene_ref=scene_ref))
                    elif idx - target_idx > 2:
                        errors.append(_issue("consumes_distance", "consumes_outcome_from must target a prior scene within distance 1-2.", scene_ref=scene_ref))
                    consumed_target_refs.add(f"{chapter_id}:{target_scene}")

            if parsed_hands:
                target_chapter, target_scene = parsed_hands
                if target_chapter != chapter_id:
                    errors.append(_issue("cross_chapter_ref", "Cross-chapter transition links are out-of-scope for v2.", scene_ref=scene_ref))
                elif target_scene not in index_by_scene_id:
                    errors.append(_issue("missing_scene_ref", f"hands_off_to references unknown scene {target_chapter}:{target_scene}.", scene_ref=scene_ref))
                else:
                    target_idx = index_by_scene_id[target_scene]
                    if target_idx <= idx:
                        errors.append(_issue("hands_direction", "hands_off_to must point to a later scene.", scene_ref=scene_ref))
                    elif target_idx - idx > 2:
                        errors.append(_issue("hands_distance", "hands_off_to must target a later scene within distance 1-2.", scene_ref=scene_ref))
                    target_consumes = str(scene_entries[target_idx]["scene"].get("consumes_outcome_from") or "").strip()
                    if target_consumes != scene_ref:
                        weak_handoff_refs.append(scene_ref)
            elif require_transition_links and not is_last:
                weak_handoff_refs.append(scene_ref)

        if require_transition_links:
            for idx, entry in enumerate(scene_entries):
                if idx == len(scene_entries) - 1:
                    continue
                if entry["scene_id"] is None:
                    continue
                scene_ref = f"{chapter_id}:{entry['scene_id']}"
                if scene_ref not in consumed_target_refs:
                    orphan_refs.append(scene_ref)

        scene_count = len(scene_entries)
        pacing = chapter.get("pacing")
        expected_scene_count = _to_int(pacing.get("expected_scene_count")) if isinstance(pacing, dict) else None
        if scene_count_range and not exact_scene_count:
            minimum, maximum = scene_count_range
            if scene_count < minimum or scene_count > maximum:
                errors.append(
                    _issue(
                        "scene_count_range",
                        f"Chapter {chapter_id} scene count {scene_count} is outside configured range {minimum}:{maximum}.",
                        path=f"chapters[{chapter_index - 1}].sections",
                    )
                )
            elif scene_count < maximum:
                warnings.append(
                    _issue(
                        "scene_count_high_end_bias",
                        f"Chapter {chapter_id} scene count {scene_count} is valid but below high-end target {maximum}.",
                        path=f"chapters[{chapter_index - 1}].sections",
                    )
                )
        else:
            if expected_scene_count is None or expected_scene_count <= 0:
                errors.append(
                    _issue(
                        "expected_scene_count",
                        "pacing.expected_scene_count must be a positive integer.",
                        path=f"chapters[{chapter_index - 1}].pacing.expected_scene_count",
                    )
                )
            elif scene_count != expected_scene_count:
                if exact_scene_count:
                    errors.append(
                        _issue(
                            "expected_scene_count_mismatch",
                            f"Chapter {chapter_id} has {scene_count} scenes but expected_scene_count is {expected_scene_count}.",
                            path=f"chapters[{chapter_index - 1}].sections",
                        )
                    )
                else:
                    warnings.append(
                        _issue(
                            "expected_scene_count_mismatch",
                            f"Chapter {chapter_id} has {scene_count} scenes and expected_scene_count is {expected_scene_count} (strong_non_exact mode warning).",
                            path=f"chapters[{chapter_index - 1}].sections",
                        )
                    )

    characters = outline.get("characters")
    if character_refs:
        if not isinstance(characters, list):
            errors.append(_issue("characters_registry_required", "Top-level characters array is required when scenes reference character ids."))
        else:
            character_ids = {str(item.get("character_id") or "").strip() for item in characters if isinstance(item, dict)}
            for missing in sorted([value for value in character_refs if value and value not in character_ids]):
                errors.append(_issue("character_id_missing", f"Scene references unknown character id '{missing}'."))

    threads = outline.get("threads")
    if thread_refs:
        if not isinstance(threads, list):
            errors.append(_issue("threads_registry_required", "Top-level threads array is required when scenes reference thread ids."))
        else:
            thread_ids = {str(item.get("thread_id") or "").strip() for item in threads if isinstance(item, dict)}
            for missing in sorted([value for value in thread_refs if value and value not in thread_ids]):
                errors.append(_issue("thread_id_missing", f"Scene references unknown thread id '{missing}'."))

    metrics["orphan_outcomes_after"] = len(orphan_refs)
    metrics["orphan_scene_refs_after"] = orphan_refs
    metrics["weak_handoffs_after"] = len(weak_handoff_refs)
    metrics["weak_handoff_refs_after"] = weak_handoff_refs

    if require_transition_links and orphan_refs:
        errors.append(_issue("orphan_outcomes", "Orphan outcomes remain after transition-link validation."))

    if strict_transition_hints:
        if not isinstance(phase_report, dict):
            errors.append(_issue("transition_hint_compliance_missing", "phase_report is required in strict transition-hints mode."))
        else:
            compliance = phase_report.get("transition_hint_compliance")
            if not isinstance(compliance, list) or not compliance:
                errors.append(_issue("transition_hint_compliance_missing", "phase_report.transition_hint_compliance must be a non-empty array in strict mode."))
            else:
                seen: Dict[str, bool] = {}
                for item in compliance:
                    if not isinstance(item, dict):
                        errors.append(_issue("transition_hint_entry_type", "transition_hint_compliance entries must be objects."))
                        continue
                    hint_id = str(item.get("hint_id") or "").strip()
                    satisfied = item.get("satisfied")
                    evidence_refs = item.get("evidence_scene_refs")
                    if not hint_id:
                        errors.append(_issue("transition_hint_id_missing", "transition_hint_compliance entries require hint_id."))
                        continue
                    if not isinstance(satisfied, bool):
                        errors.append(_issue("transition_hint_satisfied_type", f"transition hint '{hint_id}' must define boolean satisfied."))
                    if not isinstance(evidence_refs, list):
                        errors.append(_issue("transition_hint_evidence_type", f"transition hint '{hint_id}' must include evidence_scene_refs array."))
                    else:
                        for evidence in evidence_refs:
                            if _parse_scene_ref(evidence) is None:
                                errors.append(_issue("transition_hint_evidence_ref", f"transition hint '{hint_id}' evidence scene ref must use chapter_id:scene_id."))
                    if isinstance(satisfied, bool):
                        seen[hint_id] = satisfied
                        if not satisfied:
                            errors.append(_issue("transition_hint_unsatisfied", f"Transition hint '{hint_id}' is unsatisfied in strict mode."))
                for hint_id in transition_hint_ids:
                    if hint_id not in seen:
                        errors.append(_issue("transition_hint_missing", f"Transition hint '{hint_id}' has no compliance entry."))

    return {"status": "pass" if not errors else "fail", "errors": errors, "warnings": warnings, "metrics": metrics}


def _validate_phase_payload(
    *,
    phase_id: str,
    payload: Dict[str, Any],
    handoffs: Dict[str, Dict[str, Any]],
    strict_transition_hints: bool,
    strict_transition_bridges: bool,
    strict_location_identity: bool,
    transition_hint_ids: List[str],
    scene_count_range: Optional[Tuple[int, int]],
    exact_scene_count: bool,
) -> Dict[str, Any]:
    if phase_id == "phase_01_chapter_spine":
        return _validate_spine_payload(payload)
    if phase_id == "phase_02_section_architecture":
        return _validate_sections_payload(payload, handoffs.get("outline_spine_v1"))

    section_lookup = _section_end_condition_lookup(handoffs.get("outline_sections_v1"))
    if phase_id == "phase_03_scene_draft":
        return _validate_outline_payload(
            outline=payload,
            section_end_lookup=section_lookup,
            require_transition_links=True,
            require_seam_fields=False,
            strict_transition_hints=False,
            strict_transition_bridges=False,
            strict_location_identity=strict_location_identity,
            transition_hint_ids=transition_hint_ids,
            phase_report=None,
            scene_count_range=scene_count_range,
            exact_scene_count=exact_scene_count,
        )

    if phase_id in OUTLINE_WRAPPER_SCHEMA_BY_PHASE:
        expected_schema = OUTLINE_WRAPPER_SCHEMA_BY_PHASE[phase_id]
        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        metrics: Dict[str, Any] = {}
        if payload.get("schema_version") != expected_schema:
            errors.append(_issue("schema_version", f"schema_version must be '{expected_schema}'.", path="schema_version"))
        outline = payload.get("outline")
        if not isinstance(outline, dict):
            errors.append(_issue("outline_required", "Wrapper output must include an 'outline' object.", path="outline"))
            return {"status": "fail", "errors": errors, "warnings": warnings, "metrics": metrics}
        report_key = "phase_report" if phase_id == "phase_04_transition_causality_refinement" else "cast_report"
        if not isinstance(payload.get(report_key), dict):
            errors.append(_issue("report_required", f"Wrapper output must include '{report_key}' object.", path=report_key))
            return {"status": "fail", "errors": errors, "warnings": warnings, "metrics": metrics}
        if phase_id == "phase_04_transition_causality_refinement":
            phase_report = payload.get("phase_report")
            if isinstance(phase_report, dict):
                exact_conflicts = phase_report.get("exact_scene_count_transition_conflict")
                if isinstance(exact_conflicts, list) and exact_conflicts:
                    errors.append(
                        _issue(
                            "exact_scene_count_transition_conflict",
                            f"{len(exact_conflicts)} seam(s) require insertion but exact scene-count mode is enabled.",
                        )
                    )

        outline_validation = _validate_outline_payload(
            outline=outline,
            section_end_lookup=section_lookup,
            require_transition_links=True,
            require_seam_fields=True,
            strict_transition_hints=strict_transition_hints and phase_id == "phase_04_transition_causality_refinement",
            strict_transition_bridges=strict_transition_bridges,
            strict_location_identity=strict_location_identity,
            transition_hint_ids=transition_hint_ids,
            phase_report=payload.get("phase_report") if phase_id == "phase_04_transition_causality_refinement" else None,
            scene_count_range=scene_count_range,
            exact_scene_count=exact_scene_count,
        )
        errors.extend(outline_validation.get("errors", []))
        warnings.extend(outline_validation.get("warnings", []))
        metrics.update(outline_validation.get("metrics", {}))
        return {"status": "pass" if not errors else "fail", "errors": errors, "warnings": warnings, "metrics": metrics}

    if phase_id == "phase_06_thread_payoff_refinement":
        return _validate_outline_payload(
            outline=payload,
            section_end_lookup=section_lookup,
            require_transition_links=True,
            require_seam_fields=True,
            strict_transition_hints=False,
            strict_transition_bridges=strict_transition_bridges,
            strict_location_identity=strict_location_identity,
            transition_hint_ids=transition_hint_ids,
            phase_report=None,
            scene_count_range=scene_count_range,
            exact_scene_count=exact_scene_count,
        )

    return {"status": "fail", "errors": [_issue("phase_unknown", f"Unknown outline phase '{phase_id}'.")], "warnings": [], "metrics": {}}


def _phase_render_values(
    *,
    book: Dict[str, Any],
    user_prompt: str,
    transition_hints_text: str,
    handoffs: Dict[str, Dict[str, Any]],
    scene_count_mode: Dict[str, Any],
    location_registry: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "book": book,
        "targets": book.get("targets", {}),
        "notes": "",
        "user_prompt": user_prompt,
        "transition_hints": transition_hints_text,
        "scene_count_policy": scene_count_mode,
        "outline_spine_v1": handoffs.get("outline_spine_v1", {}),
        "outline_sections_v1": handoffs.get("outline_sections_v1", {}),
        "outline_draft_v1_1": handoffs.get("outline_draft_v1_1", {}),
        "outline_transitions_refined_v1_1": handoffs.get("outline_transitions_refined_v1_1", {}),
        "outline_cast_refined_v1_1": handoffs.get("outline_cast_refined_v1_1", {}),
        "location_registry": location_registry,
    }
def generate_outline(
    workspace: Path,
    book_id: str,
    new_version: bool = False,
    prompt_file: Optional[Path] = None,
    rerun: bool = False,
    resume: bool = False,
    from_phase: Optional[str] = None,
    to_phase: Optional[str] = None,
    phase: Optional[str] = None,
    transition_hints_file: Optional[Path] = None,
    strict_transition_hints: bool = False,
    strict_transition_bridges: bool = False,
    strict_location_identity: bool = True,
    transition_insert_budget_per_chapter: int = 2,
    allow_transition_scene_insertions: bool = True,
    force_rerun_with_draft: bool = False,
    exact_scene_count: bool = False,
    scene_count_range: Optional[str] = None,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
) -> Path:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    if new_version and resume:
        raise ValueError("--resume cannot be combined with --new-version.")
    if new_version and rerun:
        raise ValueError("--rerun cannot be combined with --new-version.")

    normalized_from_phase, normalized_to_phase = _normalize_phase_selector(
        from_phase=from_phase,
        to_phase=to_phase,
        phase=phase,
    )
    parsed_scene_range = _parse_scene_count_range(scene_count_range)

    book_path = book_root / "book.json"
    state_path = book_root / "state.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state.json: {state_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    book = json.loads(book_path.read_text(encoding="utf-8"))
    user_prompt = _read_prompt_file(prompt_file) if prompt_file else ""
    transition_hints_text, transition_hints_payload = _load_transition_hints_payload(transition_hints_file)
    if strict_transition_hints:
        if transition_hints_file is None:
            raise ValueError("--strict-transition-hints requires --transition-hints-file.")
        if not transition_hints_text:
            raise ValueError("--strict-transition-hints requires non-empty transition hints.")
        _validate_transition_hints_payload(transition_hints_payload)
    transition_hint_ids = _collect_transition_hint_ids(transition_hints_payload)

    outline_root = book_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)
    outline_path = outline_root / "outline.json"

    if outline_path.exists():
        if not new_version and not rerun and not resume:
            raise FileExistsError("outline.json already exists. Use --rerun, --resume, or --new-version.")
        if (rerun or resume) and _has_drafted_scene_outputs(book_root) and not force_rerun_with_draft:
            raise ValueError("Drafted scene outputs exist. Use --force-rerun-with-draft to proceed with outline rerun.")
        if new_version:
            _archive_outline(outline_root)

    phase_from = normalized_from_phase or OUTLINE_PHASE_ORDER[0]
    phase_to = normalized_to_phase or OUTLINE_PHASE_ORDER[-1]
    requested_from_idx = OUTLINE_PHASE_ORDER.index(phase_from)
    requested_to_idx = OUTLINE_PHASE_ORDER.index(phase_to)

    template_paths: Dict[str, Path] = {}
    template_checksums: Dict[str, str] = {}
    for phase_id in OUTLINE_PHASE_ORDER:
        path = _resolve_phase_template(book_root, phase_id)
        template_paths[phase_id] = path
        template_checksums[phase_id] = _sha256_file(path)
    _enforce_template_drift_guard(book_root, template_paths, template_checksums)

    scene_count_mode = {
        "exact_scene_count": bool(exact_scene_count),
        "scene_count_range": f"{parsed_scene_range[0]}:{parsed_scene_range[1]}" if parsed_scene_range else "",
        "default_policy": "strong_non_exact",
    }
    settings = {
        "from_phase": phase_from,
        "to_phase": phase_to,
        "strict_transition_hints": bool(strict_transition_hints),
        "strict_transition_bridges": bool(strict_transition_bridges),
        "strict_location_identity": bool(strict_location_identity),
        "transition_insert_budget_per_chapter": int(max(0, transition_insert_budget_per_chapter)),
        "allow_transition_scene_insertions": bool(allow_transition_scene_insertions),
        "exact_scene_count": bool(exact_scene_count),
        "scene_count_range": scene_count_mode["scene_count_range"],
        "force_rerun_with_draft": bool(force_rerun_with_draft),
    }

    latest_run_id, latest_run_dir, _latest_payload = _load_latest_run_metadata(outline_root)
    if resume:
        if not latest_run_id or latest_run_dir is None or not latest_run_dir.exists():
            raise FileNotFoundError("No resumable outline pipeline run found.")
        run_id = latest_run_id
        run_dir = latest_run_dir
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = outline_root / "pipeline_runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

    active_registry_path = _active_location_registry_path(outline_root)
    run_registry_path = run_dir / "location_registry.json"
    if resume and run_registry_path.exists():
        location_registry = _load_location_registry(run_registry_path)
    else:
        location_registry = _load_location_registry(active_registry_path)
        _write_location_registry(run_registry_path, location_registry)
    settings["location_registry_active_path"] = _relpath(book_root, active_registry_path)
    settings["location_registry_active_sha256"] = _sha256_file(active_registry_path) if active_registry_path.exists() else ""

    history = _load_history(run_dir)
    phase_entries = history.get("phases") if isinstance(history.get("phases"), dict) else {}
    handoff_payloads: Dict[str, Dict[str, Any]] = {}
    prior_handoff_hashes: Dict[str, str] = {}

    for phase_id in OUTLINE_PHASE_ORDER:
        entry = phase_entries.get(phase_id) if isinstance(phase_entries, dict) else None
        if not _phase_entry_reusable(run_dir, entry):
            continue
        artifacts = entry.get("artifacts", {})
        handoff_path = run_dir / str(artifacts.get("handoff"))
        try:
            key = OUTLINE_PHASE_HANDOFF_KEY[phase_id]
            handoff_payloads[key] = _read_json(handoff_path)
            prior_handoff_hashes[key] = _sha256_file(handoff_path)
        except Exception:
            continue

    fingerprint_handoff_hashes = prior_handoff_hashes if (not resume and requested_from_idx > 0) else {}
    fingerprint_settings = {
        key: value
        for key, value in settings.items()
        if not str(key).startswith("location_registry_active_")
    }
    fingerprint = _build_run_fingerprint(
        book=book,
        user_prompt=user_prompt,
        transition_hints=transition_hints_text,
        template_checksums=template_checksums,
        settings=fingerprint_settings,
        prior_handoff_hashes=fingerprint_handoff_hashes,
    )

    if resume:
        existing_fingerprint = str(history.get("input_fingerprint") or "")
        if existing_fingerprint and existing_fingerprint != fingerprint:
            raise ValueError("Resume fingerprint mismatch. Inputs changed since paused run; rerun is required.")
    else:
        history = _default_phase_history(
            book_id=book_id,
            run_id=run_id,
            fingerprint=fingerprint,
            settings=settings,
            template_checksums=template_checksums,
        )
        phase_entries = history["phases"]

    effective_from_idx = requested_from_idx
    if not resume and requested_from_idx > 0:
        for index in range(requested_from_idx):
            dep_phase = OUTLINE_PHASE_ORDER[index]
            dep_key = OUTLINE_PHASE_HANDOFF_KEY[dep_phase]
            if dep_key not in handoff_payloads:
                effective_from_idx = index
                break
    if resume:
        first_incomplete_idx = requested_from_idx
        for index, phase_id in enumerate(OUTLINE_PHASE_ORDER):
            if not _phase_entry_reusable(run_dir, phase_entries.get(phase_id)):
                first_incomplete_idx = index
                break
        effective_from_idx = max(requested_from_idx, first_incomplete_idx)
    if effective_from_idx > requested_to_idx:
        effective_from_idx = requested_to_idx

    if client is None:
        config = load_config()
        client = get_llm_client(config, phase="planner")
        if model is None:
            model = resolve_model("planner", config)
    elif model is None:
        model = "default"

    max_tokens = _outline_max_tokens()
    key_slot = getattr(client, "key_slot", None)
    base_system_prompt = system_path.read_text(encoding="utf-8").strip()
    outline_system_overlay = _resolve_outline_system_overlay(book_root)
    if outline_system_overlay:
        system_prompt = f"{base_system_prompt}\n\n{outline_system_overlay}"
    else:
        system_prompt = base_system_prompt
    executed_phases: List[str] = []
    reused_phases: List[str] = []
    last_handoff_path: Optional[Path] = None

    def _emit_pipeline_report(
        *,
        terminal_status: Optional[str] = None,
        terminal_reason_code: str = "",
        raw_model_output_path: str = "",
        retry_directive: str = "",
    ) -> Path:
        report_payload = _build_outline_pipeline_report_payload(
            run_dir=run_dir,
            phase_entries=phase_entries,
            handoff_payloads=handoff_payloads,
            book_id=book_id,
            run_id=run_id,
            phase_from=phase_from,
            phase_to=phase_to,
            effective_from_phase=OUTLINE_PHASE_ORDER[effective_from_idx],
            executed_phases=executed_phases,
            reused_phases=reused_phases,
            settings=settings,
            scene_count_mode=scene_count_mode,
            template_checksums=template_checksums,
            terminal_status=terminal_status,
            terminal_reason_code=terminal_reason_code,
            raw_model_output_path=raw_model_output_path,
            retry_directive=retry_directive,
        )
        validate_json(report_payload, "outline_pipeline_report")
        report_path = run_dir / "outline_pipeline_report.json"
        _write_json(report_path, report_payload)
        _write_json(
            run_dir / "outline_pipeline_decisions.json",
            {"settings": settings, "effective_from_phase": OUTLINE_PHASE_ORDER[effective_from_idx]},
        )
        _write_latest_run_metadata(outline_root, run_id)
        _write_latest_report_pointer(outline_root, run_dir)
        return report_path

    for index in range(effective_from_idx, requested_to_idx + 1):
        phase_id = OUTLINE_PHASE_ORDER[index]
        phase_key = OUTLINE_PHASE_HANDOFF_KEY[phase_id]
        entry = phase_entries.get(phase_id)
        reusable = _phase_entry_reusable(run_dir, entry)

        if resume and reusable:
            artifacts = entry.get("artifacts", {})
            handoff_path = run_dir / str(artifacts.get("handoff"))
            handoff_payloads[phase_key] = _read_json(handoff_path)
            last_handoff_path = handoff_path
            reused_phases.append(phase_id)
            continue

        if index < effective_from_idx and reusable:
            artifacts = entry.get("artifacts", {})
            handoff_path = run_dir / str(artifacts.get("handoff"))
            handoff_payloads[phase_key] = _read_json(handoff_path)
            last_handoff_path = handoff_path
            reused_phases.append(phase_id)
            continue

        render_values = _phase_render_values(
            book=book,
            user_prompt=user_prompt,
            transition_hints_text=transition_hints_text,
            handoffs=handoff_payloads,
            scene_count_mode=scene_count_mode,
            location_registry=location_registry,
        )
        template_path = template_paths[phase_id]
        prompt = render_template_file(template_path, render_values)

        input_path = run_dir / _phase_artifact_name(phase_id, "input")
        _write_json(
            input_path,
            {
                "phase": phase_id,
                "timestamp": _now_iso(),
                "template_path": template_path.as_posix(),
                "render_values": render_values,
                "settings": settings,
            },
        )

        phase_success = False
        normalized_output: Dict[str, Any] = {}
        validation_result: Dict[str, Any] = {"status": "fail", "errors": [], "warnings": [], "metrics": {}}
        attempt_files: List[str] = []
        attempts_used = 0
        validation_signature_last = ""
        retry_directive = ""
        registry_candidate_on_success: Optional[Dict[str, Any]] = None

        for attempt in range(1, OUTLINE_PIPELINE_MAX_ATTEMPTS + 1):
            messages: List[Message] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            if attempt > 1:
                messages.append({"role": "user", "content": _phase_retry_message(phase_id, validation_result)})

            request = {"model": model, "temperature": 0.6, "max_tokens": max_tokens}
            log_extra: Dict[str, Any] = {"book_id": book_id, "phase": phase_id, "attempt": attempt, "run_id": run_id}
            if key_slot:
                log_extra["key_slot"] = key_slot
            try:
                response = client.chat(messages, model=model, temperature=0.6, max_tokens=max_tokens)
            except LLMRequestError as exc:
                if should_log_llm():
                    log_llm_error(workspace, f"outline_{phase_id}_error", exc, request=request, messages=messages, extra=log_extra)
                phase_entries[phase_id] = {
                    "status": "paused",
                    "timestamp": _now_iso(),
                    "attempts": attempt,
                    "artifacts": {
                        "input": _relpath(run_dir, input_path),
                        "attempts": attempt_files,
                    },
                }
                history["updated_at"] = _now_iso()
                _write_json(run_dir / OUTLINE_PIPELINE_HISTORY, history)
                _write_pause_marker(
                    outline_root=outline_root,
                    book_id=book_id,
                    run_id=run_id,
                    phase=phase_id,
                    reason_code="llm_request_error",
                    message=str(exc),
                    attempt=attempt,
                    resume_from_phase=phase_id,
                )
                _emit_pipeline_report(
                    terminal_status="PAUSED",
                    terminal_reason_code="llm_request_error",
                    raw_model_output_path="",
                    retry_directive="Retry outline generation after resolving provider/quota issue.",
                )
                raise

            if should_log_llm():
                log_llm_response(
                    workspace,
                    f"outline_{phase_id}_attempt{attempt}",
                    response,
                    request=request,
                    messages=messages,
                    extra=log_extra,
                )

            attempt_path = run_dir / _phase_artifact_name(phase_id, "attempt", attempt=attempt)
            _write_json(
                attempt_path,
                {
                    "phase": phase_id,
                    "attempt": attempt,
                    "timestamp": _now_iso(),
                    "provider": response.provider,
                    "model": response.model,
                    "raw": response.raw,
                    "text": response.text,
                },
            )
            attempt_files.append(_relpath(run_dir, attempt_path))
            attempts_used = attempt

            try:
                normalized_output = _extract_phase_json(phase_id, response.text)
            except ValueError as exc:
                validation_result = {"status": "fail", "errors": [_issue("json_parse", str(exc), path="<root>")], "warnings": [], "metrics": {}}
                retry_directive = "Return exactly one JSON object matching the required phase schema with no extra text."
                if attempt == OUTLINE_PIPELINE_MAX_ATTEMPTS:
                    break
                continue

            if _is_error_v1_payload(normalized_output):
                validation_result = _error_v1_to_validation(phase_id, normalized_output)
                retry_directive = _phase_retry_message(phase_id, validation_result)
                if not _is_retryable_validation(validation_result):
                    break
                if attempt == OUTLINE_PIPELINE_MAX_ATTEMPTS:
                    break
                continue

            if phase_id == "phase_03_scene_draft":
                normalized_output = _apply_phase03_transition_policy(normalized_output)

            if phase_id == "phase_04_transition_causality_refinement":
                normalized_output = _apply_phase04_transition_policy(
                    normalized_output,
                    exact_scene_count=bool(exact_scene_count),
                    allow_transition_scene_insertions=bool(allow_transition_scene_insertions),
                    transition_insert_budget_per_chapter=int(max(0, transition_insert_budget_per_chapter)),
                )

            payload_for_registry: Optional[Dict[str, Any]] = None
            candidate_registry_for_attempt: Optional[Dict[str, Any]] = None
            if phase_id in {"phase_03_scene_draft", "phase_06_thread_payoff_refinement"}:
                payload_for_registry = normalized_output if isinstance(normalized_output, dict) else None
            elif phase_id in {"phase_04_transition_causality_refinement", "phase_05_cast_function_refinement"}:
                outline_payload = normalized_output.get("outline") if isinstance(normalized_output, dict) else None
                payload_for_registry = outline_payload if isinstance(outline_payload, dict) else None
            if payload_for_registry is not None:
                candidate_registry_for_attempt = copy.deepcopy(location_registry)
                compile_result = _compile_outline_location_identity(
                    outline=payload_for_registry,
                    registry=candidate_registry_for_attempt,
                )
                compile_errors = compile_result.get("errors") if isinstance(compile_result.get("errors"), list) else []
                compile_warnings = compile_result.get("warnings") if isinstance(compile_result.get("warnings"), list) else []
                if compile_errors or compile_warnings:
                    temp_validation = {
                        "status": "fail" if compile_errors else "pass",
                        "errors": [item for item in compile_errors if isinstance(item, dict)],
                        "warnings": [item for item in compile_warnings if isinstance(item, dict)],
                        "metrics": {},
                    }
                else:
                    temp_validation = {"status": "pass", "errors": [], "warnings": [], "metrics": {}}
            else:
                temp_validation = {"status": "pass", "errors": [], "warnings": [], "metrics": {}}

            validation_result = _validate_phase_payload(
                phase_id=phase_id,
                payload=normalized_output,
                handoffs=handoff_payloads,
                strict_transition_hints=strict_transition_hints,
                strict_transition_bridges=strict_transition_bridges,
                strict_location_identity=strict_location_identity,
                transition_hint_ids=transition_hint_ids,
                scene_count_range=parsed_scene_range,
                exact_scene_count=exact_scene_count,
            )
            if temp_validation.get("errors"):
                validation_result["errors"] = list(temp_validation["errors"]) + list(validation_result.get("errors", []))
            if temp_validation.get("warnings"):
                validation_result["warnings"] = list(validation_result.get("warnings", [])) + list(temp_validation["warnings"])
            if temp_validation.get("errors"):
                validation_result["status"] = "fail"

            retry_directive = _phase_retry_message(phase_id, validation_result)
            current_signature = _validation_signature(validation_result)
            if attempt > 1 and current_signature and current_signature == validation_signature_last:
                break
            validation_signature_last = current_signature
            if validation_result.get("status") == "pass":
                if candidate_registry_for_attempt is not None:
                    registry_candidate_on_success = candidate_registry_for_attempt
                phase_success = True
                break

        output_path = run_dir / _phase_artifact_name(phase_id, "output")
        validation_path = run_dir / _phase_artifact_name(phase_id, "validation")
        _write_json(output_path, normalized_output)
        _write_json(validation_path, validation_result)

        if not phase_success:
            reasons = [str(item.get("message")) for item in validation_result.get("errors", []) if isinstance(item, dict)]
            error_items = [item for item in validation_result.get("errors", []) if isinstance(item, dict)]
            reason_code = str(error_items[0].get("code") or "phase_validation_failed") if error_items else "phase_validation_failed"
            failure = OutlinePhaseFailure(
                phase=phase_id,
                reasons=reasons or [f"{phase_id} validation failed."],
                validator_evidence=error_items,
            )
            phase_entries[phase_id] = {
                "status": "failed",
                "timestamp": _now_iso(),
                "attempts": attempts_used,
                "artifacts": {
                    "input": _relpath(run_dir, input_path),
                    "output": _relpath(run_dir, output_path),
                    "validation": _relpath(run_dir, validation_path),
                    "attempts": attempt_files,
                },
            }
            history["updated_at"] = _now_iso()
            _write_json(run_dir / OUTLINE_PIPELINE_HISTORY, history)
            raw_model_output_path = attempt_files[-1] if attempt_files else ""
            _emit_pipeline_report(
                terminal_status="ERROR",
                terminal_reason_code=reason_code,
                raw_model_output_path=raw_model_output_path,
                retry_directive=retry_directive,
            )
            raise failure

        handoff_payload = _phase_handoff_payload(phase_id, normalized_output)
        if registry_candidate_on_success is not None:
            location_registry = registry_candidate_on_success
        _write_location_registry(run_registry_path, location_registry)
        handoff_path = run_dir / OUTLINE_PHASE_HANDOFF_FILE[phase_id]
        _write_json(handoff_path, handoff_payload)
        handoff_payloads[phase_key] = handoff_payload
        last_handoff_path = handoff_path

        phase_entries[phase_id] = {
            "status": "success",
            "timestamp": _now_iso(),
            "attempts": attempts_used,
            "artifacts": {
                "input": _relpath(run_dir, input_path),
                "output": _relpath(run_dir, output_path),
                "validation": _relpath(run_dir, validation_path),
                "handoff": _relpath(run_dir, handoff_path),
                "attempts": attempt_files,
            },
        }
        history["updated_at"] = _now_iso()
        _write_json(run_dir / OUTLINE_PIPELINE_HISTORY, history)
        executed_phases.append(phase_id)

    final_handoff = handoff_payloads.get("outline_final_v1_1")
    if requested_to_idx >= OUTLINE_PHASE_ORDER.index("phase_06_thread_payoff_refinement") and isinstance(final_handoff, dict):
        try:
            final_outline = final_handoff
            if "schema_version" not in final_outline:
                final_outline["schema_version"] = OUTLINE_SCHEMA_VERSION
            characters = final_outline.get("characters")
            if isinstance(characters, list):
                final_outline["characters"] = _ensure_character_ids(characters)
            chapters = final_outline.get("chapters")
            if not isinstance(chapters, list) or not chapters:
                raise ValueError("Final outline must include a non-empty chapters array.")
            _warn_outline_enum_values(final_outline)
            validate_json(final_outline, "outline")

            outline_path.write_text(json.dumps(final_outline, ensure_ascii=True, indent=2), encoding="utf-8")
            if isinstance(final_outline.get("characters"), list):
                (outline_root / "characters.json").write_text(
                    json.dumps(final_outline["characters"], ensure_ascii=True, indent=2),
                    encoding="utf-8",
                )
            _write_outline_chapters(outline_root / "chapters", chapters)

            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["outline"] = {"path": "outline/outline.json"}
            if state.get("status") == "NEW":
                state["status"] = "OUTLINED"
            validate_json(state, "state")
            state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

            _write_location_registry(active_registry_path, location_registry)
            settings["location_registry_active_sha256"] = _sha256_file(active_registry_path)
            _emit_pipeline_report()

            pause_marker = outline_root / OUTLINE_PIPELINE_PAUSE_MARKER
            if pause_marker.exists():
                pause_marker.unlink()
            return outline_path
        except Exception:
            _emit_pipeline_report(
                terminal_status="ERROR",
                terminal_reason_code="outline_publish_failed",
                raw_model_output_path="",
                retry_directive="Fix final outline payload/state publish preconditions and rerun.",
            )
            raise

    if last_handoff_path is None:
        _emit_pipeline_report(
            terminal_status="ERROR",
            terminal_reason_code="missing_handoff_artifact",
            raw_model_output_path="",
            retry_directive="Rerun outline pipeline; no handoff artifact was produced.",
        )
        raise RuntimeError("Outline pipeline completed without producing a handoff artifact.")
    _emit_pipeline_report()
    pause_marker = outline_root / OUTLINE_PIPELINE_PAUSE_MARKER
    if pause_marker.exists():
        pause_marker.unlink()
    return last_handoff_path


def load_latest_outline_pipeline_report(workspace: Path, book_id: str) -> Tuple[Optional[Path], Dict[str, Any]]:
    book_root = workspace / "books" / book_id
    outline_root = book_root / "outline"
    latest_pointer = outline_root / OUTLINE_PIPELINE_REPORT_LATEST
    if latest_pointer.exists():
        try:
            payload = _read_json(latest_pointer)
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            rel = str(payload.get("path") or "").strip()
            if rel:
                candidate = (outline_root / rel).resolve()
                if candidate.exists():
                    try:
                        report = _read_json(candidate)
                    except Exception:
                        report = {}
                    if isinstance(report, dict):
                        return candidate, report
            run_id = str(payload.get("run_id") or "").strip()
            if run_id:
                candidate = outline_root / "pipeline_runs" / run_id / "outline_pipeline_report.json"
                if candidate.exists():
                    try:
                        report = _read_json(candidate)
                    except Exception:
                        report = {}
                    if isinstance(report, dict):
                        return candidate, report

    run_id, run_dir, _payload = _load_latest_run_metadata(outline_root)
    if not run_id or run_dir is None:
        return None, {}
    candidate = run_dir / "outline_pipeline_report.json"
    if not candidate.exists():
        return None, {}
    try:
        report = _read_json(candidate)
    except Exception:
        return None, {}
    if not isinstance(report, dict):
        return None, {}
    return candidate, report


def format_outline_pipeline_summary(report: Dict[str, Any], report_path: Optional[Path] = None) -> str:
    if not isinstance(report, dict):
        return ""
    overall_status = str(report.get("overall_status") or "UNKNOWN")
    mode_values = report.get("mode_values") if isinstance(report.get("mode_values"), dict) else {}
    seam_outcomes = report.get("seam_outcomes") if isinstance(report.get("seam_outcomes"), dict) else {}
    top_decisions = report.get("top_seam_decisions") if isinstance(report.get("top_seam_decisions"), list) else []
    attention_items = report.get("attention_items") if isinstance(report.get("attention_items"), list) else []
    phase_failed = str(report.get("phase_failed") or "").strip()
    reason_codes = report.get("reason_codes") if isinstance(report.get("reason_codes"), list) else []
    attempt_usage = report.get("attempt_usage") if isinstance(report.get("attempt_usage"), dict) else {}

    lines: List[str] = []
    lines.append("Outline Pipeline Summary:")
    lines.append(f"- Result: {overall_status}")
    if phase_failed:
        lines.append(f"- Phase failed: {phase_failed}")
    if reason_codes:
        lines.append(f"- Reason codes: {', '.join(str(item) for item in reason_codes[:5])}")
    lines.append(
        "- Mode values: "
        f"strict_transition_bridges={bool(mode_values.get('strict_transition_bridges', False))} "
        f"strict_transition_hints={bool(mode_values.get('strict_transition_hints', False))} "
        f"strict_location_identity={bool(mode_values.get('strict_location_identity', True))} "
        f"insert_budget={int(mode_values.get('transition_insert_budget_per_chapter', 0) or 0)} "
        f"allow_insertions={bool(mode_values.get('allow_transition_scene_insertions', True))} "
        f"exact_scene_count={bool(mode_values.get('exact_scene_count', False))}"
    )
    lines.append(
        "- Seam outcomes: "
        f"inserted={int(seam_outcomes.get('inserted_scenes_count', 0) or 0)} "
        f"inline={int(seam_outcomes.get('inline_bridges_count', 0) or 0)} "
        f"hard_cut={int(seam_outcomes.get('hard_cut_count', 0) or 0)} "
        f"blocked_by_budget={int(seam_outcomes.get('blocked_by_budget_count', 0) or 0)}"
    )
    if top_decisions:
        lines.append("- Top seam decisions:")
        for item in top_decisions[:3]:
            if not isinstance(item, dict):
                continue
            from_ref = str(item.get("from_scene_ref") or "").strip()
            to_ref = str(item.get("to_scene_ref") or "").strip()
            seam_score = item.get("seam_score")
            seam_resolution = str(item.get("seam_resolution") or "unknown").strip()
            reason = str(item.get("reason") or "").strip()
            reason_text = f" reason={reason}" if reason else ""
            lines.append(f"  - {from_ref}->{to_ref} score={seam_score} resolution={seam_resolution}{reason_text}")
    if attempt_usage:
        phase_attempts = ", ".join(f"{key}:{value}" for key, value in list(attempt_usage.items())[:6])
        lines.append(f"- Attempts: {phase_attempts}")
    if attention_items:
        lines.append("- Attention items:")
        for item in attention_items[:5]:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "attention").strip()
            severity = str(item.get("severity") or "warning").strip()
            message = str(item.get("message") or "").strip()
            lines.append(f"  - [{severity}] {code}: {message}")
    lines.append(f"- Attention count: {len(attention_items)}")
    if report_path is not None:
        lines.append(f"- Report: {report_path}")
    return "\n".join(lines) + "\n"


def reset_outline_workspace_detailed(
    workspace: Path,
    book_id: str,
    *,
    archive: bool = False,
    keep_working_outline_artifacts: bool = False,
    clear_generated_outline: bool = True,
    clear_pipeline_runs: bool = True,
    dry_run: bool = False,
    force: bool = False,
) -> Tuple[Path, Dict[str, Any]]:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")
    outline_root = book_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)

    if (outline_root / OUTLINE_PIPELINE_PAUSE_MARKER).exists() and not force:
        raise ValueError("Outline run lock marker exists. Use --force to override reset.")

    clear_generated_effective = bool(clear_generated_outline) and not bool(keep_working_outline_artifacts)
    clear_pipeline_effective = bool(clear_pipeline_runs)

    report: Dict[str, Any] = {
        "book_id": book_id,
        "files_deleted": 0,
        "dirs_deleted": 0,
        "files_preserved": 0,
        "dirs_preserved": 0,
        "archive_path": "",
        "archive_targets": 0,
        "dry_run": bool(dry_run),
        "clear_generated_outline": bool(clear_generated_effective),
        "clear_pipeline_runs": bool(clear_pipeline_effective),
        "keep_working_outline_artifacts": bool(keep_working_outline_artifacts),
    }

    protected_root_names = {"archive"}
    pipeline_root_files = {
        OUTLINE_PIPELINE_LATEST,
        OUTLINE_PIPELINE_LATEST_ALIAS,
        OUTLINE_PIPELINE_REPORT_LATEST,
        OUTLINE_PIPELINE_REPORT_LATEST_SNAPSHOT,
        OUTLINE_PIPELINE_PAUSE_MARKER,
    }

    targets: List[Path] = []
    preserved: List[Path] = []

    for child in outline_root.iterdir():
        if child.name in protected_root_names:
            preserved.append(child)
            continue
        if child.name == "pipeline_runs":
            if clear_pipeline_effective:
                targets.append(child)
            else:
                preserved.append(child)
            continue
        if child.name in pipeline_root_files:
            if clear_pipeline_effective:
                targets.append(child)
            else:
                preserved.append(child)
            continue
        if clear_generated_effective:
            targets.append(child)
        else:
            preserved.append(child)

    if archive and targets:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_root = outline_root / "archive" / timestamp
        suffix = 1
        while archive_root.exists():
            suffix += 1
            archive_root = outline_root / "archive" / f"{timestamp}_{suffix}"
        if not dry_run:
            archive_root.mkdir(parents=True, exist_ok=False)
            for target in targets:
                rel = target.relative_to(outline_root)
                dest = archive_root / rel
                if target.is_dir():
                    shutil.copytree(target, dest)
                elif target.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, dest)
            manifest = {
                "book_id": book_id,
                "timestamp": _now_iso(),
                "targets": [str(path.relative_to(outline_root)).replace("\\", "/") for path in targets],
                "keep_working_outline_artifacts": bool(keep_working_outline_artifacts),
                "clear_generated_outline": bool(clear_generated_effective),
                "clear_pipeline_runs": bool(clear_pipeline_effective),
            }
            _write_json(archive_root / "archive_manifest.json", manifest)
        report["archive_path"] = str(archive_root)
        report["archive_targets"] = len(targets)

    report["planned_delete_paths"] = [str(path.relative_to(outline_root)).replace("\\", "/") for path in targets]
    report["planned_preserve_paths"] = [str(path.relative_to(outline_root)).replace("\\", "/") for path in preserved]

    if not dry_run:
        for target in targets:
            if target.is_dir():
                shutil.rmtree(target)
                report["dirs_deleted"] = int(report.get("dirs_deleted", 0)) + 1
            elif target.is_file():
                target.unlink()
                report["files_deleted"] = int(report.get("files_deleted", 0)) + 1
        for keep in preserved:
            if keep.is_dir():
                report["dirs_preserved"] = int(report.get("dirs_preserved", 0)) + 1
            elif keep.is_file():
                report["files_preserved"] = int(report.get("files_preserved", 0)) + 1

        reset_marker = {
            "book_id": book_id,
            "timestamp": _now_iso(),
            "keep_working_outline_artifacts": bool(keep_working_outline_artifacts),
            "clear_generated_outline": bool(clear_generated_effective),
            "clear_pipeline_runs": bool(clear_pipeline_effective),
            "note": "Retained working files are non-authoritative and managed outputs are overwritten by the next outline generation run.",
        }
        _write_json(outline_root / "outline_reset_marker.json", reset_marker)

        _write_json(outline_root / "outline_reset_report.json", report)

    return book_root, report
