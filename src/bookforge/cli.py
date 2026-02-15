import argparse
from pathlib import Path
import sys

from bookforge.author import generate_author
from bookforge.outline import (
    generate_outline,
    load_latest_outline_pipeline_report,
    format_outline_pipeline_summary,
    reset_outline_workspace_detailed,
)
from bookforge.runner import run_loop
from bookforge.characters import generate_characters
from bookforge.workspace import init_book_workspace, parse_genre, parse_targets, reset_book_workspace_detailed, update_book_templates


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
    transition_hints_file = Path(args.transition_hints_file) if getattr(args, "transition_hints_file", None) else None
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
            strict_transition_bridges=bool(getattr(args, "strict_transition_bridges", False)),
            strict_location_identity=bool(getattr(args, "strict_location_identity", True)),
            transition_insert_budget_per_chapter=int(getattr(args, "transition_insert_budget_per_chapter", 2) or 2),
            allow_transition_scene_insertions=bool(getattr(args, "allow_transition_scene_insertions", True)),
            force_rerun_with_draft=bool(getattr(args, "force_rerun_with_draft", False)),
            exact_scene_count=bool(getattr(args, "exact_scene_count", False)),
            scene_count_range=getattr(args, "scene_count_range", None),
        )
    except Exception as exc:
        sys.stderr.write(f"Outline generation failed: {exc}\n")
        return 1
    sys.stdout.write(f"Outline created at {outline_path}\n")
    report_path, report = load_latest_outline_pipeline_report(workspace=workspace, book_id=args.book)
    if report:
        sys.stdout.write(format_outline_pipeline_summary(report, report_path=report_path))
    return 0


