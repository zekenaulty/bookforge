# 0070 Add Nanda Consumption Fixtures And Contract Docs

Status: designed  
Depends On: 0060

## Goal
Give Nanda stable fixture data and docs for response capsules, action cards, branch transitions, reader anchors, and recovery workbench integration.

## Detailed Work
- Add a fixture book or generated fixture payload with:
  - query operation
  - branch-local action operation
  - refused operation
  - recovery branch creation receipt
  - produced artifacts with statuses
  - branch-local reader anchor
  - diagnostic fallback reader anchor
  - approval-required promotion placeholder
  - issue ticket and dependency examples
- Document how Nanda should consume:
  - operation IDs
  - receipt IDs
  - artifact IDs
  - artifact span IDs
  - branch refs
  - approval refs
  - dependency/staleness refs
- Document what Nanda must not infer:
  - no canonical mutation without canonical receipt
  - no clean branch claim without cleanup/validation receipts
  - no execution claim from capability projection alone
  - no mutation target from diagnostic reader fallback

## Likely Files Touched
- `tests/fixtures/evidence/`
- `docs/help/evidence.md`
- `resources/plans/Drafts/bookforge-durable-evidence-ledger/artifacts/nanda-consumption-contract.md`
- `tests/test_evidence_nanda_fixture.py`

## Tests
- Fixture validates against evidence query contract.
- Fixture contains at least one example of each major Nanda use case.
- Fixture IDs are stable across regeneration.

## Definition Of Done
- Nanda can build test coverage against BookForge evidence without a live messy workspace.
- The fixture includes enough data to prove response capsules and action cards can cite stable evidence refs.
