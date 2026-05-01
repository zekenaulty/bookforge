from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from bookforge.cli import build_parser
from bookforge.contracts import ScopeSelector
from bookforge.execution import (
    approve_book_intent_action,
    build_approve_book_intent_request,
    build_create_book_from_intent_request,
    build_draft_book_intent_request,
    build_draft_starter_outline_request,
    build_freeze_section_request,
    build_initialize_workflow_request,
    create_book_from_intent_action,
    draft_book_intent_action,
    draft_starter_outline_from_intent,
    freeze_section,
    initialize_workflow,
)
from bookforge.query import list_execution_options
from bookforge.query.capabilities import get_capability_projection
from bookforge.llm.client import LLMClient
from bookforge.llm.types import LLMResponse, Message


def _fake_starter_outline(book_id: str = "clockwork_moon") -> dict:
    return {
        "schema_version": "1.1",
        "book_id": book_id,
        "characters": [
            {
                "character_id": "locksmith",
                "name": "The Locksmith",
                "intro": {"chapter": 1, "scene": 1},
                "role": "protagonist",
            }
        ],
        "threads": [
            {
                "thread_id": "lunar_vault",
                "label": "Lunar Vault",
                "status": "active",
                "summary": "The vault wants to choose its next owner.",
            }
        ],
        "chapters": [
            {
                "chapter_id": 1,
                "title": "The Locked Moon",
                "goal": "Put the locksmith under immediate pressure at the vault.",
                "chapter_role": "opening",
                "stakes_shift": "The impossible vault becomes personal.",
                "bridge": {"from_prev": "", "to_next": "The vault answers the first breach."},
                "pacing": {"intensity": 3, "tempo": "rising", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "First Breach",
                        "intent": "Open the heist and reveal the vault's will.",
                        "section_role": "setup",
                        "target_scene_count": 1,
                        "end_condition": "The locksmith understands the vault is choosing him.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "The locksmith reaches the lunar vault and realizes its lock is inviting him in.",
                                "type": "setup",
                                "goal": "Open the first lock without triggering the moon's security.",
                                "conflict": "The vault tests his motive before it tests his tools.",
                                "outcome": "The first ward opens because the vault recognizes him.",
                                "end_condition": "The vault has chosen to engage with the locksmith.",
                                "characters": ["locksmith"],
                                "threads": ["lunar_vault"],
                                "handoff_mode": "terminal",
                                "transition_in_text": "The lunar vault waits beneath the cold light.",
                                "transition_in_anchors": ["moonlight", "vault door", "first tool"],
                                "transition_out_text": "The first ward opens into a deeper, stranger lock.",
                                "transition_out_anchors": ["first ward opened", "deeper lock", "chosen thief"],
                                "location_start_label": "Lunar vault threshold",
                                "location_end_label": "Lunar vault threshold",
                                "constraint_state": "free",
                            }
                        ],
                    }
                ],
            },
            {
                "chapter_id": 2,
                "title": "The Vault's Terms",
                "goal": "Reveal the cost of accepting the vault's invitation.",
                "chapter_role": "escalation",
                "stakes_shift": "The heist becomes a negotiation with the vault.",
                "bridge": {"from_prev": "The first ward has opened.", "to_next": ""},
                "pacing": {"intensity": 4, "tempo": "urgent", "expected_scene_count": 1},
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Terms of Entry",
                        "intent": "Turn the heist into a binding bargain.",
                        "section_role": "turn",
                        "target_scene_count": 1,
                        "end_condition": "The locksmith accepts the vault's first condition.",
                        "scenes": [
                            {
                                "scene_id": 1,
                                "summary": "The vault offers passage in exchange for a memory of a door he failed to open.",
                                "type": "choice",
                                "goal": "Decide whether the next lock is worth the personal cost.",
                                "conflict": "The price threatens the locksmith's identity.",
                                "outcome": "He accepts, losing one memory but gaining the next chamber.",
                                "end_condition": "The next chamber is open and the cost is paid.",
                                "characters": ["locksmith"],
                                "threads": ["lunar_vault"],
                                "handoff_mode": "terminal",
                                "transition_in_text": "The deeper lock waits beyond the opened ward.",
                                "transition_in_anchors": ["first ward opened", "deeper lock", "chosen thief"],
                                "transition_out_text": "The next chamber opens after the cost is paid.",
                                "transition_out_anchors": ["memory paid", "next chamber", "identity cost"],
                                "location_start_label": "Lunar vault inner door",
                                "location_end_label": "Lunar vault inner door",
                                "constraint_state": "free",
                            }
                        ],
                    }
                ],
            },
        ],
    }


class FakeOutlineClient(LLMClient):
    def __init__(self) -> None:
        super().__init__(provider="fake")
        self.calls = 0

    def chat(
        self,
        messages: Iterable[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        thinking_level=None,
        thinking_budget=None,
    ) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            text=json.dumps(_fake_starter_outline(), ensure_ascii=True),
            raw={"finish_reason": "stop"},
            provider="fake",
            model=model,
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
        )


def _write_author_fixture(workspace: Path) -> None:
    author_dir = workspace / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Eldrik writes with dry system wit.", encoding="utf-8")


