from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib
import json

from bookforge.config.env import load_config, read_int_env
from bookforge.contracts import (
    ExecutionRequest,
    ExecutionResult,
    MAIN_BRANCH_ID,
    ProducedArtifactReceipt,
    ScopeSelector,
    TimelineNodeRef,
)
from bookforge.llm.client import LLMClient
from bookforge.llm.errors import LLMRequestError
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.types import Message
from bookforge.phases.outline import validators as outline_validators
from bookforge.query.authors import get_author_profile
from bookforge.supervision import capture_main_branch_snapshot, emit_reconciled_main_branch_contracts
from bookforge.util.json_extract import extract_json
from bookforge.util.schema import validate_json


ACTION = "draft_starter_outline_from_intent"
DEFAULT_MAX_TOKENS = 65536


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_token() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _bounded_positive_int(value: Any, *, default: int, maximum: int) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return default
    if resolved < 1:
        return default
    return min(resolved, maximum)


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _rel(book_root: Path, path: Path) -> str:
    try:
        return path.relative_to(book_root).as_posix()
    except ValueError:
        return path.as_posix()


def _receipt(book_root: Path, key: str, label: str, status: str, path: Path) -> ProducedArtifactReceipt:
    return ProducedArtifactReceipt(
        artifact_key=key,
        label=label,
        artifact_status=status,
        path=_rel(book_root, path),
        format="json",
        consumable=True,
        replaceable=False,
    )


def _load_book_and_intent(book_root: Path) -> tuple[Dict[str, Any], Dict[str, Any]]:
    book_path = book_root / "book.json"
    intent_path = book_root / "book_intent.json"
    if not book_path.exists():
        raise FileNotFoundError(f"Book manifest not found: {book_path}")
    if not intent_path.exists():
        raise FileNotFoundError(
            "draft_starter_outline_from_intent requires a book created from a BookIntent."
        )
    book = _read_json(book_path)
    intent = _read_json(intent_path)
    return book, intent


def _outline_counts(book: Dict[str, Any], intent: Dict[str, Any], details: Dict[str, Any]) -> tuple[int, int, int]:
    book_targets = book.get("targets") if isinstance(book.get("targets"), dict) else {}
    intent_targets = intent.get("targets") if isinstance(intent.get("targets"), dict) else {}
    targets = {**book_targets, **intent_targets}
    chapters = _bounded_positive_int(
        _first_present(details.get("chapters"), targets.get("chapters"), targets.get("chapter_count")),
        default=1,
        maximum=80,
    )
    sections = _bounded_positive_int(
        _first_present(
            details.get("sections_per_chapter"),
            targets.get("sections_per_chapter"),
            targets.get("section_count_per_chapter"),
            targets.get("sections"),
        ),
        default=1,
        maximum=12,
    )
    scenes = _bounded_positive_int(
        _first_present(
            details.get("scenes_per_section"),
            targets.get("scenes_per_section"),
            targets.get("target_scene_count"),
            targets.get("scenes"),
        ),
        default=1,
        maximum=12,
    )
    return chapters, sections, scenes


def _compact_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, indent=2)


def _author_fragment(workspace: Path, book: Dict[str, Any], intent: Dict[str, Any]) -> str:
    author_ref = str(
        intent.get("author_ref")
        or book.get("author_ref")
        or book.get("author")
        or ""
    ).strip()
    if not author_ref:
        return ""
    try:
        profile = get_author_profile(workspace, author_ref)
    except Exception:
        return ""
    return str(profile.system_fragment or "").strip()


