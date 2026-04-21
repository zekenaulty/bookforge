#!/usr/bin/env python3
"""Compile one plan folder into a single reviewable Markdown projection."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple
import sys


STAGE_DIRS = ("Brainstorms", "Drafts", "InProgress", "Completed")
ARCHIVE_BUCKETS = ("Brainstorms", "Drafts", "CompletedHistory")


@dataclass(frozen=True)
class PlanScope:
    stage: str
    scope_path: str
    plan_name: str


@dataclass(frozen=True)
class SourceDocument:
    absolute_path: Path
    relative_path: Path
    sort_key: Tuple


def _plans_root_from_script(script_path: Path) -> Path:
    return script_path.resolve().parent


def _relative_to_plans(plan_dir: Path, plans_root: Path) -> Path:
    try:
        return plan_dir.resolve().relative_to(plans_root.resolve())
    except ValueError as exc:
        raise ValueError(f"Plan directory must be inside `{plans_root}`.") from exc


def resolve_plan_scope(plan_dir: Path, plans_root: Path) -> PlanScope:
    rel = _relative_to_plans(plan_dir, plans_root)
    parts = rel.parts

    if len(parts) < 2:
        raise ValueError(
            "Plan path must target a plan folder, for example "
            "`resources/plans/Drafts/my-plan`."
        )

    first = parts[0]
    if first in STAGE_DIRS:
        if len(parts) != 2:
            raise ValueError(
                "Stage plan paths must be exactly "
                "`resources/plans/<Stage>/<plan-folder>`."
            )
        plan_name = parts[1]
        return PlanScope(stage=first, scope_path=f"{first}/{plan_name}", plan_name=plan_name)

    if first == "Archived":
        if len(parts) != 3:
            raise ValueError(
                "Archived plan paths must be exactly "
                "`resources/plans/Archived/<Bucket>/<plan-folder>`."
            )
        bucket = parts[1]
        if bucket not in ARCHIVE_BUCKETS:
            supported = ", ".join(ARCHIVE_BUCKETS)
            raise ValueError(f"Unsupported archive bucket `{bucket}`. Supported: {supported}")
        plan_name = parts[2]
        scope_path = f"Archived/{bucket}/{plan_name}"
        return PlanScope(stage="Archived", scope_path=scope_path, plan_name=plan_name)

    supported_stages = ", ".join(STAGE_DIRS)
    raise ValueError(f"Unsupported plan stage `{first}`. Supported stages: {supported_stages}.")


def validate_plan_folder(plan_dir: Path) -> None:
    if not plan_dir.exists() or not plan_dir.is_dir():
        raise ValueError(f"Plan directory does not exist: {plan_dir}")
    plan_md = plan_dir / "plan.md"
    if not plan_md.exists():
        raise ValueError(f"Missing required file: {plan_md}")


def normalize_output_name(output_name: Optional[str], plan_name: str) -> str:
    name = output_name.strip() if output_name else f"{plan_name}.md"
    if not name.lower().endswith(".md"):
        name = f"{name}.md"
    if "/" in name or "\\" in name:
        raise ValueError("`--output-name` must be a file name only.")
    if name.lower() in {"plan.md", "archive-note.md"}:
        raise ValueError("`--output-name` cannot overwrite canonical source files.")
    return name


def _parse_step_prefix(segment: str) -> Tuple[int, str]:
    head = segment.split("-", 1)[0]
    if head.isdigit():
        return int(head), segment
    return 9999, segment


def _section_rank(relative: Path) -> Tuple:
    parts = relative.parts
    path_text = relative.as_posix().lower()

    if path_text == "plan.md":
        return (0, 0, "", "", path_text)
    if len(parts) >= 2 and parts[0] == "decisions":
        return (1, 0, "", "", path_text)
    if len(parts) >= 2 and parts[0] == "risks":
        return (2, 0, "", "", path_text)
    if len(parts) >= 2 and parts[0] == "validation":
        return (3, 0, "", "", path_text)
    if path_text == "steps/index.md":
        return (4, 0, "", "", path_text)
    if len(parts) >= 3 and parts[0] == "steps":
        step_order, step_folder = _parse_step_prefix(parts[1])
        if len(parts) == 3 and parts[2].lower() == "step.md":
            return (5, step_order, step_folder.lower(), "00-step", path_text)
        if len(parts) >= 4:
            sub = parts[2].lower()
            sub_rank = {"artifacts": 1, "validation": 2, "notes": 3}.get(sub, 9)
            return (6, step_order, step_folder.lower(), f"{sub_rank:02d}-{sub}", path_text)
        return (6, step_order, step_folder.lower(), "99-other", path_text)
    if len(parts) >= 2 and parts[0] == "notes":
        return (7, 0, "", "", path_text)
    if path_text == "archive-note.md":
        return (8, 0, "", "", path_text)
    return (9, 0, "", "", path_text)


def gather_source_documents(plan_dir: Path, output_name: str) -> List[SourceDocument]:
    excluded_names = {output_name.lower(), "compiled-plan.md"}
    docs: List[SourceDocument] = []

    for path in sorted(plan_dir.rglob("*.md")):
        if not path.is_file():
            continue
        if path.name.lower() in excluded_names:
            continue
        rel = path.resolve().relative_to(plan_dir.resolve())
        docs.append(
            SourceDocument(
                absolute_path=path.resolve(),
                relative_path=rel,
                sort_key=_section_rank(rel),
            )
        )

    docs.sort(key=lambda doc: doc.sort_key)
    return docs


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _render_toc(docs: Sequence[SourceDocument]) -> str:
    lines = ["## Contents", ""]
    for index, doc in enumerate(docs, start=1):
        lines.append(f"{index}. `{doc.relative_path.as_posix()}`")
    lines.append("")
    return "\n".join(lines)


def build_compiled_markdown(
    *,
    plan_scope: PlanScope,
    docs: Sequence[SourceDocument],
    output_name: str,
) -> str:
    lines: List[str] = [
        f"# {plan_scope.plan_name}",
        "",
        "## Compiled Plan Metadata",
        "",
        f"- Plan Scope: `{plan_scope.scope_path}`",
        f"- Compiled At (UTC): `{_now_utc_iso()}`",
        f"- Source Document Count: `{len(docs)}`",
        f"- Projection File: `{output_name}`",
        "",
        _render_toc(docs),
    ]

    for index, doc in enumerate(docs, start=1):
        lines.extend(
            [
                "---",
                "",
                f"## Source {index}: `{doc.relative_path.as_posix()}`",
                "",
                _read_utf8(doc.absolute_path).rstrip(),
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def write_compiled_markdown(output_path: Path, content: str) -> None:
    output_path.write_text(content, encoding="utf-8")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a plan folder into one shareable markdown file."
    )
    parser.add_argument(
        "plan_dir",
        help="Path to a plan folder, for example resources/plans/Drafts/my-plan",
    )
    parser.add_argument(
        "--output-name",
        help="Output file name inside the plan folder. Defaults to <plan-folder-name>.md",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate scope and list included files without writing output.",
    )
    parser.add_argument(
        "--print-files",
        action="store_true",
        help="Print included source files in compile order.",
    )
    return parser.parse_args(argv)


def _print_file_list(docs: Iterable[SourceDocument]) -> None:
    for doc in docs:
        print(doc.relative_path.as_posix())


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_path = Path(__file__).resolve()
    plans_root = _plans_root_from_script(script_path)
    plan_dir = (Path.cwd() / args.plan_dir).resolve()

    try:
        validate_plan_folder(plan_dir)
        plan_scope = resolve_plan_scope(plan_dir, plans_root)
        output_name = normalize_output_name(args.output_name, plan_scope.plan_name)
        output_path = (plan_dir / output_name).resolve()
        if output_path.parent != plan_dir:
            raise ValueError("Output path must remain inside the selected plan folder.")
        docs = gather_source_documents(plan_dir, output_name)
        if not docs:
            raise ValueError("No source markdown files were found to compile.")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.print_files or args.dry_run:
        print(f"Plan Scope: {plan_scope.scope_path}")
        print(f"Output File: {output_path}")
        print(f"Source Count: {len(docs)}")

    if args.print_files:
        print("")
        _print_file_list(docs)

    if args.dry_run:
        return 0

    compiled = build_compiled_markdown(
        plan_scope=plan_scope,
        docs=docs,
        output_name=output_name,
    )
    write_compiled_markdown(output_path, compiled)
    print(f"Compiled plan written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
