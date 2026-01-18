from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast
import json
import os
import re

from bookforge.config.env import load_config
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
from bookforge.util.paths import repo_root
from bookforge.util.schema import validate_json


DEFAULT_WRITE_MAX_TOKENS = 4096
DEFAULT_LINT_MAX_TOKENS = 2048
DEFAULT_REPAIR_MAX_TOKENS = 4096
DEFAULT_CONTINUITY_MAX_TOKENS = 2048
DEFAULT_STYLE_ANCHOR_MAX_TOKENS = 1024


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


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




def _lint_mode() -> str:
    raw = os.environ.get("BOOKFORGE_LINT_MODE", "strict").strip().lower()
    if raw in {"strict", "warn", "off"}:
        return raw
    return "strict"


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


def _extract_prose_and_patch(text: str) -> Tuple[str, Dict[str, Any]]:
    match = re.search(r"STATE_PATCH\s*:\s*", text, re.IGNORECASE)
    if not match:
        raise ValueError("Missing STATE_PATCH block in response.")
    prose_block = text[:match.start()].strip()
    patch_block = text[match.end():].strip()
    prose = re.sub(r"^PROSE\s*:\s*", "", prose_block, flags=re.IGNORECASE).strip()
    if not prose:
        prose = prose_block.strip()
    patch = _extract_json(patch_block)
    if "schema_version" not in patch:
        patch["schema_version"] = "1.0"
    return prose, patch


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


def _chat(
    workspace: Path,
    label: str,
    client: LLMClient,
    messages: List[Message],
    model: str,
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    key_slot = getattr(client, "key_slot", None)
    extra = {"key_slot": key_slot} if key_slot else None
    try:
        response = client.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
    except LLMRequestError as exc:
        if should_log_llm():
            log_llm_error(workspace, f"{label}_error", exc, messages=messages, extra=extra)
        raise
    if should_log_llm():
        log_llm_response(workspace, label, response, messages=messages, extra=extra)
    return response


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
    )
    text = response.text.strip()
    if not text:
        raise ValueError("Style anchor generation returned empty output.")
    save_style_anchor(anchor_path, text)
    return text


def _generate_continuity_pack(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    state: Dict[str, Any],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "continuity_pack.md")
    recent_facts = state.get("world", {}).get("recent_facts", [])
    prompt = render_template_file(
        template,
        {
            "state": state,
            "recent_facts": recent_facts,
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
    )

    data = _extract_json(response.text)
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
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
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
    )

    try:
        prose, patch = _extract_prose_and_patch(response.text)
    except ValueError as exc:
        extra = ""
        if _response_truncated(response):
            extra = f" Model output hit MAX_TOKENS ({_write_max_tokens()}); increase BOOKFORGE_WRITE_MAX_TOKENS."
        raise ValueError(f"{exc}{extra}") from exc

    validate_json(patch, "state_patch")
    return prose, patch


def _lint_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    state: Dict[str, Any],
    invariants: List[str],
    client: LLMClient,
    model: str,
) -> Dict[str, Any]:
    template = _resolve_template(book_root, "lint.md")
    prompt = render_template_file(
        template,
        {
            "prose": prose,
            "state": state,
            "invariants": invariants,
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
    )

    report = _extract_json(response.text)
    report = _normalize_lint_report(report)
    validate_json(report, "lint_report")
    return report


def _repair_scene(
    workspace: Path,
    book_root: Path,
    system_path: Path,
    prose: str,
    lint_report: Dict[str, Any],
    state: Dict[str, Any],
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
        },
    )

    messages: List[Message] = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
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
    )

    try:
        prose, patch = _extract_prose_and_patch(response.text)
    except ValueError as exc:
        extra = ""
        if _response_truncated(response):
            extra = f" Model output hit MAX_TOKENS ({_repair_max_tokens()}); increase BOOKFORGE_REPAIR_MAX_TOKENS."
        raise ValueError(f"{exc}{extra}") from exc

    validate_json(patch, "state_patch")
    return prose, patch


def _apply_state_patch(state: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    world_updates = patch.get("world_updates")
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

    delta = patch.get("duplication_warnings_in_row_delta")
    if isinstance(delta, int):
        current = int(state.get("duplication_warnings_in_row", 0) or 0)
        state["duplication_warnings_in_row"] = max(0, current + delta)

    return state


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
    if not chapter_order:
        raise ValueError("Outline is missing chapters; cannot run writer loop.")

    target = _parse_until(until)
    if steps is None and target == (None, None):
        steps_remaining: Optional[int] = 1
    else:
        steps_remaining = steps

    config = load_config()
    planner_client = get_llm_client(config, phase="planner")
    writer_client = get_llm_client(config, phase="writer")
    linter_client = get_llm_client(config, phase="linter")
    planner_model = resolve_model("planner", config)
    writer_model = resolve_model("writer", config)
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

        continuity_pack = _generate_continuity_pack(
            workspace,
            book_root,
            system_path,
            state,
            planner_client,
            planner_model,
        )

        invariants = book.get("invariants", []) if isinstance(book.get("invariants", []), list) else []

        prose, patch = _write_scene(
            workspace,
            book_root,
            system_path,
            scene_card,
            continuity_pack,
            state,
            style_anchor,
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
                invariants,
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
                writer_client,
                writer_model,
            )
            write_attempts += 1
            lint_report = _lint_scene(
                workspace,
                book_root,
                system_path,
                prose,
                state,
                invariants,
                linter_client,
                linter_model,
            )
            if lint_report.get("status") == "fail" and lint_mode == "strict":
                raise ValueError("Lint failed after repair; see lint logs for details.")

        state = _apply_state_patch(state, patch)

        chapter_num = int(scene_card.get("chapter", chapter))
        scene_num = int(scene_card.get("scene", scene))

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
