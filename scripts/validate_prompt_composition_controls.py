from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List


REQUIRED_LOGS = {
    "change_log.md": [
        "timestamp",
        "author",
        "scope",
        "changed_files",
        "reason",
        "expected_behavior_impact",
        "verification_method",
        "result",
        "rollback_note",
    ],
    "risk_log.md": [
        "timestamp",
        "risk_id",
        "risk_statement",
        "trigger",
        "impact",
        "likelihood",
        "mitigation",
        "owner",
        "status",
        "evidence",
    ],
    "decision_log.md": [
        "timestamp",
        "decision_id",
        "decision",
        "context",
        "options_considered",
        "selected_option",
        "rationale",
        "impact_scope",
        "risks_accepted",
        "follow_up",
    ],
    "review_log.md": [
        "timestamp",
        "review_stage",
        "reviewer",
        "scope_reviewed",
        "findings",
        "blocking_issues",
        "approvals",
        "required_follow_up",
        "status",
    ],
    "validation_log.md": [
        "timestamp",
        "validation_type",
        "command_or_method",
        "baseline_reference",
        "compared_reference",
        "metrics",
        "result",
        "regressions_detected",
        "follow_up",
    ],
}

MATERIAL_CHANGE_PREFIXES = (
    "src/bookforge/prompt/composition.py",
    "src/bookforge/workspace.py",
    "resources/prompt_blocks/",
    "resources/prompt_composition/",
    "resources/prompt_templates/",
)


def _parse_entries(path: Path) -> List[Dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    section_start = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Entries":
            section_start = idx + 1
            break
    if section_start is None:
        return []

    entries: List[Dict[str, str]] = []
    current: Dict[str, str] = {}

    for raw_line in lines[section_start:]:
        line = raw_line.strip()
        if not line:
            continue
        if not line.startswith("- ") or ":" not in line:
            continue

        field = line[2:].split(":", 1)[0].strip().lower()
        value = line.split(":", 1)[1].strip()

        if field == "timestamp":
            if current:
                entries.append(current)
            current = {}
        if current is None:
            current = {}
        current[field] = value

    if current:
        entries.append(current)

    return [entry for entry in entries if entry]


def _has_material_changes(changed_files: List[str]) -> bool:
    normalized = [item.replace("\\", "/") for item in changed_files]
    return any(any(item.startswith(prefix) for prefix in MATERIAL_CHANGE_PREFIXES) for item in normalized)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate mandatory prompt-composition control logs.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path.",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Changed file path (repeatable). Use repo-relative paths.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    controls_root = (
        repo_root
        / "resources"
        / "plans"
        / "prompt_template_composition_forensics_20260213_183000"
        / "controls"
    )

    errors: List[str] = []

    for log_name, required_fields in REQUIRED_LOGS.items():
        path = controls_root / log_name
        if not path.exists():
            errors.append(f"Missing required control log: {path}")
            continue

        entries = _parse_entries(path)
        if _has_material_changes(args.changed_file) and not entries:
            errors.append(
                f"Material composition changes detected but no entries found in {path}"
            )
            continue

        for idx, entry in enumerate(entries, start=1):
            missing = [field for field in required_fields if field not in entry]
            if missing:
                errors.append(
                    f"{path} entry {idx} missing required fields: {', '.join(missing)}"
                )

    if errors:
        for error in errors:
            sys.stderr.write(error + "\n")
        return 1

    sys.stdout.write("Prompt composition control-log validation passed.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
