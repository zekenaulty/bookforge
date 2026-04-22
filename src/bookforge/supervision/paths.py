from __future__ import annotations

from pathlib import Path

from bookforge.contracts import BRANCH_MANIFEST_FILENAME, CURRENT_NODE_FILENAME, MAIN_BRANCH_ID


STATE_SURFACE_LATEST_FILENAME = "state_surface_latest.json"
STATE_SURFACE_HISTORY_FILENAME = "state_surface_history.jsonl"
ISSUES_LATEST_FILENAME = "issues_latest.json"
ISSUES_HISTORY_FILENAME = "issues_history.jsonl"
EXECUTION_RESULTS_FILENAME = "execution_results.jsonl"


def supervision_root(book_root: Path) -> Path:
    return book_root / "runtime" / "supervision"


def branch_root(book_root: Path) -> Path:
    return supervision_root(book_root) / "branches"


def branch_dir(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    cleaned = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if cleaned == MAIN_BRANCH_ID:
        return supervision_root(book_root) / MAIN_BRANCH_ID
    return branch_root(book_root) / cleaned


def current_node_path(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    return branch_dir(book_root, branch_id) / CURRENT_NODE_FILENAME


def branch_manifest_path(book_root: Path, branch_id: str) -> Path:
    return branch_dir(book_root, branch_id) / BRANCH_MANIFEST_FILENAME


def state_surface_latest_path(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    return branch_dir(book_root, branch_id) / STATE_SURFACE_LATEST_FILENAME


def state_surface_history_path(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    return branch_dir(book_root, branch_id) / STATE_SURFACE_HISTORY_FILENAME


def issues_latest_path(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    return branch_dir(book_root, branch_id) / ISSUES_LATEST_FILENAME


def issues_history_path(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    return branch_dir(book_root, branch_id) / ISSUES_HISTORY_FILENAME


def execution_results_path(book_root: Path, branch_id: str = MAIN_BRANCH_ID) -> Path:
    return branch_dir(book_root, branch_id) / EXECUTION_RESULTS_FILENAME


def branch_snapshot_root(book_root: Path, branch_id: str) -> Path:
    return branch_dir(book_root, branch_id) / "snapshot"


def branch_snapshot_outline_root(book_root: Path, branch_id: str) -> Path:
    return branch_snapshot_root(book_root, branch_id) / "outline"


def branch_snapshot_state_path(book_root: Path, branch_id: str) -> Path:
    return branch_snapshot_root(book_root, branch_id) / "state.json"
