# Initial Risks

## Provider Drift
Model names, prices, and capabilities change quickly. Descriptors must include verification dates and source URLs.

## Transparency Assumption
The user expects transparent layers to be possible. Current OpenAI docs say `gpt-image-2` does not support transparent backgrounds. This must be a readiness/refusal condition.

## Capability Theater
Nanda may show designed visual skills as if they are wired. Capability projection must distinguish available, inspectable, planned, unavailable, and needs-bridge states.

## Workspace Size
Image assets can quickly bloat workspaces. Storage paths, hashes, and dedupe checks need to exist in the first implementation slice.

## Reference Contamination
Reference images can silently become truth. Every reference must carry role, source, scope, and hash.

## Over-Generic Image Command
A single `image generate` command would recreate the old problem. Public skills must match visual purpose and operator decision points.

