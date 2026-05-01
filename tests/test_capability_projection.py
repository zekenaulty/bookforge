from __future__ import annotations

import re
import json
from pathlib import Path

import pytest

from bookforge.cli import build_parser
from bookforge.contracts import (
    CapabilityDescriptor,
    CapabilityProjection,
    CapabilityRefusalSemantics,
)
from bookforge.query.capabilities import ACTION_CAPABILITY_SPECS, get_capability_projection


def test_capability_descriptor_round_trips_without_dynamic_readiness() -> None:
    descriptor = CapabilityDescriptor(
        capability_id="action.test_action",
        human_label="Test action",
        unit_type="primitive_action",
        capability_type="action",
        action_key="test_action",
        supported_scope_kinds=["scene"],
        required_selector_shape=["book_id", "chapter", "scene"],
        branch_policy="any",
        mutation_class="provisional_branch_mutation",
        produced_artifact_statuses=["provisional"],
        refusal_semantics=CapabilityRefusalSemantics(
            refusal_mode="dynamic_readiness_refusal",
            refusal_reason_codes=["not_ready"],
        ),
    )

    restored = CapabilityDescriptor.from_dict(descriptor.to_dict())

    assert restored == descriptor
    assert "allowed" not in restored.to_dict()


def test_capability_descriptor_rejects_dynamic_readiness_fields() -> None:
    with pytest.raises(ValueError, match="dynamic readiness"):
        CapabilityDescriptor(
            capability_id="action.bad",
            human_label="Bad action",
            unit_type="primitive_action",
            capability_type="action",
            supported_scope_kinds=["scene"],
            required_selector_shape=["book_id"],
            branch_policy="any",
            mutation_class="read_only",
            details={"allowed": True},
        )


def test_projection_exports_static_action_query_readiness_and_gap_surfaces() -> None:
    projection = get_capability_projection()
    restored = CapabilityProjection.from_dict(projection.to_dict())
    by_id = {capability.capability_id: capability for capability in restored.capabilities}

    assert "action.continue_scene" in by_id
    assert "action.write_scene_prose" in by_id
    assert "action.create_author" in by_id
    assert "action.refine_author" in by_id
    assert "action.draft_book_intent" in by_id
    assert "action.approve_book_intent" in by_id
    assert "action.create_book_from_intent" in by_id
    assert "action.promote_recovery_branch" in by_id
    assert "query.author_profiles" in by_id
    assert "query.author_profile" in by_id
    assert "query.book_intents" in by_id
    assert "query.book_intent" in by_id
    assert "query.outline_lineage_audit" in by_id
    assert "query.book_cards" in by_id
    assert "query.branch_inventory" in by_id
    assert "query.branch_detail" in by_id
    assert "query.branch_artifact_index" in by_id
    assert "query.branch_diff_summary" in by_id
    assert "query.next_writing_target" in by_id
    assert "query.writing_bootstrap_status" in by_id
    assert "query.chapter_seam_queue" in by_id
    assert "query.scene_pair_seam_detail" in by_id
    assert "query.book_reader_scene" in by_id
    assert "query.book_reader_anchor" in by_id
    assert "query.recovery_anchor_candidates" in by_id
    assert "query.recovery_plan_preview" in by_id
    assert "query.author_loop_envelopes" in by_id
    assert "readiness.scene_phase_readiness" in by_id
    assert "readiness.writing_gate_status" in by_id
    assert "action.align_scene_pair_seam" in by_id
    assert "action.plan_bridge_scene_insertion" in by_id
    assert "action.apply_bridge_scene_insertion" in by_id
    assert "gap.apply_bridge_scene_insertion" not in by_id
    assert "gap.book_intent.synopsis" not in by_id
    assert "gap.author_assets.create_refine" not in by_id
    assert by_id["action.align_scene_pair_seam"].branch_policy == "derived_only"
    assert by_id["action.plan_bridge_scene_insertion"].details["proposal_only"] is True
    assert by_id["action.apply_bridge_scene_insertion"].details["same_section_only_first_slice"] is True
    assert by_id["action.apply_bridge_scene_insertion"].details["nanda_wire_recommendation"] == "safe_to_wire_behind_gates"
    assert "missing_bridge_scene_insertion_plan" in by_id["action.apply_bridge_scene_insertion"].details["legal_refusal_codes"]
    assert "stale_write" in by_id["action.apply_bridge_scene_insertion"].details["execution_failure_codes"]
    assert "bridge_scene_insertion_apply_report" in by_id["action.apply_bridge_scene_insertion"].details["expected_artifact_keys"]
    assert by_id["action.write_frozen_section"].unit_type == "macro_workflow"
    assert by_id["action.write_frozen_section"].approval_required is True
    assert by_id["action.write_frozen_section"].details["approval_class"] == "section_macro"
    assert by_id["action.write_frozen_section"].details["broad_macro"] is True
    assert by_id["action.write_frozen_section"].details["not_for_single_scene_requests"] is True
    assert by_id["action.write_frozen_section"].details["preferred_single_scene_action"] == "continue_scene"
    assert by_id["action.write_frozen_section"].details["step_count_per_call"] == "all missing scenes in the selected frozen section"
    assert by_id["action.continue_scene"].unit_type == "macro_workflow"
    assert by_id["action.continue_scene"].details["step_count_per_call"] == 1
    assert by_id["action.continue_scene"].details["loop_step_receipt_schema"] == "author_loop_step_receipt_v1"
    assert by_id["action.initialize_section_workflow"].approval_required is True
    assert by_id["action.initialize_section_workflow"].details["does_not_call_provider"] is True
    assert by_id["action.initialize_section_workflow"].details["does_not_write_prose"] is True
    assert by_id["action.freeze_section_from_phase03_artifact"].approval_required is True
    assert by_id["action.freeze_section_from_phase03_artifact"].details["freezes_one_section_only"] is True
    assert by_id["action.freeze_section_from_phase03_artifact"].details["does_not_write_prose"] is True
    assert by_id["action.lock_section_from_written_state"].branch_policy == "any"
    assert by_id["action.lock_section_from_written_state"].details["canonical_change_requires_main"] is True
    assert by_id["action.finalize_chapter_from_locked_sections"].branch_policy == "any"
    assert by_id["action.finalize_chapter_from_locked_sections"].details["canonical_change_requires_main"] is True
    assert "plan_scene" in by_id["action.continue_scene"].child_actions
    assert by_id["action.write_scene_prose"].process_area == "writing"
    assert by_id["action.create_author"].process_area == "author_assets"
    assert by_id["query.outline_lineage_audit"].process_area == "outline"
    assert by_id["query.next_writing_target"].process_area == "writing"
    assert by_id["query.writing_bootstrap_status"].process_area == "writing"
    assert "draft_starter_outline_from_intent" in by_id["query.writing_bootstrap_status"].details["expected_sequence"]
    assert by_id["query.author_loop_envelopes"].details["refresh_required_between_steps"] is True
    assert by_id["query.author_loop_envelopes"].details["refresh_query_order"][0] == "branch_detail"
    assert by_id["query.chapter_seam_queue"].process_area == "writing"
    assert by_id["query.chapter_seam_queue"].details["action_bridge"] == "Ready items map to action.align_scene_pair_seam."
    assert by_id["query.scene_pair_seam_detail"].process_area == "writing"
    assert by_id["query.scene_pair_seam_detail"].details["report_policy"]
    assert by_id["query.book_reader_anchor"].process_area == "reader_output"
    assert by_id["query.book_reader_anchor"].details["mutation_note"]
    assert by_id["readiness.writing_gate_status"].process_area == "writing"
    assert "writing" in projection.details["process_areas"]
    assert "scene" in projection.details["scope_kinds"]
    assert "write_scene_prose" in by_id["action.write_frozen_section"].child_actions
    assert projection.details["static_dynamic_boundary"]


