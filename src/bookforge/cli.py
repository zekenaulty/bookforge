import argparse
from pathlib import Path
import sys

from bookforge.author import generate_author
from bookforge.execution import (
    apply_scene_commit,
    build_apply_scene_commit_request,
    build_generate_continuity_pack_request,
    build_lint_scene_prose_request,
    build_plan_scene_request,
    build_preflight_scene_state_request,
    build_repair_scene_prose_request,
    build_state_repair_scene_patch_request,
    build_finalize_chapter_request,
    build_freeze_section_request,
    build_initialize_workflow_request,
    build_lock_section_request,
    build_resume_paused_section_request,
    build_write_scene_prose_request,
    build_write_section_request,
    finalize_chapter,
    freeze_section,
    generate_continuity_pack,
    initialize_workflow,
    lint_scene_prose,
    lock_section,
    plan_scene_action,
    preflight_scene_state,
    repair_scene_prose,
    resume_paused_section,
    state_repair_scene_patch,
    write_scene_prose,
    write_frozen_section,
)
from bookforge.outline import (
    backup_outline_run,
    restore_outline_state,
    generate_outline,
    load_latest_outline_pipeline_report,
    format_outline_pipeline_summary,
)
from bookforge.runner import run_loop
from bookforge.characters import generate_characters
from bookforge.query import get_scene_phase_readiness, list_execution_options
from bookforge.contracts import ScopeSelector
from bookforge.workspace import init_book_workspace, parse_genre, parse_targets, reset_book_workspace_detailed, update_book_templates
from bookforge.llm.thoughts import format_thought_response, list_signatures, run_current_thoughts
from bookforge.llm.storage import signature_active_path
from bookforge.llm.signatures import select_signature, set_active_signature
from bookforge.section_workflow import get_section_workflow_status


def _init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        genre = parse_genre(args.genre)
        targets = parse_targets(args.target)
        book_dir = init_book_workspace(
            workspace=workspace,
            book_id=args.book,
            author_ref=args.author_ref,
            title=args.title,
            genre=genre,
            targets=targets,
            series_id=args.series_id,
        )
    except Exception as exc:
        sys.stderr.write(f"Init failed: {exc}\n")
        return 1
    sys.stdout.write(f"Workspace created at {book_dir}\n")
    return 0


