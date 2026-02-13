# Directory Snapshot

```plaintext
- prompt_template_composition_forensics_20260213_183000/
  - change_matrix.md
  - duplicate_lines_report.json
  - index.md
  - prompt_code_touchpoints.json
  - snapshot_manifest.json
  - artifacts/
    - appearance_projection.md.forensic_plan.md
    - author_generate.md.forensic_plan.md
    - characters_generate.md.forensic_plan.md
    - continuity_pack.md.forensic_plan.md
    - lint.md.forensic_plan.md
    - outline.md.forensic_plan.md
    - output_contract.md.forensic_plan.md
    - plan.md.forensic_plan.md
    - preflight.md.forensic_plan.md
    - repair.md.forensic_plan.md
    - state_repair.md.forensic_plan.md
    - style_anchor.md.forensic_plan.md
    - system_base.md.forensic_plan.md
    - write.md.forensic_plan.md
  - proposed_refactor_v1/
    - compiled_manifest_index.json
    - SOURCE_OF_TRUTH.md
    - compiled/
      - appearance_projection.md
      - author_generate.md
      - characters_generate.md
      - continuity_pack.md
      - lint.md
      - outline.md
      - output_contract.md
      - plan.md
      - preflight.md
      - repair.md
      - state_repair.md
      - style_anchor.md
      - system_base.md
      - write.md
    - fragments/
      - phase/
        - appearance_projection/
          - seg_01.md
        - author_generate/
          - seg_01.md
        - characters_generate/
          - seg_01.md
        - continuity_pack/
          - seg_01.md
        - lint/
          - seg_01.md
        - outline/
          - seg_01.md
        - output_contract/
          - seg_01.md
        - plan/
          - seg_01.md
        - preflight/
          - seg_01.md
          - seg_02.md
          - seg_03.md
          - seg_04.md
        - repair/
          - seg_01.md
          - seg_02.md
          - seg_03.md
          - seg_04.md
          - seg_05.md
          - seg_06.md
          - seg_07.md
        - state_repair/
          - seg_01.md
          - seg_02.md
          - seg_03.md
          - seg_04.md
          - seg_05.md
        - style_anchor/
          - seg_01.md
        - system_base/
          - seg_01.md
        - write/
          - seg_01.md
          - seg_02.md
          - seg_03.md
          - seg_04.md
          - seg_05.md
          - seg_06.md
          - seg_07.md
      - shared/
        - B001.must_stay_true_end_truth_line.md
        - B002.must_stay_true_reconciliation_block.md
        - B003.must_stay_true_remove_block.md
        - B004.scope_override_nonreal_rule.md
        - B005.json_contract_block.md
        - B006.global_continuity_array_guardrail.md
        - B007.transfer_registry_conflict_rule.md
        - B008a.appearance_updates_object_under_character_updates.md
        - B008b.appearance_updates_not_array.md
    - manifests/
      - appearance_projection.md.manifest.json
      - author_generate.md.manifest.json
      - characters_generate.md.manifest.json
      - continuity_pack.md.manifest.json
      - lint.md.manifest.json
      - outline.md.manifest.json
      - output_contract.md.manifest.json
      - plan.md.manifest.json
      - preflight.md.manifest.json
      - repair.md.manifest.json
      - state_repair.md.manifest.json
      - style_anchor.md.manifest.json
      - system_base.md.manifest.json
      - write.md.manifest.json
    - reports/
      - appearance_projection.md.change_map.md
      - author_generate.md.change_map.md
      - characters_generate.md.change_map.md
      - continuity_pack.md.change_map.md
      - lint.md.change_map.md
      - outline.md.change_map.md
      - output_contract.md.change_map.md
      - plan.md.change_map.md
      - preflight.md.change_map.md
      - repair.md.change_map.md
      - reuse_index.md
      - stability_controls.md
      - state_repair.md.change_map.md
      - style_anchor.md.change_map.md
      - system_base.md.change_map.md
      - write.md.change_map.md
  - snapshots/
    - appearance_projection.md.snapshot.md
    - author_generate.md.snapshot.md
    - characters_generate.md.snapshot.md
    - continuity_pack.md.snapshot.md
    - lint.md.snapshot.md
    - outline.md.snapshot.md
    - output_contract.md.snapshot.md
    - plan.md.snapshot.md
    - preflight.md.snapshot.md
    - repair.md.snapshot.md
    - state_repair.md.snapshot.md
    - style_anchor.md.snapshot.md
    - system_base.md.snapshot.md
    - write.md.snapshot.md
```

## change_matrix.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\change_matrix.md`

```plaintext
﻿# Prompt Composition Change Matrix (20260213_183000)

| Prompt | Risk | Primary Consumer | Planned Text Delta | Detailed Artifact |
|---|---|---|---|---|
| `appearance_projection.md` | Medium | `src/bookforge/characters.py:317` | None (phase-local block extraction only) | `artifacts/appearance_projection.md.forensic_plan.md` |
| `author_generate.md` | Low | `src/bookforge/author.py:21` | None | `artifacts/author_generate.md.forensic_plan.md` |
| `characters_generate.md` | Medium | `src/bookforge/characters.py:658` | None (initial pass) | `artifacts/characters_generate.md.forensic_plan.md` |
| `continuity_pack.md` | Medium | `src/bookforge/phases/continuity_phase.py:31` | None (initial pass) | `artifacts/continuity_pack.md.forensic_plan.md` |
| `lint.md` | High | `src/bookforge/phases/lint_phase.py:239` | None in pass 1; optional structured extraction pass 2 | `artifacts/lint.md.forensic_plan.md` |
| `outline.md` | Medium | `src/bookforge/outline.py:367-370` | None (initial pass) | `artifacts/outline.md.forensic_plan.md` |
| `output_contract.md` | High | `src/bookforge/workspace.py:303,347` | None in pass 1 | `artifacts/output_contract.md.forensic_plan.md` |
| `plan.md` | High | `src/bookforge/phases/plan.py:65-68` | None in pass 1 | `artifacts/plan.md.forensic_plan.md` |
| `preflight.md` | High | `src/bookforge/phases/preflight_phase.py:32` | Shared-block extraction only; no language change | `artifacts/preflight.md.forensic_plan.md` |
| `repair.md` | Critical | `src/bookforge/phases/repair_phase.py:35` | Deduplicate repeated reconciliation blocks; no policy semantic change | `artifacts/repair.md.forensic_plan.md` |
| `state_repair.md` | Critical | `src/bookforge/phases/state_repair_phase.py:37` | Shared-block extraction only; no language change | `artifacts/state_repair.md.forensic_plan.md` |
| `style_anchor.md` | Medium | `src/bookforge/runner.py:372` | None | `artifacts/style_anchor.md.forensic_plan.md` |
| `system_base.md` | Critical | `src/bookforge/workspace.py:302,346` | None in pass 1 | `artifacts/system_base.md.forensic_plan.md` |
| `write.md` | Critical | `src/bookforge/phases/write_phase.py:35` | Deduplicate repeated `must_stay_true` line; preserve all core rules | `artifacts/write.md.forensic_plan.md` |

## Notes
- "None" means no semantic text change; only migration to composition-managed source blocks.
- Deduplication actions are explicitly listed in each high-risk artifact with span-level citations.

```

## duplicate_lines_report.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\duplicate_lines_report.json`

```plaintext
﻿[
    {
        "Prompt":  "appearance_projection.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "author_generate.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "characters_generate.md",
        "DuplicateCount":  2,
        "Duplicates":  [
                           {
                               "Text":  "      },",
                               "Count":  3,
                               "Lines":  "99,120,126"
                           },
                           {
                               "Text":  "      ],",
                               "Count":  2,
                               "Lines":  "129,132"
                           }
                       ]
    },
    {
        "Prompt":  "continuity_pack.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "lint.md",
        "DuplicateCount":  3,
        "Duplicates":  [
                           {
                               "Text":  "}",
                               "Count":  2,
                               "Lines":  "79,88"
                           },
                           {
                               "Text":  "  \"schema_version\": \"1.0\",",
                               "Count":  2,
                               "Lines":  "76,83"
                           },
                           {
                               "Text":  "{",
                               "Count":  2,
                               "Lines":  "75,82"
                           }
                       ]
    },
    {
        "Prompt":  "outline.md",
        "DuplicateCount":  18,
        "Duplicates":  [
                           {
                               "Text":  "{",
                               "Count":  3,
                               "Lines":  "78,87,97"
                           },
                           {
                               "Text":  "}",
                               "Count":  3,
                               "Lines":  "84,91,145"
                           },
                           {
                               "Text":  "          \"intent\": \"\",",
                               "Count":  2,
                               "Lines":  "112,131"
                           },
                           {
                               "Text":  "          \"scenes\": [",
                               "Count":  2,
                               "Lines":  "113,132"
                           },
                           {
                               "Text":  "          \"section_id\": 1,",
                               "Count":  2,
                               "Lines":  "110,129"
                           },
                           {
                               "Text":  "          \"title\": \"\",",
                               "Count":  2,
                               "Lines":  "111,130"
                           },
                           {
                               "Text":  "      ]",
                               "Count":  2,
                               "Lines":  "117,136"
                           },
                           {
                               "Text":  "  ],",
                               "Count":  2,
                               "Lines":  "138,141"
                           },
                           {
                               "Text":  "          ]",
                               "Count":  2,
                               "Lines":  "115,134"
                           },
                           {
                               "Text":  "        }",
                               "Count":  2,
                               "Lines":  "116,135"
                           },
                           {
                               "Text":  "      \"title\": \"\",",
                               "Count":  2,
                               "Lines":  "102,121"
                           },
                           {
                               "Text":  "      \"goal\": \"\",",
                               "Count":  2,
                               "Lines":  "103,122"
                           },
                           {
                               "Text":  "- title",
                               "Count":  2,
                               "Lines":  "48,58"
                           },
                           {
                               "Text":  "    {",
                               "Count":  2,
                               "Lines":  "100,119"
                           },
                           {
                               "Text":  "      \"sections\": [",
                               "Count":  2,
                               "Lines":  "108,127"
                           },
                           {
                               "Text":  "        {",
                               "Count":  2,
                               "Lines":  "109,128"
                           },
                           {
                               "Text":  "      \"stakes_shift\": \"\",",
                               "Count":  2,
                               "Lines":  "105,124"
                           },
                           {
                               "Text":  "      \"bridge\": {\"from_prev\": \"\", \"to_next\": \"\"},",
                               "Count":  2,
                               "Lines":  "106,125"
                           }
                       ]
    },
    {
        "Prompt":  "output_contract.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "plan.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "preflight.md",
        "DuplicateCount":  4,
        "Duplicates":  [
                           {
                               "Text":  "    }",
                               "Count":  3,
                               "Lines":  "192,203,212"
                           },
                           {
                               "Text":  "  ],",
                               "Count":  3,
                               "Lines":  "193,204,213"
                           },
                           {
                               "Text":  "    {",
                               "Count":  3,
                               "Lines":  "183,195,207"
                           },
                           {
                               "Text":  "      \"character_id\": \"CHAR_example\",",
                               "Count":  3,
                               "Lines":  "184,196,208"
                           }
                       ]
    },
    {
        "Prompt":  "repair.md",
        "DuplicateCount":  4,
        "Duplicates":  [
                           {
                               "Text":  "  - Remove conflicting old invariants rather than preserving them.",
                               "Count":  10,
                               "Lines":  "10,58,63,68,85,90,111,137,192,197"
                           },
                           {
                               "Text":  "  - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.",
                               "Count":  10,
                               "Lines":  "9,57,62,67,84,89,110,136,191,196"
                           },
                           {
                               "Text":  "- must_stay_true reconciliation (mandatory):",
                               "Count":  10,
                               "Lines":  "8,55,60,65,82,87,108,134,189,194"
                           },
                           {
                               "Text":  "    - VALID: \"appearance_updates\": {\"set\": {\"marks_add\": [{\"name\": \"Singed Hair\", \"location\": \"head\", \"durability\": \"durable\"}]}, \"reason\": \"...\"}",
                               "Count":  2,
                               "Lines":  "140,176"
                           }
                       ]
    },
    {
        "Prompt":  "state_repair.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "style_anchor.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "system_base.md",
        "DuplicateCount":  0,
        "Duplicates":  [

                       ]
    },
    {
        "Prompt":  "write.md",
        "DuplicateCount":  2,
        "Duplicates":  [
                           {
                               "Text":  "- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.",
                               "Count":  11,
                               "Lines":  "11,24,65,68,71,81,105,155,158,194,197"
                           },
                           {
                               "Text":  "    - VALID: \"appearance_updates\": {\"set\": {\"marks_add\": [{\"name\": \"Singed Hair\", \"location\": \"head\", \"durability\": \"durable\"}]}, \"reason\": \"...\"}",
                               "Count":  2,
                               "Lines":  "109,142"
                           }
                       ]
    }
]

```

## index.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\index.md`

```plaintext
﻿# Prompt Composition Forensic Index (20260213_183000)

## Objective
Produce a forensic-grade planning package for prompt-template composition that is safe against semantic drift.

This package provides, for **every prompt template**:
- A full numbered snapshot with hash
- Code touchpoints with source-line citations
- A prompt-specific change plan with line spans and replacement language strategy

## Folder Layout
- `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshot_manifest.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/prompt_code_touchpoints.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/duplicate_lines_report.json`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/*.snapshot.md`
- `resources/plans/prompt_template_composition_forensics_20260213_183000/artifacts/*.forensic_plan.md`

## Composition Architecture (Planned)
- Source blocks: `resources/prompt_blocks/**`
- Phase manifests: `resources/prompt_composition/**`
- Generated outputs remain flat: `resources/prompt_templates/*.md`
- Runtime remains unchanged: phases still load single flat files.

## Canonical Shared Blocks (Planned Introductions)
These are planned source blocks used to replace duplicated spans while preserving language.

### `B001.must_stay_true_end_truth_line`
- Canonical source: `resources/prompt_templates/write.md:11`
- Text:
```text
- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
```
- Duplicate spans currently: `resources/prompt_templates/write.md:24,65,68,71,81,105,155,158,194,197`

### `B002.must_stay_true_reconciliation_block`
- Canonical source: `resources/prompt_templates/repair.md:8-10`
- Text:
```text
- must_stay_true reconciliation (mandatory):
  - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - Remove conflicting old invariants rather than preserving them.
```
- Duplicate spans currently: `resources/prompt_templates/repair.md:55-58,60-63,65-68,82-85,87-90,108-111,134-137,189-192,194-197`

### `B003.must_stay_true_remove_block`
- Canonical source: `resources/prompt_templates/write.md:12-15`
- Text:
```text
- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
```

### `B004.scope_override_nonreal_rule`
- Canonical source: `resources/prompt_templates/write.md:59-62`
- Equivalent spans also in:
  - `resources/prompt_templates/preflight.md:23-26`
  - `resources/prompt_templates/repair.md:71-74`
  - `resources/prompt_templates/state_repair.md:119-122`
- Text retained per phase with no semantic change.

### `B005.json_contract_block`
- Canonical source candidate: `resources/prompt_templates/write.md:215-233`
- Equivalent blocks in:
  - `resources/prompt_templates/preflight.md:135-153`
  - `resources/prompt_templates/repair.md:233-251`
  - `resources/prompt_templates/state_repair.md:163-181`

### `B006.global_continuity_array_guardrail`
- Canonical source: `resources/prompt_templates/write.md:91-93`
- Equivalent spans in:
  - `resources/prompt_templates/preflight.md:99-101`
  - `resources/prompt_templates/repair.md:120-122`
  - `resources/prompt_templates/state_repair.md:68-70`
  - `resources/prompt_templates/output_contract.md:19-21`

### `B007.transfer_registry_conflict_rule`
- Canonical source family:
  - `resources/prompt_templates/write.md:127-130`
  - `resources/prompt_templates/preflight.md:115-118`
  - `resources/prompt_templates/repair.md:158-161`
  - `resources/prompt_templates/state_repair.md:103-106`
- Note: multiple prompts currently contain line-wrap/concatenation artifacts in this region; composition pass must preserve current behavior unless explicitly approved to normalize text.

### `B008.appearance_updates_object_guardrail`
- Canonical source family:
  - `resources/prompt_templates/write.md:107-109` and `140-142`
  - `resources/prompt_templates/repair.md:138-140` and `174-176`
  - `resources/prompt_templates/state_repair.md:83-85`

## Code Coupling Map (Critical)
- Template distribution and prompt assembly:
  - `src/bookforge/workspace.py:41-53`
  - `src/bookforge/workspace.py:203-213`
- Runtime template resolution:
  - `src/bookforge/pipeline/prompts.py:40-44`
  - `src/bookforge/phases/plan.py:65-68`
  - `src/bookforge/outline.py:367-370`
- System prompt assembly:
  - `src/bookforge/workspace.py:302-303`
  - `src/bookforge/workspace.py:346-347`
  - `src/bookforge/prompt/system.py:8-24`
- JSON/contract-sensitive consumers:
  - Write parse/validation: `src/bookforge/pipeline/parse.py:70-88`, `src/bookforge/phases/write_phase.py:73-125`
  - Lint parse/normalization/tripwires: `src/bookforge/phases/lint_phase.py:309-341`, `src/bookforge/pipeline/lint/tripwires.py:29-260`
  - Preflight/state application: `src/bookforge/phases/preflight_phase.py:32-71`, `src/bookforge/runner.py:604-639`

## Prompt Artifact Inventory
- `appearance_projection.md.forensic_plan.md`
- `author_generate.md.forensic_plan.md`
- `characters_generate.md.forensic_plan.md`
- `continuity_pack.md.forensic_plan.md`
- `lint.md.forensic_plan.md`
- `outline.md.forensic_plan.md`
- `output_contract.md.forensic_plan.md`
- `plan.md.forensic_plan.md`
- `preflight.md.forensic_plan.md`
- `repair.md.forensic_plan.md`
- `state_repair.md.forensic_plan.md`
- `style_anchor.md.forensic_plan.md`
- `system_base.md.forensic_plan.md`
- `write.md.forensic_plan.md`

## Review Workflow
1. Review each `snapshots/*.snapshot.md` file for exact current text.
2. Review each `artifacts/*.forensic_plan.md` file for span-level proposed operations.
3. Approve or reject operations per prompt.
4. Only after approval: execute composition implementation and generated-template migration.

## Status
- Snapshot capture: `completed`
- Code touchpoint mapping: `completed`
- Per-prompt forensic plans: `in_progress`
- External review package readiness: `in_progress`

```

## prompt_code_touchpoints.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\prompt_code_touchpoints.json`

```plaintext
﻿{
    "output_contract.md":  [
                               "src/bookforge\\workspace.py:53:    \"output_contract.md\",",
                               "src/bookforge\\workspace.py:303:    output_contract = _read_text(book_root / \"prompts\" / \"templates\" / \"output_contract.md\")",
                               "src/bookforge\\workspace.py:347:        output_contract = _read_text(book_root / \"prompts\" / \"templates\" / \"output_contract.md\")"
                           ],
    "author_generate.md":  "src/bookforge\\author.py:21:AUTHOR_TEMPLATE = repo_root(Path(__file__).resolve()) / \u0027resources\u0027 / \u0027prompt_templates\u0027 / \u0027author_generate.md\u0027",
    "appearance_projection.md":  "src/bookforge\\characters.py:317:    template = _resolve_template(book_root, \"appearance_projection.md\")",
    "preflight.md":  [
                         "src/bookforge\\workspace.py:44:    \"preflight.md\",",
                         "src/bookforge\\phases\\preflight_phase.py:32:    preflight_template = _resolve_template(book_root, \"preflight.md\")"
                     ],
    "state_repair.md":  [
                            "src/bookforge\\workspace.py:48:    \"state_repair.md\",",
                            "src/bookforge\\phases\\state_repair_phase.py:37:    template = _resolve_template(book_root, \"state_repair.md\")"
                        ],
    "lint.md":  [
                    "src/bookforge\\workspace.py:46:    \"lint.md\",",
                    "src/bookforge\\phases\\lint_phase.py:239:    template = _resolve_template(book_root, \"lint.md\")"
                ],
    "style_anchor.md":  [
                            "src/bookforge\\workspace.py:51:    \"style_anchor.md\",",
                            "src/bookforge\\runner.py:372:    template = _resolve_template(book_root, \"style_anchor.md\")",
                            "src/bookforge\\memory\\continuity.py:79:    return book_root / \"prompts\" / \"style_anchor.md\""
                        ],
    "write.md":  [
                     "src/bookforge\\workspace.py:45:    \"write.md\",",
                     "src/bookforge\\phases\\write_phase.py:35:    template = _resolve_template(book_root, \"write.md\")"
                 ],
    "repair.md":  [
                      "src/bookforge\\workspace.py:47:    \"repair.md\",",
                      "src/bookforge\\workspace.py:48:    \"state_repair.md\",",
                      "src/bookforge\\phases\\repair_phase.py:35:    template = _resolve_template(book_root, \"repair.md\")",
                      "src/bookforge\\phases\\state_repair_phase.py:37:    template = _resolve_template(book_root, \"state_repair.md\")"
                  ],
    "system_base.md":  [
                           "src/bookforge\\workspace.py:52:    \"system_base.md\",",
                           "src/bookforge\\workspace.py:302:    base_rules = _read_text(book_root / \"prompts\" / \"templates\" / \"system_base.md\")",
                           "src/bookforge\\workspace.py:346:        base_rules = _read_text(book_root / \"prompts\" / \"templates\" / \"system_base.md\")"
                       ],
    "characters_generate.md":  [
                                   "src/bookforge\\characters.py:658:    template = _resolve_template(book_root, \"characters_generate.md\")",
                                   "src/bookforge\\workspace.py:50:    \"characters_generate.md\","
                               ],
    "plan.md":  [
                    "src/bookforge\\workspace.py:43:    \"plan.md\",",
                    "src/bookforge\\phases\\plan.py:65:    book_template = book_root / \"prompts\" / \"templates\" / \"plan.md\"",
                    "src/bookforge\\phases\\plan.py:68:    return repo_root(Path(__file__).resolve()) / \"resources\" / \"prompt_templates\" / \"plan.md\""
                ],
    "continuity_pack.md":  [
                               "src/bookforge\\workspace.py:49:    \"continuity_pack.md\",",
                               "src/bookforge\\phases\\continuity_phase.py:31:    continuity_template = _resolve_template(book_root, \"continuity_pack.md\")"
                           ],
    "outline.md":  [
                       "src/bookforge\\workspace.py:42:    \"outline.md\",",
                       "src/bookforge\\outline.py:367:    book_template = book_root / \"prompts\" / \"templates\" / \"outline.md\"",
                       "src/bookforge\\outline.py:370:    return repo_root(Path(__file__).resolve()) / \"resources\" / \"prompt_templates\" / \"outline.md\""
                   ]
}

```

## snapshot_manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshot_manifest.json`

```plaintext
﻿[
    {
        "Prompt":  "appearance_projection.md",
        "Source":  "resources/prompt_templates/appearance_projection.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/appearance_projection.md.snapshot.md",
        "SHA256":  "EF863DD5ED891E5B300A56570216752AB98A5E6B6800AE84C302D670FE906E34",
        "Lines":  31,
        "Bytes":  930
    },
    {
        "Prompt":  "author_generate.md",
        "Source":  "resources/prompt_templates/author_generate.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/author_generate.md.snapshot.md",
        "SHA256":  "E87899515FC1F1139FBDAEC81E6237B895E60F6912576EB33B47F5C44039146D",
        "Lines":  51,
        "Bytes":  1278
    },
    {
        "Prompt":  "characters_generate.md",
        "Source":  "resources/prompt_templates/characters_generate.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/characters_generate.md.snapshot.md",
        "SHA256":  "2F2EBE29BFBB7CBE823ED38BF2714E853B0C5FA41F65E47D3CD0217B4A97E85D",
        "Lines":  139,
        "Bytes":  5221
    },
    {
        "Prompt":  "continuity_pack.md",
        "Source":  "resources/prompt_templates/continuity_pack.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/continuity_pack.md.snapshot.md",
        "SHA256":  "F3E97B8B5B5C0139A232DEA15B26A8403975ECAE8D9AE60053D1433EB83CB192",
        "Lines":  52,
        "Bytes":  2176
    },
    {
        "Prompt":  "lint.md",
        "Source":  "resources/prompt_templates/lint.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/lint.md.snapshot.md",
        "SHA256":  "F3B131D17E0E7779FA5A4CA7344DD5A557EF8AFB1D68B6FC75613E503F3A9F0A",
        "Lines":  129,
        "Bytes":  6887
    },
    {
        "Prompt":  "outline.md",
        "Source":  "resources/prompt_templates/outline.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/outline.md.snapshot.md",
        "SHA256":  "5CC31E096D85313344F8030EEF1CBC5CA2539EAE7AD5625E9FF0A3FE31452848",
        "Lines":  157,
        "Bytes":  4747
    },
    {
        "Prompt":  "output_contract.md",
        "Source":  "resources/prompt_templates/output_contract.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/output_contract.md.snapshot.md",
        "SHA256":  "4FDAA9A34FD8B7857B675C366974B3D88CDB816C4CBDF1D0CF5FC69C7D25D5D0",
        "Lines":  21,
        "Bytes":  1959
    },
    {
        "Prompt":  "plan.md",
        "Source":  "resources/prompt_templates/plan.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/plan.md.snapshot.md",
        "SHA256":  "65A7BF57348EDC1596EE9FFD8F8DF87B9D98E5CC08173E15A784773D1980C194",
        "Lines":  91,
        "Bytes":  3604
    },
    {
        "Prompt":  "preflight.md",
        "Source":  "resources/prompt_templates/preflight.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/preflight.md.snapshot.md",
        "SHA256":  "DC967458F32EEC3F55A84C8BFAF2BDC16EFD608824635983A0C3B695E462A88B",
        "Lines":  224,
        "Bytes":  13545
    },
    {
        "Prompt":  "repair.md",
        "Source":  "resources/prompt_templates/repair.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/repair.md.snapshot.md",
        "SHA256":  "57605D83A5197268F33334B45C9E09118994CAD25F4AE3690C14D10F7C44EE72",
        "Lines":  257,
        "Bytes":  18703
    },
    {
        "Prompt":  "state_repair.md",
        "Source":  "resources/prompt_templates/state_repair.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/state_repair.md.snapshot.md",
        "SHA256":  "CDCA594405F79DFE7791B54BD94EC48EECF01036E22870DD0A29B27D509CE68D",
        "Lines":  189,
        "Bytes":  13505
    },
    {
        "Prompt":  "style_anchor.md",
        "Source":  "resources/prompt_templates/style_anchor.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/style_anchor.md.snapshot.md",
        "SHA256":  "1047A314F8AE316FA22A06546BD7CF680262505D35D6CFCDF8E1180971DDE0F1",
        "Lines":  10,
        "Bytes":  365
    },
    {
        "Prompt":  "system_base.md",
        "Source":  "resources/prompt_templates/system_base.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/system_base.md.snapshot.md",
        "SHA256":  "A44785B2F563F06AD7A46DDF71E9AA85C49AECD4C5A82ADB18FBB27010037682",
        "Lines":  29,
        "Bytes":  4114
    },
    {
        "Prompt":  "write.md",
        "Source":  "resources/prompt_templates/write.md",
        "Snapshot":  "resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/write.md.snapshot.md",
        "SHA256":  "898B8FCFA1997DE8C7BCDF0636E462EA52064D627E2257C3DF644725443888F4",
        "Lines":  237,
        "Bytes":  18254
    }
]

```

## artifacts\appearance_projection.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\appearance_projection.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: appearance_projection.md

## Snapshot
- Source: `resources/prompt_templates/appearance_projection.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/appearance_projection.md.snapshot.md`
- SHA256: `EF863DD5ED891E5B300A56570216752AB98A5E6B6800AE84C302D670FE906E34`
- Line count: `31`
- Byte length: `930`

## Code Touchpoints
- `src/bookforge\characters.py:317:    template = _resolve_template(book_root, "appearance_projection.md")`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/appearance_projection.md:1-31`
  - Proposed replacement surface: `resources/prompt_blocks/phase/appearance_projection.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.

```

## artifacts\author_generate.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\author_generate.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: author_generate.md

## Snapshot
- Source: `resources/prompt_templates/author_generate.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/author_generate.md.snapshot.md`
- SHA256: `E87899515FC1F1139FBDAEC81E6237B895E60F6912576EB33B47F5C44039146D`
- Line count: `51`
- Byte length: `1278`

## Code Touchpoints
- `src/bookforge\author.py:21:AUTHOR_TEMPLATE = repo_root(Path(__file__).resolve()) / 'resources' / 'prompt_templates' / 'author_generate.md'`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/author_generate.md:1-51`
  - Proposed replacement surface: `resources/prompt_blocks/phase/author_generate.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.

```

## artifacts\characters_generate.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\characters_generate.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: characters_generate.md

## Snapshot
- Source: `resources/prompt_templates/characters_generate.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/characters_generate.md.snapshot.md`
- SHA256: `2F2EBE29BFBB7CBE823ED38BF2714E853B0C5FA41F65E47D3CD0217B4A97E85D`
- Line count: `139`
- Byte length: `5221`

## Code Touchpoints
- `src/bookforge\characters.py:658:    template = _resolve_template(book_root, "characters_generate.md")`
- `src/bookforge\workspace.py:50:    "characters_generate.md",`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/characters_generate.md:1-139`
  - Proposed replacement surface: `resources/prompt_blocks/phase/characters_generate.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.

```

## artifacts\continuity_pack.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\continuity_pack.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: continuity_pack.md

## Snapshot
- Source: `resources/prompt_templates/continuity_pack.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/continuity_pack.md.snapshot.md`
- SHA256: `F3E97B8B5B5C0139A232DEA15B26A8403975ECAE8D9AE60053D1433EB83CB192`
- Line count: `52`
- Byte length: `2176`

## Code Touchpoints
- `src/bookforge\workspace.py:49:    "continuity_pack.md",`
- `src/bookforge\phases\continuity_phase.py:31:    continuity_template = _resolve_template(book_root, "continuity_pack.md")`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/continuity_pack.md:1-52`
  - Proposed replacement surface: `resources/prompt_blocks/phase/continuity_pack.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.

```

## artifacts\lint.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\lint.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: lint.md

## Snapshot
- Source: `resources/prompt_templates/lint.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/lint.md.snapshot.md`
- SHA256: `047F798DEB6B553C1F03995D5356C0570B4A6FEE4CB61007E7CB1162C5E8DCBE`
- Line count: `156`
- Byte length: `6887`

## Code Touchpoints
- `src/bookforge/workspace.py:46`
- `src/bookforge/phases/lint_phase.py:239`
- Deterministic lint coupling:
  - `src/bookforge/phases/lint_phase.py:309-341`
  - `src/bookforge/pipeline/lint/tripwires.py:29-260`
  - `src/bookforge/pipeline/lint/helpers.py:10`

