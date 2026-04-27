# 0082 Add Semantic Recovery Review And Downstream Impact Surfaces

Status: completed

## Goal
- Add semantic recovery review surfaces that let Nanda decide whether a structurally recovered branch is also story-safe.
- Keep BookForge honest:
  - structural validation remains deterministic and engine-owned
  - semantic review is evidence-generating and author/Nanda-facing
  - semantic review does not silently promote, invalidate, or rewrite anything

## Problem
- `0081` can recover a coherent structural timeline:
  - outline lineage normalized
  - invalid artifacts quarantined or removed
  - impacted prose redrafted
  - branch validated and promoted with removals
  - `chimera_risk` cleared
- But `0081` deliberately marks semantic validation as `deferred`.
- Nanda still needs structured evidence to answer:
  - did the redraft preserve causal story continuity
  - which downstream chapters/scenes need author review
  - which continuity, inventory, setting, summary, or appearance facts may now be stale
  - whether a recovered branch is ready for seam repair, revision, promotion, or user approval

## Boundary
- This step does not replace 0081 structural validation.
- This step does not add a monolithic `fix_story_semantics` command.
- This step should produce review surfaces and candidate actions.
- Mutation remains separate and branch-first.
- LLM review may be used, but the engine must constrain:
  - scope
  - input artifacts
  - output schema
  - allowed conclusions
  - whether output is diagnostic or provisional

## Proposed Query Surfaces
- `get_recovery_semantic_review(workspace, book_id, *, branch_id)`
  - summarizes semantic review status for the recovery branch
  - reports reviewed scopes, pending scopes, blockers, warnings, and recommended next action
- `get_downstream_dependency_review(workspace, book_id, *, branch_id)`
  - reports downstream scopes declared by the manifest
  - lists downstream artifacts requiring author review
  - classifies review status as:
    - `not_started`
    - `manifest_declared_only`
    - `reviewed_clean`
    - `reviewed_attention_required`
    - `review_failed`
- `get_recovery_semantic_review_readiness(workspace, book_id, *, branch_id)`
  - reports whether the branch has enough structural recovery artifacts to run semantic review
  - refuses before redraft and before structural validation has at least been attempted

## Current Implementation Slice
- Added query-only semantic review surfaces:
  - `get_recovery_semantic_review_readiness(workspace, book_id, *, branch_id)`
  - `get_recovery_semantic_review(workspace, book_id, *, branch_id)`
- Added diagnostic semantic review execution action:
  - `review_recovery_semantics`
  - exposed through `legal_next_actions`
  - exposed through `workflow review-recovery-semantics`
  - emits `recovery_semantic_review.json`
- Added downstream dependency review surfaces:
  - `get_downstream_dependency_review(workspace, book_id, *, branch_id)`
  - `review_downstream_dependencies`
  - exposed through `legal_next_actions`
  - exposed through `workflow downstream-dependency-review`
  - exposed through `workflow review-downstream-dependencies`
  - emits `downstream_dependency_review.json`
- The readiness surface is diagnostic-only and returns:
  - derived-branch requirement
  - required successful recovery receipts
  - structural branch health
  - semantic validation boundary status from 0081
  - present semantic review output, if any
  - recommended next action
- The read surface returns a truthful `not_started` diagnostic object when no semantic review artifact exists.
- The action is still evidence assembly, not automatic story repair:
  - it updates branch semantic-validation status
  - it records findings and limitations
  - it does not rewrite prose
  - it does not promote or mutate canonical state
  - it does not claim semantic continuity is proven

## Proposed Execution Actions
- `review_recovery_semantics`
  - branch-scoped
  - diagnostic output only
  - reads normalized outline, affected/downstream prose, state/projection summaries, and recovery receipts
  - emits `recovery_semantic_review.json`
- `review_downstream_dependencies`
  - branch-scoped
  - diagnostic output only
  - reads manifest downstream scopes and available downstream prose/projections
  - emits `downstream_dependency_review.json`
- Future follow-up actions may consume these diagnostics to request explicit:
  - downstream redraft
  - seam repair
  - setting/appearance refresh
  - summary rebuild
  - human approval

## Review Schema Requirements
- Every semantic review artifact must include:
  - `schema_version`
  - `book_id`
  - `branch_id`
  - `node`
  - `artifact_status: diagnostic`
  - `review_scope`
  - `reviewed_artifacts`
  - `findings`
  - `blocked_actions`
  - `recommended_next_action`
  - `confidence`
  - `review_limitations`
- Findings must distinguish:
  - structural blocker already handled by 0081
  - semantic continuity risk
  - downstream dependency risk
  - prose quality/seam risk
  - missing evidence
  - human decision required

## LLM Contract Direction
- Use the existing style of strict BookForge prompt contracts:
  - read-only context separated from writable outputs
  - exact scope
  - explicit output schema
  - `error_v1` fallback
  - no repair text unless the action is a dedicated mutation action
- The reviewer LLM should not invent canonical facts.
- It should cite the artifacts and scene/chapter refs that support each finding.
- It should be allowed to say the evidence is insufficient.

## Nanda Alignment
- Nanda should use these surfaces to populate or refine `book_timeline_impact_report_v1`.
- Nanda owns:
  - strategy selection
  - comparing candidate actions
  - human approval flow
  - deciding whether semantic findings justify downstream mutation
- BookForge owns:
  - reading branch artifacts
  - producing review receipts
  - preserving diagnostic artifacts
  - refusing mutation without explicit scoped action requests

## Definition Of Done
- Readiness query exists for semantic recovery review. Done.
- At least one diagnostic semantic review action exists and is exposed through `legal_next_actions`. Done.
- Review artifacts carry `artifact_status: diagnostic`. Done.
- Recovery branch health can surface whether semantic review is missing, clean, or attention-required. Done.
- Tests cover:
  - review refused before structural prerequisites. Done through action-discovery/refusal coverage.
  - review artifact emitted after redraft/validation. Done.
  - downstream review candidates appear without becoming mutation targets. Done.
  - Nanda-visible query output distinguishes structural health from semantic review status. Done.

## Test Plan
- Add focused unit tests for readiness and action discovery.
- Add fixture tests using the two-chapter recovery fixture from 0081.
- Keep LLM calls mocked.
- Run full regression before marking complete.

## Completion Notes
- BookForge now provides diagnostic evidence surfaces for semantic recovery review and downstream dependency review.
- The implemented actions do not call an LLM, rewrite prose, repair seams, promote branches, or decide story quality.
- LLM-backed author review is deferred to Nanda/author-reasoning integration unless BookForge later needs an engine-owned reviewer prompt.
- Latest full validation: `310 passed`.