def _create_book_from_intent(workspace: Path, *, book_id: str = "clockwork_moon") -> None:
    _write_author_fixture(workspace)
    draft = draft_book_intent_action(
        workspace,
        build_draft_book_intent_request(
            title="Clockwork Moon",
            book_id=book_id,
            author_ref="eldrik-vale/v1",
            genre=["science fantasy", "heist"],
            seed_text="A burned-out locksmith steals time from a moon-sized vault.",
            targets={"chapters": 2, "sections_per_chapter": 1, "scenes_per_section": 1},
            short_synopsis="A locksmith has one night to crack a lunar vault.",
            reader_promise="A witty, pressure-driven heist with strange machines.",
            central_conflict="The vault wants to be robbed so it can choose its next owner.",
        ),
    )
    intent_id = draft.details["intent_id"]
    approve_book_intent_action(workspace, build_approve_book_intent_request(intent_ref=intent_id))
    create_book_from_intent_action(workspace, build_create_book_from_intent_request(intent_ref=intent_id))


def test_draft_starter_outline_from_intent_enables_workflow_initialization_and_freeze(tmp_path: Path) -> None:
    _create_book_from_intent(tmp_path)
    selector = ScopeSelector(book_id="clockwork_moon", branch_id="main")

    before_options = {option.action: option for option in list_execution_options(tmp_path, selector, prefer_emitted=False)}
    assert before_options["draft_starter_outline_from_intent"].allowed is True
    assert before_options["initialize_section_workflow"].allowed is False

    result = draft_starter_outline_from_intent(
        tmp_path,
        build_draft_starter_outline_request(tmp_path, "clockwork_moon", run_id="starter_test"),
        client=FakeOutlineClient(),
        model="fake-outline-model",
    )

    assert result.status == "success"
    assert result.action == "draft_starter_outline_from_intent"
    assert result.node.workflow_family == "thin_outline"
    assert result.details["run_id"] == "starter_test"
    assert result.details["provider_used"] is True
    assert result.details["llm_calls"] == 1
    assert result.details["model"] == "fake-outline-model"
    assert result.details["deep_outline_pipeline"] is False
    assert result.details["next_recommended_action"] == "initialize_section_workflow"
    assert result.details["next_recommended_actions"] == ["initialize_section_workflow"]
    assert result.details["follow_on_sequence"] == [
        "initialize_section_workflow",
        "freeze_section_from_phase03_artifact",
        "create_branch",
        "continue_scene",
    ]
    assert "re-query legal actions" in result.details["follow_on_sequence_policy"]
    assert result.artifact_paths["outline_final"].endswith("outline_final_v1_1.json")

    book_root = tmp_path / "books" / "clockwork_moon"
    latest = json.loads((book_root / "outline" / "pipeline_latest.json").read_text(encoding="utf-8"))
    assert latest["run_id"] == "starter_test"
    assert latest["workflow_family"] == "thin_outline"
    final_outline = json.loads(
        (book_root / "outline" / "pipeline_runs" / "starter_test" / "outline_final_v1_1.json").read_text(
            encoding="utf-8"
        )
    )
    assert final_outline["source"] == "book_intent_llm"
    assert len(final_outline["chapters"]) == 2
    assert final_outline["chapters"][0]["sections"][0]["scenes"][0]["scene_id"] == 1

    after_options = {option.action: option for option in list_execution_options(tmp_path, selector, prefer_emitted=False)}
    assert after_options["draft_starter_outline_from_intent"].allowed is False
    assert after_options["initialize_section_workflow"].allowed is True
    assert after_options["initialize_section_workflow"].details["run_id"] == "starter_test"

    init_result = initialize_workflow(tmp_path, build_initialize_workflow_request(tmp_path, "clockwork_moon"))
    assert init_result.status == "success"
    assert init_result.details["run_id"] == "starter_test"

    freeze_result = freeze_section(
        tmp_path,
        build_freeze_section_request(tmp_path, "clockwork_moon", chapter_id=1, section_id=1),
    )
    assert freeze_result.status == "success"
    assert freeze_result.details["chapter_id"] == 1
    assert freeze_result.details["section_id"] == 1


def test_draft_starter_outline_capability_projection_and_cli_parse() -> None:
    projection = get_capability_projection()
    by_id = {capability.capability_id: capability for capability in projection.capabilities}

    assert "action.draft_starter_outline_from_intent" in by_id
    capability = by_id["action.draft_starter_outline_from_intent"]
    assert capability.process_area == "outline"
    assert capability.details["calls_outline_provider"] is True
    assert capability.details["provider_call_count_per_request"] == 1
    assert capability.details["deep_outline_pipeline"] is False
    assert capability.details["does_not_initialize_workflow"] is True
    assert capability.details["does_not_write_prose"] is True
    assert capability.legal_next_action_relationships == ["enables_initialize_section_workflow"]

    parser = build_parser()
    args = parser.parse_args(
        [
            "workflow",
            "draft-starter-outline",
            "--book",
            "clockwork_moon",
            "--run-id",
            "starter_test",
            "--json",
        ]
    )
    assert args.workflow_command == "draft-starter-outline"
    assert args.book == "clockwork_moon"
