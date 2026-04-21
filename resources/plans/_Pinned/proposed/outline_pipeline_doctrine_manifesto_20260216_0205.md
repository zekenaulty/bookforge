# Outline Pipeline Doctrine Manifesto (20260216_0205)

## Core Doctrine
LLM authors and lints; orchestrator never authors or discards; orchestrator only enforces validated state and deterministic invariants.

## Meaning of This Doctrine
1. Semantic authoring belongs to the LLM.
2. Semantic correction belongs to the LLM.
3. Semantic lint judgment belongs to the LLM.
4. Deterministic code performs schema checks, invariant checks, routing, retries, gating, and reporting.
5. Deterministic code does not generate transition prose, inserted scene prose, or semantic anchor content.
6. Deterministic code does not silently discard model-created data.
7. Unknown or invalid data is routed for classification or correction, never erased by default.

## Operational Commitments
1. Detect -> route -> LLM fix -> revalidate is the default semantic recovery loop.
2. Any automatic deterministic transform must be non-semantic and auditable.
3. All policy downgrades, conflicts, and blocked actions must be visible in console and run reports.
4. Terminal failures must be explicit and reason-coded.
5. Resume/rerun reuse is allowed only under deterministic fingerprint compatibility.

## Explicit Prohibitions
1. No code-authored fallback transition text.
2. No code-authored fallback transition anchors.
3. No code-authored inserted transition scenes.
4. No silent dropping of unknown keys or unknown entities.
5. No silent conversion of hard insertion requirements into inline bridges.

## PR/Review Checklist Anchor
A change is non-compliant if any of the following is true:
1. Code path creates semantic prose content to satisfy validation.
2. Code path removes unknown model data without classification path and provenance.
3. Retry path does not return semantic fixes to LLM.
4. Reports do not expose blocked or downgraded transition decisions.

## Scope
This doctrine applies to:
1. outline pipeline phases,
2. outline transition hardening,
3. downstream writing-loop transition routing and state intake where this doctrine is referenced by plan.

