import codecs
from pathlib import Path

from bookforge.prompt.composition import (
    compose_prompt_templates,
    validate_prompt_composition_determinism,
)


def test_compose_prompt_templates_contracts(tmp_path: Path) -> None:
    output_dir = tmp_path / "templates"
    result = compose_prompt_templates(
        output_dir=output_dir,
        write_reports=False,
        enforce_checksums=True,
    )

    assert len(result.compiled_templates) == 14

    for template_name, compiled_text in result.compiled_templates.items():
        assert "\r" not in compiled_text

        audit = result.placeholder_audits[template_name]
        assert audit["status"] == "pass"
        assert audit["unknown_tokens"] == []

        target = output_dir / template_name
        assert target.exists()

        payload = target.read_bytes()
        assert payload.startswith(codecs.BOM_UTF8) is False
        assert b"\r" not in payload


def test_prompt_composition_determinism(tmp_path: Path) -> None:
    checksums = validate_prompt_composition_determinism(output_dir=tmp_path / "determinism")
    assert len(checksums) == 14
