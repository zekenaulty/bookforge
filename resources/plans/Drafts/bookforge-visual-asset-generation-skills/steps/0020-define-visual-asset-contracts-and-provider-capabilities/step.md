# 0020 - Define Visual Asset Contracts And Provider Capabilities

Status: draft
Depends On: 0010

## Goal
Freeze the contract vocabulary before implementation.

## Detailed Work
- Add or plan contract classes for:
  - `VisualAssetRequest`
  - `VisualPromptPlan`
  - `VisualAssetReceipt`
  - `VisualStyleProfile`
  - `ProviderCapabilityDescriptor`
  - `ReferenceImageRef`
  - `LayerIntent`
  - `LayerCompositionManifest`
- Define visual purpose enum:
  - `background_layer`
  - `character_reference`
  - `character_in_scene`
  - `transparent_foreground_layer`
  - `scene_illustration`
  - `style_transfer`
  - `composition`
- Define provider support flags and refusal codes.

## Likely Files Touched
- `src/bookforge/contracts/visual_asset.py`
- `src/bookforge/contracts/visual_provider.py`
- `src/bookforge/contracts/visual_prompt.py`
- `tests/test_visual_contracts.py`

## Definition Of Done
- Contracts are typed and serializable.
- Provider descriptors include source URL and verification date.
- Refusal codes include unsupported transparency, unsupported references, unsupported size, missing credentials, and unknown price.

## Tests
- Contract serialization tests.
- Descriptor validation tests.

