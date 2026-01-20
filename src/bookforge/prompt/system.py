from __future__ import annotations

import json
from pathlib import Path


def build_system_prompt(
    base_rules: str,
    book_constitution: str,
    author_fragment: str,
    output_contract: str,
) -> str:
    sections = [
        "# BookForge System Prompt",
        "## Base Rules",
        base_rules.strip(),
        "## Book Constitution",
        book_constitution.strip(),
        "## Author Persona",
        author_fragment.strip(),
        "## Output Contract",
        output_contract.strip(),
    ]
    return "\n\n".join([section for section in sections if section.strip()]) + "\n"


def write_system_prompt(
    path: Path,
    base_rules: str,
    book_constitution: str,
    author_fragment: str,
    output_contract: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_system_prompt(base_rules, book_constitution, author_fragment, output_contract),
        encoding="utf-8",
    )


def minify_outline_json(outline_path: Path) -> str:
    try:
        data = json.loads(outline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return outline_path.read_text(encoding="utf-8").strip()
    return json.dumps(data, ensure_ascii=True, separators=(",", ":"))


def load_system_prompt(
    system_path: Path,
    outline_path: Path | None = None,
    include_outline: bool = False,
) -> str:
    base = system_path.read_text(encoding="utf-8")
    if not include_outline:
        return base
    if "## Full Book Outline" in base:
        return base
    if outline_path is None or not outline_path.exists():
        return base
    outline = minify_outline_json(outline_path)
    if not outline:
        return base
    return (
        base.rstrip()
        + "\n\n## Full Book Outline (minified JSON)\n"
        + "Authoritative story map; follow it.\n"
        + outline
        + "\n"
    )
