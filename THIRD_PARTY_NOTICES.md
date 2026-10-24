# Third-party notices and provenance

The root MIT license applies to project-authored work. It does not grant rights to third-party trademarks, website content or material whose redistribution terms have not been established.

## TwitchAdSolutions / vaft

- Upstream: <https://github.com/pixeltris/TwitchAdSolutions>
- Copyright (c) 2020-present TwitchAdSolutions Contributors.
- License: MIT; the full upstream notice remains embedded in `extension/src/page.js` and `scripts/twitch/twitch-stopthemadness.js`.
- The imported implementation reports version 24. Archive and source hashes are recorded in [source-manifest.json](research/twitch/source-manifest.json), alongside modifications made after import.

Preserve the upstream notice when redistributing these files. The project MIT notice does not replace it.

## Supplied extension assets and historical research

### Safari toolbar controls: Apple SF Symbols

`extension/src/icons/safari-toolbar/` contains PNG renderings of Apple's `infinity.circle` and `infinity.circle.fill` SF Symbols, generated using AppKit by `scripts/safari/export_toolbar_icons.swift`. They are Safari toolbar, popup blocking-status and native extension-status interface indicators, not app icons, logos or a trademark. Apple retains its rights; these assets are not licensed under this project's MIT license. Use is subject to [Apple's SF Symbols terms](https://developer.apple.com/sf-symbols/) and [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/sf-symbols). The Chrome packager omits these assets.

`extension/browsers/chrome/artwork/` contains original project-authored infinity-in-circle SVGs covered by the project's MIT license. The Chrome toolbar PNGs and shared extension branding PNGs are rendered from these vectors, independently of SF Symbols. Imported shield branding was replaced; original hashes remain in `research/twitch/source-manifest.json`.

The original Twitch Clean archive, icons, filter inputs, companion scripts, research reports and Twitch snapshots were supplied as the project's starting material. Their presence is not evidence of a separate upstream license grant. Provenance and modifications for the Twitch archive are recorded in the source manifest above. Other historical material is described in [research/README.md](research/README.md).

The root license covers the maintainer's original contributions to this material, not rights owned by other parties. Before a packaged release, maintainers must confirm redistribution rights for imported assets, including icons and any captured third-party material; replace or omit assets whose rights cannot be established. Do not claim that historical test reports have been independently reproduced.

Tibia and Twitch names, marks, game imagery and third-party broadcast or website content remain the property of their respective owners. Their inclusion for identification or research implies no affiliation or endorsement.

## Friendly-fansite screenshots

The [friendly-fansite collection](research/fansites/friendly/README.md) contains 23 user-supplied website screenshots received on 2026-10-22. Their original bytes and filenames are recorded in its manifest. The screenshots are research evidence; third-party website designs, text, imagery and marks retain their respective owners’ rights. The root MIT license does not grant rights to these underlying works.

## Optional scheduled local teacher

The learning workflow downloads [Ollama](https://github.com/ollama/ollama)
(MIT) and [Qwen3 4B Instruct 2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
(Apache-2.0), using the published Q4_K_M quantization. Their binaries and model
weights are not committed or included in extension downloads. Pinned runtime and
model digests are recorded in the learning tools.
