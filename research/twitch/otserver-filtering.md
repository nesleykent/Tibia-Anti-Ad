# Removing OTServer streams from Twitch's Tibia category

Current implementation: [server-identity model and held-out evaluation](../../docs/TWITCH_MODEL.md). The rules and image-processing descriptions below are historical and are no longer executable classifier behavior.

Research notes, 2026-10-21. Goal: hide streams of other games (RubinOT and other OTServers, Pokémon servers, idle games) that use Twitch's **Tibia** category, without hiding official Tibia streams.

## The problem

In the audited capture ([report](data/2026-10-21/analysis/relatorio.pdf)), 456 streams with 12,989 viewers were live in the Tibia category. Official Tibia had 92 channels and **8.1%** of viewers. RubinOT alone had 38.9%, PokeAlliance 17.8% and PokeXGames 11.7%. Twitch has no separate category for these servers, and the directory's tag filter can only *include* a tag, not exclude one.

## What the audit established

The report's method is the reference for this project:

- **Tags are decisive.** An earlier extractor dropped intermediate tags and missed signals such as miguelnutt's `rubinot` tag. Title and **all** tags must be read.
- **Strong evidence** is a game, server or world stated directly and consistently in the title and/or tags.
- **Official world names** are strong evidence of Tibia. The generic `Tibia` tag is **not** proof of CipSoft's game.
- **Commands for other games** (`!rubinot`), historical tags, announcements and titles listing several servers are noted separately and are **not** used on their own to decide the game shown.
- Anything the text cannot support stays undetermined. Probable Tibia is kept apart from confirmed Tibia.

## Existing approaches

