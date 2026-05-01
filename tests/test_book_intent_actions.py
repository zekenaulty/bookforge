from __future__ import annotations

import json
from pathlib import Path

from bookforge.cli import build_parser
from bookforge.contracts import ScopeSelector
from bookforge.execution import (
    build_approve_book_intent_request,
    build_create_book_from_intent_request,
    build_draft_book_intent_request,
    approve_book_intent_action,
    create_book_from_intent_action,
    draft_book_intent_action,
)
from bookforge.query import get_book_card, get_book_intent, list_book_intents, list_execution_options
from bookforge.query.capabilities import get_capability_projection


def _write_author_fixture(workspace: Path) -> None:
    author_dir = workspace / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Eldrik writes with dry system wit.", encoding="utf-8")


def test_book_intent_draft_approve_and_create_book(tmp_path: Path) -> None:
    _write_author_fixture(tmp_path)

    draft_request = build_draft_book_intent_request(
        title="Clockwork Moon",
        book_id="clockwork_moon",
        author_ref="eldrik-vale/v1",
        genre=["science fantasy", "heist"],
        seed_text="A burned-out locksmith steals time from a moon-sized vault.",
        targets={"chapters": 12},
        short_synopsis="A locksmith has one night to crack a lunar vault.",
        reader_promise="A witty, pressure-driven heist with strange machines.",
        central_conflict="The vault wants to be robbed so it can choose its next owner.",
        tone="deadpan, tense, clever",
        must_have=["clockwork rituals"],
        must_not=["cosmic reset"],
        source_ref="nanda:book_seed:test",
    )
    draft_result = draft_book_intent_action(tmp_path, draft_request)

    assert draft_result.status == "success"
    assert draft_result.produced_artifacts[0].artifact_status == "provisional"
    assert Path(draft_result.artifact_paths["book_intent"]).exists()

    intent_id = draft_result.details["intent_id"]
    draft_record = get_book_intent(tmp_path, intent_id)
    assert draft_record.intent.status == "draft"
    assert draft_record.intent.reader_promise == "A witty, pressure-driven heist with strange machines."
    assert len(list_book_intents(tmp_path)) == 1

    legal = {option.action: option for option in list_execution_options(tmp_path, ScopeSelector(book_id="__book_intents__", workflow_family="book_intent"), prefer_emitted=False)}
    assert legal["draft_book_intent"].allowed is True
    assert legal["approve_book_intent"].allowed is True
    assert legal["create_book_from_intent"].allowed is False

    approve_result = approve_book_intent_action(tmp_path, build_approve_book_intent_request(intent_ref=intent_id))
    assert approve_result.status == "success"
    assert approve_result.produced_artifacts[0].artifact_status == "authoritative"

    create_result = create_book_from_intent_action(tmp_path, build_create_book_from_intent_request(intent_ref=intent_id))
    assert create_result.status == "success"
    assert create_result.details["created_book_id"] == "clockwork_moon"
    assert create_result.details["canonical_transition"] == "author_only_seed_to_book_scope"

    book_root = tmp_path / "books" / "clockwork_moon"
    assert (book_root / "book.json").exists()
    assert (book_root / "book_intent.json").exists()
    assert (book_root / "draft" / "context" / "book_intent.md").exists()

    book = json.loads((book_root / "book.json").read_text(encoding="utf-8"))
    assert book["book_intent_id"] == intent_id
    assert book["book_intent"]["reader_promise"] == "A witty, pressure-driven heist with strange machines."

    bible = (book_root / "draft" / "context" / "bible.md").read_text(encoding="utf-8")
    assert "A burned-out locksmith steals time" in bible
    system_prompt = (book_root / "prompts" / "system_v1.md").read_text(encoding="utf-8")
    assert "Reader promise" in system_prompt

    created_record = get_book_intent(tmp_path, intent_id)
    assert created_record.intent.status == "created"
    assert created_record.intent.created_book_id == "clockwork_moon"
    assert get_book_card(tmp_path, "clockwork_moon").title == "Clockwork Moon"


def test_book_intent_capabilities_replace_designed_gap() -> None:
    projection = get_capability_projection()
    by_id = {capability.capability_id: capability for capability in projection.capabilities}

    assert "action.draft_book_intent" in by_id
    assert "action.approve_book_intent" in by_id
    assert "action.create_book_from_intent" in by_id
    assert "query.book_intents" in by_id
    assert "query.book_intent" in by_id
    assert "gap.book_intent.synopsis" not in by_id
    assert by_id["action.create_book_from_intent"].mutation_class == "canonical_mutation"
    assert by_id["action.draft_book_intent"].produced_artifact_statuses == ["provisional"]


def test_cli_parses_book_intent_commands() -> None:
    parser = build_parser()

    draft_args = parser.parse_args(
        [
            "book",
            "intent",
            "draft",
            "--title",
            "Clockwork Moon",
            "--book-id",
            "clockwork_moon",
            "--author-ref",
            "eldrik-vale/v1",
            "--genre",
            "fantasy",
            "--seed-text",
            "seed",
            "--json",
        ]
    )
    create_args = parser.parse_args(["book", "intent", "create", "--intent", "clockwork_moon_1", "--json"])

    assert draft_args.book_command == "intent"
    assert draft_args.book_intent_command == "draft"
    assert create_args.book_intent_command == "create"
