from __future__ import annotations

from bookforge.skill_runtime import build_skill_definition, build_prompt_bundle, render_template


def test_render_template_supports_nested_tokens() -> None:
    rendered = render_template("Hello {{user.name}}", {"user": {"name": "Ari"}})
    assert rendered == "Hello Ari"


def test_build_prompt_bundle_includes_metadata_and_params() -> None:
    skill = build_skill_definition(
        {
            "skill_id": "bookforge.test.example",
            "display_name": "Example Skill",
            "llm_description": "Example description.",
            "kind": "phase",
            "category": "outline",
            "graph_node": "outline.example",
            "phase_id": "phase_example",
            "logical_phase": "phase_example",
            "prompt_contract": "Return strict JSON.",
            "output_hint": "JSON",
            "required_params": ["request", "input_payload"],
            "source_refs": ["docs/help/index.md"],
            "help_refs": ["docs/help/index.md"],
            "example_params": {"request": "Run example", "input_payload": {"value": 1}}
        }
    )

    bundle = build_prompt_bundle(
        skill,
        {
            "request": "Run example",
            "input_payload": {"value": 1}
        },
    )

    assert bundle["skill"]["skill_id"] == "bookforge.test.example"
    assert "Run example" in bundle["user_prompt"]
    assert "Return strict JSON." in bundle["system_prompt"]
