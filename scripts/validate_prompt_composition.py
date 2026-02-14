from __future__ import annotations

import argparse
import codecs
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bookforge.prompt.composition import (  # noqa: E402
    PromptCompositionError,
    compose_prompt_templates,
    validate_prompt_composition_determinism,
)


def _has_invalid_encoding(path: Path) -> tuple[bool, bool]:
    data = path.read_bytes()
    has_bom = data.startswith(codecs.BOM_UTF8)
    has_cr = b"\r" in data
    return has_bom, has_cr


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate prompt composition determinism and contracts.")
    parser.add_argument(
        "--no-write-reports",
        action="store_true",
        help="Do not regenerate composition audit reports.",
    )
    args = parser.parse_args()

    try:
        validate_prompt_composition_determinism()
        result = compose_prompt_templates(
            write_reports=not args.no_write_reports,
            enforce_checksums=True,
        )
    except PromptCompositionError as exc:
        sys.stderr.write(f"Prompt composition validation failed: {exc}\n")
        return 1

    encoding_issues: list[str] = []
    for template in sorted(result.compiled_templates.keys()):
        target = result.output_dir / template
        has_bom, has_cr = _has_invalid_encoding(target)
        if has_bom or has_cr:
            encoding_issues.append(
                f"{template} (has_bom={has_bom}, has_cr_or_crlf={has_cr})"
            )

    if encoding_issues:
        sys.stderr.write(
            "Encoding/newline policy violation in compiled templates: "
            + "; ".join(encoding_issues)
            + "\n"
        )
        return 1

    sys.stdout.write(
        f"Prompt composition validation passed for {len(result.compiled_templates)} templates.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
