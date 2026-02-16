from bookforge.phases.outline import get_handler
from bookforge.phases.outline import context as outline_context


def test_outline_phase_handlers_registered() -> None:
    for step_id in outline_context.STEP_ORDER:
        handler = get_handler(step_id)
        assert hasattr(handler, "preprocess")
        assert hasattr(handler, "validate")
        assert hasattr(handler, "handoff_payload")
