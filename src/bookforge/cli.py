import argparse
import json
from pathlib import Path
import sys

from bookforge.author import generate_author
from bookforge.execution import (
    AUTHOR_LIBRARY_SCOPE_ID,
    BOOK_INTENT_LIBRARY_SCOPE_ID,
    align_scene_pair_seam_action,
    apply_bridge_scene_insertion_action,
    apply_scene_commit,
    approve_book_intent_action,
    build_apply_scene_commit_request,
    build_apply_bridge_scene_insertion_request,
    build_align_scene_pair_seam_request,
    build_approve_book_intent_request,
    build_create_assembly_branch_request,
    build_create_author_request,
    build_create_branch_request,
    build_create_book_from_intent_request,
    build_continue_scene_request,
    build_create_recovery_branch_request,
    build_discard_branch_request,
    build_draft_book_intent_request,
    build_draft_starter_outline_request,
    build_recovery_branch_request,
    build_generate_continuity_pack_request,
    build_lint_scene_prose_request,
    build_plan_scene_request,
    build_plan_bridge_scene_insertion_request,
    build_preflight_scene_state_request,
    build_promote_branch_request,
    build_promote_branch_to_parent_request,
    build_rebase_branch_request,
    build_record_assembly_validation_request,
    build_refine_author_request,
    build_validate_assembly_branch_request,
    build_repair_scene_prose_request,
    build_state_repair_scene_patch_request,
    build_finalize_chapter_request,
    build_freeze_section_request,
    build_initialize_workflow_request,
    build_lock_section_request,
    build_resume_paused_section_request,
    build_write_scene_prose_request,
    build_write_section_request,
    build_plan_visual_asset_request,
    build_generate_visual_asset_request,
    create_assembly_branch_action,
    create_author_action,
    create_book_from_intent_action,
    create_branch_action,
    create_recovery_branch,
    continue_scene,
    discard_branch_action,
    draft_book_intent_action,
    draft_starter_outline_from_intent,
    finalize_chapter,
    freeze_section,
    generate_continuity_pack,
    initialize_workflow,
    invalidate_scope_outputs,
    lint_scene_prose,
    lock_section,
    normalize_outline_scope,
    plan_scene_action,
    preflight_scene_state,
    promote_branch_action,
    promote_recovery_branch,
    quarantine_artifacts,
    rebase_branch_action,
    rebuild_state_scope,
    redraft_scope,
    repair_scene_prose,
    review_downstream_dependencies,
    review_recovery_semantics,
    resume_paused_section,
    record_assembly_validation_action,
    state_repair_scene_patch,
    refine_author_action,
    validate_assembly_branch_action,
    validate_recovery_branch,
    write_scene_prose,
    write_frozen_section,
    plan_visual_asset_action,
    generate_visual_asset_action,
    plan_bridge_scene_insertion_action,
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
from bookforge.query import (
    get_capability_projection,
    get_author_loop_envelopes,
    get_author_profile,
    get_book_intent,
    get_book_reader_anchor,
    get_book_reader_view,
    get_branch_artifact_index,
    get_branch_detail,
    get_branch_diff_summary,
    get_branch_inventory,
    get_chapter_seam_queue,
    get_scene_pair_seam_detail,
    get_next_writing_target,
    get_writing_bootstrap_status,
    get_outline_lineage_audit,
    get_outline_repair_candidates,
    get_scene_phase_readiness,
    get_section_lineage_matrix,
    get_stale_outline_artifact_inventory,
    list_author_profiles,
    list_book_cards,
    list_book_intents,
    list_execution_options,
    list_visual_provider_descriptors,
    get_visual_action_readiness,
    get_visual_asset_detail,
    get_visual_asset_index,
    get_visual_prompt_plan_detail,
    get_writing_gate_status,
)
from bookforge.query.recovery import (
    get_downstream_dependency_review,
    get_recovery_anchor_candidates,
    get_recovery_branch_health,
    get_recovery_blast_radius,
    get_recovery_plan_readiness,
    get_recovery_plan_preview,
    get_recovery_semantic_review,
    get_recovery_semantic_review_readiness,
    get_scope_invalidation_preview,
    get_state_rebuild_preview,
)
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


def _author_list(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        profiles = list_author_profiles(workspace)
    except Exception as exc:
        sys.stderr.write(f"Author list failed: {exc}\n")
        return 1

    def render(profiles) -> None:
        if not profiles:
            sys.stdout.write("No authors found.\n")
            return
        for profile in profiles:
            sys.stdout.write(
                f"{profile.author_ref}: {profile.display_name} "
                f"versions={profile.version_count} status={profile.artifact_status}\n"
            )
            if profile.short_description:
                sys.stdout.write(f"  {profile.short_description}\n")

    return _write_json_or_text(args, profiles, render)


def _author_profile(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        profile = get_author_profile(
            workspace,
            args.author_ref,
            version=getattr(args, "version", None),
        )
    except Exception as exc:
        sys.stderr.write(f"Author profile failed: {exc}\n")
        return 1

    def render(profile) -> None:
        sys.stdout.write(profile.profile_markdown + "\n")

    return _write_json_or_text(args, profile, render)


def _author_create(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_create_author_request(
            name=getattr(args, "name", None),
            influences=getattr(args, "influences", None),
            prompt_text=getattr(args, "prompt_text", None),
            prompt_file=getattr(args, "prompt_file", None),
            notes=getattr(args, "notes", None),
        )
        result = create_author_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Author create failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _author_refine(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_refine_author_request(
            author_ref=args.author_ref,
            instructions=getattr(args, "instructions", None),
            prompt_file=getattr(args, "prompt_file", None),
            notes=getattr(args, "notes", None),
        )
        result = refine_author_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Author refine failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


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


def _workflow_draft_starter_outline(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_draft_starter_outline_request(
            workspace=workspace,
            book_id=args.book,
            run_id=getattr(args, "run_id", None),
            chapters=getattr(args, "chapters", None),
            sections_per_chapter=getattr(args, "sections_per_chapter", None),
            scenes_per_section=getattr(args, "scenes_per_section", None),
            overwrite=bool(getattr(args, "overwrite", False)),
        )
        result = draft_starter_outline_from_intent(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Draft starter outline failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


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


def _print_execution_result(result) -> None:
    sys.stdout.write(
        f"Request: {result.request_id or ''}\n"
        f"Action: {result.action}\n"
        f"Status: {result.status}\n"
        f"Message: {result.message or ''}\n"
    )
    if result.node is not None:
        sys.stdout.write(
            f"Node: {result.node.workflow_family} "
            f"branch={result.node.branch_id} "
            f"run={result.node.source_run_id} "
            f"rev={result.node.revision_id}\n"
        )
    if result.details:
        sys.stdout.write(f"Details: {json.dumps(result.details, ensure_ascii=True, sort_keys=True)}\n")
    if result.artifact_paths:
        sys.stdout.write(f"Artifacts: {json.dumps(result.artifact_paths, ensure_ascii=True, sort_keys=True)}\n")


def _exit_code_for_result(result) -> int:
    if result.status == "retryable_pause":
        return 75
    if result.status in {"hard_fail", "integrity_degraded"}:
        return 1
    return 0


def _workflow_create_branch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_create_branch_request(
            workspace,
            args.book,
            chapter=getattr(args, "chapter", None),
            section=getattr(args, "section", None),
            branch_id=getattr(args, "branch_id", None),
            parent_branch_id=getattr(args, "parent_branch_id", None) or "main",
            fork_group_id=getattr(args, "fork_group_id", None),
            merge_operation=getattr(args, "merge_operation", None) or "promotion",
            branch_role=getattr(args, "branch_role", None) or "rerun",
        )
        result = create_branch_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Create branch failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _parse_recovery_scopes(raw_values: list[str] | None) -> list[dict[str, int]] | None:
    if not raw_values:
        return None
    scopes: list[dict[str, int]] = []
    for raw in raw_values:
        text = str(raw or "").strip()
        if not text:
            continue
        normalized = text.replace(".", ":").replace("/", ":")
        parts = [part for part in normalized.split(":") if part]
        try:
            if len(parts) == 1:
                scopes.append({"chapter_id": int(parts[0])})
            elif len(parts) == 2:
                scopes.append({"chapter_id": int(parts[0]), "section_id": int(parts[1])})
            elif len(parts) == 3:
                scopes.append({"chapter_id": int(parts[0]), "section_id": int(parts[1]), "scene_id": int(parts[2])})
            else:
                raise ValueError
        except ValueError as exc:
            raise ValueError(f"Invalid recovery scope '{text}'. Use chapter, chapter:section, or chapter:section:scene.") from exc
    return scopes or None


def _workflow_create_recovery_branch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_create_recovery_branch_request(
            workspace,
            args.book,
            anchor_type=args.anchor_type,
            source_run_id=getattr(args, "source_run_id", None),
            affected_scopes=_parse_recovery_scopes(getattr(args, "affected_scope", None)),
            branch_id=getattr(args, "branch_id", None),
            salvage_policy=getattr(args, "salvage_policy", None) or "none",
        )
        result = create_recovery_branch(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Create recovery branch failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_recovery_branch_action(args: argparse.Namespace, action: str, executor) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_recovery_branch_request(
            workspace,
            args.book,
            action=action,
            branch_id=args.branch_id,
        )
        result = executor(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"{action} failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_quarantine_artifacts(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "quarantine_artifacts", quarantine_artifacts)


def _workflow_normalize_outline_scope(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "normalize_outline_scope", normalize_outline_scope)


def _workflow_invalidate_scope_outputs(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "invalidate_scope_outputs", invalidate_scope_outputs)


def _workflow_rebuild_state_scope(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "rebuild_state_scope", rebuild_state_scope)


def _workflow_redraft_scope(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "redraft_scope", redraft_scope)


def _workflow_validate_recovery_branch(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "validate_recovery_branch", validate_recovery_branch)


def _workflow_review_recovery_semantics(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "review_recovery_semantics", review_recovery_semantics)


def _workflow_review_downstream_dependencies(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "review_downstream_dependencies", review_downstream_dependencies)


def _workflow_promote_recovery_branch(args: argparse.Namespace) -> int:
    return _workflow_recovery_branch_action(args, "promote_recovery_branch", promote_recovery_branch)


def _workflow_recovery_health(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        health = get_recovery_branch_health(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Recovery health failed: {exc}\n")
        return 1

    def render(health) -> None:
        sys.stdout.write(f"Book: {health.book_id}\n")
        sys.stdout.write(f"Branch: {health.branch_id}\n")
        sys.stdout.write(f"Status: {health.status}\n")
        for blocker in health.blockers:
            sys.stdout.write(f"Blocker: {blocker}\n")
        for warning in health.warnings:
            sys.stdout.write(f"Warning: {warning}\n")
        sys.stdout.write(f"Receipts: {', '.join(receipt.action for receipt in health.receipts) or 'none'}\n")

    return _write_json_or_text(args, health, render)


def _workflow_recovery_readiness(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        readiness = get_recovery_plan_readiness(
            workspace,
            args.book,
            branch_id=args.branch_id,
            impact_report_ref=getattr(args, "impact_report_ref", None),
        )
    except Exception as exc:
        sys.stderr.write(f"Recovery readiness failed: {exc}\n")
        return 1

    def render(payload) -> None:
        sys.stdout.write(f"Book: {payload.get('book_id')}\n")
        sys.stdout.write(f"Branch: {payload.get('branch_id')}\n")
        sys.stdout.write(f"Ready: {payload.get('ready')}\n")
        sys.stdout.write(f"Main integrity: {payload.get('main_integrity_status')}\n")
        sys.stdout.write(f"Recommended next action: {payload.get('recommended_next_action')}\n")
        for blocker in payload.get("blockers", []):
            sys.stdout.write(f"Blocker: {blocker}\n")

    return _write_json_or_text(args, readiness, render)


def _workflow_recovery_semantic_readiness(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        readiness = get_recovery_semantic_review_readiness(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Recovery semantic readiness failed: {exc}\n")
        return 1

    def render(payload) -> None:
        sys.stdout.write(f"Book: {payload.get('book_id')}\n")
        sys.stdout.write(f"Branch: {payload.get('branch_id')}\n")
        sys.stdout.write(f"Ready: {payload.get('ready')}\n")
        sys.stdout.write(f"Structural health: {payload.get('structural_health_status')}\n")
        sys.stdout.write(f"Semantic status: {payload.get('semantic_validation_status')}\n")
        sys.stdout.write(f"Recommended next action: {payload.get('recommended_next_action')}\n")
        for blocker in payload.get("blockers", []):
            sys.stdout.write(f"Blocker: {blocker}\n")

    return _write_json_or_text(args, readiness, render)


def _workflow_recovery_semantic_review(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        review = get_recovery_semantic_review(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Recovery semantic review failed: {exc}\n")
        return 1

    def render(payload) -> None:
        sys.stdout.write(f"Book: {payload.get('book_id')}\n")
        sys.stdout.write(f"Branch: {payload.get('branch_id')}\n")
        sys.stdout.write(f"Status: {payload.get('status')}\n")
        sys.stdout.write(f"Findings: {len(payload.get('findings') or [])}\n")
        sys.stdout.write(f"Recommended next action: {payload.get('recommended_next_action')}\n")

    return _write_json_or_text(args, review, render)


def _workflow_downstream_dependency_review(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        review = get_downstream_dependency_review(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Downstream dependency review failed: {exc}\n")
        return 1

    def render(payload) -> None:
        sys.stdout.write(f"Book: {payload.get('book_id')}\n")
        sys.stdout.write(f"Branch: {payload.get('branch_id')}\n")
        sys.stdout.write(f"Status: {payload.get('status')}\n")
        sys.stdout.write(f"Downstream scopes: {len(payload.get('downstream_scopes') or [])}\n")
        sys.stdout.write(f"Findings: {len(payload.get('findings') or [])}\n")
        sys.stdout.write(f"Recommended next action: {payload.get('recommended_next_action')}\n")

    return _write_json_or_text(args, review, render)


def _workflow_scope_invalidation_preview(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        preview = get_scope_invalidation_preview(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Scope invalidation preview failed: {exc}\n")
        return 1

    def render(payload) -> None:
        sys.stdout.write(f"Book: {payload.get('book_id')}\n")
        sys.stdout.write(f"Branch: {payload.get('branch_id')}\n")
        sys.stdout.write(f"Candidate paths: {len(payload.get('candidate_paths') or [])}\n")
        for rel_path in payload.get("candidate_paths", [])[:100]:
            sys.stdout.write(f"- {rel_path}\n")

    return _write_json_or_text(args, preview, render)


def _workflow_state_rebuild_preview(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        preview = get_state_rebuild_preview(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"State rebuild preview failed: {exc}\n")
        return 1

    def render(payload) -> None:
        sys.stdout.write(f"Book: {payload.get('book_id')}\n")
        sys.stdout.write(f"Branch: {payload.get('branch_id')}\n")
        sys.stdout.write(f"Rebuild mode: {payload.get('rebuild_mode')}\n")
        sys.stdout.write(f"Candidate paths: {len(payload.get('candidate_paths') or [])}\n")
        for rel_path in payload.get("candidate_paths", [])[:100]:
            sys.stdout.write(f"- {rel_path}\n")

    return _write_json_or_text(args, preview, render)


def _workflow_recovery_blast_radius(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        preview = get_recovery_blast_radius(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Recovery blast radius failed: {exc}\n")
        return 1

    def render(payload) -> None:
        sys.stdout.write(f"Book: {payload.get('book_id')}\n")
        sys.stdout.write(f"Branch: {payload.get('branch_id')}\n")
        sys.stdout.write(f"Candidate artifacts: {payload.get('total_candidate_count')}\n")
        families = payload.get("families") if isinstance(payload.get("families"), dict) else {}
        for family, row in sorted(families.items()):
            sys.stdout.write(f"- {family}: {row.get('candidate_count', 0)} candidates\n")

    return _write_json_or_text(args, preview, render)


def _workflow_create_assembly_branch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_create_assembly_branch_request(
            args.book,
            fork_group_id=args.fork_group_id,
            chapter_id=getattr(args, "chapter", None),
            branch_id=getattr(args, "branch_id", None),
        )
        result = create_assembly_branch_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Create assembly branch failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_discard_branch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_discard_branch_request(
            args.book,
            branch_id=args.branch_id,
            reason=getattr(args, "reason", None),
        )
        result = discard_branch_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Discard branch failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_promote_branch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        target_branch_id = str(getattr(args, "target_branch_id", None) or "main").strip() or "main"
        if target_branch_id == "main":
            request = build_promote_branch_request(args.book, branch_id=args.branch_id)
        else:
            request = build_promote_branch_to_parent_request(
                args.book,
                branch_id=args.branch_id,
                target_branch_id=target_branch_id,
            )
        result = promote_branch_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Promote branch failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_rebase_branch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_rebase_branch_request(
            args.book,
            branch_id=args.branch_id,
            new_branch_id=getattr(args, "new_branch_id", None),
        )
        result = rebase_branch_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Rebase branch failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_record_assembly_validation(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_record_assembly_validation_request(
            args.book,
            branch_id=args.branch_id,
            passed=bool(args.passed),
            message=getattr(args, "message", None),
        )
        result = record_assembly_validation_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Record assembly validation failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_validate_assembly_branch(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_validate_assembly_branch_request(
            args.book,
            branch_id=args.branch_id,
        )
        result = validate_assembly_branch_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Validate assembly branch failed: {exc}\n")
        return 1
    _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_legal_actions(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        options = list_execution_options(
            workspace,
            ScopeSelector(
                book_id=args.book,
                branch_id=getattr(args, "branch_id", None) or "main",
                fork_group_id=getattr(args, "fork_group_id", None),
                workflow_family=getattr(args, "workflow_family", None),
                chapter=getattr(args, "chapter", None),
                section=getattr(args, "section", None),
                scene=getattr(args, "scene", None),
            ),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow legal-actions failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps([option.to_dict() for option in options], ensure_ascii=True, indent=2) + "\n")
        return 0
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


def _book_list(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        cards = list_book_cards(workspace)
    except Exception as exc:
        sys.stderr.write(f"Book list failed: {exc}\n")
        return 1

    def render(cards) -> None:
        if not cards:
            sys.stdout.write("No books found.\n")
            return
        for card in cards:
            sys.stdout.write(
                f"{card.book_id}: {card.title} "
                f"status={card.state_status} integrity={card.integrity_status} branches={card.branch_count}\n"
            )

    return _write_json_or_text(args, cards, render)


def _book_reader(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        view = get_book_reader_view(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=getattr(args, "chapter", None),
            scene_id=getattr(args, "scene", None),
            max_text_chars=int(getattr(args, "max_text_chars", 24_000) or 0),
        )
    except Exception as exc:
        sys.stderr.write(f"Book reader failed: {exc}\n")
        return 1

    def render(view) -> None:
        sys.stdout.write(f"Book: {view.title} ({view.book_id})\n")
        sys.stdout.write(f"Source: {view.source}\n")
        sys.stdout.write(f"Chapters: {len(view.chapters)}\n")
        if view.selected:
            selected = view.selected
            sys.stdout.write(
                f"Selected: {selected.kind} ch={selected.chapter} scene={selected.scene} "
                f"status={selected.status} chars={selected.character_count} truncated={selected.truncated}\n"
            )
            if selected.text:
                sys.stdout.write(selected.text + "\n")
        for warning in view.warnings:
            sys.stdout.write(f"Warning: {warning}\n")

    return _write_json_or_text(args, view, render)


def _book_reader_anchor(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        anchor = get_book_reader_anchor(
            workspace,
            args.book,
            int(args.chapter),
            branch_id=getattr(args, "branch_id", None) or "main",
            scene_id=getattr(args, "scene", None),
            start_offset=getattr(args, "start_offset", None),
            end_offset=getattr(args, "end_offset", None),
            max_text_chars=int(getattr(args, "max_text_chars", 24_000) or 0),
        )
    except Exception as exc:
        sys.stderr.write(f"Book reader anchor failed: {exc}\n")
        return 1

    def render(anchor) -> None:
        sys.stdout.write(f"Book: {anchor.book_id}\n")
        sys.stdout.write(f"Branch: {anchor.branch_id}\n")
        sys.stdout.write(
            f"Anchor: {anchor.kind} ch={anchor.chapter} scene={anchor.scene} "
            f"status={anchor.reader_status} artifact={anchor.artifact_status}\n"
        )
        sys.stdout.write(
            f"Span: {anchor.span_start}-{anchor.span_end} "
            f"valid_mutation_target={anchor.valid_as_mutation_target}\n"
        )
        if anchor.invalid_reason:
            sys.stdout.write(f"Invalid reason: {anchor.invalid_reason}\n")
        if anchor.text:
            sys.stdout.write(anchor.text + "\n")

    return _write_json_or_text(args, anchor, render)


def _book_intent_list(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        records = list_book_intents(workspace, status=getattr(args, "status", None))
    except Exception as exc:
        sys.stderr.write(f"Book intent list failed: {exc}\n")
        return 1

    def render(records) -> None:
        if not records:
            sys.stdout.write("No book intents found.\n")
            return
        for record in records:
            intent = record.intent
            sys.stdout.write(
                f"{intent.intent_id}: {intent.title} status={intent.status} "
                f"book={intent.book_id or intent.created_book_id or ''} author={intent.author_ref}\n"
            )

    return _write_json_or_text(args, records, render)


def _book_intent_show(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        record = get_book_intent(workspace, args.intent)
    except Exception as exc:
        sys.stderr.write(f"Book intent show failed: {exc}\n")
        return 1

    def render(record) -> None:
        intent = record.intent
        sys.stdout.write(f"Intent: {intent.intent_id}\n")
        sys.stdout.write(f"Status: {intent.status}\n")
        sys.stdout.write(f"Title: {intent.title}\n")
        sys.stdout.write(f"Author: {intent.author_ref}\n")
        sys.stdout.write(f"Genre: {', '.join(intent.genre)}\n")
        if intent.book_id:
            sys.stdout.write(f"Book ID: {intent.book_id}\n")
        if intent.reader_promise:
            sys.stdout.write(f"Reader promise: {intent.reader_promise}\n")
        if intent.short_synopsis:
            sys.stdout.write(f"Short synopsis: {intent.short_synopsis}\n")
        sys.stdout.write(f"Path: {record.path}\n")

    return _write_json_or_text(args, record, render)


def _book_intent_draft(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_draft_book_intent_request(
            title=args.title,
            author_ref=args.author_ref,
            genre=parse_genre(args.genre),
            seed_text=getattr(args, "seed_text", None),
            seed_file=getattr(args, "seed_file", None),
            book_id=getattr(args, "book_id", None),
            series_id=getattr(args, "series_id", None),
            targets=parse_targets(getattr(args, "target", []) or []),
            short_synopsis=getattr(args, "short_synopsis", None),
            long_synopsis=getattr(args, "long_synopsis", None),
            reader_promise=getattr(args, "reader_promise", None),
            central_conflict=getattr(args, "central_conflict", None),
            tone=getattr(args, "tone", None),
            must_have=getattr(args, "must_have", []) or [],
            must_not=getattr(args, "must_not", []) or [],
            source_ref=getattr(args, "source_ref", None),
        )
        result = draft_book_intent_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Book intent draft failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _book_intent_approve(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_approve_book_intent_request(intent_ref=args.intent)
        result = approve_book_intent_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Book intent approve failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _book_intent_create(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_create_book_from_intent_request(
            intent_ref=args.intent,
            book_id=getattr(args, "book_id", None),
            series_id=getattr(args, "series_id", None),
        )
        result = create_book_from_intent_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Book intent create failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_branch_inventory(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        inventory = get_branch_inventory(workspace, args.book)
    except Exception as exc:
        sys.stderr.write(f"Workflow branch-inventory failed: {exc}\n")
        return 1

    def render(inventory) -> None:
        sys.stdout.write(f"Book: {inventory.book_id}\n")
        sys.stdout.write(f"Branches: {len(inventory.branches)}\n")
        sys.stdout.write(f"Fork groups: {len(inventory.fork_groups)}\n")
        for branch in inventory.branches:
            stale = " stale_parent" if branch.stale_parent else ""
            sys.stdout.write(
                f"- {branch.branch_id}: state={branch.lifecycle_state} role={branch.branch_role} "
                f"merge={branch.merge_operation}{stale}\n"
            )

    return _write_json_or_text(args, inventory, render)


def _workflow_branch_detail(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        detail = get_branch_detail(
            workspace,
            args.book,
            args.branch_id,
            chapter_id=getattr(args, "chapter", None),
            section_id=getattr(args, "section", None),
            scene_id=getattr(args, "scene", None),
            max_text_chars=int(getattr(args, "max_text_chars", 0) or 0),
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow branch-detail failed: {exc}\n")
        return 1

    def render(detail) -> None:
        sys.stdout.write(f"Book: {detail.book_id}\n")
        sys.stdout.write(f"Branch: {detail.branch_id}\n")
        if detail.branch_record is not None:
            sys.stdout.write(
                f"State: {detail.branch_record.lifecycle_state} "
                f"role={detail.branch_record.branch_role} "
                f"merge={detail.branch_record.merge_operation}\n"
            )
            if detail.branch_record.stale_parent:
                sys.stdout.write("Warning: stale_parent\n")
        sys.stdout.write(f"Legal actions: {len(detail.legal_actions)}\n")
        allowed = [action for action in detail.legal_actions if action.get("allowed")]
        if allowed:
            sys.stdout.write("Allowed:\n")
            for action in allowed[:12]:
                sys.stdout.write(f"- {action.get('action')}\n")
        if detail.scene_readiness:
            sys.stdout.write(
                f"Scene readiness: {detail.scene_readiness.get('scene_status')} "
                f"next={detail.scene_readiness.get('recommended_next_action')}\n"
            )
        if detail.reader and detail.reader.get("selected"):
            selected = detail.reader["selected"]
            sys.stdout.write(
                f"Reader selected: {selected.get('kind')} "
                f"ch={selected.get('chapter')} scene={selected.get('scene')} "
                f"status={selected.get('status')}\n"
            )
        for warning in detail.warnings:
            sys.stdout.write(f"Warning: {warning}\n")

    return _write_json_or_text(args, detail, render)


def _workflow_branch_artifact_index(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        index = get_branch_artifact_index(
            workspace,
            args.book,
            getattr(args, "branch_id", None) or "main",
            limit=int(getattr(args, "limit", 500) or 500),
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow branch-artifact-index failed: {exc}\n")
        return 1

    def render(index) -> None:
        sys.stdout.write(f"Book: {index.book_id}\n")
        sys.stdout.write(f"Branch: {index.branch_id}\n")
        sys.stdout.write(f"Artifacts: {len(index.records)}\n")
        sys.stdout.write(f"Classes: {index.class_counts}\n")
        sys.stdout.write(f"Relationships: {index.relationship_counts}\n")
        for warning in index.warnings:
            sys.stdout.write(f"Warning: {warning}\n")

    return _write_json_or_text(args, index, render)


def _workflow_branch_diff_summary(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        summary = get_branch_diff_summary(
            workspace,
            args.book,
            args.branch_id,
            against=getattr(args, "against", "main") or "main",
            limit=int(getattr(args, "limit", 500) or 500),
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow branch-diff-summary failed: {exc}\n")
        return 1

    def render(summary) -> None:
        sys.stdout.write(f"Book: {summary.book_id}\n")
        sys.stdout.write(f"Branch: {summary.branch_id} against={summary.against_branch_id}\n")
        sys.stdout.write(f"Status: {summary.status}\n")
        sys.stdout.write(f"Changed artifacts: {len(summary.changed_records)}\n")
        sys.stdout.write(f"Changed classes: {summary.class_counts}\n")
        for warning in summary.warnings:
            sys.stdout.write(f"Warning: {warning}\n")

    return _write_json_or_text(args, summary, render)


def _workflow_recovery_anchor_candidates(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        report = get_recovery_anchor_candidates(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow recovery-anchor-candidates failed: {exc}\n")
        return 1

    def render(report) -> None:
        sys.stdout.write(f"Book: {report.book_id}\n")
        sys.stdout.write(f"Status: {report.status}\n")
        sys.stdout.write(f"Affected scopes: {len(report.affected_scopes)}\n")
        sys.stdout.write(f"Recommended: {report.recommended_candidate_id}\n")
        sys.stdout.write(f"Auto-selected: {report.auto_selected_candidate_id}\n")
        for candidate in report.candidates:
            selectable = "selectable" if candidate.selectable else "blocked"
            sys.stdout.write(
                f"- {candidate.candidate_id}: {selectable} "
                f"trust={candidate.trust_level} risk={candidate.risk_level} "
                f"human={candidate.requires_human_decision}\n"
            )
        for warning in report.warnings:
            sys.stdout.write(f"Warning: {warning}\n")

    return _write_json_or_text(args, report, render)


def _workflow_recovery_plan_preview(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        preview = get_recovery_plan_preview(
            workspace,
            args.book,
            anchor_type=getattr(args, "anchor_type", None),
            source_run_id=getattr(args, "source_run_id", None),
            branch_id=getattr(args, "branch_id", None),
            salvage_policy=getattr(args, "salvage_policy", "none") or "none",
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow recovery-plan-preview failed: {exc}\n")
        return 1

    def render(preview) -> None:
        sys.stdout.write(f"Book: {preview.book_id}\n")
        sys.stdout.write(f"Status: {preview.status}\n")
        if preview.selected_anchor:
            sys.stdout.write(
                f"Anchor: {preview.selected_anchor.anchor_type} "
                f"run={preview.selected_anchor.source_run_id}\n"
            )
        if preview.blocked_reason:
            sys.stdout.write(f"Blocked: {preview.blocked_reason}\n")
        for step in preview.steps:
            approval = " approval" if step.approval_required else ""
            sys.stdout.write(f"{step.order}. {step.action}{approval}: {step.summary}\n")
            if step.command:
                sys.stdout.write(f"   {step.command}\n")

    return _write_json_or_text(args, preview, render)


def _write_json_or_text(args: argparse.Namespace, payload, render_text) -> int:
    if getattr(args, "json", False):
        if hasattr(payload, "to_dict"):
            payload = payload.to_dict()
        elif isinstance(payload, list):
            payload = [item.to_dict() if hasattr(item, "to_dict") else item for item in payload]
        sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
        return 0
    render_text(payload)
    return 0


def _capabilities(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        projection = get_capability_projection(workspace=workspace, book_id=getattr(args, "book", None))
    except Exception as exc:
        sys.stderr.write(f"Capability projection failed: {exc}\n")
        return 1

    def render(projection) -> None:
        by_status = {}
        by_unit = {}
        for capability in projection.capabilities:
            by_status[capability.implementation_status] = by_status.get(capability.implementation_status, 0) + 1
            by_unit[capability.unit_type] = by_unit.get(capability.unit_type, 0) + 1
        sys.stdout.write(f"Capability projection: {projection.projection_source}\n")
        sys.stdout.write(f"Capabilities: {len(projection.capabilities)}\n")
        sys.stdout.write(f"By status: {by_status}\n")
        sys.stdout.write(f"By unit: {by_unit}\n")
        sys.stdout.write("Use --json for the machine-readable projection consumed by Nanda.\n")

    return _write_json_or_text(args, projection, render)


def _visual_providers(args: argparse.Namespace) -> int:
    try:
        providers = list_visual_provider_descriptors()
    except Exception as exc:
        sys.stderr.write(f"Visual providers failed: {exc}\n")
        return 1

    def render(providers) -> None:
        for provider in providers:
            default = " default" if "background_layer" in provider.default_for_purpose else ""
            sys.stdout.write(
                f"{provider.key}{default}: {provider.display_name} "
                f"status={provider.implementation_status} refs={provider.reference_image_supported} "
                f"alpha={provider.transparent_background_supported}\n"
            )
            if provider.price_notes:
                sys.stdout.write(f"  price: {provider.price_notes}\n")
            if provider.limitations:
                sys.stdout.write(f"  limits: {provider.limitations[0]}\n")

    return _write_json_or_text(args, providers, render)


def _visual_readiness(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        readiness = get_visual_action_readiness(
            workspace,
            book_id=getattr(args, "book", None),
            action=getattr(args, "action", "generate_background_layer"),
            visual_purpose=getattr(args, "purpose", "background_layer"),
            provider_model=getattr(args, "model", None),
            require_credentials=not bool(getattr(args, "ignore_credentials", False)),
            reference_image_count=int(getattr(args, "reference_image_count", 0) or 0),
            transparent_background=bool(getattr(args, "transparent_background", False)),
        )
    except Exception as exc:
        sys.stderr.write(f"Visual readiness failed: {exc}\n")
        return 1

    def render(readiness) -> None:
        sys.stdout.write(
            f"Action: {readiness.action}\n"
            f"Purpose: {readiness.visual_purpose}\n"
            f"Provider: {readiness.provider_id}:{readiness.model_id}\n"
            f"Ready: {readiness.ready}\n"
            f"Allowed: {readiness.allowed}\n"
        )
        if readiness.missing_prerequisites:
            sys.stdout.write(f"Missing: {', '.join(readiness.missing_prerequisites)}\n")
        if readiness.refusal_reasons:
            sys.stdout.write(f"Refusals: {', '.join(readiness.refusal_reasons)}\n")

    return _write_json_or_text(args, readiness, render)


def _visual_plan(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        prompt_text = getattr(args, "prompt_text", None)
        if getattr(args, "prompt_file", None):
            prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")
        request = build_plan_visual_asset_request(
            book_id=args.book,
            branch_id=getattr(args, "branch_id", None),
            prompt_text=prompt_text,
            visual_purpose=getattr(args, "purpose", "background_layer"),
            provider_model=getattr(args, "model", None),
            style_profile=getattr(args, "style_profile", None),
            layer_intent=getattr(args, "layer_intent", None),
            negative_prompt=getattr(args, "negative_prompt", None),
        )
        result = plan_visual_asset_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Visual plan failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _visual_generate(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_generate_visual_asset_request(
            book_id=args.book,
            branch_id=getattr(args, "branch_id", None),
            prompt_plan_path=args.prompt_plan,
            provider_model=getattr(args, "model", None),
            allow_spend=bool(getattr(args, "allow_spend", False)),
        )
        result = generate_visual_asset_action(workspace, request)
    except Exception as exc:
        sys.stderr.write(f"Visual generate failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _visual_artifacts(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        index = get_visual_asset_index(workspace, args.book, branch_id=getattr(args, "branch_id", None) or "main")
    except Exception as exc:
        sys.stderr.write(f"Visual artifacts failed: {exc}\n")
        return 1

    def render(index) -> None:
        sys.stdout.write(f"Book: {index.book_id}\n")
        sys.stdout.write(f"Branch: {index.branch_id}\n")
        sys.stdout.write(f"Prompt plans: {len(index.prompt_plans)}\n")
        for plan in index.prompt_plans[:20]:
            sys.stdout.write(
                f"  {plan.prompt_plan_id}: {plan.visual_purpose} "
                f"{plan.provider_id}:{plan.model_id} status={plan.artifact_status}\n"
            )
        sys.stdout.write(f"Visual assets: {len(index.assets)}\n")
        for asset in index.assets[:20]:
            sys.stdout.write(
                f"  {asset.asset_id}: {asset.visual_purpose} "
                f"{asset.provider_id}:{asset.model_id} status={asset.artifact_status}\n"
            )

    return _write_json_or_text(args, index, render)


def _visual_asset_detail(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        detail = get_visual_asset_detail(
            workspace,
            args.book,
            args.asset_id,
            branch_id=getattr(args, "branch_id", None) or "main",
        )
    except Exception as exc:
        sys.stderr.write(f"Visual asset detail failed: {exc}\n")
        return 1
    return _write_json_or_text(args, detail, lambda detail: sys.stdout.write(json.dumps(detail.to_dict(), ensure_ascii=True, indent=2) + "\n"))


def _visual_prompt_plan_detail(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        detail = get_visual_prompt_plan_detail(
            workspace,
            args.book,
            args.prompt_plan,
            branch_id=getattr(args, "branch_id", None) or "main",
        )
    except Exception as exc:
        sys.stderr.write(f"Visual prompt plan detail failed: {exc}\n")
        return 1
    return _write_json_or_text(args, detail, lambda detail: sys.stdout.write(json.dumps(detail.to_dict(), ensure_ascii=True, indent=2) + "\n"))


def _workflow_outline_lineage_audit(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        audit = get_outline_lineage_audit(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Workflow outline-lineage-audit failed: {exc}\n")
        return 1

    def render(audit) -> None:
        sys.stdout.write(f"Book: {audit.book_id}\n")
        sys.stdout.write(f"Lineage status: {audit.status}\n")
        sys.stdout.write(f"Declared source run: {audit.declared_source_run_id}\n")
        sys.stdout.write(f"Latest outline run: {audit.latest_outline_run_id}\n")
        sys.stdout.write(f"First technical divergence: {audit.first_technical_divergence}\n")
        sys.stdout.write(f"First visible story divergence: {audit.first_visible_story_divergence}\n")
        sys.stdout.write(f"Affected sections: {len(audit.affected_sections)}\n")
        for row in audit.affected_sections[:25]:
            sys.stdout.write(
                f"- ch{row.chapter_id:03d} sec{row.section_id:03d}: "
                f"{row.suspected_contamination_class}; next={row.recommended_safe_next_action}; "
                f"diffs={', '.join(row.differing_fields[:5]) or 'none'}\n"
            )
        if len(audit.affected_sections) > 25:
            sys.stdout.write(f"... {len(audit.affected_sections) - 25} more affected section(s)\n")
        sys.stdout.write("Repair candidates:\n")
        for candidate in audit.repair_candidates:
            status = "blocked" if candidate.blocked else "available"
            sys.stdout.write(f"- {candidate.action} [{status}]: {candidate.summary}\n")

    return _write_json_or_text(args, audit, render)


def _workflow_section_lineage_matrix(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        rows = get_section_lineage_matrix(
            workspace,
            args.book,
            branch_id=args.branch_id,
            chapter_id=args.chapter,
            section_id=args.section,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow section-lineage-matrix failed: {exc}\n")
        return 1

    def render(rows) -> None:
        sys.stdout.write(f"Book: {args.book}\n")
        sys.stdout.write(f"Rows: {len(rows)}\n")
        for row in rows:
            sys.stdout.write(
                f"- ch{row.chapter_id:03d} sec{row.section_id:03d} {row.section_title or ''}: "
                f"{row.suspected_contamination_class}; scenes={row.scene_count_delta or 'aligned'}; "
                f"chars={'; '.join(row.character_cohort_delta) or 'aligned'}; "
                f"next={row.recommended_safe_next_action}\n"
            )

    return _write_json_or_text(args, rows, render)


def _workflow_stale_outline_artifacts(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        artifacts = get_stale_outline_artifact_inventory(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Workflow stale-outline-artifacts failed: {exc}\n")
        return 1

    def render(artifacts) -> None:
        sys.stdout.write(f"Book: {args.book}\n")
        sys.stdout.write(f"Artifacts: {len(artifacts)}\n")
        for artifact in artifacts:
            scope = ""
            if artifact.chapter_id is not None:
                scope = f" ch{artifact.chapter_id:03d}"
                if artifact.section_id is not None:
                    scope += f" sec{artifact.section_id:03d}"
            sys.stdout.write(
                f"- {artifact.path}{scope}: {artifact.artifact_family} "
                f"class={artifact.artifact_class} safe={artifact.safe_to_consume_as_canonical}\n"
            )

    return _write_json_or_text(args, artifacts, render)


def _workflow_outline_repair_candidates(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        candidates = get_outline_repair_candidates(workspace, args.book, branch_id=args.branch_id)
    except Exception as exc:
        sys.stderr.write(f"Workflow outline-repair-candidates failed: {exc}\n")
        return 1

    def render(candidates) -> None:
        sys.stdout.write(f"Book: {args.book}\n")
        for candidate in candidates:
            status = "blocked" if candidate.blocked else "available"
            sys.stdout.write(
                f"- {candidate.action} [{status}] risk={candidate.risk_level} "
                f"human={candidate.requires_human_decision}: {candidate.summary}\n"
            )
            sys.stdout.write(f"  reason={candidate.reason}\n")

    return _write_json_or_text(args, candidates, render)


def _workflow_scene_readiness(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        readiness = get_scene_phase_readiness(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
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


def _workflow_next_writing_target(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        target = get_next_writing_target(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=getattr(args, "chapter", None),
            section_id=getattr(args, "section", None),
            scene_id=getattr(args, "scene", None),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow next-writing-target failed: {exc}\n")
        return 1

    def render(target) -> None:
        sys.stdout.write(
            f"Book: {target.book_id}\n"
            f"Branch: {target.branch_id}\n"
            f"Status: {target.status}\n"
            f"Can continue: {str(bool(target.can_continue)).lower()}\n"
            f"Book complete: {str(bool(target.book_complete)).lower()}\n"
            f"Recommended action: {target.recommended_action or ''}\n"
        )
        if target.current_scene:
            current = target.current_scene
            sys.stdout.write(
                "Current scene: "
                f"ch{int(current.get('chapter') or 0):03d} "
                f"sc{int(current.get('scene') or 0):03d} "
                f"sec={current.get('section') or 'n/a'} "
                f"status={current.get('scene_status') or ''}\n"
            )
        if target.next_scene:
            nxt = target.next_scene
            sys.stdout.write(
                "Next scene: "
                f"ch{int(nxt.get('chapter') or 0):03d} "
                f"sc{int(nxt.get('scene') or 0):03d} "
                f"sec={nxt.get('section') or 'n/a'}\n"
            )
        if target.next_section:
            section = target.next_section
            sys.stdout.write(
                "Next section: "
                f"ch{int(section.get('chapter') or 0):03d} "
                f"sec={section.get('section') or 'n/a'} "
                f"status={section.get('status') or ''}\n"
            )
        if target.next_chapter:
            chapter = target.next_chapter
            sys.stdout.write(
                "Next chapter: "
                f"ch{int(chapter.get('chapter') or 0):03d} "
                f"status={chapter.get('status') or ''}\n"
            )
        if target.blocked_reason:
            sys.stdout.write(f"Blocked reason: {target.blocked_reason}\n")
        if target.node is not None:
            sys.stdout.write(
                f"Node: {target.node.workflow_family} "
                f"branch={target.node.branch_id} "
                f"run={target.node.source_run_id} "
                f"rev={target.node.revision_id}\n"
            )

    return _write_json_or_text(args, target, render)


def _workflow_writing_bootstrap(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        status = get_writing_bootstrap_status(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None),
            chapter_id=getattr(args, "chapter", None),
            section_id=getattr(args, "section", None),
            scene_id=getattr(args, "scene", None),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow writing-bootstrap failed: {exc}\n")
        return 1

    def render(status) -> None:
        sys.stdout.write(
            f"Book: {status.book_id}\n"
            f"Status: {status.status}\n"
            f"Can start writing: {str(bool(status.can_start_writing)).lower()}\n"
            f"Recommended action: {status.recommended_action or ''}\n"
            f"Approval class: {status.required_approval_class or ''}\n"
        )
        if status.target_branch_id:
            sys.stdout.write(f"Target branch: {status.target_branch_id}\n")
        if status.target_selector:
            sys.stdout.write(f"Target selector: {status.target_selector}\n")
        if status.blocked_reason:
            sys.stdout.write(f"Blocked reason: {status.blocked_reason}\n")
        for stage in status.stages:
            sys.stdout.write(
                f"{stage.stage_key}: {stage.status} ready={str(bool(stage.ready)).lower()} "
                f"action={stage.action or ''}\n"
            )
            if stage.blocked_reason:
                sys.stdout.write(f"  blocked_reason={stage.blocked_reason}\n")

    return _write_json_or_text(args, status, render)


def _workflow_writing_gates(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        status = get_writing_gate_status(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=getattr(args, "chapter", None),
            section_id=getattr(args, "section", None),
            scene_id=getattr(args, "scene", None),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow writing-gates failed: {exc}\n")
        return 1

    def render(status) -> None:
        sys.stdout.write(
            f"Book: {status.book_id}\n"
            f"Branch: {status.branch_id}\n"
            f"Can continue: {str(bool(status.can_continue)).lower()}\n"
            f"Book complete: {str(bool(status.book_complete)).lower()}\n"
            f"Recommended next action: {status.recommended_next_action or ''}\n"
        )
        if status.blocked_reason:
            sys.stdout.write(f"Blocked reason: {status.blocked_reason}\n")
        for gate in status.gates:
            sys.stdout.write(
                f"{gate.gate_key}: {gate.status} ready={str(bool(gate.ready)).lower()} "
                f"action={gate.action or ''}\n"
            )
            if gate.scope:
                sys.stdout.write(f"  scope={gate.scope}\n")
            if gate.blocked_reason:
                sys.stdout.write(f"  blocked_reason={gate.blocked_reason}\n")
        if status.node is not None:
            sys.stdout.write(
                f"Node: {status.node.workflow_family} "
                f"branch={status.node.branch_id} "
                f"run={status.node.source_run_id} "
                f"rev={status.node.revision_id}\n"
            )

    return _write_json_or_text(args, status, render)


def _workflow_author_loop_envelopes(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        envelopes = get_author_loop_envelopes(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=getattr(args, "chapter", None),
            section_id=getattr(args, "section", None),
            scene_id=getattr(args, "scene", None),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow author-loop-envelopes failed: {exc}\n")
        return 1

    def render(envelopes) -> None:
        sys.stdout.write(
            f"Book: {envelopes.book_id}\n"
            f"Branch: {envelopes.branch_id}\n"
            f"Recommended envelope: {envelopes.recommended_envelope or ''}\n"
        )
        for envelope in envelopes.envelopes:
            sys.stdout.write(
                f"{envelope.envelope_key}: ready={str(bool(envelope.ready)).lower()} "
                f"target={envelope.target_action or ''} max_steps={envelope.max_steps_hint or ''}\n"
            )
            if envelope.blocked_reason:
                sys.stdout.write(f"  blocked_reason={envelope.blocked_reason}\n")
            if envelope.allowed_actions:
                sys.stdout.write(f"  actions={', '.join(envelope.allowed_actions)}\n")

    return _write_json_or_text(args, envelopes, render)


def _workflow_chapter_seam_queue(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        queue = get_chapter_seam_queue(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=int(args.chapter),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow chapter-seam-queue failed: {exc}\n")
        return 1

    def render(queue) -> None:
        sys.stdout.write(
            f"Book: {queue.book_id}\n"
            f"Branch: {queue.branch_id}\n"
            f"Chapter: {queue.chapter_id}\n"
            f"Status: {queue.status}\n"
            f"Pairs: {len(queue.items)} ready={queue.ready_count} blocked={queue.blocked_count} aligned={queue.aligned_count}\n"
        )
        if queue.recommended_pair:
            pair = queue.recommended_pair
            sys.stdout.write(
                "Recommended pair: "
                f"sc{int(pair.get('scene_a_id') or 0):03d}->sc{int(pair.get('scene_b_id') or 0):03d} "
                f"action={pair.get('action') or ''}\n"
            )
        for item in queue.items:
            sys.stdout.write(
                f"- sc{item.scene_a_id:03d}->sc{item.scene_b_id:03d}: {item.status}"
            )
            if item.action:
                sys.stdout.write(f" action={item.action}")
            if item.report_status:
                sys.stdout.write(f" report={item.report_status}")
            sys.stdout.write("\n")
            if item.blocked_reason:
                sys.stdout.write(f"  blocked_reason={item.blocked_reason}\n")
            if item.report_path:
                sys.stdout.write(f"  report_path={item.report_path}\n")

    return _write_json_or_text(args, queue, render)


def _workflow_scene_pair_seam_detail(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        detail = get_scene_pair_seam_detail(
            workspace,
            args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=int(args.chapter),
            scene_a_id=int(args.scene_a),
            scene_b_id=int(args.scene_b),
            include_report=not bool(getattr(args, "summary_only", False)),
            prefer_emitted=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Workflow scene-pair-seam-detail failed: {exc}\n")
        return 1

    def render(detail) -> None:
        sys.stdout.write(
            f"Book: {detail.book_id}\n"
            f"Branch: {detail.branch_id}\n"
            f"Pair: ch{detail.chapter_id:03d} sc{detail.scene_a_id:03d}->sc{detail.scene_b_id:03d}\n"
            f"Status: {detail.status}\n"
            f"Report found: {str(bool(detail.report_found)).lower()}\n"
        )
        if detail.report_path:
            sys.stdout.write(f"Report path: {detail.report_path}\n")
        if detail.report_status:
            sys.stdout.write(f"Report status: {detail.report_status}\n")
        if detail.issue_counts_before:
            sys.stdout.write(f"Issues before: {detail.issue_counts_before}\n")
        if detail.issue_counts_after:
            sys.stdout.write(f"Issues after: {detail.issue_counts_after}\n")
        if detail.repair_action_count is not None:
            sys.stdout.write(f"Repair actions: {detail.repair_action_count}\n")
        if detail.action:
            sys.stdout.write(f"Next action: {detail.action}\n")
        if detail.blocked_reason:
            sys.stdout.write(f"Blocked reason: {detail.blocked_reason}\n")

    return _write_json_or_text(args, detail, render)


def _workflow_plan_scene(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_plan_scene_request(
            workspace=workspace,
            book_id=args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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


def _workflow_continue_scene(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_continue_scene_request(
            workspace=workspace,
            book_id=args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=int(args.chapter),
            scene_id=int(args.scene),
            section_id=getattr(args, "section", None),
        )
        result = continue_scene(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Continue scene failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_align_scene_pair_seam(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_align_scene_pair_seam_request(
            workspace=workspace,
            book_id=args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=int(args.chapter),
            scene_a_id=int(args.scene_a),
            scene_b_id=getattr(args, "scene_b", None),
        )
        result = align_scene_pair_seam_action(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Align scene-pair seam failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_plan_bridge_scene_insertion(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_plan_bridge_scene_insertion_request(
            workspace=workspace,
            book_id=args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=int(args.chapter),
            scene_a_id=int(args.scene_a),
            scene_b_id=getattr(args, "scene_b", None),
            objective=getattr(args, "objective", None),
        )
        result = plan_bridge_scene_insertion_action(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Plan bridge scene insertion failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


def _workflow_apply_bridge_scene_insertion(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        request = build_apply_bridge_scene_insertion_request(
            workspace=workspace,
            book_id=args.book,
            branch_id=getattr(args, "branch_id", None) or "main",
            chapter_id=int(args.chapter),
            scene_a_id=int(args.scene_a),
            scene_b_id=getattr(args, "scene_b", None),
            bridge_plan_path=getattr(args, "bridge_plan", None),
        )
        result = apply_bridge_scene_insertion_action(workspace=workspace, request=request)
    except Exception as exc:
        sys.stderr.write(f"Apply bridge scene insertion failed: {exc}\n")
        return 1
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n")
    else:
        _print_execution_result(result)
    return _exit_code_for_result(result)


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
            branch_id=args.branch_id or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=getattr(args, "branch_id", None) or "main",
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
            branch_id=args.branch_id or "main",
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
    author_list = author_sub.add_parser("list", help="List BookForge author profiles.")
    author_list.add_argument("--json", action="store_true", help="Emit JSON.")
    author_list.set_defaults(func=_author_list)
    author_profile = author_sub.add_parser("profile", help="Show a rich author profile.")
    author_profile.add_argument("author_ref", help="Author reference, such as eldrik-vale or eldrik-vale/v2.")
    author_profile.add_argument("--version", help="Optional version override, such as v2.")
    author_profile.add_argument("--json", action="store_true", help="Emit JSON.")
    author_profile.set_defaults(func=_author_profile)
    author_generate = author_sub.add_parser("generate", help="Generate an author persona.")
    author_generate.add_argument("--name", help="Optional author persona name.")
    author_generate.add_argument(
        "--influences",
        help="Comma-separated influences, optional weights with colons.",
    )
    author_generate.add_argument("--prompt-file", help="Path to author prompt file.")
    author_generate.add_argument("--notes", help="Optional notes for author creation.")
    author_generate.set_defaults(func=_author_generate)
    author_create = author_sub.add_parser("create", help="Create a versioned author persona and emit an execution receipt.")
    author_create.add_argument("--name", help="Optional author persona name.")
    author_create.add_argument("--influences", help="Comma-separated influences, optional weights with colons.")
    author_create.add_argument("--prompt-text", help="Inline author brief.")
    author_create.add_argument("--prompt-file", help="Path to author prompt file.")
    author_create.add_argument("--notes", help="Optional notes for author creation.")
    author_create.add_argument("--json", action="store_true", help="Emit JSON execution receipt.")
    author_create.set_defaults(func=_author_create)
    author_refine = author_sub.add_parser("refine", help="Refine an existing author persona into a new version.")
    author_refine.add_argument("author_ref", help="Author reference, such as eldrik-vale or eldrik-vale/v2.")
    author_refine.add_argument("--instructions", help="Inline refinement instructions.")
    author_refine.add_argument("--prompt-file", help="Path to refinement instructions.")
    author_refine.add_argument("--notes", help="Optional notes for the new author version.")
    author_refine.add_argument("--json", action="store_true", help="Emit JSON execution receipt.")
    author_refine.set_defaults(func=_author_refine)

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

    capabilities_parser = subparsers.add_parser(
        "capabilities",
        help="Show BookForge engine capability projection for Nanda/tool consumers.",
    )
    capabilities_parser.add_argument("--book", help="Optional book id for observed execution-option enrichment.")
    capabilities_parser.add_argument("--json", action="store_true", help="Emit machine-readable capability projection JSON.")
    capabilities_parser.set_defaults(func=_capabilities)

    visual_parser = subparsers.add_parser("visual", help="Visual asset provider, readiness, and planning commands.")
    visual_sub = visual_parser.add_subparsers(dest="visual_command", required=True)
    visual_providers = visual_sub.add_parser("providers", help="List visual provider/model descriptors.")
    visual_providers.add_argument("--json", action="store_true", help="Emit JSON provider descriptors.")
    visual_providers.set_defaults(func=_visual_providers)
    visual_readiness = visual_sub.add_parser("readiness", help="Check visual action readiness for a provider/model.")
    visual_readiness.add_argument("--book", help="Optional book id. Required for generation actions.")
    visual_readiness.add_argument("--action", default="generate_background_layer", help="Visual action key.")
    visual_readiness.add_argument("--purpose", default="background_layer", help="Visual purpose.")
    visual_readiness.add_argument("--model", default=None, help="Provider model or alias. Defaults to nano-banana.")
    visual_readiness.add_argument("--reference-image-count", type=int, default=0, help="Number of reference images planned.")
    visual_readiness.add_argument("--transparent-background", action="store_true", help="Require alpha/transparent background support.")
    visual_readiness.add_argument("--ignore-credentials", action="store_true", help="Ignore provider API key checks.")
    visual_readiness.add_argument("--json", action="store_true", help="Emit JSON readiness.")
    visual_readiness.set_defaults(func=_visual_readiness)
    visual_plan = visual_sub.add_parser("plan", help="Create a provisional visual prompt plan.")
    visual_plan.add_argument("--book", required=True, help="Book id.")
    visual_plan.add_argument("--branch-id", help="Optional branch id; defaults to main.")
    visual_plan.add_argument("--purpose", default="background_layer", help="Visual purpose.")
    visual_plan.add_argument("--model", default=None, help="Provider model or alias. Defaults to nano-banana.")
    visual_plan.add_argument("--prompt-text", help="Inline visual brief.")
    visual_plan.add_argument("--prompt-file", help="Path to visual brief file.")
    visual_plan.add_argument("--style-profile", help="Optional style profile text/name.")
    visual_plan.add_argument("--layer-intent", help="Optional layer/composition intent.")
    visual_plan.add_argument("--negative-prompt", help="Optional negative prompt/avoid list.")
    visual_plan.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    visual_plan.set_defaults(func=_visual_plan)
    visual_generate = visual_sub.add_parser("generate", help="Generate a visual asset from a visual prompt plan.")
    visual_generate.add_argument("--book", required=True, help="Book id.")
    visual_generate.add_argument("--branch-id", help="Optional branch id; defaults to main.")
    visual_generate.add_argument("--prompt-plan", required=True, help="Path to a visual prompt plan JSON file.")
    visual_generate.add_argument("--model", default=None, help="Provider model or alias. Defaults to the model in the prompt plan.")
    visual_generate.add_argument("--allow-spend", action="store_true", help="Required to perform a live provider image call.")
    visual_generate.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    visual_generate.set_defaults(func=_visual_generate)
    visual_artifacts = visual_sub.add_parser("artifacts", help="List visual prompt plans and generated visual assets.")
    visual_artifacts.add_argument("--book", required=True, help="Book id.")
    visual_artifacts.add_argument("--branch-id", help="Optional branch id; defaults to main.")
    visual_artifacts.add_argument("--json", action="store_true", help="Emit JSON visual asset index.")
    visual_artifacts.set_defaults(func=_visual_artifacts)
    visual_asset = visual_sub.add_parser("asset", help="Inspect one generated visual asset manifest and source prompt plan.")
    visual_asset.add_argument("--book", required=True, help="Book id.")
    visual_asset.add_argument("--branch-id", help="Optional branch id; defaults to main.")
    visual_asset.add_argument("--asset-id", required=True, help="Visual asset id.")
    visual_asset.add_argument("--json", action="store_true", help="Emit JSON visual asset detail.")
    visual_asset.set_defaults(func=_visual_asset_detail)
    visual_prompt_plan = visual_sub.add_parser("prompt-plan", help="Inspect one visual prompt plan.")
    visual_prompt_plan.add_argument("--book", required=True, help="Book id.")
    visual_prompt_plan.add_argument("--branch-id", help="Optional branch id; defaults to main.")
    visual_prompt_plan.add_argument("--prompt-plan", required=True, help="Prompt plan id or path.")
    visual_prompt_plan.add_argument("--json", action="store_true", help="Emit JSON visual prompt plan detail.")
    visual_prompt_plan.set_defaults(func=_visual_prompt_plan_detail)

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

    workflow_starter_outline = workflow_sub.add_parser(
        "draft-starter-outline",
        help="Author starter/thin outline run artifacts from a created BookIntent.",
    )
    workflow_starter_outline.add_argument("--book", required=True, help="Book id.")
    workflow_starter_outline.add_argument("--run-id", help="Optional explicit starter outline run id.")
    workflow_starter_outline.add_argument("--chapters", type=int, help="Override target chapter count.")
    workflow_starter_outline.add_argument("--sections-per-chapter", type=int, help="Override sections per chapter.")
    workflow_starter_outline.add_argument("--scenes-per-section", type=int, help="Override scenes per section.")
    workflow_starter_outline.add_argument("--overwrite", action="store_true", help="Replace an existing starter outline run before workflow initialization.")
    workflow_starter_outline.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    workflow_starter_outline.set_defaults(func=_workflow_draft_starter_outline)

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
    workflow_legal.add_argument("--workflow-family", help="Optional workflow family scope, e.g. visual_assets.")
    workflow_legal.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_legal.add_argument("--section", type=int, help="Optional section scope.")
    workflow_legal.add_argument("--scene", type=int, help="Optional scene scope.")
    workflow_legal.add_argument("--json", action="store_true", help="Emit JSON execution options.")
    workflow_legal.set_defaults(func=_workflow_legal_actions)

    workflow_branch_inventory = workflow_sub.add_parser(
        "branch-inventory",
        help="Show branch and fork-group inventory for a book.",
    )
    workflow_branch_inventory.add_argument("--book", required=True, help="Book id.")
    workflow_branch_inventory.add_argument("--json", action="store_true", help="Emit JSON.")
    workflow_branch_inventory.set_defaults(func=_workflow_branch_inventory)

    workflow_branch_detail = workflow_sub.add_parser(
        "branch-detail",
        help="Show one branch workbench view with legal actions, optional reader context, and scene readiness.",
    )
    workflow_branch_detail.add_argument("--book", required=True, help="Book id.")
    workflow_branch_detail.add_argument("--branch-id", required=True, help="Branch id to inspect. Use main for canonical state.")
    workflow_branch_detail.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_branch_detail.add_argument("--section", type=int, help="Optional section scope.")
    workflow_branch_detail.add_argument("--scene", type=int, help="Optional scene scope.")
    workflow_branch_detail.add_argument("--max-text-chars", type=int, default=0, help="Maximum selected reader text to include; 0 omits text.")
    workflow_branch_detail.add_argument("--json", action="store_true", help="Emit JSON.")
    workflow_branch_detail.set_defaults(func=_workflow_branch_detail)

    workflow_branch_artifact_index = workflow_sub.add_parser(
        "branch-artifact-index",
        help="Show a read-only artifact index for main or one derived branch.",
    )
    workflow_branch_artifact_index.add_argument("--book", required=True, help="Book id.")
    workflow_branch_artifact_index.add_argument("--branch-id", default="main", help="Branch id to inspect; defaults to main.")
    workflow_branch_artifact_index.add_argument("--limit", type=int, default=500, help="Maximum artifact records to include.")
    workflow_branch_artifact_index.add_argument("--json", action="store_true", help="Emit JSON.")
    workflow_branch_artifact_index.set_defaults(func=_workflow_branch_artifact_index)

    workflow_branch_diff_summary = workflow_sub.add_parser(
        "branch-diff-summary",
        help="Show a read-only branch-vs-main artifact diff summary.",
    )
    workflow_branch_diff_summary.add_argument("--book", required=True, help="Book id.")
    workflow_branch_diff_summary.add_argument("--branch-id", required=True, help="Derived branch id to compare.")
    workflow_branch_diff_summary.add_argument("--against", default="main", help="Comparison target; currently main.")
    workflow_branch_diff_summary.add_argument("--limit", type=int, default=500, help="Maximum artifact records to inspect.")
    workflow_branch_diff_summary.add_argument("--json", action="store_true", help="Emit JSON.")
    workflow_branch_diff_summary.set_defaults(func=_workflow_branch_diff_summary)

    workflow_lineage_audit = workflow_sub.add_parser(
        "outline-lineage-audit",
        help="Show read-only outline lineage audit evidence for a book.",
    )
    workflow_lineage_audit.add_argument("--book", required=True, help="Book id.")
    workflow_lineage_audit.add_argument("--branch-id", default="main", help="Optional branch scope; defaults to main.")
    workflow_lineage_audit.add_argument("--json", action="store_true", help="Emit the full audit as JSON.")
    workflow_lineage_audit.set_defaults(func=_workflow_outline_lineage_audit)

    workflow_lineage_matrix = workflow_sub.add_parser(
        "section-lineage-matrix",
        help="Show section-level outline lineage comparisons.",
    )
    workflow_lineage_matrix.add_argument("--book", required=True, help="Book id.")
    workflow_lineage_matrix.add_argument("--branch-id", default="main", help="Optional branch scope; defaults to main.")
    workflow_lineage_matrix.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_lineage_matrix.add_argument("--section", type=int, help="Optional section scope.")
    workflow_lineage_matrix.add_argument("--json", action="store_true", help="Emit matrix rows as JSON.")
    workflow_lineage_matrix.set_defaults(func=_workflow_section_lineage_matrix)

    workflow_stale_artifacts = workflow_sub.add_parser(
        "stale-outline-artifacts",
        help="Show outline artifacts that need explicit lineage treatment.",
    )
    workflow_stale_artifacts.add_argument("--book", required=True, help="Book id.")
    workflow_stale_artifacts.add_argument("--branch-id", default="main", help="Optional branch scope; defaults to main.")
    workflow_stale_artifacts.add_argument("--json", action="store_true", help="Emit artifact inventory as JSON.")
    workflow_stale_artifacts.set_defaults(func=_workflow_stale_outline_artifacts)

    workflow_repair_candidates = workflow_sub.add_parser(
        "outline-repair-candidates",
        help="Show non-mutating outline recovery candidates for a contaminated book.",
    )
    workflow_repair_candidates.add_argument("--book", required=True, help="Book id.")
    workflow_repair_candidates.add_argument("--branch-id", default="main", help="Optional branch scope; defaults to main.")
    workflow_repair_candidates.add_argument("--json", action="store_true", help="Emit repair candidates as JSON.")
    workflow_repair_candidates.set_defaults(func=_workflow_outline_repair_candidates)

    workflow_recovery_anchor_candidates = workflow_sub.add_parser(
        "recovery-anchor-candidates",
        help="Show trusted timeline anchor candidates for recovery planning.",
    )
    workflow_recovery_anchor_candidates.add_argument("--book", required=True, help="Book id.")
    workflow_recovery_anchor_candidates.add_argument("--branch-id", default="main", help="Optional branch scope; defaults to main.")
    workflow_recovery_anchor_candidates.add_argument("--json", action="store_true", help="Emit JSON.")
    workflow_recovery_anchor_candidates.set_defaults(func=_workflow_recovery_anchor_candidates)

    workflow_recovery_plan_preview = workflow_sub.add_parser(
        "recovery-plan-preview",
        help="Preview the ordered recovery plan after anchor selection or auto-selection.",
    )
    workflow_recovery_plan_preview.add_argument("--book", required=True, help="Book id.")
    workflow_recovery_plan_preview.add_argument("--anchor-type", help="Optional selected anchor type.")
    workflow_recovery_plan_preview.add_argument("--source-run-id", help="Optional source run id for source-run anchors.")
    workflow_recovery_plan_preview.add_argument("--branch-id", help="Optional planned recovery branch id.")
    workflow_recovery_plan_preview.add_argument("--salvage-policy", default="none", choices=["none", "reference_only", "explicit_reuse_required"], help="Salvage policy for contaminated prose.")
    workflow_recovery_plan_preview.add_argument("--json", action="store_true", help="Emit JSON.")
    workflow_recovery_plan_preview.set_defaults(func=_workflow_recovery_plan_preview)

    workflow_create_recovery_branch = workflow_sub.add_parser(
        "create-recovery-branch",
        help="Create a derived recovery branch from contaminated main state using an explicit timeline anchor.",
    )
    workflow_create_recovery_branch.add_argument("--book", required=True, help="Book id.")
    workflow_create_recovery_branch.add_argument("--branch-id", help="Optional explicit recovery branch id.")
    workflow_create_recovery_branch.add_argument(
        "--anchor-type",
        required=True,
        choices=["declared_source_run", "latest_outline_run", "frozen_chapter_projection", "manual_hybrid", "shelf"],
        help="Recovery anchor type selected by the author/operator.",
    )
    workflow_create_recovery_branch.add_argument("--source-run-id", help="Source outline run id for source-run anchors.")
    workflow_create_recovery_branch.add_argument(
        "--affected-scope",
        action="append",
        help="Affected scope as chapter, chapter:section, or chapter:section:scene. Repeatable; defaults to lineage audit affected sections.",
    )
    workflow_create_recovery_branch.add_argument(
        "--salvage-policy",
        default="none",
        choices=["none", "reference_only", "explicit_reuse_required"],
        help="How existing polluted prose may be treated during recovery.",
    )
    workflow_create_recovery_branch.set_defaults(func=_workflow_create_recovery_branch)

    workflow_recovery_readiness = workflow_sub.add_parser(
        "recovery-readiness",
        help="Show recovery plan readiness for a derived recovery branch.",
    )
    workflow_recovery_readiness.add_argument("--book", required=True, help="Book id.")
    workflow_recovery_readiness.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_recovery_readiness.add_argument("--impact-report-ref", help="Optional Nanda impact report reference.")
    workflow_recovery_readiness.add_argument("--json", action="store_true", help="Emit readiness as JSON.")
    workflow_recovery_readiness.set_defaults(func=_workflow_recovery_readiness)

    workflow_recovery_health = workflow_sub.add_parser(
        "recovery-health",
        help="Show recovery branch health, blockers, warnings, and receipt sequence.",
    )
    workflow_recovery_health.add_argument("--book", required=True, help="Book id.")
    workflow_recovery_health.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_recovery_health.add_argument("--json", action="store_true", help="Emit health as JSON.")
    workflow_recovery_health.set_defaults(func=_workflow_recovery_health)

    workflow_scope_invalidation_preview = workflow_sub.add_parser(
        "scope-invalidation-preview",
        help="Preview branch-local output artifacts that invalidate-scope-outputs would quarantine.",
    )
    workflow_scope_invalidation_preview.add_argument("--book", required=True, help="Book id.")
    workflow_scope_invalidation_preview.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_scope_invalidation_preview.add_argument("--json", action="store_true", help="Emit preview as JSON.")
    workflow_scope_invalidation_preview.set_defaults(func=_workflow_scope_invalidation_preview)

    workflow_state_rebuild_preview = workflow_sub.add_parser(
        "state-rebuild-preview",
        help="Preview branch-local state and projection artifacts that rebuild-state-scope would quarantine.",
    )
    workflow_state_rebuild_preview.add_argument("--book", required=True, help="Book id.")
    workflow_state_rebuild_preview.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_state_rebuild_preview.add_argument("--json", action="store_true", help="Emit preview as JSON.")
    workflow_state_rebuild_preview.set_defaults(func=_workflow_state_rebuild_preview)

    workflow_recovery_blast_radius = workflow_sub.add_parser(
        "recovery-blast-radius",
        help="Show categorized artifact impacts for a recovery branch.",
    )
    workflow_recovery_blast_radius.add_argument("--book", required=True, help="Book id.")
    workflow_recovery_blast_radius.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_recovery_blast_radius.add_argument("--json", action="store_true", help="Emit blast-radius preview as JSON.")
    workflow_recovery_blast_radius.set_defaults(func=_workflow_recovery_blast_radius)

    workflow_recovery_semantic_readiness = workflow_sub.add_parser(
        "recovery-semantic-readiness",
        help="Show whether a recovery branch is ready for diagnostic semantic review.",
    )
    workflow_recovery_semantic_readiness.add_argument("--book", required=True, help="Book id.")
    workflow_recovery_semantic_readiness.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_recovery_semantic_readiness.add_argument("--json", action="store_true", help="Emit semantic readiness as JSON.")
    workflow_recovery_semantic_readiness.set_defaults(func=_workflow_recovery_semantic_readiness)

    workflow_recovery_semantic_review = workflow_sub.add_parser(
        "recovery-semantic-review",
        help="Show the current diagnostic semantic review artifact, if present.",
    )
    workflow_recovery_semantic_review.add_argument("--book", required=True, help="Book id.")
    workflow_recovery_semantic_review.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_recovery_semantic_review.add_argument("--json", action="store_true", help="Emit semantic review as JSON.")
    workflow_recovery_semantic_review.set_defaults(func=_workflow_recovery_semantic_review)

    workflow_downstream_dependency_review = workflow_sub.add_parser(
        "downstream-dependency-review",
        help="Show the current diagnostic downstream dependency review artifact, if present.",
    )
    workflow_downstream_dependency_review.add_argument("--book", required=True, help="Book id.")
    workflow_downstream_dependency_review.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_downstream_dependency_review.add_argument("--json", action="store_true", help="Emit downstream review as JSON.")
    workflow_downstream_dependency_review.set_defaults(func=_workflow_downstream_dependency_review)

    workflow_quarantine_artifacts = workflow_sub.add_parser(
        "quarantine-artifacts",
        help="Move stale or invalid recovery-scope artifacts out of the active branch snapshot.",
    )
    workflow_quarantine_artifacts.add_argument("--book", required=True, help="Book id.")
    workflow_quarantine_artifacts.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_quarantine_artifacts.set_defaults(func=_workflow_quarantine_artifacts)

    workflow_normalize_outline_scope = workflow_sub.add_parser(
        "normalize-outline-scope",
        help="Replace affected branch outline scopes from the selected recovery anchor and rebuild projections.",
    )
    workflow_normalize_outline_scope.add_argument("--book", required=True, help="Book id.")
    workflow_normalize_outline_scope.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_normalize_outline_scope.set_defaults(func=_workflow_normalize_outline_scope)

    workflow_invalidate_scope_outputs = workflow_sub.add_parser(
        "invalidate-scope-outputs",
        help="Quarantine prose and generated artifacts for affected branch scopes before redraft.",
    )
    workflow_invalidate_scope_outputs.add_argument("--book", required=True, help="Book id.")
    workflow_invalidate_scope_outputs.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_invalidate_scope_outputs.set_defaults(func=_workflow_invalidate_scope_outputs)

    workflow_rebuild_state_scope = workflow_sub.add_parser(
        "rebuild-state-scope",
        help="Rebuild branch-local state/projection baselines from the normalized outline before validation.",
    )
    workflow_rebuild_state_scope.add_argument("--book", required=True, help="Book id.")
    workflow_rebuild_state_scope.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_rebuild_state_scope.set_defaults(func=_workflow_rebuild_state_scope)

    workflow_redraft_scope = workflow_sub.add_parser(
        "redraft-scope",
        help="Redraft affected recovery scopes inside the branch using scoped section writing.",
    )
    workflow_redraft_scope.add_argument("--book", required=True, help="Book id.")
    workflow_redraft_scope.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_redraft_scope.set_defaults(func=_workflow_redraft_scope)

    workflow_validate_recovery_branch = workflow_sub.add_parser(
        "validate-recovery-branch",
        help="Validate a recovery branch before it may promote to main.",
    )
    workflow_validate_recovery_branch.add_argument("--book", required=True, help="Book id.")
    workflow_validate_recovery_branch.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_validate_recovery_branch.set_defaults(func=_workflow_validate_recovery_branch)

    workflow_review_recovery_semantics = workflow_sub.add_parser(
        "review-recovery-semantics",
        help="Emit a diagnostic semantic review artifact for a structurally recovered branch.",
    )
    workflow_review_recovery_semantics.add_argument("--book", required=True, help="Book id.")
    workflow_review_recovery_semantics.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_review_recovery_semantics.set_defaults(func=_workflow_review_recovery_semantics)

    workflow_review_downstream_dependencies = workflow_sub.add_parser(
        "review-downstream-dependencies",
        help="Emit a diagnostic downstream dependency review artifact for a recovery branch.",
    )
    workflow_review_downstream_dependencies.add_argument("--book", required=True, help="Book id.")
    workflow_review_downstream_dependencies.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_review_downstream_dependencies.set_defaults(func=_workflow_review_downstream_dependencies)

    workflow_promote_recovery_branch = workflow_sub.add_parser(
        "promote-recovery-branch",
        help="Promote a healthy recovery branch to main, including recorded removals.",
    )
    workflow_promote_recovery_branch.add_argument("--book", required=True, help="Book id.")
    workflow_promote_recovery_branch.add_argument("--branch-id", required=True, help="Recovery branch id.")
    workflow_promote_recovery_branch.set_defaults(func=_workflow_promote_recovery_branch)

    workflow_create_branch = workflow_sub.add_parser(
        "create-branch",
        help="Create a derived branch from main or another branch snapshot.",
    )
    workflow_create_branch.add_argument("--book", required=True, help="Book id.")
    workflow_create_branch.add_argument("--branch-id", help="Optional explicit branch id.")
    workflow_create_branch.add_argument("--parent-branch-id", default="main", help="Parent branch scope; defaults to main.")
    workflow_create_branch.add_argument("--fork-group-id", help="Optional fork group for sibling branches.")
    workflow_create_branch.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_create_branch.add_argument("--section", type=int, help="Optional section scope.")
    workflow_create_branch.add_argument("--branch-role", default="rerun", help="Branch role label, such as rerun, chapter, section, scene, or writer.")
    workflow_create_branch.add_argument("--merge-operation", default="promotion", help="Merge operation label; defaults to promotion.")
    workflow_create_branch.set_defaults(func=_workflow_create_branch)

    workflow_create_assembly_branch = workflow_sub.add_parser(
        "create-assembly-branch",
        help="Create an off-parent assembly branch for a fork group.",
    )
    workflow_create_assembly_branch.add_argument("--book", required=True, help="Book id.")
    workflow_create_assembly_branch.add_argument("--fork-group-id", required=True, help="Fork group id to assemble.")
    workflow_create_assembly_branch.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_create_assembly_branch.add_argument("--branch-id", help="Optional explicit assembly branch id.")
    workflow_create_assembly_branch.set_defaults(func=_workflow_create_assembly_branch)

    workflow_discard_branch = workflow_sub.add_parser(
        "discard-branch",
        help="Discard a derived branch without mutating its parent or main.",
    )
    workflow_discard_branch.add_argument("--book", required=True, help="Book id.")
    workflow_discard_branch.add_argument("--branch-id", required=True, help="Derived branch id to discard.")
    workflow_discard_branch.add_argument("--reason", help="Optional discard reason.")
    workflow_discard_branch.set_defaults(func=_workflow_discard_branch)

    workflow_promote_branch = workflow_sub.add_parser(
        "promote-branch",
        help="Promote a branch to main or to an explicit parent branch.",
    )
    workflow_promote_branch.add_argument("--book", required=True, help="Book id.")
    workflow_promote_branch.add_argument("--branch-id", required=True, help="Source branch id to promote.")
    workflow_promote_branch.add_argument("--target-branch-id", default="main", help="Target branch id; defaults to main.")
    workflow_promote_branch.set_defaults(func=_workflow_promote_branch)

    workflow_rebase_branch = workflow_sub.add_parser(
        "rebase-branch",
        help="Create a refreshed child branch from the current parent snapshot and discard the old branch.",
    )
    workflow_rebase_branch.add_argument("--book", required=True, help="Book id.")
    workflow_rebase_branch.add_argument("--branch-id", required=True, help="Derived branch id to rebase.")
    workflow_rebase_branch.add_argument("--new-branch-id", help="Optional explicit id for the refreshed child branch.")
    workflow_rebase_branch.set_defaults(func=_workflow_rebase_branch)

    workflow_validate_assembly_branch = workflow_sub.add_parser(
        "validate-assembly-branch",
        help="Run deterministic staging validation for an assembly branch.",
    )
    workflow_validate_assembly_branch.add_argument("--book", required=True, help="Book id.")
    workflow_validate_assembly_branch.add_argument("--branch-id", required=True, help="Assembly branch id.")
    workflow_validate_assembly_branch.set_defaults(func=_workflow_validate_assembly_branch)

    workflow_record_assembly_validation = workflow_sub.add_parser(
        "record-assembly-validation",
        help="Record validation status for an assembly branch before promotion.",
    )
    workflow_record_assembly_validation.add_argument("--book", required=True, help="Book id.")
    workflow_record_assembly_validation.add_argument("--branch-id", required=True, help="Assembly branch id.")
    validation_group = workflow_record_assembly_validation.add_mutually_exclusive_group(required=True)
    validation_group.add_argument("--passed", dest="passed", action="store_true", help="Mark assembly validation as passed.")
    validation_group.add_argument("--failed", dest="passed", action="store_false", help="Mark assembly validation as failed.")
    workflow_record_assembly_validation.add_argument("--message", help="Optional validation message.")
    workflow_record_assembly_validation.set_defaults(func=_workflow_record_assembly_validation)

    workflow_scene_readiness = workflow_sub.add_parser(
        "scene-readiness",
        help="Show truthful scene-phase readiness for one scene on the current main-branch cursor path.",
    )
    workflow_scene_readiness.add_argument("--book", required=True, help="Book id.")
    workflow_scene_readiness.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_scene_readiness.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_scene_readiness.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_scene_readiness.add_argument("--section", type=int, help="Optional section id.")
    workflow_scene_readiness.set_defaults(func=_workflow_scene_readiness)

    workflow_next_writing_target = workflow_sub.add_parser(
        "next-writing-target",
        help="Show the next query-only writing target for a book or branch without running any mutation.",
    )
    workflow_next_writing_target.add_argument("--book", required=True, help="Book id.")
    workflow_next_writing_target.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_next_writing_target.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_next_writing_target.add_argument("--section", type=int, help="Optional section scope.")
    workflow_next_writing_target.add_argument("--scene", type=int, help="Optional scene scope.")
    workflow_next_writing_target.add_argument("--json", action="store_true", help="Emit JSON next-writing-target status.")
    workflow_next_writing_target.set_defaults(func=_workflow_next_writing_target)

    workflow_writing_bootstrap = workflow_sub.add_parser(
        "writing-bootstrap",
        help="Show the read-only setup-to-writing status for a created book.",
    )
    workflow_writing_bootstrap.add_argument("--book", required=True, help="Book id.")
    workflow_writing_bootstrap.add_argument("--branch-id", help="Optional branch scope; when omitted BookForge selects a suitable derived branch if one exists.")
    workflow_writing_bootstrap.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_writing_bootstrap.add_argument("--section", type=int, help="Optional section scope.")
    workflow_writing_bootstrap.add_argument("--scene", type=int, help="Optional scene scope.")
    workflow_writing_bootstrap.add_argument("--json", action="store_true", help="Emit JSON writing bootstrap status.")
    workflow_writing_bootstrap.set_defaults(func=_workflow_writing_bootstrap)

    workflow_writing_gates = workflow_sub.add_parser(
        "writing-gates",
        help="Show read-only scene, section, chapter, book, and export writing gates.",
    )
    workflow_writing_gates.add_argument("--book", required=True, help="Book id.")
    workflow_writing_gates.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_writing_gates.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_writing_gates.add_argument("--section", type=int, help="Optional section scope.")
    workflow_writing_gates.add_argument("--scene", type=int, help="Optional scene scope.")
    workflow_writing_gates.add_argument("--json", action="store_true", help="Emit JSON writing gate status.")
    workflow_writing_gates.set_defaults(func=_workflow_writing_gates)

    workflow_author_loop = workflow_sub.add_parser(
        "author-loop-envelopes",
        help="Show read-only author work loop envelope options for the selected scope.",
    )
    workflow_author_loop.add_argument("--book", required=True, help="Book id.")
    workflow_author_loop.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_author_loop.add_argument("--chapter", type=int, help="Optional chapter scope.")
    workflow_author_loop.add_argument("--section", type=int, help="Optional section scope.")
    workflow_author_loop.add_argument("--scene", type=int, help="Optional scene scope.")
    workflow_author_loop.add_argument("--json", action="store_true", help="Emit JSON author loop envelope options.")
    workflow_author_loop.set_defaults(func=_workflow_author_loop_envelopes)

    workflow_chapter_seams = workflow_sub.add_parser(
        "chapter-seam-queue",
        help="Show read-only adjacent scene-pair seam work for a chapter.",
    )
    workflow_chapter_seams.add_argument("--book", required=True, help="Book id.")
    workflow_chapter_seams.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_chapter_seams.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_chapter_seams.add_argument("--json", action="store_true", help="Emit JSON chapter seam queue.")
    workflow_chapter_seams.set_defaults(func=_workflow_chapter_seam_queue)

    workflow_scene_pair_seam = workflow_sub.add_parser(
        "scene-pair-seam-detail",
        help="Show read-only detail for one adjacent scene-pair seam report/readiness state.",
    )
    workflow_scene_pair_seam.add_argument("--book", required=True, help="Book id.")
    workflow_scene_pair_seam.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_scene_pair_seam.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_scene_pair_seam.add_argument("--scene-a", required=True, type=int, help="Scene A id.")
    workflow_scene_pair_seam.add_argument("--scene-b", required=True, type=int, help="Scene B id.")
    workflow_scene_pair_seam.add_argument("--summary-only", action="store_true", help="Omit full report payload from JSON output.")
    workflow_scene_pair_seam.add_argument("--json", action="store_true", help="Emit JSON scene-pair seam detail.")
    workflow_scene_pair_seam.set_defaults(func=_workflow_scene_pair_seam_detail)

    workflow_plan_scene = workflow_sub.add_parser(
        "plan-scene",
        help="Generate a provisional scene card for one scene without auto-running downstream phases.",
    )
    workflow_plan_scene.add_argument("--book", required=True, help="Book id.")
    workflow_plan_scene.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_plan_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_plan_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_plan_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_plan_scene.set_defaults(func=_workflow_plan_scene)

    workflow_preflight_scene = workflow_sub.add_parser(
        "preflight-scene-state",
        help="Generate a provisional preflight state patch for one scene without applying it.",
    )
    workflow_preflight_scene.add_argument("--book", required=True, help="Book id.")
    workflow_preflight_scene.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_preflight_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_preflight_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_preflight_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_preflight_scene.set_defaults(func=_workflow_preflight_scene_state)

    workflow_continuity_pack = workflow_sub.add_parser(
        "generate-continuity-pack",
        help="Generate a derived continuity pack for one scene without writing prose or mutating canonical state.",
    )
    workflow_continuity_pack.add_argument("--book", required=True, help="Book id.")
    workflow_continuity_pack.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_continuity_pack.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_continuity_pack.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_continuity_pack.add_argument("--section", type=int, help="Optional section id.")
    workflow_continuity_pack.set_defaults(func=_workflow_generate_continuity_pack)

    workflow_state_repair_scene = workflow_sub.add_parser(
        "state-repair-scene-patch",
        help="Generate a provisional corrected state patch for one scene without linting, repairing prose, or committing.",
    )
    workflow_state_repair_scene.add_argument("--book", required=True, help="Book id.")
    workflow_state_repair_scene.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_state_repair_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_state_repair_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_state_repair_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_state_repair_scene.set_defaults(func=_workflow_state_repair_scene_patch)

    workflow_lint_scene = workflow_sub.add_parser(
        "lint-scene-prose",
        help="Generate a provisional lint report for one scene without repairing prose or committing.",
    )
    workflow_lint_scene.add_argument("--book", required=True, help="Book id.")
    workflow_lint_scene.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_lint_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_lint_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_lint_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_lint_scene.set_defaults(func=_workflow_lint_scene_prose)

    workflow_repair_scene = workflow_sub.add_parser(
        "repair-scene-prose",
        help="Generate provisional repaired prose and patch artifacts for one scene without rerunning state repair, lint, or commit.",
    )
    workflow_repair_scene.add_argument("--book", required=True, help="Book id.")
    workflow_repair_scene.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_repair_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_repair_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_repair_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_repair_scene.set_defaults(func=_workflow_repair_scene_prose)

    workflow_apply_scene_commit = workflow_sub.add_parser(
        "apply-scene-commit",
        help="Commit the active scene's latest passing provisional baseline into canonical state and authoritative scene artifacts.",
    )
    workflow_apply_scene_commit.add_argument("--book", required=True, help="Book id.")
    workflow_apply_scene_commit.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_apply_scene_commit.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_apply_scene_commit.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_apply_scene_commit.add_argument("--section", type=int, help="Optional section id.")
    workflow_apply_scene_commit.set_defaults(func=_workflow_apply_scene_commit)

    workflow_continue_scene = workflow_sub.add_parser(
        "continue-scene",
        help="Execute exactly one recommended next scene-phase action and return a wrapper receipt.",
    )
    workflow_continue_scene.add_argument("--book", required=True, help="Book id.")
    workflow_continue_scene.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_continue_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_continue_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_continue_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_continue_scene.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    workflow_continue_scene.set_defaults(func=_workflow_continue_scene)

    workflow_align_pair = workflow_sub.add_parser(
        "align-scene-pair-seam",
        help="Re-author the seam between two adjacent scenes inside a branch.",
    )
    workflow_align_pair.add_argument("--book", required=True, help="Book id.")
    workflow_align_pair.add_argument("--branch-id", required=True, help="Derived branch id.")
    workflow_align_pair.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_align_pair.add_argument("--scene-a", required=True, type=int, help="Scene A id.")
    workflow_align_pair.add_argument("--scene-b", type=int, help="Optional scene B id; defaults to outline-adjacent next scene.")
    workflow_align_pair.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    workflow_align_pair.set_defaults(func=_workflow_align_scene_pair_seam)

    workflow_bridge_plan = workflow_sub.add_parser(
        "plan-bridge-scene-insertion",
        help="Create a provisional branch-local bridge scene insertion plan.",
    )
    workflow_bridge_plan.add_argument("--book", required=True, help="Book id.")
    workflow_bridge_plan.add_argument("--branch-id", required=True, help="Derived branch id.")
    workflow_bridge_plan.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_bridge_plan.add_argument("--scene-a", required=True, type=int, help="Scene before the proposed bridge.")
    workflow_bridge_plan.add_argument("--scene-b", type=int, help="Optional scene after the proposed bridge; defaults to outline-adjacent next scene.")
    workflow_bridge_plan.add_argument("--objective", help="Optional bridge objective.")
    workflow_bridge_plan.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    workflow_bridge_plan.set_defaults(func=_workflow_plan_bridge_scene_insertion)

    workflow_bridge_apply = workflow_sub.add_parser(
        "apply-bridge-scene-insertion",
        help="Apply a planned bridge scene insertion inside a branch.",
    )
    workflow_bridge_apply.add_argument("--book", required=True, help="Book id.")
    workflow_bridge_apply.add_argument("--branch-id", required=True, help="Derived branch id.")
    workflow_bridge_apply.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_bridge_apply.add_argument("--scene-a", required=True, type=int, help="Scene before the bridge.")
    workflow_bridge_apply.add_argument("--scene-b", type=int, help="Optional scene after the bridge; defaults to outline-adjacent next scene.")
    workflow_bridge_apply.add_argument("--bridge-plan", help="Optional explicit bridge plan path relative to the branch book root.")
    workflow_bridge_apply.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    workflow_bridge_apply.set_defaults(func=_workflow_apply_bridge_scene_insertion)

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
    workflow_write.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
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
    workflow_write_scene.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_write_scene.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_write_scene.add_argument("--scene", required=True, type=int, help="Scene id.")
    workflow_write_scene.add_argument("--section", type=int, help="Optional section id.")
    workflow_write_scene.set_defaults(func=_workflow_write_scene_prose)

    workflow_lock = workflow_sub.add_parser(
        "lock-section",
        help="Lock one frozen section after prose and meta artifacts exist for all section scenes.",
    )
    workflow_lock.add_argument("--book", required=True, help="Book id.")
    workflow_lock.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_lock.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_lock.add_argument("--section", required=True, type=int, help="Section id.")
    workflow_lock.set_defaults(func=_workflow_lock_section)

    workflow_finalize = workflow_sub.add_parser(
        "finalize-chapter",
        help="Run pairwise LLM seam repair and chapter finalization for a chapter whose sections are already locked.",
    )
    workflow_finalize.add_argument("--book", required=True, help="Book id.")
    workflow_finalize.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    workflow_finalize.add_argument("--chapter", required=True, type=int, help="Chapter id.")
    workflow_finalize.set_defaults(func=_workflow_finalize_chapter)

    workflow_seam = workflow_sub.add_parser(
        "seam-chapter",
        help="Run pairwise LLM seam repair for a fully written chapter and emit original/fixed/final chapter artifacts.",
    )
    workflow_seam.add_argument("--book", required=True, help="Book id.")
    workflow_seam.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
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

    book_list = book_sub.add_parser("list", help="List BookForge book cards.")
    book_list.add_argument("--json", action="store_true", help="Emit JSON.")
    book_list.set_defaults(func=_book_list)

    book_reader = book_sub.add_parser("reader", help="Read canonical BookForge prose by book/chapter/scene.")
    book_reader.add_argument("--book", required=True, help="Book id.")
    book_reader.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    book_reader.add_argument("--chapter", type=int, help="Optional chapter selection.")
    book_reader.add_argument("--scene", type=int, help="Optional scene selection.")
    book_reader.add_argument("--max-text-chars", type=int, default=24_000, help="Maximum selected prose characters.")
    book_reader.add_argument("--json", action="store_true", help="Emit JSON.")
    book_reader.set_defaults(func=_book_reader)

    book_reader_anchor = book_sub.add_parser("reader-anchor", help="Create a mutation-safe reader/prose anchor by chapter/scene/span.")
    book_reader_anchor.add_argument("--book", required=True, help="Book id.")
    book_reader_anchor.add_argument("--branch-id", help="Optional branch scope; defaults to main.")
    book_reader_anchor.add_argument("--chapter", type=int, required=True, help="Chapter selection.")
    book_reader_anchor.add_argument("--scene", type=int, help="Optional scene selection. Omit for chapter-level inspect-only anchor.")
    book_reader_anchor.add_argument("--start-offset", type=int, help="Selected span start offset. Defaults to start of artifact.")
    book_reader_anchor.add_argument("--end-offset", type=int, help="Selected span end offset. Defaults to end of artifact.")
    book_reader_anchor.add_argument("--max-text-chars", type=int, default=24_000, help="Maximum selected prose characters.")
    book_reader_anchor.add_argument("--json", action="store_true", help="Emit JSON.")
    book_reader_anchor.set_defaults(func=_book_reader_anchor)

    book_intent = book_sub.add_parser("intent", help="Book intent and canonical create-book commands.")
    book_intent_sub = book_intent.add_subparsers(dest="book_intent_command", required=True)
    book_intent_list = book_intent_sub.add_parser("list", help="List drafted, approved, and created book intents.")
    book_intent_list.add_argument("--status", choices=["draft", "approved", "created", "shelved"], help="Optional status filter.")
    book_intent_list.add_argument("--json", action="store_true", help="Emit JSON.")
    book_intent_list.set_defaults(func=_book_intent_list)
    book_intent_show = book_intent_sub.add_parser("show", help="Show one book intent.")
    book_intent_show.add_argument("--intent", required=True, help="Intent id or path.")
    book_intent_show.add_argument("--json", action="store_true", help="Emit JSON.")
    book_intent_show.set_defaults(func=_book_intent_show)
    book_intent_draft = book_intent_sub.add_parser("draft", help="Create a provisional BookIntent from an author-only seed.")
    book_intent_draft.add_argument("--title", required=True, help="Book title.")
    book_intent_draft.add_argument("--book-id", help="Optional proposed canonical book id.")
    book_intent_draft.add_argument("--author-ref", required=True, help="Author ref such as eldrik-vale/v1.")
    book_intent_draft.add_argument("--genre", required=True, help="Comma-separated genre list.")
    book_intent_draft.add_argument("--seed-text", help="Inline book seed text.")
    book_intent_draft.add_argument("--seed-file", help="Path to book seed text.")
    book_intent_draft.add_argument("--series-id", help="Optional series id.")
    book_intent_draft.add_argument("--target", action="append", default=[], help="Target key=value. May be repeated.")
    book_intent_draft.add_argument("--short-synopsis", help="Short synopsis.")
    book_intent_draft.add_argument("--long-synopsis", help="Long synopsis.")
    book_intent_draft.add_argument("--reader-promise", help="Reader promise.")
    book_intent_draft.add_argument("--central-conflict", help="Central conflict.")
    book_intent_draft.add_argument("--tone", help="Tone/voice promise.")
    book_intent_draft.add_argument("--must-have", action="append", default=[], help="Required constraint. May be repeated.")
    book_intent_draft.add_argument("--must-not", action="append", default=[], help="Forbidden constraint. May be repeated.")
    book_intent_draft.add_argument("--source-ref", help="Optional upstream seed/source ref.")
    book_intent_draft.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    book_intent_draft.set_defaults(func=_book_intent_draft)
    book_intent_approve = book_intent_sub.add_parser("approve", help="Approve a drafted BookIntent.")
    book_intent_approve.add_argument("--intent", required=True, help="Intent id or path.")
    book_intent_approve.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    book_intent_approve.set_defaults(func=_book_intent_approve)
    book_intent_create = book_intent_sub.add_parser("create", help="Create a canonical book workspace from an approved BookIntent.")
    book_intent_create.add_argument("--intent", required=True, help="Intent id or path.")
    book_intent_create.add_argument("--book-id", help="Override canonical book id.")
    book_intent_create.add_argument("--series-id", help="Override series id.")
    book_intent_create.add_argument("--json", action="store_true", help="Emit JSON execution result.")
    book_intent_create.set_defaults(func=_book_intent_create)

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