| Approach | What it does | Limits |
|---|---|---|
| [Unwanted Twitch](https://github.com/kwaschny/unwanted-twitch) ([AMO](https://addons.mozilla.org/addon/unwanted-twitch/), [Chrome](https://chromewebstore.google.com/detail/egbpddkgpjmliolmpjenjomflclekjld)) | User-managed blacklists of categories, channels, tags and title patterns (regex), matched against the rendered DOM | Can match only the tags the card displays; Twitch truncates them. Manual lists, no notion of evidence or official worlds |
| Old userscripts / "Filter channels from the Twitch directory" ([OpenUserJS](https://openuserjs.org/scripts/LinogeFly/Hide_unwanted_streams_on_Twitch)) | Title or channel-name filters | Unmaintained; break with Twitch markup changes |
| Cosmetic filters (uBlock Origin procedural `:has-text()`) | Hide cards whose text matches | Same truncated tags; no way to weigh official evidence against a sponsor command |
| Twitch's own UI | "Not interested" per recommendation | Per-stream, manual, not a filter |
| Permanent channel blocklists | — | Channels switch games; the audit relies on per-broadcast evidence instead |

## Data source chosen

Every directory card is rendered by React with props that include the complete `title`, **every** freeform tag (`tagListProps.freeformTags`), `channelLogin` and the viewer count. These are the same fields the audited JSON capture contained, available without any extra network request. Because React props live in the page's JavaScript world, Tibia Anti-Ad reads them from a small page-world script (`tibia-props.js`) and hands them to the filter through a data attribute. If the props cannot be found, the filter falls back to the visible card text.

## Current classification, 1.3.0

The live filter now uses a statistical model of the complete title and tags. Manual name rules and weighted lexical overrides described below are historical and no longer decide cards. See the [model card](../../docs/TWITCH_MODEL.md) for the algorithm, training provenance, comparison of inputs and limits.

## Historical classification rules, before 1.3.0

Implemented in `tools/twitch_evidence.py` (reference) and `extension/src/tibia-classify.js` (extension), configured in `filters/sources/twitch/tibia-evidence.json`:

1. **Other game:** a server declared in the title (not as a `!command`) or in a tag, including server domains and RubinOT's own world names (Infernum, Bellum, Belaria…), with no official evidence → hide.
2. **Tibia:** an official world name (from [TibiaData](https://api.tibiadata.com/v4/worlds)), "Tibia Global" or the `tibiaglobal` tag, with no server evidence → keep. World names that are also ordinary words (Dia, Sombra, Bona…) count only as tags.
3. **Undetermined** (kept visible): evidence both ways, a server only as a chat command, or nothing decisive.
4. A custom OTServer client element — the titled "Map View" minimap, Battle Pass, Daily Missions — never appears in the official client and marks the stream as another game. This resolves streams that tag both `rubinot` and `tibiaglobal`, and `!server`-only titles.

### Weighted classification (2026-10-22)

The rules above are now weighted signals rather than exact keyword tests (`weights`, `decision`, `fuzzy` and `context` in the evidence file):

- **Normalization:** accents and marks (including emoji variation selectors), lookalike Cyrillic/Greek letters and small capitals, fancy Unicode fonts (NFKD), leetspeak in mixed words (`rub1n0t`), repeated letters (`RUBINOTTT`, `TORNABRAAAA`) and spaced-out letters (`R U B I N O T`).
- **Spelling mistakes:** names listed under a game's `fuzzy` match one edit away (two for names of 10+ letters) with the same first letter, never against `fuzzy.protected` words or exact entries; an equally close official world wins.
- **Weights:** server name in the title 4 (misspelt 3.25), RubinOT or PokeAlliance world 3, `!server` command 3, server tag 3.5; official world or Tibia Global in the title 4, `global` 3, official tag 3. Weak context — server rates (`exp x50`), old client versions (`7.4`, `8.60`), `OT`/`OTs`, Pokémon words, `idle`, the channel name — weighs 1.5–2 and cannot decide alone.
- **Context:** up to two words before a mention, in the same clause, weaken it: negation ×0.2 (`não`, `sem`), leaving ×0.35 (`ex`, `saí do`), comparison ×0.5 (`vs`, `x`), another time ×0.6 (`depois`). `global` right after a server name is part of it (`Future OT Global`). Official tags count ×0.4 against a server named in the title.
- **Decision:** each side's signals combine as strongest + ½ next + ¼ next…; a side wins at 3 points with a 2-point lead, otherwise the stream is undetermined.

- **Server names everywhere (2026-10-22):** every listed server name or server world also counts as a tag (`hegal`), a name written with "ot" counts as the server (`!hegalot`), and websites in the title count: each unknown site 2 points (several add up: `troyale.online | tfight.online | …`), a dynamic-DNS host 3.5 (`tibiapirate.duckdns.org`, a self-hosted server); Tibia, fansite, social and streaming-tool sites count nothing.

`tests/data/tibia-classify-cases.json` holds hand-labelled spelling, negation and legitimate-Tibia cases; the Python reference and the extension port must agree on every verdict and score.

## Evaluation against the audit (456 channels)

| Audit category | Hidden | Undetermined (visible) | Tibia (visible) |
|---|---|---|---|
| Other games (281) | **276** | 4 | 1 |
| Tibia (92) | **0** | 6 | 86 |
| Unclear (83) | 9 | 69 | 5 |

The 9 unclear streams hidden all list several servers, none of them Tibia. On the 562-stream live capture the weighted rules agree with the reviewed verdicts on 560 streams: TORNABRAAAA (official) is now kept as Tibia, and one stream with only a `!rubinot` command and two official world tags is now undetermined. In Chrome Beta 157 on 2026-10-22 the extension hid 29 of the 30 first cards, each with its reason, and kept the official `WAR FEROBRA` stream. In WebKit (WKWebView on macOS 27 with Safari 27.0.1's engine, content scripts in an isolated world, metadata reader in the page world) the same 29 of 30 were hidden through `hide.css`, and the load-more nudge filled the list to 107 cards (96 hidden, 11 visible: 9 official-world streams, 2 undetermined). Twitch refused load-more in the DevTools-driven Chrome profile with `failed integrity check`, with or without the extension, so that run could not exercise it.

## Known gaps

- A streamer can mislabel deliberately (tagging `tibiaglobal` on an OTServer); only the screen check catches that.
