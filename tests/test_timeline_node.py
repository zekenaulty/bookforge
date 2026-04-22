import pytest

from bookforge.contracts import ScopeSelector, TimelineNodeRef


def test_timeline_node_round_trip() -> None:
    node = TimelineNodeRef(
        book_id="veiled_ledger_b1",
        workflow_family="section_write",
        source_run_id="20260419_050005",
        branch_id="main",
        fork_group_id=None,
        chapter=3,
        section=2,
        scene=5,
        phase_id="write",
        turn_id="t2",
        revision_id="r000123",
    )

    restored = TimelineNodeRef.from_dict(node.to_dict())

    assert restored == node


def test_timeline_node_requires_known_workflow_family() -> None:
    with pytest.raises(ValueError, match="Unknown workflow_family"):
        TimelineNodeRef(
            book_id="veiled_ledger_b1",
            workflow_family="outlineish",
            source_run_id="20260419_050005",
            branch_id="main",
            revision_id="r1",
        )


def test_timeline_node_requires_chapter_for_section() -> None:
    with pytest.raises(ValueError, match="section requires chapter"):
        TimelineNodeRef(
            book_id="veiled_ledger_b1",
            workflow_family="section_write",
            source_run_id="20260419_050005",
            branch_id="main",
            section=2,
            revision_id="r1",
        )


def test_scope_selector_round_trip() -> None:
    selector = ScopeSelector(
        book_id="veiled_ledger_b1",
        branch_id="section-repair-001",
        fork_group_id="fork-abc",
        workflow_family="section_local_outline",
        chapter=3,
        section=2,
        scene=5,
        phase_id="phase_04d_seam_hygiene",
        turn_id="t1",
    )

    restored = ScopeSelector.from_dict(selector.to_dict())

    assert restored == selector
    assert selector.is_book_root() is False


def test_scope_selector_book_root_detection() -> None:
    selector = ScopeSelector(book_id="veiled_ledger_b1")
    assert selector.is_book_root() is True


def test_scope_selector_requires_known_workflow_family() -> None:
    with pytest.raises(ValueError, match="Unknown workflow_family"):
        ScopeSelector(book_id="veiled_ledger_b1", workflow_family="hybrid")
