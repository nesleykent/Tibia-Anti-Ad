# Twitch: advertising and stream classification

The extension's current classifier is a supervised probabilistic machine-learning model, trained on labelled full titles and tags. It estimates private-server streams, and Safari displays the complement of that estimate as the Tibia percentage. See the [current model card](TWITCH_MODEL.md). The offline prototype below is historical; its hand-written declaration rules do not run in the extension.

## Platform advertising

Investigate display ads, overlays, telemetry and pre-roll/mid-roll video separately. Preserve playback, audio, captions, chat, sign-in, channel points and accessibility. Shared media/CDN or GraphQL endpoints must not be blocked indiscriminately. Server-inserted video advertising cannot be assumed removable with cosmetic CSS or a static hostname rule.

`research/twitch/recon.js` inventories DOM hooks and resource hosts. `collect-streams.js` is a historical scrolling collector, not an official API client or classifier; it may misread cards/counts and is not part of a default installation. Neither reconnaissance script neutralizes video ads. Collected snapshots and their classification live in [`research/twitch/data`](../research/twitch/data/2026-10-21/README.md).

The supplied **[Tibia Anti-Ad extension](../extension/README.md)** now packages vaft, Source quality, network rules and cosmetic/nag handling, each with its own switch in the extension's settings. The **[StopTheMadness Pro script](../scripts/twitch/README.md)** is a standalone alternative. Both contain the supplied vaft video-ad replacement logic; current live effectiveness remains unverified. The [complementary Twitch filters](../filters/sources/twitch/twitch.tv.txt) and [historical report](../research/twitch/twitch.tv-validation.md) are also included. Choose one vaft injection method. The standalone script does not implement OTServ filtering; the extension has a separate title/tag classifier described below.

## Historical offline prototype

Labels: **Tibia**, **OTServ**, **undetermined**. Classify the current broadcast, not the person or channel permanently. Keep timestamped evidence, source and a reason for every decision.

| Signal | Use and limits |
| --- | --- |
| Title | Explicit current-broadcast description; mentions can be quotations, negations or comparisons |
| Tags | Corroboration; user-generated tags can be inaccurate or stale |
| Language | Context for interpreting text; never an OTServ signal by itself |
| Metadata | Category, description, known server and world references; category Tibia alone is inconclusive |

The offline prototype requires matching unambiguous declarations in both title and tag: title exactly `OTServ`, `OTServer` or `Open Tibia` plus an equivalent tag yields `OTServ`; title exactly `Official Tibia` or `Tibia Global` plus an equivalent tag yields `Tibia`. Other text, missing fields, mixed declarations and uncertain statements yield `undetermined`. This intentionally has low recall. It is a synthetic demonstration, not a validated detector. Language and other metadata are preserved in input but do not affect this prototype's label. This prototype does not integrate with live pages; the extension uses title/tag evidence, as described below.

Input example:
```json
[{"title": "OTServ", "tags": ["OTServ"], "language": "en"}]
```

Every prototype output sets `hide: false`, even for OTServ: this synthetic prototype has no real-stream precision benchmark. Future optional hiding must require high-confidence corroborated evidence, a visible explanation, per-stream override and an immediate undo. Undetermined and legitimate Tibia streams stay visible. Corrections must not require exposing a viewer's private history.

## Validation gate for future integration

Build an independently reviewed, timestamped labeled set containing multilingual titles, real official broadcasts, OTServ, mixed sessions, negations, promotions and ambiguous title/tag combinations. Separate channels between tuning and holdout sets. Measure OTServ precision, false positives among official streams, recall and abstention by language. Target at least 99% OTServ precision with a reported confidence interval; a small sample cannot establish the target. Do not enable automatic hiding until the target and functional playback checks pass. Any known false positive requires investigation before release.

Official reference: [Twitch API reference](https://dev.twitch.tv/docs/api/reference), consulted 2026-10-21. Stream metadata exposes titles, language and tags; none is authoritative proof of official Tibia versus OTServ.

## OTServer filtering

The extension jointly analyzes full titles and tags with a supervised probabilistic model. It does not use a manually maintained server-name blacklist, channel identity, or heuristic point totals to decide a card. The model estimates private-server streams in the Tibia category; Safari shows `1 - P(private-server stream | title, tags)` beside the channel name. A visibility cutoff is separate from this probability, and uncertain streams stay visible. Training provenance, decision thresholds, development measurements and limitations are in the [model card](TWITCH_MODEL.md).

The settings popover summarizes how many streams it hides; **Manage Blocked Streams…** opens their titles and model reasons. **Show** keeps that broadcast visible until its title changes, and **Hide** undoes the correction. **Hide other games** immediately switches filtering on or off. Safari probability labels remain visible with either setting; the master switch pauses both. Learned parameters live in `filters/sources/twitch/tibia-evidence.json`; the reference implementation and evaluation are available with `python3 tools/twitch_evidence.py --evaluate`. Earlier rule-based approaches remain documented as history in the [research notes](../research/twitch/otserver-filtering.md).
