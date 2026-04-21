from __future__ import annotations

import json
from pathlib import Path

from bookforge.pipeline.run_logging import _run_progress_path, _write_run_progress


def test_run_progress_path_uses_runs_directory(tmp_path: Path) -> None:
    assert _run_progress_path(tmp_path, "run_20260418_120000") == (
        tmp_path / "logs" / "runs" / "run_20260418_120000.progress.json"
    )


def test_write_run_progress_persists_payload_with_run_metadata(tmp_path: Path) -> None:
    path = _write_run_progress(
        tmp_path,
        "run_20260418_120000",
        {
            "book_id": "veiled_ledger_b1",
            "status": "running",
            "phase": "write",
            "chapter": 1,
            "scene": 2,
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run_20260418_120000"
    assert payload["book_id"] == "veiled_ledger_b1"
    assert payload["status"] == "running"
    assert payload["phase"] == "write"
    assert payload["chapter"] == 1
    assert payload["scene"] == 2
    assert "updated_at" in payload
