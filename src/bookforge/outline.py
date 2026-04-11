from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import logging
import re
import shutil

from bookforge.config.env import load_config, read_env_value, read_int_env
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import LLMResponse, Message
from bookforge.phases.outline import get_handler, step_runtime_defaults
from bookforge.phases.outline import artifacts as outline_artifacts
from bookforge.phases.outline import context as outline_context
from bookforge.phases.outline import validators as outline_validators
from bookforge.prompt.renderer import render_template_file
from bookforge.util.json_extract import extract_json
from bookforge.util.schema import validate_json


logger = logging.getLogger(__name__)

OUTLINE_SCHEMA_VERSION = "1.1"
OUTLINE_MAX_ATTEMPTS = 2
OUTLINE_DEFAULT_MAX_TOKENS = 67000
SUCCESSFUL_OUTLINE_STATUSES = {"SUCCESS", "SUCCESS_WITH_WARNINGS"}
OUTLINE_BACKUP_LATEST_FILE = "outline_backup_latest.json"
OUTLINE_BACKUP_INDEX_FILE = "outline_backups_index.json"
CHAPTER_SCOPED_STEPS = {
    outline_context.STEP_04A,
    outline_context.STEP_04B,
    outline_context.PHASE_03,
    outline_context.PHASE_05,
    outline_context.PHASE_06,
}

PHASE03_T1_INSTRUCTION = (
    "THINKING PHASE: Analyze the chapter and plan your scene draft changes. "
    "Do NOT output the chapter JSON. Return ONLY a small JSON object: "
    "{\"status\":\"ready_to_execute\",\"notes\":[],\"warnings\":[],\"edge_count\":0}."
)

PHASE03_T2_INSTRUCTION = (
    "EXECUTION PHASE: Produce the final chapter-only JSON output for this phase. "
    "Do NOT include analysis or planning text. Output JSON only."
)

PHASE04A_T1_INSTRUCTION = (
    "THINKING PHASE: Audit chapter transition seams and plan candidate_seams. "
    "Do NOT output the chapter JSON. Return ONLY a small JSON object: "
    "{\"status\":\"ready_to_execute\",\"notes\":[],\"warnings\":[],\"edge_count\":0,\"candidate_count\":0}."
)

PHASE04A_T2_INSTRUCTION = (
    "EXECUTION PHASE: Emit the final chapter-only JSON for phase 04A. "
    "Do NOT include analysis or planning text. Output JSON only."
)

PHASE04B_T1_INSTRUCTION = (
    "THINKING PHASE: Plan seam insertions and transition reconciliation for this chapter. "
    "Do NOT output the chapter JSON. Return ONLY a small JSON object: "
    "{\"status\":\"ready_to_execute\",\"notes\":[],\"warnings\":[],\"insertions\":0}."
)

PHASE04B_T2_INSTRUCTION = (
    "EXECUTION PHASE: Emit the final chapter-only JSON for phase 04B, including required "
    "inserted scenes and reconciliation evidence. Do NOT include analysis or planning text. "
    "Output JSON only."
)

PHASE05_T1_INSTRUCTION = (
    "THINKING PHASE: Plan cast refinements for this chapter. "
    "Do NOT output the chapter JSON. Return ONLY a small JSON object: "
    "{\"status\":\"ready_to_execute\",\"notes\":[],\"warnings\":[],\"edge_count\":0}."
)

PHASE05_T2_INSTRUCTION = (
    "EXECUTION PHASE: Emit the final chapter-only JSON for phase 05. "
    "Do NOT include analysis or planning text. Output JSON only."
)

PHASE06_T1_INSTRUCTION = (
    "THINKING PHASE: Plan thread payoff refinements for this chapter. "
    "Do NOT output the chapter JSON. Return ONLY a small JSON object: "
    "{\"status\":\"ready_to_execute\",\"notes\":[],\"warnings\":[],\"edge_count\":0}."
)

PHASE06_T2_INSTRUCTION = (
    "EXECUTION PHASE: Emit the final chapter-only JSON for phase 06. "
    "Do NOT include analysis or planning text. Output JSON only."
)


def _resolve_outline_thinking_level(client: LLMClient, model: str) -> Optional[str]:
    if str(getattr(client, "provider", "")).lower() != "gemini":
        return None

    explicit = str(read_env_value("OUTLINE_THINKING_LEVEL") or "").strip().lower()
    if explicit in {"minimal", "low", "medium", "high"}:
        return explicit

    generic = str(read_env_value("GEMINI_THINKING_LEVEL") or "").strip().lower()
    if generic in {"minimal", "low", "medium", "high"}:
        return generic
    return None


def _resolve_outline_thinking_budget(client: LLMClient, model: str) -> Optional[int]:
    if str(getattr(client, "provider", "")).lower() != "gemini":
        return None

    explicit = read_int_env("OUTLINE_THINKING_BUDGET", 0)
    if isinstance(explicit, int) and explicit > 0:
        return explicit

    generic = read_int_env("GEMINI_THINKING_BUDGET", 0)
    if isinstance(generic, int) and generic > 0:
        return generic
    return None


def _resolve_step_thinking_level(client: LLMClient, model: str, step_id: str) -> Optional[str]:
    if str(getattr(client, "provider", "")).lower() != "gemini":
        return None

    step_key = {
        outline_context.PHASE_01: "OUTLINE_PHASE_01_THINKING_LEVEL",
        outline_context.PHASE_02: "OUTLINE_PHASE_02_THINKING_LEVEL",
        outline_context.PHASE_03: "OUTLINE_PHASE_03_THINKING_LEVEL",
        outline_context.PHASE_04: "OUTLINE_PHASE_04_THINKING_LEVEL",
        outline_context.STEP_04A: "OUTLINE_PHASE_04A_THINKING_LEVEL",
        outline_context.STEP_04B: "OUTLINE_PHASE_04B_THINKING_LEVEL",
        outline_context.PHASE_05: "OUTLINE_PHASE_05_THINKING_LEVEL",
        outline_context.PHASE_06: "OUTLINE_PHASE_06_THINKING_LEVEL",
    }.get(step_id)
    if step_key:
        explicit = str(read_env_value(step_key) or "").strip().lower()
        if explicit in {"minimal", "low", "medium", "high"}:
            return explicit

    logical_phase = outline_context.STEP_TO_LOGICAL.get(step_id, step_id)
    logical_key = {
        outline_context.PHASE_01: "OUTLINE_PHASE_01_THINKING_LEVEL",
        outline_context.PHASE_02: "OUTLINE_PHASE_02_THINKING_LEVEL",
        outline_context.PHASE_03: "OUTLINE_PHASE_03_THINKING_LEVEL",
        outline_context.PHASE_04: "OUTLINE_PHASE_04_THINKING_LEVEL",
        outline_context.PHASE_05: "OUTLINE_PHASE_05_THINKING_LEVEL",
        outline_context.PHASE_06: "OUTLINE_PHASE_06_THINKING_LEVEL",
    }.get(logical_phase)
    if logical_key:
        explicit_logical = str(read_env_value(logical_key) or "").strip().lower()
        if explicit_logical in {"minimal", "low", "medium", "high"}:
            return explicit_logical

    shared = _resolve_outline_thinking_level(client, model)
    if shared:
        return shared

    if step_id in CHAPTER_SCOPED_STEPS:
        return "high"
    model_lower = str(model or "").strip().lower()
    if "gemini-3-flash" in model_lower:
        return "minimal"
    return "low"


def _resolve_step_thinking_budget(client: LLMClient, model: str, step_id: str) -> Optional[int]:
    if str(getattr(client, "provider", "")).lower() != "gemini":
        return None

    step_key = {
        outline_context.PHASE_01: "OUTLINE_PHASE_01_THINKING_BUDGET",
        outline_context.PHASE_02: "OUTLINE_PHASE_02_THINKING_BUDGET",
        outline_context.PHASE_03: "OUTLINE_PHASE_03_THINKING_BUDGET",
        outline_context.PHASE_04: "OUTLINE_PHASE_04_THINKING_BUDGET",
        outline_context.STEP_04A: "OUTLINE_PHASE_04A_THINKING_BUDGET",
        outline_context.STEP_04B: "OUTLINE_PHASE_04B_THINKING_BUDGET",
        outline_context.PHASE_05: "OUTLINE_PHASE_05_THINKING_BUDGET",
        outline_context.PHASE_06: "OUTLINE_PHASE_06_THINKING_BUDGET",
    }.get(step_id)
    if step_key:
        explicit = read_int_env(step_key, 0)
        if isinstance(explicit, int) and explicit > 0:
            return explicit

    logical_phase = outline_context.STEP_TO_LOGICAL.get(step_id, step_id)
    logical_key = {
        outline_context.PHASE_01: "OUTLINE_PHASE_01_THINKING_BUDGET",
        outline_context.PHASE_02: "OUTLINE_PHASE_02_THINKING_BUDGET",
        outline_context.PHASE_03: "OUTLINE_PHASE_03_THINKING_BUDGET",
        outline_context.PHASE_04: "OUTLINE_PHASE_04_THINKING_BUDGET",
        outline_context.PHASE_05: "OUTLINE_PHASE_05_THINKING_BUDGET",
        outline_context.PHASE_06: "OUTLINE_PHASE_06_THINKING_BUDGET",
    }.get(logical_phase)
    if logical_key:
        explicit_logical = read_int_env(logical_key, 0)
        if isinstance(explicit_logical, int) and explicit_logical > 0:
            return explicit_logical

    shared = _resolve_outline_thinking_budget(client, model)
    if shared:
        return shared
    return None


def _resolve_phase03_t2_thinking_level(model: str) -> str:
    explicit = str(read_env_value("OUTLINE_PHASE_03_T2_THINKING_LEVEL") or "").strip().lower()
    if explicit in {"minimal", "low", "medium", "high"}:
        return explicit
    model_lower = str(model or "").strip().lower()
    if "gemini-3-flash" in model_lower:
        return "minimal"
    return "low"


def _resolve_phase04a_t2_thinking_level(model: str) -> str:
    explicit = str(read_env_value("OUTLINE_PHASE_04A_T2_THINKING_LEVEL") or "").strip().lower()
    if explicit in {"minimal", "low", "medium", "high"}:
        return explicit
    model_lower = str(model or "").strip().lower()
    if "gemini-3-flash" in model_lower:
        return "minimal"
    return "low"


def _resolve_phase04b_t2_thinking_level(model: str) -> str:
    explicit = str(read_env_value("OUTLINE_PHASE_04B_T2_THINKING_LEVEL") or "").strip().lower()
    if explicit in {"minimal", "low", "medium", "high"}:
        return explicit
    model_lower = str(model or "").strip().lower()
    if "gemini-3-flash" in model_lower:
        return "minimal"
    return "low"


def _resolve_phase05_t2_thinking_level(model: str) -> str:
    explicit = str(read_env_value("OUTLINE_PHASE_05_T2_THINKING_LEVEL") or "").strip().lower()
    if explicit in {"minimal", "low", "medium", "high"}:
        return explicit
    model_lower = str(model or "").strip().lower()
    if "gemini-3-flash" in model_lower:
        return "minimal"
    return "low"


def _resolve_phase06_t2_thinking_level(model: str) -> str:
    explicit = str(read_env_value("OUTLINE_PHASE_06_T2_THINKING_LEVEL") or "").strip().lower()
    if explicit in {"minimal", "low", "medium", "high"}:
        return explicit
    model_lower = str(model or "").strip().lower()
    if "gemini-3-flash" in model_lower:
        return "minimal"
    return "low"


def _apply_thinking_policy(
    *,
    thinking_level: Optional[str],
    thinking_budget: Optional[int],
) -> Tuple[Optional[str], Optional[int]]:
    if isinstance(thinking_budget, int) and thinking_budget > 0:
        return None, thinking_budget
    return thinking_level, None


@dataclass
class OutlinePhaseFailure(Exception):
    step_id: str
    reasons: List[str]
    validator_evidence: List[Dict[str, Any]]

    def __str__(self) -> str:
        message = "; ".join(self.reasons) if self.reasons else "Unknown outline failure"
        return f"{self.step_id}: {message}"


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _extract_phase_json(step_id: str, text: str) -> Dict[str, Any]:
    parsed = extract_json(text, label=f"{step_id} response")
    if not isinstance(parsed, dict):
        raise ValueError(f"{step_id} response must be a JSON object")
    return parsed


