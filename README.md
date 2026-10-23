# Tibia Anti-Ad

_Sorry for the inconvenience, we just want Tibia._

[![Validate project](https://github.com/nesleykent/Tibia-Anti-Ad/actions/workflows/check.yml/badge.svg)](https://github.com/nesleykent/Tibia-Anti-Ad/actions/workflows/check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Browser extensions, content-blocking filters and transparent research for a cleaner Tibia community. Find actual Tibia streams on Twitch and browse fansites without advertising and tracking, while keeping the articles, calculators, maps and tools you came for.

**Love the fansites, not the ads.** Read the full [Tibia Anti-Ad Manifesto](MANIFESTO.md) for the motivation and principles behind this project.

**[Download for Chrome (.zip)](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-chrome.zip)** · [Chrome guide](docs/INSTALL_CHROME.md)

**[Download for Safari (.zip, temporary extension)](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-safari-extension.zip)** · [Safari guide and Mac app](docs/INSTALL_SAFARI.md)

**Chrome:** Extract the ZIP, open `chrome://extensions`, enable **Developer mode**, click **Load unpacked**, and choose the extracted `tibia-anti-ad-chrome` folder. No GitHub account or terminal is needed.

**Safari:** For a quick trial, download the Safari ZIP, extract it, then use **Safari → Settings → Developer → Add Temporary Extension…**. This temporary method ends when Safari quits or after 24 hours. For an installed Mac app, see the [Safari guide and free personal signing instructions](docs/INSTALL_SAFARI.md). The maintainer's app already uses personal Apple Development signing; see [current signing status](docs/SAFARI_STATUS.md) for verified results and remaining Safari checks.

## Choose how to use it

| Component | What it does | Start here |
| --- | --- | --- |
| Browser extension | Twitch ad/tracking rules, video-ad replacement attempts, reversible stream filtering and controls for 15 fansites | [Extension setup and settings](extension/README.md) |
| Website filter lists | Site-scoped rules for an existing compatible blocker; 13 sites included | [Installation and rollback](docs/INSTALLATION.md) |
| Standalone Twitch script | Video-ad replacement through StopTheMadness Pro; choose this or the extension's video integration | [Script setup](scripts/twitch/README.md) |
| Research and classification tools | Inspect evidence and reproduce offline classifications | [Research](research/README.md) · [Twitch methodology](docs/TWITCH.md) |

## Status and limits

**Experimental.** The repository's automated checks cover generated artifacts, rule scope, settings and offline classifications. They do not certify live ad removal or browser compatibility. Historical reports are supplied evidence, not newly reproduced audits. See [verification](docs/VERIFICATION.md), [compatibility](docs/COMPATIBILITY.md) and the [roadmap](docs/ROADMAP.md).

- The extension uses a **supervised probabilistic machine-learning model** over explicit server identities in titles and tags to distinguish official Tibia from other streams. Language, generic gameplay and chat commands have no features. Separate groups fit and calibrate the model; conflicts and insufficient evidence stay visible. No image processing is used. See the [model, held-out results and annotation audit](docs/TWITCH_MODEL.md).
- The vaft integration attempts to replace stitched video ads. Live effectiveness is unverified, and playback can stall or fall back to lower quality during breaks.
- Filter subscriptions exclude TibiaWiki BR and Tibiopedia because of documented content-destruction risks. The extension includes experimental repairs for both and enables their site controls by default; review its settings and disable a site if it breaks.

## Install website filters

Choose **one** generated list and add its URL to a blocker that supports its syntax:

- [Portable bundle](https://raw.githubusercontent.com/nesleykent/Tibia-Anti-Ad/main/filters/lists/anti-ad-tibia.txt): site-scoped network rules and basic cosmetic selectors.
- [Extended bundle](https://raw.githubusercontent.com/nesleykent/Tibia-Anti-Ad/main/filters/lists/anti-ad-tibia-extended.txt): an alternative that also includes `:has()` selectors.

Read the [installation and rollback guide](docs/INSTALLATION.md) first. [Per-site inputs](filters/sources/sites) are research material, not installation-ready subscriptions. The bundles contain no Twitch video-ad replacement and install no userscripts. Cosmetic hiding alone does not stop tracking requests.

## Principles in practice

- **Preserve useful content.** Navigation, search, forms, playback, tools and accessibility must keep working.
- **Respect viewer choice.** Classify the current broadcast, keep uncertainty visible and support corrections; no permanent channel blacklist.
- **Document the evidence.** Distinguish observed, simulated, experimental and unverified results. Publish no invented scores or performance claims.
- **Support the community.** Recognize good practices and voluntary contributions without granting advertising exemptions or targeting individuals.

The [friendly-fansite collection](research/fansites/friendly/README.md) recognizes 23 community projects through supplied screenshots captured without blockers, with observations and explicit evidence limits.

Explore the [website inventory](docs/WEBSITES.md), [assessment rubric](docs/ASSESSMENTS.md) and [historical reports](research/fansites/reports).

## Repository layout

```text
extension/            Browser extension
  src/                Shared source and generated site rules
  browsers/chrome/    Chrome-specific manifest overrides
filters/
  sources/            Fansite rules and Twitch evidence inputs
  lists/              Generated subscriptions to install
docs/                 Setup, compatibility, methodology and maintenance
research/
  fansites/           Historical reports and optional userscripts
  twitch/             Captures, classification research and provenance
scripts/twitch/       Standalone video-ad script
tests/
  python/             Build, rule-scope and classification tests
  javascript/         Extension startup and settings checks
tools/                Build, classification and verification commands
```

See the [documentation index](docs/README.md) for navigation. Generated development packages go to the ignored `dist/` directory. Original local working files are archived under the ignored `local/legacy/` directory.

## Develop and contribute

Requires **Python 3.11+** and **Node.js 22+**. Build tools use the Python standard library; no package installation or Twitch credentials are required for the checks.

```sh
git clone https://github.com/nesleykent/Tibia-Anti-Ad.git
cd Tibia-Anti-Ad
python3 tools/check_project.py
python3 tools/build_chrome_extension.py
```

The check command runs syntax checks, tests, offline evaluation, documentation checks and generated-file verification. The Chrome build is written to `dist/tibia-anti-ad-chrome`; see the [extension guide](extension/README.md) before loading it. Safari source is in `extension/src`.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow, [release guidance](docs/RELEASING.md) for publication gates and [CHANGELOG.md](CHANGELOG.md) for changes. Report breakage and false positives through [GitHub issues](https://github.com/nesleykent/Tibia-Anti-Ad/issues). Report vulnerabilities using [SECURITY.md](SECURITY.md). Community participation follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## License and independence

Project-authored work is available under the [MIT License](LICENSE). Imported code and research retain their attribution and applicable terms; review [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistribution.

Independent community project, unaffiliated with CipSoft, Twitch or the reviewed websites. Tibia belongs to CipSoft GmbH. Names and marks identify the services this project works with and do not imply endorsement.