def _starter_outline_messages(
    *,
    book_id: str,
    book: Dict[str, Any],
    intent: Dict[str, Any],
    author_fragment: str,
    chapter_count: int,
    sections_per_chapter: int,
    scenes_per_section: int,
) -> list[Message]:
    title = str(book.get("title") or intent.get("title") or book_id).strip()
    targets = {
        "chapters": chapter_count,
        "sections_per_chapter": sections_per_chapter,
        "scenes_per_section": scenes_per_section,
    }
    system_parts = [
        "You are BookForge's outline author.",
        "Create a real authored starter outline from the approved BookIntent.",
        "The output will become immutable outline run artifacts for workflow initialization.",
        "Do not produce a deterministic scaffold, placeholder outline, commentary, Markdown, or prose draft.",
        "Return JSON only.",
    ]
    if author_fragment:
        system_parts.extend(["Author voice and style fragment:", author_fragment])
    user_payload = {
        "book_id": book_id,
        "title": title,
        "book": book,
        "book_intent": intent,
        "target_shape": targets,
        "required_output_contract": {
            "schema_version": "1.1",
            "book_id": book_id,
            "characters": [
                {
                    "character_id": "stable_slug",
                    "name": "Display Name",
                    "intro": {"chapter": 1, "scene": 1},
                    "role": "role in story",
                }
            ],
            "threads": [
                {
                    "thread_id": "stable_slug",
                    "label": "Thread label",
                    "status": "active",
                    "summary": "Thread summary",
                }
            ],
            "chapters": [
                {
                    "chapter_id": 1,
                    "title": "Chapter title",
                    "goal": "Narrative purpose of the chapter",
                    "chapter_role": "opening|escalation|reversal|payoff|resolution",
                    "stakes_shift": "How pressure changes in this chapter",
                    "bridge": {"from_prev": "", "to_next": "handoff to next chapter"},
                    "pacing": {
                        "intensity": 3,
                        "tempo": "measured|rising|urgent|aftermath",
                        "expected_scene_count": scenes_per_section * sections_per_chapter,
                    },
                    "sections": [
                        {
                            "section_id": 1,
                            "title": "Section title",
                            "intent": "What this section accomplishes",
                            "section_role": "setup|development|turn|payoff",
                            "target_scene_count": scenes_per_section,
                            "end_condition": "Concrete state that must be true when the section ends",
                            "scenes": [
                                {
                                    "scene_id": 1,
                                    "summary": "Specific authored beat, not a placeholder.",
                                    "type": "setup|action|reveal|escalation|choice|consequence|aftermath|transition",
                                    "goal": "Immediate scene goal",
                                    "conflict": "Immediate pressure or opposition",
                                    "outcome": "Concrete changed state",
                                    "end_condition": "Concrete handoff state for the next scene",
                                    "characters": ["stable_slug"],
                                    "threads": ["stable_slug"],
                                    "handoff_mode": "direct_continuation",
                                    "transition_in_text": "Natural entry into the scene",
                                    "transition_in_anchors": ["entry condition", "active pressure", "character aim"],
                                    "transition_out_text": "Natural handoff description",
                                    "transition_out_anchors": ["changed state", "unresolved pressure", "next aim"],
                                    "location_start_label": "Specific location",
                                    "location_end_label": "Specific location",
                                    "constraint_state": "free",
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        "rules": [
            "Honor the requested target shape unless the BookIntent explicitly requires a minor adjustment.",
            "Scene ids restart at 1 within each chapter and increase sequentially across all sections in that chapter.",
            "Section ids restart at 1 within each chapter.",
            "Chapter ids start at 1 and increase sequentially.",
            "Use stable character_id and thread_id slugs.",
            "Every scene must be a specific story beat with enough information for later prose generation.",
            "Avoid meta language such as starter, scaffold, placeholder, to be written, or author loop.",
            "The final scene in each chapter should use handoff_mode terminal unless it directly hands off inside the same chapter.",
        ],
    }
    return [
        {"role": "system", "content": "\n\n".join(system_parts)},
        {
            "role": "user",
            "content": (
                "Draft the starter/thin outline JSON for workflow initialization.\n"
                "Return one JSON object matching required_output_contract.\n\n"
                + _compact_json(user_payload)
            ),
        },
    ]


def _starter_outline_max_tokens() -> int:
    return max(4096, read_int_env("BOOKFORGE_STARTER_OUTLINE_MAX_TOKENS", DEFAULT_MAX_TOKENS))


def _response_truncated(response: Any) -> bool:
    raw = getattr(response, "raw", None)
    if not isinstance(raw, dict):
        return False
    candidates = raw.get("candidates", [])
    if candidates and str(candidates[0].get("finishReason") or "").upper() == "MAX_TOKENS":
        return True
    finish_reason = raw.get("finish_reason") or raw.get("finishReason")
    return str(finish_reason or "").upper() == "MAX_TOKENS"


def _extract_outline_payload(text: str) -> Dict[str, Any]:
    payload = extract_json(text, label="Starter outline response")
    if not isinstance(payload, dict):
        raise ValueError("Starter outline response must be a JSON object.")
    if isinstance(payload.get("outline"), dict):
        payload = payload["outline"]
    if str(payload.get("schema_version") or "").strip() == "error_v1":
        reason = str(payload.get("reason_code") or "error_v1")
        raise ValueError(f"Starter outline model returned error_v1: {reason}")
    return payload


def _normalize_and_validate_starter_outline(payload: Dict[str, Any], *, book_id: str) -> Dict[str, Any]:
    outline = dict(payload)
    outline.setdefault("schema_version", "1.1")
    outline["book_id"] = book_id
    outline["source"] = "book_intent_llm"
    outline = outline_validators.normalize_outline_for_write(outline)
    validate_json(outline, "outline")
    validation = outline_validators.validate_outline(
        outline,
        strict_transition_bridges=False,
        require_links=False,
    )
    if validation.status != "pass":
        messages = [
            str(item.get("message") or item.get("code") or "validation_error")
            for item in validation.errors[:6]
            if isinstance(item, dict)
        ]
        raise ValueError("Starter outline failed validation: " + "; ".join(messages))
    return outline


def _thin_section_view(section: Dict[str, Any]) -> Dict[str, Any]:
    item = {
        key: value
        for key, value in section.items()
        if key not in {"scenes"}
    }
    if "target_scene_count" not in item:
        scenes = section.get("scenes") if isinstance(section.get("scenes"), list) else []
        item["target_scene_count"] = len(scenes)
    if "end_condition" not in item and section.get("intent"):
        item["end_condition"] = str(section.get("intent"))
    return item


def _slice_outline_handoffs(*, book_id: str, final: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    spine_chapters: list[Dict[str, Any]] = []
    section_chapters: list[Dict[str, Any]] = []
    chapters = final.get("chapters") if isinstance(final.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        spine_chapters.append(
            {
                key: value
                for key, value in chapter.items()
                if key not in {"sections"}
            }
        )
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        section_chapters.append(
            {
                "chapter_id": chapter.get("chapter_id"),
                "title": chapter.get("title"),
                "sections": [
                    _thin_section_view(section)
                    for section in sections
                    if isinstance(section, dict)
                ],
            }
        )
    spine = {
        "schema_version": "outline_spine_v1",
        "book_id": book_id,
        "source": "book_intent_llm",
        "chapters": spine_chapters,
    }
    sections_payload = {
        "schema_version": "outline_sections_v1",
        "book_id": book_id,
        "source": "book_intent_llm",
        "chapters": section_chapters,
    }
    return spine, sections_payload


def _draft_outline_with_provider(
    *,
    workspace: Path,
    book_id: str,
    book: Dict[str, Any],
    intent: Dict[str, Any],
    chapter_count: int,
    sections_per_chapter: int,
    scenes_per_section: int,
    client: Optional[LLMClient],
    model: Optional[str],
) -> tuple[Dict[str, Any], Any, list[Message], str]:
    if client is None:
        config = load_config()
        client = get_llm_client(config, phase="outline")
        if model is None:
            model = resolve_model("outline", config)
    elif model is None:
        model = "default"
    author_fragment = _author_fragment(workspace, book, intent)
    messages = _starter_outline_messages(
        book_id=book_id,
        book=book,
        intent=intent,
        author_fragment=author_fragment,
        chapter_count=chapter_count,
        sections_per_chapter=sections_per_chapter,
        scenes_per_section=scenes_per_section,
    )
    response = client.chat(
        messages,
        model=model,
        temperature=0.4,
        max_tokens=_starter_outline_max_tokens(),
    )
    if should_log_llm():
        log_llm_response(
            workspace,
            "outline_starter_outline",
            response,
            request={
                "book_id": book_id,
                "chapter_count": chapter_count,
                "sections_per_chapter": sections_per_chapter,
                "scenes_per_section": scenes_per_section,
            },
            extra={"book_id": book_id, "phase_id": ACTION, "turn_id": "t1"},
            messages=messages,
        )
    if _response_truncated(response):
        raise ValueError("Starter outline response was truncated by provider max tokens.")
    payload = _extract_outline_payload(str(response.text or ""))
    final = _normalize_and_validate_starter_outline(payload, book_id=book_id)
    return final, response, messages, str(model)


def build_draft_starter_outline_request(
    workspace: Path,
    book_id: str,
    *,
    run_id: Optional[str] = None,
    chapters: Optional[int] = None,
    sections_per_chapter: Optional[int] = None,
    scenes_per_section: Optional[int] = None,
    overwrite: bool = False,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    del workspace
    seed = "|".join([book_id, ACTION, str(run_id or ""), _utc_now()])
    return ExecutionRequest(
        request_id=request_id or hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16],
        action=ACTION,
        selector=ScopeSelector(book_id=book_id, branch_id=MAIN_BRANCH_ID, workflow_family="thin_outline"),
        branch_id=MAIN_BRANCH_ID,
        requested_at=_utc_now(),
        details={
            "run_id": _clean_optional(run_id),
            "chapters": chapters,
            "sections_per_chapter": sections_per_chapter,
            "scenes_per_section": scenes_per_section,
            "overwrite": bool(overwrite),
        },
    )


def _result_from_bundle_or_direct(
    *,
    bundle,
    request: ExecutionRequest,
    node: TimelineNodeRef,
    selector: ScopeSelector,
    status: str,
    message: str,
    artifact_paths: Dict[str, str],
    produced_artifacts: list[ProducedArtifactReceipt],
    details: Dict[str, Any],
) -> ExecutionResult:
    if bundle.execution_result is not None:
        return bundle.execution_result
    return ExecutionResult(
        result_id=hashlib.sha1(
            "|".join([selector.book_id, request.request_id, ACTION, status, _utc_now()]).encode("utf-8")
        ).hexdigest()[:16],
        action=ACTION,
        status=status,
        node=node,
        selector=selector,
        message=message,
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details=details,
        emitted_at=_utc_now(),
        request_id=request.request_id,
    )


def draft_starter_outline_from_intent(
    workspace: Path | str,
    request: ExecutionRequest,
    *,
    client: Optional[LLMClient] = None,
    model: Optional[str] = None,
) -> ExecutionResult:
    if request.action != ACTION:
        raise ValueError("Unsupported execution action.")
    if (request.branch_id or request.selector.branch_id or MAIN_BRANCH_ID) != MAIN_BRANCH_ID:
        raise ValueError(f"{ACTION} only supports main-branch execution.")

    workspace_path = Path(workspace)
    book_id = request.selector.book_id
    book_root = workspace_path / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_root}")
    outline_root = book_root / "outline"
    latest_path = outline_root / "pipeline_latest.json"
    workflow_initialized = (outline_root / "outline.json").exists() and (outline_root / "snapshot_registry.json").exists()
    overwrite = bool(request.details.get("overwrite"))
    existing_latest = _read_json(latest_path) if latest_path.exists() else {}
    existing_run_id = str(existing_latest.get("run_id") or "").strip()
    if existing_run_id and not overwrite:
        node = TimelineNodeRef(
            book_id=book_id,
            workflow_family=str(existing_latest.get("workflow_family") or "thin_outline"),
            source_run_id=existing_run_id,
            branch_id=MAIN_BRANCH_ID,
            phase_id=ACTION,
            revision_id=existing_run_id,
        )
        produced = [
            _receipt(
                book_root,
                "outline_pipeline_latest",
                "Existing outline pipeline latest pointer",
                "diagnostic",
                latest_path,
            )
        ]
        details = {
            "run_id": existing_run_id,
            "created": False,
            "existing_outline_run": True,
            "next_recommended_actions": ["initialize_section_workflow"],
        }
        return ExecutionResult(
            result_id=f"{request.request_id}_no_op",
            action=ACTION,
            status="no_op",
            node=node,
            selector=request.selector,
            message=f"Outline run already exists for {book_id}: {existing_run_id}.",
            artifact_paths={"outline_pipeline_latest": _rel(book_root, latest_path)},
            produced_artifacts=produced,
            details=details,
            emitted_at=_utc_now(),
            request_id=request.request_id,
        )
    if workflow_initialized and overwrite:
        raise ValueError(
            "Refusing to overwrite outline run artifacts after workflow initialization; use recovery branching instead."
        )

    before_snapshot = capture_main_branch_snapshot(workspace_path, book_id)
    book, intent = _load_book_and_intent(book_root)
    if str(intent.get("status") or "").strip() != "created":
        raise ValueError("draft_starter_outline_from_intent requires a created BookIntent copied into the book.")

    chapter_count, sections_per_chapter, scenes_per_section = _outline_counts(book, intent, dict(request.details or {}))
    run_id = _clean_optional(request.details.get("run_id")) or f"starter_{_run_token()}"
    run_dir = outline_root / "pipeline_runs" / run_id
    if run_dir.exists() and not overwrite:
        raise FileExistsError(f"Outline run already exists: {run_dir}")

    try:
        final, response, _messages, resolved_model = _draft_outline_with_provider(
            workspace=workspace_path,
            book_id=book_id,
            book=book,
            intent=intent,
            chapter_count=chapter_count,
            sections_per_chapter=sections_per_chapter,
            scenes_per_section=scenes_per_section,
            client=client,
            model=model,
        )
    except LLMRequestError as exc:
        if should_log_llm():
            log_llm_error(
                workspace_path,
                "outline_starter_outline",
                exc,
                request={
                    "book_id": book_id,
                    "chapter_count": chapter_count,
                    "sections_per_chapter": sections_per_chapter,
                    "scenes_per_section": scenes_per_section,
                },
                extra={"book_id": book_id, "phase_id": ACTION, "turn_id": "t1"},
            )
        node = TimelineNodeRef(
            book_id=book_id,
            workflow_family="thin_outline",
            source_run_id=run_id,
            branch_id=MAIN_BRANCH_ID,
            phase_id=ACTION,
            revision_id=run_id,
        )
        return ExecutionResult(
            result_id=f"{request.request_id}_retryable_pause",
            action=ACTION,
            status="retryable_pause",
            node=node,
            selector=request.selector,
            message=f"Starter outline provider request failed: {exc.message}",
            details={
                "run_id": run_id,
                "failure_code": "provider_retry_exhausted",
                "status_code": exc.status_code,
                "retry_after_seconds": exc.retry_after_seconds,
                "provider_used": True,
                "llm_calls": 1,
            },
            emitted_at=_utc_now(),
            request_id=request.request_id,
        )

    spine, sections = _slice_outline_handoffs(book_id=book_id, final=final)
    authored_chapters = final.get("chapters") if isinstance(final.get("chapters"), list) else []
    authored_section_count = sum(
        len(chapter.get("sections", []))
        for chapter in authored_chapters
        if isinstance(chapter, dict) and isinstance(chapter.get("sections"), list)
    )
    authored_scene_count = sum(
        len(section.get("scenes", []))
        for chapter in authored_chapters
        if isinstance(chapter, dict)
        for section in (chapter.get("sections") if isinstance(chapter.get("sections"), list) else [])
        if isinstance(section, dict) and isinstance(section.get("scenes"), list)
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    spine_path = _write_json(run_dir / "outline_spine_v1.json", spine)
    sections_path = _write_json(run_dir / "outline_sections_v1.json", sections)
    final_path = _write_json(run_dir / "outline_final_v1_1.json", final)
    report = {
        "schema_version": "outline_pipeline_report_v1",
        "book_id": book_id,
        "run_id": run_id,
        "workflow_family": "thin_outline",
        "source": "book_intent_llm",
        "source_artifact_class": "immutable_lineage_anchor",
        "result": "SUCCESS",
        "status": "SUCCESS",
        "starter_outline": True,
        "thin_outline": True,
        "deep_outline_pipeline": False,
        "provider_used": True,
        "llm_calls": 1,
        "provider": getattr(response, "provider", ""),
        "model": resolved_model,
        "prompt_tokens": getattr(response, "prompt_tokens", None),
        "completion_tokens": getattr(response, "completion_tokens", None),
        "total_tokens": getattr(response, "total_tokens", None),
        "chapter_count": len(authored_chapters),
        "section_count": authored_section_count,
        "scene_count": authored_scene_count,
        "created_at": _utc_now(),
        "artifacts": {
            "outline_spine": _rel(book_root, spine_path),
            "outline_sections": _rel(book_root, sections_path),
            "outline_final": _rel(book_root, final_path),
        },
    }
    report_path = _write_json(run_dir / "outline_pipeline_report.json", report)
    latest_payload = {
        "run_id": run_id,
        "updated_at": _utc_now(),
        "path": f"pipeline_runs/{run_id}",
        "workflow_family": "thin_outline",
        "starter_outline": True,
        "thin_outline": True,
        "deep_outline_pipeline": False,
        "source": "book_intent_llm",
        "provider_used": True,
    }
    latest_path = _write_json(outline_root / "pipeline_latest.json", latest_payload)
    alias_path = _write_json(outline_root / "outline_pipeline_latest.json", latest_payload)
    latest_report_path = _write_json(
        outline_root / "outline_pipeline_report_latest.json",
        {
            "run_id": run_id,
            "updated_at": _utc_now(),
            "path": f"pipeline_runs/{run_id}/outline_pipeline_report.json",
            "workflow_family": "thin_outline",
            "starter_outline": True,
            "thin_outline": True,
            "deep_outline_pipeline": False,
            "provider_used": True,
        },
    )

    artifact_paths = {
        "outline_run_dir": _rel(book_root, run_dir),
        "outline_spine": _rel(book_root, spine_path),
        "outline_sections": _rel(book_root, sections_path),
        "outline_final": _rel(book_root, final_path),
        "outline_pipeline_report": _rel(book_root, report_path),
        "outline_pipeline_latest": _rel(book_root, latest_path),
        "outline_pipeline_latest_alias": _rel(book_root, alias_path),
        "outline_pipeline_report_latest": _rel(book_root, latest_report_path),
    }
    produced = [
        _receipt(book_root, "outline_spine", "Starter outline spine", "authoritative", spine_path),
        _receipt(book_root, "outline_sections", "Starter outline sections", "authoritative", sections_path),
        _receipt(book_root, "outline_final", "Starter outline final handoff", "authoritative", final_path),
        _receipt(book_root, "outline_pipeline_report", "Starter outline report", "diagnostic", report_path),
        _receipt(book_root, "outline_pipeline_latest", "Outline latest pointer", "diagnostic", latest_path),
    ]
    details = {
        "run_id": run_id,
        "created": True,
        "starter_outline": True,
        "workflow_family": "thin_outline",
        "thin_outline": True,
        "deep_outline_pipeline": False,
        "provider_used": True,
        "llm_calls": 1,
        "provider": getattr(response, "provider", ""),
        "model": resolved_model,
        "prompt_tokens": getattr(response, "prompt_tokens", None),
        "completion_tokens": getattr(response, "completion_tokens", None),
        "total_tokens": getattr(response, "total_tokens", None),
        "chapter_count": len(authored_chapters),
        "section_count": authored_section_count,
        "scene_count": authored_scene_count,
        "book_intent_id": intent.get("intent_id"),
        "next_recommended_action": "initialize_section_workflow",
        "next_recommended_actions": [
            "initialize_section_workflow",
        ],
        "follow_on_sequence": [
            "initialize_section_workflow",
            "freeze_section_from_phase03_artifact",
            "create_branch",
            "continue_scene",
        ],
        "follow_on_sequence_policy": (
            "Informational only; re-query legal actions and readiness after each receipt before running the next step."
        ),
        "truth_note": (
            "This uses the outline provider to author a thin starter outline from a created BookIntent, "
            "then slices that authored outline into immutable run artifacts. It is not the full "
            "multi-phase deep outline pipeline and does not initialize workflow state, freeze a section, "
            "create a branch, or write prose."
        ),
    }
    bundle = emit_reconciled_main_branch_contracts(
        workspace=workspace_path,
        book_id=book_id,
        before_snapshot=before_snapshot,
        action=ACTION,
        result_status="success",
        message="Starter outline run artifacts created from BookIntent.",
        artifact_paths=artifact_paths,
        produced_artifacts=produced,
        details=details,
        request_id=request.request_id,
    )
    node = TimelineNodeRef(
        book_id=book_id,
        workflow_family="thin_outline",
        source_run_id=run_id,
        branch_id=MAIN_BRANCH_ID,
        phase_id=ACTION,
        revision_id=run_id,
    )
    return _result_from_bundle_or_direct(
        bundle=bundle,
        request=request,
        node=node,
        selector=request.selector,
        status="success",
        message="Starter outline run artifacts created from BookIntent.",
        artifact_paths=artifact_paths,
        produced_artifacts=produced,
        details=details,
    )
