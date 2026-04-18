from __future__ import annotations

from bookforge.pipeline.config import _lint_repair_max_passes


def test_default_lint_repair_max_passes_is_eight(monkeypatch) -> None:
    monkeypatch.delenv("BOOKFORGE_LINT_REPAIR_MAX_PASSES", raising=False)
    assert _lint_repair_max_passes() == 8
