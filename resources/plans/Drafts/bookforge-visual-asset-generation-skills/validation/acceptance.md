# Acceptance

## Plan Acceptance
- Provider report includes current price/capability findings and source URLs.
- Legacy audit identifies what to lift and what not to port.
- Step plan separates contracts, prompt planning, provider adapters, actions/CLI, composition, and Nanda projection.

## Implementation Acceptance
- Provider descriptors can be queried without credentials.
- Readiness refuses unsupported transparent-background requests for selected models.
- OpenAI generation can produce a file-backed artifact through a mocked or live-configured provider path.
- Every generated visual artifact has a receipt with provider/model, prompt plan, hash, dimensions, output path, artifact status, and source refs.
- Capability projection reports visual skills with accurate readiness source, mutation class, expected receipt, and planned/unavailable provider status.
- Tests cover:
  - provider descriptor parsing
  - readiness/refusal
  - prompt plan output
  - provider request payload construction
  - receipt emission
  - capability projection entries