## Intent Summary
`lint.md` must stay aligned with deterministic lint add-ons and report normalization. Prompt structure changes can produce false confidence or conflict with enforced single-issue incoherence behavior.

## Detailed Change Plan (Span-Cited)

### Operation L01 - Preserve all policy rules verbatim in first migration pass
- Current span: `resources/prompt_templates/lint.md:1-73`
- Action: keep phase-local block with no semantic edits.

### Operation L02 - Preserve pass/fail JSON example blocks
- Current spans:
  - `resources/prompt_templates/lint.md:75-89`
- Action: keep examples unchanged.
- Note: duplicate braces/schema lines are intentional example pairs, not dedupe targets.

### Operation L03 - Preserve input placeholder block order
- Current span: `resources/prompt_templates/lint.md:91-156`
- Action: keep phase-local and verbatim.
- Coupling rationale:
  - `lint_phase` composes prompt values in this same conceptual order (`src/bookforge/phases/lint_phase.py:247-266`).

### Operation L04 - Optional shared extraction (no semantic delta)
- Candidate shared blocks (optional in first pass):
  - UI gate rule subsection `resources/prompt_templates/lint.md:11-15`
  - prose hygiene subsection `resources/prompt_templates/lint.md:22`
  - pipeline incoherent subsection `resources/prompt_templates/lint.md:44-51`
- Recommendation:
  - Defer extraction until second pass; keep first pass as no-op to avoid behavior drift.

## Proposed Composed Template Layout (Draft)
1. `lint/full_phase_body_v1` (first pass)
2. Optional second-pass split into `lint/policy_*` blocks after behavior lock test.

## Risk & Validation Notes
- Must not diverge from deterministic enforcement already in code (`pipeline_state_incoherent` single-issue clamp in `src/bookforge/phases/lint_phase.py:337-341`).
- Keep issue-code names unchanged to avoid downstream routing/report confusion.

## Reviewer Checklist
- Confirm no rewording in policy statements during pass 1.
- Confirm examples remain valid lint_report schema examples.
- Confirm placeholders remain present and unchanged.

```

## artifacts\outline.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\outline.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: outline.md

## Snapshot
- Source: `resources/prompt_templates/outline.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/outline.md.snapshot.md`
- SHA256: `5CC31E096D85313344F8030EEF1CBC5CA2539EAE7AD5625E9FF0A3FE31452848`
- Line count: `157`
- Byte length: `4747`

## Code Touchpoints
- `src/bookforge\workspace.py:42:    "outline.md",`
- `src/bookforge\outline.py:367:    book_template = book_root / "prompts" / "templates" / "outline.md"`
- `src/bookforge\outline.py:370:    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / "outline.md"`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/outline.md:1-157`
  - Proposed replacement surface: `resources/prompt_blocks/phase/outline.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.

```

## artifacts\output_contract.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\output_contract.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: output_contract.md

## Snapshot
- Source: `resources/prompt_templates/output_contract.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/output_contract.md.snapshot.md`
- SHA256: `1AB0A9DD99C0DB33C0AABFF9439D3877457A07A9230A1A5E3A08099BC1AC33E4`
- Line count: `21`
- Byte length: `1959`

## Code Touchpoints
- `src/bookforge/workspace.py:53`
- `src/bookforge/workspace.py:303`
- `src/bookforge/workspace.py:347`
- System prompt assembly coupling:
  - `src/bookforge/prompt/system.py:8-24`

## Intent Summary
`output_contract.md` defines cross-phase output constraints at system level. It must remain stable and concise.

## Detailed Change Plan (Span-Cited)

### Operation OC01 - Preserve full body exactly
- Current span: `resources/prompt_templates/output_contract.md:1-21`
- Action: move as single block `resources/prompt_blocks/system/output_contract_v1.md`.
- Replacement language: `NO TEXT CHANGE`.

### Operation OC02 - Optional shared extraction
- Candidate span:
  - global continuity array rule: `resources/prompt_templates/output_contract.md:19-21`
- Recommendation: keep local in pass 1 to avoid accidental divergence with system-level contract scope.

## Risk & Validation Notes
- This file is injected into every system prompt; drift here is global.
- Any wording change requires explicit multi-phase regression review.

## Reviewer Checklist
- Confirm composed output exactly matches source text.
- Confirm system prompt generation still includes this section unchanged.

```

## artifacts\plan.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\plan.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: plan.md

## Snapshot
- Source: `resources/prompt_templates/plan.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/plan.md.snapshot.md`
- SHA256: `DBA2419A902A4FF9A078EAB1744D4A40E190AE778AA01FE06BC5D5855641942D`
- Line count: `92`
- Byte length: `3604`

## Code Touchpoints
- `src/bookforge/workspace.py:43`
- `src/bookforge/phases/plan.py:65-68`
- Schema and normalization coupling:
  - `src/bookforge/phases/plan.py:24`
  - `src/bookforge/phases/plan.py:335-430`
  - `src/bookforge/phases/plan.py:593`

## Intent Summary
`plan.md` defines scene-card output constraints. It is tightly coupled to `scene_card` schema normalization.

## Detailed Change Plan (Span-Cited)

### Operation P01 - Preserve scene-card JSON contract language exactly
- Current span: `resources/prompt_templates/plan.md:1-92`
- Action: keep as single phase-local block in first pass.
- Replacement language: `NO TEXT CHANGE`.

### Operation P02 - Optional second-pass extraction candidates
- Candidate spans (deferred):
  - ui_allowed contract language (if duplicated elsewhere)
  - output-shape reminder blocks
- Recommendation: defer until after composition baseline is proven stable.

## Risk & Validation Notes
- Any drift can break normalization assumptions in `_normalize_scene_card`.
- Must preserve wording around required/optional fields and cardinality.

## Reviewer Checklist
- Confirm no semantic changes to scene-card required keys/rules.
- Confirm compatibility with `SCENE_CARD_SCHEMA_VERSION` and validation flow.

```

## artifacts\preflight.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\preflight.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: preflight.md

## Snapshot
- Source: `resources/prompt_templates/preflight.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/preflight.md.snapshot.md`
- SHA256: `1275EE1E33A36D57D417B26DBDB413DB6CA691B5EE58F6C55F8E088C2AD9C2FE`
- Line count: `224`
- Byte length: `13545`

## Code Touchpoints
- `src/bookforge/workspace.py:44`
- `src/bookforge/phases/preflight_phase.py:32`
- Runtime coupling:
  - `src/bookforge/phases/preflight_phase.py:36-71`
  - `src/bookforge/runner.py:604-639`
  - `src/bookforge/pipeline/state_patch.py:_sanitize_preflight_patch`

## Intent Summary
`preflight.md` performs initial state alignment and durable mutation gating before write. Composition changes must preserve conservative mutation behavior and scope override logic.

## Detailed Change Plan (Span-Cited)

### Operation PF01 - Preserve preflight role and hard rules section
- Current span: `resources/prompt_templates/preflight.md:1-22`
- Action: keep verbatim (phase-local).

### Operation PF02 - Preserve scope override rule
- Current span: `resources/prompt_templates/preflight.md:23-26`
- Action: extract to `B004.scope_override_nonreal_rule`.

### Operation PF03 - Preserve transition gate logic
- Current span: `resources/prompt_templates/preflight.md:27-42`
- Action: keep phase-local and verbatim.

### Operation PF04 - Preserve world/inventory alignment policy
- Current span: `resources/prompt_templates/preflight.md:43-79`
- Action: keep phase-local and verbatim.

### Operation PF05 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/preflight.md:99-101`
- Action: extract to `B006.global_continuity_array_guardrail`.

### Operation PF06 - Preserve transfer-vs-registry conflict block
- Current span: `resources/prompt_templates/preflight.md:115-118`
- Action: extract to `B007.transfer_registry_conflict_rule`.
- Caution:
  - `resources/prompt_templates/preflight.md:118` includes concatenated suffix (`- Safety check...`).
  - Preserve exact text first pass; normalization is a separate approved pass.

### Operation PF07 - Preserve JSON Contract Block
- Current span: `resources/prompt_templates/preflight.md:135-153`
- Action: extract to `B005.json_contract_block`.

### Operation PF08 - Preserve example output block
- Current span: `resources/prompt_templates/preflight.md:179-217`
- Action: keep phase-local and verbatim.

## Proposed Composed Template Layout (Draft)
1. `preflight/header_and_hard_rules_v1`
2. `shared/scope_override_nonreal_rule`
3. `preflight/transition_gate_v1`
4. `preflight/inventory_and_constraints_v1`
5. `shared/global_continuity_array_guardrail`
6. `shared/transfer_registry_conflict_rule`
7. `shared/json_contract_block`
8. `preflight/input_placeholders_and_examples_v1`

## Risk & Validation Notes
- Preflight mutations flow directly into runner state apply (`src/bookforge/runner.py:626-633`).
- Wording drift can alter LLM mutation aggressiveness and produce pauses.
- Preserve the exact conservative/continuation heuristics in lines `27-42`.

## Reviewer Checklist
- Verify no change in scope gating language.
- Verify durable mutation block definition remains unchanged.
- Verify example JSON remains schema-consistent.

```

## artifacts\repair.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\repair.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: repair.md

## Snapshot
- Source: `resources/prompt_templates/repair.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/repair.md.snapshot.md`
- SHA256: `D5F4DF4FEF7A604A8BD6EF36A4CC0D8DDCF95AA26AD3DBE3A0B8DBA65083DECC`
- Line count: `257`
- Byte length: `18703`

## Code Touchpoints
- `src/bookforge/workspace.py:47`
- `src/bookforge/phases/repair_phase.py:35`
- Parser/contract sensitivity:
  - `src/bookforge/pipeline/parse.py:70-88`
  - `src/bookforge/phases/repair_phase.py:66-125`
  - `src/bookforge/pipeline/state_patch.py:407`

## Intent Summary
`repair.md` is high risk because it can rewrite prose and patch under lint pressure. It must stay tightly aligned with schema constraints and state ownership rules.

## Detailed Change Plan (Span-Cited)

### Operation R01 - Preserve header and primary policy band
- Current span: `resources/prompt_templates/repair.md:1-54`
- Action: retain verbatim as phase-local block.
- New language: `NO TEXT CHANGE`.

### Operation R02 - Dedupe repeated must_stay_true reconciliation blocks
- Canonical source retained: `resources/prompt_templates/repair.md:8-10`
- Duplicate spans to remove:
  - `resources/prompt_templates/repair.md:55-58`
  - `resources/prompt_templates/repair.md:60-63`
  - `resources/prompt_templates/repair.md:65-68`
  - `resources/prompt_templates/repair.md:82-85`
  - `resources/prompt_templates/repair.md:87-90`
  - `resources/prompt_templates/repair.md:108-111`
  - `resources/prompt_templates/repair.md:134-137`
  - `resources/prompt_templates/repair.md:189-192`
  - `resources/prompt_templates/repair.md:194-197`
- Replacement strategy:
  - Keep canonical `B002.must_stay_true_reconciliation_block` once.
  - Remove duplicate copies.
- Canonical replacement text:
```text
- must_stay_true reconciliation (mandatory):
  - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - Remove conflicting old invariants rather than preserving them.
```

### Operation R03 - Preserve must_stay_true removal block
- Current span: `resources/prompt_templates/repair.md:11-14`
- Action: extract to `B003.must_stay_true_remove_block`.
- Replacement in composed output: exact same text.

### Operation R04 - Preserve scope override rule
- Current span: `resources/prompt_templates/repair.md:71-74`
- Action: extract to `B004.scope_override_nonreal_rule`.
- Replacement in composed output: exact same text.

### Operation R05 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/repair.md:120-122`
- Action: extract to `B006.global_continuity_array_guardrail`.

### Operation R06 - Preserve appearance updates object guardrails
- Current spans:
  - `resources/prompt_templates/repair.md:138-140`
  - `resources/prompt_templates/repair.md:174-176`
- Action: extract to `B008.appearance_updates_object_guardrail`.

### Operation R07 - Preserve transfer-vs-registry conflict block
- Current span: `resources/prompt_templates/repair.md:158-166`
- Action: extract to `B007.transfer_registry_conflict_rule`.
- Caution:
  - `resources/prompt_templates/repair.md:161` contains concatenated text due line wrap artifact.
  - Do not normalize wording in first migration pass.

### Operation R08 - Preserve JSON Contract Block
- Current span: `resources/prompt_templates/repair.md:233-251`
- Action: extract to `B005.json_contract_block`.

### Operation R09 - Preserve phase output contract region
- Current spans:
  - `resources/prompt_templates/repair.md:77-99`
  - `resources/prompt_templates/repair.md:101-232`
- Action: keep as phase-local composition blocks with no semantic edits.

## Proposed Composed Template Layout (Draft)
1. `repair/header_and_rules_v1`
2. `shared/must_stay_true_reconciliation_block`
3. `shared/must_stay_true_remove_block`
4. `repair/inventory_and_mechanics_v1`
5. `shared/scope_override_nonreal_rule`
6. `repair/output_contract_v1`
7. `repair/state_patch_rules_v1`
8. `shared/global_continuity_array_guardrail`
9. `shared/appearance_updates_object_guardrail`
10. `shared/transfer_registry_conflict_rule`
11. `shared/json_contract_block`

## Risk & Validation Notes
- Repair parse path must remain valid (`src/bookforge/phases/repair_phase.py:66-125`).
- Do not weaken JSON examples that currently prevent schema retries.
- Deduplication must not remove the only occurrence of any hard rule.

## Reviewer Checklist
- Verify every removed repeated reconciliation block is a duplicate of lines 8-10.
- Verify no unique contextual rule is accidentally removed near deduped spans.
- Confirm composed output remains parse-compatible with `PROSE:` + `STATE_PATCH:` extraction path.

```

## artifacts\state_repair.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\state_repair.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: state_repair.md

## Snapshot
- Source: `resources/prompt_templates/state_repair.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/state_repair.md.snapshot.md`
- SHA256: `8E8A1B56E9DEB467F32D3DDBA28C6DD827E27E50392580F75D7F76166181A010`
- Line count: `189`
- Byte length: `13505`

## Code Touchpoints
- `src/bookforge/workspace.py:48`
- `src/bookforge/phases/state_repair_phase.py:37`
- Parser/contract sensitivity:
  - `src/bookforge/phases/state_repair_phase.py:67-115`
  - `src/bookforge/pipeline/parse.py:_extract_json`
  - `src/bookforge/pipeline/state_patch.py:407`

## Intent Summary
`state_repair.md` is schema-critical. It is the last patch-shape checkpoint before lint and final apply.

## Detailed Change Plan (Span-Cited)

### Operation SR01 - Preserve top-level goal and must_stay_true rules
- Current span: `resources/prompt_templates/state_repair.md:1-18`
- Action: keep verbatim (phase-local).

### Operation SR02 - Preserve durable/ephemeral and UI gate region
- Current span: `resources/prompt_templates/state_repair.md:27-42`
- Action: keep verbatim; do not alter punctuation/keyword casing.

### Operation SR03 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/state_repair.md:68-70`
- Action: extract to `B006.global_continuity_array_guardrail`.

### Operation SR04 - Preserve appearance updates object guardrail
- Current span: `resources/prompt_templates/state_repair.md:83-85`
- Action: extract to `B008.appearance_updates_object_guardrail`.

### Operation SR05 - Preserve transfer-vs-registry conflict block
- Current span: `resources/prompt_templates/state_repair.md:103-111`
- Action: extract to `B007.transfer_registry_conflict_rule`.
- Caution:
  - `resources/prompt_templates/state_repair.md:106` contains concatenated text due formatting artifact; preserve text in first migration pass.

### Operation SR06 - Preserve scope override block
- Current span: `resources/prompt_templates/state_repair.md:119-122`
- Action: extract to `B004.scope_override_nonreal_rule`.

### Operation SR07 - Preserve JSON Contract Block
- Current span: `resources/prompt_templates/state_repair.md:163-181`
- Action: extract to `B005.json_contract_block`.

### Operation SR08 - Preserve all input placeholder sections
- Current span: `resources/prompt_templates/state_repair.md:123-161`
- Action: keep phase-local and verbatim.

## Proposed Composed Template Layout (Draft)
1. `state_repair/header_and_goal_v1`
2. `state_repair/rules_core_v1`
3. `shared/global_continuity_array_guardrail`
4. `shared/appearance_updates_object_guardrail`
5. `shared/transfer_registry_conflict_rule`
6. `shared/scope_override_nonreal_rule`
7. `state_repair/input_placeholders_v1`
8. `shared/json_contract_block`

## Risk & Validation Notes
- Must remain JSON-only output semantics (`src/bookforge/phases/state_repair_phase.py:67-90`).
- Any drift in guardrail examples can reintroduce schema retry churn.
- Keep canonical examples identical on first pass.

## Reviewer Checklist
- Confirm no rule-line loss in ranges `1-122`.
- Confirm all schema examples remain exactly present.
- Confirm composed output still enforces JSON-only output contract.

```

## artifacts\style_anchor.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\style_anchor.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: style_anchor.md

## Snapshot
- Source: `resources/prompt_templates/style_anchor.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/style_anchor.md.snapshot.md`
- SHA256: `1047A314F8AE316FA22A06546BD7CF680262505D35D6CFCDF8E1180971DDE0F1`
- Line count: `10`
- Byte length: `365`

## Code Touchpoints
- `src/bookforge\workspace.py:51:    "style_anchor.md",`
- `src/bookforge\runner.py:372:    template = _resolve_template(book_root, "style_anchor.md")`
- `src/bookforge\memory\continuity.py:79:    return book_root / "prompts" / "style_anchor.md"`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/style_anchor.md:1-10`
  - Proposed replacement surface: `resources/prompt_blocks/phase/style_anchor.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.

```

## artifacts\system_base.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\system_base.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: system_base.md

## Snapshot
- Source: `resources/prompt_templates/system_base.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/system_base.md.snapshot.md`
- SHA256: `DC70F4A84F6FDDDFB491A123D23B26A7CC7AC2B860363178A09B12FA606E862A`
- Line count: `32`
- Byte length: `4114`

## Code Touchpoints
- `src/bookforge/workspace.py:52`
- `src/bookforge/workspace.py:302`
- `src/bookforge/workspace.py:346`
- System prompt assembly:
  - `src/bookforge/prompt/system.py:8-24`

## Intent Summary
`system_base.md` is global authority text merged into `system_v1.md` and therefore affects every phase. Any drift here has highest blast radius.

## Detailed Change Plan (Span-Cited)

### Operation SB01 - Preserve full body exactly (first migration pass)
- Current span: `resources/prompt_templates/system_base.md:1-32`
- Action: move as a single block `resources/prompt_blocks/system/system_base_v1.md`.
- Replacement language: `NO TEXT CHANGE`.

### Operation SB02 - Optional second-pass shared extraction
- Candidate extraction spans (deferred):
  - Prose hygiene rule: `resources/prompt_templates/system_base.md:15`
  - UI gate rule: `resources/prompt_templates/system_base.md:20`
  - JSON contract baseline: `resources/prompt_templates/system_base.md:24-26`
- Recommendation: defer to avoid changing precedence interpretation.

## Coupling Notes
- This text is concatenated as the `## Base Rules` section by `build_system_prompt` (`src/bookforge/prompt/system.py:8-24`).
- It is copied/regenerated via `update_book_templates` (`src/bookforge/workspace.py:333-349`).

## Risk & Validation Notes
- High risk: even punctuation-level edits can alter model priority behavior.
- First pass should be a strict no-op extraction.

## Reviewer Checklist
- Verify no line changes between original and composed output.
- Verify generated `system_v1.md` remains equivalent under same author/constitution inputs.

```

## artifacts\write.md.forensic_plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\artifacts\write.md.forensic_plan.md`

```plaintext
﻿# Forensic Plan: write.md

## Snapshot
- Source: `resources/prompt_templates/write.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/write.md.snapshot.md`
- SHA256: `898B8FCFA1997DE8C7BCDF0636E462EA52064D627E2257C3DF644725443888F4`
- Line count: `237`
- Byte length: `18254`

## Code Touchpoints
- `src/bookforge/workspace.py:45`
- `src/bookforge/phases/write_phase.py:35`
- Parser/contract sensitivity:
  - `src/bookforge/pipeline/parse.py:70-88`
  - `src/bookforge/phases/write_phase.py:73-125`
  - `src/bookforge/pipeline/state_patch.py:407`

## Intent Summary
`write.md` is the highest-risk phase template for composition migration because it drives:
- Prose + patch dual-output formatting
- State patch schema compliance downstream
- Durable mutation rules later enforced by lint/state apply

Any wording drift here can create direct runtime failures.

## Detailed Change Plan (Span-Cited)

### Operation W01 - Keep Core Header and Phase Contract Verbatim
- Current span: `resources/prompt_templates/write.md:1-10`
- Action: move verbatim into phase block `resources/prompt_blocks/phase/write/header_v1.md`
- Replacement in composed output: exact same text.
- New language: `NO TEXT CHANGE`.

### Operation W02 - Dedupe repeated must_stay_true end-truth line
- Canonical source line retained: `resources/prompt_templates/write.md:11`
- Duplicate spans to remove:
  - `resources/prompt_templates/write.md:24`
  - `resources/prompt_templates/write.md:65`
  - `resources/prompt_templates/write.md:68`
  - `resources/prompt_templates/write.md:71`
  - `resources/prompt_templates/write.md:81`
  - `resources/prompt_templates/write.md:105`
  - `resources/prompt_templates/write.md:155`
  - `resources/prompt_templates/write.md:158`
  - `resources/prompt_templates/write.md:194`
  - `resources/prompt_templates/write.md:197`
- Replacement strategy:
  - Keep canonical block `B001.must_stay_true_end_truth_line` once in primary policy section.
  - Delete duplicate occurrences with no replacement text.
- Replacement text (canonical):
```text
- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
```
- Semantic intent: unchanged; redundancy removed.

### Operation W03 - Preserve must_stay_true removal block as shared block
- Current span: `resources/prompt_templates/write.md:12-15`
- Action: extract into shared block `B003.must_stay_true_remove_block`
- Replacement in composed output: exact same text.

### Operation W04 - Preserve inventory posture reconciliation block
- Current span: `resources/prompt_templates/write.md:18-23`
- Action: extract into shared block `resources/prompt_blocks/shared/inventory_posture_reconciliation_v1.md`
- Replacement in composed output: exact same text.

### Operation W05 - Preserve scope override rule as shared block
- Current span: `resources/prompt_templates/write.md:59-62`
- Action: extract into `B004.scope_override_nonreal_rule`
- Replacement in composed output: exact same text.

### Operation W06 - Preserve global continuity array guardrail
- Current span: `resources/prompt_templates/write.md:91-93`
- Action: extract into `B006.global_continuity_array_guardrail`
- Replacement in composed output: exact same text.

### Operation W07 - Preserve transfer-vs-registry rule (known formatting caution)
- Current span: `resources/prompt_templates/write.md:127-135`
- Action: extract into `B007.transfer_registry_conflict_rule`
- Replacement in composed output: exact same text in first migration pass.
- Caution:
  - `resources/prompt_templates/write.md:130` contains a wrapped/concatenated clause.
  - Do not normalize this line in first pass; normalization requires explicit semantic review.

### Operation W08 - Preserve appearance updates object guardrails
- Current spans:
  - `resources/prompt_templates/write.md:107-109`
  - `resources/prompt_templates/write.md:140-142`
- Action: extract to `B008.appearance_updates_object_guardrail`
- Replacement in composed output: exact same text.

### Operation W09 - Preserve JSON Contract Block as shared block
- Current span: `resources/prompt_templates/write.md:215-233`
- Action: extract to `B005.json_contract_block`
- Replacement in composed output: exact same text.

### Operation W10 - Preserve phase-local output shape and placeholders
- Current spans:
  - `resources/prompt_templates/write.md:168-213`
- Action: keep phase-local block (not shared) due strong coupling to write output structure.
- Coupling rationale:
  - Write parser expects prose + `STATE_PATCH` structure (`src/bookforge/pipeline/parse.py:70-88`).

## Proposed Composed Template Layout (Draft)
1. `write/header_v1`
2. `shared/must_stay_true_end_truth_line`
3. `shared/must_stay_true_remove_block`
4. `shared/inventory_posture_reconciliation_v1`
5. `write/durable_ephemeral_and_ui_v1`
6. `write/appearance_and_naming_v1`
7. `shared/scope_override_nonreal_rule`
8. `write/state_patch_rules_core_v1`
9. `shared/global_continuity_array_guardrail`
10. `shared/transfer_registry_conflict_rule`
11. `shared/appearance_updates_object_guardrail`
12. `write/output_blocks_v1`
13. `shared/json_contract_block`

## Risk & Validation Notes
- Must pass unchanged parsing and schema flow in:
  - `src/bookforge/phases/write_phase.py:73-125`
- Must not alter wording that state repair/lint depend on for behavior cues.
- First migration rule: semantic no-op except duplicate line removal.

## Reviewer Checklist
- Confirm all deleted duplicate spans are semantically redundant.
- Confirm no non-duplicate policy sentence was dropped.
- Confirm composed output is byte-equivalent except approved dedupe removals.

```

## proposed_refactor_v1\compiled_manifest_index.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled_manifest_index.json`

```plaintext
﻿[
    {
        "prompt":  "appearance_projection.md",
        "manifest":  "manifests/appearance_projection.md.manifest.json",
        "compiled":  "compiled/appearance_projection.md",
        "compiled_sha256":  "4F34AE9D7BFFB6BEEDC621275439D608DE1AC6C264BFAC2A5A07476F8AAAD92B",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "author_generate.md",
        "manifest":  "manifests/author_generate.md.manifest.json",
        "compiled":  "compiled/author_generate.md",
        "compiled_sha256":  "F9B4C2ED12612212ECBE68DED33EEC0A9CC891C72C64DD0888096946E707709C",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "characters_generate.md",
        "manifest":  "manifests/characters_generate.md.manifest.json",
        "compiled":  "compiled/characters_generate.md",
        "compiled_sha256":  "38F3DE2E9DD446957E9BCF49D163C93B96B8DC032E0BEFBDC7072890BA33F47C",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "continuity_pack.md",
        "manifest":  "manifests/continuity_pack.md.manifest.json",
        "compiled":  "compiled/continuity_pack.md",
        "compiled_sha256":  "9E41A1B57F1DEB570FA05A57AC318D1395E317472136EC124B7598813BE37DD8",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "lint.md",
        "manifest":  "manifests/lint.md.manifest.json",
        "compiled":  "compiled/lint.md",
        "compiled_sha256":  "451CE34C1E42EB6EA9AE0985BBE728D0BC23941A8CCAA338DA33CCDA5B4F4FAE",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "outline.md",
        "manifest":  "manifests/outline.md.manifest.json",
        "compiled":  "compiled/outline.md",
        "compiled_sha256":  "C2BDD6FC3C2BF39460C026092956A68E24604359E0E78E3511FC3155BE6C8205",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "output_contract.md",
        "manifest":  "manifests/output_contract.md.manifest.json",
        "compiled":  "compiled/output_contract.md",
        "compiled_sha256":  "067E2F6421C67AD60605CF2723691A8C6EFA55053E849645D8DB53F0E2884C68",
        "entry_count":  2,
        "shared_count":  1
    },
    {
        "prompt":  "plan.md",
        "manifest":  "manifests/plan.md.manifest.json",
        "compiled":  "compiled/plan.md",
        "compiled_sha256":  "A55E3C61B1F27B91B12A74676930E1EF9F7B7273D968A2FF8A449DFC1FCF3C90",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "preflight.md",
        "manifest":  "manifests/preflight.md.manifest.json",
        "compiled":  "compiled/preflight.md",
        "compiled_sha256":  "D05581CDE8C564447EF93F71E92DE73918480B50B859B3AF7A2461E48F7EECF2",
        "entry_count":  7,
        "shared_count":  3
    },
    {
        "prompt":  "repair.md",
        "manifest":  "manifests/repair.md.manifest.json",
        "compiled":  "compiled/repair.md",
        "compiled_sha256":  "6171B0A6AF67580D96BF4FD6DCAD349A01A909E073FD9EC37D013E9346C5FB55",
        "entry_count":  15,
        "shared_count":  8
    },
    {
        "prompt":  "state_repair.md",
        "manifest":  "manifests/state_repair.md.manifest.json",
        "compiled":  "compiled/state_repair.md",
        "compiled_sha256":  "BDA655A758FDBC0559FE0980FC92FEBA80FE2EE1792F660DE65D774297D582C2",
        "entry_count":  10,
        "shared_count":  5
    },
    {
        "prompt":  "style_anchor.md",
        "manifest":  "manifests/style_anchor.md.manifest.json",
        "compiled":  "compiled/style_anchor.md",
        "compiled_sha256":  "7264915455E13402314BC4C9BB8864443602FC5BD926C6C6D41FF71122AEF966",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "system_base.md",
        "manifest":  "manifests/system_base.md.manifest.json",
        "compiled":  "compiled/system_base.md",
        "compiled_sha256":  "F36D9AFDE4A2F46A774F450845D5B6173E87C38D1B5CF3DB8FC1870BE42B4F48",
        "entry_count":  1,
        "shared_count":  0
    },
    {
        "prompt":  "write.md",
        "manifest":  "manifests/write.md.manifest.json",
        "compiled":  "compiled/write.md",
        "compiled_sha256":  "0AECFF344DF887C79DFFF4FC1B6967817CADE8BB5569D32BAFE2FACD1B850D52",
        "entry_count":  15,
        "shared_count":  8
    }
]

```

## proposed_refactor_v1\SOURCE_OF_TRUTH.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\SOURCE_OF_TRUTH.md`

