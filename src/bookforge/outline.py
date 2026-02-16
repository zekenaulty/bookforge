from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import logging
import re
import shutil

from bookforge.config.env import load_config
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
SUCCESSFUL_OUTLINE_STATUSES = {"SUCCESS", "SUCCESS_WITH_WARNINGS"}


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

        extra = {"book_id": book_id, "step": step_id, "attempt": attempt}
        key_slot = getattr(client, "key_slot", None)
        if key_slot:
            extra["key_slot"] = key_slot

        try:
            response = client.chat(messages, model=model, temperature=0.2, max_tokens=max_tokens)
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

    max_tokens = 98304
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
    current_fingerprint = _fingerprint(
        book=book,
        targets=targets,
        user_prompt=user_prompt,
        notes=notes,
        transition_hints=transition_hints,
        settings=settings,
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

    requires_attention = False

    try:
        for step_id in planned_steps:
            spec = outline_context.step_spec(step_id)
            step_entry = history.get("steps", {}).get(step_id) if isinstance(history.get("steps"), dict) else None
            if (
                resume
                and isinstance(step_entry, dict)
                and str(step_entry.get("status") or "").strip().lower() == "success"
                and (run_dir / spec.handoff_file).exists()
            ):
                payload = _read_json(run_dir / spec.handoff_file)
                handoffs[spec.handoff_key] = payload
                if step_id == outline_context.STEP_04A:
                    runtime["outline_phase_04a_output"] = payload
                continue

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
            if validation_payload.get("warnings"):
                requires_attention = True

    except OutlinePhaseFailure as exc:
        if not isinstance(history.get("steps"), dict):
            history["steps"] = {}
        history["steps"][exc.step_id] = {
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
        requires_attention = True
    except LLMRequestError as exc:
        failed_step = "unknown"
        if isinstance(history.get("steps"), dict):
            for sid in planned_steps:
                if sid not in history["steps"]:
                    failed_step = sid
                    break
        history.setdefault("steps", {})[failed_step] = {
            "status": "paused",
            "attempts": 1,
            "logical_phase": outline_context.STEP_TO_LOGICAL.get(failed_step, failed_step),
            "validation": {
                "status": "fail",
                "errors": [outline_validators.issue("llm_request_error", exc.message, path="<request>")],
                "warnings": [],
                "metrics": {},
            },
        }
        requires_attention = True

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