def _phase_retry_message(step_id: str, errors: List[Dict[str, Any]]) -> str:
    lines = [
        f"Your previous {step_id} output failed deterministic validation.",
        "Return ONLY a corrected single JSON object.",
        "Fix these issues:",
    ]
    for item in errors[:12]:
        code = str(item.get("code") or "validation_error")
        message = str(item.get("message") or "")
        scene_ref = str(item.get("scene_ref") or "").strip()
        path = str(item.get("path") or "").strip()
        context = scene_ref or path
        if context:
            lines.append(f"- [{code}] {context}: {message}")
        else:
            lines.append(f"- [{code}] {message}")
    lines.append("Do not add commentary outside JSON.")
    return "\n".join(lines)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def _fingerprint(
    *,
    book: Dict[str, Any],
    targets: Dict[str, Any],
    user_prompt: str,
    notes: str,
    transition_hints: Dict[str, Any],
    settings: Dict[str, Any],
) -> str:
    payload = {
        "book": book,
        "targets": targets,
        "user_prompt": user_prompt,
        "notes": notes,
        "transition_hints": transition_hints,
        "settings": settings,
    }
    return _sha256_text(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def _archive_outline(outline_root: Path) -> None:
    outline_path = outline_root / "outline.json"
    if not outline_path.exists():
        return
    version = 1
    while (outline_root / f"outline_v{version}.json").exists():
        version += 1
    outline_path.replace(outline_root / f"outline_v{version}.json")

    chapters_dir = outline_root / "chapters"
    if chapters_dir.exists():
        chapters_dir.replace(outline_root / f"chapters_v{version}")


def _write_outline_chapters(chapters_dir: Path, chapters: List[Dict[str, Any]]) -> None:
    if chapters_dir.exists():
        shutil.rmtree(chapters_dir)
    chapters_dir.mkdir(parents=True, exist_ok=True)
    for idx, chapter in enumerate(chapters, start=1):
        path = chapters_dir / f"ch_{idx:03d}.json"
        path.write_text(json.dumps(chapter, ensure_ascii=True, indent=2), encoding="utf-8")


def _save_final_outline(book_root: Path, outline: Dict[str, Any], *, new_version: bool) -> Path:
    outline_root = book_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)
    outline_path = outline_root / "outline.json"

    if outline_path.exists():
        if not new_version:
            outline_path.unlink()
        else:
            _archive_outline(outline_root)

    outline_path.write_text(json.dumps(outline, ensure_ascii=True, indent=2), encoding="utf-8")

    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    _write_outline_chapters(outline_root / "chapters", chapters)

    characters = outline.get("characters") if isinstance(outline.get("characters"), list) else []
    threads = outline.get("threads") if isinstance(outline.get("threads"), list) else []
    (outline_root / "characters.json").write_text(
        json.dumps(characters, ensure_ascii=True, indent=2), encoding="utf-8"
    )
    (outline_root / "threads.json").write_text(
        json.dumps(threads, ensure_ascii=True, indent=2), encoding="utf-8"
    )

    state_path = book_root / "state.json"
    state = _read_json(state_path)
    state["outline"] = {"path": "outline/outline.json"}
    if str(state.get("status") or "").upper() in {"NEW", ""}:
        state["status"] = "OUTLINED"
    validate_json(state, "state")
    _write_json(state_path, state)
    return outline_path


def _is_error_v1_payload(payload: Dict[str, Any]) -> bool:
    return str(payload.get("schema_version") or "").strip() == "error_v1"


def _step_attempt_usage(history: Dict[str, Any]) -> Dict[str, str]:
    steps = history.get("steps") if isinstance(history.get("steps"), dict) else {}
    usage: Dict[str, str] = {}
    for step_id in outline_context.STEP_ORDER:
        entry = steps.get(step_id) if isinstance(steps, dict) else None
        if not isinstance(entry, dict):
            continue
        attempts = int(entry.get("attempts") or 0)
        usage[step_id] = f"{attempts}/{OUTLINE_MAX_ATTEMPTS}"
    return usage


def _history_reason_codes(history: Dict[str, Any]) -> List[str]:
    steps = history.get("steps") if isinstance(history.get("steps"), dict) else {}
    codes: List[str] = []
    for step_id in outline_context.STEP_ORDER:
        entry = steps.get(step_id) if isinstance(steps, dict) else None
        if not isinstance(entry, dict):
            continue
        validation = entry.get("validation") if isinstance(entry.get("validation"), dict) else {}
        errors = validation.get("errors") if isinstance(validation.get("errors"), list) else []
        for item in errors:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "").strip()
            if code and code not in codes:
                codes.append(code)
    return codes[:10]


def _phase_failed(history: Dict[str, Any]) -> str:
    steps = history.get("steps") if isinstance(history.get("steps"), dict) else {}
    for step_id in outline_context.STEP_ORDER:
        entry = steps.get(step_id) if isinstance(steps, dict) else None
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status") or "").strip().lower()
        if status in {"error", "paused"}:
            return step_id
    return ""


def _seam_outcomes(history: Dict[str, Any], runtime: Dict[str, Any]) -> Dict[str, int]:
    steps = history.get("steps") if isinstance(history.get("steps"), dict) else {}
    phase04b = steps.get(outline_context.STEP_04B) if isinstance(steps, dict) else None
    validation = phase04b.get("validation") if isinstance(phase04b, dict) else {}
    metrics = validation.get("metrics") if isinstance(validation.get("metrics"), dict) else {}

    routing = runtime.get("phase04_routing") if isinstance(runtime.get("phase04_routing"), dict) else {}
    blocked = routing.get("blocked") if isinstance(routing.get("blocked"), list) else []
    selected = routing.get("selected") if isinstance(routing.get("selected"), list) else []
    exact_conflicts = routing.get("exact_conflicts") if isinstance(routing.get("exact_conflicts"), list) else []

    return {
        "candidates": int(routing.get("candidate_count", 0) or 0),
        "selected": len(selected),
        "blocked_by_budget": len([x for x in blocked if isinstance(x, dict) and str(x.get("reason") or "") == "blocked_by_budget"]),
        "blocked_total": len(blocked),
        "exact_conflicts": len(exact_conflicts),
        "inserted": int(metrics.get("inserted_scene_count", 0) or 0),
        "unresolved_required_insertions": int(metrics.get("unresolved_required_insertions", 0) or 0),
    }


def _clear_pause_marker(run_dir: Path) -> None:
    marker = run_dir / "pipeline_run_paused.json"
    if marker.exists():
        marker.unlink()


def _prune_stale_unknown_step(history: Dict[str, Any]) -> None:
    steps = history.get("steps") if isinstance(history.get("steps"), dict) else None
    if not isinstance(steps, dict):
        return
    unknown_entry = steps.get("unknown")
    if not isinstance(unknown_entry, dict):
        return
    status = str(unknown_entry.get("status") or "").strip().lower()
    if status in {"paused", "error"}:
        steps.pop("unknown", None)


def _build_pipeline_report(
    *,
    book_id: str,
    run_id: str,
    history: Dict[str, Any],
    runtime: Dict[str, Any],
    requires_attention: bool,
) -> Dict[str, Any]:
    phase_failed = _phase_failed(history)
    reason_codes = _history_reason_codes(history)
    attempt_usage = _step_attempt_usage(history)
    seam_outcomes = _seam_outcomes(history, runtime)

    overall_status = "SUCCESS"
    if phase_failed:
        failed_step = history.get("steps", {}).get(phase_failed, {})
        status = str(failed_step.get("status") or "").strip().lower()
        overall_status = "PAUSED" if status == "paused" else "ERROR"
    elif requires_attention:
        overall_status = "SUCCESS_WITH_WARNINGS"

    report: Dict[str, Any] = {
        "book_id": book_id,
        "run_id": run_id,
        "timestamp": outline_artifacts.utc_now_iso(),
        "overall_status": overall_status,
        "requires_user_attention": requires_attention,
        "phase_failed": phase_failed,
        "reason_codes": reason_codes,
        "attempt_usage": attempt_usage,
        "seam_outcomes": seam_outcomes,
        "mode_values": {
            "strict_transition_hints": bool(history.get("settings", {}).get("strict_transition_hints", False)),
            "strict_transition_bridges": bool(history.get("settings", {}).get("strict_transition_bridges", False)),
            "strict_location_identity": bool(history.get("settings", {}).get("strict_location_identity", True)),
            "transition_insert_budget_per_chapter": int(history.get("settings", {}).get("transition_insert_budget_per_chapter", 2) or 2),
            "allow_transition_scene_insertions": bool(history.get("settings", {}).get("allow_transition_scene_insertions", True)),
            "exact_scene_count": bool(history.get("settings", {}).get("exact_scene_count", False)),
        },
        "attention_items": [],
    }

    if seam_outcomes["blocked_by_budget"] > 0:
        report["attention_items"].append(
            {
                "code": "blocked_by_budget",
                "severity": "warning",
                "message": f"{seam_outcomes['blocked_by_budget']} seam candidates were blocked by insertion budget.",
            }
        )
    if seam_outcomes["exact_conflicts"] > 0:
        report["attention_items"].append(
            {
                "code": "exact_scene_count_transition_conflict",
                "severity": "error",
                "message": f"{seam_outcomes['exact_conflicts']} transition insertions conflict with exact scene-count mode.",
            }
        )
    if seam_outcomes["unresolved_required_insertions"] > 0:
        report["attention_items"].append(
            {
                "code": "transition_insertion_required",
                "severity": "error",
                "message": f"{seam_outcomes['unresolved_required_insertions']} required insertion candidates were unresolved.",
            }
        )

    return report


