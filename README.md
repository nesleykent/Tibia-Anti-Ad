# Anti-Ad Tibia

**The player experience comes before monetization.**

Anti-Ad Tibia identifies, blocks and neutralizes intrusive advertising, tracking and navigation interference across services used by the Tibia community. The need to fund a fansite does not justify abusive advertising.

## What we cover

- Fansites, wikis, calculators, maps, databases, market tools and community portals.
- Floating ads, pop-ups, forced redirects, autoplay, intrusive banners, tracking, fingerprinting, anti-adblock walls and leftover ad containers.
- Website assessments covering advertising intrusiveness, tracking, performance and usability.
- Twitch advertising research and precision-first identification of OTServ streams among Tibia broadcasts.

Navigation, editorial content, tools and accessibility must keep working. Positive recognition never grants an exemption: **no website receives immunity from ad blocking**.

## Project status

This is an initial research and tooling release. Experimental filter inputs and historical reports are included for 15 websites. Generated bundles exclude two sites with content-destruction risks. The remaining rules still require real extension testing across browsers; historical CSS injection and network simulation are not proof of blocker enforcement.

Twitch includes reconnaissance scripts and an offline text-classification prototype. **Twitch video-ad neutralization, thumbnail analysis and automatic stream filtering are not implemented.** No production accuracy claim or public channel blocklist is made.

## Try the experimental website filters

**Private repository:** anonymous raw subscriptions will not work while access is restricted. Authorized users can download a generated list and import/paste it through a supported blocker interface. Never embed a GitHub access token in a subscription URL.

Read the [installation and rollback guide](docs/INSTALLATION.md) and [compatibility notes](docs/COMPATIBILITY.md) before enabling a list.

- [Portable syntax bundle](https://raw.githubusercontent.com/nesleykent/anti-ad-tibia/main/filters/anti-ad-tibia.txt): site-scoped network rules and basic cosmetic selectors.
- [Extended syntax bundle](https://raw.githubusercontent.com/nesleykent/anti-ad-tibia/main/filters/anti-ad-tibia-extended.txt): also includes `:has()` selectors; an alternative to the portable bundle.
- [Per-site inputs](filters/sites): research inputs, **not installation-ready lists**; some contain globally scoped rules or known breakage.

No bundle contains Twitch video-ad blocking. The lists do not depend on EasyList/EasyPrivacy for their included rules, but do not claim complete protection. Userscripts are optional research artifacts and are never installed by a subscription.

## Evidence and assessments

See the [website inventory](docs/WEBSITES.md), [assessment rubric](docs/ASSESSMENTS.md) and [research reports](research/reports). Historical reports distinguish observed, simulated and assumed behavior. Their claims have not been independently reproduced for this release, and raw screenshots/HAR files are not included. Numeric ratings and measured performance rankings are pending reproducible audits.

## Twitch

[Classification policy and limitations](docs/TWITCH.md) covers titles, tags, language, metadata and thumbnails. Missing or contradictory evidence yields `undetermined`. Language, country, viewer count and the Tibia category alone cannot establish OTServ. The prototype never automatically hides streams.

```sh
python3 tools/classify_streams.py path/to/streams.json
```

The input is an array of stream objects with `title`, `tags` and optional metadata. Processing stays local and writes results to standard output. No Twitch credentials are needed.

## Development and contributions

Python 3.11+ and its standard library are sufficient:

```sh
python3 tools/build_filters.py
python3 -m unittest discover -s tests -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md), the [specification](docs/SPEC.md) and [roadmap](docs/ROADMAP.md). Report breakage with the page URL, browser/blocker versions, active lists and reproducible steps. Never include account tokens or personal browsing data.

Independent community project. Not affiliated with CipSoft, Twitch or the reviewed websites. Tibia belongs to CipSoft GmbH.
