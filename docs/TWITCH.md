# Twitch: advertising and stream classification

## Platform advertising

Investigate display ads, overlays, telemetry and pre-roll/mid-roll video separately. Preserve playback, audio, captions, chat, sign-in, channel points and accessibility. Shared media/CDN or GraphQL endpoints must not be blocked indiscriminately. Server-inserted video advertising cannot be assumed removable with cosmetic CSS or a static hostname rule.

`research/twitch/recon.js` inventories DOM hooks and resource hosts. `collect-streams.js` is a historical scrolling collector, not an official API client or classifier; it may misread cards/counts and is not part of a default installation. Neither reconnaissance script neutralizes video ads. Collected snapshots and their classification live in [`research/twitch/data`](../research/twitch/data/2026-10-21/README.md).

The supplied **[Twitch Clean extension](../extensions/twitch-clean/README.md)** now packages vaft, Source quality, network rules and cosmetic/nag handling. The **[StopTheMadness Pro script](../scripts/twitch/README.md)** is a standalone alternative. Both contain the supplied vaft video-ad replacement logic; current live effectiveness remains unverified. The [complementary Twitch filters](../filters/twitch/twitch.tv.txt) and [historical report](../research/twitch/twitch.tv-validation.md) are also included. Choose one vaft injection method. These assets do not implement OTServ filtering.

## Precision-first classification

Labels: **Tibia**, **OTServ**, **undetermined**. Classify the current broadcast, not the person or channel permanently. Keep timestamped evidence, source and a reason for every decision.

| Signal | Use and limits |
| --- | --- |
| Title | Explicit current-broadcast description; mentions can be quotations, negations or comparisons |
| Tags | Corroboration; user-generated tags can be inaccurate or stale |
| Language | Context for interpreting text; never an OTServ signal by itself |
| Metadata | Category, description, known server and world references; category Tibia alone is inconclusive |

The offline prototype requires matching unambiguous declarations in both title and tag: title exactly `OTServ`, `OTServer` or `Open Tibia` plus an equivalent tag yields `OTServ`; title exactly `Official Tibia` or `Tibia Global` plus an equivalent tag yields `Tibia`. Other text, missing fields, mixed declarations and uncertain statements yield `undetermined`. This intentionally has low recall. It is a synthetic demonstration, not a validated detector. Language and other metadata are preserved in input but do not affect this prototype's label.

Input example:
```json
[{"title": "OTServ", "tags": ["OTServ"], "language": "en"}]
```

Every prototype output sets `hide: false`, even for OTServ: no real-stream precision benchmark has been completed. Future optional hiding must require high-confidence corroborated evidence, a visible explanation, per-stream override and an immediate undo. Undetermined and legitimate Tibia streams stay visible. Corrections must not require exposing a viewer's private history.

## Validation gate for future integration

Separate channels between tuning and holdout sets. Measure OTServ precision, false positives among official streams, recall and abstention by language. Target at least 99% OTServ precision with a reported confidence interval; a small sample cannot establish the target. Do not enable automatic hiding until the target and functional playback checks pass. Any known false positive requires investigation before release.

Official reference: [Twitch API reference](https://dev.twitch.tv/docs/api/reference), consulted 2026-10-21.

## OTServer filtering

Twitch Clean hides OTServer, Pokémon-server and idle-game streams on the Tibia category directory. Method, alternatives and evaluation: [research/twitch/otserver-filtering.md](../research/twitch/otserver-filtering.md). Rules: `filters/twitch/tibia-evidence.json`; reference implementation and evaluation: `python3 tools/twitch_evidence.py --evaluate`.
