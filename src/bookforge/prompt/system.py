from __future__ import annotations

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
