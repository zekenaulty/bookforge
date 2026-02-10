# Runner Phase Lift Plan (Low Risk)

## Goal
Lift-and-shift phase functions out of `runner.py` with no logic changes. Avoid new abstractions. Keep orchestration flow identical.

## Constraints
- No logic changes, no signature changes, no new data models.
- Only move code + update imports.
- Avoid circular imports by extracting only minimal shared helpers.
- Run tests after each phase move.

## Status
- Phase 0: complete
- Phase 1: complete
- Phase 2: complete
- Phase 3: complete
- Phase 4: complete
- Phase 5: complete
- Phase 6: complete

## Phase 0: Prep (Low Risk)
**Create:** `src/bookforge/pipeline/log.py`
**Move as-is:**
- `_status`
- `_now_iso` (if referenced by moved phases)

**Runner changes:** import from `pipeline.log`.
**Tests:** full suite.

## Phase 1: Preflight Phase
**New module:** `src/bookforge/phases/preflight_phase.py`
**Move as-is:**
- `_scene_state_preflight`

**Runner changes:** import `_scene_state_preflight` from `phases.preflight_phase`.
**Tests:** full suite.

## Phase 2: Continuity Phase
**New module:** `src/bookforge/phases/continuity_phase.py`
**Move as-is:**
- `_generate_continuity_pack`

**Runner changes:** import from `phases.continuity_phase`.
**Tests:** full suite.

## Phase 3: Write Phase
**New module:** `src/bookforge/phases/write_phase.py`
**Move as-is:**
- `_write_scene`

**Runner changes:** import from `phases.write_phase`.
**Tests:** full suite.

## Phase 4: Repair Phase
**New module:** `src/bookforge/phases/repair_phase.py`
**Move as-is:**
- `_repair_scene`

**Runner changes:** import from `phases.repair_phase`.
**Tests:** full suite.

## Phase 5: State Repair Phase
**New module:** `src/bookforge/phases/state_repair_phase.py`
**Move as-is:**
- `_state_repair`

**Runner changes:** import from `phases.state_repair_phase`.
**Tests:** full suite.

## Phase 6: Lint Phase
**New module:** `src/bookforge/phases/lint_phase.py`
**Move as-is:**
- `_lint_scene`

**Runner changes:** import from `phases.lint_phase`.
**Tests:** full suite.

## Definition of Done
- `runner.py` contains orchestration only.
- All moved phase functions live under `src/bookforge/phases/`.
- Tests pass after each phase.

## Phase 1 Notes
- Added src/bookforge/pipeline/log.py and imported _status/_now_iso in runner.
- Moved _scene_cast_ids_from_outline, _load_character_states, _normalize_continuity_pack, _parse_until into src/bookforge/pipeline/scene.py (prep for phase lifts).
- Tests: pytest -q (96 passed).


## Phase 2 Notes
- Moved _scene_state_preflight to src/bookforge/phases/preflight_phase.py (no logic changes).
- Tests: pytest -q (96 passed).


## Phase 3 Notes
- Moved _generate_continuity_pack to src/bookforge/phases/continuity_phase.py (no logic changes).
- Tests: pytest -q (96 passed).


## Phase 4 Notes
- Moved _write_scene to src/bookforge/phases/write_phase.py (no logic changes).
- Tests: pytest -q (96 passed).


## Phase 5 Notes
- Moved _repair_scene to src/bookforge/phases/repair_phase.py (no logic changes).
- Tests: pytest -q (96 passed).


## Phase 6 Notes
- Moved _state_repair to src/bookforge/phases/state_repair_phase.py (no logic changes).
- Tests: pytest -q (96 passed).


## Phase 7 Notes
- Moved _lint_scene to src/bookforge/phases/lint_phase.py (no logic changes).
- Added src/bookforge/pipeline/continuity.py for _global_continuity_stats.
- Added src/bookforge/pipeline/lint/helpers.py and updated pipeline/lint/__init__.py exports.
- Tests: pytest -q (96 passed).

