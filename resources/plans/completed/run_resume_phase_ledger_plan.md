# Run Resume + Phase Ledger Plan (Prompt-Update Friendly)

Objective
- Allow resuming a run from the last successful phase without redoing earlier phases.
- Allow controlled prompt/template updates between resume attempts (intentional, not accidental).
- Reduce cost and iteration time during debugging while preserving correctness.

Guiding Principles
- Resume is artifact-driven, not state-inference-driven.
- Prompt updates are allowed by design, but must be explicit and logged.
- Integrity checks should surface mismatches early instead of causing silent drift.

Scope
- Applies to the per-scene pipeline: plan -> preflight -> continuity_pack -> write -> repair -> state_repair -> lint -> apply/commit.
- Does not change scene content semantics; only run orchestration and artifact usage.

Non-Goals
- Cross-scene dependency rewrites.
- Automatic “best possible” repair; resume does not invent missing artifacts.

Phase Ledger (new artifact)
Location
- workspace/books/<book>/draft/context/phase_history/chNNN_scNNN.json

Schema (v1)
```
{
  "scene_id": "ch001_sc001",
  "phases": {
    "plan": {
      "status": "success|fail",
      "timestamp": "ISO",
      "artifacts": {
        "prompt": "path",
        "response": "path",
        "scene_card": "path"
      },
      "prompt_hash": "sha256",
      "template_set": {
        "system": "path",
        "phase": "path"
      }
    },
    "write": {
      "status": "success|fail",
      "timestamp": "ISO",
      "artifacts": {
        "prompt": "path",
        "response": "path",
        "prose": "path",
        "state_patch": "path"
      },
      "prompt_hash": "sha256",
      "template_set": {
        "system": "path",
        "phase": "path"
      }
    }
  }
}
```
Notes
- Store prompt_hash and template_set per phase for integrity tracking.
- Store pre_state_hash and pre_state_path for phases that need it (write/repair/state_repair/lint).

Resume Modes
1) Resume default
- Skips phases with status=success and valid artifacts.
- Loads their outputs into the next phase inputs.

2) Resume with prompt updates (explicit)
- Allow prompt/template changes when resuming, but record the delta:
  - prompt_hash_prev, prompt_hash_new, and prompt_update_reason.
- Require a flag, e.g. --resume-allow-prompt-change.

3) Rerun override
- --rerun-from <phase>: discard later phases; recompute from that phase onward.
- --rerun-all: ignore ledger and recompute all phases.

Integrity / Coherency Rules
- If pre_state_hash mismatch is detected for a phase resume, do not resume that phase unless --force-resume is set.
- If required artifacts are missing, fall back to rerun from the missing phase.
- If template paths are missing or changed and --resume-allow-prompt-change is not set, fail fast with a clear error.

Prompt Update Policy (explicitly allowed)
Allowed changes:
- Template file content changes.
- System prompt changes.
- Book override template updates.

Required metadata when prompt changes:
- Reason string (user-supplied).
- Old and new prompt hashes.

Not allowed without override:
- Skipping required phases because a new prompt might affect earlier outputs (e.g. skipping write after system prompt change).

Artifacts Required per Phase (minimum)
- plan: scene_card
- preflight: patch + updated state snapshot (if produced)
- continuity_pack: pack file + prompt hash
- write: prose + patch + prompt hash
- repair: prose + patch + prompt hash
- state_repair: patch + prompt hash
- lint: report + prompt hash
- apply/commit: post_state snapshot + registry snapshots

Implementation Steps
1) Add phase history directory creation to workspace init/reset.
2) Add phase ledger write utility (append/merge).
3) Add resume loader that:
   - Validates artifacts and prompt hashes.
   - Injects outputs into phase inputs.
4) Add CLI flags:
   - --resume
   - --resume-allow-prompt-change
   - --rerun-from <phase>
   - --rerun-all
5) Add prompt hash computation for each phase.
6) Add guardrails (hash mismatch, missing artifacts, forced rerun).

Edge Cases to Cover
- Repair/state_repair output exists but lint failed previously.
- Prompt change after write: must rerun repair/state_repair/lint unless forced.
- Manual edits of prose/state_patch: detect via hash mismatch and require --force-resume.
- Retry loops should not append duplicate ledger entries; update in place by phase.

Definition of Done
- A run can resume from any successful phase without rerunning earlier phases.
- Prompt updates are supported via explicit flag and logged with hash deltas.
- Missing artifacts or hash mismatches cause a clear rerun requirement.
- Ledger artifacts exist per scene with phase outputs and prompt hashes.

Testing Plan
- Simulate a scene run, stop after write, resume at repair.
- Change a prompt and resume with and without --resume-allow-prompt-change.
- Delete a required artifact and verify fallback rerun.

Reset Handling
- Verify reset clears phase_history artifacts (or archives them) to avoid resuming from stale runs.
- If reset already wipes draft context, explicitly confirm phase_history is included.
