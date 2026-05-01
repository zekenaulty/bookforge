from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import json
import re
import uuid

from bookforge.contracts import BookIntent, ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ProducedArtifactReceipt, ScopeSelector, TimelineNodeRef
from bookforge.query.book_intent import BOOK_INTENT_FILENAME, book_intents_root, get_book_intent
from bookforge.workspace import init_book_workspace, update_book_templates


BOOK_INTENT_LIBRARY_SCOPE_ID = "__book_intents__"
BOOK_INTENT_SOURCE_RUN_ID = "book_intents"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _clean_required(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _clean_list(values: Optional[Iterable[Any] | str]) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [item.strip() for item in values.split(",") if item.strip()]
    return [str(item).strip() for item in values if str(item).strip()]


def _read_optional_file(path_value: Any) -> Optional[str]:
    cleaned = _clean_optional(path_value)
    if not cleaned:
        return None
    return Path(cleaned).read_text(encoding="utf-8")


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned or f"book_{uuid.uuid4().hex[:8]}"


def _intent_id_from_title(title: str) -> str:
    return f"{_slugify(title)}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"


def _selector(book_id: Optional[str] = None) -> ScopeSelector:
    return ScopeSelector(book_id=book_id or BOOK_INTENT_LIBRARY_SCOPE_ID, branch_id=MAIN_BRANCH_ID, workflow_family="book_intent")


def _node(*, book_id: str, phase_id: str, revision_id: str) -> TimelineNodeRef:
    return TimelineNodeRef(
        book_id=book_id,
        workflow_family="book_intent",
        source_run_id=BOOK_INTENT_SOURCE_RUN_ID,
        branch_id=MAIN_BRANCH_ID,
        phase_id=phase_id,
        revision_id=revision_id,
    )


def _intent_dir(workspace: Path, intent_id: str) -> Path:
    return book_intents_root(workspace) / intent_id


def _intent_path(workspace: Path, intent_id: str) -> Path:
    return _intent_dir(workspace, intent_id) / BOOK_INTENT_FILENAME


def _write_intent(workspace: Path, intent: BookIntent) -> Path:
    path = _intent_path(workspace, intent.intent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(intent.to_dict(), ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _artifact_path(path: Path) -> str:
    return path.as_posix()


def _intent_receipt(path: Path, *, status: str, replaceable: bool = True) -> ProducedArtifactReceipt:
    return ProducedArtifactReceipt(
        artifact_key="book_intent",
        label="Book intent",
        artifact_status=status,
        path=_artifact_path(path),
        format="json",
        consumable=True,
        resumable=False,
        replaceable=replaceable,
    )


def _intent_markdown(intent: BookIntent) -> str:
    lines = [
        f"# {intent.title}",
        "",
        f"- Intent ID: {intent.intent_id}",
        f"- Status: {intent.status}",
        f"- Author: {intent.author_ref}",
        f"- Genre: {', '.join(intent.genre)}",
    ]
    if intent.reader_promise:
        lines.extend(["", "## Reader Promise", intent.reader_promise])
    if intent.short_synopsis:
        lines.extend(["", "## Short Synopsis", intent.short_synopsis])
    if intent.long_synopsis:
        lines.extend(["", "## Long Synopsis", intent.long_synopsis])
    if intent.central_conflict:
        lines.extend(["", "## Central Conflict", intent.central_conflict])
    if intent.tone:
        lines.extend(["", "## Tone", intent.tone])
    if intent.must_have:
        lines.extend(["", "## Must Have", *[f"- {item}" for item in intent.must_have]])
    if intent.must_not:
        lines.extend(["", "## Must Not", *[f"- {item}" for item in intent.must_not]])
    lines.extend(["", "## Seed", intent.seed_text])
    return "\n".join(lines).strip() + "\n"


def _copy_intent(intent: BookIntent, **overrides: Any) -> BookIntent:
    payload = intent.to_dict()
    payload.update(overrides)
    return BookIntent.from_dict(payload)


def _result(
    *,
    request: ExecutionRequest,
    selector: ScopeSelector,
    action: str,
    phase_id: str,
    message: str,
    intent: BookIntent,
    intent_path: Path,
    produced_artifacts: list[ProducedArtifactReceipt],
    artifact_paths: Dict[str, str],
    extra_details: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    details = {
        "intent_id": intent.intent_id,
        "intent_status": intent.status,
        "book_id": intent.book_id,
        "created_book_id": intent.created_book_id,
        "title": intent.title,
        "author_ref": intent.author_ref,
        "intent_path": _artifact_path(intent_path),
    }
    details.update(dict(extra_details or {}))
    return ExecutionResult(
        result_id=f"{request.request_id}_result",
        action=action,
        status="success",
        node=_node(book_id=selector.book_id, phase_id=phase_id, revision_id=intent.status),
        selector=selector,
        message=message,
        artifact_paths=artifact_paths,
        produced_artifacts=produced_artifacts,
        details=details,
        emitted_at=_utc_now(),
        request_id=request.request_id,
    )


def build_draft_book_intent_request(
    *,
    title: str,
    author_ref: str,
    genre: Iterable[str] | str,
    seed_text: Optional[str] = None,
    seed_file: Optional[Path | str] = None,
    book_id: Optional[str] = None,
    series_id: Optional[str] = None,
    targets: Optional[Dict[str, Any]] = None,
    short_synopsis: Optional[str] = None,
    long_synopsis: Optional[str] = None,
    reader_promise: Optional[str] = None,
    central_conflict: Optional[str] = None,
    tone: Optional[str] = None,
    must_have: Optional[Iterable[str] | str] = None,
    must_not: Optional[Iterable[str] | str] = None,
    source_ref: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    proposed_book_id = _clean_optional(book_id)
    return ExecutionRequest(
        request_id=request_id or _request_id("draft_book_intent"),
        action="draft_book_intent",
        selector=_selector(proposed_book_id),
        requested_at=_utc_now(),
        details={
            "title": _clean_required(title, "title"),
            "author_ref": _clean_required(author_ref, "author_ref"),
            "genre": _clean_list(genre),
            "seed_text": _clean_optional(seed_text),
            "seed_file": _clean_optional(seed_file),
            "book_id": proposed_book_id,
            "series_id": _clean_optional(series_id),
            "targets": dict(targets or {}),
            "short_synopsis": _clean_optional(short_synopsis),
            "long_synopsis": _clean_optional(long_synopsis),
            "reader_promise": _clean_optional(reader_promise),
            "central_conflict": _clean_optional(central_conflict),
            "tone": _clean_optional(tone),
            "must_have": _clean_list(must_have),
            "must_not": _clean_list(must_not),
            "source_ref": _clean_optional(source_ref),
        },
    )


def build_approve_book_intent_request(
    *,
    intent_ref: str | Path,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=request_id or _request_id("approve_book_intent"),
        action="approve_book_intent",
        selector=_selector(),
        requested_at=_utc_now(),
        details={"intent_ref": _clean_required(intent_ref, "intent_ref")},
    )


def build_create_book_from_intent_request(
    *,
    intent_ref: str | Path,
    book_id: Optional[str] = None,
    series_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=request_id or _request_id("create_book_from_intent"),
        action="create_book_from_intent",
        selector=_selector(_clean_optional(book_id)),
        requested_at=_utc_now(),
        details={
            "intent_ref": _clean_required(intent_ref, "intent_ref"),
            "book_id": _clean_optional(book_id),
            "series_id": _clean_optional(series_id),
        },
    )


def draft_book_intent_action(workspace: Path | str, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "draft_book_intent":
        raise ValueError("Unsupported execution action.")
    workspace_path = Path(workspace)
    details = dict(request.details or {})
    seed_parts = [
        _clean_optional(details.get("seed_text")),
        _read_optional_file(details.get("seed_file")),
    ]
    seed_text = "\n\n".join(part for part in seed_parts if part)
    if not seed_text.strip():
        raise ValueError("draft_book_intent requires seed_text or seed_file.")
    title = _clean_required(details.get("title"), "title")
    intent = BookIntent(
        intent_id=_intent_id_from_title(title),
        status="draft",
        book_id=_clean_optional(details.get("book_id")),
        title=title,
        author_ref=_clean_required(details.get("author_ref"), "author_ref"),
        genre=_clean_list(details.get("genre")),
        targets=dict(details.get("targets") or {}),
        series_id=_clean_optional(details.get("series_id")),
        seed_text=seed_text,
        short_synopsis=_clean_optional(details.get("short_synopsis")),
        long_synopsis=_clean_optional(details.get("long_synopsis")),
        reader_promise=_clean_optional(details.get("reader_promise")),
        central_conflict=_clean_optional(details.get("central_conflict")),
        tone=_clean_optional(details.get("tone")),
        must_have=_clean_list(details.get("must_have")),
        must_not=_clean_list(details.get("must_not")),
        source_ref=_clean_optional(details.get("source_ref")),
        created_at=_utc_now(),
    )
    path = _write_intent(workspace_path, intent)
    return _result(
        request=request,
        selector=request.selector,
        action="draft_book_intent",
        phase_id="draft_book_intent",
        message="Book intent draft created.",
        intent=intent,
        intent_path=path,
        produced_artifacts=[_intent_receipt(path, status="provisional")],
        artifact_paths={"book_intent": _artifact_path(path)},
    )


def approve_book_intent_action(workspace: Path | str, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "approve_book_intent":
        raise ValueError("Unsupported execution action.")
    workspace_path = Path(workspace)
    record = get_book_intent(workspace_path, _clean_required(request.details.get("intent_ref"), "intent_ref"))
    if record.intent.status == "created":
        raise ValueError("Book intent has already created a book workspace.")
    intent = _copy_intent(record.intent, status="approved", approved_at=_utc_now())
    path = _write_intent(workspace_path, intent)
    selector = _selector(intent.book_id)
    return _result(
        request=request,
        selector=selector,
        action="approve_book_intent",
        phase_id="approve_book_intent",
        message="Book intent approved.",
        intent=intent,
        intent_path=path,
        produced_artifacts=[_intent_receipt(path, status="authoritative")],
        artifact_paths={"book_intent": _artifact_path(path)},
    )


def create_book_from_intent_action(workspace: Path | str, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "create_book_from_intent":
        raise ValueError("Unsupported execution action.")
    workspace_path = Path(workspace)
    record = get_book_intent(workspace_path, _clean_required(request.details.get("intent_ref"), "intent_ref"))
    intent = record.intent
    if intent.status != "approved":
        raise ValueError("create_book_from_intent requires an approved book intent.")
    resolved_book_id = _clean_optional(request.details.get("book_id")) or intent.book_id or _slugify(intent.title)
    resolved_series_id = _clean_optional(request.details.get("series_id")) or intent.series_id
    book_root = init_book_workspace(
        workspace=workspace_path,
        book_id=resolved_book_id,
        author_ref=intent.author_ref,
        title=intent.title,
        genre=list(intent.genre),
        targets=dict(intent.targets),
        series_id=resolved_series_id,
    )
    created_intent = _copy_intent(intent, status="created", book_id=resolved_book_id, created_book_id=resolved_book_id)
    source_intent_path = _write_intent(workspace_path, created_intent)
    book_intent_path = book_root / BOOK_INTENT_FILENAME
    book_intent_path.write_text(json.dumps(created_intent.to_dict(), ensure_ascii=True, indent=2), encoding="utf-8")
    intent_md = _intent_markdown(created_intent)
    (book_root / "draft" / "context" / "book_intent.md").write_text(intent_md, encoding="utf-8")
    bible_path = book_root / "draft" / "context" / "bible.md"
    if not bible_path.read_text(encoding="utf-8").strip():
        bible_path.write_text(intent_md, encoding="utf-8")
    _attach_intent_to_book_metadata(book_root, created_intent)
    update_book_templates(workspace_path, resolved_book_id)
    selector = _selector(resolved_book_id)
    produced = [
        _intent_receipt(source_intent_path, status="authoritative", replaceable=False),
        ProducedArtifactReceipt(
            artifact_key="created_book_json",
            label="Created book manifest",
            artifact_status="authoritative",
            path=_artifact_path(book_root / "book.json"),
            format="json",
            consumable=True,
            replaceable=False,
        ),
        ProducedArtifactReceipt(
            artifact_key="created_book_intent",
            label="Created book intent copy",
            artifact_status="authoritative",
            path=_artifact_path(book_intent_path),
            format="json",
            consumable=True,
            replaceable=False,
        ),
        ProducedArtifactReceipt(
            artifact_key="book_intent_context",
            label="Book intent context markdown",
            artifact_status="authoritative",
            path=_artifact_path(book_root / "draft" / "context" / "book_intent.md"),
            format="markdown",
            consumable=True,
            replaceable=True,
        ),
    ]
    return _result(
        request=request,
        selector=selector,
        action="create_book_from_intent",
        phase_id="create_book_from_intent",
        message="Canonical BookForge book workspace created from approved intent.",
        intent=created_intent,
        intent_path=source_intent_path,
        produced_artifacts=produced,
        artifact_paths={
            "book_root": _artifact_path(book_root),
            "book_json": _artifact_path(book_root / "book.json"),
            "book_intent": _artifact_path(book_intent_path),
            "book_intent_context": _artifact_path(book_root / "draft" / "context" / "book_intent.md"),
        },
        extra_details={
            "book_root": _artifact_path(book_root),
            "canonical_transition": "author_only_seed_to_book_scope",
        },
    )


def _attach_intent_to_book_metadata(book_root: Path, intent: BookIntent) -> None:
    book_path = book_root / "book.json"
    payload = json.loads(book_path.read_text(encoding="utf-8"))
    payload["book_intent_id"] = intent.intent_id
    payload["book_intent_ref"] = f"book_intents/{intent.intent_id}/{BOOK_INTENT_FILENAME}"
    payload["book_intent"] = {
        "intent_id": intent.intent_id,
        "status": intent.status,
        "short_synopsis": intent.short_synopsis,
        "long_synopsis": intent.long_synopsis,
        "reader_promise": intent.reader_promise,
        "central_conflict": intent.central_conflict,
        "tone": intent.tone,
        "must_have": list(intent.must_have),
        "must_not": list(intent.must_not),
        "source_ref": intent.source_ref,
    }
    book_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
