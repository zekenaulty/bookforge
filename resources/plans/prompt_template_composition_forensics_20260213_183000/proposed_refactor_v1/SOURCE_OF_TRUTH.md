# Proposed Refactor v1 - Source of Truth

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