def _outline_reset(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    try:
        book_root, report = reset_outline_workspace_detailed(
            workspace=workspace,
            book_id=args.book,
            archive=bool(getattr(args, "archive", False)),
            keep_working_outline_artifacts=bool(getattr(args, "keep_working_outline_artifacts", False)),
            clear_generated_outline=bool(getattr(args, "clear_generated_outline", True)),
            clear_pipeline_runs=bool(getattr(args, "clear_pipeline_runs", True)),
            dry_run=bool(getattr(args, "dry_run", False)),
            force=bool(getattr(args, "force", False)),
        )
    except Exception as exc:
        sys.stderr.write(f"Outline reset failed: {exc}\n")
        return 1
    mode = "dry-run" if bool(getattr(args, "dry_run", False)) else "applied"
    sys.stdout.write(f"Outline reset ({mode}) at {book_root}\n")
    if report.get("archive_path"):
        sys.stdout.write(f"Outline archive created at {report.get('archive_path')}\n")
    sys.stdout.write(
        "Outline reset summary: "
        f"files_deleted={report.get('files_deleted', 0)} "
        f"dirs_deleted={report.get('dirs_deleted', 0)} "
        f"files_preserved={report.get('files_preserved', 0)} "
        f"dirs_preserved={report.get('dirs_preserved', 0)} "
        f"clear_generated_outline={report.get('clear_generated_outline', False)} "
        f"clear_pipeline_runs={report.get('clear_pipeline_runs', False)} "
        f"keep_working_outline_artifacts={report.get('keep_working_outline_artifacts', False)}\n"
    )
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
            ack_outline_attention_items=bool(getattr(args, "ack_outline_attention_items", False)),
        )
    except Exception as exc:
        sys.stderr.write(f"Run failed: {exc}\n")
        return 1
    sys.stdout.write("Run completed.\n")
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
    outline_generate = outline_sub.add_parser("generate", help="Generate an outline.")
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
        help="Resume a paused outline pipeline run.",
    )
    outline_generate.add_argument(
        "--from-phase",
        help="Start execution from phase id (outline pipeline mode).",
    )
    outline_generate.add_argument(
        "--to-phase",
        help="Stop execution at phase id (outline pipeline mode).",
    )
    outline_generate.add_argument(
        "--phase",
        help="Run only one phase (alias for --from-phase X --to-phase X).",
    )
    outline_generate.add_argument(
        "--transition-hints-file",
        help="Path to transition-hints JSON file.",
    )
    outline_generate.add_argument(
        "--strict-transition-hints",
        action="store_true",
        help="Enforce strict transition-hint compliance checks.",
    )
    outline_generate.add_argument(
        "--strict-transition-bridges",
        action="store_true",
        help="Enable strict transition-bridge enforcement mode.",
    )
    outline_generate.add_argument(
        "--strict-location-identity",
        dest="strict_location_identity",
        action="store_true",
        default=True,
        help="Require strict location identity validation (default: enabled).",
    )
    outline_generate.add_argument(
        "--relaxed-location-identity",
        dest="strict_location_identity",
        action="store_false",
        help="Allow placeholder-like location identity values as warnings instead of errors.",
    )
    outline_generate.add_argument(
        "--transition-insert-budget-per-chapter",
        type=int,
        default=2,
        help="Transition scene insertion budget per chapter (default: 2).",
    )
    outline_generate.add_argument(
        "--allow-transition-scene-insertions",
        dest="allow_transition_scene_insertions",
        action="store_true",
        default=True,
        help="Allow transition scene insertion during outline refinement (default: enabled).",
    )
    outline_generate.add_argument(
        "--disallow-transition-scene-insertions",
        dest="allow_transition_scene_insertions",
        action="store_false",
        help="Disable transition scene insertion during outline refinement.",
    )
    outline_generate.add_argument(
        "--force-rerun-with-draft",
        action="store_true",
        help="Allow rerun even when drafted scene artifacts already exist.",
    )
    outline_generate.add_argument(
        "--exact-scene-count",
        action="store_true",
        help="Force exact scene-count matching mode.",
    )
    outline_generate.add_argument(
        "--scene-count-range",
        help="Optional chapter scene-count range, format min:max.",
    )
    outline_generate.set_defaults(func=_outline_generate)

    outline_reset = outline_sub.add_parser("reset", help="Archive/reset outline pipeline artifacts.")
    outline_reset.add_argument("--book", required=True, help="Book id.")
    outline_reset.add_argument(
        "--archive",
        action="store_true",
        help="Archive outline targets before reset.",
    )
    outline_reset.add_argument(
        "--keep-working-outline-artifacts",
        action="store_true",
        help="Keep working outline files in place after archive/reset.",
    )
    outline_reset.add_argument(
        "--clear-generated-outline",
        dest="clear_generated_outline",
        action="store_true",
        default=True,
        help="Clear generated outline working artifacts (default: true).",
    )
    outline_reset.add_argument(
        "--no-clear-generated-outline",
        dest="clear_generated_outline",
        action="store_false",
        help="Do not clear generated outline working artifacts.",
    )
    outline_reset.add_argument(
        "--clear-pipeline-runs",
        dest="clear_pipeline_runs",
        action="store_true",
        default=True,
        help="Clear outline pipeline run artifacts and metadata (default: true).",
    )
    outline_reset.add_argument(
        "--no-clear-pipeline-runs",
        dest="clear_pipeline_runs",
        action="store_false",
        help="Do not clear outline pipeline run artifacts and metadata.",
    )
    outline_reset.add_argument(
        "--dry-run",
        action="store_true",
        help="Show reset/archive actions without mutating files.",
    )
    outline_reset.add_argument(
        "--force",
        action="store_true",
        help="Force outline reset even if outline run lock marker exists.",
    )
    outline_reset.set_defaults(func=_outline_reset)

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

    run_parser = subparsers.add_parser("run", help="Run the generation loop.")
    run_parser.add_argument("--book", required=True, help="Book id.")
    run_parser.add_argument("--steps", type=int, help="Number of steps to run.")
    run_parser.add_argument("--until", help="Stop condition, e.g. chapter:5.")
    run_parser.add_argument("--resume", action="store_true", help="Resume prior run.")
    run_parser.add_argument(
        "--ack-outline-attention-items",
        action="store_true",
        help="Acknowledge non-strict outline attention items and proceed with run.",
    )
    run_parser.set_defaults(func=_run)

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
        help="Do not clear workspace/logs/llm artifacts during reset.",
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
        help="Include logs/llm + logs/runs in the archive when --archive is set.",
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
