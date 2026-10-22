# Removing OTServer streams from Twitch's Tibia category

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

## Classification rules

Implemented in `tools/twitch_evidence.py` (reference) and `extensions/tibia-anti-ad/extension/tibia-classify.js` (extension), configured in `filters/twitch/tibia-evidence.json`:

1. **Other game:** a server declared in the title (not as a `!command`) or in a tag, including server domains and RubinOT's own world names (Infernum, Bellum, Belaria…), with no official evidence → hide.
2. **Tibia:** an official world name (from [TibiaData](https://api.tibiadata.com/v4/worlds)), "Tibia Global" or the `tibiaglobal` tag, with no server evidence → keep. World names that are also ordinary words (Dia, Sombra, Bona…) count only as tags.
3. **Undetermined** (kept visible): evidence both ways, a server only as a chat command, or nothing decisive.
4. A custom OTServer client element — the titled "Map View" minimap, Battle Pass, Daily Missions — never appears in the official client and marks the stream as another game. This resolves streams that tag both `rubinot` and `tibiaglobal`, and `!server`-only titles.

## Evaluation against the audit (456 channels)

| Audit category | Hidden | Undetermined (visible) | Tibia (visible) |
|---|---|---|---|
| Other games (281) | **257** | 23 | 1 |
| Tibia (92) | **0** | 8 | 84 |
| Unclear (83) | 7 | 71 | 5 |

The 7 unclear streams hidden all list several servers, none of them Tibia.

## Known gaps

- A streamer can mislabel deliberately (tagging `tibiaglobal` on an OTServer); only the screen check catches that.