def _author_generate(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    prompt_file = Path(args.prompt_file) if args.prompt_file else None
    try:
        version_dir = generate_author(
            workspace=workspace,
            influences=args.influences,
            prompt_file=prompt_file,
            name=args.name,
            notes=args.notes,
        )
    except Exception as exc:
        sys.stderr.write(f"Author generation failed: {exc}\n")
        return 1
    sys.stdout.write(f"Author created at {version_dir}\n")
    return 0


def _outline_generate(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    prompt_file = Path(args.prompt_file) if args.prompt_file else None
    transition_hints_file = (
        Path(args.transition_hints_file)
        if getattr(args, "transition_hints_file", None)
        else None
    )
    try:
        outline_path = generate_outline(
            workspace=workspace,
            book_id=args.book,
            new_version=args.new_version,
            prompt_file=prompt_file,
            rerun=bool(getattr(args, "rerun", False)),
            resume=bool(getattr(args, "resume", False)),
            from_phase=getattr(args, "from_phase", None),
            to_phase=getattr(args, "to_phase", None),
            phase=getattr(args, "phase", None),
            transition_hints_file=transition_hints_file,
            strict_transition_hints=bool(getattr(args, "strict_transition_hints", False)),
            strict_transition_bridges=bool(getattr(args, "strict_transition_bridges", True)),
            strict_location_identity=bool(getattr(args, "strict_location_identity", True)),
            transition_insert_budget_per_chapter=int(
                getattr(args, "transition_insert_budget_per_chapter", 2) or 2
            ),
            allow_transition_scene_insertions=bool(
                getattr(args, "allow_transition_scene_insertions", True)
            ),
            force_rerun_with_draft=bool(getattr(args, "force_rerun_with_draft", False)),
            exact_scene_count=bool(getattr(args, "exact_scene_count", False)),
            scene_count_range=getattr(args, "scene_count_range", None),
            force_phase_full_rerun=bool(getattr(args, "force_phase_full_rerun", False)),
        )
    except Exception as exc:
        sys.stderr.write(f"Outline generation failed: {exc}\n")
        return 1
    sys.stdout.write(f"Outline created at {outline_path}\n")
    report_path, report = load_latest_outline_pipeline_report(workspace=workspace, book_id=args.book)
    if report:
        sys.stdout.write(format_outline_pipeline_summary(report, report_path=report_path))
    return 0


def _outline_backup(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    output_dir = Path(args.output_dir) if getattr(args, "output_dir", None) else None
    if output_dir is not None and not output_dir.is_absolute():
        output_dir = workspace / output_dir
    try:
        backup_dir = backup_outline_run(
            workspace=workspace,
            book_id=args.book,
            run_id=getattr(args, "run_id", None),
            output_dir=output_dir,
            require_success=not bool(getattr(args, "allow_non_success", False)),
            copy_run_artifacts=not bool(getattr(args, "skip_run_artifacts", False)),
        )
    except Exception as exc:
        sys.stderr.write(f"Outline backup failed: {exc}\n")
        return 1
    sys.stdout.write(f"Outline backup created at {backup_dir}\n")
    return 0


def _outline_restore(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    backup_path = Path(args.backup_path) if getattr(args, "backup_path", None) else None
    try:
        outline_path = restore_outline_state(
            workspace=workspace,
            book_id=args.book,
            run_id=getattr(args, "run_id", None),
            backup_path=backup_path,
            overwrite_current=bool(getattr(args, "overwrite_current", False)),
            set_latest_run_pointer=bool(getattr(args, "set_latest_run_pointer", False)),
        )
    except Exception as exc:
        sys.stderr.write(f"Outline restore failed: {exc}\n")
        return 1
    sys.stdout.write(f"Outline restored at {outline_path}\n")
    return 0




def _run(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        run_loop(
            workspace=workspace,
            book_id=args.book,
            steps=args.steps,
            until=args.until,
            resume=args.resume,
            ack_outline_attention_items=bool(
                getattr(args, "ack_outline_attention_items", False)
            ),
            force_outline_gate_bypass=bool(
                getattr(args, "force_outline_gate_bypass", False)
            ),
        )
    except Exception as exc:
        sys.stderr.write(f"Run failed: {exc}\n")
        return 1
    sys.stdout.write("Run completed.\n")
    return 0


def _workflow_init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_initialize_workflow_request(
            workspace=workspace,
            book_id=args.book,
            run_id=getattr(args, "run_id", None),
            overwrite=bool(getattr(args, "overwrite", False)),
        )
        result = initialize_workflow(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Workflow init failed: {exc}\n")
        return 1
    paths = result.artifact_paths if isinstance(result.artifact_paths, dict) else {}
    sys.stdout.write(
        "Section workflow initialized.\n"
        f"Book: {args.book}\n"
        f"Run: {result.details.get('run_id')}\n"
        f"Status: {result.status}\n"
        f"Outline: {paths.get('outline')}\n"
        f"Registry: {paths.get('registry')}\n"
    )
    for key in ("thin", "toc", "index", "appendix"):
        if paths.get(key):
            sys.stdout.write(f"{key}: {paths.get(key)}\n")
    return 0


def _workflow_status(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        status = get_section_workflow_status(workspace=workspace, book_id=args.book)
    except Exception as exc:
        sys.stderr.write(f"Workflow status failed: {exc}\n")
        return 1
    cursor = status.get("cursor") if isinstance(status.get("cursor"), dict) else {}
    sys.stdout.write(
        f"Book: {status.get('book_id')}\n"
        f"State status: {status.get('state_status')}\n"
        f"Source run: {status.get('source_run_id')}\n"
        f"Cursor: ch{int(cursor.get('chapter', 0) or 0):03d} sc{int(cursor.get('scene', 0) or 0):03d}\n"
    )
    active = status.get("active_section")
    if isinstance(active, dict):
        sys.stdout.write(
            f"Active section: ch{int(active.get('chapter_id', 0) or 0):03d} "
            f"sec{int(active.get('section_id', 0) or 0):03d} "
            f"status={active.get('status')}\n"
        )
    chapters = status.get("chapters") if isinstance(status.get("chapters"), list) else []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = int(chapter.get("chapter_id", 0) or 0)
        chapter_status = str(chapter.get("chapter_status") or "").strip()
        chapter_suffix = f" [{chapter_status}]" if chapter_status else ""
        sys.stdout.write(f"Chapter {chapter_id}{chapter_suffix}: {chapter.get('title')}\n")
        if chapter.get("chapter_seam_report"):
            sys.stdout.write(
                f"  seam_report={chapter.get('chapter_seam_report')} "
                f"original={chapter.get('chapter_original_markdown')} "
                f"fixed={chapter.get('chapter_fixed_markdown')} "
                f"final={chapter.get('chapter_final_markdown') or chapter.get('chapter_candidate_markdown')}\n"
            )
        sections = chapter.get("sections") if isinstance(chapter.get("sections"), list) else []
        for section in sections:
            if not isinstance(section, dict):
                continue
            sys.stdout.write(
                "  "
                f"sec {int(section.get('section_id', 0) or 0)} "
                f"[{section.get('status')}] "
                f"{section.get('title')} "
                f"refs={section.get('scene_ref_start')}->{section.get('scene_ref_end')}\n"
            )
    return 0


def _workflow_legal_actions(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        options = list_execution_options(
            workspace,
            ScopeSelector(
                book_id=args.book,
                branch_id=getattr(args, "branch_id", None) or "main",
                fork_group_id=getattr(args, "fork_group_id", None),
                chapter=getattr(args, "chapter", None),
                section=getattr(args, "section", None),
                scene=getattr(args, "scene", None),
            ),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow legal-actions failed: {exc}\n")
        return 1
    for option in options:
        status = "allowed" if option.allowed else "blocked"
        sys.stdout.write(f"{option.action}: {status}\n")
        sys.stdout.write(f"  summary={option.summary}\n")
        sys.stdout.write(f"  branch_policy={option.branch_policy} workflow_family={option.workflow_family}\n")
        if option.selector_requirements:
            sys.stdout.write(f"  selector_requirements={','.join(option.selector_requirements)}\n")
        if option.details:
            sys.stdout.write(f"  details={option.details}\n")
        if option.refusal_reason:
            sys.stdout.write(f"  refusal_reason={option.refusal_reason}\n")
    return 0


def _workflow_scene_readiness(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        readiness = get_scene_phase_readiness(
            workspace,
            args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow scene-readiness failed: {exc}\n")
        return 1
    selector = readiness.selector
    section_label = f"{int(selector.section):03d}" if selector.section is not None else "n/a"
    sys.stdout.write(
        f"Book: {readiness.book_id}\n"
        f"Scope: ch{int(selector.chapter or 0):03d} sc{int(selector.scene or 0):03d} "
        f"sec={section_label}\n"
        f"Scene status: {readiness.scene_status}\n"
        f"Recommended next action: {readiness.recommended_next_action or ''}\n"
    )
    if readiness.node is not None:
        sys.stdout.write(
            f"Node: {readiness.node.workflow_family} "
            f"branch={readiness.node.branch_id} "
            f"run={readiness.node.source_run_id} "
            f"rev={readiness.node.revision_id}\n"
        )
    for action in readiness.actions:
        if action.legal and action.ready:
            status = "ready"
        elif action.legal:
            status = "blocked"
        else:
            status = "illegal"
        sys.stdout.write(f"{action.action}: {status}\n")
        sys.stdout.write(
            f"  mutation_scope={action.mutation_scope} recommended={str(bool(action.recommended)).lower()}\n"
        )
        if action.available_inputs:
            sys.stdout.write(f"  available_inputs={action.available_inputs}\n")
        if action.missing_prerequisites:
            sys.stdout.write(f"  missing_prerequisites={action.missing_prerequisites}\n")
        for receipt in action.existing_outputs:
            sys.stdout.write(
                "  output="
                f"{receipt.artifact_key} "
                f"status={receipt.artifact_status} "
                f"path={receipt.path} "
                f"consumable={str(bool(receipt.consumable)).lower()} "
                f"resumable={str(bool(receipt.resumable)).lower()} "
                f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
            )
        if action.refusal_reason:
            sys.stdout.write(f"  refusal_reason={action.refusal_reason}\n")
    return 0


def _workflow_plan_scene(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_plan_scene_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = plan_scene_action(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Plan scene failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_preflight_scene_state(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_preflight_scene_state_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = preflight_scene_state(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Preflight scene state failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_generate_continuity_pack(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_generate_continuity_pack_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = generate_continuity_pack(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Generate continuity pack failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_state_repair_scene_patch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_state_repair_scene_patch_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = state_repair_scene_patch(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"State repair scene patch failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_lint_scene_prose(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_lint_scene_prose_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = lint_scene_prose(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Lint scene prose failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_repair_scene_prose(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_repair_scene_prose_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = repair_scene_prose(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Repair scene prose failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_apply_scene_commit(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_apply_scene_commit_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = apply_scene_commit(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Apply scene commit failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_freeze_section(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_freeze_section_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            section_id=int(args.section),
            run_id=getattr(args, "run_id", None),
        )
        result = freeze_section(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Freeze section failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    paths = result.artifact_paths if isinstance(result.artifact_paths, dict) else {}
    sys.stdout.write(
        f"Section frozen: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sec{int(details.get('section_id', 0) or 0):03d}\n"
        f"Status: {result.status}\n"
        f"Boundary: {paths.get('boundary_artifact')}\n"
    )
    return 0


def _workflow_lock_section(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_lock_section_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            section_id=int(args.section),
        )
        result = lock_section(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Lock section failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    sys.stdout.write(
        f"Section locked: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sec{int(details.get('section_id', 0) or 0):03d}\n"
        f"Status: {result.status}\n"
    )
    chapter_seam_report = result.artifact_paths.get("chapter_seam_report") if isinstance(result.artifact_paths, dict) else None
    chapter_final_markdown = result.artifact_paths.get("chapter_final_markdown") if isinstance(result.artifact_paths, dict) else None
    if chapter_seam_report or chapter_final_markdown:
        sys.stdout.write(
            f"Chapter finalization: report={chapter_seam_report} "
            f"final={chapter_final_markdown}\n"
        )
    return 0


def _workflow_advance_section(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        freeze_request = build_freeze_section_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            section_id=int(args.section),
            run_id=getattr(args, "run_id", None),
        )
        freeze_result = freeze_section(workspace=workspace, request=freeze_request)
        if bool(getattr(args, "resume", False)):
            write_result = resume_paused_section(
                workspace=workspace,
                request=build_resume_paused_section_request(
                    workspace=workspace,
                    book_id=args.book,
                    chapter=int(args.chapter),
                    section=int(args.section),
                    ack_outline_attention_items=bool(
                        getattr(args, "ack_outline_attention_items", False)
                    ),
                    force_outline_gate_bypass=bool(
                        getattr(args, "force_outline_gate_bypass", False)
                    ),
                ),
            )
        else:
            write_result = write_frozen_section(
                workspace=workspace,
                request=build_write_section_request(
                    workspace=workspace,
                    book_id=args.book,
                    chapter_id=int(args.chapter),
                    section_id=int(args.section),
                    ack_outline_attention_items=bool(
                        getattr(args, "ack_outline_attention_items", False)
                    ),
                    force_outline_gate_bypass=bool(
                        getattr(args, "force_outline_gate_bypass", False)
                    ),
                ),
            )
        if write_result.status == "retryable_pause":
            sys.stdout.write(
                f"Section paused before lock: ch{int(args.chapter):03d} sec{int(args.section):03d}\n"
                f"Status: {write_result.status}\n"
                f"Message: {write_result.message or ''}\n"
            )
            return 75
        if write_result.status == "hard_fail":
            sys.stderr.write(f"Advance section failed during write: {write_result.message or ''}\n")
            return 1
        lock_request = build_lock_section_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            section_id=int(args.section),
        )
        lock_result = lock_section(workspace=workspace, request=lock_request)
    except Exception as exc:
        sys.stderr.write(f"Advance section failed: {exc}\n")
        return 1
    freeze = freeze_result.details if isinstance(freeze_result.details, dict) else {}
    lock = lock_result.details if isinstance(lock_result.details, dict) else {}
    sys.stdout.write(
        f"Section advanced end-to-end: ch{int(freeze.get('chapter_id', 0) or 0):03d} "
        f"sec{int(freeze.get('section_id', 0) or 0):03d}\n"
        f"Frozen range: {freeze.get('scene_ref_start')} -> {freeze.get('scene_ref_end')}\n"
        f"Write status: {write_result.status}\n"
        f"Locked range: {lock.get('scene_ref_start')} -> {lock.get('scene_ref_end')}\n"
    )
    chapter_seam_report = lock_result.artifact_paths.get("chapter_seam_report") if isinstance(lock_result.artifact_paths, dict) else None
    if chapter_seam_report:
        sys.stdout.write(
            f"Chapter finalization: report={chapter_seam_report} "
            f"final={lock_result.artifact_paths.get('chapter_final_markdown')}\n"
        )
    return 0


def _workflow_write_section(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_write_section_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            section_id=int(args.section),
            ack_outline_attention_items=bool(
                getattr(args, "ack_outline_attention_items", False)
            ),
            force_outline_gate_bypass=bool(
                getattr(args, "force_outline_gate_bypass", False)
            ),
        )
        result = write_frozen_section(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Write section failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Section: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sec{int(details.get('section_id', 0) or 0):03d}\n"
        f"Range: {details.get('scene_ref_start')} -> {details.get('scene_ref_end')}\n"
    )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_write_scene_prose(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_write_scene_prose_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = write_scene_prose(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Write scene prose failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    section_id = details.get("section_id")
    section_label = f"{int(section_id):03d}" if section_id is not None else "n/a"
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Scene: ch{int(details.get('chapter_id', 0) or 0):03d} "
        f"sc{int(details.get('scene_id', 0) or 0):03d} "
        f"sec={section_label}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    for receipt in result.produced_artifacts:
        sys.stdout.write(
            "Artifact: "
            f"{receipt.artifact_key} "
            f"status={receipt.artifact_status} "
            f"path={receipt.path} "
            f"consumable={str(bool(receipt.consumable)).lower()} "
            f"resumable={str(bool(receipt.resumable)).lower()} "
            f"replaceable={str(bool(receipt.replaceable)).lower()}\n"
        )
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_resume_paused_section(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_resume_paused_section_request(
            workspace=workspace,
            book_id=args.book,
            chapter=getattr(args, "chapter", None),
            section=getattr(args, "section", None),
            ack_outline_attention_items=bool(
                getattr(args, "ack_outline_attention_items", False)
            ),
            force_outline_gate_bypass=bool(
                getattr(args, "force_outline_gate_bypass", False)
            ),
        )
        result = resume_paused_section(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Resume paused section failed: {exc}\n")
        return 1
    sys.stdout.write(
        f"Request: {request.request_id}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
        f"Node: {result.node.workflow_family} "
        f"branch={result.node.branch_id} "
        f"run={result.node.source_run_id} "
        f"rev={result.node.revision_id}\n"
    )
    if result.status == "retryable_pause":
        return 75
    if result.status == "hard_fail":
        return 1
    return 0


def _workflow_finalize_chapter(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_finalize_chapter_request(
            workspace=workspace,
            book_id=args.book,
            chapter_id=int(args.chapter),
        )
        result = finalize_chapter(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Finalize chapter failed: {exc}\n")
        return 1
    details = result.details if isinstance(result.details, dict) else {}
    paths = result.artifact_paths if isinstance(result.artifact_paths, dict) else {}
    sys.stdout.write(
        f"Chapter finalized: ch{int(args.chapter):03d}\n"
        f"Status: {result.status}\n"
        f"Report: {paths.get('chapter_seam_report')}\n"
        f"Original: {paths.get('chapter_original_markdown')}\n"
        f"Fixed: {paths.get('chapter_fixed_markdown')}\n"
        f"Final: {paths.get('chapter_final_markdown') or paths.get('chapter_candidate_markdown')}\n"
    )
    return 0


def _book_update_templates(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        updated = update_book_templates(workspace=workspace, book_id=args.book)
    except Exception as exc:
        sys.stderr.write(f"Update templates failed: {exc}\n")
        return 1
    if not updated:
        sys.stdout.write("No books updated.\n")
        return 0
    updated_paths = "\n".join([str(path) for path in updated])
    sys.stdout.write(f"Templates updated for:\n{updated_paths}\n")
    return 0


def _book_reset(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        book_root, report = reset_book_workspace_detailed(
            workspace=workspace,
            book_id=args.book,
            keep_logs=bool(args.keep_logs),
            logs_scope=str(args.logs_scope),
            archive=bool(getattr(args, 'archive', False)),
            archive_mode=str(getattr(args, 'archive_mode', 'copy')),
            archive_logs=bool(getattr(args, 'archive_logs', False)),
        )
    except Exception as exc:
        sys.stderr.write(f"Reset failed: {exc}\n")
        return 1
    sys.stdout.write(f"Book reset at {book_root}\n")
    if report.get("archive_path"):
        sys.stdout.write(f"Archive created at {report.get('archive_path')}\n")
    sys.stdout.write(
        "Reset summary: "
        f"files_deleted={report.get('files_deleted', 0)} "
        f"dirs_deleted={report.get('dirs_deleted', 0)} "
        f"dirs_recreated={report.get('dirs_recreated', 0)} "
        f"book_log_files_deleted={report.get('book_log_files_deleted', 0)} "
        f"all_log_files_deleted={report.get('all_log_files_deleted', 0)}\n"
    )
    return 0


def _characters_generate(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        generate_characters(workspace=workspace, book_id=args.book, count=args.count)
    except Exception as exc:
        sys.stderr.write(f"Characters generation failed: {exc}\n")
        return 1
    sys.stdout.write("Characters generated.\n")
    return 0


def _not_implemented(args: argparse.Namespace) -> int:
    sys.stderr.write("Not implemented yet.\n")
    return 0


def _llm_signatures(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    records = list_signatures(
        workspace,
        book_id=getattr(args, "book", None),
        phase_id=getattr(args, "phase", None),
        turn_id=getattr(args, "turn", None),
        chapter_id=getattr(args, "chapter", None),
        limit=int(getattr(args, "limit", 50) or 50),
    )
    if not records:
        sys.stdout.write("No thought signatures found.\n")
        return 0
    lines = []
    for record in records:
        lines.append(
            f"{record.get('signature_id')} "
            f"phase={record.get('phase_id')} turn={record.get('turn_id')} "
            f"chapter={record.get('chapter_id')} "
            f"book={record.get('book_id')} "
            f"label={record.get('label')}"
        )
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


def _llm_current_thoughts(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        result = run_current_thoughts(
            workspace,
            model_phase=str(getattr(args, "model_phase", "planner") or "planner"),
            signature_id=getattr(args, "signature_id", None),
            phase_id=getattr(args, "phase", None),
            turn_id=getattr(args, "turn", None),
            chapter_id=getattr(args, "chapter", None),
            book_id=getattr(args, "book", None),
            use_global_author=bool(getattr(args, "global_author", False)),
            user_prompt=getattr(args, "prompt", None),
            max_tokens=int(getattr(args, "max_tokens", 2048) or 2048),
            temperature=float(getattr(args, "temperature", 0.2) or 0.2),
            thinking_level=getattr(args, "thinking_level", None),
        )
    except Exception as exc:
        sys.stderr.write(f"Current thoughts failed: {exc}\n")
        return 1
    formatted = format_thought_response(str(result.get("response_text") or ""))
    if formatted:
        sys.stdout.write(formatted.rstrip() + "\n")
    output_path = result.get("output_path")
    if output_path:
        sys.stdout.write(f"Current thoughts saved to {output_path}\n")
    history_path = result.get("history_path")
    if history_path:
        sys.stdout.write(f"Current thoughts history saved to {history_path}\n")
    return 0


def _llm_show_active(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    active_path = signature_active_path(workspace)
    if active_path.exists():
        sys.stdout.write(active_path.read_text(encoding="utf-8") + "\n")
        return 0
    sys.stdout.write("No active signature file found.\n")
    return 0


def _llm_set_active(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    record = select_signature(
        workspace,
        signature_id=getattr(args, "signature_id", None),
        phase_id=getattr(args, "phase", None),
        turn_id=getattr(args, "turn", None),
        chapter_id=getattr(args, "chapter", None),
        book_id=getattr(args, "book", None),
        global_author=bool(getattr(args, "global_author", False)),
    )
    if not record:
        sys.stderr.write("No matching signature found.\n")
        return 1
    set_active_signature(
        workspace,
        record,
        intent=not bool(getattr(args, "outcome", False)),
        outcome=bool(getattr(args, "outcome", False)),
    )
    sys.stdout.write(f"Active signature set to {record.get('signature_id')}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bookforge",
        description="BookForge CLI",
    )
    parser.add_argument(
        "--workspace",
        default="workspace",
        help="Workspace root path (default: workspace).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a new book workspace.")
    init_parser.add_argument("--book", required=True, help="Book id slug.")
    init_parser.add_argument("--author-ref", required=True, help="Author reference, e.g. name/v1.")
    init_parser.add_argument("--title", required=True, help="Book title.")
    init_parser.add_argument("--genre", required=True, help="Comma-separated genre list.")
    init_parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target key=value pair (repeatable).",
    )
    init_parser.add_argument("--series-id", help="Optional series identifier.")
    init_parser.set_defaults(func=_init)

    author_parser = subparsers.add_parser("author", help="Author commands.")
    author_sub = author_parser.add_subparsers(dest="author_command", required=True)
    author_generate = author_sub.add_parser("generate", help="Generate an author persona.")
    author_generate.add_argument("--name", help="Optional author persona name.")
    author_generate.add_argument(
        "--influences",
        help="Comma-separated influences, optional weights with colons.",
    )
    author_generate.add_argument("--prompt-file", help="Path to author prompt file.")
    author_generate.add_argument("--notes", help="Optional notes for author creation.")
    author_generate.set_defaults(func=_author_generate)

    outline_parser = subparsers.add_parser("outline", help="Outline commands.")
    outline_sub = outline_parser.add_subparsers(dest="outline_command", required=True)
    outline_generate = outline_sub.add_parser("generate", help="Generate or resume the deep-outline pipeline.")
    outline_generate.add_argument("--book", required=True, help="Book id.")
    outline_generate.add_argument("--prompt-file", help="Path to outline prompt file.")
    outline_generate.add_argument(
        "--new-version",
        action="store_true",
        help="Create a new outline version.",
    )
    outline_generate.add_argument(
        "--rerun",
        action="store_true",
        help="Rerun the outline pipeline on an existing outline.",
    )
    outline_generate.add_argument(
        "--resume",
        action="store_true",
        help="Resume the latest outline pipeline run.",
    )
    outline_generate.add_argument(
        "--force-phase-full-rerun",
        action="store_true",
        help="For chapter-scoped phases (4a/4b/5/6), rerun all chapters in selected phase range instead of reusing successful chapter checkpoints.",
    )
    outline_generate.add_argument(
        "--from-phase",
        help="Start execution from phase id or step id.",
    )
    outline_generate.add_argument(
        "--to-phase",
        help="Stop execution at phase id or step id.",
    )
    outline_generate.add_argument(
        "--phase",
        help="Run a single phase (alias for --from-phase X --to-phase X).",
    )
    outline_generate.add_argument(
        "--transition-hints-file",
        help="Path to transition hints JSON file.",
    )
    outline_generate.add_argument(
        "--strict-transition-hints",
        action="store_true",
        help="Require strict transition-hint compliance.",
    )
    outline_generate.add_argument(
        "--strict-transition-bridges",
        dest="strict_transition_bridges",
        action="store_true",
        default=True,
        help="Enable strict transition bridge policy (default: enabled).",
    )
    outline_generate.add_argument(
        "--relaxed-transition-bridges",
        dest="strict_transition_bridges",
        action="store_false",
        help="Relax strict transition bridge policy.",
    )
    outline_generate.add_argument(
        "--strict-location-identity",
        dest="strict_location_identity",
        action="store_true",
        default=True,
        help="Enable strict location identity policy (default: enabled).",
    )
    outline_generate.add_argument(
        "--relaxed-location-identity",
        dest="strict_location_identity",
        action="store_false",
        help="Relax strict location identity placeholder policy.",
    )
    outline_generate.add_argument(
        "--transition-insert-budget-per-chapter",
        type=int,
        default=12,
        help="Maximum transition scene insertions selected per chapter (default: 12).",
    )
    outline_generate.add_argument(
        "--allow-transition-scene-insertions",
        dest="allow_transition_scene_insertions",
        action="store_true",
        default=True,
        help="Allow transition scene insertion routing (default: enabled).",
    )
    outline_generate.add_argument(
        "--disallow-transition-scene-insertions",
        dest="allow_transition_scene_insertions",
        action="store_false",
        help="Disable transition scene insertion routing.",
    )
    outline_generate.add_argument(
        "--force-rerun-with-draft",
        action="store_true",
        help="Allow outline rerun even when drafted chapter markdown exists.",
    )
    outline_generate.add_argument(
        "--exact-scene-count",
        action="store_true",
        help="Enable exact chapter scene-count mode (strict).",
    )
    outline_generate.add_argument(
        "--scene-count-range",
        help="Optional chapter scene count range, format MIN-MAX.",
    )
    outline_generate.set_defaults(func=_outline_generate)

    outline_backup = outline_sub.add_parser("backup", help="Back up a completed outline state and run artifacts.")
    outline_backup.add_argument("--book", required=True, help="Book id.")
    outline_backup.add_argument("--run-id", help="Optional source run id. Defaults to latest run pointer.")
    outline_backup.add_argument(
        "--output-dir",
        help="Optional output root directory for backups (default: workspace/backups/outline_completed/<book>).",
    )
    outline_backup.add_argument(
        "--allow-non-success",
        action="store_true",
        help="Allow backup even if the source run status is not SUCCESS/SUCCESS_WITH_WARNINGS.",
    )
    outline_backup.add_argument(
        "--skip-run-artifacts",
        action="store_true",
        help="Skip copying pipeline_run artifacts into the backup snapshot.",
    )
    outline_backup.set_defaults(func=_outline_backup)

    outline_restore = outline_sub.add_parser("restore", help="Restore outline.json from a run or backup snapshot.")
    outline_restore.add_argument("--book", required=True, help="Book id.")
    outline_restore.add_argument("--run-id", help="Restore from this outline run id.")
    outline_restore.add_argument("--backup-path", help="Restore from this backup directory path.")
    outline_restore.add_argument(
        "--overwrite-current",
        action="store_true",
        help="Overwrite current outline.json in place (default archives current outline first).",
    )
    outline_restore.add_argument(
        "--set-latest-run-pointer",
        action="store_true",
        help="When source includes run id, update latest run/report pointers to that run.",
    )
    outline_restore.set_defaults(func=_outline_restore)

    characters_parser = subparsers.add_parser("characters", help="Character commands.")
    characters_sub = characters_parser.add_subparsers(dest="characters_command", required=True)
    characters_generate = characters_sub.add_parser("generate", help="Generate characters.")
    characters_generate.add_argument("--book", required=True, help="Book id.")
    characters_generate.add_argument(
        "--count",
        type=int,
        help="Optional character count limit.",
    )
    characters_generate.set_defaults(func=_characters_generate)

    run_parser = subparsers.add_parser("run", help="Run the section-write generation loop.")
    run_parser.add_argument("--book", required=True, help="Book id.")
    run_parser.add_argument("--steps", type=int, help="Number of steps to run.")
    run_parser.add_argument("--until", help="Stop condition, e.g. chapter:5.")
    run_parser.add_argument("--resume", action="store_true", help="Resume prior run.")
    run_parser.add_argument(
        "--ack-outline-attention-items",
        "--ack-outline-issues",
        dest="ack_outline_attention_items",
        action="store_true",
        help="Acknowledge outline attention items and continue writing when status permits.",
    )
    run_parser.add_argument(
        "--force-outline-gate-bypass",
        action="store_true",
        help="Bypass outline write gate checks (testing only).",
    )
    run_parser.set_defaults(func=_run)

    workflow_parser = subparsers.add_parser("workflow", help="Section-local outline/write workflow commands.")
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_command", required=True)

    workflow_init = workflow_sub.add_parser(
        "init",
        help="Initialize section-local workflow state from immutable outline run artifacts.",
    )
    workflow_init.add_argument("--book", required=True, help="Book id.")
    workflow_init.add_argument("--run-id", help="Optional outline pipeline run id.")
    workflow_init.add_argument(
        "--overwrite",
        action="store_true",
        help="Rebuild canonical workflow files from the selected outline run.",
    )
    workflow_init.set_defaults(func=_workflow_init)

    workflow_status = workflow_sub.add_parser("status", help="Show section workflow status.")
    workflow_status.add_argument("--book", required=True, help="Book id.")
    workflow_status.set_defaults(func=_workflow_status)

    workflow_legal = workflow_sub.add_parser(
        "legal-actions",
        help="Show the current narrow engine actions that are allowed or blocked for the selected scope.",
    )
    workflow_legal.add_argument("--book", required=True, help="Book id.")
    workflow_legal.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_legal.add_argument("--fork-group-id", help="Optional fork-group scope for assembly discovery.")
    workflow_legal.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_legal.add_argument("--section", type=int, help="Optional section scope.")
    workflow_legal.add_argument("--scene", type=int, help="Optional scene scope.")
    workflow_legal.set_defaults(func=_workflow_legal_actions)

    workflow_scene_readiness = workflow_sub.add_parser(
        "scene-readiness",
        help="Show truthful scene-phase readiness for one scene on the current main-branch cursor path.",
    )
    workflow_scene_readiness.add_argument("--book", required=True, help="Book id.")
    workflow_scene_readiness.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_scene_readiness.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_scene_readiness.add_argument("--section", type=int, help="Optional section id.")
    workflow_scene_readiness.set_defaults(func=_workflow_scene_readiness)

    workflow_plan_scene = workflow_sub.add_parser(
        "plan-scene",
        help="Generate a provisional scene card for one scene without auto-running downstream phases.",
    )
    workflow_plan_scene.add_argument("--book", required=True, help="Book id.")
    workflow_plan_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_plan_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_plan_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_plan_scene.set_defaults(func=_workflow_plan_scene)

    workflow_preflight_scene = workflow_sub.add_parser(
        "preflight-scene-state",
        help="Generate a provisional preflight state patch for one scene without applying it.",
    )
    workflow_preflight_scene.add_argument("--book", required=True, help="Book id.")
    workflow_preflight_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_preflight_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_preflight_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_preflight_scene.set_defaults(func=_workflow_preflight_scene_state)

    workflow_continuity_pack = workflow_sub.add_parser(
        "generate-continuity-pack",
        help="Generate a derived continuity pack for one scene without writing prose or mutating canonical state.",
    )
    workflow_continuity_pack.add_argument("--book", required=True, help="Book id.")
    workflow_continuity_pack.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_continuity_pack.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_continuity_pack.add_argument("--section", type=int, help="Optional section id.")
    workflow_continuity_pack.set_defaults(func=_workflow_generate_continuity_pack)

    workflow_state_repair_scene = workflow_sub.add_parser(
        "state-repair-scene-patch",
        help="Generate a provisional corrected state patch for one scene without linting, repairing prose, or committing.",
    )
    workflow_state_repair_scene.add_argument("--book", required=True, help="Book id.")
    workflow_state_repair_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_state_repair_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_state_repair_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_state_repair_scene.set_defaults(func=_workflow_state_repair_scene_patch)

    workflow_lint_scene = workflow_sub.add_parser(
        "lint-scene-prose",
        help="Generate a provisional lint report for one scene without repairing prose or committing.",
    )
    workflow_lint_scene.add_argument("--book", required=True, help="Book id.")
    workflow_lint_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_lint_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_lint_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_lint_scene.set_defaults(func=_workflow_lint_scene_prose)

    workflow_repair_scene = workflow_sub.add_parser(
        "repair-scene-prose",
        help="Generate provisional repaired prose and patch artifacts for one scene without rerunning state repair, lint, or commit.",
    )
    workflow_repair_scene.add_argument("--book", required=True, help="Book id.")
    workflow_repair_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_repair_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_repair_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_repair_scene.set_defaults(func=_workflow_repair_scene_prose)

    workflow_apply_scene_commit = workflow_sub.add_parser(
        "apply-scene-commit",
        help="Commit the active scene's latest passing provisional baseline into canonical state and authoritative scene artifacts.",
    )
    workflow_apply_scene_commit.add_argument("--book", required=True, help="Book id.")
    workflow_apply_scene_commit.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_apply_scene_commit.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_apply_scene_commit.add_argument("--section", type=int, help="Optional section id.")
    workflow_apply_scene_commit.set_defaults(func=_workflow_apply_scene_commit)

    workflow_freeze = workflow_sub.add_parser(
        "freeze-section",
        help="Freeze one section into the canonical outline from a phase-03 chapter artifact.",
    )
    workflow_freeze.add_argument("--book", required=True, help="Book id.")
    workflow_freeze.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_freeze.add_argument("--section", required=True, type=int, help="Section id.")
    workflow_freeze.add_argument("--run-id", help="Optional outline pipeline run id.")
    workflow_freeze.set_defaults(func=_workflow_freeze_section)

    workflow_write = workflow_sub.add_parser(
        "write-section",
        help="Run the section_write loop for one frozen section without locking it.",
    )
    workflow_write.add_argument("--book", required=True, help="Book id.")
    workflow_write.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_write.add_argument("--section", required=True, type=int, help="Section id.")
    workflow_write.add_argument(
        "--ack-outline-attention-items",
        "--ack-outline-issues",
        dest="ack_outline_attention_items",
        action="store_true",
        help="Acknowledge outline attention items before writing.",
    )
    workflow_write.add_argument(
        "--force-outline-gate-bypass",
        action="store_true",
        help="Bypass outline write gate checks while running the writer loop.",
    )
    workflow_write.set_defaults(func=_workflow_write_section)

    workflow_write_scene = workflow_sub.add_parser(
        "write-scene-prose",
        help="Generate provisional prose for one scene without auto-running lint, repair, or commit.",
    )
    workflow_write_scene.add_argument("--book", required=True, help="Book id.")
    workflow_write_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_write_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_write_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_write_scene.set_defaults(func=_workflow_write_scene_prose)

    workflow_lock = workflow_sub.add_parser(
        "lock-section",
        help="Lock one frozen section after prose and meta artifacts exist for all section scenes.",
    )
    workflow_lock.add_argument("--book", required=True, help="Book id.")
    workflow_lock.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_lock.add_argument("--section", required=True, type=int, help="Section id.")
    workflow_lock.set_defaults(func=_workflow_lock_section)

    workflow_finalize = workflow_sub.add_parser(
        "finalize-chapter",
        help="Run pairwise LLM seam repair and chapter finalization for a chapter whose sections are already locked.",
    )
    workflow_finalize.add_argument("--book", required=True, help="Book id.")
    workflow_finalize.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_finalize.set_defaults(func=_workflow_finalize_chapter)

    workflow_seam = workflow_sub.add_parser(
        "seam-chapter",
        help="Run pairwise LLM seam repair for a fully written chapter and emit original/fixed/final chapter artifacts.",
    )
    workflow_seam.add_argument("--book", required=True, help="Book id.")
    workflow_seam.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_seam.set_defaults(func=_workflow_finalize_chapter)

    workflow_advance = workflow_sub.add_parser(
        "advance-section",
        help="Freeze, write, and lock one section end to end.",
    )
    workflow_advance.add_argument("--book", required=True, help="Book id.")
    workflow_advance.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_advance.add_argument("--section", required=True, type=int, help="Section id.")
    workflow_advance.add_argument("--run-id", help="Optional outline pipeline run id.")
    workflow_advance.add_argument("--resume", action="store_true", help="Resume a prior run.")
    workflow_advance.add_argument(
        "--ack-outline-attention-items",
        "--ack-outline-issues",
        dest="ack_outline_attention_items",
        action="store_true",
        help="Acknowledge outline attention items before writing.",
    )
    workflow_advance.add_argument(
        "--force-outline-gate-bypass",
        action="store_true",
        help="Bypass outline write gate checks while running the writer loop.",
    )
    workflow_advance.set_defaults(func=_workflow_advance_section)

    workflow_resume = workflow_sub.add_parser(
        "resume-paused-section",
        help="Resume the exact currently paused main-branch section_write node after validating the expected node.",
    )
    workflow_resume.add_argument("--book", required=True, help="Book id.")
    workflow_resume.add_argument("--chapter", type=int, help="Optional expected active chapter id.")
    workflow_resume.add_argument("--section", type=int, help="Optional expected active section id.")
    workflow_resume.add_argument(
        "--ack-outline-attention-items",
        "--ack-outline-issues",
        dest="ack_outline_attention_items",
        action="store_true",
        help="Acknowledge outline attention items before resuming the writer loop.",
    )
    workflow_resume.add_argument(
        "--force-outline-gate-bypass",
        action="store_true",
        help="Bypass outline write gate checks while resuming the writer loop.",
    )
    workflow_resume.set_defaults(func=_workflow_resume_paused_section)

    llm_parser = subparsers.add_parser("llm", help="LLM utilities.")
    llm_sub = llm_parser.add_subparsers(dest="llm_command", required=True)

    llm_signatures = llm_sub.add_parser("signatures", help="List recorded thought signatures.")
    llm_signatures.add_argument("--book", help="Optional book id filter.")
    llm_signatures.add_argument("--phase", help="Optional phase id filter.")
    llm_signatures.add_argument("--turn", help="Optional turn id filter (T1/T2).")
    llm_signatures.add_argument("--chapter", help="Optional chapter id filter.")
    llm_signatures.add_argument("--limit", type=int, default=50, help="Max signatures to list.")
    llm_signatures.set_defaults(func=_llm_signatures)

    llm_current = llm_sub.add_parser("current-thoughts", help="Summarize model's current context.")
    llm_current.add_argument("--book", help="Optional book id filter for signature selection.")
    llm_current.add_argument("--phase", help="Optional phase id filter for signature selection.")
    llm_current.add_argument("--turn", help="Optional turn id filter for signature selection.")
    llm_current.add_argument("--chapter", help="Optional chapter id filter for signature selection.")
    llm_current.add_argument("--signature-id", help="Explicit signature id to use.")
    llm_current.add_argument(
        "--prompt",
        help="Override the default user prompt for current-thoughts.",
    )
    llm_current.add_argument(
        "--global-author",
        action="store_true",
        help="Use latest global author signature if available.",
    )
    llm_current.add_argument(
        "--model-phase",
        default="planner",
        help="Model phase selector for the current thoughts request (default: planner).",
    )
    llm_current.add_argument("--max-tokens", type=int, default=65000, help="Max tokens for summary.")
    llm_current.add_argument("--temperature", type=float, default=0.2, help="Temperature for summary.")
    llm_current.add_argument(
        "--thinking-level",
        choices=["minimal", "low", "medium", "high"],
        help="Optional thinking level override (Gemini only).",
    )
    llm_current.set_defaults(func=_llm_current_thoughts)

    llm_active = llm_sub.add_parser("active", help="Show active thought signature pointer.")
    llm_active.set_defaults(func=_llm_show_active)

    llm_set_active = llm_sub.add_parser("set-active", help="Set active signature pointer.")
    llm_set_active.add_argument("--book", help="Optional book id filter.")
    llm_set_active.add_argument("--phase", help="Optional phase id filter.")
    llm_set_active.add_argument("--turn", help="Optional turn id filter.")
    llm_set_active.add_argument("--chapter", help="Optional chapter id filter.")
    llm_set_active.add_argument("--signature-id", help="Explicit signature id to use.")
    llm_set_active.add_argument(
        "--global-author",
        action="store_true",
        help="Use latest global author signature if available.",
    )
    llm_set_active.add_argument(
        "--outcome",
        action="store_true",
        help="Set this signature as the outcome pointer instead of intent.",
    )
    llm_set_active.set_defaults(func=_llm_set_active)

    compile_parser = subparsers.add_parser("compile", help="Compile a manuscript.")
    compile_parser.add_argument("--book", required=True, help="Book id.")
    compile_parser.add_argument("--output", help="Output path for manuscript.")
    compile_parser.set_defaults(func=_not_implemented)

    export_parser = subparsers.add_parser("export", help="Export commands.")
    export_sub = export_parser.add_subparsers(dest="export_command", required=True)
    export_synopsis = export_sub.add_parser("synopsis", help="Export a synopsis.")
    export_synopsis.add_argument("--book", required=True, help="Book id.")
    export_synopsis.add_argument("--output", help="Output path for synopsis.")
    export_synopsis.set_defaults(func=_not_implemented)

    book_parser = subparsers.add_parser("book", help="Book scope commands.")
    book_sub = book_parser.add_subparsers(dest="book_command", required=True)

    book_set_current = book_sub.add_parser("set-current", help="Set current book.")
    book_set_current.add_argument("--book", required=True, help="Book id.")
    book_set_current.set_defaults(func=_not_implemented)

    book_show_current = book_sub.add_parser("show-current", help="Show current book.")
    book_show_current.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    book_show_current.set_defaults(func=_not_implemented)

    book_update_templates = book_sub.add_parser("update-templates", help="Update prompt templates for books.")
    book_update_templates.add_argument("--book", help="Optional book id; default updates all books.")
    book_update_templates.set_defaults(func=_book_update_templates)

    book_reset = book_sub.add_parser("reset", help="Reset book draft state.")
    book_reset.add_argument("--book", required=True, help="Book id.")
    book_reset.add_argument(
        "--keep-logs",
        action="store_true",
        help="Do not clear workspace/logs/llm transport logs or workspace/thoughts artifacts during reset.",
    )
    book_reset.add_argument(
        "--logs-scope",
        choices=["book", "all"],
        default="book",
        help="When logs are cleared, remove only this book's logs or all logs.",
    )
    book_reset.add_argument(
        "--archive",
        action="store_true",
        help="Archive reset targets before deletion (workspace/archives).",
    )
    book_reset.add_argument(
        "--archive-mode",
        choices=["copy", "move"],
        default="copy",
        help="Archive mode when --archive is set (copy|move).",
    )
    book_reset.add_argument(
        "--archive-logs",
        action="store_true",
        help="Include logs/llm transport logs and workspace/thoughts artifacts in the archive when --archive is set.",
    )
    book_reset.set_defaults(func=_book_reset)

    book_clear_current = book_sub.add_parser("clear-current", help="Clear current book.")
    book_clear_current.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation if interactive mode is added later.",
    )
    book_clear_current.set_defaults(func=_not_implemented)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