def test_projected_actions_cover_real_execution_option_action_strings() -> None:
    source = Path("src/bookforge/query/actions.py").read_text(encoding="utf-8")
    action_strings = set(re.findall(r'action="([^"]+)"', source))

    assert action_strings
    assert action_strings <= set(ACTION_CAPABILITY_SPECS)


def test_cli_parses_capability_projection_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["capabilities", "--json"])

    assert args.command == "capabilities"
    assert args.json is True


def test_nanda_fixture_validates_and_covers_representative_categories() -> None:
    payload = json.loads(Path("tests/fixtures/capability_projection_v1.json").read_text(encoding="utf-8-sig"))
    projection = CapabilityProjection.from_dict(payload)
    by_id = {capability.capability_id: capability for capability in projection.capabilities}

    assert by_id["query.outline_lineage_audit"].mutation_class == "read_only"
    assert by_id["readiness.scene_phase_readiness"].capability_type == "readiness"
    assert by_id["readiness.writing_gate_status"].capability_type == "readiness"
    assert by_id["action.write_scene_prose"].produced_artifact_statuses == ["provisional"]
    assert by_id["action.continue_scene"].details["step_count_per_call"] == 1
    assert by_id["action.continue_scene"].details["loop_step_receipt_schema"] == "author_loop_step_receipt_v1"
    assert by_id["action.write_frozen_section"].approval_required is True
    assert by_id["action.write_frozen_section"].details["not_for_single_scene_requests"] is True
    assert by_id["action.lock_section_from_written_state"].branch_policy == "any"
    assert by_id["action.finalize_chapter_from_locked_sections"].branch_policy == "any"
    assert "apply_scene_commit" in by_id["action.continue_scene"].child_actions
    assert by_id["action.lint_scene_prose"].unit_type == "validation_gate"
    assert by_id["action.create_branch"].mutation_class == "branch_mutation"
    assert by_id["action.create_recovery_branch"].details["cleanliness_status_after_success"] == "isolated_not_clean"
    assert by_id["action.promote_recovery_branch"].approval_required is True
    assert "write_scene_prose" in by_id["action.write_frozen_section"].child_actions
    assert by_id["query.book_reader_scene"].implementation_status == "implemented"
    assert by_id["query.book_reader_anchor"].implementation_status == "implemented"
    assert by_id["query.branch_detail"].implementation_status == "implemented"
    assert by_id["query.branch_artifact_index"].implementation_status == "implemented"
    assert by_id["query.branch_diff_summary"].implementation_status == "implemented"
    assert by_id["query.next_writing_target"].implementation_status == "implemented"
    assert by_id["query.writing_bootstrap_status"].implementation_status == "implemented"
    assert by_id["query.chapter_seam_queue"].implementation_status == "implemented"
    assert by_id["query.scene_pair_seam_detail"].implementation_status == "implemented"
    assert by_id["query.recovery_anchor_candidates"].implementation_status == "implemented"
    assert by_id["query.recovery_plan_preview"].implementation_status == "implemented"
    assert by_id["query.author_profile"].implementation_status == "implemented"
    assert by_id["action.create_author"].implementation_status == "implemented"
    assert by_id["action.refine_author"].implementation_status == "implemented"
    assert by_id["action.refine_author"].details["overwrite_behavior"] == "creates_new_version"
