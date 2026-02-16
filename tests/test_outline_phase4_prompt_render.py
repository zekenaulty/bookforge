from pathlib import Path

from bookforge.prompt.renderer import render_template_file


def test_phase04b_prompt_render_includes_routing_payloads(tmp_path: Path) -> None:
    template = Path("resources/prompt_templates/outline_phase_04b_transition_execution.md")
    rendered = render_template_file(
        template,
        {
            "book": {"book_id": "b1"},
            "targets": {"chapters": 10},
            "notes": "",
            "outline_phase_04a_output": {"schema_version": "transition_refine_v1", "outline": {}, "phase_report": {}},
            "phase_04_selected_candidates_json": [{"from_scene_ref": "1:1", "to_scene_ref": "1:2", "requested_resolution": "micro_scene"}],
            "phase_04_blocked_candidates_json": [],
            "phase_04_policy_context_json": {"candidate_count": 1, "exact_conflicts": []},
        },
    )

    assert "{{phase_04_selected_candidates_json}}" not in rendered
    assert "{{phase_04_blocked_candidates_json}}" not in rendered
    assert "{{phase_04_policy_context_json}}" not in rendered
    assert "{{outline_phase_04a_output}}" not in rendered