```plaintext
﻿# Proposed Refactor v1 - Source of Truth

This document is the canonical expected output set for prompt composition pass v1.

## Artifacts
- Shared fragments: `proposed_refactor_v1/fragments/shared/*`
- Phase fragments: `proposed_refactor_v1/fragments/phase/*`
- Manifests: `proposed_refactor_v1/manifests/*.manifest.json`
- Compiled templates: `proposed_refactor_v1/compiled/*.md`
- Change reports: `proposed_refactor_v1/reports/*.md`

## Expected Compiled Outputs (checksums)
- `appearance_projection.md` -> `4F34AE9D7BFFB6BEEDC621275439D608DE1AC6C264BFAC2A5A07476F8AAAD92B`
- `author_generate.md` -> `F9B4C2ED12612212ECBE68DED33EEC0A9CC891C72C64DD0888096946E707709C`
- `characters_generate.md` -> `38F3DE2E9DD446957E9BCF49D163C93B96B8DC032E0BEFBDC7072890BA33F47C`
- `continuity_pack.md` -> `9E41A1B57F1DEB570FA05A57AC318D1395E317472136EC124B7598813BE37DD8`
- `lint.md` -> `451CE34C1E42EB6EA9AE0985BBE728D0BC23941A8CCAA338DA33CCDA5B4F4FAE`
- `outline.md` -> `C2BDD6FC3C2BF39460C026092956A68E24604359E0E78E3511FC3155BE6C8205`
- `output_contract.md` -> `067E2F6421C67AD60605CF2723691A8C6EFA55053E849645D8DB53F0E2884C68`
- `plan.md` -> `A55E3C61B1F27B91B12A74676930E1EF9F7B7273D968A2FF8A449DFC1FCF3C90`
- `preflight.md` -> `D05581CDE8C564447EF93F71E92DE73918480B50B859B3AF7A2461E48F7EECF2`
- `repair.md` -> `6171B0A6AF67580D96BF4FD6DCAD349A01A909E073FD9EC37D013E9346C5FB55`
- `state_repair.md` -> `BDA655A758FDBC0559FE0980FC92FEBA80FE2EE1792F660DE65D774297D582C2`
- `style_anchor.md` -> `7264915455E13402314BC4C9BB8864443602FC5BD926C6C6D41FF71122AEF966`
- `system_base.md` -> `F36D9AFDE4A2F46A774F450845D5B6173E87C38D1B5CF3DB8FC1870BE42B4F48`
- `write.md` -> `0AECFF344DF887C79DFFF4FC1B6967817CADE8BB5569D32BAFE2FACD1B850D52`

## Review Requirement
- External/internal review should validate `compiled/*` against intended policy semantics before any live template replacement.
- No runtime behavior changes are implied by these artifacts until implementation is approved and applied.

```

## proposed_refactor_v1\compiled\appearance_projection.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\appearance_projection.md`

```plaintext
﻿# APPEARANCE PROJECTION
You are generating a derived appearance summary (and optional art prompt) from canonical appearance atoms/marks.
Return ONLY a JSON object. No prose, no commentary, no code fences.

Rules:
- Do NOT change atoms/marks. They are canonical input.
- Summary must be 2-4 sentences, durable and identity-level (no transient grime, no scene events).
- Avoid inventory/attire unless the input explicitly marks a signature outfit.
- Prefer canonical atom terms; do not invent new traits.
- If you include appearance_art, it must be derived strictly from atoms/marks and signature outfit (if any).

Output JSON:
{
  "summary": "...",
  "appearance_art": {
    "base_prompt": "...",
    "current_prompt": "...",
    "negative_prompt": "...",
    "tags": ["..."]
  }
}

Inputs:
Character:
{{character}}

Appearance base (canon):
{{appearance_base}}

Appearance current (canonical atoms/marks):
{{appearance_current}}


```

## proposed_refactor_v1\compiled\author_generate.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\author_generate.md`

```plaintext
﻿# AUTHOR GENERATION

You are generating an original author persona for BookForge.

Return ONLY a single JSON object. Do not include markdown, code fences, or extra commentary.
The JSON must be strict (double quotes, no trailing commas).

Required top-level keys:
- author (object)
- author_style_md (string)
- system_fragment_md (string)

Optional top-level key:
- banned_phrases (array of strings) only if the author is known for very specific phrases.

author object required keys:
- persona_name (string)
- influences (array of objects with name and weight; infer weights if not provided)
- trait_profile (object)
- style_rules (array of strings)
- taboos (array of strings)
- cadence_rules (array of strings)

JSON shape example (fill with real values):
{
  "author": {
    "persona_name": "",
    "influences": [
      {"name": "", "weight": 0.0}
    ],
    "trait_profile": {
      "voice": "",
      "themes": [],
      "sensory_bias": "",
      "pacing": ""
    },
    "style_rules": [],
    "taboos": [],
    "cadence_rules": []
  },
  "author_style_md": "",
  "system_fragment_md": ""
}

Influences: {{influences}}

Persona name (optional): {{persona_name}}

Notes: {{notes}}

Additional prompt text: {{prompt_text}}


```

## proposed_refactor_v1\compiled\characters_generate.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\characters_generate.md`

```plaintext
﻿# CHARACTERS GENERATE

You are refining outline character stubs into canon character entries and initial per-book character state.
Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Do not invent new characters; expand only the outline-provided stubs.

Required top-level keys:
- schema_version ("1.0")
- characters (array)

Each character object must include:
- character_id
- name
- pronouns
- role
- persona (object)
- inventory (array)
- containers (array)
- invariants (array of strings)
- appearance_base (object)

Recommended mechanic seed key (dynamic):
- character_continuity_system_state (object)
  - Include any starting mechanics known at setup time.
  - Examples: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses.
  - titles must be an array of objects (not strings).
  - You may add future mechanic families if relevant.
  - Use dynamic continuity families as needed: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, system_tracking_metadata, extended_system_data.
  - For LitRPG-like systems, prefer structured stats/skills/titles in character_continuity_system_state.

Appearance guidance (durable, canonical):
- appearance_base is the canon self-image for this character.
- Include: summary, atoms, marks, alias_map.
- Atoms are normalized traits (species, sex_presentation, age_band, height_band, build, hair_color, hair_style, eye_color, skin_tone).
- marks are durable identifiers (scars, tattoos, prosthetics). No temporary grime or wounds.
- alias_map lists acceptable synonyms for lint tolerance (e.g., hair_color: ["dark brown"]).
- appearance_current will be derived from appearance_base for the book unless explicitly overridden later.

Naming and durable item guidance:
- For items, use a human-readable item_name; do not use ITEM_* ids in prose strings.
- Reserve ITEM_* ids for canonical JSON only; do not use them in prose strings.
- If you emit an item_id here, include item_name as a human label.

Starting scene alignment (important):
- The initial inventory/containers/state must prepare each character for the book's first scene.
- Use the Book + Outline characters in THIS prompt as your source of truth for the opening situation.
- If the opening situation is unclear, default to a neutral, plausible posture (hands free, items stowed).
- Example: office/briefing -> no weapons held; battle opener -> weapon may be in hand; travel -> stowed gear.

Persona guidance (compact, factual):
- core_traits (array)
- motivations (array)
- fears (array)
- values (array)
- voice_notes (array)
- arc_hint (string)

Inventory rules:
- Every carried/held item must include a container location.
- Use explicit container labels (satchel, belt, pack, hand_left, hand_right, sheath, etc.).
- If an item is held, container must be hand_left or hand_right.
- If you use item_id, include item_name (human label) on the same inventory entry. The item_name must be human readable and not an escaped id value.
- Prefer item_name in prose-facing fields; item_id only in canonical JSON.
- Containers are tracked separately in containers[] with owner and contents.

Invariant phrasing (use exact strings where possible):
- inventory: <CHAR_ID> -> <item> (status=carried|stowed|equipped, container=<container_label>)
- container: <container_label> (owner=<CHAR_ID>, contents=[item1, item2])
- injury: <character_id> <injury/location>

Book:
{{book}}

Outline characters:
{{outline_characters}}

Outline opening context (chapter/section/scene 1):
{{outline_opening}}

Series info (if any):
{{series}}

Output JSON:
{
  "schema_version": "1.0",
  "characters": [
    {
      "character_id": "CHAR_example",
      "name": "",
      "pronouns": "",
      "role": "",
      "persona": {
        "core_traits": [],
        "motivations": [],
        "fears": [],
        "values": [],
        "voice_notes": [],
        "arc_hint": ""
      },
      "appearance_base": {
        "summary": "",
        "atoms": {
          "species": "human",
          "sex_presentation": "",
          "age_band": "",
          "height_band": "",
          "build": "",
          "hair_color": "",
          "hair_style": "",
          "eye_color": "",
          "skin_tone": ""
        },
        "marks": [
          {"name": "", "location": "", "durability": "durable"}
        ],
        "alias_map": {
          "hair_color": [""],
          "eye_color": [""]
        }
      },
      "character_continuity_system_state": {
        "stats": {"hp": {"current": 10, "max": 10}},
        "skills": {"sword": 1},
        "titles": [{"name": "Novice", "source": "starting_class", "active": true}],
        "resources": {"mana": {"current": 5, "max": 5}}
      },
      "inventory": [
        {"item_id": "ITEM_longsword", "item_name": "Longsword", "status": "carried", "container": "hand_right"}
      ],
      "containers": [
        {"container": "satchel", "owner": "CHAR_example", "location": "shoulder_left", "contents": ["maps"]}
      ],
      "invariants": [
        "inventory: CHAR_example -> longsword (status=carried, container=hand_right)",
        "container: satchel (owner=CHAR_example, contents=[maps])"
      ]
    }
  ]
}


```

## proposed_refactor_v1\compiled\continuity_pack.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\continuity_pack.md`

```plaintext
﻿# CONTINUITY PACK

Create a continuity pack JSON object with these fields:
- scene_end_anchor: 2-4 factual sentences about how the last scene ended (no prose).
- constraints: list of immediate continuity constraints.
- open_threads: list of active thread ids.
- cast_present: list of character names present next.
- location: location id or name.
- next_action: the implied next action.
- summary: echo state.summary (facts-only arrays; do not paraphrase).

Return ONLY JSON.

Rules:
- Use only characters listed in scene_card.cast_present. Do not introduce new names.
- summary must match state.summary and remain facts-only; do not add prose.
- constraints must include the highest-priority invariants from summary.must_stay_true and summary.key_facts_ring (copy exact strings when possible).
- constraints must include the highest-priority inventory/container invariants from summary.must_stay_true (copy exact strings when possible).
- If character_states are provided, prefer their inventory/container facts and continuity mechanic facts; do not invent conflicting values.
- If item_registry or plot_devices are provided, reuse canonical names/ids in constraints when referencing durable items/devices.
- Prefer item_registry.items[].display_name for prose references; reserve item_id for canonical JSON. The display_name must be human readable and not an escaped id/name.
- If state.global_continuity_system_state contains canonical mechanic labels/values, reuse those exact labels in constraints.
- If scene_card.cast_present is empty, cast_present must be an empty array.
- open_threads must be a subset of thread_registry thread_id values.
- If scene_card.thread_ids is present, prefer those thread ids.
- Do not invent new thread ids or character names.

Scene card:
{{scene_card}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

State:
{{state}}

Summary (facts-only):
{{summary}}

Recent facts:
{{recent_facts}}
Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}


```

## proposed_refactor_v1\compiled\lint.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\lint.md`

```plaintext
﻿# LINT

Check the scene for continuity, invariant violations, and duplication.
Flag invariant contradictions against must_stay_true/key facts.
Return ONLY JSON matching the lint_report schema.
- Classify UI/prose mechanic claims as DURABLE or EPHEMERAL before enforcing.
  - DURABLE: persistent stats/caps, skills/titles acquired, lasting status effects, inventory/custody, named mechanics referenced as invariants.
  - EPHEMERAL: roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat telemetry.
- Enforce DURABLE claims against authoritative_surfaces/state/registries.
- EPHEMERAL claims do not require state ownership; only flag EPHEMERAL contradictions inside the same scene as warnings.
- UI gate:
  - If scene_card.ui_allowed=false and any authoritative UI blocks appear, emit issue code 'ui_gate_violation' (severity depends on lint mode).
  - If ui_allowed is missing and UI blocks appear, emit 'ui_gate_unknown' (warning) requesting explicit ui_allowed; do not fail solely for missing flag.
  - Inline bracketed UI (e.g., [HP: 1/1]) is still UI and should be gated the same way; do not embed UI mid-sentence.
- If uncertain, default to EPHEMERAL (warning at most), not DURABLE (error).
- status="fail" only if there is at least one issue with severity="error"; warnings alone => status="pass".
- Item naming enforcement scope:
  - Do not require that every mention in narrative prose use display_name.
  - Enforce canonical display_name for: (a) anchoring at first introduction (same paragraph or within the next 2 sentences),
    (b) any custody-change sentence (drop/pick up/hand off/stow/equip/transfer), and (c) any case where a descriptor is ambiguous among multiple durable items in the scene.
  - Otherwise, treat non-canonical descriptive references as warnings at most.
- Prose hygiene: flag internal ids or container codes in narrative prose (CHAR_, ITEM_, THREAD_, DEVICE_, hand_left, hand_right).
- Naming severity policy:
  - warning: unambiguous descriptor used post-anchor.
  - error: missing anchor, descriptor used during custody-change without canonical name, or ambiguity risk.

- Appearance enforcement (authoritative surface):
  - APPEARANCE_CHECK is authoritative for cast_present_ids.
  - Compare APPEARANCE_CHECK tokens to appearance_current atoms/marks (alias-aware).
  - If APPEARANCE_CHECK contradicts appearance_current, emit error code "appearance_mismatch".
  - Prose-only appearance contradictions are warnings unless explicitly durable and uncorrected in-scene.
  - If prose depicts a durable appearance change but scene_card.durable_appearance_changes does not include it and no appearance_updates are present, emit error code "appearance_change_undeclared".
  - If APPEARANCE_CHECK is missing for a cast member, emit warning code "appearance_check_missing".
- For authoritative surfaces, prefer exact canonical item/device labels from registries.
- For milestone repetition/future checks, compare against PRE-INVARIANTS only (pre-scene canon).
- For ownership/consistency checks, compare against POST-STATE (post-patch candidate).
- POST-STATE is canonical; character_states is a derived convenience view. If they contradict, emit pipeline_state_incoherent.
- Check for POV drift vs book POV (no first-person in third-person scenes).
  - Ignore first-person pronouns inside quoted dialogue; only narration counts.
- Deterministically enforce scene-card durable constraints (required_in_custody, required_scene_accessible, forbidden_visible, device_presence; optional required_visible_on_page).
- Durable constraint evaluation must use POST-STATE candidate (after patch), not pre-state.
- Report missing durable context ids with explicit retry hints instead of guessing canon.
- Input consistency check (mandatory, before issuing continuity/durable errors):
  - If MUST_STAY_TRUE invariants contradict the provided post-patch candidate character state, treat this as an upstream snapshot error.
  - In that case emit a single error issue with code "pipeline_state_incoherent" including evidence of the invariant and the conflicting state field.
  - Do NOT emit additional continuity errors for the same fields when pipeline_state_incoherent is present.
- must_stay_true removals:
  - Lines starting with "REMOVE:" are deletion directives, not invariants.
  - Ignore REMOVE lines when checking contradictions.
  - If a REMOVE directive targets a fact, treat that fact as non-canonical even if it appears earlier in must_stay_true.
- If pipeline_state_incoherent is present, issues MUST contain exactly one issue.
- For each issue, include evidence when possible (line number + excerpt) as {"evidence": {"line": N, "excerpt": "..."}}.
- Evaluate consistency over the full scope of the scene, not a single snapshot.
  - Transitional state: a temporary mismatch later corrected or superseded within this scene.
  - Durable violation: a mismatch that persists through the end of the scene or ends unresolved.
  - You MUST read the entire scene and build a minimal timeline of explicit state claims/updates (UI lines, inventory changes, title/skill changes, location/time claims).
  - If you detect an apparent inconsistency, you MUST search forward for later updates that resolve or supersede it.
  - Only produce FAIL for durable violations. If resolved within the scene, do NOT FAIL; at most emit a warning.
  - When the same stat appears multiple times, the last occurrence in the scene is authoritative unless an explicit rollback is stated.
  - Any durability violation must cite both the conflicting line and the lack of later correction (or state "no later correction found").

Required keys:
- schema_version ("1.0")
- status ("pass" or "fail")
- issues (array of objects)

Each issue object must include:
- code
- message
Optional:
- severity
- evidence

If there are no issues, return:
{
  "schema_version": "1.0",
  "status": "pass",
  "issues": []
}

If there are issues, return:
{
  "schema_version": "1.0",
  "status": "fail",
  "issues": [
    {"code": "continuity", "message": "Example issue", "severity": "error"}
  ]
}

Scene:
{{prose}}

Scene card:
{{scene_card}}

Authoritative surfaces:
{{authoritative_surfaces}}

Appearance check (authoritative):
{{appearance_check}}

Character states (post-patch candidate, per cast_present_ids):
{{character_states}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

Pre-state (before patch):
{{pre_state}}

Pre-summary (facts-only):
{{pre_summary}}

Pre-invariants (must_stay_true + key facts):
{{pre_invariants}}

Post-state candidate (after patch):
{{post_state}}

Post-summary (facts-only):
{{post_summary}}

Post-invariants (must_stay_true + key facts):
{{post_invariants}}




```

## proposed_refactor_v1\compiled\outline.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\outline.md`

```plaintext
﻿# OUTLINE

You are the outline planner. Create a compact outline for the book.
Return ONLY a single JSON object that matches the outline schema v1.1.
No markdown, no code fences, no commentary.
Keep summaries concise but in the author voice from the system prompt.

Core contract: each SCENE is one scene to be written (scene == writing unit).
Scenes must vary per chapter. Do NOT use a fixed scene count.

Sections are required:
- Every chapter must include a sections array.
- Typical chapters should have 3-8 sections (target).
- A simple/interlude chapter may use 2-4 sections (rare).
- Each section usually has 2-6 scenes.
- A 1-scene section is allowed only for a stinger/hook moment.
- Total scenes per chapter should naturally land in 6-32, varying by complexity.

Scene quality rules:
- Each scene must include type and outcome.
- outcome must be a concrete state change.
- Do not pad with travel/recap/mood-only scenes.
If a user prompt is provided, treat it as grounding context. Integrate its details, but keep the schema and scene rules.


Chapter role vocabulary (prefer one):
- hook, setup, pressure, reversal, revelation, investigation, journey, trial, alliance, betrayal, siege, confrontation, climax, aftermath, transition, hinge
If it truly does not fit, use the closest role; custom roles are allowed but should be 1-2 words.

Scene type vocabulary (prefer one):
- setup, action, reveal, escalation, choice, consequence, aftermath, transition
If it truly does not fit, use the closest type; custom types are allowed but should be 1-2 words.

Tempo values (prefer one):
- slow_burn, steady, rush
If it truly does not fit, use the closest tempo; custom values are allowed but should be 1-2 words.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Optional top-level keys (recommended):
- threads (array of thread stubs)
- characters (array of character stubs)

Each chapter must include:
- chapter_id
- title
- goal
- chapter_role
- stakes_shift
- bridge (object with from_prev, to_next)
- pacing (object with intensity, tempo, expected_scene_count; expected_scene_count is a soft target)
- sections (array)

Each section must include:
- section_id
- title
- intent
- scenes (array of scene objects)

Optional section keys:
- section_role

Each scene must include:
- scene_id
- summary
- type
- outcome
- characters (array of character_id values present in the scene)

Optional scene keys:
- introduces (array of character_id values introduced in the scene)
- threads (array of thread_id values touched in the scene)
- callbacks (array of ids: character/thread/lore references)

Character stub format:
{
  "character_id": "CHAR_<slug>",
  "name": "",
  "pronouns": "",
  "role": "",
  "intro": {"chapter": 1, "scene": 1}
}

Thread stub format:
{
  "thread_id": "THREAD_<slug>",
  "label": "",
  "status": "open"
}

Output ordering guidance:
- Write chapters first. After chapters, list threads and characters at the end of the JSON object.

JSON shape example (fill with real values):
{
  "schema_version": "1.1",
  "chapters": [
    {
      "chapter_id": 1,
      "title": "",
      "goal": "",
      "chapter_role": "hook",
      "stakes_shift": "",
      "bridge": {"from_prev": "", "to_next": ""},
      "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 10},
      "sections": [
        {
          "section_id": 1,
          "title": "",
          "intent": "",
          "scenes": [
            {"scene_id": 1, "summary": "", "type": "setup", "outcome": "", "characters": ["CHAR_new_character_name"], "introduces": ["CHAR_new_character_name"]}
          ]
        }
      ]
    },
    {
      "chapter_id": 2,
      "title": "",
      "goal": "",
      "chapter_role": "setup",
      "stakes_shift": "",
      "bridge": {"from_prev": "", "to_next": ""},
      "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 8},
      "sections": [
        {
          "section_id": 1,
          "title": "",
          "intent": "",
          "scenes": [
            {"scene_id": 1, "summary": "", "type": "transition", "outcome": "", "characters": ["CHAR_new_character_name"]}
          ]
        }
      ]
    }
  ],
  "threads": [
    {"thread_id": "THREAD_prophecy", "label": "The Awakened Sage", "status": "open"}
  ],
  "characters": [
    {"character_id": "CHAR_new_character_name", "name": "New Character", "pronouns": "they/them", "role": "protagonist", "intro": {"chapter": 1, "scene": 1}}
  ]
}

Book:
{{book}}

Targets:
{{targets}}

User prompt (optional, may be empty):
{{user_prompt}}

Notes:
{{notes}}


```

## proposed_refactor_v1\compiled\output_contract.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\output_contract.md`

```plaintext
﻿Output must follow the requested format.
JSON blocks must be valid and schema-compliant.
All required keys and arrays must be present.
When a prompt specifies required counts or ranges, treat them as hard constraints.
Do not collapse arrays below the stated minimums.
If multiple output blocks are required (e.g. PROSE and STATE_PATCH), include all blocks in order.
If output must be JSON only, return a single JSON object with no commentary or code fences.
When creating outlines, the total scenes per chapter (sum of sections[].scenes[]) must match chapters[].pacing.expected_scene_count.
If a prompt requires a COMPLIANCE or PREFLIGHT block, include it before PROSE.
Durable vs ephemeral mechanics:
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
For durable items, prose must use display_name; item_id is reserved for JSON/patches. The display_name must be human readable and not an escaped id/name.
For durable mutations, every `transfer_updates[]` object must include `item_id` and `reason` (non-empty string).
`inventory_alignment_updates` must be an array of objects (no wrapper object with `updates`).
Use canonical continuity keys: character_continuity_system_updates and global_continuity_system_updates.
- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]


```

## proposed_refactor_v1\compiled\plan.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\plan.md`

```plaintext
﻿# PLAN

You are the planner. Use the outline window and state to create the next scene card.
Return ONLY a single JSON object that matches the scene_card schema.
No markdown, no code fences, no commentary. Use strict JSON (double quotes, no trailing commas).

If outline_window includes character information, keep those character ids in mind.
If character_states are provided, keep inventory/persona/continuity mechanics consistent; do not invent conflicting facts.
If outline_window.current.introduces is present, the scene must introduce those characters.
If recent_lint_warnings include ui_gate_unknown, set ui_allowed explicitly for this scene.

Required keys:
- schema_version ("1.1")
- scene_id
- chapter
- scene
- scene_target
- goal
- conflict
- required_callbacks (array)
- constraints (array)
- end_condition
- ui_allowed (boolean; true only when System/UI is active in this scene)

Recommended keys (use ids from the outline; do not invent ids):
- cast_present (array of character names for prose guidance)
- cast_present_ids (array of character ids, e.g. CHAR_Eldrin)
- introduces (array of character names introduced in this scene)
- introduces_ids (array of character ids introduced in this scene)
- thread_ids (array of thread ids, e.g. THREAD_Awakened_Sage)

Optional continuity-planning keys:
- required_in_custody (array of item/device ids that must still be owned by scene start)
- required_scene_accessible (array of item/device ids that must be retrievable without continuity break)
- required_visible_on_page (array of ids that must be explicitly shown in-scene; use sparingly)
- forbidden_visible (array of ids that must not be visibly carried/active in-scene)
- device_presence (array of plot-device ids expected to matter in-scene)
- transition_type (string, e.g. "time_skip", "travel_arrival", "combat_aftermath")
- timeline_scope ("present"|"flashback"|"dream"|"simulation"|"hypothetical")
- ontological_scope ("real"|"non_real")

Optional genre/system keys:
- continuity_system_focus (array of mechanic domains likely to change this scene, e.g. ["stats", "resources", "titles"])
- ui_mechanics_expected (array of UI labels likely to appear, e.g. ["HP", "Stamina", "Crit Rate"])
  - If ui_allowed=false, ui_mechanics_expected MUST be an empty array.

JSON shape example (fill with real values):
{
  "schema_version": "1.1",
  "scene_id": "SC_001_001",
  "chapter": 1,
  "scene": 1,
  "scene_target": "Protagonist commits to the journey.",
  "goal": "Force a decisive choice.",
  "conflict": "Safety versus obligation.",
  "required_callbacks": [],
  "constraints": ["target_words: 1900"],
  "end_condition": "The protagonist leaves home.",
  "ui_allowed": false,
  "cast_present": ["Eldrin"],
  "cast_present_ids": ["CHAR_Eldrin"],
  "introduces": [],
  "introduces_ids": [],
  "thread_ids": ["THREAD_Awakened_Sage"],
  "required_in_custody": ["ITEM_broken_tutorial_sword"],
  "required_scene_accessible": ["ITEM_broken_tutorial_sword"],
  "required_visible_on_page": [],
  "forbidden_visible": [],
  "device_presence": ["DEVICE_anomaly_tag"],
  "transition_type": "travel_arrival",
  "timeline_scope": "present",
  "ontological_scope": "real",
  "continuity_system_focus": ["stats", "resources"],
  "ui_mechanics_expected": ["HP", "Stamina"]
}

Outline window:
{{outline_window}}

Character states (per outline_window.current.characters):
{{character_states}}

State:
{{state}}

Recent lint warnings (prior scene, if any):
{{recent_lint_warnings}}

Task:
Create the next scene card.



```

## proposed_refactor_v1\compiled\preflight.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\preflight.md`

```plaintext
﻿# PREFLIGHT

You are the scene state preflight aligner.
Return ONLY a single JSON object that matches the state_patch schema.
No markdown, no code fences, no commentary.

Your job is to align state before writing starts for this scene.
- Output ONLY a STATE_PATCH-equivalent JSON object.
- Do not write prose.
- This pass can update inventory posture and continuity system state for cast/global scope.
- The primary goal is make changes as needed to setup the next scene.
- If uncertain, prefer leaving values unchanged.

Hard rules:
- State ownership is mandatory: if you change mechanics, write them in canonical updates.
- If a value is not changed in patch, it is treated as unchanged.
- Do not invent new character ids or thread ids.
- Keep updates scoped to current cast and global continuity only.
- Do not emit cursor_advance, summary_update, duplication counters, or chapter rollup changes.
- Keep timeline lock: only prepare state needed for the current scene card.
- Respect scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`, and optional `required_visible_on_page`.
- Respect scene scope gates: `timeline_scope` and `ontological_scope`; only use scope override when explicitly justified by reason_category.
- Scope override rule (non-present / non-real scenes):
  - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
Transition gate (do-nothing by default):
- First decide whether this scene is a CONTINUATION or a DISCONTINUOUS TRANSITION.
- Treat as CONTINUATION when ALL are true:
  - scene_card.scene_target matches state.world.location, AND
  - scene_card.timeline_scope and scene_card.ontological_scope do not change relative to current state, AND
  - scene_card.transition_type is empty OR clearly indicates continuity (e.g., "continuous", "beat", "direct_continuation"), AND
  - there is no durable-constraint violation to fix.
- If CONTINUATION:
  - Output the minimal patch: {"schema_version":"1.0"} (no other fields), unless a durable constraint is violated.
  - Do NOT "normalize" inventory posture or move items just to be scene-appropriate. Only fix actual contradictions.
- Treat as DISCONTINUOUS TRANSITION when ANY are true:
  - scene_card.scene_target differs from state.world.location, OR
  - scene_card.transition_type is present and not clearly continuous, OR
  - timeline_scope / ontological_scope indicates a scope shift, OR
  - cast_present for this scene differs materially from state.world.cast_present.

World alignment (only when needed for this scene):
- If state.world.location != scene_card.scene_target, set world_updates.location = scene_card.scene_target.
- If scene_card.cast_present_ids is provided and differs from state.world.cast_present, set world_updates.cast_present = scene_card.cast_present_ids.
- Do not modify world.time unless the scene card explicitly implies a non-present timeline_scope; if you must, record why in global_continuity_system_updates.

Hidden transition state policy:
- Posture changes (stowed/held/worn, hand->pack, pack->table, etc.) are allowed ONLY during DISCONTINUOUS TRANSITION, or to satisfy a durable constraint.
- Custody changes (an item is no longer in the character's possession / custodian changes scope) are NOT implied by posture changes.
  - If and only if custody changes, you MUST:
    - update item_registry_updates for that item (custodian + last_seen), and
    - include transfer_updates with a reason (and prefer adding expected_before).
- Never "drop" an item by omitting it from an inventory array. If an item leaves a character, represent it as an explicit transfer.

Inventory transition rules:
Appearance contract:
- appearance_current atoms/marks are canonical and must not be contradicted or mutated in preflight.
- Preflight does NOT invent or change appearance; only note missing appearance_current if present in character_states.
- Ensure carried/equipped/stowed posture is scene-appropriate.
- character_updates.inventory and inventory_alignment_updates.set.inventory must be arrays of inventory objects, never id strings.
- Preserve ownership and container consistency.
- For held items use `container=hand_left` or `container=hand_right`.

Durable-constraint compliance check (must run before output):
1) Resolve constraint tokens:
   - Treat entries in required_in_custody / required_scene_accessible / required_visible_on_page / forbidden_visible / device_presence as IDs when they look like IDs.
   - If an entry does not match an ID, attempt a best-effort lookup by name/alias in item_registry / plot_devices.
   - If still ambiguous, do not guess; leave unchanged and record the unresolved token in character_updates.notes for the most relevant cast member.
2) Enforce required_in_custody:
   - Ensure the specified item's custodian is the required character/scope.
   - Ensure the item appears in that character's inventory in an appropriate container/status.
3) Enforce forbidden_visible:
   - Ensure the item is not in hand_left/hand_right and not "worn/brandished/visible" status.
   - Prefer moving it to an existing container (pack/pouch/sheath) over inventing new containers.
4) Enforce required_scene_accessible / required_visible_on_page:
   - Accessible: item can be stowed but present in-scene.
   - Visible_on_page: item must be held/worn/placed such that the writer can naturally show it early.

Dynamic continuity rules:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
- Use canonical keys:
  - character_continuity_system_updates
  - global_continuity_system_updates
- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- Update operations use set/delta/remove/reason.
- Dynamic mechanic families are allowed (stats, skills, titles, resources, effects, statuses, classes, custom systems).
- titles must be arrays of objects with stable `name` fields, never arrays of strings.
- Durable-state updates are authoritative and must be explicit in patch blocks.
- If inventory posture is changed for scene fit, include `inventory_alignment_updates` with `reason` and `reason_category`.
- If you emit inventory_alignment_updates, the reason MUST state the final posture (item + container + status) so downstream phases can reconcile must_stay_true. Do not omit posture intent.
- `inventory_alignment_updates` must be an array of objects; do not wrap it in an object with an `updates` key.
- If durable item custody or metadata changes, include `item_registry_updates` and/or `transfer_updates`.
- Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
- If plot-device custody or activation changes, include `plot_device_updates`.
- Never rely on prose implication for durable state mutation.
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).- Safety check for non-trivial changes:
  - When making a DISCONTINUOUS TRANSITION change that moves an item between containers, changes custody, or toggles a plot device:
    - include expected_before with the minimal prior snapshot you are relying on (e.g., prior container/status/custodian).
    - if expected_before does not match current state, prefer leaving unchanged and note the discrepancy in notes.
- Patch coupling rule:
  - If you emit inventory_alignment_updates for a character, you MUST also emit character_updates for that character with the final authoritative inventory/containers for this scene.
  - The inventory arrays in both places should match (alignment is the justification record; character_updates is the durable state).
- reason_category vocabulary (use one):
  - continuity_fix
  - constraint_enforcement
  - location_transition
  - time_skip
  - scope_shift
  - equipment_posture
  - custody_transfer
  - plot_device_state

JSON Contract Block (strict; arrays only):
- All *_updates must be arrays of objects, even when there is only one update.
- INVALID vs VALID examples:
  - item_registry_updates:
    - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
    - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates:
    - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
    - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
  - transfer_updates:
    - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
    - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
  - inventory_alignment_updates:
    - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
    - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
  - global_continuity_system_updates:
    - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
    - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- custodian must be a non-null string id or "world"; never null.

Scene card:
{{scene_card}}

Current state:
{{state}}

Current summary:
{{summary}}

Character registry:
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (cast only):
{{character_states}}

Immediate previous scene (if available):
{{immediate_previous_scene}}

Last appearance prose for cast members missing from immediate previous scene:
{{cast_last_appearance}}

Output JSON shape reminder:
{
  "schema_version": "1.0",
  "character_updates": [
    {
      "character_id": "CHAR_example",
      "chapter": 1,
      "scene": 2,
      "inventory": [{"item": "ITEM_example", "container": "pockets", "status": "stowed"}],
      "containers": [],
      "persona_updates": [],
      "invariants_add": [],
      "notes": ""
    }
  ],
  "character_continuity_system_updates": [
    {
      "character_id": "CHAR_example",
      "set": {
        "titles": [{"name": "Novice"}]
      },
      "delta": {},
      "remove": [],
      "reason": "align pre-scene state"
    }
  ],
  "global_continuity_system_updates": [],
  "inventory_alignment_updates": [
    {
      "character_id": "CHAR_example",
      "set": {"inventory": [{"item": "ITEM_example", "container": "hand_right", "status": "held"}], "containers": []},
      "reason": "scene posture alignment",
      "reason_category": "after_combat_cleanup"
    }
  ],
  "item_registry_updates": [],
  "plot_device_updates": [],
  "transfer_updates": []
}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}



```

## proposed_refactor_v1\compiled\repair.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\repair.md`

```plaintext
﻿# REPAIR

Fix the scene based on lint issues.
Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
- must_stay_true reconciliation (mandatory):
  - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - Remove conflicting old invariants rather than preserving them.
- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
For held items, specify container=hand_left or container=hand_right.
Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
Durable vs ephemeral mechanics:
- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.
- UI/system readouts must be on their own line, starting with '[' and ending with ']'.
- Do NOT embed bracketed UI in narrative sentences.
- Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).

- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
- APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).

Naming repairs:
- If lint flags an item naming issue, fix it with minimal edits.
- Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
- Do not rename item_id or registry fields; only adjust prose wording.
summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
Enforce scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
Respect `timeline_scope` and `ontological_scope`.
- Scope override rule (non-present / non-real scenes):
  - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
Return corrected prose plus a corrected state_patch JSON block.

Output format (required, no code fences, no commentary):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>
Current arm-side / inventory facts: <from must_stay_true>

APPEARANCE_CHECK:
- CHAR_ID: <4-8 tokens from atoms/marks>

PROSE:
<scene prose>

STATE_PATCH:
<json>

STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
- Include character_continuity_system_updates for cast_present_ids when mechanics change.
  - Use set/delta/remove/reason.
  - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  - If a new mechanic family appears, add it under set with a stable key.
- Include global_continuity_system_updates only if global mechanics change.
- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
  - appearance_updates MUST be an object under character_updates.
    - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
  - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
  - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
  - inventory_alignment_updates[*].set MUST be an object (not a list).
    - INVALID: "set": []
    - VALID:   "set": {"inventory": [...], "containers": [...]}
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If you mutate durable state, do not leave the same mutation only in prose.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
- appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.
  - appearance_updates MUST be an object, not an array.
    - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
  - appearance_updates.set may include atoms and marks only (canonical truth).
    - Do NOT put marks_add at the top level; it belongs under set.
    - Use set.marks_add / set.marks_remove for marks changes.
    - Use set.atoms for atom changes.
  - appearance_updates.reason is required (brief, factual).
  - Do NOT set summary or art text in appearance_updates (derived after acceptance)
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - character_updates.inventory MUST be an array of objects, never string item ids.
  - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
  - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.
  - inventory: CHAR_example -> shard (carried, container=satchel)
  - inventory: CHAR_example -> longsword (carried, container=hand_right)
  - container: satchel (owner=CHAR_example, contents=[shard, maps])
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
  - injury: right forearm scar / left arm filament
  - ownership: shard (carried) / shard (bound but physical)

Issues:
{{issues}}

Scene card:
{{scene_card}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

Scene:
{{prose}}

State:
{{state}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

JSON Contract Block (strict; arrays only):
- All *_updates must be arrays of objects, even when there is only one update.
- INVALID vs VALID examples:
  - item_registry_updates:
    - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
    - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates:
    - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
    - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
  - transfer_updates:
    - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
    - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
  - inventory_alignment_updates:
    - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
    - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
  - global_continuity_system_updates:
    - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
    - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- custodian must be a non-null string id or "world"; never null.








```

## proposed_refactor_v1\compiled\state_repair.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\state_repair.md`

```plaintext
﻿# STATE REPAIR

You are the state repair step. You must output a corrected STATE_PATCH JSON only.
No prose, no commentary, no code fences.

Goal:
- Ensure state_patch fully and accurately captures the scene's events and outcomes.
- Fill missing summary_update data and fix invalid formats from draft_patch.
- Preserve pre-scene invariants unless this scene changes them; when it does, update must_stay_true to the final end-of-scene value.
- must_stay_true reconciliation (mandatory):
  - If this scene changes a durable fact (stats/HP/status/title/custody), you MUST update must_stay_true to reflect the final end-of-scene value.
  - Remove or replace any prior must_stay_true entries that conflict with new durable values.
  - Do NOT carry forward conflicting legacy invariants once the scene updates them.
- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
- Ensure mechanic/UI ownership in continuity system updates.

Rules:
- Output a single JSON object that matches the state_patch schema.
- Use schema_version "1.0".
- Use scene_card.cast_present_ids for world_updates.cast_present.
- Use scene_card.thread_ids for world_updates.open_threads.
- Do not invent new character or thread ids.
- summary_update arrays are required: last_scene (2-4 sentences), key_events (3-7 bullets), must_stay_true (3-7 bullets), chapter_so_far_add (bullets).
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates
Durable vs ephemeral mechanics:
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.

- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene..
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
- If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
- Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If prose depicts a durable appearance change, include character_updates.appearance_updates with a reason.
- Do NOT set summary or art text in appearance_updates (derived after acceptance).

Naming repairs:
- If lint flags an item naming issue, fix it with minimal edits.
- Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
- Do not rename item_id or registry fields; only adjust prose wording.
- Do not add numeric mechanics to invariants_add; store them in continuity system updates instead.
- If an event appears in prose, it must appear in key_events.
- must_stay_true must include milestone ledger entries and any inventory/injury/ownership invariants implied by prose.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
- character_updates entries must use arrays: persona_updates (array), invariants_add (array).
- character_updates.inventory must be an array of objects, never item-id strings.
- Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
- Use character_continuity_system_updates / global_continuity_system_updates to reconcile mechanics.
- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- If a new mechanic family appears in prose/UI, add it under set with a stable key.
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
- appearance_updates MUST be an object under character_updates.
    - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
  - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
  - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
  - inventory_alignment_updates[*].set MUST be an object (not a list).
    - INVALID: "set": []
    - VALID:   "set": {"inventory": [...], "containers": [...]}
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If durable mutation is implied but ambiguous, keep canonical state unchanged and emit an explicit repair note in reason fields.
- Honor scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
- Respect `timeline_scope` and `ontological_scope`; avoid physical custody changes in non-present/non-real scope unless explicit override is present.
- Scope override rule (non-present / non-real scenes):
  - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
Inputs
- prose: final scene text
- state: pre-scene state
- draft_patch: patch returned by write/repair (may be incomplete)
- continuity_pack: pre-write continuity pack
- character_states: current cast-only character state

Scene card:
{{scene_card}}

Continuity pack:
{{continuity_pack}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

State (pre-scene):
{{state}}

Summary (facts-only):
{{summary}}

Draft state patch:
{{draft_patch}}

Prose:
{{prose}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

JSON Contract Block (strict; arrays only):
- All *_updates must be arrays of objects, even when there is only one update.
- INVALID vs VALID examples:
  - item_registry_updates:
    - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
    - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates:
    - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
    - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
  - transfer_updates:
    - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
    - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
  - inventory_alignment_updates:
    - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
    - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
  - global_continuity_system_updates:
    - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
    - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- custodian must be a non-null string id or "world"; never null.










```

## proposed_refactor_v1\compiled\style_anchor.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\style_anchor.md`

```plaintext
﻿# STYLE ANCHOR

Write a short style anchor excerpt (200-400 words) that demonstrates the desired voice and cadence.
Do not reference plot events or character names.
Return ONLY the excerpt text.
Output must be non-empty and between 200-400 words.
If you are unsure, write a neutral prose excerpt in the desired voice.

Author persona:
{{author_fragment}}


```

## proposed_refactor_v1\compiled\system_base.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\system_base.md`

```plaintext
﻿You are BookForge, a deterministic book-writing engine.
Follow the output contracts exactly.
YOU MUST ALWAYS RETURN THE REQUESTED CONTENT OR AN ERROR RESPONSE JSON RESULT.
Treat all schema requirements and numeric ranges as hard constraints.
If a prompt specifies required counts or ranges, you must satisfy them.
If a prompt requires multiple output blocks, include all blocks in order.
If registries or ids are provided, use only those; do not invent new ids.
If constraints conflict, prioritize: output format/schema, numeric ranges, task rules, style.
Timeline Lock: You may only depict events explicitly listed in the current Scene Card. You must not depict, imply, or resolve any later-scene milestone outcomes (including acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
State primacy: state invariants and summary facts are binding; do not contradict them.
Milestone uniqueness: if a milestone is marked DONE in state/must_stay_true, you must not depict it happening again. If marked NOT_YET, you must not depict it happening now.
Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
Inventory contract: track item ownership and container location per character or container label; items do not teleport.
Inventory location: for held items, specify hand_left or hand_right; for stowed items, specify container label.
Prose hygiene: never use internal ids or container codes in prose (CHAR_*, ITEM_*, THREAD_*, hand_left/hand_right). Use human-readable phrasing in narrative ("left hand", "right hand", "Artie", "his wallet").
Item naming (canonical + anchored aliases): item_id is reserved for JSON/patches only. For durable items, the canonical display_name must appear in prose at first introduction (same paragraph or within the next 2 sentences). After anchoring, descriptive references are allowed if unambiguous in the scene. Any custody change (drop/pick up/hand off/stow/equip/transfer) must include the canonical display_name in the same sentence.
Appearance contract: appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change. When a prompt requires APPEARANCE_CHECK, it must match appearance_current (alias-aware). Attire boundary: wearables are inventory-owned; do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
State contract: you must create and maintain key state data each scene. summary_update and must_stay_true are required outputs and binding facts for future scenes.
Continuity system contract: if mechanics/UI are present, all numeric values and mechanic labels must be sourced from continuity system state or explicitly updated in the state_patch using continuity system updates.
UI gate: UI/system blocks (lines starting with '[' and ending with ']') are permitted only when scene_card.ui_allowed=true. If ui_allowed=false, do not include UI blocks even if an author persona says "always include".
Continuity system scope: this includes stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, and future mechanic families not yet seen, that must be tracked as they are introduced.
Durable transfer contract: every transfer_updates entry must include item_id and reason as required schema properties.
JSON contract: all *_updates fields are arrays of objects (even when single). appearance_updates is an object, not an array.
Inventory alignment contract: inventory_alignment_updates must be an array of objects, not a wrapper object.
Invariant carry-forward: if an invariant still holds, restate it in must_stay_true; do not drop it unless explicitly removing a stale fact with REMOVE and restating the current truth.
Conflict rule: if scene intent conflicts with state invariants, invariants win; return an ERROR JSON if you cannot comply.
Never recap at scene openings.
Do not repeat previous prose.



```

## proposed_refactor_v1\compiled\write.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\compiled\write.md`

```plaintext
﻿# WRITE
Write the scene described by the scene card.
- YOU MUST ALWAYS RETURN PROSE AND THE STATE_PATCH.
- Start in motion. No recap.
- Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
- Use the continuity pack and state for continuity.
- Use character_registry to keep names consistent in prose.
- Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
- State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
- Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
- Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
- Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])

- For held items, specify container=hand_left or container=hand_right.
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
Durable vs ephemeral mechanics:
- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, do not include UI blocks; rephrase into narrative prose.
- UI/system readouts must be on their own line, starting with '[' and ending with ']'.
- Do NOT embed bracketed UI in narrative sentences.
- Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).

- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- If item_registry or plot_devices are provided, they are canonical durable-state references for ownership/custody labels in authoritative outputs.
- Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
- APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).

Durable item naming discipline:
- When you first describe a durable item, anchor it by using the canonical display_name within the same paragraph (or within the next 2 sentences).
- After anchoring, you may use brief descriptors for style if unambiguous.
- During any custody/handling change, include the canonical display_name in that sentence.
- If a required event is not in the Scene Card, do not perform it.
- Enforce scene-card durable constraints: honor `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, and `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
- Respect `timeline_scope` and `ontological_scope` when proposing durable mutations; do not mutate physical custody in non-present/non-real scope unless explicitly marked override.
- Scope override rule (non-present / non-real scenes):
  - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
- summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
- STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.

- must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.

- If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.

- Return prose plus a state_patch JSON block.
STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).

- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
- Include character_continuity_system_updates for cast_present_ids when mechanics change.
  - Use set/delta/remove/reason.
  - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  - If a new mechanic family appears, add it under set with a stable key.
- Include global_continuity_system_updates only if global mechanics change.
- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}

  - appearance_updates MUST be an object under character_updates.
    - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
  - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
  - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If you mutate durable state, do not leave the same mutation only in prose.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
- appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.
  - appearance_updates MUST be an object, not an array.
    - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
  - appearance_updates.set may include atoms and marks only (canonical truth).
    - Do NOT put marks_add at the top level; it belongs under set.
    - Use set.marks_add / set.marks_remove for marks changes.
    - Use set.atoms for atom changes.
  - appearance_updates.reason is required (brief, factual).
  - Do NOT set summary or art text in appearance_updates (derived after acceptance)
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - character_updates.inventory MUST be an array of objects, never string item ids.
  - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:

  - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.

  - inventory: CHAR_example -> shard (carried, container=satchel)
  - inventory: CHAR_example -> longsword (carried, container=hand_right)
  - container: satchel (owner=CHAR_example, contents=[shard, maps])
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
  - injury: right forearm scar / left arm filament
  - ownership: shard (carried) / shard (bound but physical)

Scene card:
{{scene_card}}

Continuity pack:
{{continuity_pack}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

Style anchor:
{{style_anchor}}

State:
{{state}}

Output (required, no code fences):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>

Current arm-side / inventory facts: <from must_stay_true>

Durable changes committed: <final durable values to record in continuity updates>

APPEARANCE_CHECK:
- CHAR_ID: <4-8 tokens from atoms/marks>

PROSE:
<scene prose>
STATE_PATCH:
<json>

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

JSON Contract Block (strict; arrays only):
- All *_updates must be arrays of objects, even when there is only one update.
- INVALID vs VALID examples:
  - item_registry_updates:
    - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
    - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates:
    - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
    - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
  - transfer_updates:
    - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
    - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
  - inventory_alignment_updates:
    - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
    - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
  - global_continuity_system_updates:
    - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
    - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- custodian must be a non-null string id or "world"; never null.






```

## proposed_refactor_v1\fragments\phase\appearance_projection\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\appearance_projection\seg_01.md`

```plaintext
﻿# APPEARANCE PROJECTION
You are generating a derived appearance summary (and optional art prompt) from canonical appearance atoms/marks.
Return ONLY a JSON object. No prose, no commentary, no code fences.

Rules:
- Do NOT change atoms/marks. They are canonical input.
- Summary must be 2-4 sentences, durable and identity-level (no transient grime, no scene events).
- Avoid inventory/attire unless the input explicitly marks a signature outfit.
- Prefer canonical atom terms; do not invent new traits.
- If you include appearance_art, it must be derived strictly from atoms/marks and signature outfit (if any).

Output JSON:
{
  "summary": "...",
  "appearance_art": {
    "base_prompt": "...",
    "current_prompt": "...",
    "negative_prompt": "...",
    "tags": ["..."]
  }
}

Inputs:
Character:
{{character}}

Appearance base (canon):
{{appearance_base}}

Appearance current (canonical atoms/marks):
{{appearance_current}}


```

## proposed_refactor_v1\fragments\phase\author_generate\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\author_generate\seg_01.md`

```plaintext
﻿# AUTHOR GENERATION

You are generating an original author persona for BookForge.

Return ONLY a single JSON object. Do not include markdown, code fences, or extra commentary.
The JSON must be strict (double quotes, no trailing commas).

Required top-level keys:
- author (object)
- author_style_md (string)
- system_fragment_md (string)

Optional top-level key:
- banned_phrases (array of strings) only if the author is known for very specific phrases.

author object required keys:
- persona_name (string)
- influences (array of objects with name and weight; infer weights if not provided)
- trait_profile (object)
- style_rules (array of strings)
- taboos (array of strings)
- cadence_rules (array of strings)

JSON shape example (fill with real values):
{
  "author": {
    "persona_name": "",
    "influences": [
      {"name": "", "weight": 0.0}
    ],
    "trait_profile": {
      "voice": "",
      "themes": [],
      "sensory_bias": "",
      "pacing": ""
    },
    "style_rules": [],
    "taboos": [],
    "cadence_rules": []
  },
  "author_style_md": "",
  "system_fragment_md": ""
}

Influences: {{influences}}

Persona name (optional): {{persona_name}}

Notes: {{notes}}

Additional prompt text: {{prompt_text}}


```

## proposed_refactor_v1\fragments\phase\characters_generate\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\characters_generate\seg_01.md`

```plaintext
﻿# CHARACTERS GENERATE

You are refining outline character stubs into canon character entries and initial per-book character state.
Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Do not invent new characters; expand only the outline-provided stubs.

Required top-level keys:
- schema_version ("1.0")
- characters (array)

Each character object must include:
- character_id
- name
- pronouns
- role
- persona (object)
- inventory (array)
- containers (array)
- invariants (array of strings)
- appearance_base (object)

Recommended mechanic seed key (dynamic):
- character_continuity_system_state (object)
  - Include any starting mechanics known at setup time.
  - Examples: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses.
  - titles must be an array of objects (not strings).
  - You may add future mechanic families if relevant.
  - Use dynamic continuity families as needed: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, system_tracking_metadata, extended_system_data.
  - For LitRPG-like systems, prefer structured stats/skills/titles in character_continuity_system_state.

Appearance guidance (durable, canonical):
- appearance_base is the canon self-image for this character.
- Include: summary, atoms, marks, alias_map.
- Atoms are normalized traits (species, sex_presentation, age_band, height_band, build, hair_color, hair_style, eye_color, skin_tone).
- marks are durable identifiers (scars, tattoos, prosthetics). No temporary grime or wounds.
- alias_map lists acceptable synonyms for lint tolerance (e.g., hair_color: ["dark brown"]).
- appearance_current will be derived from appearance_base for the book unless explicitly overridden later.

Naming and durable item guidance:
- For items, use a human-readable item_name; do not use ITEM_* ids in prose strings.
- Reserve ITEM_* ids for canonical JSON only; do not use them in prose strings.
- If you emit an item_id here, include item_name as a human label.

Starting scene alignment (important):
- The initial inventory/containers/state must prepare each character for the book's first scene.
- Use the Book + Outline characters in THIS prompt as your source of truth for the opening situation.
- If the opening situation is unclear, default to a neutral, plausible posture (hands free, items stowed).
- Example: office/briefing -> no weapons held; battle opener -> weapon may be in hand; travel -> stowed gear.

Persona guidance (compact, factual):
- core_traits (array)
- motivations (array)
- fears (array)
- values (array)
- voice_notes (array)
- arc_hint (string)

Inventory rules:
- Every carried/held item must include a container location.
- Use explicit container labels (satchel, belt, pack, hand_left, hand_right, sheath, etc.).
- If an item is held, container must be hand_left or hand_right.
- If you use item_id, include item_name (human label) on the same inventory entry. The item_name must be human readable and not an escaped id value.
- Prefer item_name in prose-facing fields; item_id only in canonical JSON.
- Containers are tracked separately in containers[] with owner and contents.

Invariant phrasing (use exact strings where possible):
- inventory: <CHAR_ID> -> <item> (status=carried|stowed|equipped, container=<container_label>)
- container: <container_label> (owner=<CHAR_ID>, contents=[item1, item2])
- injury: <character_id> <injury/location>

Book:
{{book}}

Outline characters:
{{outline_characters}}

Outline opening context (chapter/section/scene 1):
{{outline_opening}}

Series info (if any):
{{series}}

Output JSON:
{
  "schema_version": "1.0",
  "characters": [
    {
      "character_id": "CHAR_example",
      "name": "",
      "pronouns": "",
      "role": "",
      "persona": {
        "core_traits": [],
        "motivations": [],
        "fears": [],
        "values": [],
        "voice_notes": [],
        "arc_hint": ""
      },
      "appearance_base": {
        "summary": "",
        "atoms": {
          "species": "human",
          "sex_presentation": "",
          "age_band": "",
          "height_band": "",
          "build": "",
          "hair_color": "",
          "hair_style": "",
          "eye_color": "",
          "skin_tone": ""
        },
        "marks": [
          {"name": "", "location": "", "durability": "durable"}
        ],
        "alias_map": {
          "hair_color": [""],
          "eye_color": [""]
        }
      },
      "character_continuity_system_state": {
        "stats": {"hp": {"current": 10, "max": 10}},
        "skills": {"sword": 1},
        "titles": [{"name": "Novice", "source": "starting_class", "active": true}],
        "resources": {"mana": {"current": 5, "max": 5}}
      },
      "inventory": [
        {"item_id": "ITEM_longsword", "item_name": "Longsword", "status": "carried", "container": "hand_right"}
      ],
      "containers": [
        {"container": "satchel", "owner": "CHAR_example", "location": "shoulder_left", "contents": ["maps"]}
      ],
      "invariants": [
        "inventory: CHAR_example -> longsword (status=carried, container=hand_right)",
        "container: satchel (owner=CHAR_example, contents=[maps])"
      ]
    }
  ]
}


```

## proposed_refactor_v1\fragments\phase\continuity_pack\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\continuity_pack\seg_01.md`

```plaintext
﻿# CONTINUITY PACK

Create a continuity pack JSON object with these fields:
- scene_end_anchor: 2-4 factual sentences about how the last scene ended (no prose).
- constraints: list of immediate continuity constraints.
- open_threads: list of active thread ids.
- cast_present: list of character names present next.
- location: location id or name.
- next_action: the implied next action.
- summary: echo state.summary (facts-only arrays; do not paraphrase).

Return ONLY JSON.

Rules:
- Use only characters listed in scene_card.cast_present. Do not introduce new names.
- summary must match state.summary and remain facts-only; do not add prose.
- constraints must include the highest-priority invariants from summary.must_stay_true and summary.key_facts_ring (copy exact strings when possible).
- constraints must include the highest-priority inventory/container invariants from summary.must_stay_true (copy exact strings when possible).
- If character_states are provided, prefer their inventory/container facts and continuity mechanic facts; do not invent conflicting values.
- If item_registry or plot_devices are provided, reuse canonical names/ids in constraints when referencing durable items/devices.
- Prefer item_registry.items[].display_name for prose references; reserve item_id for canonical JSON. The display_name must be human readable and not an escaped id/name.
- If state.global_continuity_system_state contains canonical mechanic labels/values, reuse those exact labels in constraints.
- If scene_card.cast_present is empty, cast_present must be an empty array.
- open_threads must be a subset of thread_registry thread_id values.
- If scene_card.thread_ids is present, prefer those thread ids.
- Do not invent new thread ids or character names.

Scene card:
{{scene_card}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

State:
{{state}}

Summary (facts-only):
{{summary}}

Recent facts:
{{recent_facts}}
Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}


```

## proposed_refactor_v1\fragments\phase\lint\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\lint\seg_01.md`

```plaintext
﻿# LINT

Check the scene for continuity, invariant violations, and duplication.
Flag invariant contradictions against must_stay_true/key facts.
Return ONLY JSON matching the lint_report schema.
- Classify UI/prose mechanic claims as DURABLE or EPHEMERAL before enforcing.
  - DURABLE: persistent stats/caps, skills/titles acquired, lasting status effects, inventory/custody, named mechanics referenced as invariants.
  - EPHEMERAL: roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat telemetry.
- Enforce DURABLE claims against authoritative_surfaces/state/registries.
- EPHEMERAL claims do not require state ownership; only flag EPHEMERAL contradictions inside the same scene as warnings.
- UI gate:
  - If scene_card.ui_allowed=false and any authoritative UI blocks appear, emit issue code 'ui_gate_violation' (severity depends on lint mode).
  - If ui_allowed is missing and UI blocks appear, emit 'ui_gate_unknown' (warning) requesting explicit ui_allowed; do not fail solely for missing flag.
  - Inline bracketed UI (e.g., [HP: 1/1]) is still UI and should be gated the same way; do not embed UI mid-sentence.
- If uncertain, default to EPHEMERAL (warning at most), not DURABLE (error).
- status="fail" only if there is at least one issue with severity="error"; warnings alone => status="pass".
- Item naming enforcement scope:
  - Do not require that every mention in narrative prose use display_name.
  - Enforce canonical display_name for: (a) anchoring at first introduction (same paragraph or within the next 2 sentences),
    (b) any custody-change sentence (drop/pick up/hand off/stow/equip/transfer), and (c) any case where a descriptor is ambiguous among multiple durable items in the scene.
  - Otherwise, treat non-canonical descriptive references as warnings at most.
- Prose hygiene: flag internal ids or container codes in narrative prose (CHAR_, ITEM_, THREAD_, DEVICE_, hand_left, hand_right).
- Naming severity policy:
  - warning: unambiguous descriptor used post-anchor.
  - error: missing anchor, descriptor used during custody-change without canonical name, or ambiguity risk.

- Appearance enforcement (authoritative surface):
  - APPEARANCE_CHECK is authoritative for cast_present_ids.
  - Compare APPEARANCE_CHECK tokens to appearance_current atoms/marks (alias-aware).
  - If APPEARANCE_CHECK contradicts appearance_current, emit error code "appearance_mismatch".
  - Prose-only appearance contradictions are warnings unless explicitly durable and uncorrected in-scene.
  - If prose depicts a durable appearance change but scene_card.durable_appearance_changes does not include it and no appearance_updates are present, emit error code "appearance_change_undeclared".
  - If APPEARANCE_CHECK is missing for a cast member, emit warning code "appearance_check_missing".
- For authoritative surfaces, prefer exact canonical item/device labels from registries.
- For milestone repetition/future checks, compare against PRE-INVARIANTS only (pre-scene canon).
- For ownership/consistency checks, compare against POST-STATE (post-patch candidate).
- POST-STATE is canonical; character_states is a derived convenience view. If they contradict, emit pipeline_state_incoherent.
- Check for POV drift vs book POV (no first-person in third-person scenes).
  - Ignore first-person pronouns inside quoted dialogue; only narration counts.
- Deterministically enforce scene-card durable constraints (required_in_custody, required_scene_accessible, forbidden_visible, device_presence; optional required_visible_on_page).
- Durable constraint evaluation must use POST-STATE candidate (after patch), not pre-state.
- Report missing durable context ids with explicit retry hints instead of guessing canon.
- Input consistency check (mandatory, before issuing continuity/durable errors):
  - If MUST_STAY_TRUE invariants contradict the provided post-patch candidate character state, treat this as an upstream snapshot error.
  - In that case emit a single error issue with code "pipeline_state_incoherent" including evidence of the invariant and the conflicting state field.
  - Do NOT emit additional continuity errors for the same fields when pipeline_state_incoherent is present.
- must_stay_true removals:
  - Lines starting with "REMOVE:" are deletion directives, not invariants.
  - Ignore REMOVE lines when checking contradictions.
  - If a REMOVE directive targets a fact, treat that fact as non-canonical even if it appears earlier in must_stay_true.
- If pipeline_state_incoherent is present, issues MUST contain exactly one issue.
- For each issue, include evidence when possible (line number + excerpt) as {"evidence": {"line": N, "excerpt": "..."}}.
- Evaluate consistency over the full scope of the scene, not a single snapshot.
  - Transitional state: a temporary mismatch later corrected or superseded within this scene.
  - Durable violation: a mismatch that persists through the end of the scene or ends unresolved.
  - You MUST read the entire scene and build a minimal timeline of explicit state claims/updates (UI lines, inventory changes, title/skill changes, location/time claims).
  - If you detect an apparent inconsistency, you MUST search forward for later updates that resolve or supersede it.
  - Only produce FAIL for durable violations. If resolved within the scene, do NOT FAIL; at most emit a warning.
  - When the same stat appears multiple times, the last occurrence in the scene is authoritative unless an explicit rollback is stated.
  - Any durability violation must cite both the conflicting line and the lack of later correction (or state "no later correction found").

Required keys:
- schema_version ("1.0")
- status ("pass" or "fail")
- issues (array of objects)

Each issue object must include:
- code
- message
Optional:
- severity
- evidence

If there are no issues, return:
{
  "schema_version": "1.0",
  "status": "pass",
  "issues": []
}

If there are issues, return:
{
  "schema_version": "1.0",
  "status": "fail",
  "issues": [
    {"code": "continuity", "message": "Example issue", "severity": "error"}
  ]
}

Scene:
{{prose}}

Scene card:
{{scene_card}}

Authoritative surfaces:
{{authoritative_surfaces}}

Appearance check (authoritative):
{{appearance_check}}

Character states (post-patch candidate, per cast_present_ids):
{{character_states}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

Pre-state (before patch):
{{pre_state}}

Pre-summary (facts-only):
{{pre_summary}}

Pre-invariants (must_stay_true + key facts):
{{pre_invariants}}

Post-state candidate (after patch):
{{post_state}}

Post-summary (facts-only):
{{post_summary}}

Post-invariants (must_stay_true + key facts):
{{post_invariants}}




```

## proposed_refactor_v1\fragments\phase\outline\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\outline\seg_01.md`

```plaintext
﻿# OUTLINE

You are the outline planner. Create a compact outline for the book.
Return ONLY a single JSON object that matches the outline schema v1.1.
No markdown, no code fences, no commentary.
Keep summaries concise but in the author voice from the system prompt.

Core contract: each SCENE is one scene to be written (scene == writing unit).
Scenes must vary per chapter. Do NOT use a fixed scene count.

Sections are required:
- Every chapter must include a sections array.
- Typical chapters should have 3-8 sections (target).
- A simple/interlude chapter may use 2-4 sections (rare).
- Each section usually has 2-6 scenes.
- A 1-scene section is allowed only for a stinger/hook moment.
- Total scenes per chapter should naturally land in 6-32, varying by complexity.

Scene quality rules:
- Each scene must include type and outcome.
- outcome must be a concrete state change.
- Do not pad with travel/recap/mood-only scenes.
If a user prompt is provided, treat it as grounding context. Integrate its details, but keep the schema and scene rules.


Chapter role vocabulary (prefer one):
- hook, setup, pressure, reversal, revelation, investigation, journey, trial, alliance, betrayal, siege, confrontation, climax, aftermath, transition, hinge
If it truly does not fit, use the closest role; custom roles are allowed but should be 1-2 words.

Scene type vocabulary (prefer one):
- setup, action, reveal, escalation, choice, consequence, aftermath, transition
If it truly does not fit, use the closest type; custom types are allowed but should be 1-2 words.

Tempo values (prefer one):
- slow_burn, steady, rush
If it truly does not fit, use the closest tempo; custom values are allowed but should be 1-2 words.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Optional top-level keys (recommended):
- threads (array of thread stubs)
- characters (array of character stubs)

Each chapter must include:
- chapter_id
- title
- goal
- chapter_role
- stakes_shift
- bridge (object with from_prev, to_next)
- pacing (object with intensity, tempo, expected_scene_count; expected_scene_count is a soft target)
- sections (array)

Each section must include:
- section_id
- title
- intent
- scenes (array of scene objects)

Optional section keys:
- section_role

Each scene must include:
- scene_id
- summary
- type
- outcome
- characters (array of character_id values present in the scene)

Optional scene keys:
- introduces (array of character_id values introduced in the scene)
- threads (array of thread_id values touched in the scene)
- callbacks (array of ids: character/thread/lore references)

Character stub format:
{
  "character_id": "CHAR_<slug>",
  "name": "",
  "pronouns": "",
  "role": "",
  "intro": {"chapter": 1, "scene": 1}
}

Thread stub format:
{
  "thread_id": "THREAD_<slug>",
  "label": "",
  "status": "open"
}

Output ordering guidance:
- Write chapters first. After chapters, list threads and characters at the end of the JSON object.

JSON shape example (fill with real values):
{
  "schema_version": "1.1",
  "chapters": [
    {
      "chapter_id": 1,
      "title": "",
      "goal": "",
      "chapter_role": "hook",
      "stakes_shift": "",
      "bridge": {"from_prev": "", "to_next": ""},
      "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 10},
      "sections": [
        {
          "section_id": 1,
          "title": "",
          "intent": "",
          "scenes": [
            {"scene_id": 1, "summary": "", "type": "setup", "outcome": "", "characters": ["CHAR_new_character_name"], "introduces": ["CHAR_new_character_name"]}
          ]
        }
      ]
    },
    {
      "chapter_id": 2,
      "title": "",
      "goal": "",
      "chapter_role": "setup",
      "stakes_shift": "",
      "bridge": {"from_prev": "", "to_next": ""},
      "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 8},
      "sections": [
        {
          "section_id": 1,
          "title": "",
          "intent": "",
          "scenes": [
            {"scene_id": 1, "summary": "", "type": "transition", "outcome": "", "characters": ["CHAR_new_character_name"]}
          ]
        }
      ]
    }
  ],
  "threads": [
    {"thread_id": "THREAD_prophecy", "label": "The Awakened Sage", "status": "open"}
  ],
  "characters": [
    {"character_id": "CHAR_new_character_name", "name": "New Character", "pronouns": "they/them", "role": "protagonist", "intro": {"chapter": 1, "scene": 1}}
  ]
}

Book:
{{book}}

Targets:
{{targets}}

User prompt (optional, may be empty):
{{user_prompt}}

Notes:
{{notes}}


```

## proposed_refactor_v1\fragments\phase\output_contract\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\output_contract\seg_01.md`

```plaintext
﻿Output must follow the requested format.
JSON blocks must be valid and schema-compliant.
All required keys and arrays must be present.
When a prompt specifies required counts or ranges, treat them as hard constraints.
Do not collapse arrays below the stated minimums.
If multiple output blocks are required (e.g. PROSE and STATE_PATCH), include all blocks in order.
If output must be JSON only, return a single JSON object with no commentary or code fences.
When creating outlines, the total scenes per chapter (sum of sections[].scenes[]) must match chapters[].pacing.expected_scene_count.
If a prompt requires a COMPLIANCE or PREFLIGHT block, include it before PROSE.
Durable vs ephemeral mechanics:
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
For durable items, prose must use display_name; item_id is reserved for JSON/patches. The display_name must be human readable and not an escaped id/name.
For durable mutations, every `transfer_updates[]` object must include `item_id` and `reason` (non-empty string).
`inventory_alignment_updates` must be an array of objects (no wrapper object with `updates`).
Use canonical continuity keys: character_continuity_system_updates and global_continuity_system_updates.


```

## proposed_refactor_v1\fragments\phase\plan\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\plan\seg_01.md`

```plaintext
﻿# PLAN

You are the planner. Use the outline window and state to create the next scene card.
Return ONLY a single JSON object that matches the scene_card schema.
No markdown, no code fences, no commentary. Use strict JSON (double quotes, no trailing commas).

If outline_window includes character information, keep those character ids in mind.
If character_states are provided, keep inventory/persona/continuity mechanics consistent; do not invent conflicting facts.
If outline_window.current.introduces is present, the scene must introduce those characters.
If recent_lint_warnings include ui_gate_unknown, set ui_allowed explicitly for this scene.

Required keys:
- schema_version ("1.1")
- scene_id
- chapter
- scene
- scene_target
- goal
- conflict
- required_callbacks (array)
- constraints (array)
- end_condition
- ui_allowed (boolean; true only when System/UI is active in this scene)

Recommended keys (use ids from the outline; do not invent ids):
- cast_present (array of character names for prose guidance)
- cast_present_ids (array of character ids, e.g. CHAR_Eldrin)
- introduces (array of character names introduced in this scene)
- introduces_ids (array of character ids introduced in this scene)
- thread_ids (array of thread ids, e.g. THREAD_Awakened_Sage)

Optional continuity-planning keys:
- required_in_custody (array of item/device ids that must still be owned by scene start)
- required_scene_accessible (array of item/device ids that must be retrievable without continuity break)
- required_visible_on_page (array of ids that must be explicitly shown in-scene; use sparingly)
- forbidden_visible (array of ids that must not be visibly carried/active in-scene)
- device_presence (array of plot-device ids expected to matter in-scene)
- transition_type (string, e.g. "time_skip", "travel_arrival", "combat_aftermath")
- timeline_scope ("present"|"flashback"|"dream"|"simulation"|"hypothetical")
- ontological_scope ("real"|"non_real")

Optional genre/system keys:
- continuity_system_focus (array of mechanic domains likely to change this scene, e.g. ["stats", "resources", "titles"])
- ui_mechanics_expected (array of UI labels likely to appear, e.g. ["HP", "Stamina", "Crit Rate"])
  - If ui_allowed=false, ui_mechanics_expected MUST be an empty array.

JSON shape example (fill with real values):
{
  "schema_version": "1.1",
  "scene_id": "SC_001_001",
  "chapter": 1,
  "scene": 1,
  "scene_target": "Protagonist commits to the journey.",
  "goal": "Force a decisive choice.",
  "conflict": "Safety versus obligation.",
  "required_callbacks": [],
  "constraints": ["target_words: 1900"],
  "end_condition": "The protagonist leaves home.",
  "ui_allowed": false,
  "cast_present": ["Eldrin"],
  "cast_present_ids": ["CHAR_Eldrin"],
  "introduces": [],
  "introduces_ids": [],
  "thread_ids": ["THREAD_Awakened_Sage"],
  "required_in_custody": ["ITEM_broken_tutorial_sword"],
  "required_scene_accessible": ["ITEM_broken_tutorial_sword"],
  "required_visible_on_page": [],
  "forbidden_visible": [],
  "device_presence": ["DEVICE_anomaly_tag"],
  "transition_type": "travel_arrival",
  "timeline_scope": "present",
  "ontological_scope": "real",
  "continuity_system_focus": ["stats", "resources"],
  "ui_mechanics_expected": ["HP", "Stamina"]
}

Outline window:
{{outline_window}}

Character states (per outline_window.current.characters):
{{character_states}}

State:
{{state}}

Recent lint warnings (prior scene, if any):
{{recent_lint_warnings}}

Task:
Create the next scene card.



```

## proposed_refactor_v1\fragments\phase\preflight\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\preflight\seg_01.md`

```plaintext
﻿# PREFLIGHT

You are the scene state preflight aligner.
Return ONLY a single JSON object that matches the state_patch schema.
No markdown, no code fences, no commentary.

Your job is to align state before writing starts for this scene.
- Output ONLY a STATE_PATCH-equivalent JSON object.
- Do not write prose.
- This pass can update inventory posture and continuity system state for cast/global scope.
- The primary goal is make changes as needed to setup the next scene.
- If uncertain, prefer leaving values unchanged.

Hard rules:
- State ownership is mandatory: if you change mechanics, write them in canonical updates.
- If a value is not changed in patch, it is treated as unchanged.
- Do not invent new character ids or thread ids.
- Keep updates scoped to current cast and global continuity only.
- Do not emit cursor_advance, summary_update, duplication counters, or chapter rollup changes.
- Keep timeline lock: only prepare state needed for the current scene card.
- Respect scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`, and optional `required_visible_on_page`.
- Respect scene scope gates: `timeline_scope` and `ontological_scope`; only use scope override when explicitly justified by reason_category.


```

## proposed_refactor_v1\fragments\phase\preflight\seg_02.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\preflight\seg_02.md`

```plaintext
﻿Transition gate (do-nothing by default):
- First decide whether this scene is a CONTINUATION or a DISCONTINUOUS TRANSITION.
- Treat as CONTINUATION when ALL are true:
  - scene_card.scene_target matches state.world.location, AND
  - scene_card.timeline_scope and scene_card.ontological_scope do not change relative to current state, AND
  - scene_card.transition_type is empty OR clearly indicates continuity (e.g., "continuous", "beat", "direct_continuation"), AND
  - there is no durable-constraint violation to fix.
- If CONTINUATION:
  - Output the minimal patch: {"schema_version":"1.0"} (no other fields), unless a durable constraint is violated.
  - Do NOT "normalize" inventory posture or move items just to be scene-appropriate. Only fix actual contradictions.
- Treat as DISCONTINUOUS TRANSITION when ANY are true:
  - scene_card.scene_target differs from state.world.location, OR
  - scene_card.transition_type is present and not clearly continuous, OR
  - timeline_scope / ontological_scope indicates a scope shift, OR
  - cast_present for this scene differs materially from state.world.cast_present.

World alignment (only when needed for this scene):
- If state.world.location != scene_card.scene_target, set world_updates.location = scene_card.scene_target.
- If scene_card.cast_present_ids is provided and differs from state.world.cast_present, set world_updates.cast_present = scene_card.cast_present_ids.
- Do not modify world.time unless the scene card explicitly implies a non-present timeline_scope; if you must, record why in global_continuity_system_updates.

Hidden transition state policy:
- Posture changes (stowed/held/worn, hand->pack, pack->table, etc.) are allowed ONLY during DISCONTINUOUS TRANSITION, or to satisfy a durable constraint.
- Custody changes (an item is no longer in the character's possession / custodian changes scope) are NOT implied by posture changes.
  - If and only if custody changes, you MUST:
    - update item_registry_updates for that item (custodian + last_seen), and
    - include transfer_updates with a reason (and prefer adding expected_before).
- Never "drop" an item by omitting it from an inventory array. If an item leaves a character, represent it as an explicit transfer.

Inventory transition rules:
Appearance contract:
- appearance_current atoms/marks are canonical and must not be contradicted or mutated in preflight.
- Preflight does NOT invent or change appearance; only note missing appearance_current if present in character_states.
- Ensure carried/equipped/stowed posture is scene-appropriate.
- character_updates.inventory and inventory_alignment_updates.set.inventory must be arrays of inventory objects, never id strings.
- Preserve ownership and container consistency.
- For held items use `container=hand_left` or `container=hand_right`.

Durable-constraint compliance check (must run before output):
1) Resolve constraint tokens:
   - Treat entries in required_in_custody / required_scene_accessible / required_visible_on_page / forbidden_visible / device_presence as IDs when they look like IDs.
   - If an entry does not match an ID, attempt a best-effort lookup by name/alias in item_registry / plot_devices.
   - If still ambiguous, do not guess; leave unchanged and record the unresolved token in character_updates.notes for the most relevant cast member.
2) Enforce required_in_custody:
   - Ensure the specified item's custodian is the required character/scope.
   - Ensure the item appears in that character's inventory in an appropriate container/status.
3) Enforce forbidden_visible:
   - Ensure the item is not in hand_left/hand_right and not "worn/brandished/visible" status.
   - Prefer moving it to an existing container (pack/pouch/sheath) over inventing new containers.
4) Enforce required_scene_accessible / required_visible_on_page:
   - Accessible: item can be stowed but present in-scene.
   - Visible_on_page: item must be held/worn/placed such that the writer can naturally show it early.

Dynamic continuity rules:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
- Use canonical keys:
  - character_continuity_system_updates
  - global_continuity_system_updates


```

## proposed_refactor_v1\fragments\phase\preflight\seg_03.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\preflight\seg_03.md`

```plaintext
﻿- Update operations use set/delta/remove/reason.
- Dynamic mechanic families are allowed (stats, skills, titles, resources, effects, statuses, classes, custom systems).
- titles must be arrays of objects with stable `name` fields, never arrays of strings.
- Durable-state updates are authoritative and must be explicit in patch blocks.
- If inventory posture is changed for scene fit, include `inventory_alignment_updates` with `reason` and `reason_category`.
- If you emit inventory_alignment_updates, the reason MUST state the final posture (item + container + status) so downstream phases can reconcile must_stay_true. Do not omit posture intent.
- `inventory_alignment_updates` must be an array of objects; do not wrap it in an object with an `updates` key.
- If durable item custody or metadata changes, include `item_registry_updates` and/or `transfer_updates`.
- Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
- If plot-device custody or activation changes, include `plot_device_updates`.
- Never rely on prose implication for durable state mutation.
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).- Safety check for non-trivial changes:
  - When making a DISCONTINUOUS TRANSITION change that moves an item between containers, changes custody, or toggles a plot device:
    - include expected_before with the minimal prior snapshot you are relying on (e.g., prior container/status/custodian).
    - if expected_before does not match current state, prefer leaving unchanged and note the discrepancy in notes.
- Patch coupling rule:
  - If you emit inventory_alignment_updates for a character, you MUST also emit character_updates for that character with the final authoritative inventory/containers for this scene.
  - The inventory arrays in both places should match (alignment is the justification record; character_updates is the durable state).
- reason_category vocabulary (use one):
  - continuity_fix
  - constraint_enforcement
  - location_transition
  - time_skip
  - scope_shift
  - equipment_posture
  - custody_transfer
  - plot_device_state



```

## proposed_refactor_v1\fragments\phase\preflight\seg_04.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\preflight\seg_04.md`

```plaintext
﻿
Scene card:
{{scene_card}}

Current state:
{{state}}

Current summary:
{{summary}}

Character registry:
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (cast only):
{{character_states}}

Immediate previous scene (if available):
{{immediate_previous_scene}}

Last appearance prose for cast members missing from immediate previous scene:
{{cast_last_appearance}}

Output JSON shape reminder:
{
  "schema_version": "1.0",
  "character_updates": [
    {
      "character_id": "CHAR_example",
      "chapter": 1,
      "scene": 2,
      "inventory": [{"item": "ITEM_example", "container": "pockets", "status": "stowed"}],
      "containers": [],
      "persona_updates": [],
      "invariants_add": [],
      "notes": ""
    }
  ],
  "character_continuity_system_updates": [
    {
      "character_id": "CHAR_example",
      "set": {
        "titles": [{"name": "Novice"}]
      },
      "delta": {},
      "remove": [],
      "reason": "align pre-scene state"
    }
  ],
  "global_continuity_system_updates": [],
  "inventory_alignment_updates": [
    {
      "character_id": "CHAR_example",
      "set": {"inventory": [{"item": "ITEM_example", "container": "hand_right", "status": "held"}], "containers": []},
      "reason": "scene posture alignment",
      "reason_category": "after_combat_cleanup"
    }
  ],
  "item_registry_updates": [],
  "plot_device_updates": [],
  "transfer_updates": []
}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}



```

## proposed_refactor_v1\fragments\phase\repair\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\repair\seg_01.md`

```plaintext
﻿# REPAIR

Fix the scene based on lint issues.
Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.


```

## proposed_refactor_v1\fragments\phase\repair\seg_02.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\repair\seg_02.md`

```plaintext
﻿Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
For held items, specify container=hand_left or container=hand_right.
Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
Durable vs ephemeral mechanics:
- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.
- UI/system readouts must be on their own line, starting with '[' and ending with ']'.
- Do NOT embed bracketed UI in narrative sentences.
- Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).

- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
- APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).

Naming repairs:
- If lint flags an item naming issue, fix it with minimal edits.
- Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
- Do not rename item_id or registry fields; only adjust prose wording.
summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
Enforce scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
Respect `timeline_scope` and `ontological_scope`.


```

## proposed_refactor_v1\fragments\phase\repair\seg_03.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\repair\seg_03.md`

```plaintext
﻿Return corrected prose plus a corrected state_patch JSON block.

Output format (required, no code fences, no commentary):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>
Current arm-side / inventory facts: <from must_stay_true>

APPEARANCE_CHECK:
- CHAR_ID: <4-8 tokens from atoms/marks>

PROSE:
<scene prose>

STATE_PATCH:
<json>

STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
- Include character_continuity_system_updates for cast_present_ids when mechanics change.
  - Use set/delta/remove/reason.
  - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  - If a new mechanic family appears, add it under set with a stable key.
- Include global_continuity_system_updates only if global mechanics change.


```

## proposed_refactor_v1\fragments\phase\repair\seg_04.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\repair\seg_04.md`

```plaintext
﻿- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}


```

## proposed_refactor_v1\fragments\phase\repair\seg_05.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\repair\seg_05.md`

```plaintext
﻿- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.


```

## proposed_refactor_v1\fragments\phase\repair\seg_06.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\repair\seg_06.md`

```plaintext
﻿  - inventory_alignment_updates[*].set MUST be an object (not a list).
    - INVALID: "set": []
    - VALID:   "set": {"inventory": [...], "containers": [...]}
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If you mutate durable state, do not leave the same mutation only in prose.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
- appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.


```

## proposed_refactor_v1\fragments\phase\repair\seg_07.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\repair\seg_07.md`

```plaintext
﻿  - appearance_updates.set may include atoms and marks only (canonical truth).
    - Do NOT put marks_add at the top level; it belongs under set.
    - Use set.marks_add / set.marks_remove for marks changes.
    - Use set.atoms for atom changes.
  - appearance_updates.reason is required (brief, factual).
  - Do NOT set summary or art text in appearance_updates (derived after acceptance)
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - character_updates.inventory MUST be an array of objects, never string item ids.
  - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
  - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.
  - inventory: CHAR_example -> shard (carried, container=satchel)
  - inventory: CHAR_example -> longsword (carried, container=hand_right)
  - container: satchel (owner=CHAR_example, contents=[shard, maps])
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
  - injury: right forearm scar / left arm filament
  - ownership: shard (carried) / shard (bound but physical)

Issues:
{{issues}}

Scene card:
{{scene_card}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

Scene:
{{prose}}

State:
{{state}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}



```

## proposed_refactor_v1\fragments\phase\state_repair\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\state_repair\seg_01.md`

```plaintext
﻿# STATE REPAIR

You are the state repair step. You must output a corrected STATE_PATCH JSON only.
No prose, no commentary, no code fences.

Goal:
- Ensure state_patch fully and accurately captures the scene's events and outcomes.
- Fill missing summary_update data and fix invalid formats from draft_patch.
- Preserve pre-scene invariants unless this scene changes them; when it does, update must_stay_true to the final end-of-scene value.
- must_stay_true reconciliation (mandatory):
  - If this scene changes a durable fact (stats/HP/status/title/custody), you MUST update must_stay_true to reflect the final end-of-scene value.
  - Remove or replace any prior must_stay_true entries that conflict with new durable values.
  - Do NOT carry forward conflicting legacy invariants once the scene updates them.


```

## proposed_refactor_v1\fragments\phase\state_repair\seg_02.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\state_repair\seg_02.md`

```plaintext
﻿- Ensure mechanic/UI ownership in continuity system updates.

Rules:
- Output a single JSON object that matches the state_patch schema.
- Use schema_version "1.0".
- Use scene_card.cast_present_ids for world_updates.cast_present.
- Use scene_card.thread_ids for world_updates.open_threads.
- Do not invent new character or thread ids.
- summary_update arrays are required: last_scene (2-4 sentences), key_events (3-7 bullets), must_stay_true (3-7 bullets), chapter_so_far_add (bullets).
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates
Durable vs ephemeral mechanics:
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.

- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene..
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
- If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
- Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If prose depicts a durable appearance change, include character_updates.appearance_updates with a reason.
- Do NOT set summary or art text in appearance_updates (derived after acceptance).

Naming repairs:
- If lint flags an item naming issue, fix it with minimal edits.
- Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
- Do not rename item_id or registry fields; only adjust prose wording.
- Do not add numeric mechanics to invariants_add; store them in continuity system updates instead.
- If an event appears in prose, it must appear in key_events.
- must_stay_true must include milestone ledger entries and any inventory/injury/ownership invariants implied by prose.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
- character_updates entries must use arrays: persona_updates (array), invariants_add (array).
- character_updates.inventory must be an array of objects, never item-id strings.
- Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
- Use character_continuity_system_updates / global_continuity_system_updates to reconcile mechanics.


```

## proposed_refactor_v1\fragments\phase\state_repair\seg_03.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\state_repair\seg_03.md`

```plaintext
﻿- If a new mechanic family appears in prose/UI, add it under set with a stable key.
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
- appearance_updates MUST be an object under character_updates.
    - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.


```

## proposed_refactor_v1\fragments\phase\state_repair\seg_04.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\state_repair\seg_04.md`

```plaintext
﻿  - inventory_alignment_updates[*].set MUST be an object (not a list).
    - INVALID: "set": []
    - VALID:   "set": {"inventory": [...], "containers": [...]}
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If durable mutation is implied but ambiguous, keep canonical state unchanged and emit an explicit repair note in reason fields.
- Honor scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
- Respect `timeline_scope` and `ontological_scope`; avoid physical custody changes in non-present/non-real scope unless explicit override is present.


```

## proposed_refactor_v1\fragments\phase\state_repair\seg_05.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\state_repair\seg_05.md`

```plaintext
﻿Inputs
- prose: final scene text
- state: pre-scene state
- draft_patch: patch returned by write/repair (may be incomplete)
- continuity_pack: pre-write continuity pack
- character_states: current cast-only character state

Scene card:
{{scene_card}}

Continuity pack:
{{continuity_pack}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

State (pre-scene):
{{state}}

Summary (facts-only):
{{summary}}

Draft state patch:
{{draft_patch}}

Prose:
{{prose}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}



```

## proposed_refactor_v1\fragments\phase\style_anchor\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\style_anchor\seg_01.md`

```plaintext
﻿# STYLE ANCHOR

Write a short style anchor excerpt (200-400 words) that demonstrates the desired voice and cadence.
Do not reference plot events or character names.
Return ONLY the excerpt text.
Output must be non-empty and between 200-400 words.
If you are unsure, write a neutral prose excerpt in the desired voice.

Author persona:
{{author_fragment}}


```

## proposed_refactor_v1\fragments\phase\system_base\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\system_base\seg_01.md`

```plaintext
﻿You are BookForge, a deterministic book-writing engine.
Follow the output contracts exactly.
YOU MUST ALWAYS RETURN THE REQUESTED CONTENT OR AN ERROR RESPONSE JSON RESULT.
Treat all schema requirements and numeric ranges as hard constraints.
If a prompt specifies required counts or ranges, you must satisfy them.
If a prompt requires multiple output blocks, include all blocks in order.
If registries or ids are provided, use only those; do not invent new ids.
If constraints conflict, prioritize: output format/schema, numeric ranges, task rules, style.
Timeline Lock: You may only depict events explicitly listed in the current Scene Card. You must not depict, imply, or resolve any later-scene milestone outcomes (including acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
State primacy: state invariants and summary facts are binding; do not contradict them.
Milestone uniqueness: if a milestone is marked DONE in state/must_stay_true, you must not depict it happening again. If marked NOT_YET, you must not depict it happening now.
Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
Inventory contract: track item ownership and container location per character or container label; items do not teleport.
Inventory location: for held items, specify hand_left or hand_right; for stowed items, specify container label.
Prose hygiene: never use internal ids or container codes in prose (CHAR_*, ITEM_*, THREAD_*, hand_left/hand_right). Use human-readable phrasing in narrative ("left hand", "right hand", "Artie", "his wallet").
Item naming (canonical + anchored aliases): item_id is reserved for JSON/patches only. For durable items, the canonical display_name must appear in prose at first introduction (same paragraph or within the next 2 sentences). After anchoring, descriptive references are allowed if unambiguous in the scene. Any custody change (drop/pick up/hand off/stow/equip/transfer) must include the canonical display_name in the same sentence.
Appearance contract: appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change. When a prompt requires APPEARANCE_CHECK, it must match appearance_current (alias-aware). Attire boundary: wearables are inventory-owned; do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
State contract: you must create and maintain key state data each scene. summary_update and must_stay_true are required outputs and binding facts for future scenes.
Continuity system contract: if mechanics/UI are present, all numeric values and mechanic labels must be sourced from continuity system state or explicitly updated in the state_patch using continuity system updates.
UI gate: UI/system blocks (lines starting with '[' and ending with ']') are permitted only when scene_card.ui_allowed=true. If ui_allowed=false, do not include UI blocks even if an author persona says "always include".
Continuity system scope: this includes stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, and future mechanic families not yet seen, that must be tracked as they are introduced.
Durable transfer contract: every transfer_updates entry must include item_id and reason as required schema properties.
JSON contract: all *_updates fields are arrays of objects (even when single). appearance_updates is an object, not an array.
Inventory alignment contract: inventory_alignment_updates must be an array of objects, not a wrapper object.
Invariant carry-forward: if an invariant still holds, restate it in must_stay_true; do not drop it unless explicitly removing a stale fact with REMOVE and restating the current truth.
Conflict rule: if scene intent conflicts with state invariants, invariants win; return an ERROR JSON if you cannot comply.
Never recap at scene openings.
Do not repeat previous prose.



```

## proposed_refactor_v1\fragments\phase\write\seg_01.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\write\seg_01.md`

```plaintext
﻿# WRITE
Write the scene described by the scene card.
- YOU MUST ALWAYS RETURN PROSE AND THE STATE_PATCH.
- Start in motion. No recap.
- Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
- Use the continuity pack and state for continuity.
- Use character_registry to keep names consistent in prose.
- Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
- State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
- Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.


```

## proposed_refactor_v1\fragments\phase\write\seg_02.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\write\seg_02.md`

```plaintext
﻿- Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
- Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])

- For held items, specify container=hand_left or container=hand_right.
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
Durable vs ephemeral mechanics:
- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, do not include UI blocks; rephrase into narrative prose.
- UI/system readouts must be on their own line, starting with '[' and ending with ']'.
- Do NOT embed bracketed UI in narrative sentences.
- Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).

- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- If item_registry or plot_devices are provided, they are canonical durable-state references for ownership/custody labels in authoritative outputs.
- Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
- APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).

Durable item naming discipline:
- When you first describe a durable item, anchor it by using the canonical display_name within the same paragraph (or within the next 2 sentences).
- After anchoring, you may use brief descriptors for style if unambiguous.
- During any custody/handling change, include the canonical display_name in that sentence.
- If a required event is not in the Scene Card, do not perform it.
- Enforce scene-card durable constraints: honor `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, and `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
- Respect `timeline_scope` and `ontological_scope` when proposing durable mutations; do not mutate physical custody in non-present/non-real scope unless explicitly marked override.


```

## proposed_refactor_v1\fragments\phase\write\seg_03.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\write\seg_03.md`

```plaintext
﻿- summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
- STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.

- must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.

- If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.

- Return prose plus a state_patch JSON block.
STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).

- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
- Include character_continuity_system_updates for cast_present_ids when mechanics change.
  - Use set/delta/remove/reason.
  - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  - If a new mechanic family appears, add it under set with a stable key.
- Include global_continuity_system_updates only if global mechanics change.


```

## proposed_refactor_v1\fragments\phase\write\seg_04.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\write\seg_04.md`

```plaintext
﻿- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}



```

## proposed_refactor_v1\fragments\phase\write\seg_05.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\write\seg_05.md`

```plaintext
﻿- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.


```

## proposed_refactor_v1\fragments\phase\write\seg_06.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\write\seg_06.md`

```plaintext
﻿- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If you mutate durable state, do not leave the same mutation only in prose.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
- appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.


```

## proposed_refactor_v1\fragments\phase\write\seg_07.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\phase\write\seg_07.md`

```plaintext
﻿  - appearance_updates.set may include atoms and marks only (canonical truth).
    - Do NOT put marks_add at the top level; it belongs under set.
    - Use set.marks_add / set.marks_remove for marks changes.
    - Use set.atoms for atom changes.
  - appearance_updates.reason is required (brief, factual).
  - Do NOT set summary or art text in appearance_updates (derived after acceptance)
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - character_updates.inventory MUST be an array of objects, never string item ids.
  - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:

  - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.

  - inventory: CHAR_example -> shard (carried, container=satchel)
  - inventory: CHAR_example -> longsword (carried, container=hand_right)
  - container: satchel (owner=CHAR_example, contents=[shard, maps])
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
  - injury: right forearm scar / left arm filament
  - ownership: shard (carried) / shard (bound but physical)

Scene card:
{{scene_card}}

Continuity pack:
{{continuity_pack}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

Style anchor:
{{style_anchor}}

State:
{{state}}

Output (required, no code fences):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>

Current arm-side / inventory facts: <from must_stay_true>

Durable changes committed: <final durable values to record in continuity updates>

APPEARANCE_CHECK:
- CHAR_ID: <4-8 tokens from atoms/marks>

PROSE:
<scene prose>
STATE_PATCH:
<json>

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}



```

## proposed_refactor_v1\fragments\shared\B001.must_stay_true_end_truth_line.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B001.must_stay_true_end_truth_line.md`

```plaintext
﻿- must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.


```

## proposed_refactor_v1\fragments\shared\B002.must_stay_true_reconciliation_block.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B002.must_stay_true_reconciliation_block.md`

```plaintext
﻿- must_stay_true reconciliation (mandatory):
  - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - Remove conflicting old invariants rather than preserving them.


```

## proposed_refactor_v1\fragments\shared\B003.must_stay_true_remove_block.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B003.must_stay_true_remove_block.md`

```plaintext
﻿- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).


```

## proposed_refactor_v1\fragments\shared\B004.scope_override_nonreal_rule.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B004.scope_override_nonreal_rule.md`

```plaintext
﻿- Scope override rule (non-present / non-real scenes):
  - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".


```

## proposed_refactor_v1\fragments\shared\B005.json_contract_block.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B005.json_contract_block.md`

```plaintext
﻿JSON Contract Block (strict; arrays only):
- All *_updates must be arrays of objects, even when there is only one update.
- INVALID vs VALID examples:
  - item_registry_updates:
    - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
    - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates:
    - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
    - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
  - transfer_updates:
    - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
    - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
  - inventory_alignment_updates:
    - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
    - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
  - global_continuity_system_updates:
    - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
    - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- custodian must be a non-null string id or "world"; never null.


```

## proposed_refactor_v1\fragments\shared\B006.global_continuity_array_guardrail.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B006.global_continuity_array_guardrail.md`

```plaintext
﻿- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]


```

## proposed_refactor_v1\fragments\shared\B007.transfer_registry_conflict_rule.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B007.transfer_registry_conflict_rule.md`

```plaintext
﻿- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
  - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
  - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.


```

## proposed_refactor_v1\fragments\shared\B008a.appearance_updates_object_under_character_updates.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B008a.appearance_updates_object_under_character_updates.md`

```plaintext
﻿  - appearance_updates MUST be an object under character_updates.
    - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}


```

## proposed_refactor_v1\fragments\shared\B008b.appearance_updates_not_array.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\fragments\shared\B008b.appearance_updates_not_array.md`

```plaintext
﻿  - appearance_updates MUST be an object, not an array.
    - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}


```

## proposed_refactor_v1\manifests\appearance_projection.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\appearance_projection.md.manifest.json`

```plaintext
﻿{
    "prompt":  "appearance_projection.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/appearance_projection/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/appearance_projection.md"
}

```

## proposed_refactor_v1\manifests\author_generate.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\author_generate.md.manifest.json`

```plaintext
﻿{
    "prompt":  "author_generate.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/author_generate/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/author_generate.md"
}

```

## proposed_refactor_v1\manifests\characters_generate.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\characters_generate.md.manifest.json`

```plaintext
﻿{
    "prompt":  "characters_generate.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/characters_generate/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/characters_generate.md"
}

```

## proposed_refactor_v1\manifests\continuity_pack.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\continuity_pack.md.manifest.json`

```plaintext
﻿{
    "prompt":  "continuity_pack.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/continuity_pack/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/continuity_pack.md"
}

```

## proposed_refactor_v1\manifests\lint.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\lint.md.manifest.json`

```plaintext
﻿{
    "prompt":  "lint.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/lint/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/lint.md"
}

```

## proposed_refactor_v1\manifests\outline.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\outline.md.manifest.json`

```plaintext
﻿{
    "prompt":  "outline.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/outline/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/outline.md"
}

```

## proposed_refactor_v1\manifests\output_contract.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\output_contract.md.manifest.json`

```plaintext
﻿{
    "prompt":  "output_contract.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/output_contract/seg_01.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B006.global_continuity_array_guardrail",
                        "path":  "fragments/shared/B006.global_continuity_array_guardrail.md"
                    }
                ],
    "expected_compiled":  "compiled/output_contract.md"
}

```

## proposed_refactor_v1\manifests\plan.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\plan.md.manifest.json`

```plaintext
﻿{
    "prompt":  "plan.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/plan/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/plan.md"
}

```

## proposed_refactor_v1\manifests\preflight.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\preflight.md.manifest.json`

```plaintext
﻿{
    "prompt":  "preflight.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/preflight/seg_01.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B004.scope_override_nonreal_rule",
                        "path":  "fragments/shared/B004.scope_override_nonreal_rule.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/preflight/seg_02.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B006.global_continuity_array_guardrail",
                        "path":  "fragments/shared/B006.global_continuity_array_guardrail.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/preflight/seg_03.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B005.json_contract_block",
                        "path":  "fragments/shared/B005.json_contract_block.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/preflight/seg_04.md"
                    }
                ],
    "expected_compiled":  "compiled/preflight.md"
}

```

## proposed_refactor_v1\manifests\repair.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\repair.md.manifest.json`

```plaintext
﻿{
    "prompt":  "repair.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/repair/seg_01.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B002.must_stay_true_reconciliation_block",
                        "path":  "fragments/shared/B002.must_stay_true_reconciliation_block.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B003.must_stay_true_remove_block",
                        "path":  "fragments/shared/B003.must_stay_true_remove_block.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/repair/seg_02.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B004.scope_override_nonreal_rule",
                        "path":  "fragments/shared/B004.scope_override_nonreal_rule.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/repair/seg_03.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B006.global_continuity_array_guardrail",
                        "path":  "fragments/shared/B006.global_continuity_array_guardrail.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/repair/seg_04.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B008a.appearance_updates_object_under_character_updates",
                        "path":  "fragments/shared/B008a.appearance_updates_object_under_character_updates.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/repair/seg_05.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B007.transfer_registry_conflict_rule",
                        "path":  "fragments/shared/B007.transfer_registry_conflict_rule.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/repair/seg_06.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B008b.appearance_updates_not_array",
                        "path":  "fragments/shared/B008b.appearance_updates_not_array.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/repair/seg_07.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B005.json_contract_block",
                        "path":  "fragments/shared/B005.json_contract_block.md"
                    }
                ],
    "expected_compiled":  "compiled/repair.md"
}

```

## proposed_refactor_v1\manifests\state_repair.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\state_repair.md.manifest.json`

```plaintext
﻿{
    "prompt":  "state_repair.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/state_repair/seg_01.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B003.must_stay_true_remove_block",
                        "path":  "fragments/shared/B003.must_stay_true_remove_block.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/state_repair/seg_02.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B006.global_continuity_array_guardrail",
                        "path":  "fragments/shared/B006.global_continuity_array_guardrail.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/state_repair/seg_03.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B007.transfer_registry_conflict_rule",
                        "path":  "fragments/shared/B007.transfer_registry_conflict_rule.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/state_repair/seg_04.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B004.scope_override_nonreal_rule",
                        "path":  "fragments/shared/B004.scope_override_nonreal_rule.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/state_repair/seg_05.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B005.json_contract_block",
                        "path":  "fragments/shared/B005.json_contract_block.md"
                    }
                ],
    "expected_compiled":  "compiled/state_repair.md"
}

```

## proposed_refactor_v1\manifests\style_anchor.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\style_anchor.md.manifest.json`

```plaintext
﻿{
    "prompt":  "style_anchor.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/style_anchor/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/style_anchor.md"
}

```

## proposed_refactor_v1\manifests\system_base.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\system_base.md.manifest.json`

```plaintext
﻿{
    "prompt":  "system_base.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/system_base/seg_01.md"
                    }
                ],
    "expected_compiled":  "compiled/system_base.md"
}

```

## proposed_refactor_v1\manifests\write.md.manifest.json

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\manifests\write.md.manifest.json`

```plaintext
﻿{
    "prompt":  "write.md",
    "version":  "proposed_refactor_v1",
    "entries":  [
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/write/seg_01.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B001.must_stay_true_end_truth_line",
                        "path":  "fragments/shared/B001.must_stay_true_end_truth_line.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B003.must_stay_true_remove_block",
                        "path":  "fragments/shared/B003.must_stay_true_remove_block.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/write/seg_02.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B004.scope_override_nonreal_rule",
                        "path":  "fragments/shared/B004.scope_override_nonreal_rule.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/write/seg_03.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B006.global_continuity_array_guardrail",
                        "path":  "fragments/shared/B006.global_continuity_array_guardrail.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/write/seg_04.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B008a.appearance_updates_object_under_character_updates",
                        "path":  "fragments/shared/B008a.appearance_updates_object_under_character_updates.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/write/seg_05.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B007.transfer_registry_conflict_rule",
                        "path":  "fragments/shared/B007.transfer_registry_conflict_rule.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/write/seg_06.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B008b.appearance_updates_not_array",
                        "path":  "fragments/shared/B008b.appearance_updates_not_array.md"
                    },
                    {
                        "kind":  "phase",
                        "path":  "fragments/phase/write/seg_07.md"
                    },
                    {
                        "kind":  "shared",
                        "block_id":  "B005.json_contract_block",
                        "path":  "fragments/shared/B005.json_contract_block.md"
                    }
                ],
    "expected_compiled":  "compiled/write.md"
}

```

## proposed_refactor_v1\reports\appearance_projection.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\appearance_projection.md.change_map.md`

```plaintext
﻿# Change Map: appearance_projection.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/appearance_projection.md`
- SHA256: `4F34AE9D7BFFB6BEEDC621275439D608DE1AC6C264BFAC2A5A07476F8AAAD92B`

## Composition Entries (Order)
1. phase  -> `fragments/phase/appearance_projection/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\author_generate.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\author_generate.md.change_map.md`

```plaintext
﻿# Change Map: author_generate.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/author_generate.md`
- SHA256: `F9B4C2ED12612212ECBE68DED33EEC0A9CC891C72C64DD0888096946E707709C`

## Composition Entries (Order)
1. phase  -> `fragments/phase/author_generate/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\characters_generate.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\characters_generate.md.change_map.md`

```plaintext
﻿# Change Map: characters_generate.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/characters_generate.md`
- SHA256: `38F3DE2E9DD446957E9BCF49D163C93B96B8DC032E0BEFBDC7072890BA33F47C`

## Composition Entries (Order)
1. phase  -> `fragments/phase/characters_generate/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\continuity_pack.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\continuity_pack.md.change_map.md`

```plaintext
﻿# Change Map: continuity_pack.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/continuity_pack.md`
- SHA256: `9E41A1B57F1DEB570FA05A57AC318D1395E317472136EC124B7598813BE37DD8`

## Composition Entries (Order)
1. phase  -> `fragments/phase/continuity_pack/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\lint.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\lint.md.change_map.md`

```plaintext
﻿# Change Map: lint.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/lint.md`
- SHA256: `451CE34C1E42EB6EA9AE0985BBE728D0BC23941A8CCAA338DA33CCDA5B4F4FAE`

## Composition Entries (Order)
1. phase  -> `fragments/phase/lint/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\outline.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\outline.md.change_map.md`

```plaintext
﻿# Change Map: outline.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/outline.md`
- SHA256: `C2BDD6FC3C2BF39460C026092956A68E24604359E0E78E3511FC3155BE6C8205`

## Composition Entries (Order)
1. phase  -> `fragments/phase/outline/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\output_contract.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\output_contract.md.change_map.md`

```plaintext
﻿# Change Map: output_contract.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/output_contract.md`
- SHA256: `067E2F6421C67AD60605CF2723691A8C6EFA55053E849645D8DB53F0E2884C68`

## Composition Entries (Order)
1. phase  -> `fragments/phase/output_contract/seg_01.md`
2. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)

## Reuse Summary
- Uses shared block `B006.global_continuity_array_guardrail`

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\plan.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\plan.md.change_map.md`

```plaintext
﻿# Change Map: plan.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/plan.md`
- SHA256: `A55E3C61B1F27B91B12A74676930E1EF9F7B7273D968A2FF8A449DFC1FCF3C90`

## Composition Entries (Order)
1. phase  -> `fragments/phase/plan/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\preflight.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\preflight.md.change_map.md`

```plaintext
﻿# Change Map: preflight.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/preflight.md`
- SHA256: `D05581CDE8C564447EF93F71E92DE73918480B50B859B3AF7A2461E48F7EECF2`

## Composition Entries (Order)
1. phase  -> `fragments/phase/preflight/seg_01.md`
2. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
3. phase  -> `fragments/phase/preflight/seg_02.md`
4. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
5. phase  -> `fragments/phase/preflight/seg_03.md`
6. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)
7. phase  -> `fragments/phase/preflight/seg_04.md`

## Reuse Summary
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\repair.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\repair.md.change_map.md`

```plaintext
﻿# Change Map: repair.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/repair.md`
- SHA256: `6171B0A6AF67580D96BF4FD6DCAD349A01A909E073FD9EC37D013E9346C5FB55`

## Composition Entries (Order)
1. phase  -> `fragments/phase/repair/seg_01.md`
2. shared -> `B002.must_stay_true_reconciliation_block` (`fragments/shared/B002.must_stay_true_reconciliation_block.md`)
3. shared -> `B003.must_stay_true_remove_block` (`fragments/shared/B003.must_stay_true_remove_block.md`)
4. phase  -> `fragments/phase/repair/seg_02.md`
5. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
6. phase  -> `fragments/phase/repair/seg_03.md`
7. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
8. phase  -> `fragments/phase/repair/seg_04.md`
9. shared -> `B008a.appearance_updates_object_under_character_updates` (`fragments/shared/B008a.appearance_updates_object_under_character_updates.md`)
10. phase  -> `fragments/phase/repair/seg_05.md`
11. shared -> `B007.transfer_registry_conflict_rule` (`fragments/shared/B007.transfer_registry_conflict_rule.md`)
12. phase  -> `fragments/phase/repair/seg_06.md`
13. shared -> `B008b.appearance_updates_not_array` (`fragments/shared/B008b.appearance_updates_not_array.md`)
14. phase  -> `fragments/phase/repair/seg_07.md`
15. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)

## Reuse Summary
- Uses shared block `B002.must_stay_true_reconciliation_block`
- Uses shared block `B003.must_stay_true_remove_block`
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B008a.appearance_updates_object_under_character_updates`
- Uses shared block `B007.transfer_registry_conflict_rule`
- Uses shared block `B008b.appearance_updates_not_array`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: dedupe repeated reconciliation blocks + block extraction.
- Removed duplicate lines:
  - `resources/prompt_templates/repair.md:55` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:56` -> 
  - `resources/prompt_templates/repair.md:57` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:58` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:60` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:61` -> 
  - `resources/prompt_templates/repair.md:62` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:63` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:65` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:66` -> 
  - `resources/prompt_templates/repair.md:67` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:68` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:82` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:83` -> 
  - `resources/prompt_templates/repair.md:84` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:85` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:87` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:88` -> 
  - `resources/prompt_templates/repair.md:89` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:90` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:108` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:109` -> 
  - `resources/prompt_templates/repair.md:110` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:111` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:134` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:135` -> 
  - `resources/prompt_templates/repair.md:136` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:137` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:189` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:190` -> 
  - `resources/prompt_templates/repair.md:191` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:192` ->   - Remove conflicting old invariants rather than preserving them.
  - `resources/prompt_templates/repair.md:194` -> - must_stay_true reconciliation (mandatory):
  - `resources/prompt_templates/repair.md:195` -> 
  - `resources/prompt_templates/repair.md:196` ->   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  - `resources/prompt_templates/repair.md:197` ->   - Remove conflicting old invariants rather than preserving them.
- Policy delta: none (wording preserved; duplicates removed only).

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\reuse_index.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\reuse_index.md`

```plaintext
﻿# Prompt-Level Reuse Report (proposed_refactor_v1)

## Shared Block Catalog
- `B001.must_stay_true_end_truth_line` -> write.md
- `B002.must_stay_true_reconciliation_block` -> repair.md
- `B003.must_stay_true_remove_block` -> repair.md, state_repair.md, write.md
- `B004.scope_override_nonreal_rule` -> preflight.md, repair.md, state_repair.md, write.md
- `B005.json_contract_block` -> preflight.md, repair.md, state_repair.md, write.md
- `B006.global_continuity_array_guardrail` -> output_contract.md, preflight.md, repair.md, state_repair.md, write.md
- `B007.transfer_registry_conflict_rule` -> repair.md, state_repair.md, write.md
- `B008a.appearance_updates_object_under_character_updates` -> repair.md, write.md
- `B008b.appearance_updates_not_array` -> repair.md, write.md

```

## proposed_refactor_v1\reports\stability_controls.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\stability_controls.md`

```plaintext
﻿# Stability Report (proposed_refactor_v1)

## Guardrails
- No runtime prompt-loading behavior changed in this proposal package.
- `write.md` and `repair.md` are the only prompts with textual edits; edits are dedupe-only.
- All other prompts are composition-layout changes only (semantic no-op).
- Known malformed wrapped lines are intentionally unchanged for risk containment in pass 1.

## Text-Change Scope
- `write.md`: removed duplicate lines at 24,65,68,71,81,105,155,158,194,197.
- `repair.md`: removed duplicate ranges 55-58,60-63,65-68,82-85,87-90,108-111,134-137,189-192,194-197.
- Everything else: no semantic text change proposed.

```

## proposed_refactor_v1\reports\state_repair.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\state_repair.md.change_map.md`

```plaintext
﻿# Change Map: state_repair.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/state_repair.md`
- SHA256: `BDA655A758FDBC0559FE0980FC92FEBA80FE2EE1792F660DE65D774297D582C2`

## Composition Entries (Order)
1. phase  -> `fragments/phase/state_repair/seg_01.md`
2. shared -> `B003.must_stay_true_remove_block` (`fragments/shared/B003.must_stay_true_remove_block.md`)
3. phase  -> `fragments/phase/state_repair/seg_02.md`
4. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
5. phase  -> `fragments/phase/state_repair/seg_03.md`
6. shared -> `B007.transfer_registry_conflict_rule` (`fragments/shared/B007.transfer_registry_conflict_rule.md`)
7. phase  -> `fragments/phase/state_repair/seg_04.md`
8. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
9. phase  -> `fragments/phase/state_repair/seg_05.md`
10. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)

## Reuse Summary
- Uses shared block `B003.must_stay_true_remove_block`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B007.transfer_registry_conflict_rule`
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\style_anchor.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\style_anchor.md.change_map.md`

```plaintext
﻿# Change Map: style_anchor.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/style_anchor.md`
- SHA256: `7264915455E13402314BC4C9BB8864443602FC5BD926C6C6D41FF71122AEF966`

## Composition Entries (Order)
1. phase  -> `fragments/phase/style_anchor/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\system_base.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\system_base.md.change_map.md`

```plaintext
﻿# Change Map: system_base.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/system_base.md`
- SHA256: `F36D9AFDE4A2F46A774F450845D5B6173E87C38D1B5CF3DB8FC1870BE42B4F48`

## Composition Entries (Order)
1. phase  -> `fragments/phase/system_base/seg_01.md`

## Reuse Summary
- No shared block reuse in this prompt for pass v1 (phase-local stability mode).

## One-to-One Change Detail
- Change type: no semantic text change; composition-managed layout only.
- Source-to-compiled expectation: equivalent text for this pass.

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## proposed_refactor_v1\reports\write.md.change_map.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\proposed_refactor_v1\reports\write.md.change_map.md`

```plaintext
﻿# Change Map: write.md

## Compiled Output
- Compiled: `proposed_refactor_v1/compiled/write.md`
- SHA256: `0AECFF344DF887C79DFFF4FC1B6967817CADE8BB5569D32BAFE2FACD1B850D52`

## Composition Entries (Order)
1. phase  -> `fragments/phase/write/seg_01.md`
2. shared -> `B001.must_stay_true_end_truth_line` (`fragments/shared/B001.must_stay_true_end_truth_line.md`)
3. shared -> `B003.must_stay_true_remove_block` (`fragments/shared/B003.must_stay_true_remove_block.md`)
4. phase  -> `fragments/phase/write/seg_02.md`
5. shared -> `B004.scope_override_nonreal_rule` (`fragments/shared/B004.scope_override_nonreal_rule.md`)
6. phase  -> `fragments/phase/write/seg_03.md`
7. shared -> `B006.global_continuity_array_guardrail` (`fragments/shared/B006.global_continuity_array_guardrail.md`)
8. phase  -> `fragments/phase/write/seg_04.md`
9. shared -> `B008a.appearance_updates_object_under_character_updates` (`fragments/shared/B008a.appearance_updates_object_under_character_updates.md`)
10. phase  -> `fragments/phase/write/seg_05.md`
11. shared -> `B007.transfer_registry_conflict_rule` (`fragments/shared/B007.transfer_registry_conflict_rule.md`)
12. phase  -> `fragments/phase/write/seg_06.md`
13. shared -> `B008b.appearance_updates_not_array` (`fragments/shared/B008b.appearance_updates_not_array.md`)
14. phase  -> `fragments/phase/write/seg_07.md`
15. shared -> `B005.json_contract_block` (`fragments/shared/B005.json_contract_block.md`)

## Reuse Summary
- Uses shared block `B001.must_stay_true_end_truth_line`
- Uses shared block `B003.must_stay_true_remove_block`
- Uses shared block `B004.scope_override_nonreal_rule`
- Uses shared block `B006.global_continuity_array_guardrail`
- Uses shared block `B008a.appearance_updates_object_under_character_updates`
- Uses shared block `B007.transfer_registry_conflict_rule`
- Uses shared block `B008b.appearance_updates_not_array`
- Uses shared block `B005.json_contract_block`

## One-to-One Change Detail
- Change type: dedupe exact duplicate lines + block extraction.
- Removed duplicate lines:
  - `resources/prompt_templates/write.md:24` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:65` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:68` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:71` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:81` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:105` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:155` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:158` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:194` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  - `resources/prompt_templates/write.md:197` -> - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
- Policy delta: none (wording preserved; duplicates removed only).

## Stability Controls
- Runtime path unchanged (still loads flat template files from `resources/prompt_templates/*` after distribution).
- Schema-sensitive examples preserved verbatim in this pass.
- Any normalization of known malformed wrapped lines is explicitly deferred.

```

## snapshots\appearance_projection.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\appearance_projection.md.snapshot.md`

```plaintext
﻿# Snapshot: appearance_projection.md

- Source: `resources/prompt_templates/appearance_projection.md`
- SHA256: `EF863DD5ED891E5B300A56570216752AB98A5E6B6800AE84C302D670FE906E34`
- Line count: `31`
- Byte length: `930`

```text
   1: # APPEARANCE PROJECTION
   2: You are generating a derived appearance summary (and optional art prompt) from canonical appearance atoms/marks.
   3: Return ONLY a JSON object. No prose, no commentary, no code fences.
   4: 
   5: Rules:
   6: - Do NOT change atoms/marks. They are canonical input.
   7: - Summary must be 2-4 sentences, durable and identity-level (no transient grime, no scene events).
   8: - Avoid inventory/attire unless the input explicitly marks a signature outfit.
   9: - Prefer canonical atom terms; do not invent new traits.
  10: - If you include appearance_art, it must be derived strictly from atoms/marks and signature outfit (if any).
  11: 
  12: Output JSON:
  13: {
  14:   "summary": "...",
  15:   "appearance_art": {
  16:     "base_prompt": "...",
  17:     "current_prompt": "...",
  18:     "negative_prompt": "...",
  19:     "tags": ["..."]
  20:   }
  21: }
  22: 
  23: Inputs:
  24: Character:
  25: {{character}}
  26: 
  27: Appearance base (canon):
  28: {{appearance_base}}
  29: 
  30: Appearance current (canonical atoms/marks):
  31: {{appearance_current}}
```

```

## snapshots\author_generate.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\author_generate.md.snapshot.md`

```plaintext
﻿# Snapshot: author_generate.md

- Source: `resources/prompt_templates/author_generate.md`
- SHA256: `E87899515FC1F1139FBDAEC81E6237B895E60F6912576EB33B47F5C44039146D`
- Line count: `51`
- Byte length: `1278`

```text
   1: # AUTHOR GENERATION
   2: 
   3: You are generating an original author persona for BookForge.
   4: 
   5: Return ONLY a single JSON object. Do not include markdown, code fences, or extra commentary.
   6: The JSON must be strict (double quotes, no trailing commas).
   7: 
   8: Required top-level keys:
   9: - author (object)
  10: - author_style_md (string)
  11: - system_fragment_md (string)
  12: 
  13: Optional top-level key:
  14: - banned_phrases (array of strings) only if the author is known for very specific phrases.
  15: 
  16: author object required keys:
  17: - persona_name (string)
  18: - influences (array of objects with name and weight; infer weights if not provided)
  19: - trait_profile (object)
  20: - style_rules (array of strings)
  21: - taboos (array of strings)
  22: - cadence_rules (array of strings)
  23: 
  24: JSON shape example (fill with real values):
  25: {
  26:   "author": {
  27:     "persona_name": "",
  28:     "influences": [
  29:       {"name": "", "weight": 0.0}
  30:     ],
  31:     "trait_profile": {
  32:       "voice": "",
  33:       "themes": [],
  34:       "sensory_bias": "",
  35:       "pacing": ""
  36:     },
  37:     "style_rules": [],
  38:     "taboos": [],
  39:     "cadence_rules": []
  40:   },
  41:   "author_style_md": "",
  42:   "system_fragment_md": ""
  43: }
  44: 
  45: Influences: {{influences}}
  46: 
  47: Persona name (optional): {{persona_name}}
  48: 
  49: Notes: {{notes}}
  50: 
  51: Additional prompt text: {{prompt_text}}
```

```

## snapshots\characters_generate.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\characters_generate.md.snapshot.md`

```plaintext
﻿# Snapshot: characters_generate.md

- Source: `resources/prompt_templates/characters_generate.md`
- SHA256: `2F2EBE29BFBB7CBE823ED38BF2714E853B0C5FA41F65E47D3CD0217B4A97E85D`
- Line count: `139`
- Byte length: `5221`

```text
   1: # CHARACTERS GENERATE
   2: 
   3: You are refining outline character stubs into canon character entries and initial per-book character state.
   4: Return ONLY a single JSON object. No markdown, no code fences, no commentary.
   5: Do not invent new characters; expand only the outline-provided stubs.
   6: 
   7: Required top-level keys:
   8: - schema_version ("1.0")
   9: - characters (array)
  10: 
  11: Each character object must include:
  12: - character_id
  13: - name
  14: - pronouns
  15: - role
  16: - persona (object)
  17: - inventory (array)
  18: - containers (array)
  19: - invariants (array of strings)
  20: - appearance_base (object)
  21: 
  22: Recommended mechanic seed key (dynamic):
  23: - character_continuity_system_state (object)
  24:   - Include any starting mechanics known at setup time.
  25:   - Examples: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses.
  26:   - titles must be an array of objects (not strings).
  27:   - You may add future mechanic families if relevant.
  28:   - Use dynamic continuity families as needed: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, system_tracking_metadata, extended_system_data.
  29:   - For LitRPG-like systems, prefer structured stats/skills/titles in character_continuity_system_state.
  30: 
  31: Appearance guidance (durable, canonical):
  32: - appearance_base is the canon self-image for this character.
  33: - Include: summary, atoms, marks, alias_map.
  34: - Atoms are normalized traits (species, sex_presentation, age_band, height_band, build, hair_color, hair_style, eye_color, skin_tone).
  35: - marks are durable identifiers (scars, tattoos, prosthetics). No temporary grime or wounds.
  36: - alias_map lists acceptable synonyms for lint tolerance (e.g., hair_color: ["dark brown"]).
  37: - appearance_current will be derived from appearance_base for the book unless explicitly overridden later.
  38: 
  39: Naming and durable item guidance:
  40: - For items, use a human-readable item_name; do not use ITEM_* ids in prose strings.
  41: - Reserve ITEM_* ids for canonical JSON only; do not use them in prose strings.
  42: - If you emit an item_id here, include item_name as a human label.
  43: 
  44: Starting scene alignment (important):
  45: - The initial inventory/containers/state must prepare each character for the book's first scene.
  46: - Use the Book + Outline characters in THIS prompt as your source of truth for the opening situation.
  47: - If the opening situation is unclear, default to a neutral, plausible posture (hands free, items stowed).
  48: - Example: office/briefing -> no weapons held; battle opener -> weapon may be in hand; travel -> stowed gear.
  49: 
  50: Persona guidance (compact, factual):
  51: - core_traits (array)
  52: - motivations (array)
  53: - fears (array)
  54: - values (array)
  55: - voice_notes (array)
  56: - arc_hint (string)
  57: 
  58: Inventory rules:
  59: - Every carried/held item must include a container location.
  60: - Use explicit container labels (satchel, belt, pack, hand_left, hand_right, sheath, etc.).
  61: - If an item is held, container must be hand_left or hand_right.
  62: - If you use item_id, include item_name (human label) on the same inventory entry. The item_name must be human readable and not an escaped id value.
  63: - Prefer item_name in prose-facing fields; item_id only in canonical JSON.
  64: - Containers are tracked separately in containers[] with owner and contents.
  65: 
  66: Invariant phrasing (use exact strings where possible):
  67: - inventory: <CHAR_ID> -> <item> (status=carried|stowed|equipped, container=<container_label>)
  68: - container: <container_label> (owner=<CHAR_ID>, contents=[item1, item2])
  69: - injury: <character_id> <injury/location>
  70: 
  71: Book:
  72: {{book}}
  73: 
  74: Outline characters:
  75: {{outline_characters}}
  76: 
  77: Outline opening context (chapter/section/scene 1):
  78: {{outline_opening}}
  79: 
  80: Series info (if any):
  81: {{series}}
  82: 
  83: Output JSON:
  84: {
  85:   "schema_version": "1.0",
  86:   "characters": [
  87:     {
  88:       "character_id": "CHAR_example",
  89:       "name": "",
  90:       "pronouns": "",
  91:       "role": "",
  92:       "persona": {
  93:         "core_traits": [],
  94:         "motivations": [],
  95:         "fears": [],
  96:         "values": [],
  97:         "voice_notes": [],
  98:         "arc_hint": ""
  99:       },
 100:       "appearance_base": {
 101:         "summary": "",
 102:         "atoms": {
 103:           "species": "human",
 104:           "sex_presentation": "",
 105:           "age_band": "",
 106:           "height_band": "",
 107:           "build": "",
 108:           "hair_color": "",
 109:           "hair_style": "",
 110:           "eye_color": "",
 111:           "skin_tone": ""
 112:         },
 113:         "marks": [
 114:           {"name": "", "location": "", "durability": "durable"}
 115:         ],
 116:         "alias_map": {
 117:           "hair_color": [""],
 118:           "eye_color": [""]
 119:         }
 120:       },
 121:       "character_continuity_system_state": {
 122:         "stats": {"hp": {"current": 10, "max": 10}},
 123:         "skills": {"sword": 1},
 124:         "titles": [{"name": "Novice", "source": "starting_class", "active": true}],
 125:         "resources": {"mana": {"current": 5, "max": 5}}
 126:       },
 127:       "inventory": [
 128:         {"item_id": "ITEM_longsword", "item_name": "Longsword", "status": "carried", "container": "hand_right"}
 129:       ],
 130:       "containers": [
 131:         {"container": "satchel", "owner": "CHAR_example", "location": "shoulder_left", "contents": ["maps"]}
 132:       ],
 133:       "invariants": [
 134:         "inventory: CHAR_example -> longsword (status=carried, container=hand_right)",
 135:         "container: satchel (owner=CHAR_example, contents=[maps])"
 136:       ]
 137:     }
 138:   ]
 139: }
```

```

## snapshots\continuity_pack.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\continuity_pack.md.snapshot.md`

```plaintext
﻿# Snapshot: continuity_pack.md

- Source: `resources/prompt_templates/continuity_pack.md`
- SHA256: `F3E97B8B5B5C0139A232DEA15B26A8403975ECAE8D9AE60053D1433EB83CB192`
- Line count: `52`
- Byte length: `2176`

```text
   1: # CONTINUITY PACK
   2: 
   3: Create a continuity pack JSON object with these fields:
   4: - scene_end_anchor: 2-4 factual sentences about how the last scene ended (no prose).
   5: - constraints: list of immediate continuity constraints.
   6: - open_threads: list of active thread ids.
   7: - cast_present: list of character names present next.
   8: - location: location id or name.
   9: - next_action: the implied next action.
  10: - summary: echo state.summary (facts-only arrays; do not paraphrase).
  11: 
  12: Return ONLY JSON.
  13: 
  14: Rules:
  15: - Use only characters listed in scene_card.cast_present. Do not introduce new names.
  16: - summary must match state.summary and remain facts-only; do not add prose.
  17: - constraints must include the highest-priority invariants from summary.must_stay_true and summary.key_facts_ring (copy exact strings when possible).
  18: - constraints must include the highest-priority inventory/container invariants from summary.must_stay_true (copy exact strings when possible).
  19: - If character_states are provided, prefer their inventory/container facts and continuity mechanic facts; do not invent conflicting values.
  20: - If item_registry or plot_devices are provided, reuse canonical names/ids in constraints when referencing durable items/devices.
  21: - Prefer item_registry.items[].display_name for prose references; reserve item_id for canonical JSON. The display_name must be human readable and not an escaped id/name.
  22: - If state.global_continuity_system_state contains canonical mechanic labels/values, reuse those exact labels in constraints.
  23: - If scene_card.cast_present is empty, cast_present must be an empty array.
  24: - open_threads must be a subset of thread_registry thread_id values.
  25: - If scene_card.thread_ids is present, prefer those thread ids.
  26: - Do not invent new thread ids or character names.
  27: 
  28: Scene card:
  29: {{scene_card}}
  30: 
  31: Character registry (id -> name):
  32: {{character_registry}}
  33: 
  34: Thread registry:
  35: {{thread_registry}}
  36: 
  37: Character states (per cast_present_ids):
  38: {{character_states}}
  39: 
  40: State:
  41: {{state}}
  42: 
  43: Summary (facts-only):
  44: {{summary}}
  45: 
  46: Recent facts:
  47: {{recent_facts}}
  48: Item registry (canonical):
  49: {{item_registry}}
  50: 
  51: Plot devices (canonical):
  52: {{plot_devices}}
```

```

## snapshots\lint.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\lint.md.snapshot.md`

```plaintext
﻿# Snapshot: lint.md

- Source: `resources/prompt_templates/lint.md`
- SHA256: `F3B131D17E0E7779FA5A4CA7344DD5A557EF8AFB1D68B6FC75613E503F3A9F0A`
- Line count: `129`
- Byte length: `6887`

```text
   1: # LINT
   2: 
   3: Check the scene for continuity, invariant violations, and duplication.
   4: Flag invariant contradictions against must_stay_true/key facts.
   5: Return ONLY JSON matching the lint_report schema.
   6: - Classify UI/prose mechanic claims as DURABLE or EPHEMERAL before enforcing.
   7:   - DURABLE: persistent stats/caps, skills/titles acquired, lasting status effects, inventory/custody, named mechanics referenced as invariants.
   8:   - EPHEMERAL: roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat telemetry.
   9: - Enforce DURABLE claims against authoritative_surfaces/state/registries.
  10: - EPHEMERAL claims do not require state ownership; only flag EPHEMERAL contradictions inside the same scene as warnings.
  11: - UI gate:
  12:   - If scene_card.ui_allowed=false and any authoritative UI blocks appear, emit issue code 'ui_gate_violation' (severity depends on lint mode).
  13:   - If ui_allowed is missing and UI blocks appear, emit 'ui_gate_unknown' (warning) requesting explicit ui_allowed; do not fail solely for missing flag.
  14:   - Inline bracketed UI (e.g., [HP: 1/1]) is still UI and should be gated the same way; do not embed UI mid-sentence.
  15: - If uncertain, default to EPHEMERAL (warning at most), not DURABLE (error).
  16: - status="fail" only if there is at least one issue with severity="error"; warnings alone => status="pass".
  17: - Item naming enforcement scope:
  18:   - Do not require that every mention in narrative prose use display_name.
  19:   - Enforce canonical display_name for: (a) anchoring at first introduction (same paragraph or within the next 2 sentences),
  20:     (b) any custody-change sentence (drop/pick up/hand off/stow/equip/transfer), and (c) any case where a descriptor is ambiguous among multiple durable items in the scene.
  21:   - Otherwise, treat non-canonical descriptive references as warnings at most.
  22: - Prose hygiene: flag internal ids or container codes in narrative prose (CHAR_, ITEM_, THREAD_, DEVICE_, hand_left, hand_right).
  23: - Naming severity policy:
  24:   - warning: unambiguous descriptor used post-anchor.
  25:   - error: missing anchor, descriptor used during custody-change without canonical name, or ambiguity risk.
  26: 
  27: - Appearance enforcement (authoritative surface):
  28:   - APPEARANCE_CHECK is authoritative for cast_present_ids.
  29:   - Compare APPEARANCE_CHECK tokens to appearance_current atoms/marks (alias-aware).
  30:   - If APPEARANCE_CHECK contradicts appearance_current, emit error code "appearance_mismatch".
  31:   - Prose-only appearance contradictions are warnings unless explicitly durable and uncorrected in-scene.
  32:   - If prose depicts a durable appearance change but scene_card.durable_appearance_changes does not include it and no appearance_updates are present, emit error code "appearance_change_undeclared".
  33:   - If APPEARANCE_CHECK is missing for a cast member, emit warning code "appearance_check_missing".
  34: - For authoritative surfaces, prefer exact canonical item/device labels from registries.
  35: - For milestone repetition/future checks, compare against PRE-INVARIANTS only (pre-scene canon).
  36: - For ownership/consistency checks, compare against POST-STATE (post-patch candidate).
  37: - POST-STATE is canonical; character_states is a derived convenience view. If they contradict, emit pipeline_state_incoherent.
  38: - Check for POV drift vs book POV (no first-person in third-person scenes).
  39:   - Ignore first-person pronouns inside quoted dialogue; only narration counts.
  40: - Deterministically enforce scene-card durable constraints (required_in_custody, required_scene_accessible, forbidden_visible, device_presence; optional required_visible_on_page).
  41: - Durable constraint evaluation must use POST-STATE candidate (after patch), not pre-state.
  42: - Report missing durable context ids with explicit retry hints instead of guessing canon.
  43: - Input consistency check (mandatory, before issuing continuity/durable errors):
  44:   - If MUST_STAY_TRUE invariants contradict the provided post-patch candidate character state, treat this as an upstream snapshot error.
  45:   - In that case emit a single error issue with code "pipeline_state_incoherent" including evidence of the invariant and the conflicting state field.
  46:   - Do NOT emit additional continuity errors for the same fields when pipeline_state_incoherent is present.
  47: - must_stay_true removals:
  48:   - Lines starting with "REMOVE:" are deletion directives, not invariants.
  49:   - Ignore REMOVE lines when checking contradictions.
  50:   - If a REMOVE directive targets a fact, treat that fact as non-canonical even if it appears earlier in must_stay_true.
  51: - If pipeline_state_incoherent is present, issues MUST contain exactly one issue.
  52: - For each issue, include evidence when possible (line number + excerpt) as {"evidence": {"line": N, "excerpt": "..."}}.
  53: - Evaluate consistency over the full scope of the scene, not a single snapshot.
  54:   - Transitional state: a temporary mismatch later corrected or superseded within this scene.
  55:   - Durable violation: a mismatch that persists through the end of the scene or ends unresolved.
  56:   - You MUST read the entire scene and build a minimal timeline of explicit state claims/updates (UI lines, inventory changes, title/skill changes, location/time claims).
  57:   - If you detect an apparent inconsistency, you MUST search forward for later updates that resolve or supersede it.
  58:   - Only produce FAIL for durable violations. If resolved within the scene, do NOT FAIL; at most emit a warning.
  59:   - When the same stat appears multiple times, the last occurrence in the scene is authoritative unless an explicit rollback is stated.
  60:   - Any durability violation must cite both the conflicting line and the lack of later correction (or state "no later correction found").
  61: 
  62: Required keys:
  63: - schema_version ("1.0")
  64: - status ("pass" or "fail")
  65: - issues (array of objects)
  66: 
  67: Each issue object must include:
  68: - code
  69: - message
  70: Optional:
  71: - severity
  72: - evidence
  73: 
  74: If there are no issues, return:
  75: {
  76:   "schema_version": "1.0",
  77:   "status": "pass",
  78:   "issues": []
  79: }
  80: 
  81: If there are issues, return:
  82: {
  83:   "schema_version": "1.0",
  84:   "status": "fail",
  85:   "issues": [
  86:     {"code": "continuity", "message": "Example issue", "severity": "error"}
  87:   ]
  88: }
  89: 
  90: Scene:
  91: {{prose}}
  92: 
  93: Scene card:
  94: {{scene_card}}
  95: 
  96: Authoritative surfaces:
  97: {{authoritative_surfaces}}
  98: 
  99: Appearance check (authoritative):
 100: {{appearance_check}}
 101: 
 102: Character states (post-patch candidate, per cast_present_ids):
 103: {{character_states}}
 104: 
 105: Item registry (canonical):
 106: {{item_registry}}
 107: 
 108: Plot devices (canonical):
 109: {{plot_devices}}
 110: 
 111: Pre-state (before patch):
 112: {{pre_state}}
 113: 
 114: Pre-summary (facts-only):
 115: {{pre_summary}}
 116: 
 117: Pre-invariants (must_stay_true + key facts):
 118: {{pre_invariants}}
 119: 
 120: Post-state candidate (after patch):
 121: {{post_state}}
 122: 
 123: Post-summary (facts-only):
 124: {{post_summary}}
 125: 
 126: Post-invariants (must_stay_true + key facts):
 127: {{post_invariants}}
 128: 
 129: 
```

```

## snapshots\outline.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\outline.md.snapshot.md`

```plaintext
﻿# Snapshot: outline.md

- Source: `resources/prompt_templates/outline.md`
- SHA256: `5CC31E096D85313344F8030EEF1CBC5CA2539EAE7AD5625E9FF0A3FE31452848`
- Line count: `157`
- Byte length: `4747`

```text
   1: # OUTLINE
   2: 
   3: You are the outline planner. Create a compact outline for the book.
   4: Return ONLY a single JSON object that matches the outline schema v1.1.
   5: No markdown, no code fences, no commentary.
   6: Keep summaries concise but in the author voice from the system prompt.
   7: 
   8: Core contract: each SCENE is one scene to be written (scene == writing unit).
   9: Scenes must vary per chapter. Do NOT use a fixed scene count.
  10: 
  11: Sections are required:
  12: - Every chapter must include a sections array.
  13: - Typical chapters should have 3-8 sections (target).
  14: - A simple/interlude chapter may use 2-4 sections (rare).
  15: - Each section usually has 2-6 scenes.
  16: - A 1-scene section is allowed only for a stinger/hook moment.
  17: - Total scenes per chapter should naturally land in 6-32, varying by complexity.
  18: 
  19: Scene quality rules:
  20: - Each scene must include type and outcome.
  21: - outcome must be a concrete state change.
  22: - Do not pad with travel/recap/mood-only scenes.
  23: If a user prompt is provided, treat it as grounding context. Integrate its details, but keep the schema and scene rules.
  24: 
  25: 
  26: Chapter role vocabulary (prefer one):
  27: - hook, setup, pressure, reversal, revelation, investigation, journey, trial, alliance, betrayal, siege, confrontation, climax, aftermath, transition, hinge
  28: If it truly does not fit, use the closest role; custom roles are allowed but should be 1-2 words.
  29: 
  30: Scene type vocabulary (prefer one):
  31: - setup, action, reveal, escalation, choice, consequence, aftermath, transition
  32: If it truly does not fit, use the closest type; custom types are allowed but should be 1-2 words.
  33: 
  34: Tempo values (prefer one):
  35: - slow_burn, steady, rush
  36: If it truly does not fit, use the closest tempo; custom values are allowed but should be 1-2 words.
  37: 
  38: Required top-level keys:
  39: - schema_version ("1.1")
  40: - chapters (array)
  41: 
  42: Optional top-level keys (recommended):
  43: - threads (array of thread stubs)
  44: - characters (array of character stubs)
  45: 
  46: Each chapter must include:
  47: - chapter_id
  48: - title
  49: - goal
  50: - chapter_role
  51: - stakes_shift
  52: - bridge (object with from_prev, to_next)
  53: - pacing (object with intensity, tempo, expected_scene_count; expected_scene_count is a soft target)
  54: - sections (array)
  55: 
  56: Each section must include:
  57: - section_id
  58: - title
  59: - intent
  60: - scenes (array of scene objects)
  61: 
  62: Optional section keys:
  63: - section_role
  64: 
  65: Each scene must include:
  66: - scene_id
  67: - summary
  68: - type
  69: - outcome
  70: - characters (array of character_id values present in the scene)
  71: 
  72: Optional scene keys:
  73: - introduces (array of character_id values introduced in the scene)
  74: - threads (array of thread_id values touched in the scene)
  75: - callbacks (array of ids: character/thread/lore references)
  76: 
  77: Character stub format:
  78: {
  79:   "character_id": "CHAR_<slug>",
  80:   "name": "",
  81:   "pronouns": "",
  82:   "role": "",
  83:   "intro": {"chapter": 1, "scene": 1}
  84: }
  85: 
  86: Thread stub format:
  87: {
  88:   "thread_id": "THREAD_<slug>",
  89:   "label": "",
  90:   "status": "open"
  91: }
  92: 
  93: Output ordering guidance:
  94: - Write chapters first. After chapters, list threads and characters at the end of the JSON object.
  95: 
  96: JSON shape example (fill with real values):
  97: {
  98:   "schema_version": "1.1",
  99:   "chapters": [
 100:     {
 101:       "chapter_id": 1,
 102:       "title": "",
 103:       "goal": "",
 104:       "chapter_role": "hook",
 105:       "stakes_shift": "",
 106:       "bridge": {"from_prev": "", "to_next": ""},
 107:       "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 10},
 108:       "sections": [
 109:         {
 110:           "section_id": 1,
 111:           "title": "",
 112:           "intent": "",
 113:           "scenes": [
 114:             {"scene_id": 1, "summary": "", "type": "setup", "outcome": "", "characters": ["CHAR_new_character_name"], "introduces": ["CHAR_new_character_name"]}
 115:           ]
 116:         }
 117:       ]
 118:     },
 119:     {
 120:       "chapter_id": 2,
 121:       "title": "",
 122:       "goal": "",
 123:       "chapter_role": "setup",
 124:       "stakes_shift": "",
 125:       "bridge": {"from_prev": "", "to_next": ""},
 126:       "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 8},
 127:       "sections": [
 128:         {
 129:           "section_id": 1,
 130:           "title": "",
 131:           "intent": "",
 132:           "scenes": [
 133:             {"scene_id": 1, "summary": "", "type": "transition", "outcome": "", "characters": ["CHAR_new_character_name"]}
 134:           ]
 135:         }
 136:       ]
 137:     }
 138:   ],
 139:   "threads": [
 140:     {"thread_id": "THREAD_prophecy", "label": "The Awakened Sage", "status": "open"}
 141:   ],
 142:   "characters": [
 143:     {"character_id": "CHAR_new_character_name", "name": "New Character", "pronouns": "they/them", "role": "protagonist", "intro": {"chapter": 1, "scene": 1}}
 144:   ]
 145: }
 146: 
 147: Book:
 148: {{book}}
 149: 
 150: Targets:
 151: {{targets}}
 152: 
 153: User prompt (optional, may be empty):
 154: {{user_prompt}}
 155: 
 156: Notes:
 157: {{notes}}
```

```

## snapshots\output_contract.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\output_contract.md.snapshot.md`

```plaintext
﻿# Snapshot: output_contract.md

- Source: `resources/prompt_templates/output_contract.md`
- SHA256: `4FDAA9A34FD8B7857B675C366974B3D88CDB816C4CBDF1D0CF5FC69C7D25D5D0`
- Line count: `21`
- Byte length: `1959`

```text
   1: Output must follow the requested format.
   2: JSON blocks must be valid and schema-compliant.
   3: All required keys and arrays must be present.
   4: When a prompt specifies required counts or ranges, treat them as hard constraints.
   5: Do not collapse arrays below the stated minimums.
   6: If multiple output blocks are required (e.g. PROSE and STATE_PATCH), include all blocks in order.
   7: If output must be JSON only, return a single JSON object with no commentary or code fences.
   8: When creating outlines, the total scenes per chapter (sum of sections[].scenes[]) must match chapters[].pacing.expected_scene_count.
   9: If a prompt requires a COMPLIANCE or PREFLIGHT block, include it before PROSE.
  10: Durable vs ephemeral mechanics:
  11: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  12: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  13: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  14: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
  15: For durable items, prose must use display_name; item_id is reserved for JSON/patches. The display_name must be human readable and not an escaped id/name.
  16: For durable mutations, every `transfer_updates[]` object must include `item_id` and `reason` (non-empty string).
  17: `inventory_alignment_updates` must be an array of objects (no wrapper object with `updates`).
  18: Use canonical continuity keys: character_continuity_system_updates and global_continuity_system_updates.
  19: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  20:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  21:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
```

```

## snapshots\plan.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\plan.md.snapshot.md`

```plaintext
﻿# Snapshot: plan.md

- Source: `resources/prompt_templates/plan.md`
- SHA256: `65A7BF57348EDC1596EE9FFD8F8DF87B9D98E5CC08173E15A784773D1980C194`
- Line count: `91`
- Byte length: `3604`

```text
   1: # PLAN
   2: 
   3: You are the planner. Use the outline window and state to create the next scene card.
   4: Return ONLY a single JSON object that matches the scene_card schema.
   5: No markdown, no code fences, no commentary. Use strict JSON (double quotes, no trailing commas).
   6: 
   7: If outline_window includes character information, keep those character ids in mind.
   8: If character_states are provided, keep inventory/persona/continuity mechanics consistent; do not invent conflicting facts.
   9: If outline_window.current.introduces is present, the scene must introduce those characters.
  10: If recent_lint_warnings include ui_gate_unknown, set ui_allowed explicitly for this scene.
  11: 
  12: Required keys:
  13: - schema_version ("1.1")
  14: - scene_id
  15: - chapter
  16: - scene
  17: - scene_target
  18: - goal
  19: - conflict
  20: - required_callbacks (array)
  21: - constraints (array)
  22: - end_condition
  23: - ui_allowed (boolean; true only when System/UI is active in this scene)
  24: 
  25: Recommended keys (use ids from the outline; do not invent ids):
  26: - cast_present (array of character names for prose guidance)
  27: - cast_present_ids (array of character ids, e.g. CHAR_Eldrin)
  28: - introduces (array of character names introduced in this scene)
  29: - introduces_ids (array of character ids introduced in this scene)
  30: - thread_ids (array of thread ids, e.g. THREAD_Awakened_Sage)
  31: 
  32: Optional continuity-planning keys:
  33: - required_in_custody (array of item/device ids that must still be owned by scene start)
  34: - required_scene_accessible (array of item/device ids that must be retrievable without continuity break)
  35: - required_visible_on_page (array of ids that must be explicitly shown in-scene; use sparingly)
  36: - forbidden_visible (array of ids that must not be visibly carried/active in-scene)
  37: - device_presence (array of plot-device ids expected to matter in-scene)
  38: - transition_type (string, e.g. "time_skip", "travel_arrival", "combat_aftermath")
  39: - timeline_scope ("present"|"flashback"|"dream"|"simulation"|"hypothetical")
  40: - ontological_scope ("real"|"non_real")
  41: 
  42: Optional genre/system keys:
  43: - continuity_system_focus (array of mechanic domains likely to change this scene, e.g. ["stats", "resources", "titles"])
  44: - ui_mechanics_expected (array of UI labels likely to appear, e.g. ["HP", "Stamina", "Crit Rate"])
  45:   - If ui_allowed=false, ui_mechanics_expected MUST be an empty array.
  46: 
  47: JSON shape example (fill with real values):
  48: {
  49:   "schema_version": "1.1",
  50:   "scene_id": "SC_001_001",
  51:   "chapter": 1,
  52:   "scene": 1,
  53:   "scene_target": "Protagonist commits to the journey.",
  54:   "goal": "Force a decisive choice.",
  55:   "conflict": "Safety versus obligation.",
  56:   "required_callbacks": [],
  57:   "constraints": ["target_words: 1900"],
  58:   "end_condition": "The protagonist leaves home.",
  59:   "ui_allowed": false,
  60:   "cast_present": ["Eldrin"],
  61:   "cast_present_ids": ["CHAR_Eldrin"],
  62:   "introduces": [],
  63:   "introduces_ids": [],
  64:   "thread_ids": ["THREAD_Awakened_Sage"],
  65:   "required_in_custody": ["ITEM_broken_tutorial_sword"],
  66:   "required_scene_accessible": ["ITEM_broken_tutorial_sword"],
  67:   "required_visible_on_page": [],
  68:   "forbidden_visible": [],
  69:   "device_presence": ["DEVICE_anomaly_tag"],
  70:   "transition_type": "travel_arrival",
  71:   "timeline_scope": "present",
  72:   "ontological_scope": "real",
  73:   "continuity_system_focus": ["stats", "resources"],
  74:   "ui_mechanics_expected": ["HP", "Stamina"]
  75: }
  76: 
  77: Outline window:
  78: {{outline_window}}
  79: 
  80: Character states (per outline_window.current.characters):
  81: {{character_states}}
  82: 
  83: State:
  84: {{state}}
  85: 
  86: Recent lint warnings (prior scene, if any):
  87: {{recent_lint_warnings}}
  88: 
  89: Task:
  90: Create the next scene card.
  91: 
```

```

## snapshots\preflight.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\preflight.md.snapshot.md`

```plaintext
﻿# Snapshot: preflight.md

- Source: `resources/prompt_templates/preflight.md`
- SHA256: `DC967458F32EEC3F55A84C8BFAF2BDC16EFD608824635983A0C3B695E462A88B`
- Line count: `224`
- Byte length: `13545`

```text
   1: # PREFLIGHT
   2: 
   3: You are the scene state preflight aligner.
   4: Return ONLY a single JSON object that matches the state_patch schema.
   5: No markdown, no code fences, no commentary.
   6: 
   7: Your job is to align state before writing starts for this scene.
   8: - Output ONLY a STATE_PATCH-equivalent JSON object.
   9: - Do not write prose.
  10: - This pass can update inventory posture and continuity system state for cast/global scope.
  11: - The primary goal is make changes as needed to setup the next scene.
  12: - If uncertain, prefer leaving values unchanged.
  13: 
  14: Hard rules:
  15: - State ownership is mandatory: if you change mechanics, write them in canonical updates.
  16: - If a value is not changed in patch, it is treated as unchanged.
  17: - Do not invent new character ids or thread ids.
  18: - Keep updates scoped to current cast and global continuity only.
  19: - Do not emit cursor_advance, summary_update, duplication counters, or chapter rollup changes.
  20: - Keep timeline lock: only prepare state needed for the current scene card.
  21: - Respect scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`, and optional `required_visible_on_page`.
  22: - Respect scene scope gates: `timeline_scope` and `ontological_scope`; only use scope override when explicitly justified by reason_category.
  23: - Scope override rule (non-present / non-real scenes):
  24:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  25:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  26:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
  27: Transition gate (do-nothing by default):
  28: - First decide whether this scene is a CONTINUATION or a DISCONTINUOUS TRANSITION.
  29: - Treat as CONTINUATION when ALL are true:
  30:   - scene_card.scene_target matches state.world.location, AND
  31:   - scene_card.timeline_scope and scene_card.ontological_scope do not change relative to current state, AND
  32:   - scene_card.transition_type is empty OR clearly indicates continuity (e.g., "continuous", "beat", "direct_continuation"), AND
  33:   - there is no durable-constraint violation to fix.
  34: - If CONTINUATION:
  35:   - Output the minimal patch: {"schema_version":"1.0"} (no other fields), unless a durable constraint is violated.
  36:   - Do NOT "normalize" inventory posture or move items just to be scene-appropriate. Only fix actual contradictions.
  37: - Treat as DISCONTINUOUS TRANSITION when ANY are true:
  38:   - scene_card.scene_target differs from state.world.location, OR
  39:   - scene_card.transition_type is present and not clearly continuous, OR
  40:   - timeline_scope / ontological_scope indicates a scope shift, OR
  41:   - cast_present for this scene differs materially from state.world.cast_present.
  42: 
  43: World alignment (only when needed for this scene):
  44: - If state.world.location != scene_card.scene_target, set world_updates.location = scene_card.scene_target.
  45: - If scene_card.cast_present_ids is provided and differs from state.world.cast_present, set world_updates.cast_present = scene_card.cast_present_ids.
  46: - Do not modify world.time unless the scene card explicitly implies a non-present timeline_scope; if you must, record why in global_continuity_system_updates.
  47: 
  48: Hidden transition state policy:
  49: - Posture changes (stowed/held/worn, hand->pack, pack->table, etc.) are allowed ONLY during DISCONTINUOUS TRANSITION, or to satisfy a durable constraint.
  50: - Custody changes (an item is no longer in the character's possession / custodian changes scope) are NOT implied by posture changes.
  51:   - If and only if custody changes, you MUST:
  52:     - update item_registry_updates for that item (custodian + last_seen), and
  53:     - include transfer_updates with a reason (and prefer adding expected_before).
  54: - Never "drop" an item by omitting it from an inventory array. If an item leaves a character, represent it as an explicit transfer.
  55: 
  56: Inventory transition rules:
  57: Appearance contract:
  58: - appearance_current atoms/marks are canonical and must not be contradicted or mutated in preflight.
  59: - Preflight does NOT invent or change appearance; only note missing appearance_current if present in character_states.
  60: - Ensure carried/equipped/stowed posture is scene-appropriate.
  61: - character_updates.inventory and inventory_alignment_updates.set.inventory must be arrays of inventory objects, never id strings.
  62: - Preserve ownership and container consistency.
  63: - For held items use `container=hand_left` or `container=hand_right`.
  64: 
  65: Durable-constraint compliance check (must run before output):
  66: 1) Resolve constraint tokens:
  67:    - Treat entries in required_in_custody / required_scene_accessible / required_visible_on_page / forbidden_visible / device_presence as IDs when they look like IDs.
  68:    - If an entry does not match an ID, attempt a best-effort lookup by name/alias in item_registry / plot_devices.
  69:    - If still ambiguous, do not guess; leave unchanged and record the unresolved token in character_updates.notes for the most relevant cast member.
  70: 2) Enforce required_in_custody:
  71:    - Ensure the specified item's custodian is the required character/scope.
  72:    - Ensure the item appears in that character's inventory in an appropriate container/status.
  73: 3) Enforce forbidden_visible:
  74:    - Ensure the item is not in hand_left/hand_right and not "worn/brandished/visible" status.
  75:    - Prefer moving it to an existing container (pack/pouch/sheath) over inventing new containers.
  76: 4) Enforce required_scene_accessible / required_visible_on_page:
  77:    - Accessible: item can be stowed but present in-scene.
  78:    - Visible_on_page: item must be held/worn/placed such that the writer can naturally show it early.
  79: 
  80: Dynamic continuity rules:
  81: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  82:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
  83:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
  84:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  85:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
  86:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
  87:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
  88: 
  89:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  90:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
  91:     - INVALID: "custodian": null
  92:     - VALID: "custodian": "CHAR_ARTIE" or "world"
  93:   - owner_scope must be "character" or "world" and must match the custodian scope.
  94:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  95:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
  96: - Use canonical keys:
  97:   - character_continuity_system_updates
  98:   - global_continuity_system_updates
  99: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
 100:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 101:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 102: - Update operations use set/delta/remove/reason.
 103: - Dynamic mechanic families are allowed (stats, skills, titles, resources, effects, statuses, classes, custom systems).
 104: - titles must be arrays of objects with stable `name` fields, never arrays of strings.
 105: - Durable-state updates are authoritative and must be explicit in patch blocks.
 106: - If inventory posture is changed for scene fit, include `inventory_alignment_updates` with `reason` and `reason_category`.
 107: - If you emit inventory_alignment_updates, the reason MUST state the final posture (item + container + status) so downstream phases can reconcile must_stay_true. Do not omit posture intent.
 108: - `inventory_alignment_updates` must be an array of objects; do not wrap it in an object with an `updates` key.
 109: - If durable item custody or metadata changes, include `item_registry_updates` and/or `transfer_updates`.
 110: - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 111: - If plot-device custody or activation changes, include `plot_device_updates`.
 112: - Never rely on prose implication for durable state mutation.
 113: - All *_updates arrays must contain objects; never emit bare strings as array entries.
 114: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
 115: - Transfer vs registry conflict rule (must follow):
 116:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 117:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 118:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).- Safety check for non-trivial changes:
 119:   - When making a DISCONTINUOUS TRANSITION change that moves an item between containers, changes custody, or toggles a plot device:
 120:     - include expected_before with the minimal prior snapshot you are relying on (e.g., prior container/status/custodian).
 121:     - if expected_before does not match current state, prefer leaving unchanged and note the discrepancy in notes.
 122: - Patch coupling rule:
 123:   - If you emit inventory_alignment_updates for a character, you MUST also emit character_updates for that character with the final authoritative inventory/containers for this scene.
 124:   - The inventory arrays in both places should match (alignment is the justification record; character_updates is the durable state).
 125: - reason_category vocabulary (use one):
 126:   - continuity_fix
 127:   - constraint_enforcement
 128:   - location_transition
 129:   - time_skip
 130:   - scope_shift
 131:   - equipment_posture
 132:   - custody_transfer
 133:   - plot_device_state
 134: 
 135: JSON Contract Block (strict; arrays only):
 136: - All *_updates must be arrays of objects, even when there is only one update.
 137: - INVALID vs VALID examples:
 138:   - item_registry_updates:
 139:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 140:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 141:   - plot_device_updates:
 142:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 143:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 144:   - transfer_updates:
 145:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 146:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 147:   - inventory_alignment_updates:
 148:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 149:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 150:   - global_continuity_system_updates:
 151:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 152:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 153: - custodian must be a non-null string id or "world"; never null.
 154: 
 155: Scene card:
 156: {{scene_card}}
 157: 
 158: Current state:
 159: {{state}}
 160: 
 161: Current summary:
 162: {{summary}}
 163: 
 164: Character registry:
 165: {{character_registry}}
 166: 
 167: Thread registry:
 168: {{thread_registry}}
 169: 
 170: Character states (cast only):
 171: {{character_states}}
 172: 
 173: Immediate previous scene (if available):
 174: {{immediate_previous_scene}}
 175: 
 176: Last appearance prose for cast members missing from immediate previous scene:
 177: {{cast_last_appearance}}
 178: 
 179: Output JSON shape reminder:
 180: {
 181:   "schema_version": "1.0",
 182:   "character_updates": [
 183:     {
 184:       "character_id": "CHAR_example",
 185:       "chapter": 1,
 186:       "scene": 2,
 187:       "inventory": [{"item": "ITEM_example", "container": "pockets", "status": "stowed"}],
 188:       "containers": [],
 189:       "persona_updates": [],
 190:       "invariants_add": [],
 191:       "notes": ""
 192:     }
 193:   ],
 194:   "character_continuity_system_updates": [
 195:     {
 196:       "character_id": "CHAR_example",
 197:       "set": {
 198:         "titles": [{"name": "Novice"}]
 199:       },
 200:       "delta": {},
 201:       "remove": [],
 202:       "reason": "align pre-scene state"
 203:     }
 204:   ],
 205:   "global_continuity_system_updates": [],
 206:   "inventory_alignment_updates": [
 207:     {
 208:       "character_id": "CHAR_example",
 209:       "set": {"inventory": [{"item": "ITEM_example", "container": "hand_right", "status": "held"}], "containers": []},
 210:       "reason": "scene posture alignment",
 211:       "reason_category": "after_combat_cleanup"
 212:     }
 213:   ],
 214:   "item_registry_updates": [],
 215:   "plot_device_updates": [],
 216:   "transfer_updates": []
 217: }
 218: 
 219: Item registry (canonical):
 220: {{item_registry}}
 221: 
 222: Plot devices (canonical):
 223: {{plot_devices}}
 224: 
```

```

## snapshots\repair.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\repair.md.snapshot.md`

```plaintext
﻿# Snapshot: repair.md

- Source: `resources/prompt_templates/repair.md`
- SHA256: `57605D83A5197268F33334B45C9E09118994CAD25F4AE3690C14D10F7C44EE72`
- Line count: `257`
- Byte length: `18703`

```text
   1: # REPAIR
   2: 
   3: Fix the scene based on lint issues.
   4: Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
   5: Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
   6: State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
   7: Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
   8: - must_stay_true reconciliation (mandatory):
   9:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  10:   - Remove conflicting old invariants rather than preserving them.
  11: - must_stay_true removal (mandatory when a durable fact is superseded):
  12:   - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  13:   - Place REMOVE lines before the new final invariant.
  14:   - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
  15: Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
  16: Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
  17: - Inventory posture reconciliation:
  18:   - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  19:   - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  20:   - Use canonical invariant formats:
  21:     - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
  22:     - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
  23: For held items, specify container=hand_left or container=hand_right.
  24: Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
  25: Durable vs ephemeral mechanics:
  26: - If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
  27: - You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
  28: - When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
  29: - Do not treat early UI snapshots as canonical if the scene later corrects them.
  30: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  31: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  32: - UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.
  33: - UI/system readouts must be on their own line, starting with '[' and ending with ']'.
  34: - Do NOT embed bracketed UI in narrative sentences.
  35: - Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).
  36: 
  37: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  38: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
  39: Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
  40: If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
  41: Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
  42: Appearance contract:
  43: - Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
  44: - appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
  45: - Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
  46: - If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
  47: - APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).
  48: 
  49: Naming repairs:
  50: - If lint flags an item naming issue, fix it with minimal edits.
  51: - Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
  52: - Do not rename item_id or registry fields; only adjust prose wording.
  53: summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
  54: STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
  55: - must_stay_true reconciliation (mandatory):
  56: 
  57:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  58:   - Remove conflicting old invariants rather than preserving them.
  59: must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
  60: - must_stay_true reconciliation (mandatory):
  61: 
  62:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  63:   - Remove conflicting old invariants rather than preserving them.
  64: If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
  65: - must_stay_true reconciliation (mandatory):
  66: 
  67:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  68:   - Remove conflicting old invariants rather than preserving them.
  69: Enforce scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
  70: Respect `timeline_scope` and `ontological_scope`.
  71: - Scope override rule (non-present / non-real scenes):
  72:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  73:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  74:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
  75: Return corrected prose plus a corrected state_patch JSON block.
  76: 
  77: Output format (required, no code fences, no commentary):
  78: COMPLIANCE:
  79: Scene ID: <scene_card.scene_id>
  80: Allowed events: <short list from Scene Card>
  81: Forbidden milestones: <from must_stay_true>
  82: - must_stay_true reconciliation (mandatory):
  83: 
  84:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  85:   - Remove conflicting old invariants rather than preserving them.
  86: Current arm-side / inventory facts: <from must_stay_true>
  87: - must_stay_true reconciliation (mandatory):
  88: 
  89:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  90:   - Remove conflicting old invariants rather than preserving them.
  91: 
  92: APPEARANCE_CHECK:
  93: - CHAR_ID: <4-8 tokens from atoms/marks>
  94: 
  95: PROSE:
  96: <scene prose>
  97: 
  98: STATE_PATCH:
  99: <json>
 100: 
 101: STATE_PATCH rules:
 102: - Use schema_version "1.0".
 103: - Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
 104: - Use scene_card.cast_present_ids for cast_present (ids, not names).
 105: - Use scene_card.thread_ids for open_threads (thread ids).
 106: - Do not invent new character or thread ids.
 107: - Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
 108: - must_stay_true reconciliation (mandatory):
 109: 
 110:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 111:   - Remove conflicting old invariants rather than preserving them.
 112: - Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
 113: - Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
 114: - Include character_continuity_system_updates for cast_present_ids when mechanics change.
 115:   - Use set/delta/remove/reason.
 116:   - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
 117:   - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
 118:   - If a new mechanic family appears, add it under set with a stable key.
 119: - Include global_continuity_system_updates only if global mechanics change.
 120: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
 121:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 122:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 123: - All *_updates arrays must contain objects; never emit bare strings as array entries.
 124: - JSON shape guardrails (strict, do not deviate):
 125:   - character_updates MUST be an array of objects.
 126:     - INVALID: "character_updates": {"character_id": "CHAR_X"}
 127:     - VALID: "character_updates": [{"character_id": "CHAR_X"}]
 128:   - character_continuity_system_updates MUST be an array of objects with character_id.
 129:     - INVALID: "character_continuity_system_updates": {"set": {...}}
 130:     - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
 131:   - summary_update fields must be arrays of strings.
 132:     - INVALID: "summary_update": {"last_scene": "text"}
 133:     - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
 134: - must_stay_true reconciliation (mandatory):
 135: 
 136:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 137:   - Remove conflicting old invariants rather than preserving them.
 138:   - appearance_updates MUST be an object under character_updates.
 139:     - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
 140:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 141: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
 142: - Durable-state mutation blocks are mandatory when applicable:
 143: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
 144:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
 145:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
 146:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
 147:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
 148:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
 149:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
 150: 
 151:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
 152:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
 153:     - INVALID: "custodian": null
 154:     - VALID: "custodian": "CHAR_ARTIE" or "world"
 155:   - owner_scope must be "character" or "world" and must match the custodian scope.
 156:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
 157:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
 158: - Transfer vs registry conflict rule (must follow):
 159:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 160:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 161:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
 162:   - `item_registry_updates` for durable item metadata/custody changes.
 163:   - `plot_device_updates` for durable plot-device custody/activation changes.
 164:   - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
 165:   - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 166:   - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
 167:   - inventory_alignment_updates[*].set MUST be an object (not a list).
 168:     - INVALID: "set": []
 169:     - VALID:   "set": {"inventory": [...], "containers": [...]}
 170: - For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
 171: - If you mutate durable state, do not leave the same mutation only in prose.
 172: - Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
 173: - appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.
 174:   - appearance_updates MUST be an object, not an array.
 175:     - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
 176:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 177:   - appearance_updates.set may include atoms and marks only (canonical truth).
 178:     - Do NOT put marks_add at the top level; it belongs under set.
 179:     - Use set.marks_add / set.marks_remove for marks changes.
 180:     - Use set.atoms for atom changes.
 181:   - appearance_updates.reason is required (brief, factual).
 182:   - Do NOT set summary or art text in appearance_updates (derived after acceptance)
 183:   - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
 184:   - character_updates.inventory MUST be an array of objects, never string item ids.
 185:   - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
 186:   - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
 187:   - If you have a single persona update, still wrap it in an array of strings.
 188: - must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
 189: - must_stay_true reconciliation (mandatory):
 190: 
 191:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 192:   - Remove conflicting old invariants rather than preserving them.
 193:   - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.
 194: - must_stay_true reconciliation (mandatory):
 195: 
 196:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 197:   - Remove conflicting old invariants rather than preserving them.
 198:   - inventory: CHAR_example -> shard (carried, container=satchel)
 199:   - inventory: CHAR_example -> longsword (carried, container=hand_right)
 200:   - container: satchel (owner=CHAR_example, contents=[shard, maps])
 201:   - milestone: shard_bind = DONE/NOT_YET
 202:   - milestone: maps_acquired = DONE/NOT_YET
 203:   - injury: right forearm scar / left arm filament
 204:   - ownership: shard (carried) / shard (bound but physical)
 205: 
 206: Issues:
 207: {{issues}}
 208: 
 209: Scene card:
 210: {{scene_card}}
 211: 
 212: Character registry (id -> name):
 213: {{character_registry}}
 214: 
 215: Thread registry:
 216: {{thread_registry}}
 217: 
 218: Character states (per cast_present_ids):
 219: {{character_states}}
 220: 
 221: Scene:
 222: {{prose}}
 223: 
 224: State:
 225: {{state}}
 226: 
 227: Item registry (canonical):
 228: {{item_registry}}
 229: 
 230: Plot devices (canonical):
 231: {{plot_devices}}
 232: 
 233: JSON Contract Block (strict; arrays only):
 234: - All *_updates must be arrays of objects, even when there is only one update.
 235: - INVALID vs VALID examples:
 236:   - item_registry_updates:
 237:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 238:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 239:   - plot_device_updates:
 240:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 241:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 242:   - transfer_updates:
 243:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 244:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 245:   - inventory_alignment_updates:
 246:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 247:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 248:   - global_continuity_system_updates:
 249:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 250:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 251: - custodian must be a non-null string id or "world"; never null.
 252: 
 253: 
 254: 
 255: 
 256: 
 257: 
```

```

## snapshots\state_repair.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\state_repair.md.snapshot.md`

```plaintext
﻿# Snapshot: state_repair.md

- Source: `resources/prompt_templates/state_repair.md`
- SHA256: `CDCA594405F79DFE7791B54BD94EC48EECF01036E22870DD0A29B27D509CE68D`
- Line count: `189`
- Byte length: `13505`

```text
   1: # STATE REPAIR
   2: 
   3: You are the state repair step. You must output a corrected STATE_PATCH JSON only.
   4: No prose, no commentary, no code fences.
   5: 
   6: Goal:
   7: - Ensure state_patch fully and accurately captures the scene's events and outcomes.
   8: - Fill missing summary_update data and fix invalid formats from draft_patch.
   9: - Preserve pre-scene invariants unless this scene changes them; when it does, update must_stay_true to the final end-of-scene value.
  10: - must_stay_true reconciliation (mandatory):
  11:   - If this scene changes a durable fact (stats/HP/status/title/custody), you MUST update must_stay_true to reflect the final end-of-scene value.
  12:   - Remove or replace any prior must_stay_true entries that conflict with new durable values.
  13:   - Do NOT carry forward conflicting legacy invariants once the scene updates them.
  14: - must_stay_true removal (mandatory when a durable fact is superseded):
  15:   - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  16:   - Place REMOVE lines before the new final invariant.
  17:   - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
  18: - Ensure mechanic/UI ownership in continuity system updates.
  19: 
  20: Rules:
  21: - Output a single JSON object that matches the state_patch schema.
  22: - Use schema_version "1.0".
  23: - Use scene_card.cast_present_ids for world_updates.cast_present.
  24: - Use scene_card.thread_ids for world_updates.open_threads.
  25: - Do not invent new character or thread ids.
  26: - summary_update arrays are required: last_scene (2-4 sentences), key_events (3-7 bullets), must_stay_true (3-7 bullets), chapter_so_far_add (bullets).
  27: - Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates
  28: Durable vs ephemeral mechanics:
  29: - UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.
  30: 
  31: - If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
  32: - You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
  33: - When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
  34: - Do not treat early UI snapshots as canonical if the scene later corrects them.
  35: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  36: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  37: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  38: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene..
  39: - titles are arrays of objects with stable name fields; do not emit titles as plain strings.
  40: - Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
  41: - If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
  42: - Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
  43: Appearance contract:
  44: - Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
  45: - appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
  46: - Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
  47: - If prose depicts a durable appearance change, include character_updates.appearance_updates with a reason.
  48: - Do NOT set summary or art text in appearance_updates (derived after acceptance).
  49: 
  50: Naming repairs:
  51: - If lint flags an item naming issue, fix it with minimal edits.
  52: - Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
  53: - Do not rename item_id or registry fields; only adjust prose wording.
  54: - Do not add numeric mechanics to invariants_add; store them in continuity system updates instead.
  55: - If an event appears in prose, it must appear in key_events.
  56: - must_stay_true must include milestone ledger entries and any inventory/injury/ownership invariants implied by prose.
  57: - Inventory posture reconciliation:
  58:   - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  59:   - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  60:   - Use canonical invariant formats:
  61:     - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
  62:     - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
  63: - character_updates entries must use arrays: persona_updates (array), invariants_add (array).
  64: - character_updates.inventory must be an array of objects, never item-id strings.
  65: - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  66:   - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
  67: - Use character_continuity_system_updates / global_continuity_system_updates to reconcile mechanics.
  68: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  69:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  70:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
  71: - If a new mechanic family appears in prose/UI, add it under set with a stable key.
  72: - All *_updates arrays must contain objects; never emit bare strings as array entries.
  73: - JSON shape guardrails (strict, do not deviate):
  74:   - character_updates MUST be an array of objects.
  75:     - INVALID: "character_updates": {"character_id": "CHAR_X"}
  76:     - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  77:   - character_continuity_system_updates MUST be an array of objects with character_id.
  78:     - INVALID: "character_continuity_system_updates": {"set": {...}}
  79:     - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  80:   - summary_update fields must be arrays of strings.
  81:     - INVALID: "summary_update": {"last_scene": "text"}
  82:     - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
  83: - appearance_updates MUST be an object under character_updates.
  84:     - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
  85:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
  86: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
  87: - Durable-state mutation blocks are mandatory when applicable:
  88: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  89:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
  90:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
  91:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  92:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
  93:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
  94:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
  95: 
  96:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  97:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
  98:     - INVALID: "custodian": null
  99:     - VALID: "custodian": "CHAR_ARTIE" or "world"
 100:   - owner_scope must be "character" or "world" and must match the custodian scope.
 101:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
 102:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
 103: - Transfer vs registry conflict rule (must follow):
 104:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 105:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 106:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
 107:   - `item_registry_updates` for durable item metadata/custody changes.
 108:   - `plot_device_updates` for durable plot-device custody/activation changes.
 109:   - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
 110:   - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 111:   - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
 112:   - inventory_alignment_updates[*].set MUST be an object (not a list).
 113:     - INVALID: "set": []
 114:     - VALID:   "set": {"inventory": [...], "containers": [...]}
 115: - For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
 116: - If durable mutation is implied but ambiguous, keep canonical state unchanged and emit an explicit repair note in reason fields.
 117: - Honor scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
 118: - Respect `timeline_scope` and `ontological_scope`; avoid physical custody changes in non-present/non-real scope unless explicit override is present.
 119: - Scope override rule (non-present / non-real scenes):
 120:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
 121:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
 122:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
 123: Inputs
 124: - prose: final scene text
 125: - state: pre-scene state
 126: - draft_patch: patch returned by write/repair (may be incomplete)
 127: - continuity_pack: pre-write continuity pack
 128: - character_states: current cast-only character state
 129: 
 130: Scene card:
 131: {{scene_card}}
 132: 
 133: Continuity pack:
 134: {{continuity_pack}}
 135: 
 136: Character registry (id -> name):
 137: {{character_registry}}
 138: 
 139: Thread registry:
 140: {{thread_registry}}
 141: 
 142: Character states (per cast_present_ids):
 143: {{character_states}}
 144: 
 145: State (pre-scene):
 146: {{state}}
 147: 
 148: Summary (facts-only):
 149: {{summary}}
 150: 
 151: Draft state patch:
 152: {{draft_patch}}
 153: 
 154: Prose:
 155: {{prose}}
 156: 
 157: Item registry (canonical):
 158: {{item_registry}}
 159: 
 160: Plot devices (canonical):
 161: {{plot_devices}}
 162: 
 163: JSON Contract Block (strict; arrays only):
 164: - All *_updates must be arrays of objects, even when there is only one update.
 165: - INVALID vs VALID examples:
 166:   - item_registry_updates:
 167:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 168:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 169:   - plot_device_updates:
 170:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 171:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 172:   - transfer_updates:
 173:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 174:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 175:   - inventory_alignment_updates:
 176:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 177:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 178:   - global_continuity_system_updates:
 179:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 180:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 181: - custodian must be a non-null string id or "world"; never null.
 182: 
 183: 
 184: 
 185: 
 186: 
 187: 
 188: 
 189: 
```

```

## snapshots\style_anchor.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\style_anchor.md.snapshot.md`

```plaintext
﻿# Snapshot: style_anchor.md

- Source: `resources/prompt_templates/style_anchor.md`
- SHA256: `1047A314F8AE316FA22A06546BD7CF680262505D35D6CFCDF8E1180971DDE0F1`
- Line count: `10`
- Byte length: `365`

```text
   1: # STYLE ANCHOR
   2: 
   3: Write a short style anchor excerpt (200-400 words) that demonstrates the desired voice and cadence.
   4: Do not reference plot events or character names.
   5: Return ONLY the excerpt text.
   6: Output must be non-empty and between 200-400 words.
   7: If you are unsure, write a neutral prose excerpt in the desired voice.
   8: 
   9: Author persona:
  10: {{author_fragment}}
```

```

## snapshots\system_base.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\system_base.md.snapshot.md`

```plaintext
﻿# Snapshot: system_base.md

- Source: `resources/prompt_templates/system_base.md`
- SHA256: `A44785B2F563F06AD7A46DDF71E9AA85C49AECD4C5A82ADB18FBB27010037682`
- Line count: `29`
- Byte length: `4114`

```text
   1: You are BookForge, a deterministic book-writing engine.
   2: Follow the output contracts exactly.
   3: YOU MUST ALWAYS RETURN THE REQUESTED CONTENT OR AN ERROR RESPONSE JSON RESULT.
   4: Treat all schema requirements and numeric ranges as hard constraints.
   5: If a prompt specifies required counts or ranges, you must satisfy them.
   6: If a prompt requires multiple output blocks, include all blocks in order.
   7: If registries or ids are provided, use only those; do not invent new ids.
   8: If constraints conflict, prioritize: output format/schema, numeric ranges, task rules, style.
   9: Timeline Lock: You may only depict events explicitly listed in the current Scene Card. You must not depict, imply, or resolve any later-scene milestone outcomes (including acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
  10: State primacy: state invariants and summary facts are binding; do not contradict them.
  11: Milestone uniqueness: if a milestone is marked DONE in state/must_stay_true, you must not depict it happening again. If marked NOT_YET, you must not depict it happening now.
  12: Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
  13: Inventory contract: track item ownership and container location per character or container label; items do not teleport.
  14: Inventory location: for held items, specify hand_left or hand_right; for stowed items, specify container label.
  15: Prose hygiene: never use internal ids or container codes in prose (CHAR_*, ITEM_*, THREAD_*, hand_left/hand_right). Use human-readable phrasing in narrative ("left hand", "right hand", "Artie", "his wallet").
  16: Item naming (canonical + anchored aliases): item_id is reserved for JSON/patches only. For durable items, the canonical display_name must appear in prose at first introduction (same paragraph or within the next 2 sentences). After anchoring, descriptive references are allowed if unambiguous in the scene. Any custody change (drop/pick up/hand off/stow/equip/transfer) must include the canonical display_name in the same sentence.
  17: Appearance contract: appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change. When a prompt requires APPEARANCE_CHECK, it must match appearance_current (alias-aware). Attire boundary: wearables are inventory-owned; do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
  18: State contract: you must create and maintain key state data each scene. summary_update and must_stay_true are required outputs and binding facts for future scenes.
  19: Continuity system contract: if mechanics/UI are present, all numeric values and mechanic labels must be sourced from continuity system state or explicitly updated in the state_patch using continuity system updates.
  20: UI gate: UI/system blocks (lines starting with '[' and ending with ']') are permitted only when scene_card.ui_allowed=true. If ui_allowed=false, do not include UI blocks even if an author persona says "always include".
  21: Continuity system scope: this includes stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, and future mechanic families not yet seen, that must be tracked as they are introduced.
  22: Durable transfer contract: every transfer_updates entry must include item_id and reason as required schema properties.
  23: JSON contract: all *_updates fields are arrays of objects (even when single). appearance_updates is an object, not an array.
  24: Inventory alignment contract: inventory_alignment_updates must be an array of objects, not a wrapper object.
  25: Invariant carry-forward: if an invariant still holds, restate it in must_stay_true; do not drop it unless explicitly removing a stale fact with REMOVE and restating the current truth.
  26: Conflict rule: if scene intent conflicts with state invariants, invariants win; return an ERROR JSON if you cannot comply.
  27: Never recap at scene openings.
  28: Do not repeat previous prose.
  29: 
```

```

## snapshots\write.md.snapshot.md

**Path:** `C:\Users\Zythis\source\repos\bookforge\resources\plans\prompt_template_composition_forensics_20260213_183000\snapshots\write.md.snapshot.md`

```plaintext
﻿# Snapshot: write.md

- Source: `resources/prompt_templates/write.md`
- SHA256: `898B8FCFA1997DE8C7BCDF0636E462EA52064D627E2257C3DF644725443888F4`
- Line count: `237`
- Byte length: `18254`

```text
   1: # WRITE
   2: Write the scene described by the scene card.
   3: - YOU MUST ALWAYS RETURN PROSE AND THE STATE_PATCH.
   4: - Start in motion. No recap.
   5: - Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
   6: - Use the continuity pack and state for continuity.
   7: - Use character_registry to keep names consistent in prose.
   8: - Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
   9: - State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
  10: - Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
  11: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  12: - must_stay_true removal (mandatory when a durable fact is superseded):
  13:   - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  14:   - Place REMOVE lines before the new final invariant.
  15:   - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
  16: - Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
  17: - Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
  18: - Inventory posture reconciliation:
  19:   - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  20:   - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  21:   - Use canonical invariant formats:
  22:     - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
  23:     - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
  24: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  25: 
  26: - For held items, specify container=hand_left or container=hand_right.
  27: - Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
  28: Durable vs ephemeral mechanics:
  29: - If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
  30: - You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
  31: - When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
  32: - Do not treat early UI snapshots as canonical if the scene later corrects them.
  33: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  34: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  35: - UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, do not include UI blocks; rephrase into narrative prose.
  36: - UI/system readouts must be on their own line, starting with '[' and ending with ']'.
  37: - Do NOT embed bracketed UI in narrative sentences.
  38: - Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).
  39: 
  40: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  41: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
  42: - titles are arrays of objects with stable name fields; do not emit titles as plain strings.
  43: - If item_registry or plot_devices are provided, they are canonical durable-state references for ownership/custody labels in authoritative outputs.
  44: - Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
  45: Appearance contract:
  46: - Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
  47: - appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
  48: - Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
  49: - If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
  50: - APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).
  51: 
  52: Durable item naming discipline:
  53: - When you first describe a durable item, anchor it by using the canonical display_name within the same paragraph (or within the next 2 sentences).
  54: - After anchoring, you may use brief descriptors for style if unambiguous.
  55: - During any custody/handling change, include the canonical display_name in that sentence.
  56: - If a required event is not in the Scene Card, do not perform it.
  57: - Enforce scene-card durable constraints: honor `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, and `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
  58: - Respect `timeline_scope` and `ontological_scope` when proposing durable mutations; do not mutate physical custody in non-present/non-real scope unless explicitly marked override.
  59: - Scope override rule (non-present / non-real scenes):
  60:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  61:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  62:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
  63: - summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
  64: - STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
  65: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  66: 
  67: - must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
  68: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  69: 
  70: - If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
  71: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  72: 
  73: - Return prose plus a state_patch JSON block.
  74: STATE_PATCH rules:
  75: - Use schema_version "1.0".
  76: - Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
  77: - Use scene_card.cast_present_ids for cast_present (ids, not names).
  78: - Use scene_card.thread_ids for open_threads (thread ids).
  79: - Do not invent new character or thread ids.
  80: - Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
  81: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  82: 
  83: - Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
  84: - Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
  85: - Include character_continuity_system_updates for cast_present_ids when mechanics change.
  86:   - Use set/delta/remove/reason.
  87:   - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  88:   - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  89:   - If a new mechanic family appears, add it under set with a stable key.
  90: - Include global_continuity_system_updates only if global mechanics change.
  91: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  92:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  93:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
  94: - All *_updates arrays must contain objects; never emit bare strings as array entries.
  95: - JSON shape guardrails (strict, do not deviate):
  96:   - character_updates MUST be an array of objects.
  97:     - INVALID: "character_updates": {"character_id": "CHAR_X"}
  98:     - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  99:   - character_continuity_system_updates MUST be an array of objects with character_id.
 100:     - INVALID: "character_continuity_system_updates": {"set": {...}}
 101:     - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
 102:   - summary_update fields must be arrays of strings.
 103:     - INVALID: "summary_update": {"last_scene": "text"}
 104:     - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
 105: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 106: 
 107:   - appearance_updates MUST be an object under character_updates.
 108:     - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
 109:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 110: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
 111: - Durable-state mutation blocks are mandatory when applicable:
 112: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
 113:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
 114:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
 115:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
 116:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
 117:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
 118:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
 119: 
 120:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
 121:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
 122:     - INVALID: "custodian": null
 123:     - VALID: "custodian": "CHAR_ARTIE" or "world"
 124:   - owner_scope must be "character" or "world" and must match the custodian scope.
 125:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
 126:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
 127: - Transfer vs registry conflict rule (must follow):
 128:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 129:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 130:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
 131:   - `item_registry_updates` for durable item metadata/custody changes.
 132:   - `plot_device_updates` for durable plot-device custody/activation changes.
 133:   - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
 134:   - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 135:   - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
 136: - For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
 137: - If you mutate durable state, do not leave the same mutation only in prose.
 138: - Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
 139: - appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.
 140:   - appearance_updates MUST be an object, not an array.
 141:     - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
 142:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 143:   - appearance_updates.set may include atoms and marks only (canonical truth).
 144:     - Do NOT put marks_add at the top level; it belongs under set.
 145:     - Use set.marks_add / set.marks_remove for marks changes.
 146:     - Use set.atoms for atom changes.
 147:   - appearance_updates.reason is required (brief, factual).
 148:   - Do NOT set summary or art text in appearance_updates (derived after acceptance)
 149:   - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
 150:   - character_updates.inventory MUST be an array of objects, never string item ids.
 151:   - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
 152:   - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
 153:   - If you have a single persona update, still wrap it in an array of strings.
 154: - must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
 155: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 156: 
 157:   - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.
 158: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 159: 
 160:   - inventory: CHAR_example -> shard (carried, container=satchel)
 161:   - inventory: CHAR_example -> longsword (carried, container=hand_right)
 162:   - container: satchel (owner=CHAR_example, contents=[shard, maps])
 163:   - milestone: shard_bind = DONE/NOT_YET
 164:   - milestone: maps_acquired = DONE/NOT_YET
 165:   - injury: right forearm scar / left arm filament
 166:   - ownership: shard (carried) / shard (bound but physical)
 167: 
 168: Scene card:
 169: {{scene_card}}
 170: 
 171: Continuity pack:
 172: {{continuity_pack}}
 173: 
 174: Character registry (id -> name):
 175: {{character_registry}}
 176: 
 177: Thread registry:
 178: {{thread_registry}}
 179: 
 180: Character states (per cast_present_ids):
 181: {{character_states}}
 182: 
 183: Style anchor:
 184: {{style_anchor}}
 185: 
 186: State:
 187: {{state}}
 188: 
 189: Output (required, no code fences):
 190: COMPLIANCE:
 191: Scene ID: <scene_card.scene_id>
 192: Allowed events: <short list from Scene Card>
 193: Forbidden milestones: <from must_stay_true>
 194: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 195: 
 196: Current arm-side / inventory facts: <from must_stay_true>
 197: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 198: 
 199: Durable changes committed: <final durable values to record in continuity updates>
 200: 
 201: APPEARANCE_CHECK:
 202: - CHAR_ID: <4-8 tokens from atoms/marks>
 203: 
 204: PROSE:
 205: <scene prose>
 206: STATE_PATCH:
 207: <json>
 208: 
 209: Item registry (canonical):
 210: {{item_registry}}
 211: 
 212: Plot devices (canonical):
 213: {{plot_devices}}
 214: 
 215: JSON Contract Block (strict; arrays only):
 216: - All *_updates must be arrays of objects, even when there is only one update.
 217: - INVALID vs VALID examples:
 218:   - item_registry_updates:
 219:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 220:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 221:   - plot_device_updates:
 222:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 223:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 224:   - transfer_updates:
 225:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 226:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 227:   - inventory_alignment_updates:
 228:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 229:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 230:   - global_continuity_system_updates:
 231:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 232:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 233: - custodian must be a non-null string id or "world"; never null.
 234: 
 235: 
 236: 
 237: 
```

```