def load_latest_outline_pipeline_report(
    workspace: Path,
    book_id: str,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    book_root = workspace / "books" / book_id
    outline_root = book_root / "outline"
    if not outline_root.exists():
        return None, {}
    report_path = outline_artifacts.load_report_path(outline_root)
    if report_path is None:
        return None, {}
    try:
        payload = _read_json(report_path)
    except Exception:
        return None, {}
    if not isinstance(payload, dict):
        return None, {}
    return report_path, payload


def format_outline_pipeline_summary(
    report: Dict[str, Any],
    report_path: Optional[Path] = None,
) -> str:
    if not isinstance(report, dict):
        return ""
    status = str(report.get("overall_status") or "UNKNOWN").strip()
    phase_failed = str(report.get("phase_failed") or "").strip()
    reason_codes = report.get("reason_codes") if isinstance(report.get("reason_codes"), list) else []
    seam = report.get("seam_outcomes") if isinstance(report.get("seam_outcomes"), dict) else {}
    attention_items = report.get("attention_items") if isinstance(report.get("attention_items"), list) else []

    lines: List[str] = [
        "Outline pipeline summary:",
        f"- Result: {status}",
    ]
    if phase_failed:
        lines.append(f"- Phase failed: {phase_failed}")
    if reason_codes:
        lines.append(f"- Reason codes: {', '.join([str(item) for item in reason_codes[:6]])}")

    lines.append(
        "- Seam outcomes: "
        f"candidates={int(seam.get('candidates', 0) or 0)} "
        f"selected={int(seam.get('selected', 0) or 0)} "
        f"inserted={int(seam.get('inserted', 0) or 0)} "
        f"blocked={int(seam.get('blocked_total', 0) or 0)} "
        f"exact_conflicts={int(seam.get('exact_conflicts', 0) or 0)} "
        f"unresolved_required_insertions={int(seam.get('unresolved_required_insertions', 0) or 0)}"
    )
    if attention_items:
        lines.append(f"- Attention items: {len(attention_items)}")
    if report_path is not None:
        lines.append(f"- Report: {report_path}")
    return "\n".join(lines) + "\n"


def _resolve_outline_payload_from_run(run_dir: Path) -> Tuple[Dict[str, Any], str]:
    candidates: List[Tuple[str, str]] = [
        ("outline_final_v1_1.json", "outline"),
        ("outline_cast_refined_v1_1.json", "outline"),
        ("outline_transitions_refined_v1_1.json", "outline"),
        ("phase_04a_output.json", "wrapper"),
        ("outline_draft_v1_1.json", "outline"),
    ]
    for filename, mode in candidates:
        path = run_dir / filename
        if not path.exists():
            continue
        try:
            payload = _read_json(path)
        except Exception:
            continue
        outline_payload: Dict[str, Any]
        if mode == "wrapper":
            if not isinstance(payload.get("outline"), dict):
                continue
            outline_payload = payload.get("outline")
        else:
            if not isinstance(payload, dict):
                continue
            outline_payload = payload
        chapters = outline_payload.get("chapters")
        if not isinstance(chapters, list) or not chapters:
            continue
        return deepcopy(outline_payload), filename
    raise FileNotFoundError(
        f"Could not resolve recoverable outline payload in run: {run_dir}"
    )


def _normalize_and_validate_outline_for_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = outline_validators.normalize_outline_for_write(payload)
    validate_json(normalized, "outline")
    return normalized


def _load_backup_index(outline_root: Path) -> Dict[str, Any]:
    path = outline_root / OUTLINE_BACKUP_INDEX_FILE
    if not path.exists():
        return {
            "schema_version": "outline_backup_index_v1",
            "updated_at": outline_artifacts.utc_now_iso(),
            "backups": [],
        }
    try:
        payload = _read_json(path)
    except Exception:
        return {
            "schema_version": "outline_backup_index_v1",
            "updated_at": outline_artifacts.utc_now_iso(),
            "backups": [],
        }
    if not isinstance(payload, dict):
        return {
            "schema_version": "outline_backup_index_v1",
            "updated_at": outline_artifacts.utc_now_iso(),
            "backups": [],
        }
    if not isinstance(payload.get("backups"), list):
        payload["backups"] = []
    return payload


def _write_backup_index(outline_root: Path, payload: Dict[str, Any]) -> None:
    payload["updated_at"] = outline_artifacts.utc_now_iso()
    _write_json(outline_root / OUTLINE_BACKUP_INDEX_FILE, payload)


def backup_outline_run(
    *,
    workspace: Path,
    book_id: str,
    run_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
    require_success: bool = True,
    copy_run_artifacts: bool = True,
) -> Path:
    book_root = workspace / "books" / book_id
    outline_root = book_root / "outline"
    if not outline_root.exists():
        raise FileNotFoundError(f"Missing outline directory: {outline_root}")

    resolved_run_id = str(run_id or "").strip()
    if not resolved_run_id:
        resolved_run_id = str(outline_artifacts.read_latest_run_id(outline_root) or "").strip()
    if not resolved_run_id:
        raise FileNotFoundError("No outline run available to back up.")

    run_dir = outline_root / "pipeline_runs" / resolved_run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run not found: {run_dir}")

    report_path = run_dir / outline_artifacts.PIPELINE_REPORT_FILE
    report: Dict[str, Any] = {}
    if report_path.exists():
        try:
            report = _read_json(report_path)
        except Exception:
            report = {}

    status = str(report.get("overall_status") or "").strip().upper()
    if require_success and status not in SUCCESSFUL_OUTLINE_STATUSES:
        raise ValueError(
            f"Run {resolved_run_id} has status {status or 'UNKNOWN'}; use --allow-non-success to back up anyway."
        )

    outline_payload, source_artifact = _resolve_outline_payload_from_run(run_dir)
    final_outline = _normalize_and_validate_outline_for_snapshot(outline_payload)
    outline_hash = _sha256_text(json.dumps(final_outline, ensure_ascii=True, sort_keys=True))

    stamp = outline_artifacts.utc_now_iso().replace(":", "").replace("-", "").replace("T", "_").replace("Z", "")
    root = output_dir if output_dir is not None else (workspace / "backups" / "outline_completed" / book_id)
    backup_dir = root / f"{resolved_run_id}_{stamp}"
    outline_snapshot_dir = backup_dir / "outline_snapshot"
    pipeline_snapshot_dir = backup_dir / "pipeline_run"
    outline_snapshot_dir.mkdir(parents=True, exist_ok=True)
    if copy_run_artifacts:
        pipeline_snapshot_dir.mkdir(parents=True, exist_ok=True)

    # Write canonical snapshot from run-derived payload.
    _write_json(outline_snapshot_dir / "outline.json", final_outline)
    _write_outline_chapters(outline_snapshot_dir / "chapters", final_outline.get("chapters", []))
    _write_json(
        outline_snapshot_dir / "characters.json",
        final_outline.get("characters") if isinstance(final_outline.get("characters"), list) else [],
    )
    _write_json(
        outline_snapshot_dir / "threads.json",
        final_outline.get("threads") if isinstance(final_outline.get("threads"), list) else [],
    )

    # Carry through draft prompt and location registry pointers if present.
    for rel_name in ("outline.draft.user.json", "location_registry_active.json"):
        source = outline_root / rel_name
        if source.exists():
            shutil.copy2(source, outline_snapshot_dir / rel_name)

    if copy_run_artifacts:
        shutil.copytree(run_dir, pipeline_snapshot_dir, dirs_exist_ok=True)

    manifest = {
        "schema_version": "outline_backup_manifest_v1",
        "created_at": outline_artifacts.utc_now_iso(),
        "book_id": book_id,
        "source_run_id": resolved_run_id,
        "source_run_path": outline_artifacts.relpath(workspace, run_dir),
        "source_report_path": outline_artifacts.relpath(workspace, report_path) if report_path.exists() else "",
        "source_status": status or "UNKNOWN",
        "source_outline_artifact": source_artifact,
        "outline_hash": outline_hash,
        "backup_root": outline_artifacts.relpath(workspace, backup_dir),
        "copy_run_artifacts": bool(copy_run_artifacts),
        "files": {
            "outline": "outline_snapshot/outline.json",
            "chapters": "outline_snapshot/chapters",
            "characters": "outline_snapshot/characters.json",
            "threads": "outline_snapshot/threads.json",
            "pipeline_run": "pipeline_run" if copy_run_artifacts else "",
        },
    }
    _write_json(backup_dir / "backup_manifest.json", manifest)

    # Update backup pointers for quick discovery.
    index = _load_backup_index(outline_root)
    backups = index.get("backups") if isinstance(index.get("backups"), list) else []
    backups.append(
        {
            "created_at": manifest["created_at"],
            "run_id": resolved_run_id,
            "status": manifest["source_status"],
            "outline_hash": outline_hash,
            "path": outline_artifacts.relpath(workspace, backup_dir),
            "source_outline_artifact": source_artifact,
        }
    )
    index["backups"] = backups[-200:]
    _write_backup_index(outline_root, index)
    _write_json(
        outline_root / OUTLINE_BACKUP_LATEST_FILE,
        {
            "schema_version": "outline_backup_latest_v1",
            "updated_at": outline_artifacts.utc_now_iso(),
            "path": outline_artifacts.relpath(workspace, backup_dir),
            "run_id": resolved_run_id,
            "outline_hash": outline_hash,
        },
    )
    return backup_dir


def _resolve_backup_path(workspace: Path, book_root: Path, backup_path: Optional[Path]) -> Path:
    if backup_path is not None:
        if backup_path.is_absolute():
            resolved = backup_path
        else:
            resolved = (workspace / backup_path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Backup path not found: {resolved}")
        return resolved

    outline_root = book_root / "outline"
    latest = outline_root / OUTLINE_BACKUP_LATEST_FILE
    if latest.exists():
        payload = _read_json(latest)
        rel = str(payload.get("path") or "").strip()
        if rel:
            candidate = workspace / rel
            if candidate.exists():
                return candidate
    raise FileNotFoundError("No outline backup found. Create one with `bookforge outline backup`.")


def restore_outline_state(
    *,
    workspace: Path,
    book_id: str,
    run_id: Optional[str] = None,
    backup_path: Optional[Path] = None,
    overwrite_current: bool = False,
    set_latest_run_pointer: bool = False,
) -> Path:
    if run_id and backup_path is not None:
        raise ValueError("Provide either run_id or backup_path, not both.")

    book_root = workspace / "books" / book_id
    outline_root = book_root / "outline"
    if not outline_root.exists():
        raise FileNotFoundError(f"Missing outline directory: {outline_root}")

    final_outline: Dict[str, Any]
    resolved_run_id = str(run_id or "").strip()

    if resolved_run_id:
        run_dir = outline_root / "pipeline_runs" / resolved_run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run not found: {run_dir}")
        payload, _source_artifact = _resolve_outline_payload_from_run(run_dir)
        final_outline = _normalize_and_validate_outline_for_snapshot(payload)
        if set_latest_run_pointer:
            outline_artifacts.write_latest_pointer(outline_root, resolved_run_id)
            report_path = run_dir / outline_artifacts.PIPELINE_REPORT_FILE
            if report_path.exists():
                outline_artifacts.write_latest_report_pointer(outline_root, resolved_run_id)
    else:
        source = _resolve_backup_path(workspace, book_root, backup_path)
        snapshot_outline = source / "outline_snapshot" / "outline.json"
        if not snapshot_outline.exists():
            raise FileNotFoundError(f"Backup outline snapshot missing: {snapshot_outline}")
        payload = _read_json(snapshot_outline)
        if not isinstance(payload, dict):
            raise ValueError(f"Backup outline payload is invalid: {snapshot_outline}")
        final_outline = _normalize_and_validate_outline_for_snapshot(payload)

        if set_latest_run_pointer:
            manifest_path = source / "backup_manifest.json"
            if manifest_path.exists():
                manifest = _read_json(manifest_path)
                maybe_run_id = str(manifest.get("source_run_id") or "").strip()
                if maybe_run_id and (outline_root / "pipeline_runs" / maybe_run_id).exists():
                    outline_artifacts.write_latest_pointer(outline_root, maybe_run_id)
                    run_report = (
                        outline_root / "pipeline_runs" / maybe_run_id / outline_artifacts.PIPELINE_REPORT_FILE
                    )
                    if run_report.exists():
                        outline_artifacts.write_latest_report_pointer(outline_root, maybe_run_id)

    return _save_final_outline(book_root, final_outline, new_version=not overwrite_current)


def _load_prior_handoffs_for_start(
    *,
    book_root: Path,
    from_step: str,
    current_run_dir: Path,
    handoffs: Dict[str, Any],
) -> None:
    start_index = outline_context.STEP_ORDER.index(from_step)
    if start_index == 0:
        return

    latest_run_id = outline_artifacts.read_latest_run_id(book_root / "outline")
    if not latest_run_id:
        raise FileNotFoundError(
            f"Cannot start from {from_step}: no previous outline pipeline run found."
        )

    latest_run_dir = (book_root / "outline" / "pipeline_runs" / latest_run_id)
    for index in range(0, start_index):
        step_id = outline_context.STEP_ORDER[index]
        spec = outline_context.step_spec(step_id)
        source = latest_run_dir / spec.handoff_file
        if not source.exists():
            raise FileNotFoundError(
                f"Cannot start from {from_step}: missing dependency artifact {source.name} in run {latest_run_id}."
            )
        payload = _read_json(source)
        handoffs[spec.handoff_key] = payload
        target = current_run_dir / spec.handoff_file
        if not target.exists():
            _write_json(target, payload)


def _render_values_for_step(
    *,
    step_id: str,
    book: Dict[str, Any],
    targets: Dict[str, Any],
    notes: str,
    user_prompt: str,
    transition_hints: Dict[str, Any],
    scene_count_policy: Dict[str, Any],
    handoffs: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Dict[str, Any]:
    handler = get_handler(step_id)
    extras: Dict[str, Any] = {}
    if hasattr(handler, "prompt_extras"):
        maybe = handler.prompt_extras(runtime)
        if isinstance(maybe, dict):
            extras.update(maybe)
    return outline_context.base_prompt_values(
        book=book,
        targets=targets,
        notes=notes,
        user_prompt=user_prompt,
        transition_hints=transition_hints,
        scene_count_policy=scene_count_policy,
        handoffs=handoffs,
        extras=extras,
    )


def _is_pause_error(exc: LLMRequestError) -> bool:
    status = int(exc.status_code or 0)
    return status in {429, 500, 503}


def _write_pause_marker(
    *,
    run_dir: Path,
    step_id: str,
    exc: LLMRequestError,
) -> Path:
    marker = run_dir / "pipeline_run_paused.json"
    payload = {
        "step_id": step_id,
        "status_code": exc.status_code,
        "message": exc.message,
        "retry_after_seconds": exc.retry_after_seconds,
        "created_at": outline_artifacts.utc_now_iso(),
    }
    _write_json(marker, payload)
    return marker


def _is_chapter_scoped_step(step_id: str) -> bool:
    return step_id in CHAPTER_SCOPED_STEPS


def _chapter_artifact_prefix(step_id: str, chapter_id: int) -> str:
    return f"{step_id}_chapter_{int(chapter_id):03d}"


def _chapter_artifact_name(step_id: str, chapter_id: int, kind: str, attempt: Optional[int] = None) -> str:
    prefix = _chapter_artifact_prefix(step_id, chapter_id)
    if attempt is not None:
        return f"{prefix}_{kind}_{int(attempt)}.json"
    return f"{prefix}_{kind}.json"


def _phase_checkpoint_path(run_dir: Path, step_id: str) -> Path:
    return run_dir / f"{step_id}_checkpoint.json"


def _chapter_id_from_chapter(chapter: Dict[str, Any], fallback: int) -> int:
    try:
        value = int(chapter.get("chapter_id"))
    except (TypeError, ValueError):
        value = fallback
    return value


def _outline_chapter_ids(outline: Dict[str, Any]) -> List[int]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    ids: List[int] = []
    for idx, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            continue
        ids.append(_chapter_id_from_chapter(chapter, idx))
    return ids


def _outline_chapter_map(outline: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    chapters = outline.get("chapters") if isinstance(outline.get("chapters"), list) else []
    mapping: Dict[int, Dict[str, Any]] = {}
    for idx, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            continue
        mapping[_chapter_id_from_chapter(chapter, idx)] = chapter
    return mapping


def _extract_chapter(outline: Dict[str, Any], chapter_id: int) -> Dict[str, Any]:
    mapping = _outline_chapter_map(outline)
    chapter = mapping.get(int(chapter_id))
    if not isinstance(chapter, dict):
        raise ValueError(f"Missing chapter {chapter_id} in outline payload")
    return deepcopy(chapter)


def _merge_registry_entries(
    current: List[Dict[str, Any]],
    incoming: Any,
    *,
    id_key: str,
) -> List[Dict[str, Any]]:
    if not isinstance(incoming, list):
        return current
    merged: List[Dict[str, Any]] = [deepcopy(item) for item in current if isinstance(item, dict)]
    index_by_id: Dict[str, int] = {}
    for idx, item in enumerate(merged):
        item_id = str(item.get(id_key) or "").strip()
        if item_id:
            index_by_id[item_id] = idx
    for item in incoming:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get(id_key) or "").strip()
        if not item_id:
            continue
        if item_id in index_by_id:
            merged[index_by_id[item_id]] = deepcopy(item)
        else:
            index_by_id[item_id] = len(merged)
            merged.append(deepcopy(item))
    return merged


def _merge_target_chapter_outline(
    base_outline: Dict[str, Any],
    *,
    chapter_id: int,
    chapter_patch: Dict[str, Any],
    registry_updates: Dict[str, Any],
) -> Dict[str, Any]:
    merged = deepcopy(base_outline)
    chapters = merged.get("chapters") if isinstance(merged.get("chapters"), list) else []
    replaced = False
    for idx, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            continue
        cid = _chapter_id_from_chapter(chapter, idx)
        if cid == int(chapter_id):
            patch_id = _chapter_id_from_chapter(chapter_patch, chapter_id)
            if patch_id != int(chapter_id):
                raise ValueError(
                    f"Chapter patch id mismatch for {chapter_id}; received chapter_id={patch_id}"
                )
            chapters[idx - 1] = deepcopy(chapter_patch)
            replaced = True
            break
    if not replaced:
        raise ValueError(f"Cannot merge chapter patch; chapter {chapter_id} not found")
    merged["chapters"] = chapters

    merged["characters"] = _merge_registry_entries(
        merged.get("characters") if isinstance(merged.get("characters"), list) else [],
        registry_updates.get("characters"),
        id_key="character_id",
    )
    merged["threads"] = _merge_registry_entries(
        merged.get("threads") if isinstance(merged.get("threads"), list) else [],
        registry_updates.get("threads"),
        id_key="thread_id",
    )
    return merged


def _compose_outline_from_spine_sections(
    *,
    spine: Dict[str, Any],
    sections: Dict[str, Any],
) -> Dict[str, Any]:
    spine_chapters = spine.get("chapters") if isinstance(spine.get("chapters"), list) else []
    sections_chapters = sections.get("chapters") if isinstance(sections.get("chapters"), list) else []
    sections_by_id: Dict[int, List[Dict[str, Any]]] = {}
    for chapter in sections_chapters:
        if not isinstance(chapter, dict):
            continue
        try:
            chapter_id = int(chapter.get("chapter_id"))
        except (TypeError, ValueError):
            chapter_id = 0
        if not chapter_id:
            continue
        raw_sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        sections_by_id[chapter_id] = [deepcopy(item) for item in raw_sections if isinstance(item, dict)]

    outline: Dict[str, Any] = {
        "schema_version": OUTLINE_SCHEMA_VERSION,
        "chapters": [],
        "characters": [],
        "threads": [],
    }
    for index, chapter in enumerate(spine_chapters, start=1):
        if not isinstance(chapter, dict):
            continue
        chapter_id = _chapter_id_from_chapter(chapter, index)
        chapter_payload = deepcopy(chapter)
        chapter_payload["chapter_id"] = chapter_id
        raw_sections = sections_by_id.get(chapter_id, [])
        prepared_sections: List[Dict[str, Any]] = []
        for section in raw_sections:
            section_payload = deepcopy(section)
            if not isinstance(section_payload.get("scenes"), list):
                section_payload["scenes"] = []
            prepared_sections.append(section_payload)
        chapter_payload["sections"] = prepared_sections
        outline["chapters"].append(chapter_payload)
    return outline


def _chapter_hash(chapter: Dict[str, Any]) -> str:
    return _sha256_text(json.dumps(chapter, ensure_ascii=True, sort_keys=True))


def _validate_chapter_invariants(
    *,
    before_outline: Dict[str, Any],
    after_outline: Dict[str, Any],
    target_chapter_id: int,
    baseline_chapter_ids: List[int],
) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    before_ids = _outline_chapter_ids(before_outline)
    after_ids = _outline_chapter_ids(after_outline)

    if after_ids != baseline_chapter_ids:
        errors.append(
            outline_validators.issue(
                "chapter_set_mismatch",
                "Chapter id/order changed during chapter-scoped merge.",
                path="outline.chapters",
            )
        )
    if before_ids != baseline_chapter_ids:
        errors.append(
            outline_validators.issue(
                "chapter_set_mismatch",
                "Pre-merge chapter set does not match baseline.",
                path="outline.chapters",
            )
        )

    before_map = _outline_chapter_map(before_outline)
    after_map = _outline_chapter_map(after_outline)
    for chapter_id in baseline_chapter_ids:
        if chapter_id == int(target_chapter_id):
            continue
        before_chapter = before_map.get(chapter_id)
        after_chapter = after_map.get(chapter_id)
        if not isinstance(before_chapter, dict) or not isinstance(after_chapter, dict):
            continue
        if _chapter_hash(before_chapter) != _chapter_hash(after_chapter):
            errors.append(
                outline_validators.issue(
                    "non_target_chapter_mutation",
                    f"Non-target chapter {chapter_id} mutated during chapter-scoped merge.",
                    path="outline.chapters",
                )
            )
    return errors


def _initial_phase_checkpoint(step_id: str, run_mode: str) -> Dict[str, Any]:
    return {
        "schema_version": "outline_phase_checkpoint_v1",
        "step_id": step_id,
        "phase_run_mode": run_mode,
        "chapter_attempts": {},
        "resume_cursor": {},
        "updated_at": outline_artifacts.utc_now_iso(),
    }


def _load_phase_checkpoint(run_dir: Path, step_id: str, run_mode: str) -> Dict[str, Any]:
    path = _phase_checkpoint_path(run_dir, step_id)
    if not path.exists():
        return _initial_phase_checkpoint(step_id, run_mode)
    try:
        payload = _read_json(path)
    except Exception:
        return _initial_phase_checkpoint(step_id, run_mode)
    if not isinstance(payload, dict):
        return _initial_phase_checkpoint(step_id, run_mode)
    if not isinstance(payload.get("chapter_attempts"), dict):
        payload["chapter_attempts"] = {}
    if not isinstance(payload.get("resume_cursor"), dict):
        payload["resume_cursor"] = {}
    payload["step_id"] = step_id
    payload["phase_run_mode"] = run_mode
    return payload


def _save_phase_checkpoint(path: Path, checkpoint: Dict[str, Any]) -> None:
    checkpoint["updated_at"] = outline_artifacts.utc_now_iso()
    _write_json(path, checkpoint)


def _restore_phase04_routing_from_handoff(
    *,
    runtime: Dict[str, Any],
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
) -> None:
    if runtime.get("phase04_routing_by_chapter"):
        return
    payload = handoffs.get("outline_phase_04a_output")
    if not isinstance(payload, dict):
        return
    routing_by_chapter, aggregate = _derive_phase04_routing_from_phase04a_payload(
        payload=payload,
        settings=settings,
    )
    runtime["phase04_routing_by_chapter"] = routing_by_chapter
    runtime["phase04_routing"] = aggregate


def _derive_phase04_routing_from_phase04a_payload(
    *,
    payload: Dict[str, Any],
    settings: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    report = payload.get("phase_report") if isinstance(payload.get("phase_report"), dict) else {}
    candidates = report.get("candidate_seams") if isinstance(report.get("candidate_seams"), list) else []
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for item in candidates:
        if not isinstance(item, dict):
            continue
        from_ref = str(item.get("from_scene_ref") or "").strip()
        if ":" not in from_ref:
            continue
        try:
            chapter_id = int(from_ref.split(":", 1)[0])
        except ValueError:
            continue
        grouped.setdefault(chapter_id, []).append(item)

    routing_by_chapter: Dict[str, Dict[str, Any]] = {}
    for chapter_id, chapter_candidates in grouped.items():
        routing_by_chapter[str(chapter_id)] = outline_validators.route_phase04_candidates(
            candidate_seams=chapter_candidates,
            exact_scene_count=bool(settings.get("exact_scene_count", False)),
            allow_transition_scene_insertions=bool(settings.get("allow_transition_scene_insertions", True)),
            transition_insert_budget_per_chapter=int(
                settings.get("transition_insert_budget_per_chapter", 2) or 2
            ),
        )
    aggregate = _aggregate_phase04_routing(routing_by_chapter)
    return routing_by_chapter, aggregate


def _scene_ref_chapter(value: Any) -> Optional[int]:
    text = str(value or "").strip()
    if not text:
        return None
    if "->" in text:
        text = text.split("->", 1)[0].strip()
    if ":" not in text:
        return None
    try:
        return int(text.split(":", 1)[0])
    except ValueError:
        return None


def _phase_report_item_matches_chapter(item: Any, chapter_id: int) -> bool:
    if isinstance(item, dict):
        for key in ("from_scene_ref", "scene_ref", "candidate_ref", "ref", "to_scene_ref"):
            ref_chapter = _scene_ref_chapter(item.get(key))
            if ref_chapter is not None:
                return ref_chapter == chapter_id
        return False
    ref_chapter = _scene_ref_chapter(item)
    return ref_chapter == chapter_id if ref_chapter is not None else False


def _chapter_scoped_phase_report(
    *,
    step_id: str,
    chapter_id: int,
    chapter_report: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(chapter_report, dict):
        return {}
    scoped = deepcopy(chapter_report)
    scoped.pop("chapter_reports", None)

    if step_id == outline_context.STEP_04A:
        candidates = scoped.get("candidate_seams") if isinstance(scoped.get("candidate_seams"), list) else []
        scoped["candidate_seams"] = [
            item
            for item in candidates
            if _phase_report_item_matches_chapter(item, chapter_id)
        ]
        return scoped

    if step_id == outline_context.STEP_04B:
        for key in (
            "candidate_seams",
            "resolved_candidates",
            "inserted_scene_refs",
            "blocked_by_budget",
            "downgraded_resolution",
            "unresolved_required_insertions",
        ):
            values = scoped.get(key) if isinstance(scoped.get(key), list) else []
            scoped[key] = [
                item
                for item in values
                if _phase_report_item_matches_chapter(item, chapter_id)
            ]
        return scoped

    return scoped


def _aggregate_phase04_routing(routing_by_chapter: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    aggregate = {
        "candidate_count": 0,
        "selected": [],
        "blocked": [],
        "exact_conflicts": [],
    }
    for chapter_routing in routing_by_chapter.values():
        if not isinstance(chapter_routing, dict):
            continue
        aggregate["candidate_count"] += int(chapter_routing.get("candidate_count", 0) or 0)
        for key in ("selected", "blocked", "exact_conflicts"):
            values = chapter_routing.get(key) if isinstance(chapter_routing.get(key), list) else []
            aggregate[key].extend(values)
    return aggregate


def _chapter_render_values(
    *,
    step_id: str,
    chapter_id: int,
    chapter_outline: Dict[str, Any],
    previous_chapter_outline: Optional[Dict[str, Any]],
    next_chapter_outline: Optional[Dict[str, Any]],
    book: Dict[str, Any],
    targets: Dict[str, Any],
    notes: str,
    user_prompt: str,
    transition_hints: Dict[str, Any],
    scene_count_policy: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Dict[str, Any]:
    values: Dict[str, Any] = {
        "book": book,
        "targets": targets,
        "notes": notes,
        "user_prompt": user_prompt,
        "transition_hints": transition_hints,
        "scene_count_policy": scene_count_policy,
        "chapter_target_id": chapter_id,
        "chapter_input_outline": chapter_outline,
        "chapter_prev_outline": previous_chapter_outline or {},
        "chapter_next_outline": next_chapter_outline or {},
    }
    handler = get_handler(step_id)
    if hasattr(handler, "prompt_extras"):
        extras = handler.prompt_extras(runtime)
        if isinstance(extras, dict):
            values.update(extras)
    return values


def _assert_chapter_scoped_template_contract(step_id: str, template_path: Path) -> None:
    text = template_path.read_text(encoding="utf-8")
    required_tokens = ["{{chapter_target_id}}", "{{chapter_input_outline}}"]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(
            f"{step_id} template is not chapter-scoped (missing {missing_str}) at {template_path}. "
            "Run `book update-templates` for the book workspace."
        )


def _extract_chapter_patch_from_response(
    *,
    step_id: str,
    parsed: Dict[str, Any],
    chapter_id: int,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    if step_id in {outline_context.STEP_04A, outline_context.STEP_04B, outline_context.PHASE_05}:
        outline_payload = parsed.get("outline") if isinstance(parsed.get("outline"), dict) else {}
        report_key = "phase_report" if step_id in {outline_context.STEP_04A, outline_context.STEP_04B} else "cast_report"
        chapter_report = parsed.get(report_key) if isinstance(parsed.get(report_key), dict) else {}
    else:
        outline_payload = parsed
        chapter_report = {}

    chapters = outline_payload.get("chapters") if isinstance(outline_payload.get("chapters"), list) else []
    if len(chapters) != 1:
        raise ValueError(
            f"{step_id} chapter-scoped output must include exactly one chapter; received {len(chapters)}"
        )
    chapter_patch = chapters[0] if isinstance(chapters[0], dict) else {}
    patch_id = _chapter_id_from_chapter(chapter_patch, chapter_id)
    if patch_id != int(chapter_id):
        raise ValueError(
            f"{step_id} chapter-scoped output chapter_id mismatch; expected {chapter_id}, received {patch_id}"
        )
    registry_updates = {
        "characters": outline_payload.get("characters"),
        "threads": outline_payload.get("threads"),
    }
    if step_id in {outline_context.STEP_04A, outline_context.STEP_04B}:
        chapter_report = _chapter_scoped_phase_report(
            step_id=step_id,
            chapter_id=chapter_id,
            chapter_report=chapter_report,
        )
    return chapter_patch, chapter_report, registry_updates


def _outline_from_step_payload(step_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if step_id in {outline_context.STEP_04A, outline_context.STEP_04B, outline_context.PHASE_05}:
        return payload.get("outline") if isinstance(payload.get("outline"), dict) else {}
    return payload


def _merge_step_report(
    aggregate: Dict[str, Any],
    chapter_report: Dict[str, Any],
    *,
    chapter_id: int,
) -> Dict[str, Any]:
    merged = deepcopy(aggregate) if isinstance(aggregate, dict) else {}
    chapter_reports = merged.get("chapter_reports") if isinstance(merged.get("chapter_reports"), dict) else {}
    chapter_reports[str(chapter_id)] = deepcopy(chapter_report)
    merged["chapter_reports"] = chapter_reports

    for key, value in chapter_report.items():
        if isinstance(value, list):
            existing = merged.get(key) if isinstance(merged.get(key), list) else []
            merged[key] = existing + value
        elif isinstance(value, (int, float)):
            existing_number = merged.get(key)
            if isinstance(existing_number, (int, float)):
                merged[key] = existing_number + value
            else:
                merged[key] = value
        elif key not in merged:
            merged[key] = deepcopy(value)
    return merged


def _build_step_output_payload(
    *,
    step_id: str,
    merged_outline: Dict[str, Any],
    aggregate_report: Dict[str, Any],
) -> Dict[str, Any]:
    if step_id == outline_context.STEP_04A:
        payload = {
            "schema_version": "transition_refine_v1",
            "outline": merged_outline,
            "phase_report": aggregate_report,
        }
        return payload
    if step_id == outline_context.STEP_04B:
        payload = {
            "schema_version": "transition_refine_v1",
            "outline": merged_outline,
            "phase_report": aggregate_report,
        }
        return payload
    if step_id == outline_context.PHASE_05:
        payload = {
            "schema_version": "cast_refine_v1",
            "outline": merged_outline,
            "cast_report": aggregate_report,
        }
        return payload
    return merged_outline


def _execute_chapter_scoped_step(
    *,
    workspace: Path,
    book_id: str,
    run_dir: Path,
    step_id: str,
    system_prompt: str,
    template_path: Path,
    book: Dict[str, Any],
    targets: Dict[str, Any],
    notes: str,
    user_prompt: str,
    transition_hints: Dict[str, Any],
    scene_count_policy: Dict[str, Any],
    client: LLMClient,
    model: str,
    max_tokens: int,
    thinking_level: Optional[str],
    thinking_budget: Optional[int],
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
    resume: bool,
    force_phase_full_rerun: bool,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], int, Dict[str, Any], str]:
    spec = outline_context.step_spec(step_id)
    handler = get_handler(step_id)
    _assert_chapter_scoped_template_contract(step_id, template_path)
    checkpoint_path = _phase_checkpoint_path(run_dir, step_id)
    run_mode = "force_full_rerun" if force_phase_full_rerun else "resume_incremental"
    checkpoint = _load_phase_checkpoint(run_dir, step_id, run_mode)
    if force_phase_full_rerun:
        checkpoint = _initial_phase_checkpoint(step_id, run_mode)

    if step_id == outline_context.PHASE_03:
        spine_outline = handoffs.get("outline_spine_v1")
        sections_outline = handoffs.get("outline_sections_v1")
        if not isinstance(spine_outline, dict) or not isinstance(sections_outline, dict):
            raise ValueError(f"{step_id} requires outline_spine_v1 and outline_sections_v1 handoffs.")
        base_outline = _compose_outline_from_spine_sections(
            spine=spine_outline,
            sections=sections_outline,
        )
        aggregate_report = {}
    elif step_id == outline_context.STEP_04A:
        base_outline = handoffs.get("outline_draft_v1_1")
        aggregate_report = {}
    elif step_id == outline_context.STEP_04B:
        phase04a_payload = handoffs.get("outline_phase_04a_output")
        if isinstance(phase04a_payload, dict):
            base_outline = phase04a_payload.get("outline")
            aggregate_report = (
                phase04a_payload.get("phase_report")
                if isinstance(phase04a_payload.get("phase_report"), dict)
                else {}
            )
        else:
            base_outline = None
            aggregate_report = {}
    elif step_id == outline_context.PHASE_05:
        base_outline = handoffs.get("outline_transitions_refined_v1_1")
        aggregate_report = {}
    else:
        base_outline = handoffs.get("outline_cast_refined_v1_1")
        aggregate_report = {}

    if not isinstance(base_outline, dict):
        raise ValueError(f"{step_id} requires prior outline handoff to execute chapter-scoped loop.")
    working_outline = deepcopy(base_outline)
    baseline_chapter_ids = _outline_chapter_ids(working_outline)
    if not baseline_chapter_ids:
        raise ValueError(f"{step_id} chapter-scoped loop requires non-empty chapters.")

    chapter_attempts = checkpoint.get("chapter_attempts") if isinstance(checkpoint.get("chapter_attempts"), dict) else {}
    total_attempts = 0
    last_validation: Dict[str, Any] = {"status": "pass", "errors": [], "warnings": [], "metrics": {}}

    if step_id == outline_context.STEP_04B and not runtime.get("phase04_routing_by_chapter"):
        _restore_phase04_routing_from_handoff(runtime=runtime, handoffs=handoffs, settings=settings)

    for chapter_id in baseline_chapter_ids:
        chapter_key = str(chapter_id)
        runtime["current_chapter_id"] = chapter_id
        chapter_entry = chapter_attempts.get(chapter_key) if isinstance(chapter_attempts.get(chapter_key), dict) else {}
        chapter_status = str(chapter_entry.get("status") or "").strip().lower()
        if resume and not force_phase_full_rerun and chapter_status == "success":
            stored_output_path = run_dir / _chapter_artifact_name(step_id, chapter_id, "output")
            if not stored_output_path.exists():
                raise FileNotFoundError(
                    f"Missing chapter output artifact for resumable chapter {chapter_id}: {stored_output_path.name}"
                )
            stored_payload = _read_json(stored_output_path)
            stored_outline = _outline_from_step_payload(step_id, stored_payload)
            if not isinstance(stored_outline, dict):
                raise ValueError(
                    f"Invalid chapter output artifact for chapter {chapter_id}: outline payload missing"
                )
            stored_chapter = _extract_chapter(stored_outline, chapter_id)
            working_outline = _merge_target_chapter_outline(
                working_outline,
                chapter_id=chapter_id,
                chapter_patch=stored_chapter,
                registry_updates={
                    "characters": stored_outline.get("characters"),
                    "threads": stored_outline.get("threads"),
                },
            )
            if step_id in {outline_context.STEP_04A, outline_context.STEP_04B}:
                chapter_report = (
                    stored_payload.get("phase_report")
                    if isinstance(stored_payload.get("phase_report"), dict)
                    else {}
                )
                aggregate_report = _merge_step_report(
                    aggregate_report,
                    chapter_report,
                    chapter_id=chapter_id,
                )
                if step_id == outline_context.STEP_04A:
                    chapter_specific_report = _chapter_scoped_phase_report(
                        step_id=step_id,
                        chapter_id=chapter_id,
                        chapter_report=chapter_report,
                    )
                    chapter_routing = outline_validators.route_phase04_candidates(
                        candidate_seams=chapter_specific_report.get("candidate_seams")
                        if isinstance(chapter_specific_report.get("candidate_seams"), list)
                        else [],
                        exact_scene_count=bool(settings.get("exact_scene_count", False)),
                        allow_transition_scene_insertions=bool(
                            settings.get("allow_transition_scene_insertions", True)
                        ),
                        transition_insert_budget_per_chapter=int(
                            settings.get("transition_insert_budget_per_chapter", 2) or 2
                        ),
                    )
                    runtime.setdefault("phase04_routing_by_chapter", {})
                    runtime["phase04_routing_by_chapter"][chapter_key] = chapter_routing
            elif step_id == outline_context.PHASE_05:
                chapter_report = (
                    stored_payload.get("cast_report")
                    if isinstance(stored_payload.get("cast_report"), dict)
                    else {}
                )
                aggregate_report = _merge_step_report(
                    aggregate_report,
                    chapter_report,
                    chapter_id=chapter_id,
                )
            continue

        chapter_attempt_count = int(chapter_entry.get("attempts") or 0)
        # Resume should be able to retry a failed/paused chapter even if prior attempts
        # were exhausted in the previous invocation.
        if resume and not force_phase_full_rerun and chapter_status in {"error", "paused"}:
            chapter_attempt_count = 0
        retry_message: Optional[str] = None
        chapter_output_payload: Dict[str, Any] = {}
        chapter_validation_payload: Dict[str, Any] = {
            "status": "fail",
            "errors": [outline_validators.issue("chapter_not_run", "chapter was not executed")],
            "warnings": [],
            "metrics": {},
        }

        previous_outline = deepcopy(working_outline)
        previous_ids = _outline_chapter_ids(previous_outline)
        chapter_input_outline = {
            "schema_version": OUTLINE_SCHEMA_VERSION,
            "chapters": [deepcopy(_extract_chapter(working_outline, chapter_id))],
            "characters": deepcopy(
                working_outline.get("characters") if isinstance(working_outline.get("characters"), list) else []
            ),
            "threads": deepcopy(
                working_outline.get("threads") if isinstance(working_outline.get("threads"), list) else []
            ),
        }
        chapter_index = previous_ids.index(chapter_id)
        prev_outline = None
        next_outline = None
        if chapter_index > 0:
            prev_outline = {
                "schema_version": OUTLINE_SCHEMA_VERSION,
                "chapters": [deepcopy(_extract_chapter(working_outline, previous_ids[chapter_index - 1]))],
            }
        if chapter_index < len(previous_ids) - 1:
            next_outline = {
                "schema_version": OUTLINE_SCHEMA_VERSION,
                "chapters": [deepcopy(_extract_chapter(working_outline, previous_ids[chapter_index + 1]))],
            }

        use_two_turn = step_id in {
            outline_context.PHASE_03,
            outline_context.STEP_04A,
            outline_context.STEP_04B,
            outline_context.PHASE_05,
            outline_context.PHASE_06,
        }
        t1_assistant_parts: Optional[List[Dict[str, Any]]] = None
        t1_plan_payload: Optional[Dict[str, Any]] = None
        t1_retry_message: Optional[str] = None
        t1_instruction = PHASE03_T1_INSTRUCTION
        t2_instruction = PHASE03_T2_INSTRUCTION
        if step_id == outline_context.STEP_04A:
            t1_instruction = PHASE04A_T1_INSTRUCTION
            t2_instruction = PHASE04A_T2_INSTRUCTION
        elif step_id == outline_context.STEP_04B:
            t1_instruction = PHASE04B_T1_INSTRUCTION
            t2_instruction = PHASE04B_T2_INSTRUCTION
        elif step_id == outline_context.PHASE_05:
            t1_instruction = PHASE05_T1_INSTRUCTION
            t2_instruction = PHASE05_T2_INSTRUCTION
        elif step_id == outline_context.PHASE_06:
            t1_instruction = PHASE06_T1_INSTRUCTION
            t2_instruction = PHASE06_T2_INSTRUCTION

        while chapter_attempt_count < OUTLINE_MAX_ATTEMPTS:
            chapter_attempt_count += 1
            total_attempts += 1
            if step_id == outline_context.STEP_04B:
                chapter_routing_map = runtime.get("phase04_routing_by_chapter") if isinstance(runtime.get("phase04_routing_by_chapter"), dict) else {}
                runtime["phase04_current_routing"] = deepcopy(
                    chapter_routing_map.get(chapter_key) if isinstance(chapter_routing_map.get(chapter_key), dict) else {}
                )
            chapter_render_values = _chapter_render_values(
                step_id=step_id,
                chapter_id=chapter_id,
                chapter_outline=chapter_input_outline,
                previous_chapter_outline=prev_outline,
                next_chapter_outline=next_outline,
                book=book,
                targets=targets,
                notes=notes,
                user_prompt=user_prompt,
                transition_hints=transition_hints,
                scene_count_policy=scene_count_policy,
                runtime=runtime,
            )
            rendered_prompt = render_template_file(template_path, chapter_render_values)
            input_payload = {
                "step_id": step_id,
                "logical_phase": spec.logical_phase,
                "template": str(template_path),
                "chapter_id": chapter_id,
                "render_values": chapter_render_values,
                "prompt_hash": _sha256_text(rendered_prompt),
            }
            _write_json(
                run_dir / _chapter_artifact_name(step_id, chapter_id, "input"),
                input_payload,
            )

            if use_two_turn and t1_assistant_parts is None:
                t1_messages: List[Message] = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": rendered_prompt},
                    {"role": "user", "content": t1_instruction},
                ]
                if t1_retry_message:
                    t1_messages.append({"role": "user", "content": t1_retry_message})
                t1_request = {"model": model, "temperature": 0.2, "max_tokens": max_tokens}
                t1_level, t1_budget = _apply_thinking_policy(
                    thinking_level=thinking_level,
                    thinking_budget=thinking_budget,
                )
                if t1_budget is not None:
                    t1_request["thinking_config"] = {"thinkingBudget": t1_budget}
                elif t1_level:
                    t1_request["thinking_config"] = {"thinkingLevel": t1_level}
                t1_extra = {
                    "book_id": book_id,
                    "step": step_id,
                    "phase_id": step_id,
                    "chapter": chapter_id,
                    "attempt": chapter_attempt_count,
                    "turn_id": "T1",
                }
                key_slot = getattr(client, "key_slot", None)
                if key_slot:
                    t1_extra["key_slot"] = key_slot
                try:
                    t1_response = client.chat(
                        t1_messages,
                        model=model,
                        temperature=0.2,
                        max_tokens=max_tokens,
                        thinking_level=t1_level,
                        thinking_budget=t1_budget,
                    )
                except LLMRequestError as exc:
                    if should_log_llm():
                        log_llm_error(
                            workspace,
                            f"outline_{step_id}_chapter_{chapter_id}_t1_error",
                            exc,
                            request=t1_request,
                            messages=t1_messages,
                            extra=t1_extra,
                        )
                    chapter_attempts[chapter_key] = {
                        "status": "paused" if _is_pause_error(exc) else "error",
                        "attempts": chapter_attempt_count,
                        "validation_summary": {
                            "status": "fail",
                            "errors": [outline_validators.issue("llm_request_error", exc.message, path="<request>")],
                            "warnings": [],
                            "metrics": {},
                        },
                    }
                    checkpoint["chapter_attempts"] = chapter_attempts
                    checkpoint["resume_cursor"] = {
                        "phase_id": step_id,
                        "next_chapter_id": chapter_id,
                        "reason_code": "rate_limited_retry_exhausted" if _is_pause_error(exc) else "llm_request_error",
                        "updated_at": outline_artifacts.utc_now_iso(),
                    }
                    _save_phase_checkpoint(checkpoint_path, checkpoint)
                    if _is_pause_error(exc):
                        _write_pause_marker(run_dir=run_dir, step_id=step_id, exc=exc)
                    raise

                if should_log_llm():
                    log_llm_response(
                        workspace,
                        f"outline_{step_id}_chapter_{chapter_id}_t1_attempt{chapter_attempt_count}",
                        t1_response,
                        request=t1_request,
                        messages=t1_messages,
                        extra=t1_extra,
                    )

                _write_json(
                    run_dir / _chapter_artifact_name(step_id, chapter_id, "plan_raw", chapter_attempt_count),
                    {"text": t1_response.text, "raw": t1_response.raw},
                )

                try:
                    t1_plan_payload = _extract_phase_json(step_id, t1_response.text)
                except Exception as exc:
                    t1_retry_message = (
                        "Your planning output was invalid. Return ONLY the ready JSON object "
                        "with status, notes, warnings, and edge_count."
                    )
                    retry_message = None
                    plan_errors = [outline_validators.issue("json_parse", str(exc), path="<plan>")]
                    chapter_validation_payload = {
                        "status": "fail",
                        "errors": plan_errors,
                        "warnings": [],
                        "metrics": {},
                    }
                    chapter_attempts[chapter_key] = {
                        "status": "error",
                        "attempts": chapter_attempt_count,
                        "validation_summary": chapter_validation_payload,
                    }
                    checkpoint["chapter_attempts"] = chapter_attempts
                    checkpoint["resume_cursor"] = {
                        "phase_id": step_id,
                        "next_chapter_id": chapter_id,
                        "reason_code": "plan_json_invalid",
                        "updated_at": outline_artifacts.utc_now_iso(),
                    }
                    _save_phase_checkpoint(checkpoint_path, checkpoint)
                    continue
                t1_assistant_parts = (
                    t1_response.assistant_parts if isinstance(t1_response.assistant_parts, list) else None
                )
                _write_json(
                    run_dir / _chapter_artifact_name(step_id, chapter_id, "plan"),
                    {"schema_version": f"{step_id}_plan_v1", "plan": t1_plan_payload},
                )
                t1_retry_message = None
                if t1_assistant_parts:
                    _write_json(
                        run_dir / _chapter_artifact_name(step_id, chapter_id, "plan_assistant_parts", chapter_attempt_count),
                        t1_assistant_parts,
                    )

            messages: List[Message] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": rendered_prompt},
            ]
            provider_name = str(getattr(client, "provider", "")).lower()
            if use_two_turn and t1_assistant_parts and provider_name == "gemini":
                messages.append({"role": "assistant", "parts": t1_assistant_parts})
            if use_two_turn:
                messages.append({"role": "user", "content": t2_instruction})
            if retry_message:
                messages.append({"role": "user", "content": retry_message})

            request = {"model": model, "temperature": 0.2, "max_tokens": max_tokens}
            t2_level: Optional[str] = None
            t2_budget: Optional[int] = None
            if use_two_turn:
                if step_id == outline_context.STEP_04A:
                    t2_level = _resolve_phase04a_t2_thinking_level(model)
                elif step_id == outline_context.STEP_04B:
                    t2_level = _resolve_phase04b_t2_thinking_level(model)
                elif step_id == outline_context.PHASE_05:
                    t2_level = _resolve_phase05_t2_thinking_level(model)
                elif step_id == outline_context.PHASE_06:
                    t2_level = _resolve_phase06_t2_thinking_level(model)
                else:
                    t2_level = _resolve_phase03_t2_thinking_level(model)
            else:
                t2_level, t2_budget = _apply_thinking_policy(
                    thinking_level=thinking_level,
                    thinking_budget=thinking_budget,
                )
            if t2_budget is not None:
                request["thinking_config"] = {"thinkingBudget": t2_budget}
            elif t2_level:
                request["thinking_config"] = {"thinkingLevel": t2_level}
            extra = {
                "book_id": book_id,
                "step": step_id,
                "phase_id": step_id,
                "chapter": chapter_id,
                "attempt": chapter_attempt_count,
            }
            turn_id = runtime.get("turn_id") or runtime.get("phase_turn_id") or runtime.get("turn")
            if use_two_turn:
                extra["turn_id"] = "T2"
            elif step_id in {outline_context.STEP_04A, outline_context.STEP_04B} and turn_id:
                extra["turn_id"] = str(turn_id)
            key_slot = getattr(client, "key_slot", None)
            if key_slot:
                extra["key_slot"] = key_slot

            try:
                response = client.chat(
                    messages,
                    model=model,
                    temperature=0.2,
                    max_tokens=max_tokens,
                    thinking_level=t2_level,
                    thinking_budget=t2_budget,
                )
            except LLMRequestError as exc:
                if should_log_llm():
                    log_llm_error(
                        workspace,
                        f"outline_{step_id}_chapter_{chapter_id}_error",
                        exc,
                        request=request,
                        messages=messages,
                        extra=extra,
                    )
                chapter_attempts[chapter_key] = {
                    "status": "paused" if _is_pause_error(exc) else "error",
                    "attempts": chapter_attempt_count,
                    "validation_summary": {
                        "status": "fail",
                        "errors": [outline_validators.issue("llm_request_error", exc.message, path="<request>")],
                        "warnings": [],
                        "metrics": {},
                    },
                }
                checkpoint["chapter_attempts"] = chapter_attempts
                checkpoint["resume_cursor"] = {
                    "phase_id": step_id,
                    "next_chapter_id": chapter_id,
                    "reason_code": "rate_limited_retry_exhausted" if _is_pause_error(exc) else "llm_request_error",
                    "updated_at": outline_artifacts.utc_now_iso(),
                }
                _save_phase_checkpoint(checkpoint_path, checkpoint)
                if _is_pause_error(exc):
                    _write_pause_marker(run_dir=run_dir, step_id=step_id, exc=exc)
                raise

            if should_log_llm():
                log_llm_response(
                    workspace,
                    f"outline_{step_id}_chapter_{chapter_id}_attempt{chapter_attempt_count}",
                    response,
                    request=request,
                    messages=messages,
                    extra=extra,
                )

            _write_json(
                run_dir / _chapter_artifact_name(step_id, chapter_id, "attempt_raw", chapter_attempt_count),
                {"text": response.text, "raw": response.raw},
            )

            errors: List[Dict[str, Any]] = []
            warnings: List[Dict[str, Any]] = []
            metrics: Dict[str, Any] = {}
            parsed: Dict[str, Any] = {}

            try:
                parsed = _extract_phase_json(step_id, response.text)
            except Exception as exc:
                errors.append(outline_validators.issue("json_parse", str(exc), path="<root>"))
            else:
                if _is_error_v1_payload(parsed):
                    validation_result = outline_validators.parse_error_v1(parsed, step_id)
                    errors.extend(validation_result.errors)
                    warnings.extend(validation_result.warnings)
                    metrics.update(validation_result.metrics)
                else:
                    try:
                        chapter_patch, chapter_report, registry_updates = _extract_chapter_patch_from_response(
                            step_id=step_id,
                            parsed=parsed,
                            chapter_id=chapter_id,
                        )
                    except Exception as exc:
                        errors.append(
                            outline_validators.issue(
                                "chapter_scoped_payload_expected",
                                str(exc),
                                path="outline.chapters",
                            )
                        )
                    else:
                        single_outline_payload = deepcopy(parsed)
                        if step_id in {outline_context.STEP_04A, outline_context.STEP_04B, outline_context.PHASE_05}:
                            single_outline_payload["outline"] = {
                                "schema_version": OUTLINE_SCHEMA_VERSION,
                                "chapters": [deepcopy(chapter_patch)],
                                "characters": deepcopy(registry_updates.get("characters") or []),
                                "threads": deepcopy(registry_updates.get("threads") or []),
                            }
                        else:
                            single_outline_payload = {
                                "schema_version": OUTLINE_SCHEMA_VERSION,
                                "chapters": [deepcopy(chapter_patch)],
                                "characters": deepcopy(registry_updates.get("characters") or []),
                                "threads": deepcopy(registry_updates.get("threads") or []),
                            }

                        preprocessed, preprocess_errors = handler.preprocess(
                            single_outline_payload,
                            handoffs=handoffs,
                            settings=settings,
                            runtime=runtime,
                        )
                        errors.extend(preprocess_errors)

                        if step_id == outline_context.STEP_04A:
                            chapter_routing = runtime.get("phase04_routing") if isinstance(runtime.get("phase04_routing"), dict) else {}
                            runtime.setdefault("phase04_routing_by_chapter", {})
                            runtime["phase04_routing_by_chapter"][chapter_key] = deepcopy(chapter_routing)
                        if step_id == outline_context.STEP_04B:
                            chapter_routing_map = runtime.get("phase04_routing_by_chapter") if isinstance(runtime.get("phase04_routing_by_chapter"), dict) else {}
                            runtime["phase04_current_routing"] = deepcopy(
                                chapter_routing_map.get(chapter_key) if isinstance(chapter_routing_map.get(chapter_key), dict) else {}
                            )

                        if step_id in {outline_context.STEP_04A, outline_context.STEP_04B, outline_context.PHASE_05}:
                            pre_outline = preprocessed.get("outline") if isinstance(preprocessed.get("outline"), dict) else {}
                            pre_chapters = pre_outline.get("chapters") if isinstance(pre_outline.get("chapters"), list) else []
                            if pre_chapters and isinstance(pre_chapters[0], dict):
                                chapter_patch = deepcopy(pre_chapters[0])
                            if step_id in {outline_context.STEP_04A, outline_context.STEP_04B}:
                                chapter_report = preprocessed.get("phase_report") if isinstance(preprocessed.get("phase_report"), dict) else chapter_report
                            elif step_id == outline_context.PHASE_05:
                                chapter_report = preprocessed.get("cast_report") if isinstance(preprocessed.get("cast_report"), dict) else chapter_report
                        else:
                            pre_chapters = preprocessed.get("chapters") if isinstance(preprocessed.get("chapters"), list) else []
                            if pre_chapters and isinstance(pre_chapters[0], dict):
                                chapter_patch = deepcopy(pre_chapters[0])
                            registry_updates = {
                                "characters": preprocessed.get("characters"),
                                "threads": preprocessed.get("threads"),
                            }

                        candidate_outline = _merge_target_chapter_outline(
                            previous_outline,
                            chapter_id=chapter_id,
                            chapter_patch=chapter_patch,
                            registry_updates=registry_updates,
                        )
                        invariant_errors = _validate_chapter_invariants(
                            before_outline=previous_outline,
                            after_outline=candidate_outline,
                            target_chapter_id=chapter_id,
                            baseline_chapter_ids=baseline_chapter_ids,
                        )
                        errors.extend(invariant_errors)

                        merged_report = _merge_step_report(
                            aggregate_report,
                            chapter_report,
                            chapter_id=chapter_id,
                        )
                        candidate_payload = _build_step_output_payload(
                            step_id=step_id,
                            merged_outline=candidate_outline,
                            aggregate_report=merged_report,
                        )
                        validation_result = handler.validate(
                            candidate_payload,
                            handoffs=handoffs,
                            settings=settings,
                            runtime=runtime,
                        )
                        errors.extend(validation_result.errors)
                        warnings.extend(validation_result.warnings)
                        metrics.update(validation_result.metrics)

                        if not errors:
                            working_outline = candidate_outline
                            aggregate_report = merged_report
                            chapter_output_payload = candidate_payload

            chapter_validation_payload = {
                "status": "pass" if not errors else "fail",
                "errors": errors,
                "warnings": warnings,
                "metrics": metrics,
            }
            _write_json(
                run_dir / _chapter_artifact_name(step_id, chapter_id, "validation"),
                chapter_validation_payload,
            )
            _write_json(
                run_dir / _chapter_artifact_name(step_id, chapter_id, "output"),
                chapter_output_payload if chapter_output_payload else parsed,
            )
            last_validation = chapter_validation_payload

            if not errors:
                chapter_attempts[chapter_key] = {
                    "status": "success",
                    "attempts": chapter_attempt_count,
                    "validation_summary": chapter_validation_payload,
                }
                checkpoint["chapter_attempts"] = chapter_attempts
                checkpoint["resume_cursor"] = {
                    "phase_id": step_id,
                    "next_chapter_id": chapter_id + 1,
                    "reason_code": "resume_incremental",
                    "updated_at": outline_artifacts.utc_now_iso(),
                }
                _save_phase_checkpoint(checkpoint_path, checkpoint)
                break

            retry_message = _phase_retry_message(step_id, errors)
        else:
            chapter_attempts[chapter_key] = {
                "status": "error",
                "attempts": chapter_attempt_count,
                "validation_summary": chapter_validation_payload,
            }
            checkpoint["chapter_attempts"] = chapter_attempts
            checkpoint["resume_cursor"] = {
                "phase_id": step_id,
                "next_chapter_id": chapter_id,
                "reason_code": "phase_output_truncated_or_invalid_json",
                "updated_at": outline_artifacts.utc_now_iso(),
            }
            _save_phase_checkpoint(checkpoint_path, checkpoint)
            reasons = [
                str(item.get("message") or item.get("code") or "validation_error")
                for item in chapter_validation_payload.get("errors", [])
            ][:8]
            raise OutlinePhaseFailure(
                step_id=step_id,
                reasons=reasons,
                validator_evidence=chapter_validation_payload.get("errors", []),
            )

    checkpoint["chapter_attempts"] = chapter_attempts
    checkpoint["resume_cursor"] = {
        "phase_id": step_id,
        "next_chapter_id": None,
        "reason_code": "complete",
        "updated_at": outline_artifacts.utc_now_iso(),
    }
    _save_phase_checkpoint(checkpoint_path, checkpoint)

    if step_id == outline_context.STEP_04A:
        routing_by_chapter, aggregate_routing = _derive_phase04_routing_from_phase04a_payload(
            payload={
                "phase_report": aggregate_report,
            },
            settings=settings,
        )
        runtime["phase04_routing_by_chapter"] = routing_by_chapter
        runtime["phase04_routing"] = aggregate_routing
        output_payload = {
            "schema_version": "transition_refine_v1",
            "outline": working_outline,
            "phase_report": aggregate_report,
        }
        runtime["outline_phase_04a_output"] = output_payload
    elif step_id == outline_context.STEP_04B:
        runtime["phase04_routing"] = _aggregate_phase04_routing(
            runtime.get("phase04_routing_by_chapter")
            if isinstance(runtime.get("phase04_routing_by_chapter"), dict)
            else {}
        )
        output_payload = {
            "schema_version": "transition_refine_v1",
            "outline": working_outline,
            "phase_report": aggregate_report,
        }
    elif step_id == outline_context.PHASE_05:
        output_payload = {
            "schema_version": "cast_refine_v1",
            "outline": working_outline,
            "cast_report": aggregate_report,
        }
    else:
        output_payload = working_outline

    final_validation = handler.validate(
        output_payload,
        handoffs=handoffs,
        settings=settings,
        runtime=runtime,
    )
    validation_payload = {
        "status": final_validation.status,
        "errors": final_validation.errors,
        "warnings": final_validation.warnings,
        "metrics": final_validation.metrics,
    }
    if validation_payload["status"] != "pass":
        reasons = [
            str(item.get("message") or item.get("code") or "validation_error")
            for item in validation_payload.get("errors", [])
        ][:8]
        raise OutlinePhaseFailure(
            step_id=step_id,
            reasons=reasons,
            validator_evidence=validation_payload.get("errors", []),
        )

    _write_json(run_dir / outline_artifacts.step_artifact_name(step_id, "output"), output_payload)
    _write_json(run_dir / outline_artifacts.step_artifact_name(step_id, "validation"), validation_payload)
    handoff_payload = handler.handoff_payload(output_payload)
    _write_json(run_dir / spec.handoff_file, handoff_payload)
    return (
        output_payload,
        handoff_payload,
        validation_payload,
        total_attempts,
        chapter_attempts,
        outline_artifacts.relpath(run_dir, checkpoint_path),
    )


def _execute_step(
    *,
    workspace: Path,
    book_id: str,
    run_dir: Path,
    step_id: str,
    system_prompt: str,
    template_path: Path,
    render_values: Dict[str, Any],
    client: LLMClient,
    model: str,
    max_tokens: int,
    thinking_level: Optional[str],
    thinking_budget: Optional[int],
    handoffs: Dict[str, Any],
    settings: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], int]:
    spec = outline_context.step_spec(step_id)
    handler = get_handler(step_id)

    rendered_prompt = render_template_file(template_path, render_values)
    input_payload = {
        "step_id": step_id,
        "logical_phase": spec.logical_phase,
        "template": str(template_path),
        "render_values": render_values,
        "prompt_hash": _sha256_text(rendered_prompt),
    }
    _write_json(run_dir / outline_artifacts.step_artifact_name(step_id, "input"), input_payload)

    request = {"model": model, "temperature": 0.2, "max_tokens": max_tokens}
    effective_level, effective_budget = _apply_thinking_policy(
        thinking_level=thinking_level,
        thinking_budget=thinking_budget,
    )
    if effective_budget is not None:
        request["thinking_config"] = {"thinkingBudget": effective_budget}
    elif effective_level:
        request["thinking_config"] = {"thinkingLevel": effective_level}
    attempt = 0
    retry_message: Optional[str] = None
    last_output: Dict[str, Any] = {}
    last_validation: Dict[str, Any] = {
        "status": "fail",
        "errors": [outline_validators.issue("phase_not_run", "step was not executed")],
        "warnings": [],
        "metrics": {},
    }

    while attempt < OUTLINE_MAX_ATTEMPTS:
        attempt += 1
        messages: List[Message] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": rendered_prompt},
        ]
        if retry_message:
            messages.append({"role": "user", "content": retry_message})

        extra = {"book_id": book_id, "step": step_id, "phase_id": step_id, "attempt": attempt}
        key_slot = getattr(client, "key_slot", None)
        if key_slot:
            extra["key_slot"] = key_slot

        try:
            response = client.chat(
                messages,
                model=model,
                temperature=0.2,
                max_tokens=max_tokens,
                thinking_level=effective_level,
                thinking_budget=effective_budget,
            )
        except LLMRequestError as exc:
            if should_log_llm():
                log_llm_error(
                    workspace,
                    f"outline_{step_id}_error",
                    exc,
                    request=request,
                    messages=messages,
                    extra=extra,
                )
            if _is_pause_error(exc):
                _write_pause_marker(run_dir=run_dir, step_id=step_id, exc=exc)
                raise
            raise

        if should_log_llm():
            log_llm_response(
                workspace,
                f"outline_{step_id}_attempt{attempt}",
                response,
                request=request,
                messages=messages,
                extra=extra,
            )

        _write_json(
            run_dir / outline_artifacts.step_artifact_name(step_id, "attempt_raw", attempt),
            {"text": response.text, "raw": response.raw},
        )

        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        metrics: Dict[str, Any] = {}
        parsed: Dict[str, Any] = {}

        try:
            parsed = _extract_phase_json(step_id, response.text)
        except Exception as exc:
            errors.append(outline_validators.issue("json_parse", str(exc), path="<root>"))
        else:
            if _is_error_v1_payload(parsed):
                validation_result = outline_validators.parse_error_v1(parsed, step_id)
            else:
                preprocessed, preprocess_errors = handler.preprocess(
                    parsed,
                    handoffs=handoffs,
                    settings=settings,
                    runtime=runtime,
                )
                validation_result = handler.validate(
                    preprocessed,
                    handoffs=handoffs,
                    settings=settings,
                    runtime=runtime,
                )
                parsed = preprocessed
                errors.extend(preprocess_errors)
            errors.extend(validation_result.errors)
            warnings.extend(validation_result.warnings)
            metrics.update(validation_result.metrics)

        status = "pass" if not errors else "fail"
        validation_payload = {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "metrics": metrics,
        }
        last_output = parsed
        last_validation = validation_payload

        if status == "pass":
            _write_json(run_dir / outline_artifacts.step_artifact_name(step_id, "output"), parsed)
            _write_json(run_dir / outline_artifacts.step_artifact_name(step_id, "validation"), validation_payload)
            handoff_payload = handler.handoff_payload(parsed)
            _write_json(run_dir / spec.handoff_file, handoff_payload)
            return parsed, handoff_payload, validation_payload, attempt

        retry_message = _phase_retry_message(step_id, errors)

    _write_json(run_dir / outline_artifacts.step_artifact_name(step_id, "output"), last_output)
    _write_json(run_dir / outline_artifacts.step_artifact_name(step_id, "validation"), last_validation)
    reasons = [str(item.get("message") or item.get("code") or "validation_error") for item in last_validation.get("errors", [])][:8]
    raise OutlinePhaseFailure(step_id=step_id, reasons=reasons, validator_evidence=last_validation.get("errors", []))


def generate_outline(
    workspace: Path,
    book_id: str,
    new_version: bool = False,
    prompt_file: Optional[Path] = None,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
    *,
    rerun: bool = False,
    resume: bool = False,
    from_phase: Optional[str] = None,
    to_phase: Optional[str] = None,
    phase: Optional[str] = None,
    transition_hints_file: Optional[Path] = None,
    strict_transition_hints: bool = False,
    strict_transition_bridges: bool = True,
    strict_location_identity: bool = True,
    transition_insert_budget_per_chapter: int = 2,
    allow_transition_scene_insertions: bool = True,
    force_rerun_with_draft: bool = False,
    exact_scene_count: bool = False,
    scene_count_range: Optional[str] = None,
    force_phase_full_rerun: bool = False,
    notes: str = "",
) -> Path:
    if new_version and resume:
        raise ValueError("--new-version cannot be combined with --resume")

    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")

    book_path = book_root / "book.json"
    state_path = book_root / "state.json"
    system_path = book_root / "prompts" / "system_v1.md"
    if not book_path.exists():
        raise FileNotFoundError(f"Missing book.json: {book_path}")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state.json: {state_path}")
    if not system_path.exists():
        raise FileNotFoundError(f"Missing system_v1.md: {system_path}")

    book = _read_json(book_path)
    targets = book.get("targets") if isinstance(book.get("targets"), dict) else {}
    system_prompt = system_path.read_text(encoding="utf-8")

    user_prompt = ""
    if prompt_file is not None:
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        user_prompt = prompt_file.read_text(encoding="utf-8").strip()

    transition_hints = outline_context.read_transition_hints(transition_hints_file)
    scene_count_policy = outline_context.build_scene_count_policy(
        exact_scene_count=exact_scene_count,
        scene_count_range=scene_count_range,
    )

    settings: Dict[str, Any] = {
        "strict_transition_hints": bool(strict_transition_hints),
        "strict_transition_bridges": bool(strict_transition_bridges),
        "strict_location_identity": bool(strict_location_identity),
        "transition_insert_budget_per_chapter": max(0, int(transition_insert_budget_per_chapter or 0)),
        "allow_transition_scene_insertions": bool(allow_transition_scene_insertions),
        "exact_scene_count": bool(exact_scene_count),
        "scene_count_range": scene_count_range,
        "scene_count_policy": scene_count_policy,
        "force_phase_full_rerun": bool(force_phase_full_rerun),
    }

    from_step, to_step = outline_context.normalize_phase_selector(
        from_phase=from_phase,
        to_phase=to_phase,
        single_phase=phase,
    )
    planned_steps = outline_context.step_slice(from_step, to_step)

    if client is None:
        config = load_config()
        client = get_llm_client(config, phase="outline")
        if model is None:
            model = resolve_model("outline", config)
    elif model is None:
        model = "default"

    max_tokens = max(4096, read_int_env("BOOKFORGE_OUTLINE_MAX_TOKENS", OUTLINE_DEFAULT_MAX_TOKENS))
    outline_root = book_root / "outline"
    outline_root.mkdir(parents=True, exist_ok=True)

    outline_path = outline_root / "outline.json"
    if outline_path.exists() and not (new_version or rerun or resume):
        raise FileExistsError("outline.json already exists. Use --rerun, --resume, or --new-version.")

    if rerun and (book_root / "draft" / "chapters").exists() and not force_rerun_with_draft:
        chapter_dir = book_root / "draft" / "chapters"
        if any(chapter_dir.glob("ch_*.md")):
            raise ValueError(
                "Drafted scenes exist. Use --force-rerun-with-draft to acknowledge overwrite risk before rerunning outline."
            )

    run_id: str
    run_dir: Path
    history_path: Path
    history: Dict[str, Any]
    fingerprint_settings = deepcopy(settings)
    fingerprint_settings.pop("force_phase_full_rerun", None)
    current_fingerprint = _fingerprint(
        book=book,
        targets=targets,
        user_prompt=user_prompt,
        notes=notes,
        transition_hints=transition_hints,
        settings=fingerprint_settings,
    )

    if resume:
        latest_run_id = outline_artifacts.read_latest_run_id(outline_root)
        if not latest_run_id:
            raise FileNotFoundError("No resumable outline pipeline run found.")
        run_id = latest_run_id
        run_dir = outline_root / "pipeline_runs" / run_id
        history_path = run_dir / outline_artifacts.PIPELINE_HISTORY_FILE
        if not run_dir.exists() or not history_path.exists():
            raise FileNotFoundError(f"Resume target run is missing artifacts: {run_dir}")
        history = outline_artifacts.load_history(history_path)
        existing_fingerprint = str(history.get("fingerprint") or "").strip()
        if existing_fingerprint and existing_fingerprint != current_fingerprint:
            raise ValueError(
                "Resume fingerprint mismatch. Inputs changed since the prior run; use --rerun."
            )
    else:
        run_id, run_dir = outline_artifacts.create_run(book_root)
        history_path = run_dir / outline_artifacts.PIPELINE_HISTORY_FILE
        history = outline_artifacts.load_history(history_path)

    history["book_id"] = book_id
    history["run_id"] = run_id
    history["settings"] = settings
    history["requested_from_step"] = from_step
    history["requested_to_step"] = to_step
    history["fingerprint"] = current_fingerprint

    handoffs: Dict[str, Any] = {}
    runtime = step_runtime_defaults()

    if resume:
        existing_steps = history.get("steps") if isinstance(history.get("steps"), dict) else {}
        for step_id in outline_context.STEP_ORDER:
            spec = outline_context.step_spec(step_id)
            handoff_file = run_dir / spec.handoff_file
            if handoff_file.exists():
                payload = _read_json(handoff_file)
                handoffs[spec.handoff_key] = payload
                if step_id == outline_context.STEP_04A:
                    runtime["outline_phase_04a_output"] = payload
    else:
        _load_prior_handoffs_for_start(
            book_root=book_root,
            from_step=from_step,
            current_run_dir=run_dir,
            handoffs=handoffs,
        )

    outline_artifacts.write_latest_pointer(outline_root, run_id)

    _restore_phase04_routing_from_handoff(
        runtime=runtime,
        handoffs=handoffs,
        settings=settings,
    )

    requires_attention = False

    active_step_id: Optional[str] = None
    try:
        for step_id in planned_steps:
            active_step_id = step_id
            spec = outline_context.step_spec(step_id)
            step_entry = history.get("steps", {}).get(step_id) if isinstance(history.get("steps"), dict) else None
            if (
                resume
                and isinstance(step_entry, dict)
                and str(step_entry.get("status") or "").strip().lower() == "success"
                and (run_dir / spec.handoff_file).exists()
                and not (force_phase_full_rerun and _is_chapter_scoped_step(step_id))
            ):
                payload = _read_json(run_dir / spec.handoff_file)
                handoffs[spec.handoff_key] = payload
                if step_id == outline_context.STEP_04A:
                    runtime["outline_phase_04a_output"] = payload
                continue

            if step_id == outline_context.STEP_04B:
                _restore_phase04_routing_from_handoff(
                    runtime=runtime,
                    handoffs=handoffs,
                    settings=settings,
                )

            if step_id == outline_context.STEP_04B:
                routing = runtime.get("phase04_routing") if isinstance(runtime.get("phase04_routing"), dict) else {}
                exact_conflicts = routing.get("exact_conflicts") if isinstance(routing.get("exact_conflicts"), list) else []
                if exact_conflicts:
                    conflict_errors = [
                        outline_validators.issue(
                            "exact_scene_count_transition_conflict",
                            "Exact scene-count mode conflicts with required transition insertions.",
                            path="phase_report.exact_scene_count_transition_conflict",
                        )
                    ]
                    _write_json(
                        run_dir / outline_artifacts.step_artifact_name(step_id, "validation"),
                        {
                            "status": "fail",
                            "errors": conflict_errors,
                            "warnings": [],
                            "metrics": {"exact_conflicts": len(exact_conflicts)},
                        },
                    )
                    _write_json(
                        run_dir / outline_artifacts.step_artifact_name(step_id, "output"),
                        {
                            "schema_version": "error_v1",
                            "result": "ERROR",
                            "error_type": "validation_error",
                            "reason_code": "phase04_exact_scene_count_transition_conflict",
                            "missing_fields": ["phase_04_selected_candidates_json"],
                            "phase": "phase_04b_transition_execution",
                            "action_hint": "Disable exact scene count mode or reduce required insertion seams.",
                        },
                    )
                    raise OutlinePhaseFailure(
                        step_id=step_id,
                        reasons=[
                            "Exact scene-count mode conflicts with required transition insertion."
                        ],
                        validator_evidence=conflict_errors,
                    )

            template_path = outline_context.resolve_outline_template(book_root, spec.template_name)
            step_thinking_level = _resolve_step_thinking_level(client, model, step_id)
            step_thinking_budget = _resolve_step_thinking_budget(client, model, step_id)
            chapter_attempts: Optional[Dict[str, Any]] = None
            checkpoint_path: Optional[str] = None
            if _is_chapter_scoped_step(step_id):
                (
                    output_payload,
                    handoff_payload,
                    validation_payload,
                    attempts,
                    chapter_attempts,
                    checkpoint_path,
                ) = _execute_chapter_scoped_step(
                    workspace=workspace,
                    book_id=book_id,
                    run_dir=run_dir,
                    step_id=step_id,
                    system_prompt=system_prompt,
                    template_path=template_path,
                    book=book,
                    targets=targets,
                    notes=notes,
                    user_prompt=user_prompt,
                    transition_hints=transition_hints,
                    scene_count_policy=scene_count_policy,
                    client=client,
                    model=model,
                    max_tokens=max_tokens,
                    thinking_level=step_thinking_level,
                    thinking_budget=step_thinking_budget,
                    handoffs=handoffs,
                    settings=settings,
                    runtime=runtime,
                    resume=resume,
                    force_phase_full_rerun=bool(force_phase_full_rerun),
                )
            else:
                render_values = _render_values_for_step(
                    step_id=step_id,
                    book=book,
                    targets=targets,
                    notes=notes,
                    user_prompt=user_prompt,
                    transition_hints=transition_hints,
                    scene_count_policy=scene_count_policy,
                    handoffs=handoffs,
                    runtime=runtime,
                )
                output_payload, handoff_payload, validation_payload, attempts = _execute_step(
                    workspace=workspace,
                    book_id=book_id,
                    run_dir=run_dir,
                    step_id=step_id,
                    system_prompt=system_prompt,
                    template_path=template_path,
                    render_values=render_values,
                    client=client,
                    model=model,
                    max_tokens=max_tokens,
                    thinking_level=step_thinking_level,
                    thinking_budget=step_thinking_budget,
                    handoffs=handoffs,
                    settings=settings,
                    runtime=runtime,
                )

            handoffs[spec.handoff_key] = handoff_payload
            if step_id == outline_context.STEP_04A:
                runtime["outline_phase_04a_output"] = output_payload

            if not isinstance(history.get("steps"), dict):
                history["steps"] = {}
            history["steps"][step_id] = {
                "status": "success",
                "attempts": attempts,
                "logical_phase": spec.logical_phase,
                "output_path": outline_artifacts.relpath(run_dir, run_dir / outline_artifacts.step_artifact_name(step_id, "output")),
                "validation": validation_payload,
                "handoff_path": outline_artifacts.relpath(run_dir, run_dir / spec.handoff_file),
            }
            if chapter_attempts is not None:
                history["steps"][step_id]["chapter_attempts"] = chapter_attempts
                history["steps"][step_id]["phase_run_mode"] = (
                    "force_full_rerun" if force_phase_full_rerun else "resume_incremental"
                )
            if checkpoint_path:
                history["steps"][step_id]["checkpoint_path"] = checkpoint_path
            if validation_payload.get("warnings"):
                requires_attention = True

    except OutlinePhaseFailure as exc:
        if not isinstance(history.get("steps"), dict):
            history["steps"] = {}
        history_entry: Dict[str, Any] = {
            "status": "error",
            "attempts": OUTLINE_MAX_ATTEMPTS,
            "logical_phase": outline_context.STEP_TO_LOGICAL.get(exc.step_id, exc.step_id),
            "validation": {
                "status": "fail",
                "errors": exc.validator_evidence,
                "warnings": [],
                "metrics": {},
            },
        }
        if exc.step_id in CHAPTER_SCOPED_STEPS:
            checkpoint_file = _phase_checkpoint_path(run_dir, exc.step_id)
            if checkpoint_file.exists():
                try:
                    checkpoint_payload = _read_json(checkpoint_file)
                except Exception:
                    checkpoint_payload = {}
                if isinstance(checkpoint_payload.get("chapter_attempts"), dict):
                    history_entry["chapter_attempts"] = checkpoint_payload.get("chapter_attempts")
                if isinstance(checkpoint_payload.get("resume_cursor"), dict):
                    history_entry["resume_cursor"] = checkpoint_payload.get("resume_cursor")
                history_entry["phase_run_mode"] = str(
                    checkpoint_payload.get("phase_run_mode") or "resume_incremental"
                )
                history_entry["checkpoint_path"] = outline_artifacts.relpath(run_dir, checkpoint_file)
                attempts = int(
                    sum(
                        int((entry or {}).get("attempts") or 0)
                        for entry in history_entry.get("chapter_attempts", {}).values()
                        if isinstance(entry, dict)
                    )
                )
                if attempts > 0:
                    history_entry["attempts"] = attempts
        history["steps"][exc.step_id] = history_entry
        requires_attention = True
    except LLMRequestError as exc:
        failed_step = active_step_id or ""
        if not failed_step and isinstance(history.get("steps"), dict):
            for sid in planned_steps:
                if sid not in history["steps"]:
                    failed_step = sid
                    break
        if not failed_step:
            failed_step = planned_steps[-1] if planned_steps else "unknown"
        checkpoint_payload: Dict[str, Any] = {}
        if failed_step in CHAPTER_SCOPED_STEPS:
            checkpoint_file = _phase_checkpoint_path(run_dir, failed_step)
            if checkpoint_file.exists():
                try:
                    checkpoint_payload = _read_json(checkpoint_file)
                except Exception:
                    checkpoint_payload = {}
        chapter_attempts = checkpoint_payload.get("chapter_attempts") if isinstance(checkpoint_payload.get("chapter_attempts"), dict) else {}
        resume_cursor = checkpoint_payload.get("resume_cursor") if isinstance(checkpoint_payload.get("resume_cursor"), dict) else {}
        history.setdefault("steps", {})[failed_step] = {
            "status": "paused",
            "attempts": int(
                sum(
                    int((entry or {}).get("attempts") or 0)
                    for entry in chapter_attempts.values()
                    if isinstance(entry, dict)
                )
            )
            if chapter_attempts
            else 1,
            "logical_phase": outline_context.STEP_TO_LOGICAL.get(failed_step, failed_step),
            "validation": {
                "status": "fail",
                "errors": [outline_validators.issue("llm_request_error", exc.message, path="<request>")],
                "warnings": [],
                "metrics": {},
            },
        }
        if chapter_attempts:
            history["steps"][failed_step]["chapter_attempts"] = chapter_attempts
        if resume_cursor:
            history["steps"][failed_step]["resume_cursor"] = resume_cursor
        if checkpoint_payload:
            history["steps"][failed_step]["phase_run_mode"] = str(
                checkpoint_payload.get("phase_run_mode") or "resume_incremental"
            )
            history["steps"][failed_step]["checkpoint_path"] = outline_artifacts.relpath(
                run_dir, _phase_checkpoint_path(run_dir, failed_step)
            )
        requires_attention = True

    if not _phase_failed(history):
        _prune_stale_unknown_step(history)

    outline_artifacts.write_history(history_path, history)

    report = _build_pipeline_report(
        book_id=book_id,
        run_id=run_id,
        history=history,
        runtime=runtime,
        requires_attention=requires_attention,
    )
    validate_json(report, "outline_pipeline_report")
    report_path = run_dir / outline_artifacts.PIPELINE_REPORT_FILE
    _write_json(report_path, report)
    outline_artifacts.write_latest_report_pointer(outline_root, run_id)

    if report.get("overall_status") not in SUCCESSFUL_OUTLINE_STATUSES:
        raise RuntimeError(
            f"Outline pipeline ended with status {report.get('overall_status')}. See {report_path}"
        )

    _clear_pause_marker(run_dir)

    final_outline: Optional[Dict[str, Any]] = None
    if isinstance(handoffs.get("outline_final_v1_1"), dict):
        final_outline = outline_validators.normalize_outline_for_write(handoffs["outline_final_v1_1"])
    elif isinstance(handoffs.get("outline_cast_refined_v1_1"), dict):
        final_outline = outline_validators.normalize_outline_for_write(handoffs["outline_cast_refined_v1_1"])
    elif isinstance(handoffs.get("outline_transitions_refined_v1_1"), dict):
        final_outline = outline_validators.normalize_outline_for_write(handoffs["outline_transitions_refined_v1_1"])

    if final_outline is None:
        return run_dir / outline_artifacts.step_artifact_name(planned_steps[-1], "output")

    validate_json(final_outline, "outline")
    return _save_final_outline(book_root, final_outline, new_version=new_version)
